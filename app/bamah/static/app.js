// Bamah: the page. Plain JavaScript, no build step.

const $app = document.getElementById('app');

const P = {
  back: '<path d="M15 18l-6-6 6-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  send: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  up: '<path d="M7 11v9H4v-9h3zm0 0l4-8c1.5 0 2.5 1 2.3 2.6L13 9h5.6c1.3 0 2.2 1.2 1.9 2.4l-1.6 6.5c-.2.9-1 1.6-2 1.6H7"/>',
  down: '<g transform="rotate(180 12 12)"><path d="M7 11v9H4v-9h3zm0 0l4-8c1.5 0 2.5 1 2.3 2.6L13 9h5.6c1.3 0 2.2 1.2 1.9 2.4l-1.6 6.5c-.2.9-1 1.6-2 1.6H7"/></g>',
  star: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8L3.5 9.7l5.9-.9z"/>',
  redo: '<path d="M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5"/>',
  swap: '<path d="M7 7h12l-3-3M17 17H5l3 3"/>',
  more: '<circle cx="5" cy="12" r="1.4" fill="currentColor"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/><circle cx="19" cy="12" r="1.4" fill="currentColor"/>',
  heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
  people: '<circle cx="9" cy="8" r="3.2"/><path d="M3 19c.6-3.3 3-5 6-5s5.4 1.7 6 5"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.2c2.5.2 4.5 1.7 5 4.8"/>',
  book: '<path d="M4 5.5C6.5 4 9.5 4 12 5.5 14.5 4 17.5 4 20 5.5V19c-2.5-1.5-5.5-1.5-8 0-2.5-1.5-5.5-1.5-8 0zM12 5.5V19"/>',
  bulb: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
  sliders: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  pin: '<path d="M9 4h6l-1 6 4 3H6l4-3zM12 13v7"/>',
  trash: '<path d="M5 7h14M10 7V5h4v2M7 7l1 13h8l1-13"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
  stop: '<rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor"/>',
  go: '<path d="M6 6l6 6-6 6M13 6l6 6-6 6"/>',
  left: '<path d="M14 7l-5 5 5 5"/>',
  right: '<path d="M10 7l5 5-5 5"/>',
  clip: '<path d="M20 11.5l-8.2 8.2a5 5 0 0 1-7.1-7.1l8.6-8.6a3.3 3.3 0 0 1 4.7 4.7l-8.6 8.6a1.7 1.7 0 0 1-2.4-2.4l7.9-7.9"/>',
  wand: '<path d="M4 20L15 9M14 3.5v3M12.5 5h3M19.5 8v2.5M18.2 9.2h2.6M19 14.5v2M18 15.5h2"/>',
  doc: '<path d="M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6"/>',
};

