/* ============================================================
   ELKINGSL MODS — script.js
   ============================================================ */

const container  = document.getElementById('mods-container');
const emptyMsg   = document.getElementById('empty-msg');
const searchInput = document.getElementById('search');
const filterBtns = document.querySelectorAll('.filter-btn');

let allMods      = [];
let activeFilter = 'all';
let searchQuery  = '';

/* ---------- FETCH ---------- */
fetch('data/mods.json')
  .then(res => {
    if (!res.ok) throw new Error('Failed to load mods.json');
    return res.json();
  })
  .then(data => {
    allMods = data;
    render();
  })
  .catch(err => {
    console.error(err);
    container.innerHTML = `<p class="empty-msg" style="display:block">⚠️ Could not load mods. Check the console.</p>`;
  });

/* ---------- RENDER ---------- */
function render() {
  const q = searchQuery.trim().toLowerCase();

  const filtered = allMods.filter(mod => {
    const matchType   = activeFilter === 'all' || mod.type === activeFilter;
    const matchSearch = !q
      || mod.name.toLowerCase().includes(q)
      || mod.description.toLowerCase().includes(q);
    return matchType && matchSearch;
  });

  container.innerHTML = '';

  if (filtered.length === 0) {
    emptyMsg.hidden = false;
    return;
  }

  emptyMsg.hidden = true;

  filtered.forEach((mod, i) => {
    const card = document.createElement('div');
    card.className = 'mod-card';
    card.style.animationDelay = `${i * 0.055}s`;

    const badgeClass = mod.type === 'Mod'
      ? 'badge-mod'
      : mod.type === 'Shader'
        ? 'badge-shader'
        : 'badge-other';

    card.innerHTML = `
      <div class="thumb-wrap">
        <img src="${mod.image}" alt="${mod.name}" loading="lazy" />
      </div>
      <span class="badge ${badgeClass}">${mod.type}</span>
      <h2>${mod.name}</h2>
      <p class="desc">${mod.description}</p>
      <p class="version">Version <span>${mod.version}</span></p>
      <a class="dl-btn" href="${mod.download}" download>⬇ Download</a>
    `;

    container.appendChild(card);
  });
}

/* ---------- FILTERS ---------- */
filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    render();
  });
});

/* ---------- SEARCH (debounced) ---------- */
let debounceTimer;
searchInput.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    searchQuery = searchInput.value;
    render();
  }, 200);
});
