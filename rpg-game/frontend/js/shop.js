import { apiFetch, apiBase } from './app.js';
import { showToast } from './ui.js';
import { loadCharacter, currentChar } from './character.js';

const CAT_LABELS = {
  potion: '🧪 Зелья',
  weapon: '⚔️ Оружие',
  armor: '🛡️ Броня',
  pet: '🐾 Питомцы',
  misc: '📦 Прочее',
};

let shopData = null;

async function apiRootMeta() {
  const base = apiBase();
  const r = await fetch(`${base}/`).catch(() => null);
  if (!r?.ok) return { ok: false, base, meta: null };
  const meta = await r.json().catch(() => ({}));
  return { ok: true, base, meta };
}

export async function loadShop() {
  const el = document.getElementById('shopContent');
  if (!el) return;
  el.innerHTML = '<div class="spinner" style="margin:48px auto;"></div>';
  try {
    const { ok, base, meta } = await apiRootMeta();
    if (!ok) {
      el.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);max-width:520px;margin:0 auto;line-height:1.6;">
        <p>Нет ответа от API по адресу <code style="color:var(--arcane-bright)">${base}</code></p>
        <p style="font-size:13px;color:var(--text-dim);">Запустите сервер из папки <code>rpg-game/backend</code> (файл <strong>start_backend.bat</strong>) или командой:<br>
        <code style="font-size:12px;">py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000</code></p>
        <p style="font-size:12px;color:var(--text-dim);">Другой порт/ПК: в консоли браузера выполните<br><code>localStorage.setItem('rpg_api_base','http://127.0.0.1:8000')</code> и обновите страницу.</p>
      </div>`;
      return;
    }
    if (meta.shop_enabled !== true) {
      el.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);max-width:520px;margin:0 auto;line-height:1.6;">
        <p>Запущена <strong>старая версия</strong> API (без магазина) на <code>${base}</code></p>
        <p style="font-size:13px;color:var(--text-dim);">Остановите все старые окна Uvicorn и снова запустите бэкенд из актуальной папки проекта (см. <strong>start_backend.bat</strong>).</p>
      </div>`;
      return;
    }
    const [shop, inv] = await Promise.all([
      apiFetch('/api/shop'),
      apiFetch('/api/inventory'),
    ]);
    shopData = shop;
    renderShop(el, shop, inv, nameMapFromShop(shop));
  } catch (err) {
    el.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger)">⚠️ ${err.message}</div>`;
  }
}

function nameMapFromShop(shop) {
  const m = {};
  (shop.categories || []).forEach((c) => (c.items || []).forEach((i) => (m[i.id] = i.name)));
  return m;
}

function renderShop(container, shop, inv, nameMap = {}) {
  const gold = inv.gold ?? currentChar?.gold ?? 0;
  const invMap = Object.fromEntries((inv.items || []).map((i) => [i.id, i.quantity]));
  const eq = inv.equipment || {};

  const shopBlock = (shop.categories || [])
    .map(
      (cat) => `
    <div class="shop-category">
      <h3 class="shop-cat-title">${CAT_LABELS[cat.id] || cat.id}</h3>
      <div class="shop-grid">
        ${cat.items.map((it) => shopItemCard(it, invMap[it.id] || 0, gold)).join('')}
      </div>
    </div>`
    )
    .join('');

  const invItems = inv.items || [];
  const invBlock =
    invItems.length === 0
      ? '<p style="color:var(--text-dim);text-align:center;">Рюкзак пуст</p>'
      : `<div class="shop-grid">${invItems.map((it) => invItemCard(it, eq)).join('')}</div>`;

  container.innerHTML = `
    <div class="shop-layout" style="animation:fadeIn 0.35s ease;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px;">
        <h2 style="margin:0;color:var(--primary-gold);">🏪 Торговля</h2>
        <div style="font-size:18px;color:var(--primary-gold);">💰 ${gold}</div>
      </div>
      <p style="color:var(--text-dim);font-size:13px;margin-bottom:24px;">
        Покупайте за золото, используйте зелья, экипируйте оружие и броню. Питомцы пока без боевых бонусов.
      </p>
      <div class="shop-panels">
        <section class="shop-panel">
          <h3 class="shop-panel-title">Магазин</h3>
          ${shopBlock}
        </section>
        <section class="shop-panel">
          <h3 class="shop-panel-title">Рюкзак и экипировка</h3>
          ${equipmentStrip(eq, nameMap)}
          ${invBlock}
        </section>
      </div>
    </div>`;

  bindShopActions(container, invMap, gold);
}

