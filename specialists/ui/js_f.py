from tb import jsfix

jsfix("ui-fix-debounce-clear", "easy", "timing",
      "Rapid calls should be collapsed into one call, but `fn` runs once per call.", "debounce.js",
      """function debounce(fn, wait) {
  let t = null;
  return function (...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), wait);
  };
}
module.exports = { debounce };""",
      [("    clearTimeout(t);\n", "")],
      """const { debounce } = require('./debounce.js');
test('burst -> one call, last args', () => { const c = clock(); const o = []; const d = debounce((x) => o.push(x), 50); d(1); c.tick(20); d(2); c.tick(20); d(3); c.tick(50); assert.deepEqual(o, [3]); c.restore(); });
test('single', () => { const c = clock(); let n = 0; const d = debounce(() => n++, 50); d(); c.tick(49); assert.equal(n, 0); c.tick(1); assert.equal(n, 1); c.restore(); });""")

jsfix("ui-fix-tab-wrap", "easy", "keyboard",
      "Pressing Left on the first tab produces index -1 instead of wrapping to the last tab.", "tabnav.js",
      """function nextTab(i, n, dir) {
  return (((i + dir) % n) + n) % n;
}
function firstEnabled(disabled, n) {
  for (let i = 0; i < n; i++) if (!disabled.includes(i)) return i;
  return -1;
}
module.exports = { nextTab, firstEnabled };""",
      [("(((i + dir) % n) + n) % n", "(i + dir) % n")],
      """const { nextTab, firstEnabled } = require('./tabnav.js');
test('right wraps', () => assert.equal(nextTab(2, 3, 1), 0));
test('left wraps', () => assert.equal(nextTab(0, 3, -1), 2));
test('middle', () => { assert.equal(nextTab(1, 3, 1), 2); assert.equal(nextTab(1, 3, -1), 0); });
test('firstEnabled', () => { assert.equal(firstEnabled([0, 1], 4), 2); assert.equal(firstEnabled([0], 1), -1); });""")

jsfix("ui-fix-sort-numbers", "easy", "tables",
      "Sorting [10, 9, 100, 1] gives [1, 10, 100, 9], and the original array gets reordered too.", "sortnums.js",
      """function sortNumbers(values, dir = 'asc') {
  const out = values.slice().sort((a, b) => a - b);
  return dir === 'desc' ? out.reverse() : out;
}
module.exports = { sortNumbers };""",
      [("values.slice().sort((a, b) => a - b)", "values.sort()")],
      """const { sortNumbers: s } = require('./sortnums.js');
test('numeric order', () => assert.deepEqual(s([10, 9, 100, 1]), [1, 9, 10, 100]));
test('desc', () => assert.deepEqual(s([10, 9, 100, 1], 'desc'), [100, 10, 9, 1]));
test('does not mutate', () => { const a = [3, 1, 2]; s(a); assert.deepEqual(a, [3, 1, 2]); });
test('negatives', () => assert.deepEqual(s([-5, 3, -10, 0]), [-10, -5, 0, 3]));""")

jsfix("ui-fix-pagination-count", "medium", "tables",
      "A list of 21 items with page size 10 reports 2 pages, and the last page shows the wrong slice.", "pager.js",
      """function pageCount(total, size) {
  return Math.max(1, Math.ceil(total / size));
}
function pageSlice(items, page, size) {
  const start = (page - 1) * size;
  return items.slice(start, start + size);
}
module.exports = { pageCount, pageSlice };""",
      [("Math.max(1, Math.ceil(total / size))", "Math.floor(total / size)"), ("(page - 1) * size", "page * size")],
      """const { pageCount, pageSlice } = require('./pager.js');
const a = Array.from({ length: 21 }, (_, i) => i + 1);
test('count', () => { assert.equal(pageCount(21, 10), 3); assert.equal(pageCount(20, 10), 2); assert.equal(pageCount(0, 10), 1); assert.equal(pageCount(5, 10), 1); });
test('slice first', () => assert.deepEqual(pageSlice(a, 1, 10), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]));
test('slice last', () => assert.deepEqual(pageSlice(a, 3, 10), [21]));""")

