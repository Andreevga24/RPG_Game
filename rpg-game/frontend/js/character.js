import { apiFetch } from './app.js';
import { showToast } from './ui.js';

const CLASS_ICONS = { Tauran:'🐂', Gnombaf:'🧙', Arachnid:'🕷️', Angel:'👼' };
const CLASS_RU    = { Tauran:'Тауран', Gnombaf:'Гномбаф', Arachnid:'Арахнид', Angel:'Ангел' };

const FULL_REGEN_SECONDS = 6 * 60 * 60; // full restore in 6 hours

export let currentChar = null;

export async function loadCharacter() {
  currentChar = await apiFetch('/api/character');
  renderCharHeader(currentChar);
  renderSidebarInfo(currentChar);
  return currentChar;
}

// ── Stat definitions (single source of truth) ──────────────────────────────
const STAT_DEFS = [
  { key: 'str_', api: 'str', label: 'Сила',     icon: '⚔️', desc: 'Сила — урон в бою (не ниже 0)' },
  { key: 'dex',  api: 'dex', label: 'Ловкость', icon: '🏹', desc: 'Ловкость — защита, инициатива, шанс уклонения' },
  { key: 'con',  api: 'con', label: 'Тело',     icon: '🛡️', desc: 'Телосложение — +5 HP за очко; реген HP после боя' },
  { key: 'int_', api: 'int', label: 'Интел',    icon: '🔮', desc: 'Интеллект — шанс крита в обычном бою; INT/2 к атаке в рейде' },
  { key: 'wis',  api: 'wis', label: 'Мудрость', icon: '👁️', desc: 'Мудрость — макс. энергия: 10 + 2 за каждое WIS выше 5' },
  { key: 'cha',  api: 'cha', label: 'Харизма',  icon: '✨', desc: 'Харизма — бонус партии в рейде (лидерство), инициатива в рейде' },
  { key: '_hp',  api: 'hp',  label: 'Здоровье', icon: '❤️', desc: 'Здоровье — +20 макс. HP за очко' },
];

function statVal(char, key) {
  return key === '_hp' ? char.hp_max : (char[key] ?? 0);
}

function statBarWidth(key, val) {
  return key === '_hp' ? Math.min(100, val / 5) : Math.min(100, val * 4);
}

// ── Header ──────────────────────────────────────────────────────────────────
function renderCharHeader(char) {
  const el = document.getElementById('charHeader');
  if (!el) return;
  const expLabel = char.level >= 85 ? 'МАКС' : `${char.exp}/${char.exp_next}`;
  const expPct   = char.level >= 85 ? 100 : (char.exp / char.exp_next) * 100;
  el.innerHTML = `
    <div class="char-avatar">${CLASS_ICONS[char.char_class] || '👤'}</div>
    <div class="char-details">
      <div class="char-name">${char.name}</div>
      <div class="char-meta">
        <span class="rank-badge rank-${char.rank}">${char.rank}</span>
        <span style="color:var(--text-dim);font-size:13px;">${CLASS_RU[char.char_class] || char.char_class}</span>
        <span style="color:var(--text-dim);font-size:13px;">Ур.${char.level}</span>
      </div>
    </div>
    <div class="char-bars">
      ${bar('❤️ HP', 'hpText', `${char.hp}/${char.hp_max}`, 'bar-hp', 'headerHpBar', (char.hp/char.hp_max)*100)}
      ${bar('⚡ Энергия', 'energyText', `${char.energy}/${char.energy_max}`, 'bar-energy', 'headerEnergyBar', (char.energy/char.energy_max)*100)}
      ${bar(`✨ Опыт &nbsp;<span style="color:var(--arcane-bright);font-weight:bold;">Ур.${char.level}</span>`,
            'expText', expLabel, 'bar-exp', 'headerExpBar', expPct)}
      <div id="regenTimer" style="font-size:10px;color:var(--arcane-bright);text-align:right;margin-top:2px;opacity:0.7;"></div>
    </div>
  `;
  document.getElementById('goldDisplay').textContent = `💰 ${char.gold}`;
}

function bar(labelHtml, textId, textVal, barClass, fillId, pct) {
  return `
    <div>
      <div class="bar-label"><span>${labelHtml}</span><span id="${textId}">${textVal}</span></div>
      <div class="bar-wrap ${barClass}"><div class="bar-fill" id="${fillId}" style="width:${pct}%"></div></div>
    </div>`;
}

