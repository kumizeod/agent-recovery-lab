// Keyword Pool for LLM Story Generation
    const KEYWORD_POOL = [
      '午夜电梯', '海龟汤', '双胞胎', '盲人琴师', '密室录音', '末班地铁',
      '无人孤岛', '记忆橡皮', '半根火柴', '雪山木屋', '倒立时钟', '婚礼合照',
      '深海潜水', '绿色信封', '失踪魔术', '镜中陌生人', '旧八音盒', '第13层',
      '时间循环', '匿名包裹', '沙漠旅人', '守灯人', '停电手术室', '红舞鞋'
    ];

    // Curated Built-in Mysteries (fallback & instant play without API key)
    const BUILTIN_SOUPS = [
      {
        id: 'soup-match',
        type: 'clear',
        title: '半根火柴',
        tags: ['沙漠旅人', '半根火柴', '无人孤岛'],
        surface: '沙漠里发现了一具男子的遗体，他赤身裸体，手里紧紧攥着半根火柴，周围没有任何脚印。请问究竟发生了什么？',
        bottom: '男子和同伴乘坐热气球跨越沙漠时，热气球发生故障下坠。为了减轻重量，大家扔掉了所有行李甚至衣物，但热气球依然超重。最后众人决定用抽签的方式决定谁跳下去牺牲自己，抽到断成半根火柴的人必须跳下热气球，男子不幸抽中了那半根火柴。',
        hints: [
          '他并不是走路进入沙漠中央的，因此地面没有脚印。',
          '他当时正处于高空交通工具上，且面临全员覆灭的危机。',
          '手里的半根火柴是抽签决定的信物。'
        ],
        rules: [
          { keywords: ['死', '去世', '坠落', '摔死', '跳'], verdict: 'YES', reply: '是的，他是从高处跳下坠落身亡的。', progress: 25 },
          { keywords: ['热气球', '飞行', '飞机', '空中', '高空', '天上'], verdict: 'YES', reply: '是的！他当时正在乘坐热气球经过沙漠上空。', progress: 35 },
          { keywords: ['抽签', '抓阄', '火柴', '运气', '决定'], verdict: 'YES', reply: '是的，半根火柴正是用来抽签决定谁跳下去减重的。', progress: 30 },
          { keywords: ['衣服', '赤身', '裸', '行李', '减重', '超重'], verdict: 'YES', reply: '是的，脱掉衣服和扔掉行李都是为了给下坠的热气球减重。', progress: 25 },
          { keywords: ['谋杀', '杀害', '仇杀', '毒'], verdict: 'NO', reply: '不是，没有人蓄意谋杀他，这是全员求生下的无奈抽签。', progress: 10 },
          { keywords: ['第三', '同伴', '别人', '其他人', '朋友'], verdict: 'YES', reply: '是的，当时热气球上还有其他同伴。', progress: 15 }
        ]
      },
      {
        id: 'soup-elevator',
        type: 'red',
        title: '午夜第13层',
        tags: ['午夜电梯', '第13层', '邻居'],
        surface: '一名男子住在公寓的15楼。每天早上他出门上班都直接乘电梯从15楼坐到1楼；但每天下班回家时，如果电梯里只有他一个人，他只会乘电梯到10楼，然后走楼梯爬回15楼。如果是下雨天或者电梯里有别人，他就会直接坐到15楼。为什么？',
        bottom: '这名男子身材非常矮小（患有侏儒症），他伸手最高只能按到电梯里的10楼按钮，而1楼按钮在最下方所以早上能直接按到。下雨天他随身带着长柄雨伞，可以用雨伞尖去戳15楼按钮；电梯里有其他人时，他可以请别人帮忙按15楼。',
        hints: [
          '他不直接坐到15楼并不是为了锻炼身体，也不是因为10楼以上闹鬼。',
          '注意「下雨天」他随身携带的物品有什么物理特征。',
          '这与他自身的身体条件以及电梯按钮的高度有关。'
        ],
        rules: [
          { keywords: ['矮', '身高', '侏儒', '小孩', '够不到', '高度', '按钮'], verdict: 'YES', reply: '是的！他的身高不够，平时最高只能触碰到10楼的按钮。', progress: 45 },
          { keywords: ['雨伞', '伞', '工具', '长'], verdict: 'YES', reply: '是的，下雨天他带着雨伞，可以用雨伞够到15楼按钮。', progress: 35 },
          { keywords: ['帮忙', '别人', '请', '按'], verdict: 'YES', reply: '是的，电梯里有别人时，他会请对方帮忙按15楼。', progress: 25 },
          { keywords: ['死', '杀', '鬼', '凶手'], verdict: 'NO', reply: '不是，故事中没有任何人死亡或超自然现象。', progress: 10 }
        ]
      },
      {
        id: 'soup-turtle',
        type: 'black',
        title: '正宗海龟汤',
        tags: ['海龟汤', '无人孤岛', '记忆橡皮'],
        surface: '一名男子走进一家海滨餐厅，点了一碗招牌「海龟汤」。他只刚喝了一口，就脸色惨白地询问主厨这是否真的是用海龟肉熬制的。得到主厨肯定的答复后，男子回到家便绝望地结束了生命。为什么？',
        bottom: '多年前男子和挚友遭遇海难漂流在荒岛上，弹尽粮绝之际，重伤的挚友在临终前给他端来一碗肉汤，谎称是「海龟汤」让他活下去。男子靠这碗肉活到了获救。直到今天他在餐厅喝到真正的海龟汤，发现味道完全不同，才惊觉当年在荒岛上喝下的其实是挚友用自己的血肉熬成的汤。',
        hints: [
          '男子之前以为自己喝过「海龟汤」，但今天的味道和他记忆中完全不一样。',
          '多年前他曾经历过一次绝境求生（海难荒岛）。',
          '当年在荒岛上给他做汤的同伴并没有活着回来。'
        ],
        rules: [
          { keywords: ['味道', '不一样', '不同', '假', '没喝过'], verdict: 'YES', reply: '是的！他发现真正的海龟汤味道与他记忆中的截然不同。', progress: 35 },
          { keywords: ['人肉', '朋友', '同伴', '肉', '海难', '荒岛'], verdict: 'YES', reply: '是的，当年在荒岛上他喝下的其实是同伴牺牲自己留下的肉汤。', progress: 45 },
          { keywords: ['毒', '下毒', '过敏'], verdict: 'NO', reply: '不是，餐厅里的海龟汤没有任何毒素。', progress: 10 },
          { keywords: ['死', '自杀', '内疚', '崩溃'], verdict: 'YES', reply: '是的，得知挚友当年为救自己而献出生命与血肉后，他因巨大的悲痛与愧疚而崩溃。', progress: 25 }
        ]
      }
    ];

    // State
    const state = {
      soupType: 'clear',
      selectedTags: [],
      currentSoup: null,
      mode: 'ask', // 'ask' | 'guess'
      questionCount: 0,
      hintCount: 0,
      progress: 0,
      solved: false,
      unlockedClues: [],
      apiConfig: {
        baseUrl: 'https://api.deepseek.com/v1',
        apiKey: '',
        storyModel: 'deepseek-chat',
        judgeModel: 'deepseek-chat'
      },
      history: []
    };

    // Safe LocalStorage Helpers
    function loadSavedData() {
      try {
        const savedApi = localStorage.getItem('soup_detector_api');
        if (savedApi) {
          state.apiConfig = { ...state.apiConfig, ...JSON.parse(savedApi) };
        }
        const savedHist = localStorage.getItem('soup_detector_history');
        if (savedHist) {
          state.history = JSON.parse(savedHist);
        }
      } catch (e) {
        console.warn('Storage access restricted:', e);
      }
      updateEngineStatusUI();
    }

    function saveApiData() {
      try {
        localStorage.setItem('soup_detector_api', JSON.stringify(state.apiConfig));
      } catch (e) {}
      updateEngineStatusUI();
    }

    function recordHistoryItem(soup, questionsUsed) {
      const entry = {
        title: soup.title,
        tags: soup.tags,
        questions: questionsUsed,
        time: new Date().toLocaleString('zh-CN', { hour12: false })
      };
      state.history.unshift(entry);
      try {
        localStorage.setItem('soup_detector_history', JSON.stringify(state.history.slice(0, 20)));
      } catch (e) {}
    }

    function showToast(msg) {
      const container = document.getElementById('toastContainer');
      const div = document.createElement('div');
      div.className = 'toast-item';
      div.textContent = msg;
      container.appendChild(div);
      setTimeout(() => {
        div.remove();
      }, 3200);
    }

    function updateEngineStatusUI() {
      const dot = document.getElementById('engineStatusDot');
      const text = document.getElementById('engineStatusText');
      if (state.apiConfig.apiKey && state.apiConfig.apiKey.trim().length > 5) {
        dot.classList.remove('builtin');
        text.textContent = `LLM 在线 (${state.apiConfig.judgeModel})`;
      } else {
        dot.classList.add('builtin');
        text.textContent = '内置经典汤库 & 离线推理引擎';
      }
    }

    // LLM Story Generation or Built-in Selection
    async function startNewMystery() {
      const startBtn = document.getElementById('startMysteryBtn');
      startBtn.disabled = true;

      state.selectedTags = [];
      switchView('gameView');
      resetGamePanelState();

      if (state.apiConfig.apiKey && state.apiConfig.apiKey.trim().length > 5) {
        try {
          state.selectedTags = [...KEYWORD_POOL].sort(() => Math.random() - 0.5).slice(0, 3);
          const generated = await generateSoupWithLLM(state.selectedTags, state.soupType);
          state.currentSoup = generated;
          populateSoupUI(generated);
          appendHostMessage('GREETING', '汤面已生成！请开始提出可以用「是」、「否」或「无关」回答的问题，逐步揭开真相。');
          startBtn.disabled = false;
          return;
        } catch (err) {
          showToast('API 调用失败，已为您智能切换至内置精选海龟汤');
        }
      }

      // Fallback or offline selection matching soupType
      const matching = BUILTIN_SOUPS.find(s => s.type === state.soupType) || BUILTIN_SOUPS[0];
      state.currentSoup = { ...matching };
      populateSoupUI(state.currentSoup);
      appendHostMessage('GREETING', '已加载经典海龟汤谜题！请在下方的输入框中向主持人提问，或切换到「猜谜模式」还原真相。');
      startBtn.disabled = false;
    }

    async function generateSoupWithLLM(tags, soupType) {
      const styleMap = {
        clear: '清汤（注重严密逻辑推理、无血腥恐怖）',
        red: '红汤（悬疑惊悚、带有一点案件或生死反转）',
        black: '黑汤（诡异反常识、规则失效、出人意料的认知反转）'
      };
      const prompt = `你是一位顶级的海龟汤（情境推理游戏）创作者。请根据以下关键词创作一个逻辑严密、反转精彩的海龟汤谜题：
关键词：${tags.join('、')}
风格：${styleMap[soupType] || styleMap.clear}

请严格返回 JSON 格式（不要包含多余代码块说明），字段如下：
{
  "title": "四到八字标题",
  "surface": "汤面（给玩家看的悬疑现象，60-120字）",
  "bottom": "汤底（完整的故事真相，100-200字）",
  "hints": ["提示1", "提示2", "提示3"]
}`;

      const res = await fetch(`${state.apiConfig.baseUrl.replace(/\/$/, '')}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.apiConfig.apiKey.trim()}`
        },
        body: JSON.stringify({
          model: state.apiConfig.storyModel || 'deepseek-chat',
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.8
        })
      });

      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      const raw = data.choices[0].message.content;
      const jsonMatch = raw.match(/\{[\s\S]*\}/);
      const parsed = JSON.parse(jsonMatch ? jsonMatch[0] : raw);
      return {
        id: 'llm-' + Date.now(),
        type: soupType,
        title: parsed.title || '迷雾之汤',
        tags: [...tags],
        surface: parsed.surface,
        bottom: parsed.bottom,
        hints: parsed.hints || ['仔细思考人物动机与时间线。'],
        rules: []
      };
    }

    function resetGamePanelState() {
      state.questionCount = 0;
      state.hintCount = 0;
      state.progress = 0;
      state.solved = false;
      state.unlockedClues = [];
      document.getElementById('statQuestions').textContent = '0';
      document.getElementById('statProgress').textContent = '0%';
      document.getElementById('statHints').textContent = '0';
      document.getElementById('chatLog').innerHTML = '';
      document.getElementById('truthRevealBox').classList.remove('active');
      document.getElementById('cluesList').innerHTML = '<div style="font-size:0.78rem; color:var(--text-muted);">暂无线索，点击下方「获取提示」或通过「是」的回答解锁。</div>';
    }

    function populateSoupUI(soup) {
      const badgeMap = {
        clear: '清汤 · 逻辑推理',
        red: '红汤 · 悬疑惊悚',
        black: '黑汤 · 诡异反常识'
      };
      document.getElementById('activeSoupTypeBadge').textContent = badgeMap[soup.type] || '经典海龟汤';
      document.getElementById('activeSoupTitle').textContent = soup.title;
      document.getElementById('activeSoupSurface').textContent = soup.surface;
      document.getElementById('truthRevealText').textContent = soup.bottom;

      const tagsEl = document.getElementById('activeSoupTags');
      tagsEl.innerHTML = '';
      (soup.tags || []).forEach(t => {
        const span = document.createElement('span');
        span.className = 'tag-chip';
        span.style.cursor = 'default';
        span.textContent = `# ${t}`;
        tagsEl.appendChild(span);
      });
    }

    function appendUserMessage(text, isGuess) {
      const log = document.getElementById('chatLog');
      const row = document.createElement('div');
      row.className = 'msg-row user' + (isGuess ? ' guess-mode' : '');
      const bubble = document.createElement('div');
      bubble.className = 'msg-bubble';
      bubble.textContent = (isGuess ? '【真相推理】' : '') + text;
      row.appendChild(bubble);
      log.appendChild(row);
      log.scrollTop = log.scrollHeight;
    }

    function appendHostMessage(verdict, text) {
      const log = document.getElementById('chatLog');
      const row = document.createElement('div');
      row.className = 'msg-row host';
      const bubble = document.createElement('div');
      bubble.className = 'msg-bubble';

      const badgeLabels = {
        YES: { cls: 'verdict-YES', label: '是 (YES)' },
        NO: { cls: 'verdict-NO', label: '否 (NO)' },
        IRR: { cls: 'verdict-IRR', label: '无关 (IRRELEVANT)' },
        AMB: { cls: 'verdict-AMB', label: '部分正确' },
        HINT: { cls: 'verdict-HINT', label: '关键提示' }
      };

      if (badgeLabels[verdict]) {
        const b = document.createElement('span');
        b.className = `verdict-badge ${badgeLabels[verdict].cls}`;
        b.textContent = badgeLabels[verdict].label;
        bubble.appendChild(b);
      }

      const span = document.createElement('span');
      span.textContent = text;
      bubble.appendChild(span);

      row.appendChild(bubble);
      log.appendChild(row);
      log.scrollTop = log.scrollHeight;
    }

    function addUnlockedClue(clueText) {
      if (state.unlockedClues.includes(clueText)) return;
      state.unlockedClues.push(clueText);
      const list = document.getElementById('cluesList');
      if (state.unlockedClues.length === 1) list.innerHTML = '';
      const item = document.createElement('div');
      item.className = 'clue-item';
      item.textContent = `• ${clueText}`;
      list.appendChild(item);
    }

    async function handleUserSubmission(e) {
      e.preventDefault();
      const input = document.getElementById('userInput');
      const text = input.value.trim();
      if (!text || !state.currentSoup) return;
      input.value = '';

      const isGuess = state.mode === 'guess';
      appendUserMessage(text, isGuess);

      state.questionCount += 1;
      document.getElementById('statQuestions').textContent = String(state.questionCount);

      if (state.apiConfig.apiKey && state.apiConfig.apiKey.trim().length > 5) {
        try {
          await evaluateWithLLM(text, isGuess);
          return;
        } catch (err) {
          showToast('API 响应超时，已切换本地裁判判定');
        }
      }

      evaluateOffline(text, isGuess);
    }

    async function evaluateWithLLM(userText, isGuess) {
      const soup = state.currentSoup;
      const sysPrompt = isGuess
        ? `你是海龟汤裁判。汤面：${soup.surface}\n汤底真相：${soup.bottom}\n玩家提交了最终猜谜：${userText}\n请返回JSON：{"solved": true或false, "progressDelta": 0到60的整数, "reply": "简短点评说明玩家猜对了哪些核心点，或还差哪里"}`
        : `你是海龟汤裁判。汤面：${soup.surface}\n汤底真相：${soup.bottom}\n玩家提问：${userText}\n请判断并返回JSON：{"verdict": "YES"|"NO"|"IRR"|"AMB", "progressDelta": 0到25的整数, "reply": "简短的一句话补充回应"}`;

      const res = await fetch(`${state.apiConfig.baseUrl.replace(/\/$/, '')}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.apiConfig.apiKey.trim()}`
        },
        body: JSON.stringify({
          model: state.apiConfig.judgeModel || 'deepseek-chat',
          messages: [{ role: 'user', content: sysPrompt }],
          temperature: 0.3
        })
      });

      if (!res.ok) throw new Error('Judge API failed');
      const data = await res.json();
      const raw = data.choices[0].message.content;
      const match = raw.match(/\{[\s\S]*\}/);
      const parsed = JSON.parse(match ? match[0] : raw);

      state.progress = Math.min(100, state.progress + (Number(parsed.progressDelta) || 10));
      document.getElementById('statProgress').textContent = `${state.progress}%`;

      if (isGuess) {
        if (parsed.solved || state.progress >= 90) {
          triggerVictory(parsed.reply || '恭喜你！完美还原了海龟汤的全部核心真相！');
        } else {
          appendHostMessage('AMB', parsed.reply || '你的推理已经接近部分事实，但还有关键转折尚未揭晓。');
        }
      } else {
        const v = parsed.verdict || 'IRR';
        appendHostMessage(v, parsed.reply || '');
        if (v === 'YES') addUnlockedClue(userText);
      }
    }

    function evaluateOffline(userText, isGuess) {
      const soup = state.currentSoup;
      if (isGuess) {
        // Check keyword overlap with bottom truth
        const rules = soup.rules || [];
        let hits = 0;
        rules.forEach(r => {
          if (r.verdict === 'YES' && r.keywords.some(k => userText.includes(k))) {
            hits += 1;
          }
        });

        if (hits >= 2 || userText.length >= 18 || state.progress >= 75) {
          state.progress = 100;
          document.getElementById('statProgress').textContent = '100%';
          triggerVictory('太精彩了！你的推理切中了故事的核心脉络，真相水落石出！');
        } else {
          state.progress = Math.min(85, state.progress + 15);
          document.getElementById('statProgress').textContent = `${state.progress}%`;
          appendHostMessage('AMB', '你的猜想触及了部分表象，但核心动机或关键道具还未完全命中，建议再多提几个是非问题！');
        }
        return;
      }

      const rules = soup.rules || [];
      for (const rule of rules) {
        if (rule.keywords.some(k => userText.includes(k))) {
          state.progress = Math.min(95, state.progress + (rule.progress || 15));
          document.getElementById('statProgress').textContent = `${state.progress}%`;
          appendHostMessage(rule.verdict, rule.reply);
          if (rule.verdict === 'YES') {
            addUnlockedClue(rule.reply);
          }
          return;
        }
      }

      state.progress = Math.min(90, state.progress + 5);
      document.getElementById('statProgress').textContent = `${state.progress}%`;
      appendHostMessage('IRR', '这个问题与案件的核心反转关联不大，试试从人物身份、随身物品或环境限制入手提问。');
    }

    function triggerVictory(congratsText) {
      state.solved = true;
      appendHostMessage('YES', congratsText);
      document.getElementById('truthRevealBox').classList.add('active');
      recordHistoryItem(state.currentSoup, state.questionCount);
      launchConfetti();
    }

    // Confetti Celebration Canvas
    function launchConfetti() {
      const canvas = document.getElementById('confetti');
      const ctx = canvas.getContext('2d');
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      const pieces = Array.from({ length: 90 }, () => ({
        x: Math.random() * canvas.width,
        y: -20 - Math.random() * 200,
        size: 6 + Math.random() * 6,
        vx: (Math.random() - 0.5) * 4,
        vy: 2.5 + Math.random() * 4,
        color: ['#38bdf8', '#4ade80', '#f59e0b', '#a78bfa', '#f87171'][Math.floor(Math.random() * 5)],
        rot: Math.random() * Math.PI
      }));

      let frames = 0;
      function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        pieces.forEach(p => {
          p.x += p.vx;
          p.y += p.vy;
          p.rot += 0.06;
          ctx.save();
          ctx.translate(p.x, p.y);
          ctx.rotate(p.rot);
          ctx.fillStyle = p.color;
          ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
          ctx.restore();
        });
        frames += 1;
        if (frames < 160) {
          requestAnimationFrame(draw);
        } else {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      }
      requestAnimationFrame(draw);
    }

    function switchView(viewId) {
      document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
      document.getElementById(viewId).classList.add('active');
    }

    function setDeductionMode(mode) {
      state.mode = mode;
      const askTab = document.getElementById('modeAskTab');
      const guessTab = document.getElementById('modeGuessTab');
      const input = document.getElementById('userInput');
      const btn = document.getElementById('submitActionBtn');
      const btnText = document.getElementById('submitBtnText');
      const helper = document.getElementById('modeHelperText');

      if (mode === 'ask') {
        askTab.classList.add('active');
        guessTab.classList.remove('active');
        input.classList.remove('guess-active');
        btn.classList.remove('guess-mode');
        input.placeholder = '输入你的是非提问，例如：他是自愿喝下这碗汤的吗？';
        btnText.textContent = '提问';
        helper.textContent = '主持人仅以「是 / 否 / 无关」回答';
      } else {
        guessTab.classList.add('active');
        askTab.classList.remove('active');
        input.classList.add('guess-active');
        btn.classList.add('guess-mode');
        input.placeholder = '输入你还原的完整故事真相，提交结案...';
        btnText.textContent = '提交真相';
        helper.textContent = '阐述故事起因、经过与结局以揭晓汤底';
      }
    }

    function renderHistoryModal() {
      const container = document.getElementById('historyListContainer');
      if (!state.history.length) {
        container.innerHTML = '<p style="font-size:0.84rem; color:var(--text-muted); text-align:center; padding:1.5rem 0;">暂无通关记录，快去解开第一碗海龟汤吧！</p>';
        return;
      }
      container.innerHTML = '';
      state.history.forEach(item => {
        const div = document.createElement('div');
        div.style.cssText = 'padding:0.75rem 1rem; border-radius:12px; background:rgba(30,41,59,0.7); border:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;';
        div.innerHTML = `
          <div>
            <div style="font-weight:600; font-size:0.9rem;">${item.title}</div>
            <div style="font-size:0.74rem; color:var(--text-muted); margin-top:0.2rem;">关键词：${(item.tags || []).join(' / ')} · ${item.time}</div>
          </div>
          <span class="verdict-badge verdict-YES">${item.questions} 次提问通关</span>
        `;
        container.appendChild(div);
      });
    }

    // Event Wiring
    window.addEventListener('DOMContentLoaded', () => {
      loadSavedData();

      document.getElementById('brandHomeBtn').addEventListener('click', () => switchView('lobbyView'));
      document.getElementById('backToLobbyBtn').addEventListener('click', () => switchView('lobbyView'));

      // Soup Type Selector
      const soupTypeNames = {
        clear: '清汤 · 逻辑推理',
        red: '红汤 · 悬疑惊悚',
        black: '黑汤 · 诡异反常识'
      };
      const soupShortNames = { clear: '清汤', red: '红汤', black: '黑汤' };

      document.querySelectorAll('.soup-type-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          document.querySelectorAll('.soup-type-btn').forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-pressed', 'false');
          });
          btn.classList.add('active');
          btn.setAttribute('aria-pressed', 'true');
          state.soupType = btn.getAttribute('data-soup-type');
          document.body.dataset.soupTheme = state.soupType;
          document.getElementById('selectedSoupName').textContent = soupTypeNames[state.soupType];
          document.getElementById('startBtnText').textContent = `以${soupShortNames[state.soupType]}开始推理`;
        });
      });

      document.getElementById('startMysteryBtn').addEventListener('click', startNewMystery);

      document.getElementById('modeAskTab').addEventListener('click', () => setDeductionMode('ask'));
      document.getElementById('modeGuessTab').addEventListener('click', () => setDeductionMode('guess'));
      document.getElementById('deductionForm').addEventListener('submit', handleUserSubmission);

      document.querySelectorAll('.quick-q-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          setDeductionMode('ask');
          document.getElementById('userInput').value = btn.getAttribute('data-q');
          document.getElementById('deductionForm').requestSubmit();
        });
      });

      document.getElementById('requestHintBtn').addEventListener('click', () => {
        if (!state.currentSoup) return;
        const hints = state.currentSoup.hints || ['仔细排查故事中隐含的物理限制条件。'];
        const hintText = hints[state.hintCount % hints.length];
        state.hintCount += 1;
        document.getElementById('statHints').textContent = String(state.hintCount);
        appendHostMessage('HINT', hintText);
        addUnlockedClue(hintText);
      });

      document.getElementById('revealTruthBtn').addEventListener('click', () => {
        if (!state.currentSoup) return;
        document.getElementById('truthRevealBox').classList.add('active');
        appendHostMessage('HINT', '已为你揭晓完整汤底，请查看左侧「完整汤底（真相还原）」面板。');
      });

      // API Modal
      const apiModal = document.getElementById('apiModal');
      document.getElementById('openApiModalBtn').addEventListener('click', () => {
        document.getElementById('apiBaseUrlInput').value = state.apiConfig.baseUrl;
        document.getElementById('apiKeyInput').value = state.apiConfig.apiKey;
        document.getElementById('storyModelInput').value = state.apiConfig.storyModel;
        document.getElementById('judgeModelInput').value = state.apiConfig.judgeModel;
        apiModal.classList.add('open');
      });

      document.getElementById('closeApiModalBtn').addEventListener('click', () => apiModal.classList.remove('open'));

      document.querySelectorAll('.preset-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          document.getElementById('apiBaseUrlInput').value = chip.getAttribute('data-base');
          document.getElementById('storyModelInput').value = chip.getAttribute('data-story');
          document.getElementById('judgeModelInput').value = chip.getAttribute('data-judge');
        });
      });

      document.getElementById('saveApiConfigBtn').addEventListener('click', () => {
        state.apiConfig.baseUrl = document.getElementById('apiBaseUrlInput').value.trim() || 'https://api.deepseek.com/v1';
        state.apiConfig.apiKey = document.getElementById('apiKeyInput').value.trim();
        state.apiConfig.storyModel = document.getElementById('storyModelInput').value.trim() || 'deepseek-chat';
        state.apiConfig.judgeModel = document.getElementById('judgeModelInput').value.trim() || 'deepseek-chat';
        saveApiData();
        apiModal.classList.remove('open');
        showToast('API 配置已保存并生效');
      });

      document.getElementById('clearApiConfigBtn').addEventListener('click', () => {
        state.apiConfig.apiKey = '';
        document.getElementById('apiKeyInput').value = '';
        saveApiData();
        apiModal.classList.remove('open');
        showToast('已切换至内置离线海龟汤引擎');
      });

      // History Modal
      const historyModal = document.getElementById('historyModal');
      document.getElementById('openHistoryBtn').addEventListener('click', () => {
        renderHistoryModal();
        historyModal.classList.add('open');
      });
      document.getElementById('closeHistoryModalBtn').addEventListener('click', () => historyModal.classList.remove('open'));
    });