jsfix("ui-fix-date-month", "easy", "dates",
      "formatted dates show the wrong month (off by one) and single-digit days are not zero padded.", "fmt.js",
      """function isoDate(d) {
  const p = (n) => String(n).padStart(2, '0');
  return d.getUTCFullYear() + '-' + p(d.getUTCMonth() + 1) + '-' + p(d.getUTCDate());
}
function monthName(d) {
  return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getUTCMonth()];
}
module.exports = { isoDate, monthName };""",
      [("p(d.getUTCMonth() + 1) + '-' + p(d.getUTCDate())", "d.getUTCMonth() + '-' + d.getUTCDate()")],
      """const { isoDate, monthName } = require('./fmt.js');
test('iso', () => { assert.equal(isoDate(new Date(Date.UTC(2024, 0, 5))), '2024-01-05'); assert.equal(isoDate(new Date(Date.UTC(2024, 11, 25))), '2024-12-25'); });
test('name', () => assert.equal(monthName(new Date(Date.UTC(2024, 2, 1))), 'Mar'));""")

jsfix("ui-fix-closure-loop", "easy", "events",
      "Every button handler reports the same index (the number of buttons) instead of its own.", "handlers.js",
      """function makeHandlers(n, log) {
  const hs = [];
  for (let i = 0; i < n; i++) {
    hs.push(() => log.push(i));
  }
  return hs;
}
module.exports = { makeHandlers };""",
      [("for (let i = 0", "for (var i = 0")],
      """const { makeHandlers } = require('./handlers.js');
test('each handler logs its own index', () => { const log = []; const hs = makeHandlers(3, log); hs[0](); hs[2](); hs[1](); assert.deepEqual(log, [0, 2, 1]); });
test('zero', () => assert.deepEqual(makeHandlers(0, []), []));""")

jsfix("ui-fix-escape-order", "easy", "security",
      "Escaping '<b>' produces '&amp;lt;b&amp;gt;' (double-escaped) and quotes are not escaped.", "esc.js",
      """function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
module.exports = { escapeHtml };""",
      [("    .replace(/&/g, '&amp;')\n    .replace(/</g, '&lt;')\n    .replace(/>/g, '&gt;')\n    .replace(/\"/g, '&quot;')\n    .replace(/'/g, '&#39;');",
        "    .replace(/</g, '&lt;')\n    .replace(/>/g, '&gt;')\n    .replace(/&/g, '&amp;');")],
      """const { escapeHtml: e } = require('./esc.js');
test('tags', () => assert.equal(e('<b>'), '&lt;b&gt;'));
test('amp', () => assert.equal(e('a & b'), 'a &amp; b'));
test('quotes', () => assert.equal(e(`"x" 'y'`), '&quot;x&quot; &#39;y&#39;'));
test('combined', () => assert.equal(e('<a href="x">&</a>'), '&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;'));""")

jsfix("ui-fix-emitter-once", "medium", "events",
      "With a `once` handler registered first, the next handler is skipped during emit.", "emitter.js",
      """function createEmitter() {
  const handlers = {};
  return {
    on(e, fn) { (handlers[e] = handlers[e] || []).push(fn); return () => this.off(e, fn); },
    once(e, fn) { const w = (...a) => { this.off(e, w); fn(...a); }; return this.on(e, w); },
    off(e, fn) { const l = handlers[e] || []; const i = l.indexOf(fn); if (i >= 0) l.splice(i, 1); },
    emit(e, ...a) { (handlers[e] || []).slice().forEach((f) => f(...a)); },
  };
}
module.exports = { createEmitter };""",
      [("(handlers[e] || []).slice().forEach", "(handlers[e] || []).forEach")],
      """const { createEmitter } = require('./emitter.js');
test('once does not skip next', () => { const e = createEmitter(); const o = []; e.once('x', () => o.push('a')); e.on('x', () => o.push('b')); e.on('x', () => o.push('c')); e.emit('x'); assert.deepEqual(o, ['a', 'b', 'c']); e.emit('x'); assert.deepEqual(o, ['a', 'b', 'c', 'b', 'c']); });
test('plain on/off', () => { const e = createEmitter(); let n = 0; const off = e.on('y', () => n++); e.emit('y'); off(); e.emit('y'); assert.equal(n, 1); });""")

