// Bamah: the page. Plain JavaScript, no build step.

const $app = document.getElementById('app');

const P = {
  back: '<path d="M15 18l-6-6 6-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  send: '<path d="M12 19V5M5 12l7-7 7 7"/>',
  up: '<path d="M7 11v9H4v-9h3zm0 0l4-8c1.5 0 2.5 1 2.3 2.6L13 9h5.6c1.3 0 2.2 1.2 1.9 2.4l-1.6 6.5c-.2.9-1 1.6-2 1.6H7"/>',
  down: '<g transform="rotate(180 12 12)"><path d="M7 11v9H4v-9h3zm0 0l4-8c1.5 0 2.5 1 2.3 2.6L13 9h5.6c1.3 0 2.2 1.2 1.9 2.4l-1.6 6.5c-.2.9-1 1.6-2 1.6H7"/></g>',
  star: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8L3.5 9.7l5.9-.9z"/>',
  redo: '<path d="M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5"/>',
  swap: '<path d="M16 3h5v5M4 20 21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>',
  more: '<circle cx="5" cy="12" r="1.4" fill="currentColor"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/><circle cx="19" cy="12" r="1.4" fill="currentColor"/>',
  heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
  people: '<circle cx="9" cy="8" r="3.2"/><path d="M3 19c.6-3.3 3-5 6-5s5.4 1.7 6 5"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.2c2.5.2 4.5 1.7 5 4.8"/>',
  book: '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h11"/>',
  bulb: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
  sliders: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  pin: '<path d="M9 4h6l-1 6 4 3H6l4-3zM12 13v7"/>',
  trash: '<path d="M5 7h14M10 7V5h4v2M7 7l1 13h8l1-13"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
  stop: '<rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor"/>',
  go: '<path d="M5 6l6 6-6 6M13 6l6 6-6 6"/>',
  left: '<path d="M14 7l-5 5 5 5"/>',
  right: '<path d="M10 7l5 5-5 5"/>',
  chev: '<path d="M6 9l6 6 6-6"/>',
  clip: '<path d="M20 11.5l-8.2 8.2a5 5 0 0 1-7.1-7.1l8.6-8.6a3.3 3.3 0 0 1 4.7 4.7l-8.6 8.6a1.7 1.7 0 0 1-2.4-2.4l7.9-7.9"/>',
  wand: '<path d="M4 20L15 9M13 7l4 4M19 3v4M17 5h4M8 3v2M7 4h2"/>',
  doc: '<path d="M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
  stage: '<path d="M4 20V10a8 8 0 0 1 16 0v10M4 20h16M9 20v-6a3 3 0 0 1 6 0v6"/>',
  person: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  memory: '<path d="M6 3h12v18l-6-4-6 4z"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  chip: '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9 9h6v6H9z"/>',
  branch: '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="7" r="2"/><path d="M6 7v10M18 9c0 5-7 4-11.5 8.5"/>',
  quill: '<path d="M20 4c-8 0-13 5-14 12l-2 4M8 14c3 0 6-1 8-4"/>',
};

// Reading comfort: text size and theme are per device. Dark unless she picks Light or Auto.
function applyLook() {
  let size = '1', theme = 'dark';
  try { size = localStorage.getItem('bamah.size') || '1'; theme = localStorage.getItem('bamah.theme') || 'dark'; } catch (e) {}
  document.documentElement.style.setProperty('--scale', size);
  document.documentElement.setAttribute('data-theme', theme);
}
applyLook();

function icon(name) {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('viewBox', '0 0 24 24');
  s.setAttribute('fill', 'none');
  s.setAttribute('stroke', 'currentColor');
  s.setAttribute('stroke-width', '1.8');
  s.setAttribute('stroke-linecap', 'round');
  s.setAttribute('stroke-linejoin', 'round');
  s.setAttribute('aria-hidden', 'true');
  s.innerHTML = P[name] || '';
  return s;
}

function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (k === 'html') el.innerHTML = v;
    else if (k === 'style') el.style.cssText = v;
    else if (k === 'value') el.value = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

// Name an element for the tour to point at.
const mark = (el, name) => { el.setAttribute('data-tour', name); return el; };

// append, skipping empty slots (Element.append would print them as "null")
const add = (el, ...kids) => { el.append(...kids.flat().filter((k) => k != null && k !== false)); return el; };

const ibtn = (name, onclick, props = {}) => h('button', {class: 'icon', type: 'button', onclick, 'aria-label': props.title, ...props}, icon(name));

async function api(method, url, body) {
  const r = await fetch(url, {method, headers: body ? {'content-type': 'application/json'} : {}, body: body ? JSON.stringify(body) : undefined});
  if (r.status === 401) { location.href = '/login'; throw new Error('signin'); }
  const data = r.headers.get('content-type')?.includes('json') ? await r.json() : await r.text();
  if (!r.ok) { const e = new Error(data?.error || data?.detail || r.status); e.data = data; throw e; }
  return data;
}
const GET = (u) => api('GET', u), POST = (u, b) => api('POST', u, b || {}), PATCH = (u, b) => api('PATCH', u, b), PUT = (u, b) => api('PUT', u, b), DEL = (u) => api('DELETE', u);

function debounce(fn, ms = 600) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

// Save a few fields a moment after typing stops, all together, so a quick edit to one box
// doesn't swallow the edit to the box before it.
function saver(url, ms = 600) {
  let pending = {}, t;
  return (patch) => {
    Object.assign(pending, patch);
    clearTimeout(t);
    t = setTimeout(() => { const p = pending; pending = {}; PATCH(url, p); }, ms);
  };
}

function toast(text) {
  const t = h('div', {class: 'toast'}, text);
  document.body.append(t);
  setTimeout(() => t.remove(), 2200);
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"]/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
}