// ── Sidebar ─────────────────────────────────────────────────────────────────
function renderSidebarInfo(char) {
  const el = document.getElementById('sidebarCharInfo');
  if (!el) return;
  const hpPerHour = Math.round((char.hp_max / 6) * 10) / 10;
  const energyPerHour = Math.round((char.energy_max / 6) * 10) / 10;
  el.innerHTML = `
    <div style="line-height:2;margin-bottom:8px;">
      <div>🏅 Ранг: <span class="rank-badge rank-${char.rank}" style="font-size:11px;">${char.rank}</span></div>
      <div>⚔️ Класс: ${CLASS_RU[char.char_class] || char.char_class}</div>
      <div>📊 Уровень: ${char.level}</div>
      <div>💰 Золото: ${char.gold}</div>
      <div>🏆 Очки: ${char.f1_points}</div>
    </div>
    ${rankUpBlock(char)}
    <div class="sidebar-section-title" style="padding-left:0;margin-top:12px;">
      Характеристики
      ${char.stat_points > 0
        ? `<span style="color:var(--primary-gold);margin-left:6px;animation:runeFlicker 2s infinite;">+${char.stat_points} очков</span>`
        : ''}
    </div>
    <div class="stats-list">${STAT_DEFS.map(s => statRow(s, char, 4)).join('')}</div>
    <div style="margin-top:8px;font-size:11px;color:var(--text-dim);">
      Реген: +${hpPerHour} HP/ч, +${energyPerHour} ⚡/ч (полное восстановление за 6 часов)
    </div>
  `;
  // Bind rank up button after render
  document.getElementById('rankUpBtn')?.addEventListener('click', window.rankUp);
}

function statRow(s, char, barMult) {
  const val = statVal(char, s.key);
  const btn = char.stat_points > 0
    ? `<button class="stat-up-btn" onclick="window.upgradeStat('${s.api}')" title="+1 ${s.label}">+</button>`
    : `<span class="stat-up-btn stat-up-disabled">+</span>`;
  return `
    <div class="stat-row" title="${s.desc}">
      <div class="stat-icon-wrap">
        <span class="stat-icon">${s.icon}</span>
        <span class="stat-icon-label">${s.label}</span>
      </div>
      <span class="stat-bar-wrap">
        <span class="stat-bar-fill" style="width:${statBarWidth(s.key, val)}%"></span>
      </span>
      <span class="stat-value">${val}</span>
      ${btn}
    </div>`;
}

// ── Rank up block ────────────────────────────────────────────────────────────
const RANK_ORDER = ['E','D','C','B','A','S'];
const RANK_UP_COST = { E:10, D:25, C:50, B:100, A:200 };

function rankUpBlock(char) {
  const isMax = char.rank === 'S';
  const cost  = RANK_UP_COST[char.rank];
  const nextRank = isMax ? null : RANK_ORDER[RANK_ORDER.indexOf(char.rank) + 1];
  const canUp = !isMax && char.rank_points >= cost;
  return `
    <div style="margin:10px 0;padding:10px;border:1px solid var(--border-arcane);border-radius:8px;background:rgba(10,20,40,0.4);">
      <div style="font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Очки ранга</div>
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;">
        <span style="color:var(--primary-gold);font-weight:bold;font-size:14px;">⭐ ${char.rank_points}</span>
        ${isMax
          ? `<span style="font-size:11px;color:var(--rarity-s);">Макс. ранг S</span>`
          : `<span style="font-size:11px;color:var(--text-dim);">До ${nextRank}: ${cost} очков</span>`}
      </div>
      ${!isMax ? `
        <div style="margin-top:8px;">
          <div style="height:4px;background:rgba(0,0,0,0.4);border-radius:2px;overflow:hidden;">
            <div style="height:100%;width:${Math.min(100,(char.rank_points/cost)*100)}%;background:linear-gradient(90deg,var(--arcane),var(--arcane-bright));border-radius:2px;transition:width 0.4s;"></div>
          </div>
        </div>
        <button class="btn ${canUp ? 'btn-success' : ''}" id="rankUpBtn"
          style="width:100%;margin-top:8px;padding:6px;font-size:12px;${!canUp ? 'opacity:0.5;cursor:not-allowed;' : ''}"
          ${!canUp ? 'disabled' : ''}>
          ${canUp ? `🆙 Повысить ранг → ${nextRank}` : `🔒 Нужно ${cost} очков`}
        </button>` : ''}
    </div>`;
}