jsfix("ui-fix-store-unsubscribe", "medium", "state",
      "If a subscriber unsubscribes itself (or another) while listeners are being notified, some other subscribers are not called.", "mini.js",
      """function createStore(reducer, state) {
  let listeners = [];
  return {
    getState: () => state,
    dispatch(a) { state = reducer(state, a); listeners.slice().forEach((l) => l()); },
    subscribe(l) { listeners.push(l); return () => { listeners = listeners.filter((x) => x !== l); }; },
  };
}
module.exports = { createStore };""",
      [("listeners.slice().forEach((l) => l());", "const ls = listeners; for (let i = 0; i < ls.length; i++) ls[i]();"),
       ("listeners = listeners.filter((x) => x !== l);", "listeners.splice(listeners.indexOf(l), 1);")],
      """const { createStore } = require('./mini.js');
const r = (s, a) => (a.type === 'inc' ? s + 1 : s);
test('self unsubscribe does not skip neighbours', () => { const s = createStore(r, 0); const calls = []; const off = s.subscribe(() => { calls.push('a'); off(); }); s.subscribe(() => calls.push('b')); s.subscribe(() => calls.push('c')); s.dispatch({ type: 'inc' }); assert.deepEqual(calls, ['a', 'b', 'c']); s.dispatch({ type: 'inc' }); assert.deepEqual(calls, ['a', 'b', 'c', 'b', 'c']); });
test('double unsubscribe harmless', () => { const s = createStore(r, 0); const calls = []; s.subscribe(() => calls.push('x')); const off = s.subscribe(() => calls.push('y')); off(); off(); s.dispatch({ type: 'inc' }); assert.deepEqual(calls, ['x']); });""")

jsfix("ui-fix-global-regex", "medium", "regex",
      "`isSlug('abc')` returns true on the first call and false on the second.", "slugcheck.js",
      """const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
function isSlug(s) {
  return SLUG.test(s);
}
function countWords(s) {
  return (s.match(/\\w+/g) || []).length;
}
module.exports = { isSlug, countWords };""",
      [("/^[a-z0-9]+(?:-[a-z0-9]+)*$/;", "/^[a-z0-9]+(?:-[a-z0-9]+)*$/g;")],
      """const { isSlug, countWords } = require('./slugcheck.js');
test('repeatable', () => { for (let i = 0; i < 4; i++) assert.equal(isSlug('abc-def'), true, 'call ' + i); });
test('invalid', () => { assert.equal(isSlug('Abc'), false); assert.equal(isSlug('a--b'), false); assert.equal(isSlug('-a'), false); });
test('words', () => assert.equal(countWords('a bb ccc'), 3));""")

jsfix("ui-fix-search-regex-escape", "medium", "text",
      "Searching for 'c++' or '(' throws a SyntaxError; searching '.' matches every character.", "find.js",
      """function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
}
function countMatches(text, query) {
  if (!query) return 0;
  const m = text.match(new RegExp(escapeRegExp(query), 'gi'));
  return m ? m.length : 0;
}
module.exports = { countMatches, escapeRegExp };""",
      [("new RegExp(escapeRegExp(query), 'gi')", "new RegExp(query, 'gi')")],
      """const { countMatches: c } = require('./find.js');
test('plain', () => assert.equal(c('Foo foo FOO', 'foo'), 3));
test('plus', () => assert.equal(c('I like c++ and c++', 'c++'), 2));
test('paren', () => assert.equal(c('f(x) g(x)', '('), 2));
test('dot literal', () => assert.equal(c('a.b.c', '.'), 2));
test('empty', () => assert.equal(c('abc', ''), 0));
test('no match', () => assert.equal(c('abc', 'z'), 0));""")

jsfix("ui-fix-currency-sign", "medium", "formatting",
      "Negative amounts render as '$-5.00' (should be '-$5.00') and -0.001 renders as '-$0.00'.", "cur.js",
      """function fmt(n) {
  const r = Math.round(Math.abs(n) * 100) / 100;
  const neg = n < 0 && r !== 0;
  const [i, f] = r.toFixed(2).split('.');
  return (neg ? '-' : '') + '$' + i.replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',') + '.' + f;
}
module.exports = { fmt };""",
      [("""  const r = Math.round(Math.abs(n) * 100) / 100;
  const neg = n < 0 && r !== 0;
  const [i, f] = r.toFixed(2).split('.');
  return (neg ? '-' : '') + '$' + i""", """  const [i, f] = n.toFixed(2).split('.');
  return '$' + i""")],
      """const { fmt } = require('./cur.js');
test('basic', () => { assert.equal(fmt(5), '$5.00'); assert.equal(fmt(1234567.891), '$1,234,567.89'); });
test('negative', () => { assert.equal(fmt(-5), '-$5.00'); assert.equal(fmt(-1234.5), '-$1,234.50'); });
test('negative zero', () => { assert.equal(fmt(-0.001), '$0.00'); assert.equal(fmt(0), '$0.00'); });""")

