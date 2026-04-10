export function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

export function showFieldError(id, message) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = message;
  el.classList.add('visible');
  const input = el.previousElementSibling?.tagName === 'INPUT'
    ? el.previousElementSibling
    : el.closest('.form-group')?.querySelector('input');
  if (input) input.classList.add('error');
}

export function clearFieldError(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = '';
  el.classList.remove('visible');
  const input = el.closest('.form-group')?.querySelector('input');
  if (input) input.classList.remove('error');
}

export function openModal(id) {
  document.getElementById(id)?.classList.remove('hidden');
}

export function closeModal(id) {
  document.getElementById(id)?.classList.add('hidden');
}

export function setBar(barId, current, max) {
  const el = document.getElementById(barId);
  if (!el) return;
  el.style.width = `${Math.max(0, Math.min(100, (current / max) * 100))}%`;
}

export function formatTimer(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map(v => String(v).padStart(2, '0')).join(':');
}

export function skeletonCards(count = 3) {
  return Array.from({ length: count }, () =>
    `<div class="skeleton skeleton-card"></div>`
  ).join('');
}
