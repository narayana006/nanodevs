from tb import js, stub

js("ui-js-tabs-reducer", "write", "medium", "state-machine",
   "Implement a pure tabs state machine in tabs.js (`module.exports = { initTabs, tabsReducer }`). `initTabs(count, {selected = 0, disabled = []})` returns `{count, selected, focused, disabled}` with focused = selected. `tabsReducer(state, action)` returns a NEW state (never mutate) or the SAME object when nothing changes. Actions: `{type:'key', key}` where key is 'ArrowRight' / 'ArrowLeft' (move focus to the next/previous ENABLED tab, wrapping around), 'Home' / 'End' (first / last enabled tab); automatic activation means `selected` follows `focused`. `{type:'select', index}` selects and focuses that tab unless it is out of range or disabled. Any other key returns the same state.",
   {"tabs.js": stub("initTabs", "tabsReducer")},
   {"tabs.js": """function initTabs(count, { selected = 0, disabled = [] } = {}) {
  return { count, selected, focused: selected, disabled: disabled.slice() };
}
function tabsReducer(s, a) {
  const on = (i) => !s.disabled.includes(i);
  const go = (i) => (i === s.focused && i === s.selected ? s : { ...s, focused: i, selected: i });
  const step = (dir) => {
    for (let k = 1; k <= s.count; k++) { const j = (((s.focused + dir * k) % s.count) + s.count) % s.count; if (on(j)) return go(j); }
    return s;
  };
  if (a.type === 'select') return a.index >= 0 && a.index < s.count && on(a.index) ? go(a.index) : s;
  if (a.type === 'key') {
    if (a.key === 'ArrowRight') return step(1);
    if (a.key === 'ArrowLeft') return step(-1);
    if (a.key === 'Home') { for (let i = 0; i < s.count; i++) if (on(i)) return go(i); return s; }
    if (a.key === 'End') { for (let i = s.count - 1; i >= 0; i--) if (on(i)) return go(i); return s; }
  }
  return s;
}
module.exports = { initTabs, tabsReducer };"""},
   """const { initTabs: init, tabsReducer: r } = require('./tabs.js');
const K = (key) => ({ type: 'key', key });
test('init', () => assert.deepEqual(init(3), { count: 3, selected: 0, focused: 0, disabled: [] }));
test('arrow right wraps', () => { let s = init(3); s = r(s, K('ArrowRight')); assert.equal(s.selected, 1); s = r(s, K('ArrowRight')); s = r(s, K('ArrowRight')); assert.equal(s.selected, 0); });
test('arrow left wraps', () => assert.equal(r(init(3), K('ArrowLeft')).selected, 2));
test('skips disabled', () => { const s = init(4, { disabled: [1, 2] }); assert.equal(r(s, K('ArrowRight')).selected, 3); assert.equal(r(r(s, K('ArrowRight')), K('ArrowRight')).selected, 0); assert.equal(r(s, K('ArrowLeft')).selected, 3); });
test('home end', () => { const s = init(5, { selected: 2, disabled: [0, 4] }); assert.equal(r(s, K('Home')).selected, 1); assert.equal(r(s, K('End')).selected, 3); });
test('select', () => { const s = init(3, { disabled: [2] }); assert.equal(r(s, { type: 'select', index: 1 }).selected, 1); assert.equal(r(s, { type: 'select', index: 2 }), s); assert.equal(r(s, { type: 'select', index: 9 }), s); assert.equal(r(s, { type: 'select', index: -1 }), s); });
test('unknown key same object', () => { const s = init(3); assert.equal(r(s, K('x')), s); assert.equal(r(s, { type: 'nope' }), s); });
test('immutable', () => { const s = init(3); const t = r(s, K('ArrowRight')); assert.equal(s.selected, 0); assert.notEqual(s, t); });
test('only one enabled', () => { const s = init(3, { selected: 1, disabled: [0, 2] }); assert.equal(r(s, K('ArrowRight')).selected, 1); });""")