jsfix("ui-fix-search-race", "hard", "async",
      "When the user types quickly, a slow response for an OLD query arrives after the newer one and overwrites the displayed results (stale result wins).", "search.js",
      """function createSearch(fetcher, onResult) {
  let latest = 0;
  return async function search(q) {
    const id = ++latest;
    const res = await fetcher(q);
    if (id !== latest) return false;
    onResult(q, res);
    return true;
  };
}
module.exports = { createSearch };""",
      [("    if (id !== latest) return false;\n", "")],
      """const { createSearch } = require('./search.js');
const defer = () => { let resolve; const p = new Promise((r) => { resolve = r; }); return { p, resolve }; };
test('stale response ignored', async () => {
  const d = { a: defer(), ab: defer() }; const out = [];
  const s = createSearch((q) => d[q].p, (q, r) => out.push([q, r]));
  const p1 = s('a'); const p2 = s('ab');
  d.ab.resolve(['x']); assert.equal(await p2, true);
  d.a.resolve(['y', 'z']); assert.equal(await p1, false);
  assert.deepEqual(out, [['ab', ['x']]]);
});
test('sequential both delivered', async () => {
  const out = []; const s = createSearch(async (q) => q.toUpperCase(), (q, r) => out.push(r));
  await s('a'); await s('b'); assert.deepEqual(out, ['A', 'B']);
});
test('in-order responses: only latest', async () => {
  const d = { a: defer(), b: defer() }; const out = [];
  const s = createSearch((q) => d[q].p, (q, r) => out.push(q));
  const p1 = s('a'); const p2 = s('b'); d.a.resolve(1); d.b.resolve(2); await p1; await p2; assert.deepEqual(out, ['b']);
});""")

jsfix("ui-fix-clamp-nan", "easy", "utilities",
      "`clamp(NaN, 0, 10)` should return the lower bound 0 (not NaN), and when min > max the bounds must be swapped instead of returning garbage.", "clamp.js",
      """function clamp(n, min, max) {
  if (min > max) [min, max] = [max, min];
  if (Number.isNaN(n)) return min;
  return Math.min(Math.max(n, min), max);
}
module.exports = { clamp };""",
      [("  if (min > max) [min, max] = [max, min];\n  if (Number.isNaN(n)) return min;\n  return Math.min(Math.max(n, min), max);", "  return n < min ? min : n > max ? max : n;")],
      """const { clamp } = require('./clamp.js');
test('inside', () => assert.equal(clamp(5, 0, 10), 5));
test('below/above', () => { assert.equal(clamp(-1, 0, 10), 0); assert.equal(clamp(11, 0, 10), 10); });
test('NaN -> min', () => assert.equal(clamp(NaN, 0, 10), 0));
test('swapped bounds', () => { assert.equal(clamp(5, 10, 0), 5); assert.equal(clamp(15, 10, 0), 10); assert.equal(clamp(-5, 10, 0), 0); });
test('infinity', () => { assert.equal(clamp(Infinity, 0, 10), 10); assert.equal(clamp(-Infinity, 0, 10), 0); });""")

