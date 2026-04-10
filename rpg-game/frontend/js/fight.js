import { apiFetch } from './app.js';
import { showToast, openModal, closeModal, setBar } from './ui.js';
import { currentChar, loadCharacter, showLevelUpModal } from './character.js';

export function initFight() {
  document.getElementById('fightCloseBtn').addEventListener('click', () => {
    closeModal('fightModal');
    loadCharacter();
    if (typeof window._onFightClose === 'function') {
      window._onFightClose();
      window._onFightClose = null;
    }
  });
}

window.startFight = async (monsterId, monsterName, monsterHp, onClose) => {
  window._onFightClose = onClose || null;
  const hp    = currentChar?.hp     || 1;
  const hpMax = currentChar?.hp_max || 1;

  document.getElementById('fightTitle').textContent = `⚔️ Битва с ${monsterName}`;
  document.getElementById('fightLog').innerHTML = '';
  document.getElementById('fightResult').style.display = 'none';
  document.getElementById('fightActions').style.display = 'flex';
  document.getElementById('fightPlayerHp').textContent  = `${hp}/${hpMax}`;
  document.getElementById('fightMonsterHp').textContent = `${monsterHp}/${monsterHp}`;
  setBar('fightPlayerBar',  hp, hpMax);
  setBar('fightMonsterBar', 1, 1);

  // Replace buttons with clean clones (removes disabled + all stale listeners)
  ['fightStartBtn', 'fightCancelBtn'].forEach(id => {
    const el = document.getElementById(id);
    const clone = el.cloneNode(true);
    clone.disabled = false;
    el.replaceWith(clone);
  });

  document.getElementById('fightCancelBtn').addEventListener('click', () => closeModal('fightModal'));

  openModal('fightModal');

  document.getElementById('fightStartBtn').addEventListener('click', async () => {
    document.getElementById('fightStartBtn').disabled  = true;
    document.getElementById('fightCancelBtn').disabled = true;
    const log = document.getElementById('fightLog');
    log.innerHTML = '<div class="fight-log-entry" style="color:var(--text-dim)">⚔️ Бой начался...</div>';

    try {
      const result = await apiFetch('/api/fight', {
        method: 'POST',
        body: JSON.stringify({ monster_id: monsterId })
      });

      for (const line of result.log) {
        await new Promise(r => setTimeout(r, 200));
        const entry = document.createElement('div');
        entry.className = 'fight-log-entry';
        entry.textContent = line;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
      }

      setBar('fightPlayerBar',  result.hp_remaining, hpMax);
      setBar('fightMonsterBar', result.victory ? 0 : monsterHp * 0.3, monsterHp);
      document.getElementById('fightPlayerHp').textContent = `${result.hp_remaining}/${hpMax}`;

      await new Promise(r => setTimeout(r, 500));
      document.getElementById('fightActions').style.display = 'none';
      document.getElementById('fightResult').style.display  = 'block';
      document.getElementById('fightResultIcon').textContent = result.victory ? '🏆' : '💀';
      document.getElementById('fightResultText').textContent = result.victory ? 'Победа!' : 'Поражение';
      document.getElementById('fightResultRewards').innerHTML = result.victory
        ? `+${result.exp_gained} опыта &nbsp; +${result.gold_gained} 💰`
        : `+${result.exp_gained} опыта`;

      showToast(result.victory ? `Победа! +${result.exp_gained} опыта` : 'Поражение...', result.victory ? 'success' : 'warning');

      const levelUpEntry = result.log.find(l => l.includes('Уровень') && l.includes('очков'));
      if (levelUpEntry) {
        const match = levelUpEntry.match(/Уровень (\d+)/);
        const updated = await loadCharacter();
        if (match) showLevelUpModal(updated, parseInt(match[1]));
      }
    } catch (err) {
      showToast(err.message, 'error');
      closeModal('fightModal');
    }
  });
};