js("ui-js-accordion-reducer", "write", "medium", "state-machine",
   "Implement an accordion state machine in accordion.js (`module.exports = { initAccordion, accordionReducer }`). `initAccordion({multiple = false, open = []})` returns `{multiple, open}` where open is an array of open panel ids (in single mode only the first given id is kept). `accordionReducer(state, action)` returns a NEW state without mutating the old one. Actions: `{type:'toggle', id}`: an open panel closes; a closed panel opens (in single mode all others close, in multiple mode it is appended). `{type:'expandAll', ids}` (only in multiple mode: open = all ids, keeping order; ignored in single mode), `{type:'collapseAll'}`. Unknown actions return the same state.",
   {"accordion.js": stub("initAccordion", "accordionReducer")},
   {"accordion.js": """function initAccordion({ multiple = false, open = [] } = {}) {
  return { multiple, open: multiple ? open.slice() : open.slice(0, 1) };
}
function accordionReducer(s, a) {
  switch (a.type) {
    case 'toggle':
      if (s.open.includes(a.id)) return { ...s, open: s.open.filter((x) => x !== a.id) };
      return { ...s, open: s.multiple ? [...s.open, a.id] : [a.id] };
    case 'expandAll': return s.multiple ? { ...s, open: a.ids.slice() } : s;
    case 'collapseAll': return { ...s, open: [] };
    default: return s;
  }
}
module.exports = { initAccordion, accordionReducer };"""},
   """const { initAccordion: init, accordionReducer: r } = require('./accordion.js');
test('init single keeps first', () => assert.deepEqual(init({ open: ['a', 'b'] }), { multiple: false, open: ['a'] }));
test('init multiple', () => assert.deepEqual(init({ multiple: true, open: ['a', 'b'] }), { multiple: true, open: ['a', 'b'] }));
test('single: open closes others', () => { let s = init(); s = r(s, { type: 'toggle', id: 'a' }); s = r(s, { type: 'toggle', id: 'b' }); assert.deepEqual(s.open, ['b']); });
test('single: toggle open closes', () => { const s = r(init({ open: ['a'] }), { type: 'toggle', id: 'a' }); assert.deepEqual(s.open, []); });
test('multiple', () => { let s = init({ multiple: true }); s = r(s, { type: 'toggle', id: 'a' }); s = r(s, { type: 'toggle', id: 'b' }); assert.deepEqual(s.open, ['a', 'b']); s = r(s, { type: 'toggle', id: 'a' }); assert.deepEqual(s.open, ['b']); });
test('expand all', () => { assert.deepEqual(r(init({ multiple: true }), { type: 'expandAll', ids: ['x', 'y'] }).open, ['x', 'y']); const s = init(); assert.equal(r(s, { type: 'expandAll', ids: ['x', 'y'] }), s); });
test('collapse all', () => assert.deepEqual(r(init({ multiple: true, open: ['a'] }), { type: 'collapseAll' }).open, []));
test('immutable', () => { const s = init({ multiple: true, open: ['a'] }); r(s, { type: 'toggle', id: 'b' }); assert.deepEqual(s.open, ['a']); const o = init({ open: ['q'] }); r(o, { type: 'collapseAll' }); assert.deepEqual(o.open, ['q']); });
test('unknown', () => { const s = init(); assert.equal(r(s, { type: 'zzz' }), s); });""")

js("ui-js-modal-stack", "write", "medium", "state-machine",
   "Implement `createModalStack()` in modals.js (`module.exports = { createModalStack }`) managing stacked dialogs. Methods: `open(id)` pushes id on top (if it is already open it is moved to the top, no duplicates), `close(id)` removes that id wherever it is (no-op if not open), `escape()` closes only the TOP modal and returns its id (or null if none), `top()` returns the top id or null, `isOpen(id)`, `ids()` returns a copy of the stack bottom->top, `scrollLocked()` is true while at least one modal is open. `onChange(fn)` registers a listener called with `{ids, scrollLocked}` after every call that actually changes the stack; it returns an unsubscribe function.",
   {"modals.js": stub("createModalStack")},
   {"modals.js": """function createModalStack() {
  let stack = []; const ls = [];
  const emit = () => { const snap = { ids: stack.slice(), scrollLocked: stack.length > 0 }; ls.slice().forEach((f) => f(snap)); };
  return {
    open(id) { if (stack[stack.length - 1] === id) return; stack = stack.filter((x) => x !== id); stack.push(id); emit(); },
    close(id) { if (!stack.includes(id)) return; stack = stack.filter((x) => x !== id); emit(); },
    escape() { if (!stack.length) return null; const id = stack.pop(); emit(); return id; },
    top() { return stack.length ? stack[stack.length - 1] : null; },
    isOpen(id) { return stack.includes(id); },
    ids() { return stack.slice(); },
    scrollLocked() { return stack.length > 0; },
    onChange(fn) { ls.push(fn); return () => { const i = ls.indexOf(fn); if (i >= 0) ls.splice(i, 1); }; },
  };
}
module.exports = { createModalStack };"""},
   """const { createModalStack: mk } = require('./modals.js');
test('open/top/close', () => { const m = mk(); assert.equal(m.top(), null); m.open('a'); m.open('b'); assert.equal(m.top(), 'b'); assert.deepEqual(m.ids(), ['a', 'b']); m.close('a'); assert.deepEqual(m.ids(), ['b']); });
test('no duplicates, moves to top', () => { const m = mk(); m.open('a'); m.open('b'); m.open('a'); assert.deepEqual(m.ids(), ['b', 'a']); });
test('escape closes top only', () => { const m = mk(); m.open('a'); m.open('b'); assert.equal(m.escape(), 'b'); assert.deepEqual(m.ids(), ['a']); assert.equal(m.escape(), 'a'); assert.equal(m.escape(), null); });
test('scrollLocked', () => { const m = mk(); assert.equal(m.scrollLocked(), false); m.open('a'); assert.equal(m.scrollLocked(), true); m.close('a'); assert.equal(m.scrollLocked(), false); });
test('ids is a copy', () => { const m = mk(); m.open('a'); m.ids().push('x'); assert.deepEqual(m.ids(), ['a']); });
test('onChange only on change', () => {
  const m = mk(); const seen = []; const off = m.onChange((s) => seen.push(s));
  m.open('a'); m.open('a'); m.close('zzz'); m.open('b'); m.escape(); assert.deepEqual(seen, [{ ids: ['a'], scrollLocked: true }, { ids: ['a', 'b'], scrollLocked: true }, { ids: ['a'], scrollLocked: true }]);
  off(); m.close('a'); assert.equal(seen.length, 3);
});
test('close middle', () => { const m = mk(); m.open('a'); m.open('b'); m.open('c'); m.close('b'); assert.deepEqual(m.ids(), ['a', 'c']); assert.equal(m.isOpen('b'), false); });""")