jsfix("ui-fix-json-storage", "medium", "utilities",
      "`load('theme')` throws on corrupted JSON, and a stored `false` or `0` comes back as the fallback value.", "prefs.js",
      """function load(store, key, fallback = null) {
  const raw = store.getItem(key);
  if (raw === null) return fallback;
  try { return JSON.parse(raw); } catch (e) { return fallback; }
}
function save(store, key, value) {
  store.setItem(key, JSON.stringify(value));
}
module.exports = { load, save };""",
      [("""  if (raw === null) return fallback;
  try { return JSON.parse(raw); } catch (e) { return fallback; }""", """  return JSON.parse(raw) || fallback;""")],
      """const { load, save } = require('./prefs.js');
const mem = () => { const m = {}; return { getItem: (k) => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = v; } }; };
test('roundtrip', () => { const s = mem(); save(s, 'a', { x: 1 }); assert.deepEqual(load(s, 'a'), { x: 1 }); });
test('missing', () => { const s = mem(); assert.equal(load(s, 'a'), null); assert.equal(load(s, 'a', 7), 7); });
test('false and 0 and empty string survive', () => { const s = mem(); save(s, 'f', false); save(s, 'z', 0); save(s, 'e', ''); assert.equal(load(s, 'f', true), false); assert.equal(load(s, 'z', 5), 0); assert.equal(load(s, 'e', 'x'), ''); });
test('corrupted', () => { const s = mem(); s.setItem('c', '{not json'); assert.equal(load(s, 'c', 'fb'), 'fb'); });""")

jsfix("ui-fix-focus-wrap", "easy", "keyboard",
      "Shift+Tab on the first element should wrap to the last one; currently it returns -1, and Tab on the last element returns the length.", "trap.js",
      """function nextFocus(current, count, shift) {
  if (count === 0) return -1;
  if (shift) return current <= 0 ? count - 1 : current - 1;
  return current >= count - 1 ? 0 : current + 1;
}
module.exports = { nextFocus };""",
      [("  if (shift) return current <= 0 ? count - 1 : current - 1;\n  return current >= count - 1 ? 0 : current + 1;", "  if (shift) return current - 1;\n  return current + 1;")],
      """const { nextFocus: n } = require('./trap.js');
test('forward', () => { assert.equal(n(0, 3, false), 1); assert.equal(n(2, 3, false), 0); });
test('backward', () => { assert.equal(n(1, 3, true), 0); assert.equal(n(0, 3, true), 2); });
test('from outside (-1)', () => { assert.equal(n(-1, 3, false), 0); assert.equal(n(-1, 3, true), 2); });
test('empty', () => assert.equal(n(0, 0, false), -1));""")

jsfix("ui-fix-aria-expanded", "medium", "a11y",
      "The disclosure button never collapses: `aria-expanded` is always set to 'true' after a click, and the panel stays visible.", "disclosure.js",
      """function initDisclosure(button, panel) {
  function set(open) {
    button.setAttribute('aria-expanded', String(open));
    panel.hidden = !open;
  }
  set(button.getAttribute('aria-expanded') === 'true');
  button.addEventListener('click', () => set(button.getAttribute('aria-expanded') !== 'true'));
}
module.exports = { initDisclosure };""",
      [("set(button.getAttribute('aria-expanded') !== 'true'));", "set(button.getAttribute('aria-expanded') != true));"),
       ("set(button.getAttribute('aria-expanded') === 'true');", "set(button.getAttribute('aria-expanded') == true);")],
      """const { initDisclosure } = require('./disclosure.js');
function mk(open) { const doc = makeDom(); const b = doc.build(['button', open ? { 'aria-expanded': 'true' } : {}, 'More']); const p = doc.build(['div', 'text']); doc.body.append(b, p); initDisclosure(b, p); return { b, p }; }
test('initial closed', () => { const { b, p } = mk(false); assert.equal(b.getAttribute('aria-expanded'), 'false'); assert.equal(p.hidden, true); });
test('initial open respected', () => { const { b, p } = mk(true); assert.equal(b.getAttribute('aria-expanded'), 'true'); assert.equal(p.hidden, false); });
test('toggle open/close', () => { const { b, p } = mk(false); b.click(); assert.equal(b.getAttribute('aria-expanded'), 'true'); assert.equal(p.hidden, false); b.click(); assert.equal(b.getAttribute('aria-expanded'), 'false'); assert.equal(p.hidden, true); });""")

