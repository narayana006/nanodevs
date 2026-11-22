from tb import jsext

jsext("ui-ext-debounce-flush", "medium", "timing",
      "Extend debounce.js: besides `.cancel()`, the debounced function must get `.flush()` (if a call is pending, run `fn` immediately with the pending args/this, clear the timer, and return fn's result; otherwise return undefined) and `.pending()` (true while a call is waiting). Keep existing behaviour.", "debounce.js",
      """function debounce(fn, wait) {
  let t = null;
  function d(...args) {
    clearTimeout(t);
    t = setTimeout(() => { t = null; fn.apply(this, args); }, wait);
  }
  d.cancel = () => { clearTimeout(t); t = null; };
  return d;
}
module.exports = { debounce };""",
      """function debounce(fn, wait) {
  let t = null, lastArgs = null, lastThis = null;
  function d(...args) {
    lastArgs = args; lastThis = this;
    clearTimeout(t);
    t = setTimeout(() => { t = null; const a = lastArgs, c = lastThis; lastArgs = lastThis = null; fn.apply(c, a); }, wait);
  }
  d.cancel = () => { clearTimeout(t); t = null; lastArgs = lastThis = null; };
  d.flush = () => {
    if (t === null) return undefined;
    clearTimeout(t); t = null;
    const a = lastArgs, c = lastThis; lastArgs = lastThis = null;
    return fn.apply(c, a);
  };
  d.pending = () => t !== null;
  return d;
}
module.exports = { debounce };""",
      """const { debounce } = require('./debounce.js');
test('flush runs now with latest args', () => { const c = clock(); const o = []; const d = debounce((x) => { o.push(x); return x + 1; }, 100); d(1); d(2); assert.equal(d.flush(), 3); assert.deepEqual(o, [2]); c.tick(500); assert.deepEqual(o, [2]); c.restore(); });
test('flush without pending', () => { const c = clock(); const d = debounce(() => 1, 100); assert.equal(d.flush(), undefined); c.restore(); });
test('pending', () => { const c = clock(); const d = debounce(() => {}, 100); assert.equal(d.pending(), false); d(); assert.equal(d.pending(), true); c.tick(100); assert.equal(d.pending(), false); d(); d.cancel(); assert.equal(d.pending(), false); c.restore(); });
test('flush keeps this', () => { const c = clock(); const o = { v: 5, f: debounce(function () { return this.v; }, 10) }; o.f(); assert.equal(o.f.flush(), 5); c.restore(); });
test('existing behaviour', () => { const c = clock(); let n = 0; const d = debounce(() => n++, 10); d(); d(); c.tick(10); assert.equal(n, 1); c.restore(); });""")

jsext("ui-ext-tabs-disabled", "medium", "keyboard",
      "Extend the tab navigation helper: `nextTab(current, count, key, disabled = [])` must skip disabled indices when moving with ArrowRight/ArrowLeft (wrapping), and Home/End must go to the first/last ENABLED tab. If no tab is enabled, return `current`. Behaviour without `disabled` must stay the same.", "tabnav.js",
      """function nextTab(current, count, key) {
  if (key === 'ArrowRight') return (current + 1) % count;
  if (key === 'ArrowLeft') return (current - 1 + count) % count;
  if (key === 'Home') return 0;
  if (key === 'End') return count - 1;
  return current;
}
module.exports = { nextTab };""",
      """function nextTab(current, count, key, disabled = []) {
  const on = (i) => !disabled.includes(i);
  if (key === 'ArrowRight' || key === 'ArrowLeft') {
    const dir = key === 'ArrowRight' ? 1 : -1;
    for (let k = 1; k <= count; k++) { const j = (((current + dir * k) % count) + count) % count; if (on(j)) return j; }
    return current;
  }
  if (key === 'Home') { for (let i = 0; i < count; i++) if (on(i)) return i; return current; }
  if (key === 'End') { for (let i = count - 1; i >= 0; i--) if (on(i)) return i; return current; }
  return current;
}
module.exports = { nextTab };""",
      """const { nextTab: n } = require('./tabnav.js');
test('old behaviour', () => { assert.equal(n(0, 3, 'ArrowRight'), 1); assert.equal(n(2, 3, 'ArrowRight'), 0); assert.equal(n(0, 3, 'ArrowLeft'), 2); assert.equal(n(1, 3, 'Home'), 0); assert.equal(n(1, 3, 'End'), 2); assert.equal(n(1, 3, 'x'), 1); });
test('skips disabled right', () => assert.equal(n(0, 4, 'ArrowRight', [1, 2]), 3));
test('skips disabled left wrap', () => assert.equal(n(0, 4, 'ArrowLeft', [3]), 2));
test('wraps past disabled', () => assert.equal(n(3, 4, 'ArrowRight', [0, 1]), 2));
test('home/end enabled', () => { assert.equal(n(2, 5, 'Home', [0, 1]), 2); assert.equal(n(1, 5, 'End', [3, 4]), 2); });
test('all disabled', () => { assert.equal(n(1, 3, 'ArrowRight', [0, 1, 2]), 1); assert.equal(n(1, 3, 'Home', [0, 1, 2]), 1); });
test('only current enabled', () => assert.equal(n(1, 3, 'ArrowRight', [0, 2]), 1));""")

