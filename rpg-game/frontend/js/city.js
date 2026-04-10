import { apiFetch } from './app.js';
import { showToast, skeletonCards } from './ui.js';
import { currentChar, loadCharacter } from './character.js';

const MONSTER_ICONS = { S:'👹', A:'🐉', B:'🧟', C:'🐺', D:'🐗', E:'🐀' };
const RANK_GLOW = {
  S:'var(--rarity-s)', A:'var(--rarity-a)', B:'var(--rarity-b)',
  C:'var(--rarity-c)', D:'var(--rarity-d)', E:'var(--text-dim)'
};
const CITY_ICONS = ['🌲', '🏔️', '🌑'];

let cities = [];
let currentCityIndex = 0;
let onArena = false;

export async function loadCity() {
  const el = document.getElementById('cityContent');
  el.innerHTML = skeletonCards(2);
  try {
    cities = await apiFetch('/api/city');
    if (!cities.length) { el.innerHTML = '<p style="color:var(--text-dim)">Города не найдены</p>'; return; }
    onArena = false;
    renderCityScreen();
  } catch (err) {
    el.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger)">⚠️ ${err.message}</div>`;
  }
}

// ── City overview screen ─────────────────────────────────────────────────────
function renderCityScreen() {
  const el = document.getElementById('cityContent');
  const city = cities[currentCityIndex];
  const cityBtns = cities.map((c, i) =>
    `<button class="btn ${i === currentCityIndex ? 'btn-success' : ''}"
      style="padding:6px 14px;font-size:12px;" onclick="window.switchCity(${i})">${c.name}</button>`
  ).join('');

  el.innerHTML = `
    <div style="animation:fadeIn 0.4s ease;">
      <!-- City card -->
      <div class="city-card" style="margin-bottom:24px;">
        <div style="display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap;gap:12px;">
          <div>
            <div class="city-name">${CITY_ICONS[currentCityIndex] || '🏙️'} ${city.name}</div>
            <div class="city-desc">${city.description}</div>
            <div style="margin-top:8px;font-size:12px;color:var(--text-dim);">
              Ранг локации: <span class="rank-badge rank-${city.min_rank}" style="font-size:10px;">${city.min_rank}</span>
            </div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">${cityBtns}</div>
        </div>
      </div>

      <!-- Arena entry -->
      <div style="display:flex;flex-direction:column;align-items:center;gap:16px;
        padding:32px;border:1px solid var(--border-arcane);border-radius:12px;
        background:rgba(10,20,40,0.5);text-align:center;">
        <div style="font-size:56px;animation:arcanePulse 2s infinite;">⚔️</div>
        <div style="font-size:20px;color:var(--arcane-bright);font-weight:bold;letter-spacing:1px;">Арена</div>
        <div style="font-size:13px;color:var(--text-dim);max-width:320px;">
          Войди на арену и сразись с монстром. Каждый бой стоит <b style="color:var(--arcane-bright)">5 ⚡</b>.
          Можно убежать за <b style="color:var(--arcane-bright)">1 ⚡</b>.
        </div>
        <button class="btn btn-danger" style="padding:12px 36px;font-size:16px;margin-top:8px;"
          id="enterArenaBtn">🚪 Войти на арену</button>
      </div>
    </div>
  `;

  document.getElementById('enterArenaBtn').addEventListener('click', enterArena);
}

// ── Arena screen ─────────────────────────────────────────────────────────────
async function enterArena() {
  onArena = true;
  const el = document.getElementById('cityContent');
  el.innerHTML = '<div class="spinner" style="margin:60px auto;"></div>';
  try {
    const city = cities[currentCityIndex];
    const m = await apiFetch(`/api/fight/random_monster?city_id=${city.id}`);
    renderArena(m);
  } catch (err) {
    el.innerHTML = `<div style="color:var(--danger);text-align:center;padding:40px;">⚠️ ${err.message}</div>`;
  }
}

function renderArena(m) {
  const el = document.getElementById('cityContent');
  const icon = MONSTER_ICONS[m.rank] || '👾';
  const glow = RANK_GLOW[m.rank] || 'var(--text-dim)';

  el.innerHTML = `
    <div style="animation:fadeIn 0.35s ease;">
      <!-- Back button -->
      <button class="btn" style="margin-bottom:20px;padding:6px 16px;font-size:12px;" id="leaveArenaBtn">
        ← Покинуть арену
      </button>

      <!-- Monster encounter -->
      <div style="display:flex;flex-direction:column;align-items:center;gap:20px;padding:28px;
        border:1px solid var(--border-arcane);border-radius:12px;background:rgba(10,20,40,0.6);">

        <div style="font-size:13px;color:var(--text-dim);text-transform:uppercase;letter-spacing:2px;">
          Противник появился!
        </div>

        <div style="text-align:center;">
          <div style="font-size:80px;filter:drop-shadow(0 0 24px ${glow});animation:arcanePulse 2s infinite;">${icon}</div>
          <div style="font-size:24px;color:var(--text-light);margin:10px 0;font-weight:bold;">${m.name}</div>
          <span class="rank-badge rank-${m.rank}" style="font-size:13px;">${m.rank}</span>
        </div>

        <div style="display:flex;gap:20px;flex-wrap:wrap;justify-content:center;font-size:14px;color:var(--text-dim);">
          <span>❤️ <b style="color:var(--text-light)">${m.hp}</b></span>
          <span>⚔️ <b style="color:var(--text-light)">${m.attack}</b></span>
          <span>🛡️ <b style="color:var(--text-light)">${m.defense}</b></span>
          <span style="color:var(--exp-color)">✨ +${m.exp_reward} опыта</span>
          <span style="color:var(--primary-gold)">💰 +${m.gold_reward}</span>
        </div>

        <div style="display:flex;gap:14px;flex-wrap:wrap;justify-content:center;margin-top:8px;">
          <button class="btn btn-danger" style="padding:12px 32px;font-size:15px;" id="arenaFightBtn">
            ⚔️ Сразиться <span style="font-size:11px;opacity:0.7;">(-5 ⚡)</span>
          </button>
          <button class="btn" style="padding:12px 32px;font-size:15px;" id="arenaFleeBtn">
            🏃 Убежать <span style="font-size:11px;opacity:0.7;">(-1 ⚡)</span>
          </button>
        </div>
      </div>
    </div>
  `;

  document.getElementById('leaveArenaBtn').addEventListener('click', () => {
    onArena = false;
    renderCityScreen();
  });

  document.getElementById('arenaFightBtn').addEventListener('click', () => {
    window.startFight(m.id, m.name, m.hp, () => enterArena());
  });

  document.getElementById('arenaFleeBtn').addEventListener('click', async () => {
    const btn = document.getElementById('arenaFleeBtn');
    btn.disabled = true;
    try {
      const res = await apiFetch('/api/fight/flee', { method: 'POST' });
      const bar  = document.getElementById('headerEnergyBar');
      const text = document.getElementById('energyText');
      if (bar)  bar.style.width = `${(res.energy / res.energy_max) * 100}%`;
      if (text) text.textContent = `${res.energy}/${res.energy_max}`;
      if (currentChar) currentChar.energy = res.energy;
      showToast('Вы убежали! -1 ⚡', 'warning');
      enterArena();
    } catch (err) {
      showToast(err.message, 'error');
      btn.disabled = false;
    }
  });
}

window.switchCity = (index) => {
  currentCityIndex = index;
  onArena = false;
  renderCityScreen();
};