js("ui-js-toast-queue", "write", "medium", "state-machine",
   "Implement `createToasts({max = 3})` in toasts.js (`module.exports = { createToasts }`). `add(message, {duration = 0} = {})` returns a numeric id (1, 2, 3, ... in call order), shows the toast if fewer than `max` are visible, otherwise queues it (FIFO). `visible()` returns copies of the visible toasts `{id, message}` in insertion order, `queued()` returns the queued count. `dismiss(id)` removes a visible or queued toast; when a visible one is removed the oldest queued toast becomes visible. If `duration > 0`, a toast auto-dismisses `duration` ms AFTER it becomes visible (queued toasts do not tick while queued). Use global `setTimeout`/`clearTimeout`. `dismiss` on an unknown id does nothing and returns false, otherwise true.",
   {"toasts.js": stub("createToasts")},
   {"toasts.js": """function createToasts({ max = 3 } = {}) {
  let nextId = 1; const vis = [], queue = [], timers = new Map();
  function show(t) {
    vis.push(t);
    if (t.duration > 0) timers.set(t.id, setTimeout(() => dismiss(t.id), t.duration));
  }
  function dismiss(id) {
    let i = vis.findIndex((t) => t.id === id);
    if (i >= 0) {
      vis.splice(i, 1); clearTimeout(timers.get(id)); timers.delete(id);
      if (queue.length && vis.length < max) show(queue.shift());
      return true;
    }
    i = queue.findIndex((t) => t.id === id);
    if (i >= 0) { queue.splice(i, 1); return true; }
    return false;
  }
  return {
    add(message, { duration = 0 } = {}) {
      const t = { id: nextId++, message, duration };
      if (vis.length < max) show(t); else queue.push(t);
      return t.id;
    },
    visible: () => vis.map(({ id, message }) => ({ id, message })),
    queued: () => queue.length,
    dismiss,
  };
}
module.exports = { createToasts };"""},
   """const { createToasts: mk } = require('./toasts.js');
test('ids and visible', () => { const t = mk(); assert.equal(t.add('a'), 1); assert.equal(t.add('b'), 2); assert.deepEqual(t.visible(), [{ id: 1, message: 'a' }, { id: 2, message: 'b' }]); });
test('queue beyond max', () => { const t = mk({ max: 2 }); t.add('a'); t.add('b'); t.add('c'); assert.equal(t.visible().length, 2); assert.equal(t.queued(), 1); });
test('dismiss promotes queue', () => { const t = mk({ max: 2 }); t.add('a'); t.add('b'); t.add('c'); t.add('d'); assert.equal(t.dismiss(1), true); assert.deepEqual(t.visible().map((x) => x.message), ['b', 'c']); assert.equal(t.queued(), 1); });
test('dismiss queued', () => { const t = mk({ max: 1 }); t.add('a'); const q = t.add('b'); assert.equal(t.dismiss(q), true); assert.equal(t.queued(), 0); });
test('unknown id', () => { const t = mk(); assert.equal(t.dismiss(99), false); });
test('auto dismiss', () => { const c = clock(); const t = mk(); t.add('a', { duration: 100 }); c.tick(99); assert.equal(t.visible().length, 1); c.tick(1); assert.equal(t.visible().length, 0); c.restore(); });
test('queued toast timer starts when shown', () => {
  const c = clock(); const t = mk({ max: 1 }); t.add('a', { duration: 100 }); t.add('b', { duration: 100 });
  c.tick(100); assert.deepEqual(t.visible().map((x) => x.message), ['b']); c.tick(99); assert.equal(t.visible().length, 1); c.tick(1); assert.equal(t.visible().length, 0); c.restore();
});
test('manual dismiss clears timer', () => { const c = clock(); const t = mk(); const id = t.add('a', { duration: 100 }); t.dismiss(id); assert.equal(c.pending(), 0); c.restore(); });
test('ids never reused', () => { const t = mk(); t.add('a'); t.dismiss(1); assert.equal(t.add('b'), 2); });""")