jsext("ui-ext-sort-multi", "medium", "tables",
      "Extend `sortRows(rows, key, dir)` so that `key` may also be an ARRAY of `{key, dir}` specs (multi-column sort: later specs break ties of earlier ones; `dir` defaults to 'asc'). The single-key call form must keep working. Strings compare case-insensitively, numbers numerically, the sort stays stable, and the input array is not mutated.", "sort.js",
      """function cmp(a, b) {
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  const x = String(a).toLowerCase(), y = String(b).toLowerCase();
  return x < y ? -1 : x > y ? 1 : 0;
}
function sortRows(rows, key, dir = 'asc') {
  const s = dir === 'desc' ? -1 : 1;
  return rows.slice().sort((a, b) => s * cmp(a[key], b[key]));
}
module.exports = { sortRows };""",
      """function cmp(a, b) {
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  const x = String(a).toLowerCase(), y = String(b).toLowerCase();
  return x < y ? -1 : x > y ? 1 : 0;
}
function sortRows(rows, key, dir = 'asc') {
  const specs = Array.isArray(key) ? key.map((k) => ({ key: k.key, dir: k.dir || 'asc' })) : [{ key, dir }];
  return rows.slice().sort((a, b) => {
    for (const sp of specs) {
      const c = cmp(a[sp.key], b[sp.key]);
      if (c) return sp.dir === 'desc' ? -c : c;
    }
    return 0;
  });
}
module.exports = { sortRows };""",
      """const { sortRows: s } = require('./sort.js');
const rows = [{ n: 'b', g: 2, id: 1 }, { n: 'A', g: 1, id: 2 }, { n: 'a', g: 2, id: 3 }, { n: 'B', g: 1, id: 4 }];
const ids = (r) => r.map((x) => x.id);
test('single key (old API)', () => { assert.deepEqual(ids(s(rows, 'g')), [2, 4, 1, 3]); assert.deepEqual(ids(s(rows, 'g', 'desc')), [1, 3, 2, 4]); });
test('multi', () => assert.deepEqual(ids(s(rows, [{ key: 'g' }, { key: 'n' }])), [2, 4, 3, 1]));
test('multi with directions', () => assert.deepEqual(ids(s(rows, [{ key: 'g', dir: 'desc' }, { key: 'n', dir: 'asc' }])), [3, 1, 2, 4]));
test('stability', () => assert.deepEqual(ids(s(rows, [{ key: 'g' }])), [2, 4, 1, 3]));
test('no mutation', () => { const copy = rows.map((r) => r.id); s(rows, [{ key: 'n' }]); assert.deepEqual(ids(rows), copy); });
test('empty spec list keeps order', () => assert.deepEqual(ids(s(rows, [])), [1, 2, 3, 4]));""")

