/**
 * VocabMaster - 前端 JS 逻辑
 * 三轮记忆法 + AI 功能 + 词根词缀 + WordReview 融合
 */

// ========================================================================
// ===== 工具函数 =====
// ========================================================================

/** API 请求封装 */
async function api(path, options = {}) {
  const url = path.startsWith('/') ? path : `/api/${path}`;
  const isFormData = options.body instanceof FormData;
  const headers = isFormData ? {} : { 'Content-Type': 'application/json' };
  const resp = await fetch(url, { headers, ...options });
  
  // 处理 401 未授权错误
  if (resp.status === 401) {
    window.location.href = '/login';
    throw new Error('未登录，请先登录');
  }
  
  if (!resp.ok) {
    let err;
    try { err = await resp.json(); } catch { err = await resp.text(); }
    throw new Error(err.detail || err.message || err || `API Error ${resp.status}`);
  }
  return resp.json();
}

/** 发音 */
function speakWord(word, rate) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(word);
  u.lang = 'en-US'; u.rate = rate || 0.85; u.pitch = 1;
  window.speechSynthesis.speak(u);
  return u;
}

/** Toast */
function showToast(msg, duration) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.className = 'toast'; t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), duration || 2500);
}

/** HTML 转义 */
function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str; return d.innerHTML;
}

/** 格式化释义（常考释义高亮） */
function formatDefinition(defCn, highFreqDefs) {
  if (!highFreqDefs) return escapeHtml(defCn);
  const highFreqs = highFreqDefs.split(';').map(s => s.trim()).filter(Boolean);
  if (highFreqs.length === 0) return escapeHtml(defCn);
  let result = escapeHtml(defCn);
  highFreqs.forEach(hf => {
    const escaped = escapeHtml(hf);
    result = result.replace(escaped, `<span class="high-freq-def">${escaped}</span>`);
  });
  return result;
}

/** today */
function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** 例句中关键词高亮 */
function highlightWordInSentence(sentence, word) {
  if (!sentence || !word) return escapeHtml(sentence);
  // Build regex matching word and its common inflections
  const base = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = new RegExp(`(${base}(?:s|es|ed|ing|d|er|est|ly|tion|ment|ness|ity|ous|ive|al|ful|less|able|ible)?)`, 'gi');
  return escapeHtml(sentence).replace(new RegExp(`(${base}(?:s|es|ed|ing|d|er|est|ly|tion|ment|ness|ity|ous|ive|al|ful|less|able|ible)?)`, 'gi'), '<span class="highlight-word">$1</span>');
}

/** 词根拆解可视化渲染 */
function renderRootVisualization(note, rootText, rootMeaning) {
  let html = '';
  // Priority: note field with colorized root decomposition
  if (note && note.includes('=')) {
    html += '<div class="root-viz-section">';
    html += '<div class="root-viz-title">🧬 词根拆解</div>';
    html += '<div class="root-viz-parts">';
    const lines = note.split('\n').filter(l => l.trim());
    lines.forEach(line => {
      if (line.includes('=')) {
        const [part, meaning] = line.split('=').map(s => s.trim());
        // Detect prefix vs stem
        const isPrefix = /^(un|in|im|dis|mis|pre|re|ab|ad|af|ag|al|ap|as|at|con|com|de|ex|sub|sur|trans|inter|anti|contra|per|pro|co|col|di)$/i.test(part);
        html += `<span class="root-part ${isPrefix ? 'prefix' : 'stem'}">${escapeHtml(part)}</span>`;
        if (meaning) html += `<span class="root-part meaning">${escapeHtml(meaning)}</span>`;
      } else {
        // Suffix or standalone stem
        const isSuffix = /^(tion|sion|ment|ness|ity|ous|ive|al|ful|less|able|ible|ly|er|est|ed|ing|ate|ize|ise|fy|ent|ant|ence|ance|ic|ical|ous|ious|eous|uous|ary|ory|dom|ship|hood|ness|less|ish|like|ward|wards|wise|en|ate)$/.test(line.trim().toLowerCase());
        html += `<span class="root-part ${isSuffix ? 'suffix' : 'stem'}">${escapeHtml(line.trim())}</span>`;
      }
    });
    html += '</div></div>';
    return html;
  }
  // Fallback: simple root display
  if (rootText) {
    html += `<div class="root-viz-section">
      <div class="root-viz-title">🧬 词根解析</div>
      <div class="root-viz-parts">
        <span class="root-part stem">${escapeHtml(rootText)}</span>
        <span class="root-part meaning">${escapeHtml(rootMeaning)}</span>
      </div>
    </div>`;
  }
  return html;
}

/** 生成单词卡片的通用增强内容（助记法、相关词、笔记、标签、记忆历史） */
function renderWordEnhancements(w, progress, showFlagBtns = true) {
  let html = '';

  // 助记法
  if (w.mnemonic) {
    html += `<div class="mnemonic-section">
      <div class="mnemonic-title">💡 助记法</div>
      <div class="mnemonic-text">${escapeHtml(w.mnemonic)}</div>
    </div>`;
  }

  // 词根拆解可视化
  html += renderRootVisualization(w.note, w.root_text, w.root_meaning);

  // 相关词
  if (w.synonym || w.antonym || w.derivative) {
    html += '<div class="related-words-section"><div class="related-words-title">🔗 相关词</div>';
    if (w.synonym) html += `<div class="related-words-row"><span class="rw-label">近义</span>${w.synonym.split(',').map(s => `<span class="related-word-tag">${escapeHtml(s.trim())}</span>`).join('')}</div>`;
    if (w.antonym) html += `<div class="related-words-row"><span class="rw-label">反义</span>${w.antonym.split(',').map(s => `<span class="related-word-tag">${escapeHtml(s.trim())}</span>`).join('')}</div>`;
    if (w.derivative) html += `<div class="related-words-row"><span class="rw-label">派生</span>${w.derivative.split(',').map(s => `<span class="related-word-tag">${escapeHtml(s.trim())}</span>`).join('')}</div>`;
    html += '</div>';
  }

  // 记忆历史趋势图
  const history = progress?.history || '';
  if (history && history.length > 0) {
    const last20 = typeof history === 'string' ? history.slice(-20) : String(history).slice(-20);
    html += '<div class="history-chart-section">';
    html += '<div class="history-chart-title">📈 记忆历史（最近20次）</div>';
    html += '<div class="history-chart">';
    for (let i = 0; i < last20.length; i++) {
      const isRemembered = last20[i] === '1';
      html += `<div class="h-bar ${isRemembered ? 'remembered' : 'forgotten'}" style="height:${isRemembered ? '100%' : '40%'}"></div>`;
    }
    html += '</div></div>';
  }

  // 笔记
  const userNote = progress?.user_note || '';
  html += `<div class="note-section" id="note-section-${w.id}" onclick="event.stopPropagation();openNoteEditor(${w.id})">
    <div class="note-content">${userNote ? escapeHtml(userNote) : '<span class="note-placeholder">点击此处添加笔记...</span>'}</div>
    <button class="note-edit-btn" onclick="event.stopPropagation();openNoteEditor(${w.id})" title="编辑笔记">✏️</button>
  </div>`;

  // 标签按钮
  if (showFlagBtns) {
    const flag = progress?.flag ?? 0;
    html += `<div class="flag-btns" id="flag-btns-${w.id}">
      <button class="flag-btn flag-hard ${flag === -1 ? 'active' : ''}" onclick="setWordFlag(${w.id},-1)">⭐ 重难</button>
      <button class="flag-btn flag-normal ${flag === 0 ? 'active' : ''}" onclick="setWordFlag(${w.id},0)">默认</button>
      <button class="flag-btn flag-mastered ${flag === 1 ? 'active' : ''}" onclick="setWordFlag(${w.id},1)">🟢 已掌握</button>
      <button class="flag-btn flag-familiar ${flag === 2 ? 'active' : ''}" onclick="setWordFlag(${w.id},2)">☁ 很熟悉</button>
      <button class="flag-btn flag-easy ${flag === 10 ? 'active' : ''}" onclick="setWordFlag(${w.id},10)">✅ 太简单</button>
    </div>`;
  }

  return html;
}

// ========================================================================
// ===== 导航 =====
// ========================================================================
let currentPage = 'dashboard';

function navigateTo(page) {
  if (page === 'learn') { startLearning(); return; }
  if (page === 'more') { document.getElementById('more-menu').classList.add('show'); return; }

  currentPage = page;
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById(`page-${page}`);
  if (el) el.classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');

  if (page === 'dashboard') renderDashboard();
  else if (page === 'review') renderReviewModes();
  else if (page === 'books') renderBooks();
  else if (page === 'roots') renderRoots();
  else if (page === 'stats') renderStats();
  else if (page === 'cloze') renderClozePage();
  else if (page === 'writing') renderWritingPage();
  else if (page === 'calendar') renderEbbinghausCalendar();
}

function closeModal(id) { document.getElementById(id).classList.remove('show'); }