js("ui-js-wizard", "write", "medium", "state-machine",
   "Implement `createWizard(steps, validators = {})` in wizard.js (`module.exports = { createWizard }`). `steps` is an array of step names. Methods: `state()` returns `{index, step, isFirst, isLast, reached}` (reached = highest index visited, starts at 0); `next(data)`: if a validator exists for the current step name it is called with `data` and must return true, otherwise `next` returns false and nothing changes; on the last step a successful `next` returns true without moving; otherwise it moves forward, updates `reached` and returns true. `back()` moves back one step (no-op on the first step, returns false then, otherwise true). `goTo(i)` jumps to index i only if 0 <= i <= reached (returns true/false).",
   {"wizard.js": stub("createWizard")},
   {"wizard.js": """function createWizard(steps, validators = {}) {
  let index = 0, reached = 0;
  const state = () => ({ index, step: steps[index], isFirst: index === 0, isLast: index === steps.length - 1, reached });
  return {
    state,
    next(data) {
      const v = validators[steps[index]];
      if (v && v(data) !== true) return false;
      if (index < steps.length - 1) { index++; reached = Math.max(reached, index); }
      return true;
    },
    back() { if (index === 0) return false; index--; return true; },
    goTo(i) { if (!Number.isInteger(i) || i < 0 || i > reached) return false; index = i; return true; },
  };
}
module.exports = { createWizard };"""},
   """const { createWizard: mk } = require('./wizard.js');
test('initial', () => assert.deepEqual(mk(['a', 'b', 'c']).state(), { index: 0, step: 'a', isFirst: true, isLast: false, reached: 0 }));
test('next/back', () => { const w = mk(['a', 'b', 'c']); assert.equal(w.next(), true); assert.equal(w.state().step, 'b'); assert.equal(w.back(), true); assert.equal(w.state().step, 'a'); assert.equal(w.back(), false); });
test('validator blocks', () => { const w = mk(['a', 'b'], { a: (d) => !!d && d.ok === true }); assert.equal(w.next({ ok: false }), false); assert.equal(w.state().index, 0); assert.equal(w.next({ ok: true }), true); assert.equal(w.state().index, 1); });
test('validator must return true exactly', () => { const w = mk(['a', 'b'], { a: () => 'yes' }); assert.equal(w.next(), false); });
test('last step', () => { const w = mk(['a', 'b']); w.next(); assert.equal(w.state().isLast, true); assert.equal(w.next(), true); assert.equal(w.state().index, 1); });
test('goTo limited by reached', () => { const w = mk(['a', 'b', 'c', 'd']); w.next(); w.next(); w.back(); assert.equal(w.state().reached, 2); assert.equal(w.goTo(2), true); assert.equal(w.goTo(3), false); assert.equal(w.goTo(-1), false); assert.equal(w.goTo(0), true); assert.equal(w.state().index, 0); });
test('validator on last step gates completion', () => { const w = mk(['a'], { a: () => false }); assert.equal(w.next(), false); });
test('validator gets data', () => { let got; const w = mk(['a', 'b'], { a: (d) => { got = d; return true; } }); w.next({ x: 1 }); assert.deepEqual(got, { x: 1 }); });""")