jsext("ui-ext-toast-max", "medium", "state",
      "Extend `createToasts()`: accept `{max = Infinity}`. When more than `max` toasts are added, the extras wait in a FIFO queue and are shown (in order) as visible ones are dismissed. Add `queued()` returning the queue length. `visible()` keeps returning visible toasts in insertion order. Existing `add`/`dismiss` behaviour (ids 1,2,3..., dismiss returns true/false) stays.", "toasts.js",
      """function createToasts() {
  let next = 1; const list = [];
  return {
    add(message) { const t = { id: next++, message }; list.push(t); return t.id; },
    dismiss(id) { const i = list.findIndex((t) => t.id === id); if (i < 0) return false; list.splice(i, 1); return true; },
    visible: () => list.slice(),
  };
}
module.exports = { createToasts };""",
      """function createToasts({ max = Infinity } = {}) {
  let next = 1; const list = [], queue = [];
  return {
    add(message) {
      const t = { id: next++, message };
      if (list.length < max) list.push(t); else queue.push(t);
      return t.id;
    },
    dismiss(id) {
      let i = list.findIndex((t) => t.id === id);
      if (i >= 0) { list.splice(i, 1); if (queue.length) list.push(queue.shift()); return true; }
      i = queue.findIndex((t) => t.id === id);
      if (i >= 0) { queue.splice(i, 1); return true; }
      return false;
    },
    visible: () => list.slice(),
    queued: () => queue.length,
  };
}
module.exports = { createToasts };""",
      """const { createToasts: mk } = require('./toasts.js');
test('old API', () => { const t = mk(); assert.equal(t.add('a'), 1); assert.equal(t.add('b'), 2); assert.equal(t.visible().length, 2); assert.equal(t.dismiss(1), true); assert.equal(t.dismiss(1), false); });
test('max queues', () => { const t = mk({ max: 2 }); t.add('a'); t.add('b'); t.add('c'); assert.deepEqual(t.visible().map((x) => x.message), ['a', 'b']); assert.equal(t.queued(), 1); });
test('promotes in order', () => { const t = mk({ max: 1 }); t.add('a'); t.add('b'); t.add('c'); t.dismiss(1); assert.deepEqual(t.visible().map((x) => x.message), ['b']); t.dismiss(2); assert.deepEqual(t.visible().map((x) => x.message), ['c']); assert.equal(t.queued(), 0); });
test('dismiss queued', () => { const t = mk({ max: 1 }); t.add('a'); const q = t.add('b'); assert.equal(t.dismiss(q), true); assert.equal(t.queued(), 0); });
test('queued() default 0', () => assert.equal(mk().queued(), 0));
test('ids keep counting', () => { const t = mk({ max: 1 }); t.add('a'); t.add('b'); t.dismiss(1); assert.equal(t.add('c'), 3); });""")