function equipmentStrip(eq, nameMap) {
  const w = eq.weapon_id;
  const a = eq.armor_id;
  const p = eq.pet_id;
  const b = eq.bonuses || {};
  const label = (id) => (id ? nameMap[id] || id : '—');
  return `
    <div class="equip-strip">
      <div><span class="eq-label">Оружие</span> <span class="eq-val">${label(w)}</span>
        ${w ? `<button type="button" class="btn btn-sm" data-unequip="weapon">Снять</button>` : ''}</div>
      <div><span class="eq-label">Броня</span> <span class="eq-val">${label(a)}</span>
        ${a ? `<button type="button" class="btn btn-sm" data-unequip="armor">Снять</button>` : ''}</div>
      <div><span class="eq-label">Питомец</span> <span class="eq-val">${label(p)}</span>
        ${p ? `<button type="button" class="btn btn-sm" data-unequip="pet">Снять</button>` : ''}</div>
      <div class="eq-bonuses">Бонусы: ⚔️+${b.str || 0} 🔮+${b.int || 0} 🛡️+${b.def || 0}</div>
    </div>`;
}

function shopItemCard(it, owned, gold) {
  const affordable = gold >= it.price;
  const soon = it.coming_soon ? '<span class="badge-soon">скоро</span>' : '';
  return `
    <div class="shop-card" data-item-id="${it.id}">
      <div class="shop-card-name">${it.name} ${soon}</div>
      <div class="shop-card-desc">${it.description}</div>
      <div class="shop-card-meta">
        <span class="shop-price">${it.price} 💰</span>
        ${owned ? `<span class="shop-owned">есть: ${owned}</span>` : ''}
      </div>
      <button type="button" class="btn btn-success shop-buy" data-buy="${it.id}"
        ${!affordable ? 'disabled' : ''}>Купить</button>
    </div>`;
}

function invItemCard(it, eq) {
  const isWeapon = it.equippable === 'weapon' && eq.weapon_id === it.id;
  const isArmor = it.equippable === 'armor' && eq.armor_id === it.id;
  const isPet = it.equippable === 'pet' && eq.pet_id === it.id;
  const equipped = isWeapon || isArmor || isPet;
  const useBtn = it.consumable
    ? `<button type="button" class="btn btn-sm" data-use="${it.id}">Применить</button>`
    : '';
  const eqBtn =
    it.equippable && !it.consumable
      ? `<button type="button" class="btn btn-sm" data-equip="${it.id}" ${equipped ? 'disabled' : ''}>${
          equipped ? 'Надето' : 'Надеть'
        }</button>`
      : '';
  const soon = it.coming_soon ? ' <span class="badge-soon">в разработке</span>' : '';
  return `
    <div class="shop-card inv-card">
      <div class="shop-card-name">${it.name}${soon}</div>
      <div class="shop-card-desc">${it.description}</div>
      <div class="shop-card-meta">×${it.quantity}</div>
      <div class="inv-actions">${useBtn}${eqBtn}</div>
    </div>`;
}

function bindShopActions(container, _invMap, _gold) {
  container.querySelectorAll('[data-buy]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-buy');
      try {
        const res = await apiFetch('/api/inventory/buy', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ item_id: id, quantity: 1 }),
        });
        showToast('Куплено!', 'success');
        document.getElementById('goldDisplay').textContent = `💰 ${res.gold}`;
        if (currentChar) currentChar.gold = res.gold;
        loadShop();
      } catch (e) {
        showToast(e.message || 'Ошибка', 'error');
      }
    });
  });

  container.querySelectorAll('[data-use]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-use');
      try {
        const res = await apiFetch('/api/inventory/use', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ item_id: id }),
        });
        showToast(res.message || 'Применено', 'success');
        await loadCharacter();
        loadShop();
      } catch (e) {
        showToast(e.message || 'Ошибка', 'error');
      }
    });
  });

  container.querySelectorAll('[data-equip]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-equip');
      try {
        await apiFetch('/api/inventory/equip', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ item_id: id }),
        });
        showToast('Экипировано', 'success');
        await loadCharacter();
        loadShop();
      } catch (e) {
        showToast(e.message || 'Ошибка', 'error');
      }
    });
  });

  container.querySelectorAll('[data-unequip]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const slot = btn.getAttribute('data-unequip');
      try {
        await apiFetch('/api/inventory/unequip', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slot }),
        });
        showToast('Снято', 'success');
        await loadCharacter();
        loadShop();
      } catch (e) {
        showToast(e.message || 'Ошибка', 'error');
      }
    });
  });
}