// ========================================================================
// ===== 仪表盘 =====
// ========================================================================
async function renderDashboard() {
  try {
    const task = await api('study/today');
    const checkin = await api('checkin/status');

    const hour = new Date().getHours();
    let greeting = '今天也要加油哦 💪';
    if (hour < 6) greeting = '夜深了，注意休息 🌙';
    else if (hour < 12) greeting = '早安，新的一天开始了 ☀️';
    else if (hour < 18) greeting = '下午好，继续加油 🌤️';
    else greeting = '晚上好，温故知新 🌙';
    document.getElementById('greeting-text').textContent = greeting;

    document.getElementById('stat-new').textContent = task.today_new;
    document.getElementById('stat-review').textContent = task.today_review;
    document.getElementById('stat-total').textContent = task.total_learned;
    document.getElementById('stat-mastered').textContent = task.total_mastered;

    document.getElementById('task-new-count').textContent = task.new_words_remaining;
    document.getElementById('task-new-desc').textContent =
      task.new_words_remaining > 0 ? `今日还需学习 ${task.new_words_remaining} 个新词` : '今日新词已学完 🎉';
    document.getElementById('task-review-count').textContent = task.review_words_remaining;
    document.getElementById('task-review-desc').textContent =
      task.review_words_remaining > 0 ? `有 ${task.review_words_remaining} 个单词待复习` : '暂无待复习 🎉';

    const checkinBtn = document.getElementById('checkin-btn');
    const checkinText = document.getElementById('checkin-text');
    const checkinStatus = document.getElementById('checkin-status');
    if (checkin.checked) {
      checkinBtn.classList.add('checked');
      checkinText.textContent = '已打卡';
      checkinStatus.textContent = `今日已打卡 · 新学${checkin.words_learned}词 · 复习${checkin.words_reviewed}词`;
    } else {
      checkinBtn.classList.remove('checked');
      checkinText.textContent = '打卡';
      checkinStatus.textContent = (checkin.words_learned > 0 || checkin.words_reviewed > 0) ? '完成学习后记得打卡哦' : '今日尚未打卡';
    }

    document.getElementById('streak-count').textContent = task.streak;

    // 三轮进度
    document.getElementById('stage1-cnt').textContent = task.stage1_count || 0;
    document.getElementById('stage2-cnt').textContent = task.stage2_count || 0;
    document.getElementById('stage3-cnt').textContent = task.stage3_count || 0;
    document.getElementById('mastered-cnt').textContent = task.total_mastered || 0;

    // 每日新词上限
    const limitData = await api('study/daily-limit');
    document.getElementById('daily-limit-input').value = limitData.daily_new_words_limit;

    // 复习计划
    loadReviewPlan();

    // 双记忆率
    loadMemoryRates();

    // 标签统计
    loadFlagStats();

    // 昨日重现数量
    loadYesterdayReviewCount();
  } catch (e) {
    console.error('渲染仪表盘失败:', e);
  }
}

async function loadMemoryRates() {
  try {
    const rates = await api('words/memory-rates');
    document.getElementById('history-rate-bar').style.width = rates.history_rate + '%';
    document.getElementById('history-rate-val').textContent = rates.history_rate + '%';
    document.getElementById('recent-rate-bar').style.width = rates.recent_rate + '%';
    document.getElementById('recent-rate-val').textContent = rates.recent_rate + '%';
  } catch (e) { console.error(e); }
}

async function loadFlagStats() {
  try {
    const stats = await api('words/flag-stats');
    const grid = document.getElementById('flag-stats-grid');
    grid.innerHTML = `
      <div class="flag-stat-item"><span class="flag-icon">⭐</span>重难 <span class="flag-count">${stats.hard_count}</span></div>
      <div class="flag-stat-item"><span class="flag-icon">📝</span>默认 <span class="flag-count">${stats.normal_count}</span></div>
      <div class="flag-stat-item"><span class="flag-icon">🟢</span>已掌握 <span class="flag-count">${stats.mastered_count}</span></div>
      <div class="flag-stat-item"><span class="flag-icon">☁️</span>很熟悉 <span class="flag-count">${stats.familiar_count}</span></div>
      <div class="flag-stat-item"><span class="flag-icon">✅</span>太简单 <span class="flag-count">${stats.easy_count}</span></div>
    `;
  } catch (e) { console.error(e); }
}

async function loadYesterdayReviewCount() {
  try {
    const data = await api('review/yesterday-review');
    const count = data.total || 0;
    document.getElementById('task-yesterday-count').textContent = count;
    document.getElementById('task-yesterday-desc').textContent = count > 0 ? `${count} 个遗忘词汇待巩固` : '暂无遗忘词汇';
  } catch (e) { console.error(e); }
}

async function loadReviewPlan() {
  try {
    const plan = await api('review/plan');
    const listDiv = document.getElementById('review-plan-list');
    const card = document.getElementById('review-plan-card');
    if (plan.items.length === 0) {
      card.style.display = 'none';
      return;
    }
    card.style.display = 'block';
    listDiv.innerHTML = plan.items.slice(0, 10).map(item => `
      <div class="review-plan-item">
        <span class="urgency ${item.urgency}">${item.urgency === 'overdue' ? '逾期' : item.urgency === 'urgent' ? '紧急' : '正常'}</span>
        <span class="word-text">${escapeHtml(item.word)}</span>
        <span class="def-text">${escapeHtml(item.definition_cn)}</span>
      </div>
    `).join('');
  } catch (e) { console.error(e); }
}

async function saveDailyLimit() {
  const val = parseInt(document.getElementById('daily-limit-input').value) || 15;
  try {
    await api('study/daily-limit', { method: 'POST', body: JSON.stringify({ daily_new_words_limit: val }) });
    showToast('每日新词上限已保存');
  } catch (e) { showToast('保存失败'); }
}

async function handleCheckin() {
  try {
    const result = await api('checkin', { method: 'POST' });
    if (result.already) { showToast('今日已打卡 ✅'); }
    else {
      const btn = document.getElementById('checkin-btn');
      btn.classList.add('checked'); btn.style.transform = 'scale(1.15)';
      setTimeout(() => btn.style.transform = '', 300);
      showToast('打卡成功！继续加油 🔥');
    }
    renderDashboard();
  } catch (e) { showToast('打卡失败'); }
}

// ========================================================================
// ===== 学习流程（三轮记忆法） =====
// ========================================================================
let learnQueue = [];
let learnIndex = 0;
let learnFlipped = false;
let learnTodayNew = 0;
let learnStage = 1;  // 1=第一轮, 2=第二轮复习, 3=第三轮验证
let learnWordScores = {};  // word_id -> {correct: n, total: n, passed: bool}
let LEARN_PASS_THRESHOLD = 0.7;  // 70%正确率达标（可从设置中加载）

async function startLearning() {
  try {
    // 加载学习模式阈值设置
    try {
      const settings = await api('stats/settings');
      if (settings.learn_pass_threshold) {
        LEARN_PASS_THRESHOLD = settings.learn_pass_threshold;
      }
    } catch (e) { console.error('加载阈值设置失败:', e); }

    const task = await api('study/today');
    if (task.new_words_remaining <= 0) {
      const reviewNext = await api('study/review-next');
      if (reviewNext.word) {
        showToast('新词已学完，进入复习 🔄');
        startReviewStudy();
        return;
      }
      showToast('今日任务已完成！🎉');
      return;
    }

    const settings = await api('stats/settings');
    const allWords = await api(`books/${settings.current_book_id}/words`);
    learnQueue = allWords.slice(0, task.new_words_remaining);

    if (learnQueue.length === 0) { showToast('今日新词已学完！'); return; }

    learnIndex = 0; learnFlipped = false; learnTodayNew = 0; learnStage = 1;
    learnWordScores = {};  // 重置单词评分
    currentPage = 'learn';
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-learn').classList.add('active');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector('.nav-item[data-page="learn"]')?.classList.add('active');
    renderLearnCard();
  } catch (e) {
    console.error('开始学习失败:', e);
    showToast('获取学习数据失败');
  }
}

async function startReviewStudy() {
  try {
    learnQueue = [];
    learnIndex = 0;
    learnStage = 2;

    const nextWord = await api('study/review-next');
    if (nextWord.word) {
      learnQueue = [nextWord.word];
      learnStage = nextWord.stage;
      learnFlipped = false;

      currentPage = 'learn';
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.getElementById('page-learn').classList.add('active');

      renderReviewStudyCard(nextWord);
    }
  } catch (e) {
    console.error(e);
    showToast('获取复习数据失败');
  }
}