jsext("ui-ext-validate-async", "hard", "forms",
      "Extend the validator: besides the existing synchronous `validate(values, rules)` (rules map field -> array of `(value) => errorMessage | null`, first failing rule wins), add `validateAsync(values, rules)` returning a Promise of `{valid, errors}`. In the async version a rule may return a Promise (or a plain value); all fields are checked concurrently, but within a field rules run in order and the first non-null message wins. A rule that throws/rejects counts as the error message 'Validation failed'.", "validate.js",
      """function validate(values, rules) {
  const errors = {};
  for (const f of Object.keys(rules)) {
    for (const rule of rules[f]) {
      const m = rule(values[f]);
      if (m) { errors[f] = m; break; }
    }
  }
  return { valid: Object.keys(errors).length === 0, errors };
}
module.exports = { validate };""",
      """function validate(values, rules) {
  const errors = {};
  for (const f of Object.keys(rules)) {
    for (const rule of rules[f]) {
      const m = rule(values[f]);
      if (m) { errors[f] = m; break; }
    }
  }
  return { valid: Object.keys(errors).length === 0, errors };
}
async function validateAsync(values, rules) {
  const errors = {};
  await Promise.all(Object.keys(rules).map(async (f) => {
    for (const rule of rules[f]) {
      let m;
      try { m = await rule(values[f]); } catch (e) { m = 'Validation failed'; }
      if (m) { errors[f] = m; break; }
    }
  }));
  return { valid: Object.keys(errors).length === 0, errors };
}
module.exports = { validate, validateAsync };""",
      """const { validate, validateAsync } = require('./validate.js');
const req = (v) => (v ? null : 'Required');
test('sync still works', () => assert.deepEqual(validate({ a: '' }, { a: [req] }), { valid: false, errors: { a: 'Required' } }));
test('async basic', async () => { const r = await validateAsync({ a: 'x', b: '' }, { a: [req], b: [req] }); assert.deepEqual(r, { valid: false, errors: { b: 'Required' } }); });
test('async rule', async () => { const taken = async (v) => (v === 'bob' ? 'Taken' : null); assert.deepEqual(await validateAsync({ u: 'bob' }, { u: [req, taken] }), { valid: false, errors: { u: 'Taken' } }); assert.equal((await validateAsync({ u: 'amy' }, { u: [req, taken] })).valid, true); });
test('first failing wins, later rules not run', async () => { let ran = false; const r = await validateAsync({ a: '' }, { a: [req, () => { ran = true; return 'Late'; }] }); assert.equal(r.errors.a, 'Required'); assert.equal(ran, false); });
test('throw/reject', async () => { const r = await validateAsync({ a: 1, b: 2 }, { a: [() => { throw new Error('x'); }], b: [async () => { throw new Error('y'); }] }); assert.deepEqual(r.errors, { a: 'Validation failed', b: 'Validation failed' }); });
test('fields concurrent', async () => { const order = []; let release; const gate = new Promise((r) => { release = r; }); const p = validateAsync({ a: 1, b: 2 }, { a: [async () => { order.push('a-start'); await gate; return null; }], b: [async () => { order.push('b-start'); return null; }] }); await Promise.resolve(); await Promise.resolve(); assert.deepEqual(order, ['a-start', 'b-start']); release(); assert.equal((await p).valid, true); });
test('returns a promise', () => assert.ok(validateAsync({}, {}) instanceof Promise));""")

jsext("ui-ext-date-styles", "easy", "dates",
      "Extend `formatDate(date, style = 'iso')` (UTC getters): add styles 'us' -> '03/05/2024', 'eu' -> '05.03.2024', 'long' -> 'March 5, 2024', 'time' -> '14:07' (24h, HH:mm). The default 'iso' (`2024-03-05`) stays. An unknown style throws a RangeError.", "datefmt.js",
      """const p2 = (n) => String(n).padStart(2, '0');
function formatDate(d) {
  return d.getUTCFullYear() + '-' + p2(d.getUTCMonth() + 1) + '-' + p2(d.getUTCDate());
}
module.exports = { formatDate };""",
      """const p2 = (n) => String(n).padStart(2, '0');
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
function formatDate(d, style = 'iso') {
  const y = d.getUTCFullYear(), m = d.getUTCMonth(), day = d.getUTCDate();
  switch (style) {
    case 'iso': return y + '-' + p2(m + 1) + '-' + p2(day);
    case 'us': return p2(m + 1) + '/' + p2(day) + '/' + y;
    case 'eu': return p2(day) + '.' + p2(m + 1) + '.' + y;
    case 'long': return MONTHS[m] + ' ' + day + ', ' + y;
    case 'time': return p2(d.getUTCHours()) + ':' + p2(d.getUTCMinutes());
    default: throw new RangeError('unknown style ' + style);
  }
}
module.exports = { formatDate };""",
      """const { formatDate: f } = require('./datefmt.js');
const d = new Date(Date.UTC(2024, 2, 5, 14, 7));
test('iso default', () => { assert.equal(f(d), '2024-03-05'); assert.equal(f(d, 'iso'), '2024-03-05'); });
test('us/eu', () => { assert.equal(f(d, 'us'), '03/05/2024'); assert.equal(f(d, 'eu'), '05.03.2024'); });
test('long', () => { assert.equal(f(d, 'long'), 'March 5, 2024'); assert.equal(f(new Date(Date.UTC(2023, 11, 25)), 'long'), 'December 25, 2023'); });
test('time', () => { assert.equal(f(d, 'time'), '14:07'); assert.equal(f(new Date(Date.UTC(2024, 0, 1, 3, 4)), 'time'), '03:04'); });
test('unknown', () => assert.throws(() => f(d, 'nope'), RangeError));""")

