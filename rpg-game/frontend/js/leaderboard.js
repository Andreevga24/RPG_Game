import { apiFetch } from './app.js';
import { skeletonCards } from './ui.js';

const RANKS   = ['E','D','C','B','A','S'];
const CLASSES = ['Tauran','Gnombaf','Arachnid','Angel'];
const CLASS_RU = { Tauran:'Тауран', Gnombaf:'Гномбаф', Arachnid:'Арахнид', Angel:'Ангел' };
const MEDALS  = { 1:'🥇', 2:'🥈', 3:'🥉' };

export async function loadLeaderboard(rankFilter = '', classFilter = '') {
  const el = document.getElementById('leaderboardContent');
  el.innerHTML = skeletonCards(5);
  try {
    const params = new URLSearchParams();
    if (rankFilter)  params.set('rank_filter',  rankFilter);
    if (classFilter) params.set('class_filter', classFilter);
    renderLeaderboard(await apiFetch(`/api/leaderboard?${params}`), rankFilter, classFilter);
  } catch (err) {
    el.innerHTML = `<div style="color:var(--danger);text-align:center;padding:40px;">⚠️ ${err.message}</div>`;
  }
}

function renderLeaderboard(entries, rankFilter, classFilter) {
  const rankOpts  = RANKS.map(r =>
    `<option value="${r}" ${r === rankFilter ? 'selected' : ''}>${r}</option>`).join('');
  const classOpts = CLASSES.map(c =>
    `<option value="${c}" ${c === classFilter ? 'selected' : ''}>${CLASS_RU[c]}</option>`).join('');

  const rows = entries.map((e, i) => `
    <tr class="${i < 3 ? `pos-${i+1}` : ''}" style="animation-delay:${i*0.05}s">
      <td class="pos-num">${MEDALS[e.rank_position] || e.rank_position}</td>
      <td>${e.username}</td>
      <td><span class="rank-badge rank-${e.rank}">${e.rank}</span></td>
      <td>${CLASS_RU[e.char_class] || e.char_class}</td>
      <td style="color:var(--primary-gold);font-weight:bold;">${e.f1_points.toLocaleString()}</td>
    </tr>`).join('');

  document.getElementById('leaderboardContent').innerHTML = `
    <div style="margin-bottom:20px;">
      <div style="font-size:22px;color:var(--primary-gold);margin-bottom:16px;">🏆 Таблица лидеров</div>
      <div class="filter-bar">
        <select class="filter-select" id="rankFilter" onchange="window.filterLeaderboard()">
          <option value="">Все ранги</option>${rankOpts}
        </select>
        <select class="filter-select" id="classFilter" onchange="window.filterLeaderboard()">
          <option value="">Все классы</option>${classOpts}
        </select>
      </div>
    </div>
    ${entries.length === 0
      ? '<p style="color:var(--text-dim);text-align:center;padding:40px;">Нет данных</p>'
      : `<div style="overflow-x:auto;"><table class="leaderboard-table">
          <thead><tr><th>#</th><th>Игрок</th><th>Ранг</th><th>Класс</th><th>Очки</th></tr></thead>
          <tbody>${rows}</tbody>
        </table></div>`}`;
}

window.filterLeaderboard = () => loadLeaderboard(
  document.getElementById('rankFilter')?.value  || '',
  document.getElementById('classFilter')?.value || ''
);