function renderLearnCard() {
  if (learnIndex >= learnQueue.length) { finishLearning(); return; }

  const w = learnQueue[learnIndex];
  learnFlipped = false;
  const total = learnQueue.length;

  document.getElementById('learn-progress').textContent = `${learnIndex + 1} / ${total}`;
  document.getElementById('learn-progress-bar').style.width = `${((learnIndex + 1) / total) * 100}%`;

  const badge = document.getElementById('learn-stage-badge');
  badge.textContent = '第一轮 · 初次学习';
  badge.className = 'learn-stage-badge stage1';

  const enhancements = renderWordEnhancements(w, null, false);

  // 【新增】智能助记按钮
  const crawlerBtnHtml = `
    <div style="margin-top:12px;text-align:center">
      <button type="button" id="crawler-btn-${w.id}" class="btn btn-ghost btn-sm" onclick="event.preventDefault(); event.stopPropagation(); fetchSmartMnemonic('${escapeHtml(w.word)}', ${w.id})">
        ✨ 一键获取全网助记
      </button>
    </div>`;

  // 第一轮：提供多个选项让用户评估掌握程度
  const wordId = w.id;
  const score = learnWordScores[wordId] || {correct: 0, total: 0};
  const accuracy = score.total > 0 ? Math.round((score.correct / score.total) * 100) : 0;
  const accuracyBadge = score.total > 0 ? `
    <div style="margin-top:12px;padding:8px 12px;background:var(--bg-secondary);border-radius:8px;text-align:center;font-size:0.85rem;color:var(--text-secondary)">
      📊 正确率: ${accuracy}% (${score.correct}/${score.total})
    </div>` : '';
  
  const container = document.getElementById('learn-card-container');
  container.innerHTML = `
    <div class="word-card" id="learn-word-card" onclick="flipLearnCard()">
      <div class="front">
        <div class="word-main">
          <div class="word-text">${escapeHtml(w.word)}</div>
          <div class="word-phonetic">${escapeHtml(w.phonetic)}</div>
          <span class="word-pos">${escapeHtml(w.part_of_speech)}</span>
          <div><button class="word-speak-btn" onclick="event.stopPropagation(); speakWord('${escapeHtml(w.word)}')">🔊</button></div>
        </div>
        <div class="tap-hint">👆 点击翻转查看释义</div>
      </div>
      <div class="back">
        <div class="word-main">
          <div class="word-text">${escapeHtml(w.word)}</div>
          <div class="word-phonetic">${escapeHtml(w.phonetic)}</div>
        </div>
        <div class="word-detail">
          <div class="word-definition">${formatDefinition(w.definition_cn, w.high_freq_defs)}</div>
          <div class="word-example">
            <div class="en">${highlightWordInSentence(w.example_sentence, w.word)}</div>
            <div class="zh">${escapeHtml(w.example_translation)}</div>
          </div>
          ${enhancements}
          ${accuracyBadge}
          ${crawlerBtnHtml}
        </div>
        <div class="tap-hint">👆 点击翻转回正面</div>
      </div>
    </div>`;

  setTimeout(() => speakWord(w.word, 0.8), 300);
  
  // 渲染底部按钮
  document.getElementById('learn-actions-container').innerHTML = `
    <div class="learn-actions">
      <button class="btn btn-danger" onclick="markStage1Done(1)">😟 忘了</button>
      <button class="btn btn-warning" onclick="markStage1Done(3)">🤔 模糊</button>
      <button class="btn btn-success" onclick="markStage1Done(5)">😊 记住了</button>
    </div>`;
}

function flipLearnCard() {
  const card = document.getElementById('learn-word-card');
  if (!card) return;
  learnFlipped = !learnFlipped;
  card.classList.toggle('flipped', learnFlipped);
}

async function markStage1Done(rating) {
  const w = learnQueue[learnIndex];
  const wordId = w.id;
  
  // 初始化评分记录
  if (!learnWordScores[wordId]) {
    learnWordScores[wordId] = {correct: 0, total: 0, passed: false};
  }
  
  // 更新评分
  learnWordScores[wordId].total++;
  if (rating >= 4) {
    learnWordScores[wordId].correct++;
  }
  
  const score = learnWordScores[wordId];
  const accuracy = score.correct / score.total;
  
  // 判断是否达标
  if (accuracy >= LEARN_PASS_THRESHOLD && score.total >= 2) {
    score.passed = true;
    // 提交到后端
    try {
      await api('study/submit', { method: 'POST', body: JSON.stringify({ word_id: wordId, rating: rating, action: 'study' }) });
    } catch (e) { console.error(e); }
    learnTodayNew++;
    learnIndex++;
  } else if (score.total >= 2) {
    // 未达标，从当前位置移除并打乱插入到后面
    learnQueue.splice(learnIndex, 1);  // 先移除当前单词
    
    // 计算剩余未学习的单词数量
    const remainingWords = learnQueue.length - learnIndex;
    
    if (remainingWords >= 3) {
      // 有足够的单词，插入到至少3个单词之后的随机位置
      const minGap = Math.min(3, remainingWords);
      const maxGap = Math.min(remainingWords, 6);
      const insertPos = learnIndex + minGap + Math.floor(Math.random() * (maxGap - minGap + 1));
      learnQueue.splice(Math.min(insertPos, learnQueue.length), 0, w);
    } else if (remainingWords > 0) {
      // 单词不够，插入到队列末尾
      learnQueue.push(w);
    } else {
      // 没有其他单词了，只能放到末尾（下一个就会出现）
      learnQueue.push(w);
    }
    
    // 提示
    showToast(`"${w.word}" 还需巩固，稍后再次出现`, 2000);
  }
  
  // 如果队列中该单词次数过多（最多5次），则强制继续下一个
  if (!score.passed && score.total >= 5) {
    // 提交到后端
    try {
      await api('study/submit', { method: 'POST', body: JSON.stringify({ word_id: wordId, rating: rating, action: 'study' }) });
    } catch (e) { console.error(e); }
    learnTodayNew++;  // 超过5次也算完成
    showToast(`"${w.word}" 已学习5次，进入下一轮复习`, 2000);
    learnIndex++;
  }
  
  renderLearnCard();
}

// 第二/三轮复习卡
function renderReviewStudyCard(data) {
  const w = data.word;
  const progress = data.progress || {};
  const stage = data.stage || 2;
  learnStage = stage;

  const badge = document.getElementById('learn-stage-badge');
  if (stage === 2) {
    badge.textContent = '第二轮 · 间隔复习';
    badge.className = 'learn-stage-badge stage2';
  } else {
    badge.textContent = '第三轮 · 输出验证';
    badge.className = 'learn-stage-badge stage3';
  }

  document.getElementById('learn-progress').textContent = `复习`;
  document.getElementById('learn-progress-bar').style.width = '50%';

  const enhancements = renderWordEnhancements(w, progress);

  const container = document.getElementById('learn-card-container');

  if (stage === 2) {
    container.innerHTML = `
      <div class="word-card" id="learn-word-card" onclick="flipLearnCard()">
        <div class="front">
          <div class="word-main">
            <div class="word-text">${escapeHtml(w.word)}</div>
            <div class="word-phonetic">${escapeHtml(w.phonetic)}</div>
            <button class="word-speak-btn" onclick="event.stopPropagation(); speakWord('${escapeHtml(w.word)}')">🔊</button>
          </div>
          <div class="tap-hint">👆 想想释义，然后点击翻转</div>
        </div>
        <div class="back">
          <div class="word-main">
            <div class="word-text">${escapeHtml(w.word)}</div>
            <div class="word-phonetic">${escapeHtml(w.phonetic)}</div>
          </div>
          <div class="word-detail">
            <div class="word-definition">${formatDefinition(w.definition_cn, w.high_freq_defs)}</div>
            <div class="word-example">
              <div class="en">${highlightWordInSentence(w.example_sentence, w.word)}</div>
              <div class="zh">${escapeHtml(w.example_translation)}</div>
            </div>
            ${enhancements}
          </div>
        </div>
      </div>`;

    document.getElementById('learn-actions-container').innerHTML = `
      <div class="learn-actions">
        <button class="btn btn-danger" onclick="submitReviewStudy(1)">😟 忘了</button>
        <button class="btn btn-warning" onclick="submitReviewStudy(3)">🤔 模糊</button>
        <button class="btn btn-success" onclick="submitReviewStudy(5)">😊 记住了</button>
      </div>`;
  } else {
    container.innerHTML = `
      <div class="review-card">
        <div class="review-question" style="flex-direction:column">
          <div style="font-size:.85rem;color:var(--text-secondary)">根据释义拼写单词</div>
          <div style="font-size:1.1rem;font-weight:600;margin-top:6px">${escapeHtml(w.part_of_speech)} ${escapeHtml(w.definition_cn)}</div>
        </div>
        <div class="spelling-input">
          <input type="text" id="stage3-answer" placeholder="输入单词..." autocomplete="off" autocapitalize="off" spellcheck="false">
        </div>
        <div id="stage3-feedback"></div>
      </div>`;

    document.getElementById('learn-actions-container').innerHTML = `
      <button class="btn btn-primary btn-block" onclick="checkStage3Answer()">确认</button>`;

    setTimeout(() => {
      const input = document.getElementById('stage3-answer');
      if (input) { input.focus(); input.addEventListener('keydown', e => { if (e.key === 'Enter') checkStage3Answer(); }); }
    }, 100);
  }

  setTimeout(() => speakWord(w.word, 0.8), 300);
}

async function submitReviewStudy(rating) {
  const w = learnQueue[0];
  try {
    await api('study/submit', { method: 'POST', body: JSON.stringify({ word_id: w.id, rating: rating, action: 'review' }) });
  } catch (e) { console.error(e); }

  try {
    const nextWord = await api('study/review-next');
    if (nextWord.word) {
      learnQueue = [nextWord.word];
      learnStage = nextWord.stage;
      renderReviewStudyCard(nextWord);
    } else {
      finishLearning();
    }
  } catch (e) {
    finishLearning();
  }
}

async function checkStage3Answer() {
  const input = document.getElementById('stage3-answer');
  if (!input || input.disabled) return;

  const w = learnQueue[0];
  const answer = input.value.trim().toLowerCase();
  const correct = w.word.toLowerCase();
  const isCorrect = answer === correct;

  if (isCorrect) { input.classList.add('correct'); }
  else { input.classList.add('wrong'); input.value = correct; }
  input.disabled = true;

  const feedbackDiv = document.getElementById('stage3-feedback');
  feedbackDiv.innerHTML = `
    <div class="review-feedback ${isCorrect ? 'correct' : 'wrong'}" style="margin-top:12px">
      <div class="feedback-word">${escapeHtml(w.word)} ${escapeHtml(w.phonetic)}</div>
      <div class="feedback-def">${escapeHtml(w.part_of_speech)} ${escapeHtml(w.definition_cn)}</div>
    </div>`;

  try {
    await api('study/submit', { method: 'POST', body: JSON.stringify({ word_id: w.id, rating: isCorrect ? 5 : 1, action: 'review' }) });
  } catch (e) { console.error(e); }

  document.getElementById('learn-actions-container').innerHTML = `
    <button class="btn btn-primary btn-block" onclick="nextReviewStudyWord()">继续</button>`;
}