jsfix("ui-fix-reducer-mutation", "medium", "state",
      "The reducer mutates the previous state, so UI frameworks that compare state by identity never re-render, and old snapshots change.", "cartstate.js",
      """function cartReducer(state, action) {
  switch (action.type) {
    case 'add': {
      const found = state.items.find((i) => i.id === action.id);
      const items = found
        ? state.items.map((i) => (i.id === action.id ? { ...i, qty: i.qty + 1 } : i))
        : [...state.items, { id: action.id, qty: 1 }];
      return { ...state, items };
    }
    case 'remove':
      return { ...state, items: state.items.filter((i) => i.id !== action.id) };
    default:
      return state;
  }
}
module.exports = { cartReducer };""",
      [("""      const items = found
        ? state.items.map((i) => (i.id === action.id ? { ...i, qty: i.qty + 1 } : i))
        : [...state.items, { id: action.id, qty: 1 }];
      return { ...state, items };""", """      if (found) found.qty += 1; else state.items.push({ id: action.id, qty: 1 });
      return state;"""),
       ("return { ...state, items: state.items.filter((i) => i.id !== action.id) };", "state.items = state.items.filter((i) => i.id !== action.id);\n      return state;")],
      """const { cartReducer: r } = require('./cartstate.js');
test('add new', () => { const s0 = { items: [] }; const s1 = r(s0, { type: 'add', id: 'a' }); assert.notEqual(s1, s0); assert.deepEqual(s0.items, []); assert.deepEqual(s1.items, [{ id: 'a', qty: 1 }]); });
test('add existing', () => { const s0 = { items: [{ id: 'a', qty: 1 }, { id: 'b', qty: 1 }] }; const s1 = r(s0, { type: 'add', id: 'a' }); assert.equal(s0.items[0].qty, 1); assert.equal(s1.items[0].qty, 2); assert.equal(s1.items[1], s0.items[1]); });
test('remove', () => { const s0 = { items: [{ id: 'a', qty: 1 }] }; const s1 = r(s0, { type: 'remove', id: 'a' }); assert.equal(s0.items.length, 1); assert.deepEqual(s1.items, []); assert.notEqual(s1, s0); });
test('unknown returns same', () => { const s0 = { items: [] }; assert.equal(r(s0, { type: 'zzz' }), s0); });
test('other fields preserved', () => assert.equal(r({ items: [], coupon: 'X' }, { type: 'add', id: 'q' }).coupon, 'X'));""")

jsfix("ui-fix-throttle-starve", "hard", "timing",
      "While events keep arriving faster than the wait interval (e.g. scroll events every 30 ms with wait 100), the handler is called once and then never again until the events stop.", "throttle.js",
      """function throttle(fn, wait) {
  let last = -Infinity;
  return function (...args) {
    const now = Date.now();
    if (now - last >= wait) {
      last = now;
      return fn.apply(this, args);
    }
  };
}
module.exports = { throttle };""",
      [("""    if (now - last >= wait) {
      last = now;
      return fn.apply(this, args);
    }""", """    const ready = now - last >= wait;
    last = now;
    if (ready) return fn.apply(this, args);""")],
      """const { throttle } = require('./throttle.js');
test('keeps firing under continuous input', () => { const c = clock(); let n = 0; const t = throttle(() => n++, 100); for (let i = 0; i < 20; i++) { t(); c.tick(30); } assert.ok(n >= 5, 'fired ' + n); c.restore(); });
test('exact schedule', () => { const c = clock(); const at = []; const t = throttle(() => at.push(Date.now() - 1000), 100); for (let i = 0; i < 10; i++) { t(); c.tick(30); } assert.deepEqual(at, [0, 120, 240]); c.restore(); });
test('leading immediate', () => { const c = clock(); let n = 0; const t = throttle(() => n++, 100); t(); assert.equal(n, 1); t(); assert.equal(n, 1); c.restore(); });
test('returns fn result when called', () => { const c = clock(); const t = throttle((x) => x * 2, 100); assert.equal(t(4), 8); c.restore(); });""")

