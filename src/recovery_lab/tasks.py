"""One task family. Seeds vary data, NOT task structure or model randomness."""

import random

from recovery_lab.types import Row, Task


def make_task(seed: int = 0, requires_approval: bool = False,
              approval_granted: bool = True) -> Task:
    rng = random.Random(seed)
    rows = [Row("sample-a", rng.randrange(1, 100)), Row("sample-b", rng.randrange(1, 100)),
            Row("sample-a", rng.randrange(101, 200)), Row("sample-c", rng.randrange(1, 100))]
    rng.shuffle(rows)
    return Task(f"deduplicate-{seed}", tuple(rows), requires_approval, approval_granted)