async function nextReviewStudyWord() {
  try {
    const nextWord = await api('study/review-next');
    if (nextWord.word) {
      learnQueue = [nextWord.word];
      learnStage = nextWord.stage;
      renderReviewStudyCard(nextWord);
    } else { finishLearning(); }
  } catch (e) { finishLearning(); }
}

function finishLearning() {
  const container = document.getElementById('learn-card-container');
  const actions = document.getElementById('learn-actions-container');
  container.innerHTML = `
    <div class="completion-screen">
      <div class="completion-icon">🎉</div>
      <h2>学习完成！</h2>
      <p style="color:var(--text-secondary);margin-top:8px">本轮学习了 ${learnTodayNew} 个新单词</p>
      <div class="btn-group" style="justify-content:center;margin-top:20px">
        <button class="btn btn-outline" onclick="navigateTo('dashboard')">返回首页</button>
        <button class="btn btn-primary" onclick="navigateTo('review')">去复习</button>
      </div>
    </div>`;
  actions.innerHTML = '';
}

function exitLearning() { navigateTo('dashboard'); }

// ========================================================================
// ===== 昨日重现 =====
// ========================================================================
async function startYesterdayReview() {
  try {
    const data = await api('review/yesterday-review');
    if (!data.words || data.words.length === 0) {
      showToast('暂无遗忘词汇需要复习');
      return;
    }
    // Start a review session with yesterday-review words
    reviewMode = 'choice';
    reviewIndex = 0;
    reviewResults = [];
    reviewQueue = data.words.map(item => ({
      word: item.word,
      progress: item.progress,
      options: [],
      correct_index: 0,
    }));

    currentPage = 'review';
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-review').classList.add('active');
    document.getElementById('review-mode-select').style.display = 'none';
    document.getElementById('review-session').style.display = 'block';
    document.getElementById('review-back-btn').style.display = 'inline-flex';
    document.getElementById('review-complete').style.display = 'none';

    renderYesterdayReviewCard();
  } catch (e) {
    console.error(e);
    showToast('获取昨日重现数据失败');
  }
}

function renderYesterdayReviewCard() {
  if (reviewIndex >= reviewQueue.length) { finishReview(); return; }
  const item = reviewQueue[reviewIndex];
  const w = item.word;
  const total = reviewQueue.length;

  document.getElementById('review-count').textContent = `${reviewIndex + 1} / ${total}`;
  document.getElementById('review-progress-bar').style.width = `${((reviewIndex + 1) / total) * 100}%`;

  const area = document.getElementById('review-card-area');
  const enhancements = renderWordEnhancements(w, item.progress);

  area.innerHTML = `
    <div class="review-card">
      <div class="review-question">${escapeHtml(w.word)}<span class="review-tag revisit">重温</span><span class="phonetic-hint">${escapeHtml(w.phonetic)}</span></div>
      <button class="word-speak-btn" style="margin:0 auto 16px" onclick="speakWord('${escapeHtml(w.word)}')">🔊</button>
      <div class="word-definition" style="margin-bottom:12px">${formatDefinition(w.definition_cn, w.high_freq_defs)}</div>
      ${w.example_sentence ? `<div class="word-example"><div class="en">${highlightWordInSentence(w.example_sentence, w.word)}</div><div class="zh">${escapeHtml(w.example_translation)}</div></div>` : ''}
      ${enhancements}
      <div style="margin-top:16px" class="learn-actions">
        <button class="btn btn-danger" onclick="submitYesterdayReview(1)">😟 忘了</button>
        <button class="btn btn-success" onclick="submitYesterdayReview(4)">😊 记住了</button>
      </div>
    </div>`;

  setTimeout(() => speakWord(w.word), 300);
}

async function submitYesterdayReview(quality) {
  const item = reviewQueue[reviewIndex];
  const w = item.word;
  try {
    await api('review/submit', { method: 'POST', body: JSON.stringify({ word_id: w.id, quality, mode: 'yesterday-review' }) });
  } catch (e) { console.error(e); }
  reviewResults.push({ word: w.word, correct: quality >= 3, quality });
  reviewIndex++;
  renderYesterdayReviewCard();
}

// ========================================================================
// ===== 复习模式 =====
// ========================================================================
let reviewMode = null;
let reviewQueue = [];
let reviewIndex = 0;
let reviewResults = [];
// 智能重现机制
let revisitQueue = []; // {wordItem, insertAfter, revisitCount}
let revisitCounts = {}; // word_id -> count

