/** База API: window.RPG_API_BASE или localStorage rpg_api_base, иначе IPv4 (избегает проблем localhost → ::1). */
export function apiBase() {
  if (typeof window !== 'undefined' && window.RPG_API_BASE) {
    return String(window.RPG_API_BASE).replace(/\/$/, '');
  }
  try {
    const s = localStorage.getItem('rpg_api_base');
    if (s) return s.replace(/\/$/, '');
  } catch (_) {}
  return 'http://127.0.0.1:8000';
}

export function getToken() {
  return localStorage.getItem('rpg_token');
}

export function setToken(token) {
  localStorage.setItem('rpg_token', token);
}

export function removeToken() {
  localStorage.removeItem('rpg_token');
}

export function isLoggedIn() {
  return !!getToken();
}

export async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res;
  const base = apiBase();
  try {
    res = await fetch(base + path, { ...options, headers });
  } catch {
    throw new Error('Сервер недоступен. Проверьте подключение.');
  }

  if (res.status === 401) {
    removeToken();
    window.location.href = 'login.html';
    throw new Error('Сессия истекла');
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    const msg =
      typeof d === 'string'
        ? d
        : Array.isArray(d)
          ? d.map((x) => x.msg || x).join(', ')
          : `Ошибка ${res.status}`;
       if (
      res.status === 404 &&
      (path.startsWith('/api/shop') || path.startsWith('/api/inventory')) &&
      (d === 'Not Found' || d === undefined)
    ) {
      throw new Error(
        `Маршруты магазина не найдены (404) на ${base}. Запустите актуальный бэкенд: rpg-game/backend/start_backend.bat или в терминале из папки backend: py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`
      );
    }
    throw new Error(msg);
  }
  return data;
}
