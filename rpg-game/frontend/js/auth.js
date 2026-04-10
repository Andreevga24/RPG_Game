import { apiFetch, setToken, removeToken } from './app.js';

export async function login(username, password) {
  const data = await apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
  setToken(data.access_token);
  return data;
}

export async function register(username, email, password) {
  const data = await apiFetch('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password })
  });
  setToken(data.access_token);
  return data;
}

export function logout() {
  removeToken();
  window.location.href = 'login.html';
}