jsext("ui-ext-form-state", "medium", "forms",
      "Extend `createFormState(initial)`: add `isDirty()` (true if any value differs from the initial value, compared with ===), `touch(name)` / `isTouched(name)` (a field is touched after `touch` or after `set` was called for it), and `reset()` which restores the initial values and clears touched flags. `set`, `get`, `values()` keep working; `values()` returns a copy. `initial` must not be mutated by `set`.", "formstate.js",
      """function createFormState(initial) {
  const v = { ...initial };
  return {
    get: (n) => v[n],
    set(n, x) { v[n] = x; },
    values: () => ({ ...v }),
  };
}
module.exports = { createFormState };""",
      """function createFormState(initial) {
  let v = { ...initial };
  const touched = new Set();
  return {
    get: (n) => v[n],
    set(n, x) { v[n] = x; touched.add(n); },
    values: () => ({ ...v }),
    isDirty: () => Object.keys({ ...initial, ...v }).some((k) => v[k] !== initial[k]),
    touch(n) { touched.add(n); },
    isTouched: (n) => touched.has(n),
    reset() { v = { ...initial }; touched.clear(); },
  };
}
module.exports = { createFormState };""",
      """const { createFormState: mk } = require('./formstate.js');
test('old API', () => { const f = mk({ a: 1 }); f.set('a', 2); assert.equal(f.get('a'), 2); const v = f.values(); v.a = 9; assert.equal(f.get('a'), 2); });
test('initial not mutated', () => { const i = { a: 1 }; const f = mk(i); f.set('a', 2); assert.equal(i.a, 1); });
test('dirty', () => { const f = mk({ a: 1, b: 'x' }); assert.equal(f.isDirty(), false); f.set('a', 2); assert.equal(f.isDirty(), true); f.set('a', 1); assert.equal(f.isDirty(), false); });
test('dirty with new key', () => { const f = mk({ a: 1 }); f.set('z', 5); assert.equal(f.isDirty(), true); });
test('touched', () => { const f = mk({ a: 1, b: 2 }); assert.equal(f.isTouched('a'), false); f.touch('a'); assert.equal(f.isTouched('a'), true); f.set('b', 2); assert.equal(f.isTouched('b'), true); });
test('reset', () => { const f = mk({ a: 1 }); f.set('a', 5); f.set('n', 1); f.reset(); assert.equal(f.get('a'), 1); assert.equal(f.get('n'), undefined); assert.equal(f.isTouched('a'), false); assert.equal(f.isDirty(), false); });""")