// Reading comfort: text size and theme are per device.
function applyLook() {
  let size = '1', theme = 'auto';
  try { size = localStorage.getItem('bamah.size') || '1'; theme = localStorage.getItem('bamah.theme') || 'auto'; } catch (e) {}
  document.documentElement.style.setProperty('--scale', size);
  if (theme === 'auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', theme);
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

// append, skipping empty slots (Element.append would print them as "null")
const add = (el, ...kids) => { el.append(...kids.flat().filter((k) => k != null && k !== false)); return el; };

const ibtn = (name, onclick, props = {}) => h('button', {class: 'icon', type: 'button', onclick, ...props}, icon(name));

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

function toast(text) {
  const t = h('div', {class: 'toast'}, text);
  document.body.append(t);
  setTimeout(() => t.remove(), 2200);
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"]/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
}

function prose(text) {
  const t = esc(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>*$1*</em>');
  return t.split(/\n{2,}/).map((p) => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}

const hue = (c) => `hsl(${c?.hue ?? 30} 36% 44%)`;
function avatar(c, size = '') {
  const el = h('span', {class: `av ${size}`, style: `background:${hue(c)}`, title: c?.name || ''});
  if (c?.avatar) el.append(h('img', {src: `/avatars/${c.avatar}`, alt: ''}));
  else el.textContent = (c?.name || '?').trim().charAt(0).toUpperCase();
  return el;
}
const stack = (people, size = 'sm') => h('div', {class: 'stack'}, (people || []).slice(0, 6).map((c) => avatar(c, size)));

const STYLES = [['dialogue', 'Talk'], ['roleplay', 'Roleplay'], ['narrative', 'Narrative']];

const ERR = {key: 'Key not accepted', model: 'Model not found', limit: 'Limit reached', refused: 'Declined by the model',
  network: "Can't reach the service", down: 'Service error', setup: 'No model set', request: 'Request refused', empty: 'Empty reply'};

// --- Sheets -------------------------------------------------------------------------------------

function sheet(build) {
  const box = h('div', {class: 'sheet', role: 'dialog'});
  const veil = h('div', {class: 'veil', onclick: (e) => { if (e.target === veil) close(); }}, box);
  const onkey = (e) => { if (e.key === 'Escape') close(); };
  function close() { veil.remove(); document.removeEventListener('keydown', onkey); }
  document.addEventListener('keydown', onkey);
  document.body.append(veil);
  build(box, close);
  box.querySelector('input,textarea')?.focus();
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
function pickModel(title, {allowDefault, defaultLabel = 'Default'} = {}) {
  return new Promise(async (done) => {
    const s = await getSettings(true);
    sheet((box, close) => {
      const finish = (v) => { close(); done(v); };
      box.append(h('h2', {}, title));
      if (!s.connections.length) {
        box.append(h('div', {class: 'foot'}, h('a', {class: 'btn primary', href: '#/settings', onclick: () => finish(null)}, 'Settings')));
        return;
      }
      const body = h('div');
      const list = h('div', {class: 'menu'});
      if (allowDefault) list.append(h('button', {onclick: () => finish('')}, defaultLabel));
      for (const c of s.connections) list.append(h('button', {onclick: () => open(c)}, c.name));
      body.append(list);
      box.append(body);
      async function open(c) {
        body.innerHTML = '';
        const search = h('input', {type: 'search', placeholder: s.presets[c.preset]?.model_label || 'Model'});
        const results = h('div', {class: 'picker-list'}, h('div', {class: 'muted small', style: 'padding:10px'}, 'Loading…'));
        const typed = h('button', {class: 'btn small', onclick: () => search.value.trim() && finish(`${c.id}/${search.value.trim()}`)}, 'Use');
        body.append(h('div', {class: 'row'}, ibtn('back', () => { body.innerHTML = ''; body.append(list); }), h('b', {}, c.name)),
          h('div', {class: 'row', style: 'margin-top:8px'}, search, typed), results);
        let all = [];
        try { all = await GET(`/api/connections/${c.id}/models`); }
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

// --- Frame and routing ------------------------------------------------------------------------

const TABS = [['stories', '#/', 'Stories', 'book'], ['characters', '#/characters', 'Characters', 'people'],
  ['ideas', '#/ideas', 'Ideas', 'bulb'], ['settings', '#/settings', 'Settings', 'sliders']];

function frame(active, {scene = false} = {}) {
  document.body.classList.toggle('in-scene', scene);
  $app.innerHTML = '';
  const nav = h('nav', {class: 'nav'}, TABS.map(([k, href, label]) => h('a', {href, class: k === active ? 'on' : ''}, label)));
  const top = h('header', {class: 'top'}, h('div', {class: 'top-in'}, h('a', {class: 'brand', href: '#/'}, 'Bamah'), nav));
  const main = h('main');
  const bottom = h('nav', {class: 'tabs-bottom'}, TABS.map(([k, href, label, ic]) => h('a', {href, class: k === active ? 'on' : ''}, icon(ic), label)));
  $app.append(top, main, bottom);
  return main;
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
      try { await fn(m); } catch (e) { console.error(e); if (e.message !== 'signin') { frame(''); $app.querySelector('main').append(h('div', {class: 'empty err'}, 'Not found')); } }
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
  const main = frame('stories');
  main.append(h('div', {class: 'head'}, h('h1', {}, 'Stories'), h('button', {class: 'btn primary', onclick: newStory}, icon('plus'), 'New story')));
  if (!list.length) return main.append(h('div', {class: 'empty'}, h('button', {class: 'btn primary', onclick: newStory}, 'New story')));
  main.append(h('div', {class: 'list'}, list.map((s) => h('a', {class: 'item', href: `#/story/${s.id}`},
    h('div', {class: 'grow'}, h('div', {class: 't'}, s.title), s.premise ? h('div', {class: 's'}, s.premise) : null),
    stack(s.cast), h('span', {class: 'badge'}, `${s.scenes} ${s.scenes === 1 ? 'scene' : 'scenes'}`)))));
}

async function storyView(id, tab) {
  const s = await GET(`/api/stories/${id}`);
  tab = tab || query().tab || 'scenes';
  const main = frame('stories');
  const save = debounce((patch) => PATCH(`/api/stories/${id}`, patch));
  const title = h('input', {class: 'title-input', value: s.title, oninput: () => save({title: title.value})});
  main.append(h('div', {class: 'row'}, ibtn('back', () => (location.hash = '#/')), h('div', {class: 'grow'}, title)));
  const tabs = [['scenes', 'Scenes'], ['feelings', 'Feelings'], ['setup', 'Setup'], ['journal', 'Journal']];
  const body = h('div');
  const bar = h('div', {class: 'tabs'}, tabs.map(([k, label]) => h('button', {class: k === tab ? 'on' : '', onclick: () => {
    history.replaceState(null, '', `#/story/${id}?tab=${k}`); storyView(id, k);
  }}, label)));
  main.append(bar, body);
  ({scenes: storyScenes, feelings: storyFeelings, setup: storySetup, journal: storyJournal})[tab](s, body, save);
}

function storyScenes(s, body) {
  const people = Object.fromEntries(s.cast.map((c) => [c.id, c]));
  body.append(h('div', {class: 'row', style: 'margin-bottom:14px'}, h('div', {class: 'grow'}),
    h('button', {class: 'btn primary', onclick: () => newSceneSheet(s)}, icon('plus'), 'New scene')));
  if (!s.scenes.length) return body.append(h('div', {class: 'empty'}, h('button', {class: 'btn primary', onclick: () => newSceneSheet(s)}, 'New scene')));
  body.append(h('div', {class: 'list'}, s.scenes.map((sc) => h('a', {class: 'item', href: `#/scene/${sc.id}`},
    h('div', {class: 'grow'}, h('div', {class: 't'}, sc.title || 'Untitled'), sc.setting ? h('div', {class: 's'}, sc.setting) : null),
    stack(sc.everyone.map((i) => people[i]).filter(Boolean)),
    sc.whatif ? h('span', {class: 'badge whatif'}, 'What if') : null,
    sc.state === 'ended' ? h('span', {class: 'badge'}, 'Ended') : null))));
}

async function newSceneSheet(s, from) {
  const all = await GET('/api/characters');
  const inCast = new Set(s.cast.map((c) => c.id));
  const chosen = new Set(from ? from.here : []);
  sheet((box, close) => {
    const title = h('input', {placeholder: 'Title'});
    const setting = h('textarea', {class: 'prose'});
    const chips = h('div', {class: 'chips'});
    const pool = from ? all.filter((c) => from.here.includes(c.id)) : [...all].sort((a, b) => inCast.has(b.id) - inCast.has(a.id));
    const draw = () => {
      chips.innerHTML = '';
      for (const c of pool) chips.append(h('button', {class: `chip ${chosen.has(c.id) ? 'on' : ''}`, type: 'button',
        onclick: () => { chosen.has(c.id) ? chosen.delete(c.id) : chosen.add(c.id); draw(); }}, avatar(c, 'xs'), c.name));
    };
    draw();
    let whatif = false;
    const wi = h('button', {class: 'chip plain', type: 'button', onclick: () => { whatif = !whatif; wi.classList.toggle('on', whatif); }}, 'What if');
    box.append(h('h2', {}, from ? 'Move to a new scene' : 'New scene'),
      h('label', {class: 'field'}, h('span', {}, 'Title'), title),
      h('label', {class: 'field'}, h('span', {}, 'Setting'), setting),
      h('div', {class: 'field'}, h('span', {class: 'muted small'}, from ? 'Who goes' : "Who's in it"), h('div', {style: 'margin-top:6px'}, chips)),
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

function feelingCard(c, f, names, people) {
  const card = h('div', {class: 'card'});
  card.append(h('a', {class: 'row', href: `#/character/${c.id}`}, avatar(c, 'sm'), h('b', {}, c.name)));
  if (!f) { card.append(h('div', {class: 'muted', style: 'margin-top:8px'}, '—')); return card; }
  if (f.mood) card.append(h('div', {class: 'mood'}, f.mood));
  const tw = h('div', {class: 'toward'});
  for (const [k, how] of Object.entries(f.toward || {})) {
    const other = people[k] || {name: names[k] || k};
    tw.append(h('div', {class: 'row'}, avatar(other, 'xs'), h('div', {class: 'grow'}, h('div', {class: 'name'}, other.name), h('div', {class: 'how'}, how))));
  }
  card.append(tw);
  return card;
}

function storyFeelings(s, body) {
  const people = Object.fromEntries(s.cast.map((c) => [String(c.id), c]));
  if (!s.cast.length) return body.append(h('div', {class: 'empty muted'}, '—'));
  body.append(h('div', {class: 'feel'}, s.cast.map((c) => feelingCard(c, s.feelings[String(c.id)], s.names, people))));
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

function modelButton(label, fallback, onpick, opts) {
  const b = h('button', {class: 'btn', type: 'button', onclick: async () => {
    const v = await pickModel('Model', opts);
    if (v === null) return;
    await onpick(v);
    b.textContent = v ? v.split('/').slice(1).join('/') : fallback;
  }}, label || fallback);
  return b;
}

function storySetup(s, body, save) {
  const ta = (key, cls = 'prose', rows) => h('textarea', {class: cls, value: s[key] || '', rows, oninput: (e) => save({[key]: e.target.value})});
  body.append(
    field('Premise', ta('premise', 'prose', 6)),
    field('How it is written', ta('directive', '', 3)),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Style'), h('div', {style: 'margin-top:6px'},
      seg(STYLES, s.style, (v) => PATCH(`/api/stories/${s.id}`, {style: v})))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Characters speak as'), h('div', {style: 'margin-top:6px'},
      seg([['first', 'I'], ['third', 'She / he / they']], s.person || 'first', (v) => PATCH(`/api/stories/${s.id}`, {person: v})))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Length'), h('div', {style: 'margin-top:6px'},
      seg([['short', 'Short'], ['medium', 'Medium'], ['long', 'Long']], s.length, (v) => PATCH(`/api/stories/${s.id}`, {length: v})))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Memory'), h('div', {style: 'margin-top:6px'},
      seg([['witnessed', 'Only what they saw'], ['shared', 'Everyone knows everything']], s.memory, (v) => PATCH(`/api/stories/${s.id}`, {memory: v})))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Who answers'), h('div', {style: 'margin-top:6px'},
      seg([['auto', 'The story picks'], ['manual', 'I pick']], s.turns, (v) => PATCH(`/api/stories/${s.id}`, {turns: v})))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Model'), h('div', {style: 'margin-top:6px'},
      modelButton(s.model ? s.model.split('/').slice(1).join('/') : '', 'Default', (v) => PATCH(`/api/stories/${s.id}`, {model: v || null}), {allowDefault: true}))),
  );

  body.append(h('h3', {}, 'You play'));
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
    })}, '+ Persona'));
  };
  drawPersonas();
  body.append(pBox);

  body.append(h('h3', {}, 'Cast'));
  const castBox = h('div', {class: 'chips'});
  for (const c of s.cast) castBox.append(h('span', {class: 'chip'}, avatar(c, 'xs'), h('a', {href: `#/character/${c.id}`}, c.name),
    h('button', {class: 'icon', style: 'width:22px;height:22px', onclick: async () => { await DEL(`/api/stories/${s.id}/cast/${c.id}`); storyView(s.id, 'setup'); }}, icon('close'))));
  castBox.append(h('button', {class: 'chip plain', onclick: () => addCastSheet(s)}, '+ Add'));
  body.append(castBox);

  body.append(h('h3', {}, 'Story'), h('div', {class: 'row wrap'},
    h('a', {class: 'btn', href: `/api/stories/${s.id}/export`, download: ''}, 'Export'),
    h('button', {class: 'btn danger', onclick: async () => {
      if (await ask(`Delete “${s.title}”?`)) { await DEL(`/api/stories/${s.id}`); location.hash = '#/'; }
    }}, 'Delete story')));
}

async function addCastSheet(s) {
  const all = await GET('/api/characters');
  const inCast = new Set(s.cast.map((c) => c.id));
  sheet((box, close) => {
    const name = h('input', {placeholder: 'Name'});
    box.append(h('h2', {}, 'Add to the cast'),
      h('div', {class: 'chips'}, all.filter((c) => !inCast.has(c.id)).map((c) => h('button', {class: 'chip', onclick: async () => {
        await POST(`/api/stories/${s.id}/cast`, {character_id: c.id}); close(); storyView(s.id, 'setup');
      }}, avatar(c, 'xs'), c.name))),
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
    const view = h('div', {class: 'grow'}, h('div', {}, h('b', {}, j.title || ''), j.keys ? h('span', {class: 'meta'}, '  ' + j.keys) : null),
      h('div', {class: 'text', style: 'padding-top:2px'}, j.text));
    const note = h('div', {class: 'note'}, view,
      ibtn('edit', () => {
        const t = h('input', {value: j.title, placeholder: 'Title'}), k = h('input', {value: j.keys, placeholder: 'Keyphrases'}), x = h('textarea', {value: j.text});
        note.innerHTML = '';
        note.append(h('div', {class: 'grow'}, t, h('div', {style: 'height:6px'}), k, h('div', {style: 'height:6px'}), x,
          h('div', {class: 'row', style: 'justify-content:flex-end;margin-top:6px'},
            h('button', {class: 'btn small', onclick: reload}, 'Cancel'),
            h('button', {class: 'btn small primary', onclick: async () => { await PATCH(`/api/journal/${j.id}`, {title: t.value, keys: k.value, text: x.value}); reload(); }}, 'Save'))));
      }),
      ibtn('trash', async () => { await DEL(`/api/journal/${j.id}`); reload(); }));
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
  body.append(journalEditor(s.journal.filter((j) => !j.character_id), {story_id: s.id}, () => storyView(s.id, 'journal')));
}

// --- A scene ----------------------------------------------------------------------------------

async function sceneView(id) {
  let sc = await GET(`/api/scenes/${id}`);
  const main = frame('stories', {scene: true});
  let busy = null;                  // the AbortController of what's streaming
  let showInner = localStorage.getItem('bamah.inner') !== '0';
  const people = () => Object.fromEntries(sc.cast.map((c) => [c.id, c]));

  const titleBox = h('div', {class: 'scene-title', onclick: () => editScene()});
  const here = h('button', {class: 'icon', style: 'width:auto;padding:0 4px', onclick: () => presenceSheet()});
  const top = h('div', {class: 'scene-top'}, ibtn('back', () => (location.hash = `#/story/${sc.story.id}`)), titleBox, here, ibtn('more', () => sceneMenu()));
  const logIn = h('div', {class: 'log-in'});
  const log = h('div', {class: 'log'}, logIn);
  const speakers = h('div', {class: 'speakers'});
  const as = h('select');
  const input = h('textarea', {rows: 1, placeholder: 'Write'});
  const send = h('button', {class: 'send', onclick: () => (busy ? stop() : submit())}, icon('send'));
  const attach = ibtn('clip', () => attachSheet(), {title: 'File'});
  const wand = ibtn('wand', () => suggest(), {title: 'Write my line'});
  const tools = h('div', {class: 'tools'}, attach, wand);
  const dock = h('div', {class: 'dock'}, h('div', {class: 'dock-in'}, h('div', {class: 'dock-row'}, speakers, tools),
    h('div', {class: 'compose'}, as, input, send)));
  main.append(h('div', {class: 'scene'}, top, log, dock));

  input.addEventListener('input', grow);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && matchMedia('(hover: hover)').matches) { e.preventDefault(); if (!busy) submit(); }
  });
  function grow() { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, innerHeight * 0.4) + 'px'; }

  function drawTop() {
    titleBox.innerHTML = '';
    const names = sc.here.map((i) => people()[i]?.name).filter(Boolean);
    titleBox.append(h('div', {class: 't'}, sc.title || 'Untitled', sc.whatif ? h('span', {class: 'badge whatif'}, 'What if') : null),
      h('div', {class: 's'}, names.join(', ') || '—'));
    here.innerHTML = '';
    here.append(sc.here.length ? stack(sc.here.map((i) => people()[i]), 'sm') : icon('people'));
  }

  function drawDock() {
    speakers.innerHTML = '';
    const ended = sc.state === 'ended';
    for (const i of sc.here) {
      const c = people()[i];
      if (c) speakers.append(h('button', {class: 'chip', disabled: !!busy || ended, onclick: () => run([i])}, avatar(c, 'xs'), c.name.split(' ')[0]));
    }
    if (sc.here.length) speakers.append(h('button', {class: 'chip plain', disabled: !!busy || ended, title: 'Go on', onclick: async () => {
      const {speakers: who} = await POST(`/api/scenes/${id}/next`, {more: true}); run(who);
    }}, icon('go')));
    else speakers.append(h('button', {class: 'chip plain', onclick: presenceSheet}, icon('people'), "Who's here"));
    as.innerHTML = '';
    const inStory = new Set(sc.story.personas || []);
    const ps = [...(sc.personas || [])].sort((a, b) => inStory.has(b.id) - inStory.has(a.id));
    add(as, h('option', {value: ''}, 'Narrator'), ps.map((p) => h('option', {value: p.name}, p.name)));
    as.classList.toggle('hidden', !ps.length);
    as.value = localStorage.getItem(`bamah.as.${sc.story.id}`) || '';
    if (!ps.some((p) => p.name === as.value)) as.value = '';
    attach.disabled = wand.disabled = !!busy || ended;
    send.innerHTML = '';
    send.append(icon(busy ? 'stop' : 'send'));
    input.disabled = ended;
    input.placeholder = ended ? 'Ended' : 'Write';
  }
  as.addEventListener('change', () => localStorage.setItem(`bamah.as.${sc.story.id}`, as.value));

  function nearBottom() { return log.scrollHeight - log.scrollTop - log.clientHeight < 160; }
  function toBottom() { log.scrollTop = log.scrollHeight; }

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
          ibtn('trash', () => deleteEvent(e))),
        full);
    }
    if (e.kind === 'you') {
      const narr = !e.speaker || e.speaker.toLowerCase() === 'narrator';
      const el = h('div', {class: `msg you ${narr ? 'narr' : ''}`, 'data-id': e.id},
        h('div', {class: 'bubble', onclick: () => youMenu(e)}, !narr ? h('div', {class: 'as'}, e.speaker) : null, h('div', {class: 'prose-text', html: prose(e.content)})));
      return el;
    }
    const c = who[e.character_id] || {name: sc.names[e.character_id] || '?', hue: 0};
    const el = h('div', {class: 'msg', 'data-id': e.id});
    const body = h('div', {class: 'body'});
    const textEl = h('div', {class: 'prose-text', html: prose(e.content)});
    const innerEl = h('div', {class: `inner ${showInner && e.inner ? '' : 'hidden'}`}, e.inner || '');
    body.append(h('div', {class: 'who', style: `color:${hue(c)}`}, c.name, e.model_label ? h('span', {class: 'm'}, e.model_label.split(' · ')[0]) : null), innerEl, textEl);
    body.addEventListener('click', (ev) => { if (!ev.target.closest('button,textarea,input,a')) el.classList.toggle('open'); });
    if (!e.temp) {
      const acts = h('div', {class: 'acts'});
      const n = (e.versions || []).length;
      if (n > 1) acts.append(h('span', {class: 'ver'},
        ibtn('left', () => pickVersion(e, e.pick - 1), {disabled: e.pick <= 0 || !!busy}), `${e.pick + 1}/${n}`,
        ibtn('right', () => pickVersion(e, e.pick + 1), {disabled: e.pick >= n - 1 || !!busy})));
      add(acts,
        ibtn('up', () => rate(e, e.rating > 0 ? 0 : 1), {class: `icon ${e.rating > 0 ? 'on' : ''}`, title: 'Sounds right'}),
        ibtn('down', () => thumbsDown(e, body), {class: `icon ${e.rating < 0 ? 'on' : ''}`, title: 'Not like them'}),
        ibtn('star', () => starIt(e, body), {class: `icon ${e.starred ? 'on' : ''}`, title: 'Idea'}),
        ibtn('redo', () => redo(e), {class: 'icon hover', title: 'Again', disabled: !!busy}),
        ibtn('swap', async () => { const m = await pickModel('Try with'); if (m) redo(e, {model: m}); }, {class: 'icon hover', title: 'Try another model', disabled: !!busy}),
        e.inner ? ibtn('heart', () => innerEl.classList.toggle('hidden'), {class: 'icon hover', title: 'Inside'}) : null,
        ibtn('more', () => charMenu(e), {class: 'icon hover'}));
      body.append(acts);
      if (e.starred && e.idea) body.append(h('div', {class: 'recalled'}, '★ ' + e.idea));
      if ((e.recalled || []).length) {
        const list = h('ul', {class: 'hidden'}, e.recalled.map((r) => h('li', {}, r.text)));
        body.append(h('div', {class: 'recalled'}, h('button', {class: 'btn quiet small', style: 'padding:2px 6px', onclick: () => list.classList.toggle('hidden')},
          `Remembered ${e.recalled.length}`), list));
      }
    } else {
      textEl.classList.add('typing');
    }
    el.append(avatar(c, 'sm'), body);
    el._text = textEl;
    el._inner = innerEl;
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

  async function reload() { sc = await GET(`/api/scenes/${id}`); drawTop(); drawDock(); drawLog(); }

  async function submit() {
    const text = input.value.trim();
    if (!text) { if (sc.here.length) { const {speakers: who} = await POST(`/api/scenes/${id}/next`, {more: true}); run(who); } return; }
    input.value = ''; grow();
    const ev = await POST(`/api/scenes/${id}/say`, {text, as: as.value});
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
      el._inner.textContent = base.inner;
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
    if (failed && !existing) setTimeout(() => el.isConnected && el.querySelector('.err') && el.remove(), 6000);
    return !failed;
  }

  async function redo(e, opts = {}) {
    const el = logIn.querySelector(`[data-id="${e.id}"]`);
    await stream(`/api/events/${e.id}/redo`, opts, {content: '', inner: ''}, el);
  }

  async function pickVersion(e, i) { replace(await POST(`/api/events/${e.id}/pick`, {index: i})); }
  async function rate(e, value) { replace(await POST(`/api/events/${e.id}/rate`, {value})); }

  function thumbsDown(e, body) {
    body.querySelector('.panel')?.remove();
    const name = people()[e.character_id]?.name || '';
    const note = h('textarea', {placeholder: `What would ${name.split(' ')[0]} do?`});
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
    const target = el.querySelector('.body') || el.querySelector('.bubble');
    const text = h('textarea', {class: 'prose', value: e.content, rows: 5});
    const inner = e.kind === 'character' ? h('textarea', {value: e.inner || '', placeholder: 'Inside', rows: 2}) : null;
    target.innerHTML = '';
    add(target, inner, text, h('div', {class: 'row', style: 'justify-content:flex-end;margin-top:6px'},
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
  }

  function charMenu(e) {
    const last = [...sc.events].reverse().find((x) => x.kind !== 'enter' && x.kind !== 'leave');
    menu([
      last?.id === e.id ? ['Continue', () => stream(`/api/events/${e.id}/continue`, {}, {content: e.content + ' ', inner: e.inner}, logIn.querySelector(`[data-id="${e.id}"]`))] : null,
      ['Edit', () => editEvent(e)],
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
          }}, avatar(c, 'xs'), c.name));
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
      const {text} = await POST(`/api/scenes/${id}/suggest`, {as: as.value});
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

  drawTop(); drawDock(); drawLog(); toBottom();
  if (!sc.here.length && !sc.events.length) presenceSheet();
  leave = () => busy?.abort();
}