window.rankUp = async () => {
  try {
    currentChar = await apiFetch('/api/character/rank_up', { method: 'POST' });
    renderCharHeader(currentChar);
    renderSidebarInfo(currentChar);
    showToast(`Ранг повышен до ${currentChar.rank}!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// ── Upgrade stat ─────────────────────────────────────────────────────────────
const STAT_NAMES = { str:'Сила', dex:'Ловкость', con:'Телосложение', int:'Интеллект', wis:'Мудрость', cha:'Харизма', hp:'Здоровье +20' };

window.upgradeStat = async (stat, fromLevelUp = false) => {
  try {
    currentChar = await apiFetch('/api/character/upgrade', {
      method: 'POST',
      body: JSON.stringify({ stat })
    });
    renderCharHeader(currentChar);
    renderSidebarInfo(currentChar);
    if (!fromLevelUp) showToast(`${STAT_NAMES[stat] || stat} +1`, 'success');
    if (document.getElementById('levelUpModal')?.classList.contains('hidden') === false) {
      renderLevelUpStats(currentChar);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// ── Level-up modal ───────────────────────────────────────────────────────────
export function showLevelUpModal(char, newLevel) {
  const modal = document.getElementById('levelUpModal');
  if (!modal) return;
  document.getElementById('levelUpTitle').textContent = `Уровень ${newLevel}!`;
  document.getElementById('levelUpSubtitle').textContent =
    char.exp_next > 0 ? `Следующий уровень: ${char.exp_next.toLocaleString()} опыта` : '';
  renderLevelUpStats(char);
  modal.classList.remove('hidden');
  document.getElementById('levelUpCloseBtn').onclick = () => {
    modal.classList.add('hidden');
    renderSidebarInfo(currentChar);
  };
}

function renderLevelUpStats(char) {
  const container = document.getElementById('levelUpStats');
  const pointsEl  = document.getElementById('levelUpPointsLeft');
  if (!container || !pointsEl) return;
  pointsEl.textContent = char.stat_points > 0
    ? `Свободных очков: ${char.stat_points}` : '✅ Все очки распределены';
  container.innerHTML = STAT_DEFS.map(s => {
    const val  = statVal(char, s.key);
    const canUp = char.stat_points > 0;
    return `
      <div class="stat-row levelup-stat-row">
        <div class="stat-icon-wrap">
          <span class="stat-icon">${s.icon}</span>
          <span class="stat-icon-label">${s.label}</span>
        </div>
        <span style="flex:1;font-size:12px;color:var(--text-dim);">${s.desc}</span>
        <span class="stat-bar-wrap" style="width:80px;flex:none;">
          <span class="stat-bar-fill" style="width:${statBarWidth(s.key, val)}%"></span>
        </span>
        <span class="stat-value" style="min-width:28px;">${val}</span>
        ${canUp
          ? `<button class="stat-up-btn" onclick="window.upgradeStat('${s.api}',true)">+</button>`
          : `<span class="stat-up-btn stat-up-disabled">+</span>`}
      </div>`;
  }).join('');
}

// ── Regen timer ──────────────────────────────────────────────────────────────
export function startRegenTimer(char) {
  let hp     = char.hp,     hpMax     = char.hp_max;
  let energy = char.energy, energyMax = char.energy_max;

  function fmt(sec) {
    const s = Math.max(0, Math.floor(sec));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return `${h}:${String(m).padStart(2,'0')}`;
  }

  function secondsToFull(current, max) {
    if (!max || max <= 0) return 0;
    if (current >= max) return 0;
    const missing = max - current;
    return (missing * FULL_REGEN_SECONDS) / max;
  }

  return setInterval(() => {
    // Use latest values if available (e.g., after actions / reloads)
    if (currentChar) {
      hp = currentChar.hp;
      hpMax = currentChar.hp_max;
      energy = currentChar.energy;
      energyMax = currentChar.energy_max;
    }

    const timerEl = document.getElementById('regenTimer');
    if (!timerEl) return;
    if (hp >= hpMax && energy >= energyMax) { timerEl.textContent = ''; return; }

    const parts = [];
    if (hp < hpMax) parts.push(`❤️ до полного ~${fmt(secondsToFull(hp, hpMax))}`);
    if (energy < energyMax) parts.push(`⚡ до полного ~${fmt(secondsToFull(energy, energyMax))}`);
    timerEl.textContent = parts.join(' · ');
  }, 1000);
}

function _setBar(barId, textId, val, max) {
  const bar  = document.getElementById(barId);
  const text = document.getElementById(textId);
  if (bar)  bar.style.width = `${(val / max) * 100}%`;
  if (text) text.textContent = `${val}/${max}`;
}
