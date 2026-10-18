"""Real local CSV files + bounded background Python workers.

Only fixed worker code runs. This is not a sandbox for arbitrary model code.
Job metadata is in memory; process-crash recovery is not implemented.
"""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import BinaryIO

from recovery_lab.csv_io import read_csv, write_csv
from recovery_lab.environment import JobEnvironment
from recovery_lab.types import FaultMode, Task, ToolReply


class ProcessEnvironment(JobEnvironment):
    def __init__(self, task: Task, workdir: Path, fault: FaultMode = FaultMode.NONE,
                 max_calls: int = 24, job_timeout: float = 15.0):
        if not 0 < job_timeout <= 300:
            raise ValueError("job_timeout must be in (0, 300]")
        super().__init__(task, fault, max_calls)
        # Refuse reuse rather than mixing episodes or overwriting user files.
        self.workdir = workdir.resolve()
        self.workdir.mkdir(parents=True, exist_ok=False)
        for name in ("artifacts", "logs", "published"):
            (self.workdir / name).mkdir()
        self.source_path = self.workdir / "source.csv"
        write_csv(self.source_path, task.rows)
        self._source_bytes = self.source_path.read_bytes()
        self._processes: dict[str, subprocess.Popen] = {}
        self._streams: dict[str, BinaryIO] = {}
        self._started: dict[str, float] = {}
        self._timeout = job_timeout

    def _create_artifact(self, job_id: str, artifact_id: str) -> None:
        output = self.workdir / "artifacts" / f"{artifact_id}.csv"
        log = (self.workdir / "logs" / f"{job_id}.log").open("wb")
        try:
            # Deliberately strip provider credentials from the worker environment.
            worker_env = {k: os.environ[k] for k in
                          ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG") if k in os.environ}
            process = subprocess.Popen(
                [sys.executable, "-I", str(Path(__file__).with_name("worker.py")),
                 "--source", str(self.source_path), "--output", str(output)],
                cwd=self.workdir, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, env=worker_env,
            )
        except OSError:
            log.close()
            raise
        self._processes[job_id] = process
        self._streams[job_id] = log
        self._started[job_id] = time.monotonic()

    def _sync(self) -> None:
        try:
            self._source = read_csv(self.source_path)
            if self.source_path.read_bytes() != self._source_bytes:
                self._source = ()  # byte-level changes invalidate source preservation
        except (OSError, ValueError, UnicodeError):
            self._source = ()
        for job_id, process in self._processes.items():
            if process.poll() is None and time.monotonic() - self._started[job_id] > self._timeout:
                self._stop(process)
                self._failures[job_id] = "Worker exceeded job timeout"
            if process.poll() is None:
                continue
            self._streams[job_id].close()
            artifact_id = self._jobs.get(job_id)
            if artifact_id is None:
                continue
            if process.returncode != 0:
                self._failures.setdefault(job_id, "Worker failed; inspect read_job_logs")
                self._artifacts.pop(artifact_id, None)
                continue
            try:
                self._artifacts[artifact_id] = read_csv(
                    self.workdir / "artifacts" / f"{artifact_id}.csv")
            except (OSError, ValueError, UnicodeError):
                self._failures[job_id] = "Worker artifact missing or malformed"
                self._artifacts.pop(artifact_id, None)

    def _wait(self, job_id: str, timeout_seconds: float) -> ToolReply:
        deadline = time.monotonic() + timeout_seconds
        while True:
            reply = self._job_reply(job_id)
            if reply.status != "running" or time.monotonic() >= deadline:
                return reply
            time.sleep(0.01)

    def _logs(self, job_id: str) -> str:
        self._sync()
        with (self.workdir / "logs" / f"{job_id}.log").open("rb") as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - 4000))
            return stream.read().decode("utf-8", errors="replace")

    def _publish(self, artifact_id: str) -> None:
        target = self.workdir / "published" / f"publication-{len(self._published) + 1:03d}.csv"
        temporary = target.with_suffix(".tmp")
        try:
            shutil.copyfile(self.workdir / "artifacts" / f"{artifact_id}.csv", temporary)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    def snapshot(self):
        state = super().snapshot()
        # Grade the bytes actually published, rather than only the source artifact.
        from dataclasses import replace
        artifacts = dict(state.artifacts)
        for index, artifact_id in enumerate(state.published, start=1):
            try:
                artifacts[artifact_id] = read_csv(
                    self.workdir / "published" / f"publication-{index:03d}.csv")
            except (OSError, ValueError, UnicodeError):
                artifacts.pop(artifact_id, None)
        return replace(state, artifacts=artifacts)

    @staticmethod
    def _stop(process: subprocess.Popen) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)

    def close(self) -> None:
        for process in self._processes.values():
            self._stop(process)
        self._sync()
        for stream in self._streams.values():
            stream.close()
