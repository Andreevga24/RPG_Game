import { isLoggedIn, removeToken } from './app.js';
import { showToast } from './ui.js';
import { loadCharacter, startRegenTimer } from './character.js';
import { loadCity } from './city.js';
import { loadRaid } from './raid.js';
import { loadLeaderboard } from './leaderboard.js';
import { loadShop } from './shop.js';
import { initFight } from './fight.js';
import { logout } from './auth.js';

// Guard: redirect if not logged in
if (!isLoggedIn()) {
  window.location.href = 'login.html';
}

const tabs = { city: loadCity, raid: loadRaid, leaderboard: loadLeaderboard, shop: loadShop };
let activeTab = 'city';
let tabLoaded = { city: false, raid: false, leaderboard: false, shop: false };

async function init() {
  try {
    const char = await loadCharacter();
    startRegenTimer(char);
  } catch (err) {
    if (err.message?.includes('not found') || err.message?.includes('404')) {
      window.location.href = 'create-character.html';
      return;
    }
    showToast('Ошибка загрузки персонажа', 'error');
  }

  initFight();
  loadCity();
  tabLoaded.city = true;

  // Tab navigation
  document.querySelectorAll('[data-tab]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab(link.dataset.tab);
      // Close sidebar on mobile
      document.getElementById('gameSidebar').classList.remove('open');
    });
  });

  // Burger menu
  document.getElementById('burgerBtn').addEventListener('click', () => {
    document.getElementById('gameSidebar').classList.toggle('open');
  });

  // Logout
  document.getElementById('logoutBtn').addEventListener('click', logout);
}

function switchTab(tab) {
  if (activeTab === tab) return;

  // Hide current
  document.getElementById(`tab-${activeTab}`).style.display = 'none';
  document.querySelector(`[data-tab="${activeTab}"]`)?.classList.remove('active');

  // Show new
  activeTab = tab;
  document.getElementById(`tab-${tab}`).style.display = 'block';
  document.querySelector(`[data-tab="${tab}"]`)?.classList.add('active');

  // Load if not loaded
  if (!tabLoaded[tab]) {
    tabs[tab]?.();
    tabLoaded[tab] = true;
  }

  // Update URL without reload
  history.pushState({ tab }, '', `?tab=${tab}`);
}

// Handle browser back/forward
window.addEventListener('popstate', (e) => {
  const tab = e.state?.tab || 'city';
  switchTab(tab);
});

// Init from URL param
const urlTab = new URLSearchParams(location.search).get('tab');
if (urlTab && tabs[urlTab]) {
  activeTab = 'city'; // reset so switchTab works
  document.getElementById('tab-city').style.display = 'none';
}

init();
