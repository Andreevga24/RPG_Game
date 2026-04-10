import { apiFetch } from './app.js';
import { showToast, formatTimer, openModal, closeModal } from './ui.js';
import { loadCharacter } from './character.js';

const CLASS_ICONS = { Tauran:'🐂', Gnombaf:'🧙', Arachnid:'🕷️', Angel:'👼' };
const CLASS_RU    = { Tauran:'Тауран', Gnombaf:'Гномбаф', Arachnid:'Арахнид', Angel:'Ангел' };
const RANK_GLOW   = { S:'var(--rarity-s)', A:'var(--rarity-a)', B:'var(--rarity-b)', C:'var(--rarity-c)', D:'var(--rarity-d)', E:'var(--text-dim)' };
const BOSS_ICONS  = { S:'👹', A:'🐉', B:'🧟', C:'🌑', D:'💀', E:'👻' };

let pollInterval = null;
let countdownInterval = null;

export async function loadRaid() {
  clearInterval(pollInterval);
  clearInterval(countdownInterval);
  const el = document.getElementById('raidContent');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const data = await apiFetch('/api/raid/status');
    if (data.is_open && data.gate) {
      renderGateOpen(data.gate);
      pollInterval = setInterval(async () => {
        const d = await apiFetch('/api/raid/status').catch(() => null);
        if (d?.is_open && d?.gate) updateBossHp(d.gate);
        else loadRaid();
      }, 10000);
    } else {
      renderGateClosed(data.seconds_until_open || 3600);
    }
  } catch (err) {
    el.innerHTML = `<div style="color:var(--danger);text-align:center;padding:40px;">⚠️ ${err.message}</div>`;
  }
}

// ── Closed screen ─────────────────────────────────────────────────────────────
function renderGateClosed(seconds) {
  clearInterval(countdownInterval);
  const el = document.getElementById('raidContent');
  el.innerHTML = `
    <div style="text-align:center;padding:48px 20px;animation:fadeIn 0.4s ease;">
      <div style="font-size:72px;margin-bottom:16px;filter:grayscale(0.5);">🚪</div>
      <div style="font-size:20px;color:var(--text-dim);text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">Врата закрыты</div>
      <div style="font-size:14px;color:var(--text-dim);margin-bottom:24px;">Следующее открытие через</div>
      <div style="font-size:36px;color:var(--arcane-bright);font-weight:bold;font-family:monospace;" id="gateCountdown">${formatTimer(seconds)}</div>
      <div style="font-size:12px;color:var(--text-dim);margin-top:8px;">часов : минут : секунд</div>
      <button class="btn" style="margin-top:32px;padding:10px 28px;" onclick="window._forceOpenGate()">🔧 Открыть (тест)</button>
    </div>`;
  let rem = seconds;
  countdownInterval = setInterval(() => {
    const el = document.getElementById('gateCountdown');
    if (el) el.textContent = formatTimer(Math.max(0, --rem));
    if (rem <= 0) { clearInterval(countdownInterval); loadRaid(); }
  }, 1000);
}

// ── Open screen ───────────────────────────────────────────────────────────────
function renderGateOpen(gate) {
  const el = document.getElementById('raidContent');
  const glow = RANK_GLOW[gate.rank] || 'var(--text-dim)';
  const icon = BOSS_ICONS[gate.rank] || '👹';
  const hpPct = Math.max(0, (gate.boss_hp / gate.boss_hp_max) * 100);
  const groups = Array.isArray(gate.groups) ? gate.groups : [];

  el.innerHTML = `
    <div style="animation:fadeIn 0.4s ease;">
      <!-- Gate header -->
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;flex-wrap:wrap;">
        <div style="font-size:48px;filter:drop-shadow(0 0 16px ${glow});animation:arcanePulse 2s infinite;">🚪</div>
        <div>
          <div style="font-size:20px;color:${glow};font-weight:bold;letter-spacing:1px;">ВРАТА ОТКРЫТЫ</div>
          <div style="font-size:13px;color:var(--text-dim);">Ранг: <span class="rank-badge rank-${gate.rank}">${gate.rank}</span>
            &nbsp;Закроются через: <span id="closeTimer" style="color:var(--arcane-bright);">${formatTimer(gate.seconds_until_close)}</span>
          </div>
        </div>
      </div>

      <!-- Boss card -->
      <div style="padding:20px;border:2px solid ${glow};border-radius:12px;background:rgba(10,5,20,0.7);margin-bottom:20px;text-align:center;">
        <div style="font-size:64px;filter:drop-shadow(0 0 24px ${glow});animation:arcanePulse 1.5s infinite;margin-bottom:8px;">${icon}</div>
        <div style="font-size:22px;color:var(--text-light);font-weight:bold;margin-bottom:12px;">${gate.boss_name}</div>
        <div style="font-size:12px;color:var(--text-dim);margin-bottom:6px;">
          HP: <b style="color:var(--text-light);">${gate.boss_hp.toLocaleString()}</b> / ${gate.boss_hp_max.toLocaleString()}
        </div>
        <div style="height:14px;background:rgba(0,0,0,0.5);border-radius:7px;overflow:hidden;border:1px solid ${glow};margin-bottom:16px;">
          <div id="bossHpBar" style="height:100%;width:${hpPct}%;background:linear-gradient(90deg,#8b0000,${glow});border-radius:7px;transition:width 0.5s;"></div>
        </div>
        <button class="btn btn-danger" id="attackBtn" style="padding:12px 36px;font-size:16px;">
          ⚔️ Атаковать босса <span style="font-size:11px;opacity:0.7;">(-10 ⚡)</span>
        </button>
      </div>

      <!-- Attack log -->
      <div id="attackLog" style="max-height:160px;overflow-y:auto;margin-bottom:20px;display:none;
        background:rgba(0,0,0,0.3);border:1px solid var(--border-arcane);border-radius:8px;padding:10px;
        font-size:12px;color:var(--text-dim);"></div>

      <!-- Groups -->
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div style="font-size:15px;color:var(--text-light);">⚔️ Группы (${groups.length})</div>
        <button class="btn btn-success" style="padding:6px 16px;font-size:12px;" id="createGroupBtn">+ Создать группу</button>
      </div>
      <div id="groupsList">
        ${groups.length ? groups.map(renderGroupCard).join('') : '<p style="color:var(--text-dim);font-size:13px;">Нет групп. Войди один или создай группу.</p>'}
      </div>
    </div>`;

  // Close timer
  let rem = gate.seconds_until_close;
  countdownInterval = setInterval(() => {
    const el = document.getElementById('closeTimer');
    if (el) el.textContent = formatTimer(Math.max(0, --rem));
    if (rem <= 0) { clearInterval(countdownInterval); loadRaid(); }
  }, 1000);

  // Attack button
  document.getElementById('attackBtn').addEventListener('click', attackBoss);

  // Group modal
  document.getElementById('createGroupBtn').addEventListener('click', () => openModal('groupModal'));
  document.getElementById('createGroupBtn2')?.addEventListener('click', () => openModal('groupModal'));
  document.getElementById('cancelGroupBtn')?.addEventListener('click', () => closeModal('groupModal'));
  document.getElementById('createGroupConfirmBtn')?.addEventListener('click', createGroup);
}