jsfix("ui-fix-quantity-parse", "easy", "forms",
      "A quantity of '0' becomes 1, and '3.7' should be floored to 3; non-numeric text and negatives become 1.", "qty.js",
      """function parseQty(v) {
  if (v === null || v === undefined || (typeof v === 'string' && v.trim() === '')) return 1;
  const n = Math.floor(Number(v));
  return Number.isFinite(n) && n >= 0 ? n : 1;
}
module.exports = { parseQty };""",
      [("""  if (v === null || v === undefined || (typeof v === 'string' && v.trim() === '')) return 1;
  const n = Math.floor(Number(v));
  return Number.isFinite(n) && n >= 0 ? n : 1;""", """  return parseInt(v) || 1;""")],
      """const { parseQty: q } = require('./qty.js');
test('normal', () => { assert.equal(q('5'), 5); assert.equal(q(7), 7); });
test('zero stays zero', () => { assert.equal(q('0'), 0); assert.equal(q(0), 0); });
test('decimals floor', () => assert.equal(q('3.7'), 3));
test('junk -> 1', () => { assert.equal(q('abc'), 1); assert.equal(q(''), 1); assert.equal(q(undefined), 1); assert.equal(q(NaN), 1); });
test('negative -> 1', () => assert.equal(q('-4'), 1));""")

jsfix("ui-fix-relative-sign", "easy", "formatting",
      "Future timestamps are labelled 'ago' and past ones 'in ...' (the sign is inverted), and 1 unit is pluralised ('1 minutes').", "ago.js",
      """function ago(then, now) {
  const d = Math.round((then - now) / 60000);
  const n = Math.abs(d);
  const label = n + ' minute' + (n === 1 ? '' : 's');
  return d < 0 ? label + ' ago' : d > 0 ? 'in ' + label : 'now';
}
module.exports = { ago };""",
      [("""  const d = Math.round((then - now) / 60000);
  const n = Math.abs(d);
  const label = n + ' minute' + (n === 1 ? '' : 's');
  return d < 0 ? label + ' ago' : d > 0 ? 'in ' + label : 'now';""", """  const d = Math.round((now - then) / 60000);
  const n = Math.abs(d);
  const label = n + ' minutes';
  return d < 0 ? label + ' ago' : d > 0 ? 'in ' + label : 'now';""")],
      """const { ago } = require('./ago.js');
const now = 1700000000000, M = 60000;
test('past', () => { assert.equal(ago(now - 5 * M, now), '5 minutes ago'); assert.equal(ago(now - M, now), '1 minute ago'); });
test('future', () => { assert.equal(ago(now + 3 * M, now), 'in 3 minutes'); assert.equal(ago(now + M, now), 'in 1 minute'); });
test('now', () => assert.equal(ago(now + 10000, now), 'now'));""")

jsfix("ui-fix-contrast-gamma", "medium", "a11y",
      "Contrast ratios are too low: black on white should be 21 and #777 on white about 4.48, but the numbers are off because colours are not converted to linear light.", "wcag.js",
      """function channel(v) {
  const c = v / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}
function luminance([r, g, b]) {
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}
function ratio(a, b) {
  const l1 = Math.max(luminance(a), luminance(b)), l2 = Math.min(luminance(a), luminance(b));
  return (l1 + 0.05) / (l2 + 0.05);
}
module.exports = { luminance, ratio };""",
      [("  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);", "  return c;")],
      """const { luminance, ratio } = require('./wcag.js');
test('extremes', () => { assert.equal(luminance([0, 0, 0]), 0); assert.ok(Math.abs(luminance([255, 255, 255]) - 1) < 1e-9); });
test('black/white', () => assert.equal(ratio([0, 0, 0], [255, 255, 255]).toFixed(2), '21.00'));
test('grey 777', () => assert.equal(ratio([0x77, 0x77, 0x77], [255, 255, 255]).toFixed(2), '4.48'));
test('symmetry', () => assert.equal(ratio([10, 20, 30], [200, 210, 220]), ratio([200, 210, 220], [10, 20, 30])));""")

jsfix("ui-fix-days-in-month", "medium", "dates",
      "A calendar shows 31 days for February and 30 for March: the days-in-month helper looks at the wrong month.", "days.js",
      """function daysInMonth(year, month) {
  return new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
}
function isLeap(y) {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
}
module.exports = { daysInMonth, isLeap };""",
      [("Date.UTC(year, month + 1, 0)", "Date.UTC(year, month, 0)"), ("(y % 4 === 0 && y % 100 !== 0) || y % 400 === 0", "y % 4 === 0")],
      """const { daysInMonth: d, isLeap } = require('./days.js');
test('feb', () => { assert.equal(d(2023, 1), 28); assert.equal(d(2024, 1), 29); });
test('31/30', () => { assert.equal(d(2024, 0), 31); assert.equal(d(2024, 2), 31); assert.equal(d(2024, 3), 30); assert.equal(d(2024, 11), 31); });
test('leap rules', () => { assert.equal(isLeap(1900), false); assert.equal(isLeap(2000), true); assert.equal(isLeap(2024), true); assert.equal(isLeap(2023), false); });""")