function prose(text) {
  const t = esc(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>');
  return t.split(/\n{2,}/).map((p) => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}

const hue = (c) => `hsl(${c?.hue ?? 20} 30% 40%)`;
const TITLES = new Set(['aunt', 'uncle', 'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'miss', 'dr', 'dr.', 'sir', 'lady', 'lord', 'father', 'mother', 'sister', 'brother', 'grandma', 'grandpa', 'madame', 'monsieur', 'señor', 'señora', 'don', 'doña']);
// What to call someone for short: their first name, or "Aunt Odile" when the first word is a title.
const first = (name) => { const w = (name || '').trim().split(/\s+/); return TITLES.has(w[0].toLowerCase()) && w[1] ? `${w[0]} ${w[1]}` : w[0]; };
const initial = (name) => (name || '?').trim().charAt(0).toUpperCase();
const shortModel = (label) => (label || '').split(' · ')[0].split('/').pop();

// A face in a circle.
function avatar(c, size = '') {
  const el = h('span', {class: `av ${size}`, style: `background:${hue(c)}`, title: c?.name || ''});
  if (c?.avatar) el.append(h('img', {src: `/avatars/${c.avatar}`, alt: '', loading: 'lazy'}));
  else el.textContent = initial(c?.name);
  return el;
}
// A face as a small portrait.
function portrait(c, style = '') {
  const el = h('span', {class: 'pt', style: `background:${hue(c)};${style}`, title: c?.name || ''});
  if (c?.avatar) el.append(h('img', {src: `/avatars/${c.avatar}`, alt: '', loading: 'lazy'}));
  else el.textContent = initial(c?.name);
  return el;
}
const stack = (people, size = 'sm') => h('div', {class: 'stack'}, (people || []).slice(0, 6).map((c) => avatar(c, size)));

const STYLES = [['dialogue', 'Talk'], ['roleplay', 'Roleplay'], ['narrative', 'Narrative']];

const ERR = {key: 'Key not accepted', model: 'Model not found', limit: 'Limit reached', refused: 'Declined by the model',
  network: "Can't reach the service", down: 'Service error', setup: 'No model set', request: 'Request refused', empty: 'Empty reply'};

// --- Sheets -------------------------------------------------------------------------------------

function sheet(build, cls = '') {
  const box = h('div', {class: `sheet ${cls}`, role: 'dialog'});
  const veil = h('div', {class: 'veil', onclick: (e) => { if (e.target === veil) close(); }}, box);
  const onkey = (e) => { if (e.key === 'Escape') close(); };
  function close() { veil.remove(); document.removeEventListener('keydown', onkey); }
  document.addEventListener('keydown', onkey);
  document.body.append(veil);
  build(box, close);
  if (matchMedia('(hover: hover)').matches) box.querySelector('input:not([type=search]),textarea')?.focus();
  return close;
}

function ask(title, okLabel = 'Delete', danger = true) {
  return new Promise((done) => {
    sheet((box, close) => {
      box.append(h('h2', {}, title), h('div', {class: 'foot'},
        h('button', {class: 'btn', onclick: () => { close(); done(false); }}, 'Cancel'),
        h('button', {class: `btn ${danger ? 'danger' : 'primary'}`, onclick: () => { close(); done(true); }}, okLabel)));
    });
  });
}

function menu(items) {
  sheet((box, close) => {
    box.append(h('div', {class: 'menu'}, items.filter(Boolean).map(([label, fn, cls]) =>
      h('button', {class: cls || '', onclick: () => { close(); fn(); }}, label))));
  });
}

let settingsCache = null;
async function getSettings(fresh) {
  if (!settingsCache || fresh) settingsCache = await GET('/api/settings');
  return settingsCache;
}

// Pick a model: a connection, then one of its models (or a typed name). Resolves to "id/model", '' (default) or null.
function pickModel(title, {allowDefault, defaultLabel = 'Default', images = false} = {}) {
  return new Promise(async (done) => {
    const s = await getSettings(true);
    const conns = images ? s.connections.filter((c) => s.presets[c.preset]?.draws !== false) : s.connections;
    sheet((box, close) => {
      const finish = (v) => { close(); done(v); };
      box.append(h('h2', {}, title));
      if (!conns.length) {
        box.append(h('div', {class: 'foot'}, h('a', {class: 'btn primary', href: '#/settings', onclick: () => finish(null)}, 'Settings')));
        return;
      }
      const body = h('div');
      const list = h('div', {class: 'menu'});
      if (allowDefault) list.append(h('button', {onclick: () => finish('')}, defaultLabel));
      for (const c of conns) list.append(h('button', {onclick: () => open(c)}, c.name));
      body.append(list);
      box.append(body);
      if (conns.length === 1 && !allowDefault) open(conns[0]);
      async function open(c) {
        body.innerHTML = '';
        const search = h('input', {type: 'search', placeholder: s.presets[c.preset]?.model_label || 'Model'});
        const results = h('div', {class: 'picker-list'}, h('div', {class: 'muted small', style: 'padding:10px'}, 'Loading…'));
        const typed = h('button', {class: 'btn small', onclick: () => search.value.trim() && finish(`${c.id}/${search.value.trim()}`)}, 'Use');
        body.append(h('div', {class: 'row'}, ibtn('back', () => { body.innerHTML = ''; body.append(list); }, {title: 'Back'}), h('b', {}, c.name)),
          h('div', {class: 'row', style: 'margin-top:8px'}, search, typed), results);
        let all = [];
        try { all = await GET(`/api/connections/${c.id}/models${images ? '?kind=image' : ''}`); }
        catch (e) { results.innerHTML = ''; results.append(h('div', {class: 'err', style: 'padding:10px'}, ERR[e.data?.error] || 'No list')); return; }
        const draw = () => {
          const q = search.value.trim().toLowerCase();
          results.innerHTML = '';
          const hits = all.filter((m) => !q || m.id.toLowerCase().includes(q) || (m.name || '').toLowerCase().includes(q)).slice(0, 200);
          for (const m of hits) results.append(h('button', {onclick: () => finish(`${c.id}/${m.id}`)},
            h('div', {}, m.name || m.id), m.name && m.name !== m.id ? h('div', {class: 'id'}, m.id) : null));
          if (!hits.length) results.append(h('div', {class: 'muted small', style: 'padding:10px'}, '—'));
        };
        search.addEventListener('input', draw);
        search.addEventListener('keydown', (e) => { if (e.key === 'Enter' && search.value.trim()) finish(`${c.id}/${search.value.trim()}`); });
        draw();
        search.focus();
      }
    });
  });
}

// Server-sent events from a POST.
async function sse(url, body, on, signal) {
  const r = await fetch(url, {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body || {}), signal});
  if (r.status === 401) { location.href = '/login'; return; }
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  for (;;) {
    const {value, done} = await reader.read();
    if (done) break;
    buf += dec.decode(value, {stream: true});
    let i;
    while ((i = buf.indexOf('\n\n')) >= 0) {
      const block = buf.slice(0, i);
      buf = buf.slice(i + 2);
      let kind = 'message', data = '';
      for (const ln of block.split('\n')) {
        if (ln.startsWith('event: ')) kind = ln.slice(7);
        else if (ln.startsWith('data: ')) data += ln.slice(6);
      }
      try { on(kind, JSON.parse(data)); } catch (e) { console.error(e); }
    }
  }
}

// --- Frame: the side list (big screens), the top bar and tabs (phones) ------------------------

const TABS = [['stories', '#/', 'Stories', 'book'], ['characters', '#/characters', 'Characters', 'people'],
  ['ideas', '#/ideas', 'Ideas', 'bulb'], ['settings', '#/settings', 'Settings', 'sliders']];

let railCache = {stories: null, story: null};

// active: which tab; story/scene: what's open, so the list can show it; nav: a different side column (a character's sections).
function frame(active, {scene = false, story = null, sceneId = null, filter = null, nav = null, top = null} = {}) {
  document.body.classList.toggle('in-scene', scene);
  document.body.classList.toggle('in-char', !!nav);
  $app.innerHTML = '';
  const side = nav || h('aside', {class: 'rail'});
  const main = h('main');
  const mtop = h('header', {class: 'mtop'}, h('a', {class: 'logo', href: '#/', 'aria-label': 'Bamah'}, icon('stage')),
    h('span', {class: 'brand'}, 'Bamah'), top);
  const mtabs = h('nav', {class: 'mtabs'}, TABS.map(([k, href, label, ic]) => h('a', {href, class: k === active ? 'on' : ''}, icon(ic), label)));
  $app.append(h('div', {class: 'shell'}, side, h('div', {class: 'page'}, mtop, main, mtabs)));
  if (!nav) {
    drawRail(side, active, story, sceneId, filter);
    Promise.all([GET('/api/stories'), story ? GET(`/api/stories/${story}`) : null]).then(([stories, s]) => {
      railCache = {stories, story: s};
      if (side.isConnected) drawRail(side, active, story, sceneId, filter);
    }).catch(() => {});
  }
  return main;
}

function drawRail(rail, active, storyId, sceneId, filter) {
  const keep = rail.querySelector('.search input')?.value || '';
  rail.innerHTML = '';
  const q = h('input', {type: 'search', placeholder: 'Search', 'aria-label': 'Search', value: keep});
  rail.append(
    h('div', {class: 'brandrow'}, h('a', {class: 'logo', href: '#/', 'aria-label': 'Bamah'}, icon('stage')), h('span', {class: 'brand'}, 'Bamah'),
      h('button', {class: 'sqbtn', title: active === 'characters' ? 'New character' : 'New story', 'aria-label': active === 'characters' ? 'New character' : 'New story',
        onclick: active === 'characters' ? newCharacter : newStory}, icon('plus'))),
    h('nav', {class: 'pills'}, h('a', {href: '#/', class: active === 'characters' ? '' : 'on'}, 'Stories'),
      h('a', {href: '#/characters', class: active === 'characters' ? 'on' : ''}, 'Characters')),
    h('label', {class: 'search'}, icon('search'), q));
  const list = h('div', {class: 'rlist'});
  const stories = railCache.stories || [];
  if (active === 'characters') {
    list.append(h('a', {class: `ritem ${!filter ? 'sel' : ''}`, href: '#/characters', 'data-text': ''}, h('span', {class: 'grow'}, 'All')));
    for (const s of stories) list.append(h('a', {class: `ritem ${String(filter) === String(s.id) ? 'sel' : ''}`, href: `#/characters?story=${s.id}`, 'data-text': s.title.toLowerCase()},
      h('span', {class: 'grow'}, s.title), h('span', {class: 'n'}, s.cast.length)));
    q.addEventListener('input', () => document.dispatchEvent(new CustomEvent('bamah:search', {detail: q.value})));
  } else {
    for (const s of stories) {
      const open = String(s.id) === String(storyId);
      const text = [s.title, ...(open && railCache.story?.scenes || []).map((x) => x.title)].join(' ').toLowerCase();
      list.append(h('a', {class: `ritem ${open ? 'on' : ''}`, href: `#/story/${s.id}`, 'data-text': text},
        s.cast.length ? stack(s.cast.slice(0, 3), 'sm') : null, h('span', {class: 'grow'}, s.title || 'Untitled'),
        open ? icon('chev') : null));
      if (open && railCache.story && String(railCache.story.id) === String(s.id)) {
        const scenes = [...railCache.story.scenes].reverse();
        list.append(h('div', {class: 'rscenes', 'data-text': text},
          scenes.map((sc, i) => h('a', {class: `rscene ${String(sc.id) === String(sceneId) ? 'on' : ''}`, href: `#/scene/${sc.id}`},
            h('span', {class: 'no'}, i + 1), h('span', {class: 't'}, sc.title || 'Untitled'), sc.whatif ? h('span', {class: 'badge whatif'}, 'What if') : null)),
          h('button', {class: 'rscene add', style: 'border:0;background:transparent;text-align:left', onclick: () => newSceneSheet(railCache.story)},
            h('span', {class: 'no'}, icon('plus')), h('span', {class: 't'}, 'New scene'))));
      }
    }
    if (!stories.length && railCache.stories) list.append(h('button', {class: 'ritem', style: 'border:0;background:transparent', onclick: newStory}, icon('plus'), 'New story'));
    q.addEventListener('input', () => {
      const v = q.value.trim().toLowerCase();
      for (const el of list.children) el.classList.toggle('hidden', !!v && !(el.dataset.text || '').includes(v));
    });
  }
  rail.append(list, h('div', {class: 'rfoot'},
    h('a', {class: `rlink ${active === 'ideas' ? 'on' : ''}`, href: '#/ideas'}, icon('bulb'), 'Ideas'),
    h('a', {class: `rlink ${active === 'settings' ? 'on' : ''}`, href: '#/settings'}, icon('sliders'), 'Settings')));
  if (keep) q.dispatchEvent(new Event('input'));
}

function query() {
  const q = location.hash.split('?')[1] || '';
  return Object.fromEntries(new URLSearchParams(q));
}

const ROUTES = [
  [/^#?\/?(\?.*)?$/, () => storiesView()],
  [/^#\/story\/(\d+)/, (m) => storyView(+m[1])],
  [/^#\/scene\/(\d+)/, (m) => sceneView(+m[1])],
  [/^#\/characters/, () => charactersView()],
  [/^#\/character\/(\d+)/, (m) => characterView(+m[1])],
  [/^#\/ideas/, () => ideasView()],
  [/^#\/settings/, () => settingsView()],
];

let leave = null;
async function route() {
  if (leave) { leave(); leave = null; }
  const hash = location.hash || '#/';
  for (const [re, fn] of ROUTES) {
    const m = hash.match(re);
    if (m) {
      try { await fn(m); window.scrollTo(0, 0); } catch (e) { console.error(e); if (e.message !== 'signin') { frame('').append(h('div', {class: 'empty err'}, 'Not found')); } }
      return;
    }
  }
  location.hash = '#/';
}
window.addEventListener('hashchange', route);

// --- Stories ----------------------------------------------------------------------------------

async function newStory() {
  const {id} = await POST('/api/stories', {title: 'New story'});
  location.hash = `#/story/${id}?tab=setup`;
}

async function storiesView() {
  const list = await GET('/api/stories');
  railCache.stories = list;
  const main = frame('stories', {top: h('button', {class: 'sqbtn', 'aria-label': 'New story', onclick: newStory}, icon('plus'))});
  main.append(h('div', {class: 'head'}, h('h1', {}, 'Stories'), h('button', {class: 'btn primary', 'data-tour': 'new-story', onclick: newStory}, icon('plus'), 'New story')));
  if (!list.length) return main.append(h('div', {class: 'empty'}, h('button', {class: 'btn primary', onclick: newStory}, 'New story')));
  main.append(h('div', {class: 'scards'}, list.map((s) => h('a', {class: 'scard', href: `#/story/${s.id}`},
    s.cast.length ? h('div', {class: 'stack'}, s.cast.slice(0, 6).map((c) => portrait(c, 'width:44px;height:56px'))) : null,
    h('div', {class: 't'}, s.title || 'Untitled'),
    s.premise ? h('div', {class: 's'}, s.premise) : null,
    h('div', {class: 'row'}, h('span', {class: 'badge'}, `${s.scenes} ${s.scenes === 1 ? 'scene' : 'scenes'}`))))));
}

async function storyView(id, tab) {
  const s = await GET(`/api/stories/${id}`);
  railCache.story = s;
  tab = tab || query().tab || 'scenes';
  const main = frame('stories', {story: id});
  const save = saver(`/api/stories/${id}`);
  const title = h('input', {class: 'title-input', value: s.title, 'aria-label': 'Title', oninput: () => save({title: title.value})});
  main.append(h('div', {class: 'story-head'}, h('div', {class: 'grow'}, title),
    tab === 'scenes' ? h('button', {class: 'btn primary', 'data-tour': 'new-scene', onclick: () => newSceneSheet(s)}, icon('plus'), 'New scene') : null));
  const tabs = [['scenes', 'Scenes'], ['feelings', 'Feelings'], ['setup', 'Setup'], ['journal', 'Journal']];
  const body = h('div');
  const bar = h('div', {class: 'pills quiet', style: 'max-width:460px;margin-bottom:20px'}, tabs.map(([k, label]) => h('button', {class: k === tab ? 'on' : '', onclick: () => {
    history.replaceState(null, '', `#/story/${id}?tab=${k}`); storyView(id, k);
  }}, label)));
  main.append(bar, body);
  ({scenes: storyScenes, feelings: storyFeelings, setup: storySetup, journal: storyJournal})[tab](s, body, save);
}

function storyScenes(s, body) {
  const people = Object.fromEntries(s.cast.map((c) => [c.id, c]));
  if (!s.scenes.length) return body.append(h('div', {class: 'empty'}, h('button', {class: 'btn primary', onclick: () => newSceneSheet(s)}, 'New scene')));
  const n = s.scenes.length;
  body.append(h('div', {class: 'list'}, s.scenes.map((sc, i) => h('a', {class: 'item', href: `#/scene/${sc.id}`},
    h('span', {class: 'no'}, n - i),
    h('div', {class: 'grow'}, h('div', {class: 't'}, sc.title || 'Untitled'), sc.setting ? h('div', {class: 's'}, sc.setting) : null),
    sc.whatif ? h('span', {class: 'badge whatif'}, 'What if') : null,
    sc.state === 'ended' ? h('span', {class: 'badge'}, 'Ended') : null,
    stack(sc.everyone.map((i) => people[i]).filter(Boolean))))));
}

// opts.whatif: start it as a what-if; opts.with: who to pick to begin with.
async function newSceneSheet(s, from, opts = {}) {
  const all = await GET('/api/characters');
  const inCast = new Set(s.cast.map((c) => c.id));
  const chosen = new Set(from ? from.here : opts.with || []);
  sheet((box, close) => {
    const title = h('input', {placeholder: 'Title'});
    const setting = h('textarea', {class: 'prose'});
    const chips = h('div', {class: 'chips'});
    const pool = from ? all.filter((c) => from.here.includes(c.id)) : [...all].sort((a, b) => inCast.has(b.id) - inCast.has(a.id));
    const draw = () => {
      chips.innerHTML = '';
      for (const c of pool) chips.append(h('button', {class: `chip ${chosen.has(c.id) ? 'on' : ''}`, type: 'button',
        onclick: () => { chosen.has(c.id) ? chosen.delete(c.id) : chosen.add(c.id); draw(); }}, avatar(c, 'sm'), c.name));
    };
    draw();
    let whatif = !!opts.whatif;
    const wi = h('button', {class: `chip plain ${whatif ? 'on' : ''}`, type: 'button', onclick: () => { whatif = !whatif; wi.classList.toggle('on', whatif); }}, icon('branch'), 'What if');
    box.append(h('h2', {}, from ? 'Move to a new scene' : 'New scene'),
      h('label', {class: 'field'}, h('span', {}, 'Title'), title),
      h('label', {class: 'field'}, h('span', {}, 'Setting'), setting),
      h('div', {class: 'field'}, h('span', {class: 'lab'}, from ? 'Who goes' : "Who's in it"), chips),
      h('div', {class: 'field'}, wi),
      h('div', {class: 'foot'}, h('button', {class: 'btn', onclick: close}, 'Cancel'),
        h('button', {class: 'btn primary', onclick: async (e) => {
          e.target.disabled = true;
          const {id} = await POST(`/api/stories/${s.id}/scenes`, {title: title.value, setting: setting.value,
            characters: [...chosen], from_scene: from?.id, whatif});
          close();
          location.hash = `#/scene/${id}`;
        }}, from ? 'Move' : 'Start')));
  });
}

// How someone feels: their mood in a word and a line, and toward each of the others, with how strongly.
function feelCard(c, f, names, people, {big = false} = {}) {
  const card = h('div', {class: 'feelcard'});
  const word = f?.word || '';
  card.append(h('a', {class: 'fhead', href: `#/character/${c.id}?s=feelings`},
    big ? portrait(c) : avatar(c, 'md'),
    h('div', {class: 'who'}, h('b', {}, c.name), f?.mood ? h('span', {class: 'mood'}, f.mood) : null),
    word ? h('span', {class: 'fword'}, word) : null));
  if (!f) { card.append(h('div', {class: 'muted small'}, '—')); return card; }
  for (const [k, how] of Object.entries(f.toward || {})) {
    const other = people[k] || {name: names[k] || k};
    const much = (f.strength || {})[k];
    card.append(h('div', {class: 'tw'}, h('div', {class: 'row'}, avatar(other, 'xs'), h('b', {}, first(other.name)), h('span', {class: 'grow'}, how)),
      much ? h('div', {class: 'bar'}, h('i', {style: `width:${much * 20}%`})) : null));
  }
  return card;
}

function storyFeelings(s, body) {
  const people = Object.fromEntries(s.cast.map((c) => [String(c.id), c]));
  if (!s.cast.length) return body.append(h('div', {class: 'empty muted'}, '—'));
  body.append(h('div', {class: 'feel grid2'}, s.cast.map((c) => feelCard(c, s.feelings[String(c.id)], s.names, people, {big: true}))));
}

function seg(options, value, onpick) {
  const el = h('div', {class: 'seg'});
  const draw = (v) => {
    el.innerHTML = '';
    for (const [k, label] of options) el.append(h('button', {type: 'button', class: String(k) === String(v) ? 'on' : '', onclick: () => { draw(k); onpick(k); }}, label));
  };
  draw(value);
  return el;
}

function field(label, control) {
  return h('label', {class: 'field'}, h('span', {}, label), control);
}

// A labelled row inside a group card.
const line = (label, control) => h('div', {class: 'rowline'}, h('span', {class: 'lab'}, label), control);

// A labelled text box that sits in its own card, and grows with what's in it.
function fieldCard(label, textarea) {
  const fit = () => { if (!textarea.isConnected) return; textarea.style.height = 'auto'; textarea.style.height = textarea.scrollHeight + 'px'; };
  textarea.addEventListener('input', fit);
  requestAnimationFrame(() => requestAnimationFrame(fit));
  document.fonts?.ready.then(fit);
  return h('label', {class: 'fieldcard'}, h('span', {class: 'lab'}, label), textarea);
}

function modelButton(label, fallback, onpick, opts) {
  const b = h('button', {class: 'btn small', type: 'button', onclick: async () => {
    const v = await pickModel('Model', opts);
    if (v === null) return;
    await onpick(v);
    b.textContent = v ? v.split('/').slice(1).join('/') : fallback;
  }}, label || fallback);
  return b;
}

function storySetup(s, body, save) {
  const ta = (key, rows, cls = 'prose') => h('textarea', {class: cls, value: s[key] || '', rows, oninput: (e) => save({[key]: e.target.value})});
  const set = (k) => (v) => PATCH(`/api/stories/${s.id}`, {[k]: v});
  body.append(h('div', {class: 'stack-v', style: 'max-width:760px'},
    mark(fieldCard('Premise', ta('premise', 6)), 'premise'),
    fieldCard('How it is written', ta('directive', 3, '')),
    h('div', {class: 'group'},
      line('Style', seg(STYLES, s.style, set('style'))),
      line('Characters speak as', seg([['first', 'I'], ['third', 'She / he / they']], s.person || 'first', set('person'))),
      line('Length', seg([['short', 'Short'], ['medium', 'Medium'], ['long', 'Long']], s.length, set('length'))),
      line('Memory', seg([['witnessed', 'Only what they saw'], ['shared', 'Everyone knows everything']], s.memory, set('memory'))),
      line('Who answers', seg([['auto', 'The story picks'], ['manual', 'I pick']], s.turns, set('turns'))),
      line('Model', modelButton(s.model ? s.model.split('/').slice(1).join('/') : '', 'Default', (v) => PATCH(`/api/stories/${s.id}`, {model: v || null}), {allowDefault: true})))));

  const wrap = h('div', {style: 'max-width:760px'});
  wrap.append(h('h3', {}, 'You play'));
  const mine = new Set(s.personas || []);
  const pBox = h('div', {class: 'chips'});
  const drawPersonas = async () => {
    const all = await GET('/api/personas');
    pBox.innerHTML = '';
    for (const p of all) pBox.append(h('button', {class: `chip plain ${mine.has(p.id) ? 'on' : ''}`, type: 'button', onclick: async () => {
      mine.has(p.id) ? mine.delete(p.id) : mine.add(p.id);
      await PATCH(`/api/stories/${s.id}`, {personas: [...mine]});
      drawPersonas();
    }}, p.name));
    pBox.append(h('button', {class: 'chip plain', onclick: () => personaSheet(null, async (pid) => {
      if (pid) { mine.add(pid); await PATCH(`/api/stories/${s.id}`, {personas: [...mine]}); }
      drawPersonas();
    })}, icon('plus'), 'Persona'));
  };
  drawPersonas();
  wrap.append(pBox);

  wrap.append(h('h3', {}, 'Cast'));
  const castBox = h('div', {class: 'chips', 'data-tour': 'cast'});
  for (const c of s.cast) castBox.append(h('span', {class: 'chip'}, avatar(c, 'sm'), h('a', {href: `#/character/${c.id}`}, c.name),
    h('button', {class: 'icon', style: 'width:24px;height:24px;margin-right:-8px', 'aria-label': `Remove ${c.name}`, onclick: async () => { await DEL(`/api/stories/${s.id}/cast/${c.id}`); storyView(s.id, 'setup'); }}, icon('close'))));
  castBox.append(h('button', {class: 'chip plain', onclick: () => addCastSheet(s)}, icon('plus'), 'Add'));
  wrap.append(castBox);

  wrap.append(h('h3', {}, 'Story'), h('div', {class: 'row wrap'},
    h('a', {class: 'btn', href: `/api/stories/${s.id}/export`, download: ''}, 'Export'),
    h('button', {class: 'btn danger', onclick: async () => {
      if (await ask(`Delete “${s.title}”?`)) { await DEL(`/api/stories/${s.id}`); location.hash = '#/'; }
    }}, 'Delete story')));
  body.append(wrap);
}

async function addCastSheet(s) {
  const all = await GET('/api/characters');
  const inCast = new Set(s.cast.map((c) => c.id));
  sheet((box, close) => {
    const name = h('input', {placeholder: 'Name'});
    box.append(h('h2', {}, 'Add to the cast'),
      h('div', {class: 'chips'}, all.filter((c) => !inCast.has(c.id)).map((c) => h('button', {class: 'chip', onclick: async () => {
        await POST(`/api/stories/${s.id}/cast`, {character_id: c.id}); close(); storyView(s.id, 'setup');
      }}, avatar(c, 'sm'), c.name))),
      h('h3', {}, 'New character'),
      h('div', {class: 'row'}, name, h('button', {class: 'btn primary', onclick: async () => {
        if (!name.value.trim()) return;
        const {id} = await POST('/api/characters', {name: name.value.trim(), story_id: s.id});
        close(); location.hash = `#/character/${id}`;
      }}, 'Create')));
  });
}

// A file brought in: into a scene, onto a character (their journal) or into a story's journal.
function pickFile(accept = '.txt,.md,.docx,.pdf') {
  return new Promise((done) => {
    const f = h('input', {type: 'file', accept, class: 'hidden', onchange: () => done(f.files[0] || null)});
    document.body.append(f);
    f.click();
    setTimeout(() => f.remove(), 60000);
  });
}

async function bringIn(target, targetId) {
  const file = await pickFile();
  if (!file) return null;
  const fd = new FormData();
  fd.append('file', file);
  fd.append('target', target);
  fd.append('target_id', String(targetId));
  toast('Reading…');
  const r = await fetch('/api/import', {method: 'POST', body: fd});
  if (!r.ok) { toast(r.status === 415 ? 'Word, PDF or text only' : 'Not added'); return null; }
  const out = await r.json();
  toast(`${out.words.toLocaleString()} words added`);
  return out;
}

function journalEditor(entries, scope, reload) {
  const box = h('div', {class: 'notes'});
  const fileTarget = scope.character_id ? ['character', scope.character_id] : scope.story_id ? ['story', scope.story_id] : null;
  for (const j of entries) {
    const view = h('div', {class: 'grow', style: 'padding-top:6px'}, h('div', {}, h('b', {}, j.title || ''), j.keys ? h('span', {class: 'meta'}, '  ' + j.keys) : null),
      h('div', {class: 'text', style: 'padding-top:2px'}, j.text));
    const note = h('div', {class: 'note'}, view,
      ibtn('edit', () => {
        const t = h('input', {value: j.title, placeholder: 'Title'}), k = h('input', {value: j.keys, placeholder: 'Keyphrases'}), x = h('textarea', {value: j.text});
        note.innerHTML = '';
        note.append(h('div', {class: 'grow'}, t, h('div', {style: 'height:6px'}), k, h('div', {style: 'height:6px'}), x,
          h('div', {class: 'row', style: 'justify-content:flex-end;margin-top:6px'},
            h('button', {class: 'btn small', onclick: reload}, 'Cancel'),
            h('button', {class: 'btn small primary', onclick: async () => { await PATCH(`/api/journal/${j.id}`, {title: t.value, keys: k.value, text: x.value}); reload(); }}, 'Save'))));
      }, {title: 'Edit'}),
      ibtn('trash', async () => { await DEL(`/api/journal/${j.id}`); reload(); }, {title: 'Delete'}));
    box.append(note);
  }
  const t = h('input', {placeholder: 'Title'}), k = h('input', {placeholder: 'Keyphrases'}), x = h('textarea', {placeholder: 'Entry'});
  box.append(h('div', {class: 'card'}, t, h('div', {style: 'height:6px'}), k, h('div', {style: 'height:6px'}), x,
    h('div', {class: 'row', style: 'justify-content:flex-end;margin-top:8px'},
      fileTarget ? h('button', {class: 'btn small quiet', onclick: async () => { if (await bringIn(...fileTarget)) reload(); }}, icon('clip'), 'File') : null,
      h('button', {class: 'btn small primary', onclick: async () => {
        if (!x.value.trim()) return;
        await POST('/api/journal', {...scope, title: t.value, keys: k.value, text: x.value});
        reload();
      }}, 'Add'))));
  return box;
}

// A persona: one of the people she plays.
function personaSheet(p, done) {
  sheet((box, close) => {
    const name = h('input', {value: p?.name || ''});
    const pron = h('input', {value: p?.pronouns || ''});
    const about = h('textarea', {value: p?.about || '', rows: 3});
    box.append(h('h2', {}, p ? p.name : 'New persona'), field('Name', name), field('Pronouns', pron), field('Who they are', about),
      h('div', {class: 'foot'},
        p ? h('button', {class: 'btn danger', onclick: async () => {
          if (await ask(`Delete ${p.name}?`)) { await DEL(`/api/personas/${p.id}`); close(); done(null); }
        }}, 'Delete') : null,
        h('button', {class: 'btn', onclick: close}, 'Cancel'),
        h('button', {class: 'btn primary', onclick: async () => {
          if (!name.value.trim()) return name.focus();
          const body = {name: name.value.trim(), pronouns: pron.value.trim(), about: about.value.trim()};
          let pid = p?.id;
          if (p) await PATCH(`/api/personas/${p.id}`, body); else pid = (await POST('/api/personas', body)).id;
          close();
          done(pid);
        }}, 'Save')));
  });
}

function storyJournal(s, body) {
  const wrap = h('div', {style: 'max-width:760px'});
  wrap.append(journalEditor(s.journal.filter((j) => !j.character_id), {story_id: s.id}, () => storyView(s.id, 'journal')));
  body.append(wrap);
}

// --- A scene ----------------------------------------------------------------------------------

async function sceneView(id) {
  let sc = await GET(`/api/scenes/${id}`);
  let story = await GET(`/api/stories/${sc.story.id}`).catch(() => null);
  if (story) railCache.story = story;
  const main = frame('stories', {scene: true, story: sc.story.id, sceneId: id});
  let busy = null;                  // the AbortController of what's streaming
  let showInner = localStorage.getItem('bamah.inner') !== '0';
  let sideTab = localStorage.getItem('bamah.side') || 'feelings';
  const people = () => Object.fromEntries(sc.cast.map((c) => [c.id, c]));

  const titleBox = h('div', {class: 'stage-title', onclick: () => editScene()});
  const castBtn = h('button', {class: 'cast', 'aria-label': "Who's here", onclick: () => presenceSheet()});
  const feelBtn = ibtn('heart', () => side.classList.toggle('open'), {class: 'icon feel-btn', title: 'Feelings', 'data-tour': 'feelings-btn'});
  const head = h('div', {class: 'stage-head'},
    ibtn('back', () => (location.hash = `#/story/${sc.story.id}`), {class: 'icon back', title: 'Back'}),
    castBtn, titleBox,
    h('button', {class: 'btn small', style: 'border-style:dashed', title: 'What if', 'data-tour': 'whatif', onclick: () => newSceneSheet(story || {id: sc.story.id, cast: sc.cast}, null, {whatif: true, with: sc.here})},
      icon('branch'), h('span', {}, 'What if')),
    feelBtn, ibtn('more', () => sceneMenu(), {title: 'Scene menu', 'data-tour': 'scene-menu'}));
  const logIn = h('div', {class: 'log-in'});
  const log = h('div', {class: 'log'}, logIn);
  const speakers = h('div', {class: 'speakers', 'data-tour': 'speakers'});
  let as = localStorage.getItem(`bamah.as.${sc.story.id}`) || '';
  const asBtn = h('button', {class: 'asbtn', type: 'button', onclick: () => pickAs()});
  const input = h('textarea', {rows: 1, placeholder: 'Write', 'aria-label': 'Write'});
  const send = h('button', {class: 'send', 'aria-label': 'Send', onclick: () => (busy ? stop() : submit())}, icon('send'));
  const attach = ibtn('clip', () => attachSheet(), {title: 'File'});
  const wand = ibtn('wand', () => suggest(), {title: 'Write my line'});
  const dock = h('div', {class: 'dock'}, h('div', {class: 'dock-in'}, speakers,
    h('div', {class: 'composer', 'data-tour': 'composer'}, input, h('div', {class: 'cbar'}, attach, asBtn, h('span', {class: 'grow'}), wand, send))));
  const side = h('aside', {class: 'side', 'data-tour': 'feelings'});
  main.append(h('div', {class: 'scene'}, h('div', {class: 'stage'}, head, log, dock), side));

  input.addEventListener('input', grow);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && matchMedia('(hover: hover)').matches) { e.preventDefault(); if (!busy) submit(); }
  });
  function grow() { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, innerHeight * 0.4) + 'px'; }

  function sceneNo() {
    const list = story?.scenes || [];
    const i = list.findIndex((x) => x.id === id);
    return i < 0 ? '' : `Scene ${list.length - i}`;
  }

  function drawTop() {
    titleBox.innerHTML = '';
    const firstLine = (sc.setting || '').split('\n')[0];
    add(titleBox, h('span', {class: 'k'}, [sc.story.title, sceneNo()].filter(Boolean).join(' · ')),
      h('div', {class: 't'}, h('span', {}, sc.title || 'Untitled'), sc.whatif ? h('span', {class: 'badge whatif'}, 'What if') : null),
      h('span', {class: 't2'}, sc.story.title),
      firstLine ? h('span', {class: 's'}, firstLine) : null);
    castBtn.innerHTML = '';
    const here = sc.here.map((i) => people()[i]).filter(Boolean);
    castBtn.append(here.length ? h('div', {class: 'stack'}, here.slice(0, 4).map((c) => portrait(c))) : h('span', {class: 'icon'}, icon('people')));
  }

  function drawAs() {
    asBtn.innerHTML = '';
    const narr = !as;
    asBtn.append(narr ? h('span', {class: 'av sm', style: 'background:var(--line-2);color:var(--ink-2)'}, icon('quill')) : avatar({name: as, hue: 0}, 'sm'),
      narr ? 'Narrator' : as, icon('chev'));
  }

  function pickAs() {
    const inStory = new Set(sc.story.personas || []);
    const ps = [...(sc.personas || [])].sort((a, b) => inStory.has(b.id) - inStory.has(a.id));
    menu([['Narrator', () => setAs('')], ...ps.map((p) => [p.name, () => setAs(p.name)]),
      ['New persona', () => personaSheet(null, async () => { sc = await GET(`/api/scenes/${id}`); pickAs(); })]]);
  }
  function setAs(v) { as = v; localStorage.setItem(`bamah.as.${sc.story.id}`, v); drawAs(); }

  function drawDock() {
    speakers.innerHTML = '';
    const ended = sc.state === 'ended';
    for (const i of sc.here) {
      const c = people()[i];
      if (c) speakers.append(h('button', {class: 'chip', disabled: !!busy || ended, onclick: () => run([i])}, avatar(c, 'sm'), first(c.name)));
    }
    if (sc.here.length) speakers.append(h('button', {class: 'chip plain', disabled: !!busy || ended, onclick: async () => {
      const {speakers: who} = await POST(`/api/scenes/${id}/next`, {more: true}); run(who);
    }}, icon('go'), 'Go on'));
    else speakers.append(h('button', {class: 'chip plain', onclick: presenceSheet}, icon('people'), "Who's here"));
    if (!(sc.personas || []).some((p) => p.name === as)) as = '';
    drawAs();
    attach.disabled = wand.disabled = !!busy || ended;
    send.innerHTML = '';
    send.append(icon(busy ? 'stop' : 'send'));
    send.setAttribute('aria-label', busy ? 'Stop' : 'Send');
    input.disabled = ended;
    input.placeholder = ended ? 'Ended' : 'Write';
  }

  function nearBottom() { return log.scrollHeight - log.scrollTop - log.clientHeight < 160; }
  function toBottom() { log.scrollTop = log.scrollHeight; }
  // Stay at the newest line while fonts and pictures settle, unless she has scrolled up to read.
  let stick = true;
  log.addEventListener('scroll', () => { stick = nearBottom(); });
  const settle = new ResizeObserver(() => { if (stick) toBottom(); });
  settle.observe(logIn);

  function lastLineId() { return [...sc.events].reverse().find((x) => x.kind === 'character')?.id; }
  function lastEventId() { return [...sc.events].reverse().find((x) => x.kind !== 'enter' && x.kind !== 'leave')?.id; }

  function drawLog() {
    logIn.innerHTML = '';
    if (sc.setting) logIn.append(h('div', {class: 'setting'}, sc.setting));
    for (const e of sc.events) logIn.append(msgEl(e));
  }

  function msgEl(e) {
    const who = people();
    if (e.kind === 'enter' || e.kind === 'leave') {
      const n = who[e.character_id]?.name || sc.names[e.character_id] || 'Someone';
      return h('div', {class: 'note-line', 'data-id': e.id}, `${n} ${e.kind === 'enter' ? 'comes in' : 'leaves'}`);
    }
    if (e.kind === 'doc') {
      const full = h('div', {class: 'prose-text hidden'}, h('div', {html: prose(e.content)}));
      const words = (e.content.match(/\S+/g) || []).length;
      return h('div', {class: 'doc', 'data-id': e.id},
        h('div', {class: 'doc-head'}, icon('doc'),
          h('button', {class: 'doc-title', onclick: () => full.classList.toggle('hidden')}, e.speaker || 'Untitled'),
          h('span', {class: 'muted small'}, `${words.toLocaleString()} words`),
          ibtn('trash', () => deleteEvent(e), {title: 'Delete'})),
        full);
    }
    if (e.kind === 'you') {
      const narr = !e.speaker || e.speaker.toLowerCase() === 'narrator';
      return h('div', {class: 'msg you', 'data-id': e.id},
        h('div', {class: 'body'}, h('span', {class: 'as'}, narr ? 'Narrator' : e.speaker),
          h('div', {class: 'bubble', onclick: () => youMenu(e)}, h('div', {class: 'prose-text', html: prose(e.content)}))));
    }
    const c = who[e.character_id] || {name: sc.names[e.character_id] || '?', hue: 0};
    const el = h('div', {class: `msg ${!e.temp && e.id === lastLineId() ? 'last' : ''}`, 'data-id': e.id});
    const body = h('div', {class: 'body'});
    const textEl = h('div', {class: 'prose-text'});
    textEl.innerHTML = prose(e.content);
    const innerText = h('span', {}, e.inner || '');
    const innerEl = h('div', {class: `inner ${showInner && e.inner ? '' : 'hidden'}`}, icon('heart'), innerText);
    body.append(h('div', {class: 'who'}, c.name, e.model_label ? h('span', {class: 'm'}, shortModel(e.model_label)) : null),
      innerEl, h('div', {class: 'bubble'}, textEl));
    body.addEventListener('click', (ev) => { if (!ev.target.closest('button,textarea,input,a')) el.classList.toggle('open'); });
    if (!e.temp) {
      const acts = h('div', {class: 'acts'});
      const n = (e.versions || []).length;
      if (n > 1) add(acts, h('span', {class: 'ver hover'},
        ibtn('left', () => pickVersion(e, e.pick - 1), {disabled: e.pick <= 0 || !!busy, title: 'Previous take'}), `${e.pick + 1} / ${n}`,
        ibtn('right', () => pickVersion(e, e.pick + 1), {disabled: e.pick >= n - 1 || !!busy, title: 'Next take'})), h('span', {class: 'sep hover'}));
      const isLast = e.id === lastEventId();
      add(acts,
        ibtn('redo', () => redo(e), {class: 'icon hover', title: 'Again', disabled: !!busy}),
        isLast ? ibtn('go', () => stream(`/api/events/${e.id}/continue`, {}, {content: e.content + ' ', inner: e.inner}, logIn.querySelector(`[data-id="${e.id}"]`)), {class: 'icon hover', title: 'Continue', disabled: !!busy}) : null,
        ibtn('swap', async () => { const m = await pickModel('Try with'); if (m) redo(e, {model: m}); }, {class: 'icon hover', title: 'Try another model', disabled: !!busy}),
        ibtn('up', () => rate(e, e.rating > 0 ? 0 : 1), {class: `icon ${e.rating > 0 ? 'on' : 'hover'}`, title: 'Sounds right'}),
        ibtn('down', () => thumbsDown(e, body), {class: `icon ${e.rating < 0 ? 'on' : 'hover'}`, title: 'Not like them'}),
        ibtn('star', () => starIt(e, body), {class: `icon ${e.starred ? 'on' : 'hover'}`, title: 'Idea'}),
        e.inner ? ibtn('heart', () => innerEl.classList.toggle('hidden'), {class: 'icon hover', title: 'Inside'}) : null,
        ibtn('edit', () => editEvent(e), {class: 'icon hover', title: 'Edit'}),
        ibtn('more', () => charMenu(e), {class: 'icon hover', title: 'More'}));
      body.append(acts);
      if (e.starred && e.idea) body.append(h('div', {class: 'recalled'}, '★ ' + e.idea));
      if ((e.recalled || []).length) {
        const list = h('ul', {class: 'hidden'}, e.recalled.map((r) => h('li', {}, r.text)));
        body.append(h('div', {class: 'recalled'}, h('button', {class: 'btn quiet small', style: 'padding:0 8px;height:26px', onclick: () => list.classList.toggle('hidden')},
          `Remembered ${e.recalled.length}`), list));
      }
    } else {
      textEl.classList.add('typing');
    }
    el.append(avatar(c), body);
    el._text = textEl;
    el._inner = innerEl;
    el._innerText = innerText;
    return el;
  }

  function replace(e) {
    const i = sc.events.findIndex((x) => x.id === e.id);
    if (i >= 0) sc.events[i] = e; else sc.events.push(e);
    const old = logIn.querySelector(`[data-id="${e.id}"]`);
    const el = msgEl(e);
    if (old) old.replaceWith(el); else logIn.append(el);
    return el;
  }

  // Only the newest character line keeps its buttons showing; redraw it so they're live again.
  function markLast() {
    const lid = lastLineId();
    for (const el of logIn.querySelectorAll('.msg.last')) if (+el.dataset.id !== lid) replace(sc.events.find((x) => x.id === +el.dataset.id));
    const e = sc.events.find((x) => x.id === lid);
    if (e && logIn.querySelector(`[data-id="${lid}"]`)) replace(e);
  }

  async function reload() { sc = await GET(`/api/scenes/${id}`); drawTop(); drawDock(); drawLog(); drawSide(); }

  // After a turn the helper model updates feelings in the background; look again a little later.
  let feelTimer = null;
  function refreshFeelings() {
    clearTimeout(feelTimer);
    feelTimer = setTimeout(async () => {
      try {
        const fresh = await GET(`/api/scenes/${id}`);
        if (JSON.stringify(fresh.feelings) !== JSON.stringify(sc.feelings)) { sc.feelings = fresh.feelings; if (sideTab === 'feelings') drawSide(); }
      } catch (e) {}
    }, 3500);
  }

  async function submit() {
    const text = input.value.trim();
    if (!text) { if (sc.here.length) { const {speakers: who} = await POST(`/api/scenes/${id}/next`, {more: true}); run(who); } return; }
    input.value = ''; grow();
    const ev = await POST(`/api/scenes/${id}/say`, {text, as});
    sc.events.push(ev);
    logIn.append(msgEl(ev));
    toBottom();
    if (sc.story.turns !== 'manual') {
      const {speakers: who} = await POST(`/api/scenes/${id}/next`, {});
      await run(who);
    }
  }

  function stop() { busy?.abort(); }

  // Stream turns one after the other.
  async function run(ids) {
    for (const cid of ids) {
      const ok = await stream(`/api/scenes/${id}/turn`, {character_id: cid}, {kind: 'character', character_id: cid, content: '', inner: '', temp: true, id: 'temp'});
      if (!ok) break;
    }
    refreshFeelings();
  }

  async function stream(url, body, temp, existing) {
    busy = new AbortController();
    drawDock();
    let el = existing || msgEl(temp);
    if (!existing) { logIn.append(el); toBottom(); }
    const base = existing ? {...temp} : temp;
    let failed = false;
    const paint = () => {
      const follow = nearBottom();
      el._text.innerHTML = prose(base.content);
      el._text.classList.add('typing');
      el._innerText.textContent = base.inner;
      el._inner.classList.toggle('hidden', !(showInner && base.inner));
      if (follow) toBottom();
    };
    try {
      await sse(url, body, (kind, data) => {
        if (kind === 'inner') base.inner += data;
        else if (kind === 'text') base.content += data;
        else if (kind === 'reset') { base.content = data; base.inner = ''; }
        else if (kind === 'done') {
          const i = sc.events.findIndex((x) => x.id === data.id);
          if (i >= 0) sc.events[i] = data; else sc.events.push(data);
          const fresh = msgEl(data);
          el.replaceWith(fresh);
          el = fresh;
          return;
        } else if (kind === 'error') {
          failed = true;
          el._text.classList.remove('typing');
          el._text.innerHTML = '';
          el._text.append(h('div', {class: 'err'}, ERR[data.code] || 'Error', data.detail ? h('div', {class: 'small muted'}, data.detail) : null));
          return;
        }
        paint();
      }, busy.signal);
    } catch (e) {
      failed = true;
      if (existing) replace(sc.events.find((x) => x.id === existing.dataset.id * 1)); else el.remove();
    }
    busy = null;
    drawDock();
    markLast();
    if (failed && !existing) setTimeout(() => el.isConnected && el.querySelector('.err') && el.remove(), 6000);
    return !failed;
  }

  async function redo(e, opts = {}) {
    const el = logIn.querySelector(`[data-id="${e.id}"]`);
    await stream(`/api/events/${e.id}/redo`, opts, {content: '', inner: ''}, el);
    refreshFeelings();
  }

  async function pickVersion(e, i) { replace(await POST(`/api/events/${e.id}/pick`, {index: i})); }
  async function rate(e, value) { replace(await POST(`/api/events/${e.id}/rate`, {value})); }

  function thumbsDown(e, body) {
    body.querySelector('.panel')?.remove();
    const name = people()[e.character_id]?.name || '';
    const note = h('textarea', {placeholder: `What would ${first(name)} do?`});
    const panel = h('div', {class: 'panel'}, note, h('div', {class: 'row'},
      h('button', {class: 'btn small quiet', onclick: () => panel.remove()}, 'Cancel'),
      h('button', {class: 'btn small', onclick: () => { panel.remove(); POST(`/api/events/${e.id}/rate`, {value: -1}); redo(e, {note: note.value}); }}, 'Redo'),
      h('button', {class: 'btn small primary', onclick: () => {
        if (!note.value.trim()) return note.focus();
        panel.remove(); POST(`/api/events/${e.id}/rate`, {value: -1}); redo(e, {note: note.value, save: true});
      }}, 'Save and redo')));
    body.append(panel);
    note.focus();
  }

  function starIt(e, body) {
    body.querySelector('.panel')?.remove();
    if (e.starred) { POST(`/api/events/${e.id}/star`, {starred: false}).then(replace); return; }
    const idea = h('textarea', {placeholder: 'Idea'});
    const panel = h('div', {class: 'panel'}, idea, h('div', {class: 'row'},
      h('button', {class: 'btn small quiet', onclick: () => panel.remove()}, 'Cancel'),
      h('button', {class: 'btn small primary', onclick: async () => replace(await POST(`/api/events/${e.id}/star`, {starred: true, idea: idea.value}))}, 'Save')));
    body.append(panel);
    idea.focus();
  }

  function editEvent(e) {
    const el = logIn.querySelector(`[data-id="${e.id}"]`);
    const target = el.querySelector('.body');
    const text = h('textarea', {class: 'prose', value: e.content, rows: 5});
    const inner = e.kind === 'character' ? h('textarea', {value: e.inner || '', placeholder: 'Inside', rows: 2}) : null;
    target.innerHTML = '';
    add(target, inner, text, h('div', {class: 'row', style: 'justify-content:flex-end'},
      h('button', {class: 'btn small', onclick: () => replace(e)}, 'Cancel'),
      h('button', {class: 'btn small primary', onclick: async () => replace(await PATCH(`/api/events/${e.id}`, {content: text.value, ...(inner ? {inner: inner.value} : {})}))}, 'Save')));
    text.focus();
  }

  async function rewindTo(e) {
    if (!await ask('Take back this line and everything after it?', 'Rewind')) return;
    await POST(`/api/events/${e.id}/rewind`);
    reload();
  }

  async function deleteEvent(e) {
    await DEL(`/api/events/${e.id}`);
    sc.events = sc.events.filter((x) => x.id !== e.id);
    logIn.querySelector(`[data-id="${e.id}"]`)?.remove();
    markLast();
  }

  function charMenu(e) {
    menu([
      ['Rewind to here', () => rewindTo(e)],
      ['Delete', () => deleteEvent(e), 'danger'],
    ]);
  }

  function youMenu(e) {
    if (busy) return;
    menu([['Edit', () => editEvent(e)], ['Rewind to here', () => rewindTo(e)], ['Delete', () => deleteEvent(e), 'danger']]);
  }

  async function presenceSheet() {
    const all = await GET('/api/characters');
    const inCast = new Set(sc.cast.map((c) => c.id));
    sheet((box, close) => {
      const list = h('div', {class: 'chips'});
      const draw = () => {
        list.innerHTML = '';
        for (const c of [...all].sort((a, b) => inCast.has(b.id) - inCast.has(a.id))) {
          const on = sc.here.includes(c.id);
          list.append(h('button', {class: `chip ${on ? 'on' : ''}`, onclick: async (ev) => {
            ev.currentTarget.disabled = true;
            await POST(`/api/scenes/${id}/presence`, {character_id: c.id, here: !on});
            await reload();
            draw();
          }}, avatar(c, 'sm'), c.name));
        }
      };
      draw();
      box.append(h('h2', {}, "Who's here"), list, h('div', {class: 'foot'},
        sc.here.length ? h('button', {class: 'btn', onclick: () => { close(); newSceneSheet({id: sc.story.id, cast: sc.cast}, {id, here: sc.here}); }}, 'Move to a new scene') : null,
        h('button', {class: 'btn primary', onclick: close}, 'Done')));
    });
  }

  function editScene() {
    sheet((box, close) => {
      const title = h('input', {value: sc.title});
      const setting = h('textarea', {class: 'prose', value: sc.setting, rows: 5});
      box.append(h('h2', {}, 'Scene'), field('Title', title), field('Setting', setting), h('div', {class: 'foot'},
        h('button', {class: 'btn', onclick: close}, 'Cancel'),
        h('button', {class: 'btn primary', onclick: async () => {
          await PATCH(`/api/scenes/${id}`, {title: title.value, setting: setting.value}); close(); reload();
        }}, 'Save')));
    });
  }

  function attachSheet() {
    const who = people();
    menu([
      ['This scene', async () => {
        const out = await bringIn('scene', id);
        if (out?.event) { sc.events.push(out.event); logIn.append(msgEl(out.event)); toBottom(); }
      }],
      ...sc.here.filter((i) => who[i]).map((i) => [`${who[i].name}’s journal`, () => bringIn('character', i)]),
      ['The story’s journal', () => bringIn('story', sc.story.id)],
    ]);
  }

  async function suggest() {
    wand.disabled = true;
    try {
      const {text} = await POST(`/api/scenes/${id}/suggest`, {as});
      input.value = text; grow(); input.focus();
    } catch (e) { toast(ERR[e.data?.error] || 'No suggestion'); }
    wand.disabled = false;
  }

  function sceneMenu() {
    menu([
      sc.whatif ? ['Make it count', async () => { await PATCH(`/api/scenes/${id}`, {whatif: false}); reload(); }] : null,
      sc.whatif ? ['Throw it away', async () => {
        if (await ask('Throw away this scene?', 'Throw away')) { await DEL(`/api/scenes/${id}`); location.hash = `#/story/${sc.story.id}`; }
      }, 'danger'] : null,
      ['Scene', editScene],
      ["Who's here", presenceSheet],
      ['What if', () => newSceneSheet(story || {id: sc.story.id, cast: sc.cast}, null, {whatif: true, with: sc.here})],
      sc.here.length ? ['Move to a new scene', () => newSceneSheet({id: sc.story.id, cast: sc.cast}, {id, here: sc.here})] : null,
      [showInner ? 'Hide what they feel' : 'Show what they feel', () => {
        showInner = !showInner; localStorage.setItem('bamah.inner', showInner ? '1' : '0'); drawLog();
      }],
      ['Story', () => (location.hash = `#/story/${sc.story.id}`)],
      sc.state === 'ended' ? ['Reopen scene', async () => { await POST(`/api/scenes/${id}/reopen`); reload(); }]
        : ['End scene', async () => { toast('Writing memories…'); await POST(`/api/scenes/${id}/end`); reload(); }],
      sc.whatif ? null : ['Delete scene', async () => {
        if (await ask('Delete this scene and what they remember of it?')) { await DEL(`/api/scenes/${id}`); location.hash = `#/story/${sc.story.id}`; }
      }, 'danger'],
    ]);
  }

  // The side panel: how they feel, what they remember, the story's journal.
  function drawSide() {
    side.innerHTML = '';
    const tabs = [['feelings', 'Feelings'], ['memory', 'Memory'], ['journal', 'Journal']];
    side.append(h('div', {class: 'side-head'}, h('div', {class: 'pills quiet'}, tabs.map(([k, label]) =>
      h('button', {class: k === sideTab ? 'on' : '', onclick: () => { sideTab = k; localStorage.setItem('bamah.side', k); drawSide(); }}, label))),
      ibtn('close', () => side.classList.remove('open'), {title: 'Close'})));
    const who = people();
    const here = sc.here.map((i) => who[i]).filter(Boolean);
    const list = here.length ? here : sc.cast;
    if (sideTab === 'feelings') {
      const byId = Object.fromEntries(sc.cast.map((c) => [String(c.id), c]));
      side.append(h('div', {class: 'feel'}, list.map((c) => feelCard(c, sc.feelings?.[String(c.id)], sc.names, byId))));
    } else if (sideTab === 'memory') {
      const box = h('div', {class: 'feel'});
      side.append(box);
      for (const c of list) {
        const card = h('div', {class: 'feelcard'}, h('a', {class: 'fhead', href: `#/character/${c.id}?s=memory`}, avatar(c, 'md'), h('div', {class: 'who'}, h('b', {}, c.name))));
        box.append(card);
        GET(`/api/characters/${c.id}`).then((full) => {
          const st = full.stories.find((x) => x.id === sc.story.id);
          const mems = (st?.memories || []).slice().sort((a, b) => (b.pinned || 0) - (a.pinned || 0)).slice(0, 8);
          if (st?.learned) card.append(h('div', {class: 'small', style: 'white-space:pre-wrap;color:var(--muted);max-height:9em;overflow:hidden'}, st.learned));
          card.append(mems.length ? h('ul', {class: 'small', style: 'margin:0;padding-left:18px;display:grid;gap:6px'}, mems.map((m) => h('li', {}, m.text)))
            : h('div', {class: 'muted small'}, '—'));
        }).catch(() => {});
      }
    } else {
      const reloadJ = async () => { story = await GET(`/api/stories/${sc.story.id}`); drawSide(); };
      side.append(journalEditor((story?.journal || []).filter((j) => !j.character_id), {story_id: sc.story.id}, reloadJ));
    }
  }

  drawTop(); drawDock(); drawLog(); drawSide(); toBottom();
  if (!sc.here.length && !sc.events.length) presenceSheet();
  leave = () => { busy?.abort(); clearTimeout(feelTimer); settle.disconnect(); };
}

// --- Characters -------------------------------------------------------------------------------

async function newCharacter() {
  const {id} = await POST('/api/characters', {name: 'New character'});
  location.hash = `#/character/${id}`;
}

async function charactersView() {
  const list = await GET('/api/characters');
  const filter = query().story || null;
  const main = frame('characters', {filter, top: h('button', {class: 'sqbtn', 'aria-label': 'New character', onclick: newCharacter}, icon('plus'))});
  const shown = filter ? list.filter((c) => c.stories.some((s) => String(s.id) === String(filter))) : list;
  const story = filter && list.flatMap((c) => c.stories).find((s) => String(s.id) === String(filter));
  main.append(h('div', {class: 'head'}, h('h1', {}, story ? story.title : 'Characters'),
    h('button', {class: 'btn', onclick: () => librarySheet(null)}, icon('image'), 'Portraits'),
    h('button', {class: 'btn primary', 'data-tour': 'new-character', onclick: newCharacter}, icon('plus'), 'New character')));
  const grid = h('div', {class: 'gallery'});
  for (const c of shown) {
    grid.append(h('a', {class: 'pcard', href: `#/character/${c.id}`, 'data-text': `${c.name} ${c.personality || ''}`.toLowerCase()},
      h('div', {class: 'pimg', style: c.avatar ? '' : `background:${hue(c)}`},
        c.avatar ? h('img', {src: `/avatars/${c.avatar}`, alt: '', loading: 'lazy'}) : h('span', {class: 'letter'}, initial(c.name)),
        c.model_label ? h('span', {class: 'tag'}, shortModel(c.model_label)) : null),
      h('div', {class: 'pmeta'},
        h('div', {class: 'pname'}, h('b', {}, c.name), c.pronouns ? h('span', {}, c.pronouns) : null),
        c.personality ? h('div', {class: 'pline'}, c.personality) : null,
        c.stories.length ? h('div', {class: 'pchips'}, c.stories.slice(0, 2).map((s) => h('span', {}, s.title))) : null)));
  }
  grid.append(h('button', {class: 'newtile', onclick: newCharacter}, h('span', {}, icon('plus')), 'New character'));
  main.append(grid);
  const onSearch = (e) => {
    const v = (e.detail || '').trim().toLowerCase();
    for (const el of grid.querySelectorAll('.pcard')) el.classList.toggle('hidden', !!v && !el.dataset.text.includes(v));
  };
  document.addEventListener('bamah:search', onSearch);
  leave = () => document.removeEventListener('bamah:search', onSearch);

  const personas = await GET('/api/personas');
  main.append(h('h2', {}, 'You play'), h('div', {class: 'chips'},
    personas.map((p) => h('button', {class: 'chip', onclick: () => personaSheet(p, () => charactersView())}, avatar({name: p.name, hue: 0}, 'sm'), p.name)),
    h('button', {class: 'chip plain', onclick: () => personaSheet(null, () => charactersView())}, icon('plus'), 'Persona')));
}

// The portrait library: everything made here, plus the public-domain portraits that came with Bamah.
// With a character: picking one makes it theirs. Without: just to look through.
async function librarySheet(c, done) {
  const all = await GET('/api/portraits');
  sheet((box, close) => {
    let kind = 'all';
    const q = h('input', {type: 'search', placeholder: 'Search', 'aria-label': 'Search'});
    const grid = h('div', {class: 'lib'});
    const draw = () => {
      const v = q.value.trim().toLowerCase();
      grid.innerHTML = '';
      const hits = all.filter((p) => (kind === 'all' || (kind === 'mine' ? !p.source : p.source && p.style === kind))
        && (!v || `${p.source || ''} ${p.name || ''} ${p.prompt || ''}`.toLowerCase().includes(v)));
      for (const p of hits.slice(0, 600)) grid.append(h('button', {class: `thumb ${c && p.file === c.avatar ? 'on' : ''}`, title: p.source || p.name || '',
        onclick: () => menu([
          c ? ['Use', async () => { await POST(`/api/characters/${c.id}/portrait`, {portrait_id: p.id}); close(); done?.(); }] : null,
          p.prompt ? ['Copy description', () => navigator.clipboard?.writeText(p.prompt).then(() => toast('Copied'))] : null,
          p.source ? ['Where it’s from', () => toast(p.source)] : null,
          ['Delete', async () => { await DEL(`/api/portraits/${p.id}`); all.splice(all.indexOf(p), 1); draw(); }, 'danger'],
        ])}, h('img', {src: `/avatars/${p.file}`, alt: '', loading: 'lazy'})));
      if (!hits.length) grid.append(h('div', {class: 'muted'}, '—'));
    };
    q.addEventListener('input', draw);
    box.append(h('div', {class: 'row', style: 'margin-bottom:12px'}, h('h2', {class: 'grow', style: 'margin:0'}, c ? `${c.name}: portrait` : 'Portraits'), ibtn('close', close, {title: 'Close'})),
      h('div', {class: 'libbar'}, h('label', {class: 'search'}, icon('search'), q),
        seg([['all', 'All'], ['painted', 'Painted'], ['photo', 'Photos'], ['mine', 'Made here']], kind, (v) => { kind = v; draw(); })),
      grid);
    draw();
  }, 'wide');
}

function noteList(items, {text = (x) => x.text, onsave, ondelete, onpin, meta}) {
  const box = h('div', {class: 'notes'});
  for (const it of items) {
    const note = h('div', {class: `note ${it.pinned ? 'pinned' : ''}`});
    const draw = () => {
      note.innerHTML = '';
      add(note, h('div', {class: 'grow'}, meta ? h('div', {class: 'meta'}, meta(it)) : null, h('div', {class: 'text'}, text(it))),
        onpin ? ibtn('pin', () => onpin(it), {class: `icon ${it.pinned ? 'on' : ''}`, title: 'Pin'}) : null,
        onsave ? ibtn('edit', () => {
          const t = h('textarea', {value: text(it)});
          note.innerHTML = '';
          note.append(h('div', {class: 'grow'}, t, h('div', {class: 'row', style: 'justify-content:flex-end;margin-top:6px'},
            h('button', {class: 'btn small', onclick: draw}, 'Cancel'),
            h('button', {class: 'btn small primary', onclick: async () => { await onsave(it, t.value); it.text = t.value; draw(); }}, 'Save'))));
          t.focus();
        }, {title: 'Edit'}) : null,
        ibtn('trash', async () => { await ondelete(it); note.remove(); }, {title: 'Delete'}));
    };
    draw();
    box.append(note);
  }
  return box;
}

function adder(placeholder, onadd) {
  const t = h('textarea', {placeholder, rows: 2, style: 'min-height:48px'});
  return h('div', {class: 'row', style: 'margin-top:8px;align-items:flex-end'}, t,
    h('button', {class: 'btn', onclick: async () => { if (t.value.trim()) { await onadd(t.value.trim()); } }}, 'Add'));
}

const SECTIONS = [['personality', 'Personality', 'person'], ['portrait', 'Portrait', 'image'], ['memory', 'Memory', 'memory'],
  ['feelings', 'Feelings', 'heart'], ['corrections', 'Corrections', 'edit'], ['journal', 'Journal', 'book'], ['model', 'Model', 'chip']];

async function characterView(id) {
  const c = await GET(`/api/characters/${id}`);
  const sec = SECTIONS.some(([k]) => k === query().s) ? query().s : 'personality';
  const go = (k) => `#/character/${id}?s=${k}`;
  const reload = () => characterView(id);
  const backTo = () => (history.length > 1 ? history.back() : (location.hash = '#/characters'));
  const nav = h('aside', {class: 'cnav'},
    h('a', {class: 'back', href: '#/characters'}, icon('back'), 'Characters'),
    h('div', {class: 'me'}, avatar(c, 'lg'), h('div', {}, h('b', {}, c.name), c.pronouns ? h('span', {}, c.pronouns) : null)),
    h('nav', {}, SECTIONS.map(([k, label, ic]) => h('a', {href: go(k), class: k === sec ? 'on' : ''}, icon(ic), label))));
  const main = frame('characters', {nav});
  main.style.cssText = 'max-width:none;padding:0;display:flex';
  const save = saver(`/api/characters/${id}`);
  const file = h('input', {type: 'file', accept: 'image/*', class: 'hidden', onchange: async () => {
    const fd = new FormData();
    fd.append('file', file.files[0]);
    await fetch(`/api/characters/${id}/avatar`, {method: 'POST', body: fd});
    reload();
  }});
  const body = h('div', {class: 'cbody'});
  body.append(file,
    h('div', {class: 'cmhead'}, ibtn('back', backTo, {title: 'Back'}), avatar(c, 'md'), h('b', {class: 'grow'}, c.name)),
    h('nav', {class: 'csecs'}, SECTIONS.map(([k, label]) => h('a', {href: go(k), class: k === sec ? 'on' : ''}, label))));
  const inner = h('div', {class: 'cbody-in'});
  body.append(inner);
  main.append(body);
  const col = h('div', {class: 'ccol'});
  inner.append(col);
  const ta = (key, rows, cls = 'prose') => h('textarea', {class: cls, rows, value: c[key] || '', oninput: (e) => save({[key]: e.target.value})});

  // The portrait and its buttons; shown beside the personality and on its own page.
  const portraitBlock = () => {
    let style = 'painted';
    const gen = h('button', {class: 'btn primary grow', onclick: async () => {
      if (!(await getSettings(true)).settings.portrait_model) {     // nothing to paint with yet: pick one here
        const v = await pickModel('Portraits', {images: true});
        if (!v) return;
        await PUT('/api/settings', {portrait_model: v});
      }
      gen.disabled = true; gen.textContent = 'Painting…';
      try { await POST(`/api/characters/${id}/portraits`, {style}); reload(); }
      catch (e) { toast(ERR[e.data?.error] || 'No portrait'); gen.disabled = false; gen.replaceChildren(icon('wand'), 'Generate'); }
    }}, icon('wand'), 'Generate');
    return {
      pic: h('div', {class: 'bigportrait', style: c.avatar ? '' : `background:${hue(c)}`},
        c.avatar ? h('img', {src: `/avatars/${c.avatar}`, alt: c.name}) : h('span', {class: 'letter'}, initial(c.name))),
      seg: seg([['photo', 'Photoreal'], ['painted', 'Painted'], ['anime', 'Anime']], style, (v) => { style = v; }),
      buttons: h('div', {class: 'row'}, gen, h('button', {class: 'btn grow', onclick: () => file.click()}, 'Upload'),
        h('button', {class: 'sqbtn', style: 'width:40px;height:40px;border-radius:12px', title: 'Library', 'aria-label': 'Library', 'data-tour': 'library', onclick: () => librarySheet(c, reload)}, icon('grid'))),
    };
  };

  if (sec === 'personality') {
    const words = h('input', {placeholder: 'A few words', 'aria-label': 'A few words'});
    const draftBtn = h('button', {class: 'btn primary', onclick: async () => {
      if (!words.value.trim()) return words.focus();
      const keys = ['pronouns', 'appearance', 'personality', 'inner_life', 'voice', 'key_memories'];
      if (keys.some((k) => (c[k] || '').trim()) && !await ask('Replace what’s there?', 'Replace', false)) return;
      draftBtn.disabled = true; draftBtn.textContent = 'Drafting…';
      try {
        const out = await POST(`/api/characters/${id}/draft`, {words: words.value});
        await PATCH(`/api/characters/${id}`, out);
        reload();
      } catch (e) { toast(ERR[e.data?.error] || 'No draft'); draftBtn.disabled = false; draftBtn.textContent = 'Draft'; }
    }}, 'Draft');
    words.addEventListener('keydown', (e) => { if (e.key === 'Enter') draftBtn.click(); });
    const personas = await GET('/api/personas');
    const tied = h('select', {'aria-label': 'Usually with', onchange: () => PATCH(`/api/characters/${id}`, {persona_id: tied.value ? +tied.value : null})},
      h('option', {value: ''}, '—'), personas.map((p) => h('option', {value: p.id}, p.name)));
    tied.value = c.persona_id || '';
    const name = h('input', {value: c.name, 'aria-label': 'Name', oninput: () => save({name: name.value})});
    col.append(h('h1', {style: 'margin:0 0 4px'}, 'Personality'),
      h('div', {class: 'draftbar', 'data-tour': 'draft'}, h('label', {}, icon('wand'), words), draftBtn),
      add(h('div', {class: 'group'}),
        mark(line('Name', name), 'name'),
        line('Pronouns', h('input', {value: c.pronouns || '', 'aria-label': 'Pronouns', oninput: (e) => save({pronouns: e.target.value})})),
        line('Speaks as', seg([['', 'Story’s'], ['first', 'I'], ['third', 'She / he / they']], c.person || '', (v) => PATCH(`/api/characters/${id}`, {person: v || null}))),
        line('Style', seg([['', 'Story’s'], ...STYLES], c.style || '', (v) => PATCH(`/api/characters/${id}`, {style: v || null}))),
        personas.length ? line('Usually with', tied) : null),
      mark(fieldCard('Who they are', ta('personality', 5)), 'who'),
      fieldCard('Inner life', ta('inner_life', 3)),
      fieldCard('How they talk', ta('voice', 3)),
      fieldCard('Always remembers', ta('key_memories', 3, '')),
      fieldCard('Always', ta('directive', 2, '')));
    const pb = portraitBlock();
    inner.append(h('div', {class: 'cside'}, pb.pic, pb.buttons,
      fieldCard('Appearance', ta('appearance', 3)),
      h('div', {class: 'group'}, line('Model', modelButton(c.model ? c.model.split('/').slice(1).join('/') : '', "Story's model",
        (v) => PATCH(`/api/characters/${id}`, {model: v || null}), {allowDefault: true, defaultLabel: "Story's model"})))));
  } else if (sec === 'portrait') {
    const pb = portraitBlock();
    col.append(h('h1', {style: 'margin:0 0 4px'}, 'Portrait'), fieldCard('Appearance', ta('appearance', 3)),
      h('div', {class: 'row wrap'}, pb.seg), pb.buttons);
    const lib = h('div', {class: 'lib'});
    col.append(h('h3', {}, 'Made for them'), lib);
    GET('/api/portraits').then((all) => {
      const mine = all.filter((p) => p.character_id === id || p.file === c.avatar);
      for (const p of mine) lib.append(h('button', {class: `thumb ${p.file === c.avatar ? 'on' : ''}`, onclick: () => menu([
        ['Use', async () => { await POST(`/api/characters/${id}/portrait`, {portrait_id: p.id}); reload(); }],
        p.prompt ? ['Copy description', () => navigator.clipboard?.writeText(p.prompt).then(() => toast('Copied'))] : null,
        ['Delete', async () => { await DEL(`/api/portraits/${p.id}`); reload(); }, 'danger'],
      ])}, h('img', {src: `/avatars/${p.file}`, alt: '', loading: 'lazy'})));
      if (!mine.length) lib.append(h('div', {class: 'muted'}, '—'));
    });
    col.append(h('div', {style: 'margin-top:12px'}, h('button', {class: 'btn', onclick: () => librarySheet(c, reload)}, icon('grid'), 'Library')));
    inner.append(h('div', {class: 'cside'}, pb.pic));
  } else if (sec === 'memory') {
    col.append(h('h1', {style: 'margin:0'}, 'Memory'));
    if (!c.stories.length) col.append(h('div', {class: 'muted'}, '—'));
    for (const s of c.stories) {
      const learned = h('textarea', {rows: 8, value: s.learned, oninput: debounce(() => PUT(`/api/learned/${s.id}/${id}`, {text: learned.value}))});
      col.append(h('h2', {}, h('a', {href: `#/story/${s.id}`}, s.title)), fieldCard('Come to know', learned),
        h('h3', {}, 'Memories'),
        noteList(s.memories, {meta: (m) => m.scene_title || '', onpin: async (m) => { await PATCH(`/api/memories/${m.id}`, {pinned: m.pinned ? 0 : 1}); reload(); },
          onsave: (m, t) => PATCH(`/api/memories/${m.id}`, {text: t}), ondelete: (m) => DEL(`/api/memories/${m.id}`)}),
        adder('Memory', async (t) => { await POST('/api/memories', {character_id: id, story_id: s.id, text: t}); reload(); }));
    }
  } else if (sec === 'feelings') {
    col.append(h('h1', {style: 'margin:0'}, 'Feelings'));
    if (!c.stories.length) col.append(h('div', {class: 'muted'}, '—'));
    const people = {};
    for (const s of c.stories) {
      col.append(h('h2', {}, h('a', {href: `#/story/${s.id}`}, s.title)), feelCard(c, s.feelings[0], c.names, people));
      if (s.feelings.length > 1) {
        const arc = h('div', {class: 'arc hidden'}, s.feelings.slice(1).map((f) => h('div', {},
          h('div', {class: 'when'}, f.created_at.slice(0, 16).replace('T', ' ')),
          h('div', {style: 'font:italic 15px/1.45 var(--prose);margin:2px 0'}, [f.word, f.mood].filter(Boolean).join(' · ')),
          Object.entries(f.toward || {}).map(([k, how]) => h('div', {class: 'small'}, h('b', {}, c.names[k] || k), ' ', how)))));
        col.append(h('div', {}, h('button', {class: 'btn quiet small', onclick: () => arc.classList.toggle('hidden')}, 'Earlier')), arc);
      }
    }
  } else if (sec === 'corrections') {
    col.append(h('h1', {style: 'margin:0'}, 'Corrections'),
      noteList(c.corrections, {onsave: (it, t) => PATCH(`/api/corrections/${it.id}`, {text: t}), ondelete: (it) => DEL(`/api/corrections/${it.id}`)}),
      adder('Correction', async (t) => { await POST(`/api/characters/${id}/corrections`, {text: t}); reload(); }));
    if (c.examples.length) col.append(h('h2', {}, 'Sounded right'), noteList(c.examples, {ondelete: (it) => DEL(`/api/examples/${it.id}`)}));
  } else if (sec === 'journal') {
    col.append(h('h1', {style: 'margin:0'}, 'Journal'), journalEditor(c.journal, {character_id: id}, reload));
  } else if (sec === 'model') {
    col.append(h('h1', {style: 'margin:0'}, 'Model'),
      h('div', {class: 'group'}, line('Model', modelButton(c.model ? c.model.split('/').slice(1).join('/') : '', "Story's model",
        (v) => PATCH(`/api/characters/${id}`, {model: v || null}), {allowDefault: true, defaultLabel: "Story's model"}))),
      h('div', {style: 'margin-top:28px'}, h('button', {class: 'btn danger', onclick: async () => {
        if (await ask(`Delete ${c.name}?`)) { await DEL(`/api/characters/${id}`); location.hash = '#/characters'; }
      }}, 'Delete character')));
  }
}

// --- Ideas ------------------------------------------------------------------------------------

async function ideasView() {
  const list = await GET('/api/ideas');
  const main = frame('ideas');
  main.append(h('div', {class: 'head'}, h('h1', {}, 'Ideas')));
  if (!list.length) return main.append(h('div', {class: 'empty muted'}, '—'));
  main.append(h('div', {class: 'list', style: 'max-width:780px'}, list.map((it) => {
    const idea = h('textarea', {value: it.idea || '', placeholder: 'Idea', rows: 2, style: 'min-height:48px;margin-top:10px',
      oninput: debounce(() => POST(`/api/events/${it.id}/star`, {starred: true, idea: idea.value}))});
    const who = it.kind === 'you' ? (it.speaker || 'Narrator') : it.name;
    const card = h('div', {class: 'card'},
      h('div', {class: 'row'}, it.kind === 'character' ? avatar(it, 'md') : null, h('div', {class: 'grow'}, h('b', {}, who),
        h('div', {class: 'small muted'}, h('a', {href: `#/scene/${it.scene_id}`}, `${it.story_title} · ${it.scene_title || 'Untitled'}`))),
        ibtn('star', async () => { await POST(`/api/events/${it.id}/star`, {starred: false}); card.remove(); }, {class: 'icon on', title: 'Remove'})),
      h('div', {class: 'prose-text', style: 'margin-top:10px', html: prose(it.content)}), idea);
    return card;
  })));
}

// --- Settings ---------------------------------------------------------------------------------

async function settingsView() {
  const s = await getSettings(true);
  const main = frame('settings');
  const reload = () => settingsView();
  const wrap = h('div', {style: 'max-width:760px'});
  main.append(wrap);
  wrap.append(h('div', {class: 'head'}, h('h1', {}, 'Settings')));

  wrap.append(h('h3', {style: 'margin-top:0'}, 'Models'));
  const conns = h('div', {class: 'group', 'data-tour': 'models'});
  for (const c of s.connections.filter((c) => c.preset !== 'chatgpt')) {
    conns.append(h('div', {class: 'rowline'},
      h('div', {class: 'grow'}, h('div', {style: 'font-weight:600'}, c.name), h('div', {class: 'small muted'}, [s.presets[c.preset]?.name, c.key_tail ? `•••• ${c.key_tail}` : null, c.preset === 'ollama' || c.preset === 'custom' ? c.base_url : null].filter(Boolean).join(' · '))),
      ibtn('edit', () => connectionSheet(s, c, reload), {title: 'Edit'}),
      ibtn('trash', async () => { if (await ask(`Remove ${c.name}?`, 'Remove')) { await DEL(`/api/connections/${c.id}`); reload(); } }, {title: 'Remove'})));
  }
  conns.append(h('div', {class: 'rowline'}, h('button', {class: 'btn small', onclick: () => connectionSheet(s, null, reload)}, icon('plus'), 'Add')));
  wrap.append(conns);

  wrap.append(h('h3', {}, 'ChatGPT'));
  if (s.chatgpt) {
    wrap.append(h('div', {class: 'group'}, h('div', {class: 'rowline'}, h('div', {class: 'grow'}, h('div', {style: 'font-weight:600'}, 'ChatGPT'), h('div', {class: 'small muted'}, s.chatgpt.email || s.chatgpt.name)),
      h('button', {class: 'btn small', onclick: async () => { if (await ask('Disconnect ChatGPT?', 'Disconnect')) { await POST('/api/chatgpt/disconnect'); reload(); } }}, 'Disconnect'))));
  } else {
    const paste = h('input', {placeholder: 'Address from the ChatGPT tab'});
    const err = h('div', {class: 'err'});
    const finish = h('div', {class: 'hidden', style: 'margin-top:10px'}, h('div', {class: 'row'}, paste,
      h('button', {class: 'btn primary', onclick: async () => {
        try { await POST('/api/chatgpt/finish', {url: paste.value}); toast('Connected'); reload(); }
        catch (e) { err.textContent = e.data?.error === 'state' || e.data?.error === 'start' ? 'Start again' : e.data?.error === 'scope' ? 'Plan usage not granted' : 'Not connected'; }
      }}, 'Connect')), err);
    wrap.append(h('div', {class: 'card'}, h('button', {class: 'btn', onclick: async () => {
      const {url} = await POST('/api/chatgpt/start');
      window.open(url, '_blank', 'noopener');
      finish.classList.remove('hidden');
      paste.focus();
    }}, 'Continue with ChatGPT'), finish));
    const q = query();
    if (q.chatgpt) err.textContent = 'Not connected';
  }

  const set = (k) => (v) => PUT('/api/settings', {[k]: v});
  wrap.append(h('h3', {}, 'Default'), h('div', {class: 'group'},
    line('Characters', modelButton(s.labels.default_model, 'Pick', async (v) => { await PUT('/api/settings', {default_model: v}); })),
    line('Memory and turn order', modelButton(s.labels.helper_model, 'Same as characters', async (v) => { await PUT('/api/settings', {helper_model: v}); }, {allowDefault: true, defaultLabel: 'Same as characters'})),
    line('Portraits', modelButton(s.labels.portrait_model, 'Pick', async (v) => { await PUT('/api/settings', {portrait_model: v}); }, {images: true})),
    mark(line('Thinking', seg([['off', 'Off'], ['low', 'Low'], ['high', 'High']], s.settings.thinking, set('thinking'))), 'thinking')));

  wrap.append(h('h3', {}, 'Memory'), h('div', {class: 'group'},
    line('Short-term', seg([['20000', 'Small'], ['60000', 'Medium'], ['150000', 'Large'], ['400000', 'Huge']], s.settings.short_term, set('short_term'))),
    line('Memories recalled per reply', seg([['3', '3'], ['6', '6'], ['9', '9'], ['15', '15']], s.settings.recall, set('recall'))),
    line('Feelings', seg([['1', 'Track'], ['0', 'Off']], s.settings.feelings, set('feelings'))),
    line('Replies per round', seg([['1', '1'], ['2', '2'], ['3', '3'], ['5', '5']], s.settings.round, set('round'))),
    line('Repetition guard', seg([['1', 'On'], ['0', 'Off']], s.settings.repetition, set('repetition')))));

  const local = (k, fallback) => { try { return localStorage.getItem(k) || fallback; } catch (e) { return fallback; } };
  const keep = (k) => (v) => { try { localStorage.setItem(k, v); } catch (e) {} applyLook(); };
  wrap.append(h('h3', {}, 'Reading'), h('div', {class: 'group'},
    line('Text size', seg([['0.9', 13], ['1', 15], ['1.12', 18], ['1.25', 21]].map(([v, px]) => [v, h('span', {style: `font:600 ${px}px var(--prose)`}, 'A')]), local('bamah.size', '1'), keep('bamah.size'))),
    line('Theme', seg([['dark', 'Dark'], ['light', 'Light'], ['auto', 'Auto']], local('bamah.theme', 'dark'), keep('bamah.theme'))),
    line('Tour', h('button', {class: 'btn small', onclick: () => tourStart()}, 'Start'))));

  wrap.append(h('h3', {}, 'Shared journal'));
  const gj = await GET('/api/journal');
  wrap.append(journalEditor(gj, {}, reload));

  wrap.append(h('h3', {}, 'Data'), h('div', {class: 'row wrap'},
    h('a', {class: 'btn', href: '/api/backup', download: ''}, 'Backup'),
    s.signin ? h('button', {class: 'btn', onclick: async () => { await POST('/api/logout'); location.href = '/login'; }}, 'Sign out') : null));
}

function connectionSheet(s, c, done) {
  sheet((box, close) => {
    let preset = c?.preset || 'openrouter';
    const name = h('input', {value: c?.name || ''});
    const key = h('input', {type: 'password', placeholder: c?.has_key ? '•••• ' + (c.key_tail || '') : '', autocomplete: 'off'});
    const url = h('input', {value: c?.base_url || ''});
    const fields = h('div');
    const draw = () => {
      const p = s.presets[preset];
      if (!c) { name.value = p.name; url.value = p.base_url; }
      fields.innerHTML = '';
      fields.append(field('Name', name));
      if (p.key || preset === 'custom') fields.append(field('Key', key));
      if (preset !== 'anthropic') fields.append(field('Address', url));
    };
    const presets = Object.entries(s.presets).filter(([k]) => k !== 'chatgpt').map(([k, p]) => [k, p.name]);
    add(box, h('h2', {}, c ? c.name : 'Add a connection'),
      c ? null : seg(presets, preset, (v) => { preset = v; draw(); }), fields,
      h('div', {class: 'foot'}, h('button', {class: 'btn', onclick: close}, 'Cancel'),
        h('button', {class: 'btn primary', onclick: async () => {
          const body = {name: name.value, base_url: url.value};
          if (key.value) body.api_key = key.value;
          if (c) await PATCH(`/api/connections/${c.id}`, body);
          else await POST('/api/connections', {preset, ...body});
          close();
          settingsCache = null;
          if (!c && !s.settings.default_model) {
            const v = await pickModel('Default model');
            if (v) await PUT('/api/settings', {default_model: v});
          }
          done();
        }}, 'Save')));
    draw();
  });
}

// --- The tour: a first story, one step at a time ----------------------------------------------
// It points at one thing, says one thing, and waits while she does it. Progress is kept per device,
// so it carries on across pages and reloads. It starts by itself on a device's first visit while there's no story yet.

const TOUR = 'bamah.tour';
const T = {state: null, root: null, spot: null, card: null, tick: null, checking: false, lastCheck: 0};
const visible = (el) => { if (!el) return null; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 ? el : null; };
const pick = (...sels) => { for (const sel of sels) { const el = [...document.querySelectorAll(sel)].reverse().find(visible); if (el) return el; } return null; };
const at = (re) => () => re.test(location.hash || '#/');
const story = () => T.state?.story;
const twoCharacters = async () => (await GET('/api/characters')).filter((c) => (c.personality || '').trim()).length >= 2;

const STEPS = [
  {title: 'Welcome to Bamah', center: true, next: 'Start',
    text: "Bamah is a stage for your characters. In a few minutes you'll make two of them, put them in a scene together and see how they take to each other."},
  {title: 'First, a model', go: '#/settings', at: at(/^#\/settings/), target: () => pick('[data-tour=models] .btn', '[data-tour=models]'),
    text: 'Your characters need a model to speak through. Tap Add, choose a service and paste its key. OpenRouter is the easiest start: one key opens almost every model. Then choose which model they use.',
    done: async () => { const x = await getSettings(true); return x.connections.length > 0 && !!x.settings.default_model; }},
  {title: 'Your first character', go: '#/characters', at: at(/^#\/characters/), target: () => pick('[data-tour=new-character]'),
    text: 'Tap New character.', skip: twoCharacters, done: async () => /^#\/character\/\d+/.test(location.hash)},
  {title: 'Start from a few words', at: at(/^#\/character\/\d+/), target: () => pick('[data-tour=draft]'), skip: twoCharacters,
    text: 'Write a few words about who they are, like “proud, funny, runs her late mother’s kitchen”, and tap Draft. It fills in the rest, and you can change any of it.',
    done: async () => !!document.querySelector('[data-tour=who] textarea')?.value.trim()},
  {title: 'Their name', at: at(/^#\/character\/\d+/), target: () => pick('[data-tour=name]'), skip: twoCharacters,
    text: 'Give them a name here. Their pronouns, how they speak and their style are just below.'},
  {title: 'A face', at: at(/^#\/character\/\d+/), target: () => pick('[data-tour=library]'), skip: twoCharacters, next: 'Next',
    text: 'Open the library and choose a portrait, or upload one of your own.',
    done: async () => !!document.querySelector('.bigportrait img')},
  {title: 'Who they are', at: at(/^#\/character\/\d+/), target: () => pick('[data-tour=who]'), skip: twoCharacters,
    text: 'These boxes are the character: who they are, their inner life, how they talk, what they always remember. The more specific, the more they sound like themselves.'},
  {title: 'Someone to talk to', go: '#/characters', at: at(/^#\/character/), target: () => pick('[data-tour=new-character]'), skip: twoCharacters,
    text: 'Now make a second character the same way: New character, a few words, Draft, a name and a face. Then Next.',
    done: twoCharacters, next: 'Next', hold: true},
  {title: 'A story', go: '#/', at: at(/^#\/?(\?.*)?$/), target: () => pick('[data-tour=new-story]', '.empty .btn'),
    text: 'Tap New story.', done: async () => /^#\/story\/\d+/.test(location.hash),
    keep: () => ({story: +location.hash.match(/^#\/story\/(\d+)/)[1]})},
  {title: 'What it’s about', go: () => `#/story/${story()}?tab=setup`, at: () => location.hash.startsWith(`#/story/${story()}`) && query().tab === 'setup',
    target: () => pick('[data-tour=premise]'),
    text: 'Give the story a title at the top and a premise here. Everyone in the story knows the premise.'},
  {title: 'The cast', go: () => `#/story/${story()}?tab=setup`, at: () => location.hash.startsWith(`#/story/${story()}`) && query().tab === 'setup',
    target: () => pick('[data-tour=cast]'), text: 'Add both characters to the cast with Add.',
    done: async () => (await GET(`/api/stories/${story()}`)).cast.length >= 2},
  {title: 'A scene', go: () => `#/story/${story()}?tab=scenes`, at: () => location.hash.startsWith(`#/story/${story()}`) && (query().tab || 'scenes') === 'scenes',
    target: () => pick('[data-tour=new-scene]'),
    text: 'Tap New scene. Say where and when it happens, choose who’s in it, and Start.',
    done: async () => /^#\/scene\/\d+/.test(location.hash), keep: () => ({scene: +location.hash.match(/^#\/scene\/(\d+)/)[1]})},
  {title: 'Set it going', go: () => `#/scene/${T.state.scene}`, at: at(/^#\/scene\/\d+/), target: () => pick('[data-tour=composer]'),
    text: 'Write what happens, as the narrator: someone walks in, a letter arrives, a question is asked. Send it, and the characters answer.',
    done: async () => !!document.querySelector('.msg.last .acts')},
  {title: 'What they don’t say', at: at(/^#\/scene\/\d+/), target: () => pick('.msg.last .inner', '.msg .inner'),
    text: 'This line is what the character feels and keeps to themselves. It shapes how they answer, and only you can see it.'},
  {title: 'When a line isn’t right', at: at(/^#\/scene\/\d+/), target: () => pick('.msg.last .acts'),
    text: 'The circle arrow asks for a new take. The thumbs down lets you say what they’d really do, and can keep it as a correction for next time. The crossed arrows try the line with another model.'},
  {title: 'Who speaks next', at: at(/^#\/scene\/\d+/), target: () => pick('[data-tour=speakers]'),
    text: 'Tap a face to have that character answer, or Go on to let the scene decide.'},
  {title: 'How they feel', at: at(/^#\/scene\/\d+/), target: () => innerWidth >= 1280 ? pick('[data-tour=feelings]') : pick('[data-tour=feelings-btn]'),
    text: 'After every line, each character’s mood and feelings toward the others are updated here. The bars show how strongly they feel it.'},
  {title: 'What if', at: at(/^#\/scene\/\d+/), target: () => pick('[data-tour=whatif]', '[data-tour=scene-menu]'),
    text: 'A what-if scene is a sketch. Nothing in it is remembered unless you decide it counts.'},
  {title: 'When the scene is over', at: at(/^#\/scene\/\d+/), target: () => pick('[data-tour=scene-menu]'),
    text: 'End it from this menu. Each character keeps memories of what they saw, and carries them into the next scene.'},
  {title: 'That’s the stage', center: true, next: 'Done', text: 'You can take this tour again from Settings.'},
];

function tourSave() { try { localStorage.setItem(TOUR, JSON.stringify(T.state)); } catch (e) {} }

function tourStart() {
  T.state = {i: 0};
  tourSave();
  tourShow();
}

function tourEnd() {
  T.state = null;
  try { localStorage.removeItem(TOUR); localStorage.setItem('bamah.tour.seen', '1'); } catch (e) {}
  clearInterval(T.tick);
  T.root?.remove();
  T.root = null;
}

async function tourGo(i) {
  if (i < 0) i = 0;
  if (i >= STEPS.length) return tourEnd();
  T.state.i = i;
  tourSave();
  const st = STEPS[i];
  try { if (st.skip && await st.skip()) return tourGo(i + 1); } catch (e) {}
  const where = typeof st.go === 'function' ? st.go() : st.go;
  if (where && st.at && !st.at()) location.hash = where;
  tourShow();
}

async function tourNext() {
  const st = STEPS[T.state.i];
  if (st.keep) Object.assign(T.state, st.keep());
  tourGo(T.state.i + 1);
}

function tourShow() {
  if (!T.state) return;
  if (!T.root) {
    T.spot = h('div', {class: 'tour-spot'});
    T.card = h('div', {class: 'tour-card', role: 'dialog', 'aria-live': 'polite'});
    T.root = h('div', {class: 'tour'}, T.spot, T.card);
    document.body.append(T.root);
    clearInterval(T.tick);
    T.tick = setInterval(tourFollow, 300);
  }
  const st = STEPS[T.state.i];
  const steps = STEPS.length - 2;          // the welcome and the last card don't count
  T.card.innerHTML = '';
  const n = T.state.i;
  add(T.card,
    !st.center ? h('div', {class: 'tour-n'}, `${n} / ${steps}`) : null,
    h('div', {class: 'tour-t'}, st.title),
    h('div', {class: 'tour-x'}, st.text),
    h('div', {class: 'tour-b'},
      n > 0 && !st.center ? h('button', {class: 'btn quiet small', onclick: () => tourGo(n - 1)}, 'Back') : null,
      h('button', {class: 'btn quiet small', onclick: tourEnd}, n === 0 ? 'Not now' : st.center ? null : 'Skip tour'),
      h('span', {class: 'grow'}),
      h('button', {class: 'btn small tour-there hidden', onclick: () => { const w = typeof st.go === 'function' ? st.go() : st.go; if (w) location.hash = w; }}, 'Take me there'),
      h('button', {class: `btn primary small tour-next ${st.done && (!st.next || st.hold) ? 'hidden' : ''}`, onclick: tourNext}, st.next || 'Next')));
  if (st.center && n > 0) T.card.querySelector('.tour-b .btn.quiet')?.remove();
  T.root.classList.toggle('center', !!st.center);
  tourFollow();
}

// Keep the highlight on its target, and check whether she has done what the step asks.
function tourFollow() {
  if (!T.state || !T.root) return;
  const st = STEPS[T.state.i];
  const blocked = !!document.querySelector('.veil');            // a sheet is open: let it have the screen
  T.root.classList.toggle('under', blocked);
  const here = !st.at || st.at();
  T.card.querySelector('.tour-there')?.classList.toggle('hidden', here || !st.go);
  const el = !st.center && here ? st.target?.() : null;
  if (el) {
    const r = el.getBoundingClientRect();
    if (r.top < 0 || r.bottom > innerHeight) el.scrollIntoView({block: 'center', behavior: 'smooth'});
    const pad = 6;
    Object.assign(T.spot.style, {display: 'block', left: `${r.left - pad}px`, top: `${r.top - pad}px`, width: `${r.width + pad * 2}px`, height: `${r.height + pad * 2}px`});
    placeCard(r);
  } else {
    T.spot.style.display = 'none';
    placeCard(null);
  }
  if (st.done && !T.checking && Date.now() - T.lastCheck > 900) {      // doing it often takes her to another page
    T.checking = true;
    T.lastCheck = Date.now();
    st.done().then((ok) => {
      T.checking = false;
      if (!ok || STEPS[T.state?.i] !== st) return;
      if (st.next) T.card.querySelector('.tour-next')?.classList.remove('hidden');
      else setTimeout(() => STEPS[T.state?.i] === st && tourNext(), 500);
    }).catch(() => { T.checking = false; });
  }
}

function placeCard(r) {
  const c = T.card;
  const w = Math.min(340, innerWidth - 24);
  c.style.width = `${w}px`;
  const ch = c.offsetHeight || 180;
  let left, top;
  if (!r) { left = (innerWidth - w) / 2; top = Math.max(12, (innerHeight - ch) / 2); }
  else {
    left = Math.min(Math.max(12, r.left), innerWidth - w - 12);
    if (r.bottom + 14 + ch < innerHeight - 8) top = r.bottom + 14;
    else if (r.top - 14 - ch > 8) top = r.top - 14 - ch;
    else { top = innerHeight - ch - 12; left = (innerWidth - w) / 2; }
  }
  c.style.left = `${left}px`;
  c.style.top = `${top}px`;
}

// On the first visit to an empty Bamah, or to carry on where she left off.
async function tourMaybe() {
  try { T.state = JSON.parse(localStorage.getItem(TOUR) || 'null'); } catch (e) { T.state = null; }
  if (T.state) return tourShow();
  let seen = null;
  try { seen = localStorage.getItem('bamah.tour.seen'); } catch (e) {}
  if (seen) return;
  try {
    if (!(await GET('/api/stories')).length) tourStart();
  } catch (e) {}
}

route().then(tourMaybe);