jsext("ui-ext-store-selector", "hard", "state",
      "Extend `createStore(reducer, state)` so `subscribe` also accepts `(selector, listener)`: the listener is called with `(newSelected, prevSelected)` only when `selector(state)` changes by `===` after a dispatch. The one-argument form `subscribe(listener)` (called after every dispatch with no args) must still work. Both return an unsubscribe function. The selected value is computed at subscription time as the baseline.", "store.js",
      """function createStore(reducer, state) {
  let listeners = [];
  return {
    getState: () => state,
    dispatch(a) { state = reducer(state, a); listeners.slice().forEach((l) => l()); return a; },
    subscribe(l) { listeners.push(l); return () => { listeners = listeners.filter((x) => x !== l); }; },
  };
}
module.exports = { createStore };""",
      """function createStore(reducer, state) {
  let listeners = [];
  return {
    getState: () => state,
    dispatch(a) { state = reducer(state, a); listeners.slice().forEach((l) => l()); return a; },
    subscribe(selector, listener) {
      let l = selector;
      if (listener) {
        let prev = selector(state);
        l = () => { const next = selector(state); if (next !== prev) { const p = prev; prev = next; listener(next, p); } };
      }
      listeners.push(l);
      return () => { listeners = listeners.filter((x) => x !== l); };
    },
  };
}
module.exports = { createStore };""",
      """const { createStore } = require('./store.js');
const r = (s, a) => (a.type === 'set' ? { ...s, [a.k]: a.v } : s);
test('old subscribe', () => { const s = createStore(r, { a: 1 }); let n = 0; s.subscribe(() => n++); s.dispatch({ type: 'set', k: 'a', v: 1 }); s.dispatch({ type: 'x' }); assert.equal(n, 2); });
test('selector only on change', () => { const s = createStore(r, { a: 1, b: 1 }); const seen = []; s.subscribe((st) => st.a, (n, p) => seen.push([n, p])); s.dispatch({ type: 'set', k: 'b', v: 2 }); assert.deepEqual(seen, []); s.dispatch({ type: 'set', k: 'a', v: 5 }); assert.deepEqual(seen, [[5, 1]]); s.dispatch({ type: 'set', k: 'a', v: 5 }); assert.equal(seen.length, 1); });
test('prev tracks', () => { const s = createStore(r, { a: 1 }); const seen = []; s.subscribe((st) => st.a, (n, p) => seen.push([n, p])); s.dispatch({ type: 'set', k: 'a', v: 2 }); s.dispatch({ type: 'set', k: 'a', v: 3 }); assert.deepEqual(seen, [[2, 1], [3, 2]]); });
test('unsubscribe selector', () => { const s = createStore(r, { a: 1 }); let n = 0; const off = s.subscribe((st) => st.a, () => n++); off(); s.dispatch({ type: 'set', k: 'a', v: 2 }); assert.equal(n, 0); });
test('baseline at subscription time', () => { const s = createStore(r, { a: 1 }); s.dispatch({ type: 'set', k: 'a', v: 2 }); const seen = []; s.subscribe((st) => st.a, (n, p) => seen.push([n, p])); s.dispatch({ type: 'set', k: 'a', v: 2 }); assert.deepEqual(seen, []); s.dispatch({ type: 'set', k: 'a', v: 3 }); assert.deepEqual(seen, [[3, 2]]); });
test('two selectors independent', () => { const s = createStore(r, { a: 1, b: 1 }); let a = 0, b = 0; s.subscribe((st) => st.a, () => a++); s.subscribe((st) => st.b, () => b++); s.dispatch({ type: 'set', k: 'a', v: 9 }); assert.deepEqual([a, b], [1, 0]); });""")

jsext("ui-ext-cart-coupon", "medium", "commerce-ui",
      "Extend `cartTotal(items, coupon)`: `items` are `{price, qty}` (price in cents). Add an optional `coupon` of `{type: 'percent', value: 10, minSpend?: 5000}` or `{type: 'fixed', value: 500, minSpend?}` (cents). The discount applies only if the subtotal >= minSpend (default 0); percent discounts are rounded down to whole cents; the total never goes below 0. Return `{subtotal, discount, total}` (all integers). Without a coupon discount is 0. Existing subtotal logic stays, items with qty <= 0 are ignored.", "cart.js",
      """function cartTotal(items) {
  const subtotal = items.reduce((s, i) => s + i.price * i.qty, 0);
  return { subtotal, discount: 0, total: subtotal };
}
module.exports = { cartTotal };""",
      """function cartTotal(items, coupon) {
  const subtotal = items.reduce((s, i) => s + (i.qty > 0 ? i.price * i.qty : 0), 0);
  let discount = 0;
  if (coupon && subtotal >= (coupon.minSpend || 0)) {
    discount = coupon.type === 'percent' ? Math.floor(subtotal * coupon.value / 100) : coupon.type === 'fixed' ? coupon.value : 0;
  }
  discount = Math.min(discount, subtotal);
  return { subtotal, discount, total: subtotal - discount };
}
module.exports = { cartTotal };""",
      """const { cartTotal: t } = require('./cart.js');
const items = [{ price: 1999, qty: 2 }, { price: 500, qty: 1 }];
test('no coupon', () => assert.deepEqual(t(items), { subtotal: 4498, discount: 0, total: 4498 }));
test('percent floor', () => assert.deepEqual(t(items, { type: 'percent', value: 10 }), { subtotal: 4498, discount: 449, total: 4049 }));
test('fixed', () => assert.deepEqual(t(items, { type: 'fixed', value: 500 }), { subtotal: 4498, discount: 500, total: 3998 }));
test('minSpend not met', () => assert.deepEqual(t(items, { type: 'fixed', value: 500, minSpend: 5000 }), { subtotal: 4498, discount: 0, total: 4498 }));
test('minSpend met exactly', () => assert.equal(t([{ price: 5000, qty: 1 }], { type: 'percent', value: 10, minSpend: 5000 }).total, 4500));
test('never below zero', () => assert.deepEqual(t([{ price: 300, qty: 1 }], { type: 'fixed', value: 1000 }), { subtotal: 300, discount: 300, total: 0 }));
test('qty <= 0 ignored', () => assert.equal(t([{ price: 100, qty: 0 }, { price: 100, qty: -2 }, { price: 50, qty: 1 }]).subtotal, 50));
test('empty cart', () => assert.deepEqual(t([], { type: 'percent', value: 50 }), { subtotal: 0, discount: 0, total: 0 }));""")