async function renderReviewModes() {
  try {
    const reviewData = await api('review/count');
    const reviewCount = reviewData.count;

    document.getElementById('review-back-btn').style.display = 'none';
    document.getElementById('review-mode-select').style.display = 'block';
    document.getElementById('review-session').style.display = 'none';
    document.getElementById('review-complete').style.display = 'none';

    const modesDiv = document.getElementById('review-modes');
    if (reviewCount === 0) {
      modesDiv.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🎉</div>
          <div class="empty-text">暂无待复习单词</div>
          <button class="btn btn-primary" onclick="navigateTo('dashboard')">返回首页</button>
        </div>`;
    } else {
      modesDiv.innerHTML = `
        <div class="mode-card" onclick="startReview('choice')">
          <div class="mode-icon">🎯</div>
          <div class="mode-info"><div class="mode-name">选择题模式</div><div class="mode-desc">看单词，选出正确释义（强干扰项）</div></div>
          <div class="mode-count">${reviewCount}题</div>
        </div>
        <div class="mode-card" onclick="startReview('spelling')">
          <div class="mode-icon">✍️</div>
          <div class="mode-info"><div class="mode-name">拼写模式</div><div class="mode-desc">根据释义拼写正确的单词</div></div>
          <div class="mode-count">${reviewCount}题</div>
        </div>
        <div class="mode-card" onclick="startReview('listening')">
          <div class="mode-icon">🎧</div>
          <div class="mode-info"><div class="mode-name">听音辨意模式</div><div class="mode-desc">听发音，从选项中选出释义</div></div>
          <div class="mode-count">${reviewCount}题</div>
        </div>`;
    }
  } catch (e) { console.error(e); }
}

async function startReview(mode) {
  reviewMode = mode; reviewIndex = 0; reviewResults = [];
  revisitQueue = []; revisitCounts = {};
  try {
    const data = await api(`review/mode/${mode}`);
    if (!data.words || data.words.length === 0) { showToast('暂无待复习单词'); return; }
    reviewQueue = data.words;

    document.getElementById('review-mode-select').style.display = 'none';
    document.getElementById('review-session').style.display = 'block';
    document.getElementById('review-back-btn').style.display = 'inline-flex';
    document.getElementById('review-complete').style.display = 'none';
    renderReviewCard();
  } catch (e) { console.error(e); showToast('获取复习数据失败'); }
}

function renderReviewCard() {
  if (reviewIndex >= reviewQueue.length) { finishReview(); return; }
  const item = reviewQueue[reviewIndex];
  const w = item.word;
  const total = reviewQueue.length;
  const isRevisit = item._isRevisit || false;

  document.getElementById('review-count').textContent = `${reviewIndex + 1} / ${total}`;
  document.getElementById('review-progress-bar').style.width = `${((reviewIndex + 1) / total) * 100}%`;

  const area = document.getElementById('review-card-area');
  if (reviewMode === 'choice') renderChoiceMode(area, w, item.options, item.correct_index, isRevisit, item.progress);
  else if (reviewMode === 'spelling') renderSpellingMode(area, w, isRevisit, item.progress);
  else if (reviewMode === 'listening') renderListeningMode(area, w, item.options, item.correct_index, isRevisit, item.progress);
}

function renderChoiceMode(area, w, options, correctIndex, isRevisit, progress) {
  const labels = ['A', 'B', 'C', 'D'];
  const revisitTag = isRevisit ? '<span class="review-tag revisit">重温</span>' : '';

  area.innerHTML = `
    <div class="review-card">
      <div class="review-question">${escapeHtml(w.word)}${revisitTag}<span class="phonetic-hint">${escapeHtml(w.phonetic)}</span></div>
      <button class="word-speak-btn" style="margin:0 auto 16px" onclick="speakWord('${escapeHtml(w.word)}')">🔊</button>
      <div class="choices" id="choices-container">
        ${options.map((opt, i) => `<button class="choice-btn" data-index="${i}" onclick="checkChoice(this,${correctIndex},${i})"><span class="choice-label">${labels[i]}</span>${escapeHtml(opt)}</button>`).join('')}
      </div>
      <div id="review-feedback-area"></div>
      <div id="review-enhancements-area" style="display:none"></div>
    </div>`;
  setTimeout(() => speakWord(w.word), 300);
}

function checkChoice(btn, correctIndex, selectedIndex) {
  const btns = document.querySelectorAll('#choices-container .choice-btn');
  if (btns[0].disabled) return;
  const isCorrect = selectedIndex === correctIndex;
  btn.disabled = true;
  btns.forEach((b, i) => { b.style.pointerEvents = 'none'; if (i === correctIndex) b.classList.add('correct'); });
  if (!isCorrect) btn.classList.add('wrong');
  const item = reviewQueue[reviewIndex];
  const w = item.word;
  const isRevisit = item._isRevisit || false;
  
  // 显示反馈
  document.getElementById('review-feedback-area').innerHTML = `
    <div class="review-feedback ${isCorrect ? 'correct' : 'wrong'}">
      <div class="feedback-word">${escapeHtml(w.word)} ${escapeHtml(w.phonetic)}</div>
      <div class="feedback-def">${escapeHtml(w.part_of_speech)} ${escapeHtml(w.definition_cn)}</div>
    </div>
    <div style="margin-top:12px"><button class="btn btn-primary btn-block" onclick="nextReviewCard(${isCorrect ? 4 : 1})">继续</button></div>`;
  
  // 显示单词增强内容（词根、例句等）
  if (!isRevisit && item.progress) {
    const enhancements = renderWordEnhancements(w, item.progress);
    const enhancementsArea = document.getElementById('review-enhancements-area');
    if (enhancementsArea) {
      enhancementsArea.innerHTML = enhancements;
      enhancementsArea.style.display = 'block';
    }
  }
}

function renderSpellingMode(area, w, isRevisit, progress) {
  const revisitTag = isRevisit ? '<span class="review-tag revisit">重温</span>' : '';
  area.innerHTML = `
    <div class="review-card">
      <div class="review-question" style="flex-direction:column">
        ${revisitTag ? `<div style="margin-bottom:4px">${revisitTag}</div>` : ''}
        <div style="font-size:.85rem;color:var(--text-secondary);margin-bottom:4px">根据释义拼写单词</div>
        <div style="font-size:1.1rem;font-weight:600">${escapeHtml(w.part_of_speech)} ${escapeHtml(w.definition_cn)}</div>
      </div>
      <div class="spelling-input"><input type="text" id="spelling-answer" placeholder="输入单词..." autocomplete="off" autocapitalize="off" spellcheck="false"></div>
      <button class="btn btn-primary btn-block" onclick="checkSpelling()" id="spelling-submit">确认</button>
      <div id="review-feedback-area"></div>
    </div>`;
  const input = document.getElementById('spelling-answer');
  input.focus();
  input.addEventListener('keydown', e => { if (e.key === 'Enter') checkSpelling(); });
}

function checkSpelling() {
  const input = document.getElementById('spelling-answer');
  if (!input || input.disabled) return;
  const item = reviewQueue[reviewIndex];
  const w = item.word;
  const answer = input.value.trim().toLowerCase();
  const isCorrect = answer === w.word.toLowerCase();
  if (isCorrect) input.classList.add('correct');
  else { input.classList.add('wrong'); input.value = w.word; }
  input.disabled = true;
  document.getElementById('review-feedback-area').innerHTML = `
    <div class="review-feedback ${isCorrect ? 'correct' : 'wrong'}">
      <div class="feedback-word">${escapeHtml(w.word)} ${escapeHtml(w.phonetic)}</div>
      <div class="feedback-def">${escapeHtml(w.part_of_speech)} ${escapeHtml(w.definition_cn)}</div>
      ${!isCorrect ? `<div style="margin-top:4px;font-size:.8rem">例句：${highlightWordInSentence(w.example_sentence, w.word)}</div>` : ''}
    </div>
    <div style="margin-top:12px"><button class="btn btn-primary btn-block" onclick="nextReviewCard(${isCorrect ? 4 : 1})">继续</button></div>`;
}

function renderListeningMode(area, w, options, correctIndex, isRevisit, progress) {
  const labels = ['A', 'B', 'C', 'D'];
  const revisitTag = isRevisit ? '<span class="review-tag revisit">重温</span>' : '';
  area.innerHTML = `
    <div class="review-card">
      ${revisitTag ? `<div style="text-align:center;margin-bottom:8px">${revisitTag}</div>` : ''}
      <button class="listen-btn-large" onclick="speakWord('${escapeHtml(w.word)}', 0.7)">
        <span class="listen-icon">🎧</span><span class="listen-text">点击播放发音</span>
      </button>
      <div class="choices" id="choices-container">
        ${options.map((opt, i) => `<button class="choice-btn" data-index="${i}" onclick="checkChoice(this,${correctIndex},${i})"><span class="choice-label">${labels[i]}</span>${escapeHtml(opt)}</button>`).join('')}
      </div>
      <div id="review-feedback-area"></div>
    </div>`;
  setTimeout(() => speakWord(w.word, 0.7), 500);
}

async function nextReviewCard(quality) {
  const item = reviewQueue[reviewIndex];
  const w = item.word;
  const isRevisit = item._isRevisit || false;

  try { await api('review/submit', { method: 'POST', body: JSON.stringify({ word_id: w.id, quality, mode: reviewMode }) }); } catch (e) { console.error(e); }
  reviewResults.push({ word: w.word, correct: quality >= 3, quality });

  // 智能重现机制：如果答错且不是重温词，加入重现队列
  if (quality < 3 && !isRevisit) {
    const wordId = w.id;
    const count = (revisitCounts[wordId] || 0) + 1;
    revisitCounts[wordId] = count;

    if (count <= 3) {
      // 至少间隔5个单词后重现
      const insertAfter = reviewIndex + 5;
      revisitQueue.push({
        item: { ...item, _isRevisit: true },
        insertAfter: insertAfter,
        wordId: wordId,
      });
    }
  }

  // 检查是否有需要插入的重现词
  const toInsert = revisitQueue.filter(r => r.insertAfter === reviewIndex && revisitCounts[r.wordId] <= 3);
  revisitQueue = revisitQueue.filter(r => r.insertAfter !== reviewIndex);

  // Insert revisit words at current position (after increment)
  reviewIndex++;

  if (toInsert.length > 0) {
    // Insert the revisit word right after current position
    for (const r of toInsert) {
      if (revisitCounts[r.wordId] <= 3) {
        reviewQueue.splice(reviewIndex, 0, r.item);
      }
    }
  }

  renderReviewCard();
}

function finishReview() {
  const correctCount = reviewResults.filter(r => r.correct).length;
  const total = reviewResults.length;
  const accuracy = total > 0 ? Math.round((correctCount / total) * 100) : 0;

  document.getElementById('review-session').style.display = 'none';
  document.getElementById('review-complete').style.display = 'block';
  document.getElementById('review-back-btn').style.display = 'none';

  document.getElementById('review-complete').innerHTML = `
    <div class="completion-screen">
      <div class="completion-icon">${accuracy >= 80 ? '🏆' : accuracy >= 60 ? '👍' : '💪'}</div>
      <h2>复习完成！</h2>
      <div class="completion-stats">
        <div class="completion-stat"><div class="val">${total}</div><div class="lbl">复习单词</div></div>
        <div class="completion-stat"><div class="val">${correctCount}</div><div class="lbl">回答正确</div></div>
        <div class="completion-stat"><div class="val">${accuracy}%</div><div class="lbl">正确率</div></div>
      </div>
      <div style="margin-top:16px">${reviewResults.map(r => `<div class="result-card"><span class="result-word">${escapeHtml(r.word)}</span><span class="result-status ${r.correct ? 'mastered' : 'learning'}">${r.correct ? '✓ 正确' : '✗ 错误'}</span></div>`).join('')}</div>
      <div class="btn-group" style="justify-content:center;margin-top:20px">
        <button class="btn btn-outline" onclick="navigateTo('dashboard')">返回首页</button>
        <button class="btn btn-primary" onclick="renderReviewModes()">继续复习</button>
      </div>
    </div>`;
}

function exitReview() {
  const s = document.getElementById('review-session').style.display === 'block';
  const c = document.getElementById('review-complete').style.display === 'block';
  if (s || c) renderReviewModes();
  else navigateTo('dashboard');
}

// ========================================================================
// ===== 单词标签 & 笔记 =====
// ========================================================================
async function setWordFlag(wordId, flag) {
  try {
    await api(`words/${wordId}/flag`, { method: 'POST', body: JSON.stringify({ flag }) });
    showToast('标签已更新');
    // Update UI
    const btns = document.querySelectorAll(`#flag-btns-${wordId} .flag-btn`);
    btns.forEach(b => b.classList.remove('active'));
    const flagClass = flag === -1 ? 'flag-hard' : flag === 0 ? 'flag-normal' : flag === 1 ? 'flag-mastered' : flag === 2 ? 'flag-familiar' : 'flag-easy';
    const activeBtn = document.querySelector(`#flag-btns-${wordId} .flag-btn.${flagClass}`);
    if (activeBtn) activeBtn.classList.add('active');
  } catch (e) { showToast('标签更新失败'); }
}

let currentNoteWordId = null;
function openNoteEditor(wordId) {
  currentNoteWordId = wordId;
  const section = document.getElementById(`note-section-${wordId}`);
  const content = section?.querySelector('.note-content');
  const existing = content && !content.querySelector('.note-placeholder') ? content.textContent : '';
  document.getElementById('note-textarea').value = existing;
  document.getElementById('note-modal').classList.add('show');
}

async function saveCurrentNote() {
  if (!currentNoteWordId) return;
  const note = document.getElementById('note-textarea').value.trim();
  try {
    await api(`words/${currentNoteWordId}/note`, { method: 'POST', body: JSON.stringify({ user_note: note }) });
    closeModal('note-modal');
    showToast('笔记已保存');
    // Update UI
    const section = document.getElementById(`note-section-${currentNoteWordId}`);
    if (section) {
      const content = section.querySelector('.note-content');
      if (content) {
        content.innerHTML = note ? escapeHtml(note) : '<span class="note-placeholder">添加笔记...</span>';
      }
    }
  } catch (e) { showToast('保存笔记失败'); }
}

// ========================================================================
// ===== 词书页面 =====
// ========================================================================
async function renderBooks() {
  try {
    const books = await api('books');
    const booksDiv = document.getElementById('books-list');
    booksDiv.innerHTML = books.map(book => {
      // 判断是否可以删除（非系统默认词书且不是当前使用的）
      const systemBooks = ['cet4', 'cet6', 'kaoyan', 'ielts', 'toefl'];
      const isSystemBook = systemBooks.includes(book.id);
      const canDelete = !isSystemBook && !book.is_current;
      
      return `
      <div class="book-card ${book.is_current ? 'active' : ''}" onclick="selectBook('${book.id}')">
        <div class="book-icon">${book.icon}</div>
        <div class="book-info">
          <div class="book-name">${escapeHtml(book.name)}</div>
          <div class="book-desc">${escapeHtml(book.description)}</div>
          <div class="progress-bar" style="margin-top:6px;position:relative">
            <div class="fill" style="width:${book.progress_pct}%;background:linear-gradient(90deg,var(--info),var(--info-light))"></div>
          </div>
          <div class="book-progress">已学 ${book.learned}/${book.word_count} · 掌握 ${book.mastered} · ${book.progress_pct}%</div>
          <div style="font-size:.72rem;color:var(--text-secondary);margin-top:2px">
            记忆率: <span style="color:var(--info)">历史${book.history_rate}%</span> · <span style="color:var(--success)">近期${book.recent_rate}%</span>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <span class="book-status ${book.is_current ? 'using' : ''} ${book.progress_pct === 100 ? 'completed' : ''}">${book.is_current ? '使用中' : book.progress_pct === 100 ? '已完成' : '选择'}</span>
          ${canDelete ? `<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();deleteBook('${book.id}', '${escapeHtml(book.name)}')" title="删除词书" style="color:var(--danger);padding:4px 8px">🗑️</button>` : ''}
        </div>
      </div>`;
    }).join('');
  } catch (e) { console.error(e); }
}

async function selectBook(bookId) {
  try {
    await api(`books/${bookId}/select`, { method: 'POST' });
    showToast('已切换词书');
    renderBooks();
  } catch (e) { showToast('切换词书失败'); }
}

async function deleteBook(bookId, bookName) {
  if (!confirm(`确定要删除词书「${bookName}」吗？\n\n此操作将删除：\n- 所有单词\n- 学习进度\n- 学习记录\n\n此操作不可恢复！`)) {
    return;
  }
  
  try {
    await api(`books/${bookId}`, { method: 'DELETE' });
    showToast('词书已删除');
    renderBooks();
  } catch (e) {
    showToast('删除失败: ' + (e.message || '未知错误'));
  }
}

// ===== 导入词书 =====
function showImportModal() { 
  document.getElementById('import-modal').classList.add('show'); 
  // 清空之前的输入
  document.getElementById('import-book-name').value = '';
  document.getElementById('import-file-input').value = '';
  document.getElementById('import-result').style.display = 'none';
}

function handleImportFile(input) {
  const file = input.files[0];
  if (!file) return;
  
  const bookName = document.getElementById('import-book-name').value.trim();
  const formData = new FormData();
  formData.append('file', file);
  if (bookName) {
    formData.append('book_name', bookName);
  }

  document.getElementById('import-progress').style.display = 'block';
  document.getElementById('import-result').style.display = 'none';

  fetch('/api/books/import', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(result => {
      document.getElementById('import-progress').style.display = 'none';
      document.getElementById('import-result').style.display = 'block';
      document.getElementById('import-result').innerHTML = `
        <div style="padding:12px;background:var(--primary-bg);border-radius:var(--radius-sm)">
          <div style="font-weight:600;margin-bottom:6px">导入完成</div>
          <div style="font-size:.85rem">词书: ${escapeHtml(result.book_name)}</div>
          <div style="font-size:.85rem;color:var(--success)">✅ 成功: ${result.success_count} 个</div>
          ${result.fail_count > 0 ? `<div style="font-size:.85rem;color:var(--danger)">❌ 失败: ${result.fail_count} 个</div>` : ''}
          ${result.errors.length > 0 ? `<div style="font-size:.8rem;color:var(--text-secondary);margin-top:4px">${result.errors.slice(0, 5).join('<br>')}</div>` : ''}
        </div>`;
      renderBooks();
    })
    .catch(e => {
      document.getElementById('import-progress').style.display = 'none';
      showToast('导入失败: ' + e.message);
    });
}

// ========================================================================
// ===== 词根词缀页面 =====
// ========================================================================
async function renderRoots() {
  try {
    const roots = await api('roots');
    const div = document.getElementById('roots-list');
    if (roots.length === 0) {
      div.innerHTML = '<div class="empty-state"><div class="empty-icon">🧬</div><div class="empty-text">暂无词根词缀数据</div></div>';
      return;
    }
    div.innerHTML = '';
    for (const root of roots) {
      if (root.word_count === 0) continue;
      let wordsHtml = '';
      try {
        const data = await api(`roots/${root.id}/words`);
        wordsHtml = data.words.map(w => `
          <div class="root-word-item">
            <span class="rw-word">${escapeHtml(w.word)}</span>
            <span class="rw-arrow">→</span>
            <span class="rw-def">${escapeHtml(w.definition_cn.split('；')[0])}</span>
          </div>`).join('');
      } catch (e) { wordsHtml = ''; }

      div.innerHTML += `
        <div class="root-group">
          <div class="root-header">
            <span class="root-badge">${escapeHtml(root.root_text)} = ${escapeHtml(root.meaning)}</span>
            <span style="font-size:.8rem;color:var(--text-secondary)">${root.word_count} 个词</span>
          </div>
          ${root.description ? `<div class="root-desc">${escapeHtml(root.description)}</div>` : ''}
          <div class="root-word-list">${wordsHtml}</div>
        </div>`;
    }
  } catch (e) { console.error(e); }
}

// ========================================================================
// ===== 艾宾浩斯日历 =====
// ========================================================================
let ebCalMonth = new Date().getMonth();
let ebCalYear = new Date().getFullYear();

async function renderEbbinghausCalendar() {
  try {
    const data = await api(`review/calendar?year=${ebCalYear}&month=${ebCalMonth + 1}`);
    document.getElementById('eb-calendar-month').textContent = `${data.year}年${data.month}月`;
    const firstDay = new Date(data.year, data.month - 1, 1).getDay();
    const todayDateStr = todayStr();
    let html = '';
    ['日','一','二','三','四','五','六'].forEach(l => html += `<div class="day-label">${l}</div>`);
    for (let i = 0; i < firstDay; i++) html += '<div class="day-cell empty"></div>';
    for (const day of data.days) {
      const dayNum = parseInt(day.date.split('-')[2]);
      let cls = 'day-cell';
      let style = '';
      let content = `${dayNum}`;
      if (day.is_ebbinghaus) { cls += ' checked'; style = 'background:var(--info);color:#fff;font-weight:600;cursor:pointer'; }
      if (day.is_extra && !day.is_ebbinghaus) { cls += ' extra'; style = 'background:var(--success);color:#fff;font-weight:600;cursor:pointer'; }
      if (day.date === todayDateStr) cls += ' today';
      html += `<div class="${cls}" style="${style}" onclick="showCalDayDetail('${day.date}')">${content}</div>`;
    }
    document.getElementById('eb-calendar-grid').innerHTML = html;
  } catch (e) { console.error(e); }
}

function changeCalMonth(delta) {
  ebCalMonth += delta;
  if (ebCalMonth > 11) { ebCalMonth = 0; ebCalYear++; }
  if (ebCalMonth < 0) { ebCalMonth = 11; ebCalYear--; }
  renderEbbinghausCalendar();
}

async function showCalDayDetail(dateStr) {
  try {
    const data = await api(`review/calendar?year=${parseInt(dateStr.split('-')[0])}&month=${parseInt(dateStr.split('-')[1])}`);
    const day = data.days.find(d => d.date === dateStr);
    const detail = document.getElementById('eb-calendar-detail');
    if (day && (day.is_ebbinghaus || day.is_extra)) {
      detail.innerHTML = `
        <div style="padding:12px;background:var(--primary-bg);border-radius:var(--radius-sm)">
          <div style="font-weight:600;margin-bottom:6px">${dateStr} 复习计划</div>
          ${day.books.length > 0 ? `<div style="font-size:.85rem">📚 ${day.books.join('、')}</div>` : ''}
          <div style="font-size:.85rem">📝 ${day.word_count} 个单词待复习</div>
          ${day.is_ebbinghaus ? '<div style="font-size:.78rem;color:var(--info)">🔵 艾宾浩斯计划复习</div>' : ''}
          ${day.is_extra ? '<div style="font-size:.78rem;color:var(--success)">🟢 额外复习</div>' : ''}
        </div>`;
    } else {
      detail.innerHTML = `<div style="font-size:.85rem;color:var(--text-secondary);text-align:center">${dateStr} 暂无复习计划</div>`;
    }
  } catch (e) { console.error(e); }
}

// ========================================================================
// ===== AI 完形填空 =====
// ========================================================================
let clozeData = null;

function renderClozePage() {
  if (!clozeData) {
    document.getElementById('cloze-content').innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🤖</div>
        <div class="empty-text">基于今日所学单词生成完形填空</div>
        <button class="btn btn-primary" onclick="generateCloze()">生成完形填空</button>
      </div>`;
  }
}

async function generateCloze() {
  document.getElementById('cloze-content').innerHTML = '<div class="loading-spinner"></div><div style="text-align:center;font-size:.85rem;color:var(--text-secondary);margin-top:8px">AI 生成中，请稍候...</div>';
  try {
    const result = await api('skills/cloze/generate', { method: 'POST', body: JSON.stringify({}) });
    if (result.error) { showToast(result.error); return; }
    clozeData = result;
    renderClozeContent();
  } catch (e) {
    document.getElementById('cloze-content').innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <div class="empty-text">${escapeHtml(e.message)}</div>
        <button class="btn btn-primary" onclick="generateCloze()">重试</button>
      </div>`;
  }
}

function renderClozeContent() {
  if (!clozeData) return;
  const article = clozeData.article || '';
  const blanks = clozeData.blanks || [];
  const title = clozeData.title || '完形填空';

  let articleHtml = escapeHtml(article);
  blanks.forEach((blank, i) => {
    articleHtml = articleHtml.replace(`__BLANK_${i}__`, `<span class="cloze-blank" id="blank-${i}">____${i + 1}____</span>`);
  });

  let optionsHtml = blanks.map((blank, i) => {
    const opts = (blank.options || []).map((opt, j) => `<option value="${j}">${escapeHtml(opt)}</option>`).join('');
    return `<div class="cloze-option-row"><span class="blank-label">(${i + 1})</span><select class="cloze-option-select" id="select-${i}"><option value="">请选择</option>${opts}</select></div>`;
  }).join('');

  document.getElementById('cloze-content').innerHTML = `
    <div style="font-weight:600;font-size:1rem;margin-bottom:12px">${escapeHtml(title)}</div>
    <div class="cloze-article">${articleHtml}</div>
    <div class="cloze-options">
      <div class="cloze-options-title">选择答案</div>
      ${optionsHtml}
    </div>
    <button class="btn btn-primary btn-block" onclick="submitCloze()">提交答案</button>
    <div id="cloze-result" style="margin-top:12px"></div>`;
}

async function submitCloze() {
  const blanks = clozeData.blanks || [];
  const answers = {};
  blanks.forEach((blank, i) => {
    const sel = document.getElementById(`select-${i}`);
    if (sel) answers[i] = sel.value;
  });

  try {
    const result = await api('skills/cloze/submit', { method: 'POST', body: JSON.stringify({ answers, cloze_data: clozeData }) });
    
    // 显示分数
    let resultHtml = `
      <div style="text-align:center;padding:16px;background:var(--primary-bg);border-radius:var(--radius-sm);margin-bottom:16px">
        <div style="font-size:1.5rem;font-weight:700;color:var(--primary)">${result.score}分</div>
        <div style="font-size:.85rem;color:var(--text-secondary)">正确 ${result.correct}/${result.total}</div>
      </div>`;
    
    // 标记答案
    result.results.forEach(r => {
      const blankEl = document.getElementById(`blank-${r.index}`);
      if (blankEl) {
        blankEl.style.background = r.correct ? '#e8f8f0' : '#fde8e8';
        blankEl.style.borderColor = r.correct ? 'var(--success)' : 'var(--danger)';
        blankEl.textContent = r.correct_answer;
      }
    });
    
    // 显示解析
    resultHtml += '<div style="margin-top:20px"><h3 style="font-size:1rem;margin-bottom:12px">📝 答案解析</h3>';
    result.results.forEach(r => {
      resultHtml += `
        <div style="background:var(--card);padding:12px;border-radius:var(--radius-sm);margin-bottom:8px;box-shadow:var(--shadow)">
          <div style="font-weight:600;margin-bottom:4px">第${r.index + 1}题：${escapeHtml(r.correct_answer)}</div>
          <div style="font-size:.85rem;color:var(--text-secondary)">${escapeHtml(r.explanation || '')}</div>
        </div>`;
    });
    resultHtml += '</div>';
    
    // 显示全文翻译
    if (result.translation) {
      resultHtml += `
        <div style="margin-top:20px">
          <h3 style="font-size:1rem;margin-bottom:12px">🌐 全文翻译</h3>
          <div style="background:var(--card);padding:16px;border-radius:var(--radius-sm);box-shadow:var(--shadow);line-height:1.8;font-size:.9rem">
            ${escapeHtml(result.translation)}
          </div>
        </div>`;
    }
    
    document.getElementById('cloze-result').innerHTML = resultHtml;
  } catch (e) { showToast('提交失败'); }
}

// ========================================================================
// ===== AI 作文优化 =====
// ========================================================================
let writingMode = 'text';
let writingImageFile = null;
let writingDocFile = null;

function renderWritingPage() { /* 页面已在 HTML 中渲染 */ }

function switchWritingTab(mode) {
  writingMode = mode;
  document.querySelectorAll('.writing-tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('writing-input-text').style.display = mode === 'text' ? 'block' : 'none';
  document.getElementById('writing-input-image').style.display = mode === 'image' ? 'block' : 'none';
  document.getElementById('writing-input-file').style.display = mode === 'file' ? 'block' : 'none';
}

function handleWritingImage(input) {
  writingImageFile = input.files[0];
  if (writingImageFile) {
    document.querySelector('#writing-image-zone div:nth-child(2)').textContent = writingImageFile.name;
  }
}

function handleWritingFile(input) {
  writingDocFile = input.files[0];
  if (writingDocFile) {
    document.querySelector('#writing-input-file .upload-zone div:nth-child(2)').textContent = writingDocFile.name;
  }
}

async function optimizeWriting() {
  const btn = document.getElementById('writing-submit-btn');
  btn.disabled = true; btn.textContent = '🤖 AI 优化中...';
  document.getElementById('writing-result').innerHTML = '<div class="loading-spinner"></div>';

  try {
    const formData = new FormData();
    formData.append('mode', writingMode);

    if (writingMode === 'text') {
      const text = document.getElementById('writing-textarea').value;
      if (!text.trim()) { showToast('请输入作文内容'); return; }
      formData.append('text', text);
    } else if (writingMode === 'image' && writingImageFile) {
      formData.append('image', writingImageFile);
    } else if (writingMode === 'file' && writingDocFile) {
      formData.append('file', writingDocFile);
    } else {
      showToast('请提供作文内容'); return;
    }

    const resp = await fetch('/api/skills/writing/optimize', { method: 'POST', body: formData });
    if (!resp.ok) { const err = await resp.json(); throw new Error(err.detail || '优化失败'); }
    const result = await resp.json();

    renderWritingResult(result);
  } catch (e) {
    document.getElementById('writing-result').innerHTML = `
      <div class="empty-state" style="padding:20px"><div class="empty-icon">⚠️</div><div class="empty-text">${escapeHtml(e.message)}</div></div>`;
  } finally {
    btn.disabled = false; btn.textContent = '🤖 AI 优化';
  }
}

function renderWritingResult(r) {
  let html = '<div class="writing-result">';
  if (r.score) html += `<div class="writing-score">${r.score}分</div>`;
  if (r.feedback) html += `<div class="writing-feedback-text">${escapeHtml(r.feedback)}</div>`;

  if (r.grammar && r.grammar.length > 0) {
    html += `<div class="writing-section"><div class="writing-section-title">📝 语法纠正</div>`;
    r.grammar.forEach(g => { html += `<div class="writing-item"><span class="original">${escapeHtml(g.original)}</span> → <span class="corrected">${escapeHtml(g.corrected)}</span><div class="reason">${escapeHtml(g.explanation || '')}</div></div>`; });
    html += '</div>';
  }

  if (r.vocabulary && r.vocabulary.length > 0) {
    html += `<div class="writing-section"><div class="writing-section-title">💡 用词优化</div>`;
    r.vocabulary.forEach(v => { html += `<div class="writing-item"><span class="original">${escapeHtml(v.original)}</span> → <span class="corrected">${escapeHtml(v.suggestion)}</span><div class="reason">${escapeHtml(v.reason || '')}</div></div>`; });
    html += '</div>';
  }

  if (r.optimized) {
    const original = document.getElementById('writing-textarea')?.value || '';
    html += `<div class="writing-section"><div class="writing-section-title">📄 对比查看</div><div class="writing-compare">`;
    html += `<div class="writing-compare-col"><h4>原文</h4>${escapeHtml(original)}</div>`;
    html += `<div class="writing-compare-col"><h4>优化版</h4>${escapeHtml(r.optimized)}</div></div></div>`;
  }

  html += '</div>';
  document.getElementById('writing-result').innerHTML = html;
}

// ========================================================================
// ===== 统计页面 =====
// ========================================================================
let statsCalendarMonth = new Date().getMonth();
let statsCalendarYear = new Date().getFullYear();

async function renderStats() {
  try {
    const [overview, mastery, weekly, stageProgress] = await Promise.all([
      api('stats/overview'), api('stats/mastery'), api('stats/weekly'), api('stats/stage-progress'),
    ]);

    document.getElementById('stats-overview').innerHTML = `
      <div class="stat-item"><div class="stat-val">${overview.total_days}</div><div class="stat-lbl">学习天数</div></div>
      <div class="stat-item"><div class="stat-val">${overview.total_learned}</div><div class="stat-lbl">已学单词</div></div>
      <div class="stat-item"><div class="stat-val">${overview.total_mastered}</div><div class="stat-lbl">已掌握</div></div>`;

    // 双记忆率
    document.getElementById('stats-history-rate-bar').style.width = (overview.history_rate || 0) + '%';
    document.getElementById('stats-history-rate-val').textContent = (overview.history_rate || 0) + '%';
    document.getElementById('stats-recent-rate-bar').style.width = (overview.recent_rate || 0) + '%';
    document.getElementById('stats-recent-rate-val').textContent = (overview.recent_rate || 0) + '%';

    // 三轮进度
    document.getElementById('stats-stage-progress').innerHTML = `
      <div class="stage-item"><span class="stage-dot stage1"></span>初次学习 <b>${stageProgress.stage1_count}</b></div>
      <div class="stage-item"><span class="stage-dot stage2"></span>间隔复习 <b>${stageProgress.stage2_count}</b></div>
      <div class="stage-item"><span class="stage-dot stage3"></span>输出验证 <b>${stageProgress.stage3_count}</b></div>
      <div class="stage-item"><span class="stage-dot mastered"></span>已掌握 <b>${stageProgress.mastered_count}</b></div>`;

    const total = mastery.total || 1;
    document.getElementById('mastery-bar').innerHTML = `
      <div class="seg new" style="width:${(mastery.new_count / total) * 100}%"></div>
      <div class="seg learning" style="width:${(mastery.learning_count / total) * 100}%"></div>
      <div class="seg familiar" style="width:${(mastery.familiar_count / total) * 100}%"></div>
      <div class="seg mastered" style="width:${(mastery.mastered_count / total) * 100}%"></div>`;

    document.getElementById('mastery-legend').innerHTML = `
      <div class="legend-item"><span class="legend-dot new"></span>未学 ${mastery.new_count}</div>
      <div class="legend-item"><span class="legend-dot learning"></span>学习中 ${mastery.learning_count}</div>
      <div class="legend-item"><span class="legend-dot familiar"></span>熟悉 ${mastery.familiar_count}</div>
      <div class="legend-item"><span class="legend-dot mastered"></span>已掌握 ${mastery.mastered_count}</div>`;

    renderCalendar();
    renderDailyChart(weekly);
  } catch (e) { console.error(e); }
}

async function renderCalendar() {
  try {
    const data = await api(`checkin/calendar?year=${statsCalendarYear}&month=${statsCalendarMonth + 1}`);
    document.getElementById('calendar-month').textContent = `${data.year}年${data.month}月`;
    const firstDay = new Date(data.year, data.month - 1, 1).getDay();
    const todayDateStr = todayStr();
    let html = '';
    ['日','一','二','三','四','五','六'].forEach(l => html += `<div class="day-label">${l}</div>`);
    for (let i = 0; i < firstDay; i++) html += '<div class="day-cell empty"></div>';
    for (const day of data.days) {
      const dayNum = parseInt(day.date.split('-')[2]);
      let cls = 'day-cell';
      if (day.checked) cls += ' checked';
      if (day.date === todayDateStr) cls += ' today';
      html += `<div class="${cls}">${dayNum}</div>`;
    }
    document.getElementById('calendar-grid').innerHTML = html;
  } catch (e) { console.error(e); }
}

function changeMonth(delta) {
  statsCalendarMonth += delta;
  if (statsCalendarMonth > 11) { statsCalendarMonth = 0; statsCalendarYear++; }
  if (statsCalendarMonth < 0) { statsCalendarMonth = 11; statsCalendarYear--; }
  renderCalendar();
}

function renderDailyChart(weekly) {
  const days = weekly.days || [];
  const max = Math.max(...days.map(d => d.total), 1);
  document.getElementById('daily-chart').innerHTML = days.map(d => `<div class="chart-bar" style="height:${Math.max(2, (d.total / max) * 100)}%"></div>`).join('');
  document.getElementById('daily-chart-labels').innerHTML = days.map(d => `<span>${parseInt(d.date.split('-')[1])}/${parseInt(d.date.split('-')[2])}</span>`).join('');
}

// ========================================================================
// ===== 设置 =====
// ========================================================================
async function showSettings() {
  try {
    const settings = await api('stats/settings');
    document.getElementById('setting-daily-new').value = settings.daily_new;
    document.getElementById('setting-daily-review').value = settings.daily_review;

    // 熬夜模式
    const delayData = await api('settings/delay-hours');
    document.getElementById('setting-delay-hours').value = delayData.delay_hours;

    // AI 配置
    const llmSettings = await api('settings/llm');
    document.getElementById('setting-llm-key').value = '';
    document.getElementById('setting-llm-key').placeholder = llmSettings.api_key_set ? llmSettings.api_key_masked : 'sk-...';
    document.getElementById('setting-llm-base').value = llmSettings.api_base;
    document.getElementById('setting-llm-model').value = llmSettings.model;
    document.getElementById('llm-status').textContent = llmSettings.api_key_set ? '✅ API Key 已配置' : '⚠️ 未配置 API Key，AI 功能不可用';

    // 学习模式阈值
    if (document.getElementById('setting-learn-threshold')) {
      document.getElementById('setting-learn-threshold').value = Math.round((settings.learn_pass_threshold || 0.7) * 100);
    }

    document.getElementById('settings-modal').classList.add('show');
  } catch (e) { showToast('获取设置失败'); }
}

async function saveSettings() {
  const dailyNew = parseInt(document.getElementById('setting-daily-new').value) || 10;
  const dailyReview = parseInt(document.getElementById('setting-daily-review').value) || 30;
  const delayHours = parseInt(document.getElementById('setting-delay-hours').value) || 0;

  try {
    await api('stats/settings', { method: 'POST', body: JSON.stringify({ daily_new: dailyNew, daily_review: dailyReview }) });

    // 熬夜模式
    await api('settings/delay-hours', { method: 'POST', body: JSON.stringify({ delay_hours: delayHours }) });

    // AI 配置
    const llmKey = document.getElementById('setting-llm-key').value;
    const llmBase = document.getElementById('setting-llm-base').value;
    const llmModel = document.getElementById('setting-llm-model').value;

    const llmUpdate = {};
    if (llmKey) llmUpdate.api_key = llmKey;
    if (llmBase) llmUpdate.api_base = llmBase;
    if (llmModel) llmUpdate.model = llmModel;

    if (Object.keys(llmUpdate).length > 0) {
      await api('settings/llm', { method: 'POST', body: JSON.stringify(llmUpdate) });
    }

    // 学习模式阈值
    const thresholdInput = document.getElementById('setting-learn-threshold');
    if (thresholdInput) {
      const thresholdValue = parseInt(thresholdInput.value) || 70;
      const thresholdDecimal = Math.max(50, Math.min(90, thresholdValue)) / 100;
      await api('stats/settings', { method: 'POST', body: JSON.stringify({ learn_pass_threshold: thresholdDecimal }) });
      LEARN_PASS_THRESHOLD = thresholdDecimal;
    }

    document.getElementById('settings-modal').classList.remove('show');
    showToast('设置已保存');
    renderDashboard();
  } catch (e) { showToast('保存设置失败'); }
}

async function resetAllData() {
  if (confirm('确定要清除所有学习数据吗？此操作不可恢复！')) {
    try {
      await api('stats/reset', { method: 'POST' });
      document.getElementById('settings-modal').classList.remove('show');
      showToast('学习数据已重置');
      renderDashboard();
    } catch (e) { showToast('重置失败'); }
  }
}

document.getElementById('settings-modal').addEventListener('click', function(e) { if (e.target === this) this.classList.remove('show'); });
document.getElementById('import-modal').addEventListener('click', function(e) { if (e.target === this) this.classList.remove('show'); });
document.getElementById('note-modal').addEventListener('click', function(e) { if (e.target === this) this.classList.remove('show'); });

// 拖拽上传支持
const dropZone = document.getElementById('import-drop-zone');
if (dropZone) {
  ['dragenter', 'dragover'].forEach(ev => dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.add('drag-over'); }));
  ['dragleave', 'drop'].forEach(ev => dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.remove('drag-over'); }));
  dropZone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      document.getElementById('import-file-input').files = files;
      handleImportFile(document.getElementById('import-file-input'));
    }
  });
}

// ========================================================================
// ===== 智能爬虫功能 (Smart Crawler) =====
// ========================================================================

/**
 * 一键获取单词的助记法和例句
 */
async function fetchSmartMnemonic(word, wordId) {
  const btn = document.getElementById(`crawler-btn-${wordId}`);
  if (!btn) return;

  const originalText = btn.innerHTML;
  btn.innerHTML = '🕷️ 正在全网搜索...';
  btn.disabled = true;

  try {
    console.log(`[Crawler] 开始爬取: ${word}`);
    const resp = await fetch('/api/crawler/crawl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word: word, save_to_db: true })
    });
    
    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${resp.status}`);
    }
    
    const data = await resp.json();
    console.log('[Crawler] 结果:', data);

    if (data.success) {
      let msg = '✅ 数据已更新';
      if (data.mnemonic && data.example_sentence) msg = '✨ 助记与例句均已找到！';
      else if (data.mnemonic) msg = '💡 已找到趣味助记法';
      else if (data.example_sentence) msg = '📖 已补充经典例句';
      
      showToast(msg);
      
      // 【优化】如果当前正在学习这个单词，立即更新卡片显示
      if (currentPage === 'learn' && learnQueue.length > 0) {
        const currentWord = learnQueue[learnIndex];
        if (currentWord && currentWord.word.toLowerCase() === word.toLowerCase()) {
          // 更新本地数据以便重新渲染
          currentWord.example_sentence = data.example_sentence || currentWord.example_sentence;
          currentWord.example_translation = data.example_translation || currentWord.example_translation;
          currentWord.mnemonic = data.mnemonic || currentWord.mnemonic;
          renderLearnCard(learnIndex);
        }
      }
    } else {
      showToast('⚠️ 暂未找到相关助记，请稍后再试');
    }
  } catch (e) {
    console.error('[Crawler Error]', e);
    showToast(`❌ 爬取异常: ${e.message}`);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

// ========================================================================
// ===== 初始化 =====
// ========================================================================
async function init() {
  await renderDashboard();
}

init();