function updateBossHp(gate) {
  const bar  = document.getElementById('bossHpBar');
  const text = document.querySelector('#raidContent [style*="HP:"] b');
  if (bar)  bar.style.width = `${Math.max(0,(gate.boss_hp/gate.boss_hp_max)*100)}%`;
  if (text) text.textContent = gate.boss_hp.toLocaleString();
}

// ── Attack ────────────────────────────────────────────────────────────────────
async function attackBoss() {
  const btn = document.getElementById('attackBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Атакуем...';
  try {
    const res = await apiFetch('/api/raid/attack', { method: 'POST' });

    // Show log
    const logEl = document.getElementById('attackLog');
    logEl.style.display = 'block';
    logEl.innerHTML = res.log.map(l => `<div style="margin-bottom:2px;">▸ ${l}</div>`).join('');
    logEl.scrollTop = logEl.scrollHeight;

    // Update boss HP bar
    const hpPct = Math.max(0, (res.boss_hp / res.boss_hp_max) * 100);
    const bar = document.getElementById('bossHpBar');
    if (bar) bar.style.width = `${hpPct}%`;

    showToast(`⚔️ ${res.damage_dealt.toLocaleString()} урона! +${res.rank_points} очков ранга`, 'success');
    await loadCharacter();

    if (res.boss_defeated) {
      showToast('💀 Босс повержен! Врата закрываются!', 'success');
      setTimeout(loadRaid, 2000);
    }
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '⚔️ Атаковать босса <span style="font-size:11px;opacity:0.7;">(-10 ⚡)</span>'; }
  }
}

// ── Groups ────────────────────────────────────────────────────────────────────
function renderGroupCard(group) {
  const membersHtml = group.members.map(m => `
    <div class="member-avatar ${m.is_ready ? 'ready' : ''}"
      title="${m.username} (${CLASS_RU[m.char_class] || m.char_class}) — ${m.damage_dealt.toLocaleString()} урона">
      ${CLASS_ICONS[m.char_class] || '👤'}
    </div>`).join('');
  const emptySlots = Array(MAX_GROUP - group.member_count)
    .fill('<div class="member-avatar" style="opacity:0.2;border-style:dashed;">+</div>').join('');

  return `
    <div class="group-card" style="animation:fadeIn 0.3s ease;margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px;">
        <div>
          <div style="font-size:15px;color:var(--text-light);">${group.name}</div>
          <div style="font-size:11px;color:var(--text-dim);">${group.member_count}/${MAX_GROUP} участников</div>
        </div>
        <button class="btn" style="padding:5px 12px;font-size:12px;" onclick="window.joinGroup(${group.id})">Вступить</button>
      </div>
      <div class="group-members">${membersHtml}${emptySlots}</div>
    </div>`;
}

const MAX_GROUP = 10;

async function createGroup() {
  const name = document.getElementById('groupName').value.trim();
  if (!name) { showToast('Введите название', 'warning'); return; }
  try {
    await apiFetch('/api/raid/group', { method: 'POST', body: JSON.stringify({ name }) });
    closeModal('groupModal');
    showToast('Группа создана!', 'success');
    loadRaid();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

window.joinGroup = async (groupId) => {
  try {
    await apiFetch(`/api/raid/group/${groupId}/join`, { method: 'POST' });
    showToast('Вступили в группу!', 'success');
    loadRaid();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window._forceOpenGate = async () => {
  try {
    await apiFetch('/api/raid/open', { method: 'POST' });
    loadRaid();
  } catch (err) {
    showToast(err.message, 'error');
  }
};