js("ui-js-carousel", "write", "hard", "state-machine",
   "Implement `createCarousel({count, loop = true, interval = 0})` in carousel.js (`module.exports = { createCarousel }`). Methods: `index()`, `next()`, `prev()`, `goTo(i)` (ignored if i is not an integer in range), `start()`, `stop()`, `running()`. With `loop` true next/prev wrap around; with loop false they stay at the ends. `start()` (only when interval > 0) calls `next()` every `interval` ms using global `setInterval`/`clearInterval`; any manual next/prev/goTo while running restarts the interval timer (so the next auto-advance is `interval` ms after the manual action). With `loop: false` autoplay stops itself after reaching the last slide. `start()` twice must not create a second timer. `stop()` clears the timer.",
   {"carousel.js": stub("createCarousel")},
   {"carousel.js": """function createCarousel({ count, loop = true, interval = 0 }) {
  let i = 0, timer = null;
  const clear = () => { if (timer !== null) { clearInterval(timer); timer = null; } };
  const arm = () => { clear(); if (interval > 0) timer = setInterval(() => { c.next(true); }, interval); };
  const c = {
    index: () => i,
    next(auto) {
      if (i < count - 1) i++; else if (loop) i = 0;
      if (!loop && i === count - 1 && auto) clear(); else if (!auto && timer !== null) arm();
    },
    prev() { if (i > 0) i--; else if (loop) i = count - 1; if (timer !== null) arm(); },
    goTo(n) { if (Number.isInteger(n) && n >= 0 && n < count) { i = n; if (timer !== null) arm(); } },
    start() { if (timer === null) arm(); },
    stop: clear,
    running: () => timer !== null,
  };
  return c;
}
module.exports = { createCarousel };"""},
   """const { createCarousel: mk } = require('./carousel.js');
test('loop', () => { const c = mk({ count: 3 }); c.next(); c.next(); c.next(); assert.equal(c.index(), 0); c.prev(); assert.equal(c.index(), 2); });
test('no loop', () => { const c = mk({ count: 2, loop: false }); c.prev(); assert.equal(c.index(), 0); c.next(); c.next(); assert.equal(c.index(), 1); });
test('goTo', () => { const c = mk({ count: 4 }); c.goTo(2); assert.equal(c.index(), 2); c.goTo(9); c.goTo(-1); c.goTo(1.5); assert.equal(c.index(), 2); });
test('autoplay', () => { const k = clock(); const c = mk({ count: 3, interval: 100 }); c.start(); assert.equal(c.running(), true); k.tick(100); assert.equal(c.index(), 1); k.tick(200); assert.equal(c.index(), 0); c.stop(); k.tick(500); assert.equal(c.index(), 0); assert.equal(c.running(), false); k.restore(); });
test('manual action restarts timer', () => { const k = clock(); const c = mk({ count: 5, interval: 100 }); c.start(); k.tick(80); c.next(); assert.equal(c.index(), 1); k.tick(80); assert.equal(c.index(), 1); k.tick(20); assert.equal(c.index(), 2); k.restore(); });
test('goTo / prev restart timer', () => { const k = clock(); const c = mk({ count: 5, interval: 100 }); c.start(); k.tick(90); c.goTo(3); k.tick(90); assert.equal(c.index(), 3); k.tick(10); assert.equal(c.index(), 4); c.prev(); k.tick(99); assert.equal(c.index(), 3); k.restore(); });
test('double start single timer', () => { const k = clock(); const c = mk({ count: 9, interval: 100 }); c.start(); c.start(); assert.equal(k.pending(), 1); k.tick(100); assert.equal(c.index(), 1); k.restore(); });
test('no loop autoplay stops at end', () => { const k = clock(); const c = mk({ count: 3, loop: false, interval: 50 }); c.start(); k.tick(500); assert.equal(c.index(), 2); assert.equal(c.running(), false); assert.equal(k.pending(), 0); k.restore(); });
test('interval 0 never runs', () => { const k = clock(); const c = mk({ count: 3 }); c.start(); assert.equal(c.running(), false); assert.equal(k.pending(), 0); k.restore(); });
test('stop when not running ok', () => { const c = mk({ count: 3, interval: 10 }); c.stop(); assert.equal(c.running(), false); });""")

