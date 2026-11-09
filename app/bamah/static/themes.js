/* Bamah's looks. A theme is a handful of colours in a dark and a light version, and every colour token
   app.css uses is made from them here, so a theme reads the same everywhere and the text keeps its
   contrast. The fun ones are rooms as well: the frame (the side list, and the bars on a phone) is made
   of something, there's a faint texture behind the cards, and headings get their own typeface. What she
   reads stays plain. app.css draws the rooms under html[data-room].

   Kept per device in localStorage: bamah.look (which theme) and bamah.mode (dark, light or auto, which
   follows the device). Loaded in the page's head, so the colours are on before anything shows. */
(() => {
// bg: the page; rail: the side list; card: cards and lines; ink: text; accent: links and what's chosen;
// fill: buttons (the accent if not given); inner: the hue of what they keep to themselves; good, warn.
// A room's also has frame: what the side list and the bars are made of, with frameInk its text and
// frameAccent its own accent.
const FAMILIES = [
  { id: 'bamah', name: 'Bamah',
    dark: { bg: '#120e0f', rail: '#171213', card: '#1d1718', ink: '#f2eae7', accent: '#e8907f', fill: '#b4513f', inner: '#cdb0d6' },
    light: { bg: '#f7f2ec', rail: '#efe8df', card: '#fffdfa', ink: '#2b2220', accent: '#a2432f', inner: '#8a6aa8' } },
  // the rooms
  { id: 'theatre', name: 'Velvet theatre', room: 'theatre',
    dark: { bg: '#170b0e', card: '#24141a', ink: '#f3e6dc', accent: '#e3b85c', fill: '#a3192d', inner: '#d9a8c4', frame: '#6a0e1c', frameInk: '#f6e3c6', frameAccent: '#f0c66b' },
    light: { bg: '#f6efe4', card: '#fffaf2', ink: '#2a1a17', accent: '#8e1a26', inner: '#8a5a8f', frame: '#7a1220', frameInk: '#f8e6c8', frameAccent: '#f0c66b' } },
  { id: 'candle', name: 'Candlelit', room: 'candle',
    dark: { bg: '#130d07', card: '#1f160d', ink: '#f2e3c8', accent: '#f0a848', fill: '#b06a1c', inner: '#d9a8a0', frame: '#0c0804', frameInk: '#eedcbc', frameAccent: '#f3b257' },
    light: { bg: '#f8efdc', card: '#fffaf0', ink: '#33240f', accent: '#97520f', inner: '#8f5a6a', frame: '#3b2814', frameInk: '#f6e5c4', frameAccent: '#f3b257' } },
  { id: 'noir', name: 'Film noir', room: 'noir',
    dark: { bg: '#0c0c0d', card: '#171719', ink: '#ececec', accent: '#d4d4d4', fill: '#b3141f', inner: '#a9a9bd', good: '#a8c7a8', warn: '#f08080', frame: '#050505', frameInk: '#e6e6e6', frameAccent: '#e23a3a' },
    light: { bg: '#e8e6e0', card: '#f6f5f1', ink: '#141414', accent: '#8c1018', fill: '#141414', inner: '#55556e', frame: '#1a1a1a', frameInk: '#efefef', frameAccent: '#ff5a5a' } },
  { id: 'manuscript', name: 'Manuscript', room: 'manuscript',
    light: { bg: '#f1e5c8', card: '#f8eed6', ink: '#3b2a17', accent: '#a1281a', inner: '#2f5d9a', frame: '#5b3a1f', frameInk: '#f3e2bf', frameAccent: '#e0b25a' },
    dark: { bg: '#1f170f', card: '#2a2016', ink: '#ecdcbc', accent: '#e07a5a', fill: '#a63a22', inner: '#8fa9d6', frame: '#120c07', frameInk: '#ead6b0', frameAccent: '#d9a34e' } },
  { id: 'storybook', name: 'Storybook', room: 'storybook',
    light: { bg: '#fbf6ee', card: '#ffffff', ink: '#3a3350', accent: '#b84870', inner: '#7d62b8', frame: '#4b5d9c', frameInk: '#fffaf0', frameAccent: '#ffd36b' },
    dark: { bg: '#1c1b2e', card: '#262540', ink: '#ece8f7', accent: '#f2a7c3', fill: '#c25985', inner: '#b8a5ee', frame: '#14132a', frameInk: '#e9e6fb', frameAccent: '#ffd36b' } },
  { id: 'garden', name: 'Garden', room: 'garden',
    light: { bg: '#f1f1e4', card: '#fbfbf4', ink: '#26321f', accent: '#a64d2a', inner: '#7a5f9e', frame: '#3e5a34', frameInk: '#eef3e0', frameAccent: '#f2c46b' },
    dark: { bg: '#111913', card: '#1a241c', ink: '#e3ecd9', accent: '#e59a6f', fill: '#b45a33', inner: '#b9a3d8', frame: '#0a110b', frameInk: '#dfe9d3', frameAccent: '#e8c46e' } },
  { id: 'console', name: 'Starship', room: 'console',
    dark: { bg: '#070c16', card: '#0d1626', ink: '#d8e6ff', accent: '#3fe0f0', fill: '#19b8c9', inner: '#b48cff', good: '#5ee0a0', warn: '#ff7a8a', frame: '#03060c', frameInk: '#cfe0ff', frameAccent: '#ffb340' },
    light: { bg: '#edf2f8', card: '#ffffff', ink: '#0f1a2b', accent: '#006f86', inner: '#6a4fc4', frame: '#0f1a2b', frameInk: '#dbe8ff', frameAccent: '#ffb340' } },
  { id: 'gothic', name: 'Gothic', room: 'gothic',
    dark: { bg: '#16141a', card: '#201d25', ink: '#ebe3d3', accent: '#d6b25e', fill: '#8a1b2a', inner: '#b39ad6', frame: '#3a0b14', frameInk: '#f2e3c4', frameAccent: '#e4bf64' },
    light: { bg: '#ece8e1', card: '#f9f6f0', ink: '#231b1d', accent: '#8a1b2a', inner: '#6a4f8e', frame: '#5a0f1e', frameInk: '#f5e6c8', frameAccent: '#e6c36c' } },
  // plain colours
  { id: 'paper', name: 'Paper',
    light: { bg: '#f7f0e3', rail: '#f0e7d6', ink: '#3a3127', accent: '#9a5b1f' },
    dark: { bg: '#1d1915', rail: '#241f19', ink: '#e8dcc6', accent: '#d39a5b' } },
  { id: 'pencil', name: 'Blue pencil',
    light: { bg: '#ffffff', rail: '#f4f7fa', ink: '#3a4450', accent: '#2e7bd6', inner: '#d0457b' },
    dark: { bg: '#17202b', rail: '#1c2733', ink: '#cfd8e2', accent: '#5aa5f0', inner: '#f07aa5' } },
  { id: 'nord', name: 'Nord',
    light: { bg: '#eceff4', rail: '#e5e9f0', ink: '#2e3440', accent: '#5e81ac', good: '#5f8a4a', warn: '#bf616a', inner: '#b48ead' },
    dark: { bg: '#2e3440', rail: '#3b4252', ink: '#e5e9f0', accent: '#88c0d0', good: '#a3be8c', warn: '#bf616a', inner: '#b48ead' } },
  { id: 'solarized', name: 'Solarized',
    light: { bg: '#fdf6e3', rail: '#eee8d5', ink: '#475b62', accent: '#268bd2', good: '#859900', warn: '#dc322f', inner: '#6c71c4' },
    dark: { bg: '#002b36', rail: '#073642', ink: '#a3b1b1', accent: '#268bd2', good: '#859900', warn: '#dc322f', inner: '#6c71c4' } },
  { id: 'gruvbox', name: 'Gruvbox',
    light: { bg: '#fbf1c7', rail: '#f2e5bc', ink: '#3c3836', accent: '#076678', good: '#79740e', warn: '#9d0006', inner: '#8f3f71' },
    dark: { bg: '#282828', rail: '#32302f', ink: '#ebdbb2', accent: '#83a598', good: '#b8bb26', warn: '#fb4934', inner: '#d3869b' } },
  { id: 'catppuccin', name: 'Catppuccin',
    light: { bg: '#eff1f5', rail: '#e6e9ef', ink: '#4c4f69', accent: '#1e66f5', good: '#40a02b', warn: '#d20f39', inner: '#8839ef' },
    dark: { bg: '#1e1e2e', rail: '#181825', ink: '#cdd6f4', accent: '#89b4fa', good: '#a6e3a1', warn: '#f38ba8', inner: '#cba6f7' } },
  { id: 'rose-pine', name: 'Rosé Pine',
    light: { bg: '#faf4ed', rail: '#f2e9e1', ink: '#575279', accent: '#286983', good: '#56949f', warn: '#b4637a', inner: '#907aa9' },
    dark: { bg: '#232136', rail: '#2a273f', ink: '#e0def4', accent: '#c4a7e7', good: '#9ccfd8', warn: '#eb6f92', inner: '#ea9a97' } },
  { id: 'tokyo', name: 'Tokyo Night',
    light: { bg: '#e1e2e7', rail: '#d5d6db', ink: '#343b58', accent: '#2e7de9', good: '#587539', warn: '#f52a65', inner: '#9854f1' },
    dark: { bg: '#1a1b26', rail: '#16161e', ink: '#c0caf5', accent: '#7aa2f7', good: '#9ece6a', warn: '#f7768e', inner: '#bb9af7' } },
  { id: 'dracula', name: 'Dracula',
    light: { bg: '#fffbeb', rail: '#f5f0d8', ink: '#1f1f1f', accent: '#644ac9', good: '#14710a', warn: '#cb3a2a', inner: '#a3144d' },
    dark: { bg: '#282a36', rail: '#21222c', ink: '#f8f8f2', accent: '#bd93f9', good: '#50fa7b', warn: '#ff5555', inner: '#ff79c6' } },
  { id: 'everforest', name: 'Everforest',
    light: { bg: '#fdf6e3', rail: '#f4f0d9', ink: '#4d5a61', accent: '#3a94c5', good: '#8da101', warn: '#f85552', inner: '#df69ba' },
    dark: { bg: '#2d353b', rail: '#343f44', ink: '#d3c6aa', accent: '#a7c080', good: '#a7c080', warn: '#e67e80', inner: '#d699b6' } },
  { id: 'eink', name: 'E-ink',
    light: { bg: '#f4f1ea', rail: '#ebe7de', ink: '#1a1a1a', accent: '#2f2f2f', inner: '#5a5a6e' },
    dark: { bg: '#121212', rail: '#1a1a1a', ink: '#e8e4da', accent: '#c9c9c9', inner: '#a8a8bb' } },
  { id: 'contrast', name: 'High contrast',
    light: { bg: '#ffffff', rail: '#f3f3f3', card: '#ffffff', ink: '#000000', accent: '#0040c0', good: '#006b2d', warn: '#b00020', inner: '#5b2a86' },
    dark: { bg: '#000000', rail: '#0c0c0c', card: '#0c0c0c', ink: '#ffffff', accent: '#7ab8ff', good: '#5ee08a', warn: '#ff7a7a', inner: '#d4b0ff' } },
  { id: 'black', name: 'Black',
    dark: { bg: '#000000', rail: '#0b0b0c', card: '#111112', ink: '#ece7e4', accent: '#e8907f', fill: '#b4513f', inner: '#cdb0d6' },
    light: { bg: '#ffffff', rail: '#f6f5f4', card: '#ffffff', ink: '#1f1a19', accent: '#a2432f', inner: '#8a6aa8' } },
];

/* ---------- colour arithmetic ---------- */
const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
const hex = (c) => '#' + c.map((v) => Math.round(Math.min(1, Math.max(0, v)) * 255).toString(16).padStart(2, '0')).join('');
const mix = (a, b, t) => hex(rgb(a).map((v, i) => v + (rgb(b)[i] - v) * t));
const lum = (h) => { const [r, g, b] = rgb(h).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const contrast = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
const rgba = (h, a) => `rgba(${rgb(h).map((v) => Math.round(v * 255)).join(', ')}, ${a})`;
// c, moved toward white or black (away from the grounds) until it reads on every one of them
const readable = (c, grounds, min) => {
  const toward = lum(grounds[0]) < 0.3 ? '#ffffff' : '#000000';
  for (let t = 0; t <= 1.001; t += 0.04) {
    const x = mix(c, toward, t);
    if (grounds.every((g) => contrast(x, g) >= min)) return x;
  }
  return toward;
};
const onFill = (f) => (contrast(f, '#ffffff') >= contrast(f, '#141414') ? '#ffffff' : '#141414');

// Every token app.css uses, from a palette's few colours.
function vars(p, dark) {
  const bg = p.bg, ink = p.ink;
  const card = p.card || (dark ? mix(bg, ink, 0.055) : mix(bg, '#ffffff', 0.62));
  const rail = p.rail || (dark ? mix(bg, ink, 0.03) : mix(bg, ink, 0.035));
  const innerHue = p.inner || (dark ? '#cdb0d6' : '#8a6aa8');
  const inner = mix(bg, innerHue, dark ? 0.1 : 0.11);
  let fill = p.fill || p.accent;
  const fillInk = onFill(fill);
  fill = readable(fill, [fillInk], 4.5);
  const v = {
    '--bg': bg, '--rail': rail, '--panel': mix(bg, rail, 0.5), '--card': card,
    '--raise': dark ? mix(card, ink, 0.025) : mix(card, '#ffffff', 0.6), '--sunk': dark ? mix(bg, '#000000', 0.15) : mix(bg, ink, 0.045),
    '--hover': mix(bg, ink, dark ? 0.075 : 0.06), '--sel': mix(bg, ink, dark ? 0.11 : 0.1),
    '--line': mix(bg, ink, dark ? 0.1 : 0.1), '--line-2': mix(bg, ink, dark ? 0.16 : 0.16),
    '--ink': ink, '--ink-2': mix(ink, bg, 0.06),
    '--muted': readable(mix(ink, bg, 0.3), [bg, card], 4.5), '--faint': readable(mix(ink, bg, 0.48), [bg], 3.2),
    '--act': readable(mix(ink, bg, 0.3), [bg], 4.5),
    '--accent': readable(p.accent, [bg, card], 4.5), '--accent-fill': fill, '--accent-ink': fillInk,
    '--accent-soft': mix(bg, p.accent, dark ? 0.15 : 0.1),
    '--you': mix(bg, p.accent, dark ? 0.13 : 0.08), '--inner': inner,
    '--inner-ink': readable(mix(innerHue, ink, dark ? 0.3 : 0.4), [inner], 4.5),
    '--good': readable(p.good || (dark ? '#8cc196' : '#3f6b45'), [bg, card], 3.2),
    '--warn': readable(p.warn || (dark ? '#ef8f78' : '#a4442f'), [bg, card], 3.2),
    '--veil': dark ? 'rgba(0, 0, 0, .62)' : rgba(mix(ink, bg, 0.2), 0.32),
    '--shadow': dark ? '0 12px 40px rgba(0, 0, 0, .45)' : `0 12px 40px ${rgba(mix(ink, bg, 0.2), 0.16)}`,
    'color-scheme': dark ? 'dark' : 'light',
  };
  // A room's frame: the side list and the bars, with their own text, lines and accent (app.css swaps
  // these in as the ordinary tokens inside the frame).
  if (p.frame) {
    const f = p.frame, fi = p.frameInk;
    let fa = readable(p.frameAccent, [f], 4.5);
    if (contrast(fa, onFill(fa)) < 4.5) fa = readable(fa, [f, onFill(fa)], 4.5);   // it's a button's colour too
    Object.assign(v, {
      '--frame': f, '--frame-ink': fi, '--frame-muted': readable(mix(fi, f, 0.3), [f], 4.5), '--frame-faint': readable(mix(fi, f, 0.45), [f], 3.2),
      '--frame-line': mix(f, fi, 0.16), '--frame-line-2': mix(f, fi, 0.26), '--frame-hover': mix(f, fi, 0.09), '--frame-sel': mix(f, fi, 0.16),
      '--frame-raise': mix(f, fi, 0.07), '--frame-sunk': mix(f, '#000000', 0.25),
      '--frame-accent': fa, '--frame-accent-ink': onFill(fa), '--frame-accent-soft': mix(f, fa, 0.2),
    });
  }
  return v;
}

const FRAME_KEYS = ['--frame', '--frame-ink', '--frame-muted', '--frame-faint', '--frame-line', '--frame-line-2', '--frame-hover', '--frame-sel',
  '--frame-raise', '--frame-sunk', '--frame-accent', '--frame-accent-ink', '--frame-accent-soft'];
const media = matchMedia('(prefers-color-scheme: dark)');
const store = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} return null; };
const byId = (id) => FAMILIES.find((f) => f.id === id) || FAMILIES[0];

function get() {
  let look = store('bamah.look'), mode = store('bamah.mode');
  if (!mode) {                                   // the old three-way switch: dark, light, auto
    const old = store('bamah.theme');
    mode = ['dark', 'light', 'auto'].includes(old) ? old : 'dark';
  }
  return { look: byId(look).id, mode };
}
const isDark = (mode) => mode === 'dark' || (mode === 'auto' && media.matches);

function apply(a) {
  a = a || get();
  const fam = byId(a.look), dark = isDark(a.mode), r = document.documentElement;
  const v = vars(dark ? fam.dark : fam.light, dark);
  for (const k of FRAME_KEYS) if (!(k in v)) r.style.removeProperty(k);
  for (const [k, val] of Object.entries(v)) r.style.setProperty(k, val);
  r.dataset.mode = dark ? 'dark' : 'light';
  r.dataset.look = fam.id;
  if (fam.room) r.dataset.room = fam.room; else delete r.dataset.room;
  let m = document.querySelector('meta[name="theme-color"]');
  if (!m) { m = document.createElement('meta'); m.name = 'theme-color'; document.head.appendChild(m); }
  m.content = v['--frame'] || v['--bg'];
}

function set(patch) {
  const a = Object.assign(get(), patch);
  store('bamah.look', a.look);
  store('bamah.mode', a.mode);
  apply(a);
}

media.addEventListener('change', () => { if (get().mode === 'auto') apply(); });
window.BamahThemes = { FAMILIES, vars, get, set, apply, isDark, contrast };
apply();
})();