jsext("ui-ext-storage-ttl", "hard", "utilities",
      "Extend `createCache(store)` (a JSON wrapper around a Storage-like object): `set(key, value, ttlMs)` takes an optional time-to-live; `get(key)` must return `undefined` (and remove the stored entry) once `Date.now()` has reached the expiry (expiry time = set time + ttl; exactly at expiry it is expired). Without ttl entries never expire. Also add `has(key)` that respects expiry. Use the global `Date.now` at call time. Existing set/get/remove stay compatible.", "cache.js",
      """function createCache(store) {
  return {
    set(key, value) { store.setItem(key, JSON.stringify({ v: value })); },
    get(key) { const raw = store.getItem(key); return raw === null ? undefined : JSON.parse(raw).v; },
    remove(key) { store.removeItem(key); },
  };
}
module.exports = { createCache };""",
      """function createCache(store) {
  function read(key) {
    const raw = store.getItem(key);
    if (raw === null) return undefined;
    const e = JSON.parse(raw);
    if (e.exp !== undefined && Date.now() >= e.exp) { store.removeItem(key); return undefined; }
    return e;
  }
  return {
    set(key, value, ttlMs) {
      const e = { v: value };
      if (ttlMs !== undefined) e.exp = Date.now() + ttlMs;
      store.setItem(key, JSON.stringify(e));
    },
    get(key) { const e = read(key); return e === undefined ? undefined : e.v; },
    has(key) { return read(key) !== undefined; },
    remove(key) { store.removeItem(key); },
  };
}
module.exports = { createCache };""",
      """const { createCache } = require('./cache.js');
const mem = () => { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, v), removeItem: (k) => m.delete(k), _m: m }; };
test('old API', () => { const c = createCache(mem()); c.set('a', { x: 1 }); assert.deepEqual(c.get('a'), { x: 1 }); c.remove('a'); assert.equal(c.get('a'), undefined); });
test('falsy values', () => { const c = createCache(mem()); c.set('z', 0); c.set('f', false); assert.equal(c.get('z'), 0); assert.equal(c.get('f'), false); assert.equal(c.has('z'), true); });
test('ttl expiry', () => { const k = clock(); const c = createCache(mem()); c.set('a', 1, 1000); k.tick(999); assert.equal(c.get('a'), 1); k.tick(1); assert.equal(c.get('a'), undefined); k.restore(); });
test('expired entry removed from store', () => { const k = clock(); const m = mem(); const c = createCache(m); c.set('a', 1, 10); k.tick(10); c.get('a'); assert.equal(m._m.size, 0); k.restore(); });
test('no ttl never expires', () => { const k = clock(); const c = createCache(mem()); c.set('a', 1); k.tick(1e10); assert.equal(c.get('a'), 1); k.restore(); });
test('has respects ttl', () => { const k = clock(); const c = createCache(mem()); c.set('a', 1, 5); assert.equal(c.has('a'), true); k.tick(5); assert.equal(c.has('a'), false); assert.equal(c.has('nope'), false); k.restore(); });
test('set again refreshes', () => { const k = clock(); const c = createCache(mem()); c.set('a', 1, 10); k.tick(8); c.set('a', 2, 10); k.tick(8); assert.equal(c.get('a'), 2); k.restore(); });""")