js("ui-js-undo-history", "write", "medium", "state-machine",
   "Implement `createHistory(initial, {limit = 100} = {})` in history.js (`module.exports = { createHistory }`), an undo/redo stack for an editor. Methods: `present()`, `push(value)` (makes value the present, clears the redo stack; ignored when `value === present()`), `undo()`, `redo()` (both return true if they moved, false otherwise), `canUndo()`, `canRedo()`. At most `limit` undo steps are kept (the oldest are dropped).",
   {"history.js": stub("createHistory")},
   {"history.js": """function createHistory(initial, { limit = 100 } = {}) {
  let past = [], present = initial, future = [];
  return {
    present: () => present,
    push(v) { if (v === present) return; past.push(present); if (past.length > limit) past.shift(); present = v; future = []; },
    undo() { if (!past.length) return false; future.push(present); present = past.pop(); return true; },
    redo() { if (!future.length) return false; past.push(present); present = future.pop(); return true; },
    canUndo: () => past.length > 0,
    canRedo: () => future.length > 0,
  };
}
module.exports = { createHistory };"""},
   """const { createHistory: mk } = require('./history.js');
test('basic', () => { const h = mk('a'); h.push('b'); h.push('c'); assert.equal(h.present(), 'c'); assert.equal(h.undo(), true); assert.equal(h.present(), 'b'); assert.equal(h.redo(), true); assert.equal(h.present(), 'c'); });
test('empty', () => { const h = mk(0); assert.equal(h.canUndo(), false); assert.equal(h.canRedo(), false); assert.equal(h.undo(), false); assert.equal(h.redo(), false); });
test('push clears redo', () => { const h = mk(1); h.push(2); h.undo(); assert.equal(h.canRedo(), true); h.push(3); assert.equal(h.canRedo(), false); assert.equal(h.redo(), false); assert.equal(h.present(), 3); });
test('same value ignored', () => { const h = mk(1); h.push(1); assert.equal(h.canUndo(), false); h.push(2); h.undo(); h.push(1); assert.equal(h.canRedo(), true); });
test('limit', () => { const h = mk(0, { limit: 2 }); for (let i = 1; i <= 5; i++) h.push(i); assert.equal(h.undo(), true); assert.equal(h.undo(), true); assert.equal(h.undo(), false); assert.equal(h.present(), 3); });
test('multi undo redo', () => { const h = mk(0); [1, 2, 3].forEach((x) => h.push(x)); h.undo(); h.undo(); h.undo(); assert.equal(h.present(), 0); h.redo(); h.redo(); assert.equal(h.present(), 2); });""")

js("ui-js-todo-reducer", "write", "medium", "state-machine",
   "Implement `todoReducer(state = [], action)` and `visibleTodos(todos, filter)` in todos.js (`module.exports = { todoReducer, visibleTodos }`). A todo is `{id, text, done}`. Actions: `{type:'add', text}` (trim the text; blank text is ignored; id = max existing id + 1, or 1), `{type:'toggle', id}`, `{type:'remove', id}`, `{type:'edit', id, text}` (trimmed; blank text removes the todo), `{type:'clearCompleted'}`, `{type:'toggleAll'}` (if every todo is done mark all not done, otherwise mark all done). Never mutate the old state; todos that did not change keep the same object identity; an action that changes nothing returns the same array. `visibleTodos(todos, 'all' | 'active' | 'done')` filters; unknown filter returns all.",
   {"todos.js": stub("todoReducer", "visibleTodos")},
   {"todos.js": """function todoReducer(state = [], a) {
  switch (a.type) {
    case 'add': {
      const text = String(a.text || '').trim();
      if (!text) return state;
      return [...state, { id: state.reduce((m, t) => Math.max(m, t.id), 0) + 1, text, done: false }];
    }
    case 'toggle': return state.some((t) => t.id === a.id) ? state.map((t) => (t.id === a.id ? { ...t, done: !t.done } : t)) : state;
    case 'remove': return state.some((t) => t.id === a.id) ? state.filter((t) => t.id !== a.id) : state;
    case 'edit': {
      const text = String(a.text || '').trim();
      if (!state.some((t) => t.id === a.id)) return state;
      if (!text) return state.filter((t) => t.id !== a.id);
      return state.map((t) => (t.id === a.id && t.text !== text ? { ...t, text } : t));
    }
    case 'clearCompleted': return state.some((t) => t.done) ? state.filter((t) => !t.done) : state;
    case 'toggleAll': {
      const all = state.length > 0 && state.every((t) => t.done);
      return state.map((t) => (t.done === !all ? t : { ...t, done: !all }));
    }
    default: return state;
  }
}
function visibleTodos(todos, filter) {
  if (filter === 'active') return todos.filter((t) => !t.done);
  if (filter === 'done') return todos.filter((t) => t.done);
  return todos;
}
module.exports = { todoReducer, visibleTodos };"""},
   """const { todoReducer: r, visibleTodos: v } = require('./todos.js');
test('add', () => { let s = r(undefined, { type: 'add', text: '  milk ' }); s = r(s, { type: 'add', text: 'eggs' }); assert.deepEqual(s, [{ id: 1, text: 'milk', done: false }, { id: 2, text: 'eggs', done: false }]); });
test('add blank ignored', () => { const s = []; assert.equal(r(s, { type: 'add', text: '   ' }), s); });
test('id after removal uses max', () => { let s = r([], { type: 'add', text: 'a' }); s = r(s, { type: 'add', text: 'b' }); s = r(s, { type: 'remove', id: 1 }); s = r(s, { type: 'add', text: 'c' }); assert.deepEqual(s.map((t) => t.id), [2, 3]); });
test('toggle and identity', () => { const s = [{ id: 1, text: 'a', done: false }, { id: 2, text: 'b', done: false }]; const t = r(s, { type: 'toggle', id: 1 }); assert.equal(t[0].done, true); assert.equal(t[1], s[1]); assert.equal(s[0].done, false); });
test('toggle unknown id same state', () => { const s = [{ id: 1, text: 'a', done: false }]; assert.equal(r(s, { type: 'toggle', id: 9 }), s); assert.equal(r(s, { type: 'remove', id: 9 }), s); });
test('edit', () => { const s = [{ id: 1, text: 'a', done: false }]; assert.equal(r(s, { type: 'edit', id: 1, text: ' z ' })[0].text, 'z'); assert.deepEqual(r(s, { type: 'edit', id: 1, text: '  ' }), []); });
test('clearCompleted', () => { const s = [{ id: 1, text: 'a', done: true }, { id: 2, text: 'b', done: false }]; assert.deepEqual(r(s, { type: 'clearCompleted' }).map((t) => t.id), [2]); const u = [s[1]]; assert.equal(r(u, { type: 'clearCompleted' }), u); });
test('toggleAll', () => { let s = [{ id: 1, text: 'a', done: true }, { id: 2, text: 'b', done: false }]; s = r(s, { type: 'toggleAll' }); assert.deepEqual(s.map((t) => t.done), [true, true]); s = r(s, { type: 'toggleAll' }); assert.deepEqual(s.map((t) => t.done), [false, false]); assert.deepEqual(r([], { type: 'toggleAll' }), []); });
test('visible', () => { const s = [{ id: 1, text: 'a', done: true }, { id: 2, text: 'b', done: false }]; assert.deepEqual(v(s, 'active').map((t) => t.id), [2]); assert.deepEqual(v(s, 'done').map((t) => t.id), [1]); assert.equal(v(s, 'zzz').length, 2); });""")