// --- Characters -------------------------------------------------------------------------------

async function newCharacter() {
  const {id} = await POST('/api/characters', {name: 'New character'});
  location.hash = `#/character/${id}`;
}

async function charactersView() {
  const list = await GET('/api/characters');
  const main = frame('characters');
  main.append(h('div', {class: 'head'}, h('h1', {}, 'Characters'), h('button', {class: 'btn primary', onclick: newCharacter}, icon('plus'), 'New character')));
  if (!list.length) main.append(h('div', {class: 'empty'}, h('button', {class: 'btn primary', onclick: newCharacter}, 'New character')));
  else main.append(h('div', {class: 'grid'}, list.map((c) => h('a', {class: 'person', href: `#/character/${c.id}`},
    avatar(c, 'lg'), h('div', {class: 't'}, c.name), c.personality ? h('div', {class: 's'}, c.personality) : null))));
  const personas = await GET('/api/personas');
  main.append(h('h2', {}, 'You play'), h('div', {class: 'chips'},
    personas.map((p) => h('button', {class: 'chip plain', onclick: () => personaSheet(p, () => charactersView())}, p.name)),
    h('button', {class: 'chip plain', onclick: () => personaSheet(null, () => charactersView())}, '+ Persona')));
}

function noteList(items, {text = (x) => x.text, onsave, ondelete, onpin, meta}) {
  const box = h('div', {class: 'notes'});
  for (const it of items) {
    const note = h('div', {class: `note ${it.pinned ? 'pinned' : ''}`});
    const draw = () => {
      note.innerHTML = '';
      add(note, h('div', {class: 'grow'}, meta ? h('div', {class: 'meta'}, meta(it)) : null, h('div', {class: 'text'}, text(it))),
        onpin ? ibtn('pin', () => onpin(it), {class: `icon ${it.pinned ? 'on' : ''}`}) : null,
        onsave ? ibtn('edit', () => {
          const t = h('textarea', {value: text(it)});
          note.innerHTML = '';
          note.append(h('div', {class: 'grow'}, t, h('div', {class: 'row', style: 'justify-content:flex-end;margin-top:6px'},
            h('button', {class: 'btn small', onclick: draw}, 'Cancel'),
            h('button', {class: 'btn small primary', onclick: async () => { await onsave(it, t.value); it.text = t.value; draw(); }}, 'Save'))));
          t.focus();
        }) : null,
        ibtn('trash', async () => { await ondelete(it); note.remove(); }));
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

async function characterView(id) {
  const c = await GET(`/api/characters/${id}`);
  const main = frame('characters');
  const reload = () => characterView(id);
  const save = debounce((patch) => PATCH(`/api/characters/${id}`, patch));
  const file = h('input', {type: 'file', accept: 'image/*', class: 'hidden', onchange: async () => {
    const fd = new FormData();
    fd.append('file', file.files[0]);
    await fetch(`/api/characters/${id}/avatar`, {method: 'POST', body: fd});
    reload();
  }});
  const name = h('input', {class: 'title-input', value: c.name, oninput: () => save({name: name.value})});
  main.append(h('div', {class: 'row'}, ibtn('back', () => history.length > 1 ? history.back() : (location.hash = '#/characters'))),
    h('div', {class: 'row', style: 'gap:16px;margin:6px 0 10px'}, h('button', {class: 'icon', style: 'width:auto;height:auto', onclick: () => file.click()}, avatar(c, 'xl')),
      h('div', {class: 'grow'}, name)), file);

  const ta = (key, label, rows, cls = '') => field(label, h('textarea', {class: cls, rows, value: c[key] || '', oninput: (e) => save({[key]: e.target.value})}));
  const words = h('input', {placeholder: 'A few words'});
  const draftBtn = h('button', {class: 'btn', onclick: async () => {
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
  const tied = h('select', {onchange: () => PATCH(`/api/characters/${id}`, {persona_id: tied.value ? +tied.value : null})},
    h('option', {value: ''}, '—'), personas.map((p) => h('option', {value: p.id}, p.name)));
  tied.value = c.persona_id || '';
  main.append(
    h('div', {class: 'row draft-row'}, words, draftBtn),
    field('Pronouns', h('input', {value: c.pronouns || '', oninput: (e) => save({pronouns: e.target.value})})),
    ta('appearance', 'Appearance', 3, 'prose'),
    ta('personality', 'Who they are', 8, 'prose'),
    ta('inner_life', 'Inner life', 4, 'prose'),
    ta('key_memories', 'Always remembers', 3),
    ta('voice', 'How they talk', 3, 'prose'),
    ta('directive', 'Always', 2),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Speaks as'), h('div', {style: 'margin-top:6px'},
      seg([['', 'Story’s'], ['first', 'I'], ['third', 'She / he / they']], c.person || '', (v) => PATCH(`/api/characters/${id}`, {person: v || null})))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Style'), h('div', {style: 'margin-top:6px'},
      seg([['', 'Story’s'], ...STYLES], c.style || '', (v) => PATCH(`/api/characters/${id}`, {style: v || null})))),
    personas.length ? field('Usually with', tied) : null,
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Model'), h('div', {style: 'margin-top:6px'},
      modelButton(c.model ? c.model.split('/').slice(1).join('/') : '', "Story's model", (v) => PATCH(`/api/characters/${id}`, {model: v || null}),
        {allowDefault: true, defaultLabel: "Story's model"}))));

  // Portraits: made from the appearance, kept in one library.
  let style = 'painted';
  const gen = h('button', {class: 'btn primary', onclick: async () => {
    gen.disabled = true; gen.textContent = 'Painting…';
    try { await POST(`/api/characters/${id}/portraits`, {style}); reload(); }
    catch (e) { toast(ERR[e.data?.error] || 'No portrait'); gen.disabled = false; gen.textContent = 'Generate'; }
  }}, 'Generate');
  const lib = h('div', {class: 'portraits'});
  main.append(h('h2', {}, 'Portrait'), h('div', {class: 'row wrap'},
    seg([['photo', 'Photoreal'], ['painted', 'Painted'], ['anime', 'Anime']], style, (v) => { style = v; }), gen,
    h('button', {class: 'btn quiet', onclick: () => file.click()}, 'Upload')), lib);
  GET('/api/portraits').then((all) => {
    all.sort((a, b) => (b.character_id === id) - (a.character_id === id));
    for (const p of all) lib.append(h('button', {class: `thumb ${p.file === c.avatar ? 'on' : ''}`, title: p.name || '', onclick: () => menu([
      ['Use', async () => { await POST(`/api/characters/${id}/portrait`, {portrait_id: p.id}); reload(); }],
      p.prompt ? ['Copy description', () => navigator.clipboard?.writeText(p.prompt).then(() => toast('Copied'))] : null,
      ['Delete', async () => { await DEL(`/api/portraits/${p.id}`); reload(); }, 'danger'],
    ])}, h('img', {src: `/avatars/${p.file}`, alt: '', loading: 'lazy'})));
  });

  main.append(h('h2', {}, 'Corrections'),
    noteList(c.corrections, {onsave: (it, t) => PATCH(`/api/corrections/${it.id}`, {text: t}), ondelete: (it) => DEL(`/api/corrections/${it.id}`)}),
    adder('Correction', async (t) => { await POST(`/api/characters/${id}/corrections`, {text: t}); reload(); }));

  if (c.examples.length) main.append(h('h2', {}, 'Sounded right'), noteList(c.examples, {ondelete: (it) => DEL(`/api/examples/${it.id}`)}));

  main.append(h('h2', {}, 'Journal'), journalEditor(c.journal, {character_id: id}, reload));

  const people = {};
  for (const s of c.stories) {
    main.append(h('h2', {}, h('a', {href: `#/story/${s.id}`}, s.title)));
    const latest = s.feelings[0];
    main.append(h('h3', {}, 'Feelings'), feelingCard(c, latest, c.names, people));
    if (s.feelings.length > 1) {
      const arc = h('div', {class: 'arc hidden'}, s.feelings.slice(1).map((f) => h('div', {},
        h('div', {class: 'when'}, f.created_at.slice(0, 16).replace('T', ' ')), h('div', {class: 'mood', style: 'margin:2px 0'}, f.mood),
        Object.entries(f.toward || {}).map(([k, how]) => h('div', {class: 'small'}, h('b', {}, c.names[k] || k), ' ', how)))));
      main.append(h('button', {class: 'btn quiet small', style: 'margin-top:6px', onclick: () => arc.classList.toggle('hidden')}, 'Earlier'), arc);
    }
    const learned = h('textarea', {rows: 8, value: s.learned, oninput: debounce(() => PUT(`/api/learned/${s.id}/${id}`, {text: learned.value}))});
    main.append(h('h3', {}, 'Come to know'), learned);
    main.append(h('h3', {}, 'Memories'),
      noteList(s.memories, {meta: (m) => m.scene_title || '', onpin: async (m) => { await PATCH(`/api/memories/${m.id}`, {pinned: m.pinned ? 0 : 1}); reload(); },
        onsave: (m, t) => PATCH(`/api/memories/${m.id}`, {text: t}), ondelete: (m) => DEL(`/api/memories/${m.id}`)}),
      adder('Memory', async (t) => { await POST('/api/memories', {character_id: id, story_id: s.id, text: t}); reload(); }));
  }

  main.append(h('h2', {}, ''), h('button', {class: 'btn danger', onclick: async () => {
    if (await ask(`Delete ${c.name}?`)) { await DEL(`/api/characters/${id}`); location.hash = '#/characters'; }
  }}, 'Delete character'));
}

// --- Ideas ------------------------------------------------------------------------------------

async function ideasView() {
  const list = await GET('/api/ideas');
  const main = frame('ideas');
  main.append(h('div', {class: 'head'}, h('h1', {}, 'Ideas')));
  if (!list.length) return main.append(h('div', {class: 'empty muted'}, '—'));
  main.append(h('div', {class: 'list'}, list.map((it) => {
    const idea = h('textarea', {value: it.idea || '', placeholder: 'Idea', rows: 2, style: 'min-height:48px;margin-top:10px',
      oninput: debounce(() => POST(`/api/events/${it.id}/star`, {starred: true, idea: idea.value}))});
    const who = it.kind === 'you' ? (it.speaker || 'Narrator') : it.name;
    const card = h('div', {class: 'card'},
      h('div', {class: 'row'}, it.kind === 'character' ? avatar(it, 'sm') : null, h('div', {class: 'grow'}, h('b', {}, who),
        h('div', {class: 'small muted'}, h('a', {href: `#/scene/${it.scene_id}`}, `${it.story_title} · ${it.scene_title || 'Untitled'}`))),
        ibtn('star', async () => { await POST(`/api/events/${it.id}/star`, {starred: false}); card.remove(); }, {class: 'icon on'})),
      h('div', {class: 'prose-text', style: 'margin-top:8px', html: prose(it.content)}), idea);
    return card;
  })));
}

// --- Settings ---------------------------------------------------------------------------------

async function settingsView() {
  const s = await getSettings(true);
  const main = frame('settings');
  const reload = () => settingsView();
  main.append(h('div', {class: 'head'}, h('h1', {}, 'Settings')));

  main.append(h('h2', {}, 'Models'));
  const conns = h('div', {class: 'list'});
  for (const c of s.connections.filter((c) => c.preset !== 'chatgpt')) {
    conns.append(h('div', {class: 'item', style: 'cursor:default'},
      h('div', {class: 'grow'}, h('div', {class: 't'}, c.name), h('div', {class: 's'}, [s.presets[c.preset]?.name, c.key_tail ? `•••• ${c.key_tail}` : null, c.preset === 'ollama' || c.preset === 'custom' ? c.base_url : null].filter(Boolean).join(' · '))),
      ibtn('edit', () => connectionSheet(s, c, reload)),
      ibtn('trash', async () => { if (await ask(`Remove ${c.name}?`, 'Remove')) { await DEL(`/api/connections/${c.id}`); reload(); } })));
  }
  conns.append(h('div', {}, h('button', {class: 'btn', onclick: () => connectionSheet(s, null, reload)}, icon('plus'), 'Add')));
  main.append(conns);

  main.append(h('h3', {}, 'ChatGPT'));
  if (s.chatgpt) {
    main.append(h('div', {class: 'item', style: 'cursor:default'}, h('div', {class: 'grow'}, h('div', {class: 't'}, 'ChatGPT'), h('div', {class: 's'}, s.chatgpt.email || s.chatgpt.name)),
      h('button', {class: 'btn small', onclick: async () => { if (await ask('Disconnect ChatGPT?', 'Disconnect')) { await POST('/api/chatgpt/disconnect'); reload(); } }}, 'Disconnect')));
  } else {
    const paste = h('input', {placeholder: 'Address from the ChatGPT tab'});
    const err = h('div', {class: 'err'});
    const finish = h('div', {class: 'hidden', style: 'margin-top:10px'}, h('div', {class: 'row'}, paste,
      h('button', {class: 'btn primary', onclick: async () => {
        try { await POST('/api/chatgpt/finish', {url: paste.value}); toast('Connected'); reload(); }
        catch (e) { err.textContent = e.data?.error === 'state' || e.data?.error === 'start' ? 'Start again' : e.data?.error === 'scope' ? 'Plan usage not granted' : 'Not connected'; }
      }}, 'Connect')), err);
    main.append(h('div', {class: 'card'}, h('button', {class: 'btn', onclick: async () => {
      const {url} = await POST('/api/chatgpt/start');
      window.open(url, '_blank', 'noopener');
      finish.classList.remove('hidden');
      paste.focus();
    }}, 'Continue with ChatGPT'), finish));
    const q = query();
    if (q.chatgpt) err.textContent = 'Not connected';
  }

  main.append(h('h3', {}, 'Default'));
  main.append(h('div', {class: 'row wrap'},
    field('Characters', modelButton(s.labels.default_model, 'Pick', async (v) => { await PUT('/api/settings', {default_model: v}); })),
    field('Memory and turn order', modelButton(s.labels.helper_model, 'Same as characters', async (v) => { await PUT('/api/settings', {helper_model: v}); }, {allowDefault: true, defaultLabel: 'Same as characters'})),
    field('Portraits', modelButton(s.labels.portrait_model, 'Pick', async (v) => { await PUT('/api/settings', {portrait_model: v}); }))));

  const set = (k) => (v) => PUT('/api/settings', {[k]: v});
  main.append(h('h2', {}, 'Memory'),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Short-term'), h('div', {style: 'margin-top:6px'},
      seg([['20000', 'Small'], ['60000', 'Medium'], ['150000', 'Large'], ['400000', 'Huge']], s.settings.short_term, set('short_term')))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Memories recalled per reply'), h('div', {style: 'margin-top:6px'},
      seg([['3', '3'], ['6', '6'], ['9', '9'], ['15', '15']], s.settings.recall, set('recall')))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Feelings'), h('div', {style: 'margin-top:6px'},
      seg([['1', 'Track'], ['0', 'Off']], s.settings.feelings, set('feelings')))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Replies per round'), h('div', {style: 'margin-top:6px'},
      seg([['1', '1'], ['2', '2'], ['3', '3'], ['5', '5']], s.settings.round, set('round')))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Repetition guard'), h('div', {style: 'margin-top:6px'},
      seg([['1', 'On'], ['0', 'Off']], s.settings.repetition, set('repetition')))));

  const local = (k, fallback) => { try { return localStorage.getItem(k) || fallback; } catch (e) { return fallback; } };
  const keep = (k) => (v) => { try { localStorage.setItem(k, v); } catch (e) {} applyLook(); };
  main.append(h('h2', {}, 'Reading'),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Text size'), h('div', {style: 'margin-top:6px'},
      seg([['0.9', 14], ['1', 16], ['1.12', 19], ['1.25', 22]].map(([v, px]) => [v, h('span', {style: `font:600 ${px}px var(--prose)`}, 'A')]), local('bamah.size', '1'), keep('bamah.size')))),
    h('div', {class: 'field'}, h('span', {class: 'muted small'}, 'Theme'), h('div', {style: 'margin-top:6px'},
      seg([['auto', 'Auto'], ['light', 'Light'], ['dark', 'Dark']], local('bamah.theme', 'auto'), keep('bamah.theme')))));

  main.append(h('h2', {}, 'Shared journal'));
  const gj = await GET('/api/journal');
  main.append(journalEditor(gj, {}, reload));

  main.append(h('h2', {}, 'Data'), h('div', {class: 'row wrap'},
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

route();