jsfix("ui-fix-required-zero", "medium", "forms",
      "A required numeric field with value 0 is reported as missing, and whitespace-only text counts as filled in.", "req.js",
      """function isEmpty(v) {
  if (v === null || v === undefined) return true;
  if (typeof v === 'string') return v.trim() === '';
  if (Array.isArray(v)) return v.length === 0;
  return false;
}
function missingFields(values, required) {
  return required.filter((k) => isEmpty(values[k]));
}
module.exports = { isEmpty, missingFields };""",
      [("""  if (v === null || v === undefined) return true;
  if (typeof v === 'string') return v.trim() === '';
  if (Array.isArray(v)) return v.length === 0;
  return false;""", """  return !v;""")],
      """const { isEmpty, missingFields } = require('./req.js');
test('empties', () => { for (const v of [null, undefined, '', '   ', []]) assert.equal(isEmpty(v), true); });
test('non-empties', () => { for (const v of [0, false, 'a', [0], { }, ' x ']) assert.equal(isEmpty(v), false); });
test('missingFields', () => assert.deepEqual(missingFields({ a: 0, b: ' ', c: 'x', d: false }, ['a', 'b', 'c', 'd', 'e']), ['b', 'e']));""")

jsfix("ui-fix-filter-case", "easy", "tables",
      "Filtering a table by 'ann' does not find 'Ann Lee', and rows are matched on the stringified object ('[object Object]') instead of their values.", "rows.js",
      """function search(rows, q) {
  const needle = q.trim().toLowerCase();
  if (!needle) return rows;
  return rows.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(needle)));
}
module.exports = { search };""",
      [("""  const needle = q.trim().toLowerCase();
  if (!needle) return rows;
  return rows.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(needle)));""", """  if (!q) return rows;
  return rows.filter((r) => String(r).includes(q));""")],
      """const { search } = require('./rows.js');
const rows = [{ n: 'Ann Lee', age: 30 }, { n: 'Bob', age: 41 }, { n: 'Cy', age: 30 }];
test('case-insensitive', () => assert.deepEqual(search(rows, 'ann').map((r) => r.n), ['Ann Lee']));
test('numbers', () => assert.deepEqual(search(rows, '30').map((r) => r.n), ['Ann Lee', 'Cy']));
test('blank returns all', () => { assert.equal(search(rows, '  ').length, 3); assert.equal(search(rows, '').length, 3); });
test('trim', () => assert.deepEqual(search(rows, ' bob ').map((r) => r.n), ['Bob']));""")

jsfix("ui-fix-listener-leak", "medium", "events",
      "Every call to `bindClick` adds another handler, so re-rendering a widget makes one click fire the callback several times; the returned cleanup function does nothing.", "bind.js",
      """function bindClick(el, fn) {
  const handler = (e) => fn(e);
  el.addEventListener('click', handler);
  return () => el.removeEventListener('click', handler);
}
function bindOnce(el, type, fn) {
  const h = (e) => { el.removeEventListener(type, h); fn(e); };
  el.addEventListener(type, h);
  return () => el.removeEventListener(type, h);
}
module.exports = { bindClick, bindOnce };""",
      [("  return () => el.removeEventListener('click', handler);", "  return () => el.removeEventListener('click', (e) => fn(e));"),
       ("const h = (e) => { el.removeEventListener(type, h); fn(e); };", "const h = (e) => { fn(e); };")],
      """const { bindClick, bindOnce } = require('./bind.js');
test('cleanup removes handler', () => { const el = makeDom().createElement('button'); let n = 0; const off = bindClick(el, () => n++); el.click(); off(); el.click(); assert.equal(n, 1); });
test('once fires once', () => { const el = makeDom().createElement('button'); let n = 0; bindOnce(el, 'click', () => n++); el.click(); el.click(); assert.equal(n, 1); });
test('once cleanup before fire', () => { const el = makeDom().createElement('button'); let n = 0; const off = bindOnce(el, 'click', () => n++); off(); el.click(); assert.equal(n, 0); });""")