js("ui-js-store", "write", "hard", "state-machine",
   "Implement `createStore(reducer, initialState)` in store.js (`module.exports = { createStore }`), a minimal Redux-like store. `getState()`, `dispatch(action)` (calls reducer(state, action), stores the result, then notifies listeners with no arguments, and returns the action; throws if the action is not an object with a string `type`), `subscribe(listener)` returns an unsubscribe function (idempotent). Listeners are notified from a snapshot taken when notification starts: a listener added during notification is NOT called until the next dispatch, and the snapshot is used as-is (so a listener unsubscribed by an earlier listener in the same round is still called that round). Subscribing the same function twice makes two registrations; each unsubscribe removes only its own. Calling `dispatch` from inside the reducer must throw an Error('Reducers may not dispatch'). The reducer is NOT called at creation time.",
   {"store.js": stub("createStore")},
   {"store.js": """function createStore(reducer, initial) {
  let state = initial, listeners = [], reducing = false;
  const store = {
    getState: () => state,
    dispatch(action) {
      if (!action || typeof action !== 'object' || typeof action.type !== 'string') throw new TypeError('Actions must be objects with a string type');
      if (reducing) throw new Error('Reducers may not dispatch');
      try { reducing = true; state = reducer(state, action); } finally { reducing = false; }
      const snap = listeners.slice();
      snap.forEach((r) => r.l());
      return action;
    },
    subscribe(l) {
      const rec = { l };
      listeners.push(rec);
      return () => { listeners = listeners.filter((x) => x !== rec); };
    },
  };
  return store;
}
module.exports = { createStore };"""},
   """const { createStore: mk } = require('./store.js');
const counter = (s = 0, a) => (a.type === 'inc' ? s + 1 : a.type === 'add' ? s + a.n : s);
test('state and dispatch', () => { const s = mk(counter, 5); assert.equal(s.getState(), 5); const a = { type: 'inc' }; assert.equal(s.dispatch(a), a); assert.equal(s.getState(), 6); s.dispatch({ type: 'add', n: 10 }); assert.equal(s.getState(), 16); });
test('reducer not called at creation', () => { let n = 0; mk(() => { n++; return 0; }, 0); assert.equal(n, 0); });
test('subscribe / unsubscribe', () => { const s = mk(counter, 0); let n = 0; const off = s.subscribe(() => n++); s.dispatch({ type: 'inc' }); off(); off(); s.dispatch({ type: 'inc' }); assert.equal(n, 1); });
test('listeners see new state', () => { const s = mk(counter, 0); let seen; s.subscribe(() => { seen = s.getState(); }); s.dispatch({ type: 'inc' }); assert.equal(seen, 1); });
test('subscribe during notify not called this round', () => { const s = mk(counter, 0); let late = 0; s.subscribe(() => { s.subscribe(() => late++); }); s.dispatch({ type: 'inc' }); assert.equal(late, 0); s.dispatch({ type: 'inc' }); assert.equal(late, 1); });
test('unsubscribe during notify does not break others', () => { const s = mk(counter, 0); const calls = []; let off2; s.subscribe(() => { calls.push('a'); off2(); }); off2 = s.subscribe(() => calls.push('b')); s.subscribe(() => calls.push('c')); s.dispatch({ type: 'inc' }); assert.deepEqual(calls, ['a', 'b', 'c']); calls.length = 0; s.dispatch({ type: 'inc' }); assert.deepEqual(calls, ['a', 'c']); });
test('dispatch in reducer throws', () => { const s = mk((st, a) => { if (a.type === 'x') s.dispatch({ type: 'y' }); return st; }, 0); assert.throws(() => s.dispatch({ type: 'x' }), /may not dispatch/); s.dispatch({ type: 'z' }); });
test('bad action', () => { const s = mk(counter, 0); assert.throws(() => s.dispatch(null)); assert.throws(() => s.dispatch({})); assert.throws(() => s.dispatch('inc')); });
test('same listener subscribed twice, unsubscribe one', () => { const s = mk(counter, 0); let n = 0; const f = () => n++; const o1 = s.subscribe(f); s.subscribe(f); o1(); s.dispatch({ type: 'inc' }); assert.equal(n, 1); });""")