jsext("ui-ext-emitter-wildcard", "medium", "events",
      "Extend `createEmitter()`: a handler registered for the special event name `'*'` must be called for EVERY emitted event with `(eventName, ...args)` after the specific handlers of that event have run. `emit` returns the total number of handlers called (specific + wildcard). Emitting `'*'` itself calls the wildcard handlers once with `('*', ...args)`. `on` still returns an unsubscribe function.", "emitter.js",
      """function createEmitter() {
  const h = {};
  return {
    on(e, fn) { (h[e] = h[e] || []).push(fn); return () => { h[e] = (h[e] || []).filter((f) => f !== fn); }; },
    emit(e, ...a) { const l = (h[e] || []).slice(); l.forEach((f) => f(...a)); return l.length; },
  };
}
module.exports = { createEmitter };""",
      """function createEmitter() {
  const h = {};
  return {
    on(e, fn) { (h[e] = h[e] || []).push(fn); return () => { h[e] = (h[e] || []).filter((f) => f !== fn); }; },
    emit(e, ...a) {
      const l = e === '*' ? [] : (h[e] || []).slice();
      l.forEach((f) => f(...a));
      const w = (h['*'] || []).slice();
      w.forEach((f) => f(e, ...a));
      return l.length + w.length;
    },
  };
}
module.exports = { createEmitter };""",
      """const { createEmitter } = require('./emitter.js');
test('old behaviour', () => { const e = createEmitter(); const o = []; const off = e.on('a', (x) => o.push(x)); assert.equal(e.emit('a', 1), 1); off(); assert.equal(e.emit('a', 2), 0); assert.deepEqual(o, [1]); });
test('wildcard receives name and args', () => { const e = createEmitter(); const o = []; e.on('*', (n, ...a) => o.push([n, ...a])); e.emit('x', 1, 2); e.emit('y'); assert.deepEqual(o, [['x', 1, 2], ['y']]); });
test('order: specific first', () => { const e = createEmitter(); const o = []; e.on('*', () => o.push('w')); e.on('x', () => o.push('s')); e.emit('x'); assert.deepEqual(o, ['s', 'w']); });
test('count', () => { const e = createEmitter(); e.on('*', () => {}); e.on('x', () => {}); e.on('x', () => {}); assert.equal(e.emit('x'), 3); assert.equal(e.emit('other'), 1); });
test('unsubscribe wildcard', () => { const e = createEmitter(); let n = 0; const off = e.on('*', () => n++); e.emit('a'); off(); e.emit('a'); assert.equal(n, 1); });
test('emit * directly', () => { const e = createEmitter(); const o = []; e.on('*', (n, v) => o.push([n, v])); e.emit('*', 7); assert.deepEqual(o, [['*', 7]]); });""")

jsext("ui-ext-slug-unique", "easy", "text",
      "Extend slug.js: keep `slugify(s)` and add `uniqueSlug(text, taken)` where `taken` is a Set or array of existing slugs. Return slugify(text) if free, otherwise append `-2`, `-3`, ... until unused. If slugify(text) is empty use 'untitled' as the base. `taken` must not be modified.", "slug.js",
      """function slugify(s) {
  return String(s).normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}
module.exports = { slugify };""",
      """function slugify(s) {
  return String(s).normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}
function uniqueSlug(text, taken) {
  const set = new Set(taken);
  const base = slugify(text) || 'untitled';
  if (!set.has(base)) return base;
  let n = 2;
  while (set.has(base + '-' + n)) n++;
  return base + '-' + n;
}
module.exports = { slugify, uniqueSlug };""",
      """const { slugify, uniqueSlug: u } = require('./slug.js');
test('slugify unchanged', () => assert.equal(slugify('Héllo World!'), 'hello-world'));
test('free', () => assert.equal(u('Hello World', []), 'hello-world'));
test('taken', () => assert.equal(u('Hello World', ['hello-world']), 'hello-world-2'));
test('skips used suffixes', () => assert.equal(u('Post', new Set(['post', 'post-2', 'post-3'])), 'post-4'));
test('gap', () => assert.equal(u('Post', ['post', 'post-3']), 'post-2'));
test('empty base', () => { assert.equal(u('!!!', []), 'untitled'); assert.equal(u('', ['untitled']), 'untitled-2'); });
test('taken not modified', () => { const t = new Set(['a']); u('a', t); assert.equal(t.size, 1); const arr = ['a']; u('a', arr); assert.deepEqual(arr, ['a']); });""")