js("ui-js-emitter", "write", "medium", "utilities",
   "Implement `createEmitter()` in emitter.js (`module.exports = { createEmitter }`) with `on(event, fn)` (returns an unsubscribe function), `once(event, fn)` (also returns unsubscribe; the handler runs at most once), `off(event, fn)` (removes ONE registration of fn; no-op if absent), `emit(event, ...args)` which calls handlers in registration order with args and returns the number of handlers called, and `listenerCount(event)`. emit iterates a snapshot: handlers added during an emit run only on later emits, and handlers removed during an emit (including a `once` handler removing itself) must not break the iteration of the others.",
   {"emitter.js": stub("createEmitter")},
   {"emitter.js": """function createEmitter() {
  const map = new Map();
  const list = (e) => { if (!map.has(e)) map.set(e, []); return map.get(e); };
  const api = {
    on(e, fn) { const rec = { fn }; list(e).push(rec); return () => { const l = list(e), i = l.indexOf(rec); if (i >= 0) l.splice(i, 1); }; },
    once(e, fn) { const off = api.on(e, (...a) => { off(); fn(...a); }); return off; },
    off(e, fn) { const l = list(e), i = l.findIndex((r) => r.fn === fn); if (i >= 0) l.splice(i, 1); },
    emit(e, ...args) { const snap = list(e).slice(); snap.forEach((r) => r.fn(...args)); return snap.length; },
    listenerCount: (e) => list(e).length,
  };
  return api;
}
module.exports = { createEmitter };"""},
   """const { createEmitter: mk } = require('./emitter.js');
test('on/emit', () => { const e = mk(); const got = []; e.on('x', (a, b) => got.push([a, b])); assert.equal(e.emit('x', 1, 2), 1); assert.deepEqual(got, [[1, 2]]); assert.equal(e.emit('none'), 0); });
test('order', () => { const e = mk(); const o = []; e.on('x', () => o.push(1)); e.on('x', () => o.push(2)); e.emit('x'); assert.deepEqual(o, [1, 2]); });
test('unsubscribe', () => { const e = mk(); let n = 0; const off = e.on('x', () => n++); off(); e.emit('x'); assert.equal(n, 0); assert.equal(e.listenerCount('x'), 0); });
test('off removes one registration', () => { const e = mk(); let n = 0; const f = () => n++; e.on('x', f); e.on('x', f); e.off('x', f); e.emit('x'); assert.equal(n, 1); e.off('x', () => {}); });
test('once', () => { const e = mk(); let n = 0; e.once('x', () => n++); e.emit('x'); e.emit('x'); assert.equal(n, 1); assert.equal(e.listenerCount('x'), 0); });
test('once unsubscribe before fire', () => { const e = mk(); let n = 0; const off = e.once('x', () => n++); off(); e.emit('x'); assert.equal(n, 0); });
test('once does not skip neighbours', () => { const e = mk(); const o = []; e.once('x', () => o.push('a')); e.on('x', () => o.push('b')); e.on('x', () => o.push('c')); assert.equal(e.emit('x'), 3); assert.deepEqual(o, ['a', 'b', 'c']); });
test('added during emit not called', () => { const e = mk(); let late = 0; e.on('x', () => e.on('x', () => late++)); e.emit('x'); assert.equal(late, 0); e.emit('x'); assert.equal(late, 1); });
test('event isolation', () => { const e = mk(); let n = 0; e.on('a', () => n++); e.emit('b'); assert.equal(n, 0); });""")
