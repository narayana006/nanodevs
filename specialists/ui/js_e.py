from tb import js, stub

DOMNOTE = " Tests run against a tiny DOM stub (createElement, appendChild, querySelector(All) with tag/.class/#id/[attr] compound selectors and descendant combinators, classList, setAttribute/getAttribute/removeAttribute, hidden, addEventListener/dispatchEvent with bubbling, focus() updating document.activeElement); stick to that API."

js("ui-dom-tabs", "write", "hard", "dom-component",
   "Implement `initTabs(root)` in tabs.js (`module.exports = { initTabs }`) that makes this markup an accessible tab widget: `root` contains one `.tablist` element holding `.tab` buttons and, in the same order, `.panel` elements. Set `role=tablist` on the list, `role=tab` on tabs, `role=tabpanel` on panels; give every tab and panel an id if it lacks one (e.g. `${root.id || 'tabs'}-tab-0`), link them with `aria-controls` (tab -> panel) and `aria-labelledby` (panel -> tab). The selected tab (initially the one with `aria-selected=\"true\"`, else the first) has `aria-selected=\"true\"` and `tabindex=\"0\"`; the others `aria-selected=\"false\"` and `tabindex=\"-1\"`; only the selected panel is visible (others get the `hidden` attribute). Clicking a tab selects it. On `keydown` on a tab: ArrowRight/ArrowLeft move to the next/previous tab (wrapping), Home/End to the first/last; the new tab is selected AND focused (call `.focus()`), and `preventDefault()` is called for handled keys. Return `{ select(i) }`." + DOMNOTE,
   {"tabs.js": stub("initTabs")},
   {"tabs.js": """function initTabs(root) {
  const tablist = root.querySelector('.tablist');
  const tabs = root.querySelectorAll('.tab'), panels = root.querySelectorAll('.panel');
  const base = root.id || 'tabs';
  tablist.setAttribute('role', 'tablist');
  tabs.forEach((t, i) => {
    if (!t.id) t.id = base + '-tab-' + i;
    if (!panels[i].id) panels[i].id = base + '-panel-' + i;
    t.setAttribute('role', 'tab');
    t.setAttribute('aria-controls', panels[i].id);
    panels[i].setAttribute('role', 'tabpanel');
    panels[i].setAttribute('aria-labelledby', t.id);
  });
  function select(i, focus) {
    tabs.forEach((t, j) => {
      const on = j === i;
      t.setAttribute('aria-selected', String(on));
      t.setAttribute('tabindex', on ? '0' : '-1');
      panels[j].hidden = !on;
    });
    if (focus) tabs[i].focus();
  }
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => select(i, false));
    t.addEventListener('keydown', (e) => {
      const n = tabs.length;
      let j = null;
      if (e.key === 'ArrowRight') j = (i + 1) % n;
      else if (e.key === 'ArrowLeft') j = (i - 1 + n) % n;
      else if (e.key === 'Home') j = 0;
      else if (e.key === 'End') j = n - 1;
      if (j !== null) { e.preventDefault(); select(j, true); }
    });
  });
  const init = tabs.findIndex((t) => t.getAttribute('aria-selected') === 'true');
  select(init < 0 ? 0 : init, false);
  return { select: (i) => select(i, false) };
}
module.exports = { initTabs };"""},
   """const { initTabs } = require('./tabs.js');
function setup(extra) {
  const doc = makeDom();
  const root = doc.build(['div#demo', ['div.tablist', ['button.tab', extra || {}, 'One'], ['button.tab', 'Two'], ['button.tab', 'Three']], ['div.panel', 'P1'], ['div.panel', 'P2'], ['div.panel', 'P3']]);
  doc.body.appendChild(root);
  return { doc, root, tabs: root.querySelectorAll('.tab'), panels: root.querySelectorAll('.panel') };
}
test('roles', () => { const { root, tabs, panels } = setup(); initTabs(root); assert.equal(root.querySelector('.tablist').getAttribute('role'), 'tablist'); tabs.forEach((t) => assert.equal(t.getAttribute('role'), 'tab')); panels.forEach((p) => assert.equal(p.getAttribute('role'), 'tabpanel')); });
test('ids and relationships', () => { const { root, tabs, panels } = setup(); initTabs(root); const ids = new Set(); tabs.forEach((t, i) => { assert.ok(t.id && panels[i].id); ids.add(t.id); ids.add(panels[i].id); assert.equal(t.getAttribute('aria-controls'), panels[i].id); assert.equal(panels[i].getAttribute('aria-labelledby'), t.id); }); assert.equal(ids.size, 6); });
test('existing ids kept', () => { const { root, tabs, panels } = setup({ id: 'mine' }); initTabs(root); assert.equal(tabs[0].id, 'mine'); assert.equal(panels[0].getAttribute('aria-labelledby'), 'mine'); });
test('initial selection', () => { const { root, tabs, panels } = setup(); initTabs(root); assert.deepEqual(tabs.map((t) => t.getAttribute('aria-selected')), ['true', 'false', 'false']); assert.deepEqual(tabs.map((t) => t.getAttribute('tabindex')), ['0', '-1', '-1']); assert.deepEqual(panels.map((p) => p.hidden), [false, true, true]); });
test('initial aria-selected honoured', () => { const { root, tabs, panels } = setup(); tabs[1].setAttribute('aria-selected', 'true'); initTabs(root); assert.deepEqual(panels.map((p) => p.hidden), [true, false, true]); });
test('click', () => { const { root, tabs, panels } = setup(); initTabs(root); tabs[2].click(); assert.equal(tabs[2].getAttribute('aria-selected'), 'true'); assert.equal(tabs[0].getAttribute('aria-selected'), 'false'); assert.deepEqual(panels.map((p) => p.hidden), [true, true, false]); assert.equal(tabs[2].getAttribute('tabindex'), '0'); });
test('arrow keys select+focus+prevent', () => { const { doc, root, tabs } = setup(); initTabs(root); const e = key('ArrowRight'); tabs[0].dispatchEvent(e); assert.equal(e.defaultPrevented, true); assert.equal(doc.activeElement, tabs[1]); assert.equal(tabs[1].getAttribute('aria-selected'), 'true'); });
test('wrap and home/end', () => { const { doc, root, tabs } = setup(); initTabs(root); tabs[0].dispatchEvent(key('ArrowLeft')); assert.equal(doc.activeElement, tabs[2]); tabs[2].dispatchEvent(key('ArrowRight')); assert.equal(doc.activeElement, tabs[0]); tabs[0].dispatchEvent(key('End')); assert.equal(doc.activeElement, tabs[2]); tabs[2].dispatchEvent(key('Home')); assert.equal(doc.activeElement, tabs[0]); });
test('other keys untouched', () => { const { root, tabs } = setup(); initTabs(root); const e = key('a'); tabs[0].dispatchEvent(e); assert.equal(e.defaultPrevented, false); });
test('select api', () => { const { root, panels } = setup(); const api = initTabs(root); api.select(1); assert.deepEqual(panels.map((p) => p.hidden), [true, false, true]); });""")

js("ui-dom-accordion", "write", "medium", "dom-component",
   "Implement `initAccordion(root)` in acc.js (`module.exports = { initAccordion }`). `root` contains `.acc-trigger` buttons; each has `aria-controls` pointing at the id of its panel (a descendant of root). On init, every trigger gets `aria-expanded` (kept as 'true' if it already is, otherwise 'false') and its panel gets the `hidden` attribute unless expanded. Clicking a trigger toggles it. Unless `root` has `data-multiple=\"true\"`, opening a panel closes all the others (single-open mode). Closing an open panel is always allowed." + DOMNOTE,
   {"acc.js": stub("initAccordion")},
   {"acc.js": """function initAccordion(root) {
  const triggers = root.querySelectorAll('.acc-trigger');
  const multiple = root.dataset.multiple === 'true';
  const panel = (t) => root.querySelector('#' + t.getAttribute('aria-controls'));
  function set(t, open) { t.setAttribute('aria-expanded', String(open)); panel(t).hidden = !open; }
  triggers.forEach((t) => {
    set(t, t.getAttribute('aria-expanded') === 'true');
    t.addEventListener('click', () => {
      const open = t.getAttribute('aria-expanded') !== 'true';
      if (open && !multiple) triggers.forEach((o) => { if (o !== t) set(o, false); });
      set(t, open);
    });
  });
}
module.exports = { initAccordion };"""},
   """const { initAccordion } = require('./acc.js');
function setup(attrs, firstOpen) {
  const doc = makeDom();
  const root = doc.build(['div', attrs || {}, ['button.acc-trigger', { 'aria-controls': 'p1' }, 'A'], ['div#p1', 'a'], ['button.acc-trigger', { 'aria-controls': 'p2' }, 'B'], ['div#p2', 'b'], ['button.acc-trigger', { 'aria-controls': 'p3' }, 'C'], ['div#p3', 'c']]);
  const t = root.querySelectorAll('.acc-trigger'); if (firstOpen) t[0].setAttribute('aria-expanded', 'true');
  doc.body.appendChild(root); return { root, t, p: ['#p1', '#p2', '#p3'].map((s) => root.querySelector(s)) };
}
test('init all closed', () => { const { root, t, p } = setup(); initAccordion(root); assert.deepEqual(t.map((x) => x.getAttribute('aria-expanded')), ['false', 'false', 'false']); assert.deepEqual(p.map((x) => x.hidden), [true, true, true]); });
test('init keeps open', () => { const { root, t, p } = setup({}, true); initAccordion(root); assert.equal(t[0].getAttribute('aria-expanded'), 'true'); assert.deepEqual(p.map((x) => x.hidden), [false, true, true]); });
test('click opens', () => { const { root, t, p } = setup(); initAccordion(root); t[1].click(); assert.equal(t[1].getAttribute('aria-expanded'), 'true'); assert.equal(p[1].hidden, false); });
test('single mode closes others', () => { const { root, t, p } = setup(); initAccordion(root); t[0].click(); t[1].click(); assert.deepEqual(t.map((x) => x.getAttribute('aria-expanded')), ['false', 'true', 'false']); assert.deepEqual(p.map((x) => x.hidden), [true, false, true]); });
test('click again closes', () => { const { root, t, p } = setup(); initAccordion(root); t[2].click(); t[2].click(); assert.equal(t[2].getAttribute('aria-expanded'), 'false'); assert.equal(p[2].hidden, true); });
test('multiple mode', () => { const { root, t, p } = setup({ 'data-multiple': 'true' }); initAccordion(root); t[0].click(); t[2].click(); assert.deepEqual(p.map((x) => x.hidden), [false, true, false]); t[0].click(); assert.deepEqual(p.map((x) => x.hidden), [true, true, false]); });
test('data-multiple=false is single', () => { const { root, t, p } = setup({ 'data-multiple': 'false' }); initAccordion(root); t[0].click(); t[1].click(); assert.deepEqual(p.map((x) => x.hidden), [true, false, true]); });""")

js("ui-dom-modal-focus", "write", "hard", "dom-component",
   "Implement `createModal(dialog, doc)` in modal.js (`module.exports = { createModal }`). `dialog` is a container element (initially `hidden`), `doc` the document stub. Returns `{ open(), close(), isOpen() }`. `open()`: remember `doc.activeElement` as the opener, remove `hidden`, set `role=\"dialog\"` and `aria-modal=\"true\"`, start listening to `keydown` on the dialog, and focus the first focusable descendant (focusable = `button`, `a[href]`, `input`, `select`, `textarea` or any element with a `tabindex` attribute, excluding ones with a `disabled` attribute or `tabindex=\"-1\"`); if there is none, give the dialog `tabindex=\"-1\"` and focus the dialog. `close()`: hide the dialog, stop listening, and restore focus to the opener (if any). Keys while open: Escape closes (and calls preventDefault); Tab on the LAST focusable (no shift) moves focus to the first with preventDefault; Shift+Tab (event has `shiftKey: true`) on the FIRST moves to the last with preventDefault; if the active element is not one of the focusable items, Tab focuses the first. Opening twice must not register two listeners." + DOMNOTE,
   {"modal.js": stub("createModal")},
   {"modal.js": """const FOCUSABLE = 'button, a[href], input, select, textarea, [tabindex]';
function createModal(dialog, doc) {
  let opener = null, opened = false;
  const items = () => dialog.querySelectorAll(FOCUSABLE).filter((e) => !e.hasAttribute('disabled') && e.getAttribute('tabindex') !== '-1');
  function onKey(e) {
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key !== 'Tab') return;
    const f = items();
    if (!f.length) { e.preventDefault(); return; }
    const a = doc.activeElement, first = f[0], last = f[f.length - 1];
    if (f.indexOf(a) < 0) { e.preventDefault(); first.focus(); }
    else if (e.shiftKey && a === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && a === last) { e.preventDefault(); first.focus(); }
  }
  function open() {
    if (opened) return;
    opened = true; opener = doc.activeElement;
    dialog.hidden = false; dialog.setAttribute('role', 'dialog'); dialog.setAttribute('aria-modal', 'true');
    dialog.addEventListener('keydown', onKey);
    const f = items();
    if (f.length) f[0].focus(); else { dialog.setAttribute('tabindex', '-1'); dialog.focus(); }
  }
  function close() {
    if (!opened) return;
    opened = false; dialog.hidden = true; dialog.removeEventListener('keydown', onKey);
    if (opener && opener.focus) opener.focus();
  }
  return { open, close, isOpen: () => opened };
}
module.exports = { createModal };"""},
   """const { createModal } = require('./modal.js');
function setup(inner) {
  const doc = makeDom();
  const opener = doc.build(['button#opener', 'Open']); doc.body.appendChild(opener);
  const dlg = doc.build(['div#dlg', { hidden: '' }].concat(inner || [['button#a', 'A'], ['input#b'], ['button#c', 'C']]));
  doc.body.appendChild(dlg); opener.focus();
  return { doc, opener, dlg, m: createModal(dlg, doc) };
}
test('open shows, roles, focuses first', () => { const { doc, dlg, m } = setup(); m.open(); assert.equal(dlg.hidden, false); assert.equal(dlg.getAttribute('role'), 'dialog'); assert.equal(dlg.getAttribute('aria-modal'), 'true'); assert.equal(doc.activeElement.id, 'a'); assert.equal(m.isOpen(), true); });
test('close restores focus', () => { const { doc, opener, dlg, m } = setup(); m.open(); m.close(); assert.equal(dlg.hidden, true); assert.equal(doc.activeElement, opener); assert.equal(m.isOpen(), false); });
test('escape closes', () => { const { doc, opener, dlg, m } = setup(); m.open(); const e = key('Escape'); doc.activeElement.dispatchEvent(e); assert.equal(e.defaultPrevented, true); assert.equal(dlg.hidden, true); assert.equal(doc.activeElement, opener); });
test('tab wraps at end', () => { const { doc, dlg, m } = setup(); m.open(); dlg.querySelector('#c').focus(); const e = key('Tab'); dlg.querySelector('#c').dispatchEvent(e); assert.equal(e.defaultPrevented, true); assert.equal(doc.activeElement.id, 'a'); });
test('shift+tab wraps at start', () => { const { doc, dlg, m } = setup(); m.open(); const e = key('Tab', { shiftKey: true }); dlg.querySelector('#a').dispatchEvent(e); assert.equal(e.defaultPrevented, true); assert.equal(doc.activeElement.id, 'c'); });
test('tab in the middle left alone', () => { const { doc, dlg, m } = setup(); m.open(); dlg.querySelector('#b').focus(); const e = key('Tab'); dlg.querySelector('#b').dispatchEvent(e); assert.equal(e.defaultPrevented, false); assert.equal(doc.activeElement.id, 'b'); });
test('disabled and tabindex -1 skipped', () => { const { doc, dlg, m } = setup([['button#x', { disabled: '' }, 'X'], ['button#y', { tabindex: '-1' }], ['a#z', { href: '#' }, 'link'], ['button#w', 'W']]); m.open(); assert.equal(doc.activeElement.id, 'z'); dlg.querySelector('#w').focus(); dlg.querySelector('#w').dispatchEvent(key('Tab')); assert.equal(doc.activeElement.id, 'z'); });
test('no focusables', () => { const { doc, dlg, m } = setup([['p', 'text']]); m.open(); assert.equal(doc.activeElement, dlg); assert.equal(dlg.getAttribute('tabindex'), '-1'); });
test('listeners not doubled / removed after close', () => { const { doc, opener, dlg, m } = setup(); m.open(); m.open(); assert.equal(dlg._l.keydown.length, 1); m.close(); assert.equal((dlg._l.keydown || []).length, 0); m.open(); doc.activeElement.dispatchEvent(key('Escape')); assert.equal(doc.activeElement, opener); });
test('tab with focus outside goes to first', () => { const { doc, dlg, m } = setup(); m.open(); doc.activeElement = dlg; const e = key('Tab'); dlg.dispatchEvent(e); assert.equal(doc.activeElement.id, 'a'); });""")

js("ui-dom-form-validate", "write", "hard", "dom-component",
   "Implement `attachValidation(form)` in validate.js (`module.exports = { attachValidation }`). On the form's `submit` event, check every control with a `required` attribute (use its `.value`, trimmed). Empty -> message 'This field is required'; `type=\"email\"` with a non-empty value that does not look like `x@y.z` -> 'Enter a valid email'. For an invalid control: set `aria-invalid=\"true\"`, make sure an error element exists with id `<control id>-error`, class `error`, text = the message (create a `span` with `form.ownerDocument.createElement` and append it to the control's parent; reuse it if it already exists and update the text), and set `aria-describedby` on the control to that id. For a valid control: remove `aria-invalid` and `aria-describedby` and remove its error element. If anything is invalid call `event.preventDefault()` and `.focus()` the FIRST invalid control. A fully valid form must not be prevented." + DOMNOTE,
   {"validate.js": stub("attachValidation")},
   {"validate.js": """function attachValidation(form) {
  form.addEventListener('submit', (e) => {
    const doc = form.ownerDocument; let first = null;
    for (const f of form.querySelectorAll('[required]')) {
      const v = String(f.value || '').trim();
      let msg = '';
      if (!v) msg = 'This field is required';
      else if (f.getAttribute('type') === 'email' && !/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(v)) msg = 'Enter a valid email';
      const eid = f.id + '-error';
      let err = form.querySelector('#' + eid);
      if (msg) {
        if (!err) { err = doc.createElement('span'); err.id = eid; err.className = 'error'; f.parentNode.appendChild(err); }
        err.textContent = msg;
        f.setAttribute('aria-invalid', 'true'); f.setAttribute('aria-describedby', eid);
        if (!first) first = f;
      } else {
        if (err) err.remove();
        f.removeAttribute('aria-invalid'); f.removeAttribute('aria-describedby');
      }
    }
    if (first) { e.preventDefault(); first.focus(); }
  });
}
module.exports = { attachValidation };"""},
   """const { attachValidation } = require('./validate.js');
function setup(vals) {
  const doc = makeDom();
  const form = doc.build(['form', ['div.f', ['input#name', { required: '' }]], ['div.f', ['input#email', { required: '', type: 'email' }]], ['div.f', ['input#nick']]]);
  doc.body.appendChild(form); attachValidation(form);
  const [n, e, k] = form.querySelectorAll('input'); n.value = vals[0]; e.value = vals[1]; k.value = '';
  return { doc, form, n, e, k };
}
const submit = (form) => { const ev = { type: 'submit' }; form.dispatchEvent(ev); return ev; };
test('valid not prevented', () => { const { form, n } = setup(['Ann', 'a@b.co']); const ev = submit(form); assert.equal(ev.defaultPrevented, false); assert.equal(n.hasAttribute('aria-invalid'), false); assert.equal(form.querySelectorAll('.error').length, 0); });
test('empty required', () => { const { form, n, e } = setup(['  ', 'a@b.co']); const ev = submit(form); assert.equal(ev.defaultPrevented, true); assert.equal(n.getAttribute('aria-invalid'), 'true'); assert.equal(n.getAttribute('aria-describedby'), 'name-error'); assert.equal(form.querySelector('#name-error').textContent, 'This field is required'); assert.equal(form.querySelector('#name-error').className, 'error'); assert.equal(e.hasAttribute('aria-invalid'), false); });
test('error appended in field wrapper', () => { const { form, n } = setup(['', 'a@b.co']); submit(form); assert.equal(form.querySelector('#name-error').parentNode, n.parentNode); });
test('bad email message', () => { const { form, e } = setup(['Ann', 'nope']); submit(form); assert.equal(form.querySelector('#email-error').textContent, 'Enter a valid email'); assert.equal(e.getAttribute('aria-invalid'), 'true'); });
test('focus first invalid', () => { const { doc, form, n } = setup(['', '']); submit(form); assert.equal(doc.activeElement, n); assert.equal(form.querySelectorAll('.error').length, 2); });
test('optional ignored', () => { const { form, k } = setup(['Ann', 'a@b.co']); const ev = submit(form); assert.equal(ev.defaultPrevented, false); assert.equal(k.hasAttribute('aria-invalid'), false); });
test('fix and resubmit clears', () => { const { form, n } = setup(['', 'a@b.co']); submit(form); n.value = 'Ann'; const ev = submit(form); assert.equal(ev.defaultPrevented, false); assert.equal(form.querySelector('#name-error'), null); assert.equal(n.hasAttribute('aria-invalid'), false); assert.equal(n.hasAttribute('aria-describedby'), false); });
test('no duplicate error elements', () => { const { form } = setup(['', 'a@b.co']); submit(form); submit(form); assert.equal(form.querySelectorAll('#name-error').length, 1); });
test('message updates', () => { const { form, e } = setup(['Ann', '']); submit(form); assert.equal(form.querySelector('#email-error').textContent, 'This field is required'); e.value = 'bad'; submit(form); assert.equal(form.querySelector('#email-error').textContent, 'Enter a valid email'); });""")

js("ui-dom-switch", "write", "easy", "dom-component",
   "Implement `initSwitch(button, onChange)` in switch.js (`module.exports = { initSwitch }`). Turn a `<button>` into an accessible toggle: set `role=\"switch\"` and `aria-checked` ('true'/'false', initially from an existing `aria-checked=\"true\"`, else 'false'). Each click flips the state, updates `aria-checked`, toggles the class `on` accordingly, and calls `onChange(newBoolean)` (if given). Clicks are ignored while the button has the `disabled` attribute. Return `{ get(), set(value) }`; `set` updates attribute and class but does NOT call onChange, and does nothing if the value is unchanged." + DOMNOTE,
   {"switch.js": stub("initSwitch")},
   {"switch.js": """function initSwitch(button, onChange) {
  let on = button.getAttribute('aria-checked') === 'true';
  function paint() { button.setAttribute('aria-checked', String(on)); button.classList.toggle('on', on); }
  button.setAttribute('role', 'switch'); paint();
  button.addEventListener('click', () => {
    if (button.hasAttribute('disabled')) return;
    on = !on; paint(); if (onChange) onChange(on);
  });
  return { get: () => on, set(v) { v = !!v; if (v !== on) { on = v; paint(); } } };
}
module.exports = { initSwitch };"""},
   """const { initSwitch } = require('./switch.js');
const mk = (attrs) => { const doc = makeDom(); const b = doc.build(['button', attrs || {}, 'Dark mode']); doc.body.appendChild(b); return b; };
test('init', () => { const b = mk(); initSwitch(b); assert.equal(b.getAttribute('role'), 'switch'); assert.equal(b.getAttribute('aria-checked'), 'false'); assert.equal(b.classList.contains('on'), false); });
test('init on', () => { const b = mk({ 'aria-checked': 'true' }); const s = initSwitch(b); assert.equal(s.get(), true); assert.equal(b.classList.contains('on'), true); });
test('click toggles + callback', () => { const b = mk(); const calls = []; initSwitch(b, (v) => calls.push(v)); b.click(); b.click(); assert.deepEqual(calls, [true, false]); assert.equal(b.getAttribute('aria-checked'), 'false'); });
test('class on', () => { const b = mk(); initSwitch(b); b.click(); assert.equal(b.classList.contains('on'), true); assert.equal(b.getAttribute('aria-checked'), 'true'); });
test('disabled ignored', () => { const b = mk({ disabled: '' }); const calls = []; const s = initSwitch(b, (v) => calls.push(v)); b.click(); assert.deepEqual(calls, []); assert.equal(s.get(), false); });
test('set silent', () => { const b = mk(); const calls = []; const s = initSwitch(b, (v) => calls.push(v)); s.set(true); assert.equal(b.getAttribute('aria-checked'), 'true'); assert.deepEqual(calls, []); s.set(true); assert.equal(s.get(), true); });
test('no callback ok', () => { const b = mk(); initSwitch(b); b.click(); assert.equal(b.getAttribute('aria-checked'), 'true'); });""")

js("ui-dom-sortable-table", "write", "hard", "dom-component",
   "Implement `makeSortable(table)` in sortable.js (`module.exports = { makeSortable }`). Header cells `thead th` that carry a `data-sort` attribute (`'num'` or `'text'`) become sortable: clicking one reorders the `tbody tr` rows by the trimmed text of the cell in the same column index (DOM reordering with appendChild, no cloning). First click on a column sorts ascending; clicking the same column again toggles to descending; clicking another column starts ascending. 'num' compares with parseFloat (a NaN cell compares as equal to everything, so with a stable tiebreak it simply keeps its original relative position), 'text' compares case-insensitively. Ties are broken by the ORIGINAL load order of the rows (stable in both directions). Set `aria-sort=\"ascending\"`/`\"descending\"` on the active th and remove the attribute from the others. Headers without `data-sort` ignore clicks." + DOMNOTE,
   {"sortable.js": stub("makeSortable")},
   {"sortable.js": """function makeSortable(table) {
  const ths = table.querySelectorAll('thead th'), tbody = table.querySelector('tbody');
  const orig = tbody.querySelectorAll('tr');
  let col = -1, dir = 'ascending';
  ths.forEach((th, i) => {
    if (!th.hasAttribute('data-sort')) return;
    th.addEventListener('click', () => {
      dir = col === i && dir === 'ascending' ? 'descending' : 'ascending'; col = i;
      ths.forEach((t) => t.removeAttribute('aria-sort')); th.setAttribute('aria-sort', dir);
      const num = th.getAttribute('data-sort') === 'num';
      const rows = orig.map((r, idx) => ({ r, idx, v: r.children[i].textContent.trim() }));
      rows.sort((a, b) => {
        let c = num ? parseFloat(a.v) - parseFloat(b.v) : a.v.toLowerCase() < b.v.toLowerCase() ? -1 : a.v.toLowerCase() > b.v.toLowerCase() ? 1 : 0;
        if (Number.isNaN(c)) c = 0;
        return (dir === 'ascending' ? c : -c) || a.idx - b.idx;
      });
      rows.forEach((x) => tbody.appendChild(x.r));
    });
  });
}
module.exports = { makeSortable };"""},
   """const { makeSortable } = require('./sortable.js');
function setup() {
  const doc = makeDom();
  const row = (...c) => ['tr'].concat(c.map((x) => ['td', x]));
  const t = doc.build(['table', ['thead', ['tr', ['th', { 'data-sort': 'text' }, 'Name'], ['th', { 'data-sort': 'num' }, 'Qty'], ['th', 'Note']]], ['tbody', row('pear', '10', 'x'), row('Apple', '9', 'y'), row('fig', '9', 'z'), row('Banana', '12', 'w')]]);
  doc.body.appendChild(t); makeSortable(t);
  return { t, th: t.querySelectorAll('th'), names: () => t.querySelectorAll('tbody tr').map((r) => r.children[0].textContent) };
}
test('text asc case-insens', () => { const { th, names } = setup(); th[0].click(); assert.deepEqual(names(), ['Apple', 'Banana', 'fig', 'pear']); });
test('toggle desc', () => { const { th, names } = setup(); th[0].click(); th[0].click(); assert.deepEqual(names(), ['pear', 'fig', 'Banana', 'Apple']); assert.equal(th[0].getAttribute('aria-sort'), 'descending'); });
test('third click back to asc', () => { const { th, names } = setup(); th[0].click(); th[0].click(); th[0].click(); assert.equal(th[0].getAttribute('aria-sort'), 'ascending'); assert.equal(names()[0], 'Apple'); });
test('numeric not lexicographic', () => { const { th, names } = setup(); th[1].click(); assert.deepEqual(names(), ['Apple', 'fig', 'pear', 'Banana']); });
test('stable ties both directions', () => { const { th, names } = setup(); th[1].click(); th[1].click(); assert.deepEqual(names(), ['Banana', 'pear', 'Apple', 'fig']); });
test('aria-sort exclusive', () => { const { th } = setup(); th[0].click(); th[1].click(); assert.equal(th[0].hasAttribute('aria-sort'), false); assert.equal(th[1].getAttribute('aria-sort'), 'ascending'); });
test('new column starts ascending', () => { const { th } = setup(); th[0].click(); th[0].click(); th[1].click(); assert.equal(th[1].getAttribute('aria-sort'), 'ascending'); });
test('unsortable header', () => { const { th, names } = setup(); const before = names(); th[2].click(); assert.deepEqual(names(), before); assert.equal(th[2].hasAttribute('aria-sort'), false); });
test('rows are moved not cloned', () => { const { t, th } = setup(); const rows = t.querySelectorAll('tbody tr'); th[0].click(); const after = t.querySelectorAll('tbody tr'); assert.equal(after.length, 4); assert.ok(rows.every((r) => after.includes(r))); });""")

js("ui-dom-char-counter", "write", "easy", "dom-component",
   "Implement `attachCounter(input, output, max)` in counter.js (`module.exports = { attachCounter }`). Keep `output.textContent` in sync with `input.value.length` on every `input` event and once immediately at attach time. Text: while remaining >= 0, `'N characters left'` (singular `'1 character left'`); when over the limit `'N over limit'` and the output gets class `over`; the `over` class is removed again when back within the limit. The input gets `aria-invalid=\"true\"` while over the limit and the attribute is removed otherwise. Also set `aria-live=\"polite\"` on the output at attach time." + DOMNOTE,
   {"counter.js": stub("attachCounter")},
   {"counter.js": """function attachCounter(input, output, max) {
  output.setAttribute('aria-live', 'polite');
  function update() {
    const left = max - input.value.length;
    output.textContent = left >= 0 ? left + (left === 1 ? ' character left' : ' characters left') : -left + ' over limit';
    output.classList.toggle('over', left < 0);
    if (left < 0) input.setAttribute('aria-invalid', 'true'); else input.removeAttribute('aria-invalid');
  }
  input.addEventListener('input', update);
  update();
}
module.exports = { attachCounter };"""},
   """const { attachCounter } = require('./counter.js');
function setup(v) { const doc = makeDom(); const i = doc.build(['textarea']); const o = doc.build(['span']); doc.body.append(i, o); i.value = v || ''; attachCounter(i, o, 5); return { i, o, type(x) { i.value = x; i.dispatchEvent({ type: 'input' }); } }; }
test('initial', () => { const { o } = setup(); assert.equal(o.textContent, '5 characters left'); assert.equal(o.getAttribute('aria-live'), 'polite'); });
test('initial with value', () => { const { o } = setup('ab'); assert.equal(o.textContent, '3 characters left'); });
test('singular', () => { const { o, type } = setup(); type('abcd'); assert.equal(o.textContent, '1 character left'); });
test('zero', () => { const { o, type } = setup(); type('abcde'); assert.equal(o.textContent, '0 characters left'); assert.equal(o.classList.contains('over'), false); });
test('over', () => { const { i, o, type } = setup(); type('abcdefg'); assert.equal(o.textContent, '2 over limit'); assert.equal(o.classList.contains('over'), true); assert.equal(i.getAttribute('aria-invalid'), 'true'); });
test('back within', () => { const { i, o, type } = setup(); type('abcdefg'); type('abc'); assert.equal(o.textContent, '2 characters left'); assert.equal(o.classList.contains('over'), false); assert.equal(i.hasAttribute('aria-invalid'), false); });""")

js("ui-dom-menu-button", "write", "hard", "dom-component",
   "Implement `initMenu(button, menu)` in menu.js (`module.exports = { initMenu }`). `menu` holds `.item` children. Set `aria-haspopup=\"menu\"` on the button, `role=\"menu\"` on the menu, `role=\"menuitem\"` and `tabindex=\"-1\"` on items. The menu starts closed: `hidden` on the menu, `aria-expanded=\"false\"` on the button. Clicking the button toggles it (keeping `aria-expanded` in sync). Button keydown: ArrowDown opens and focuses the first item, ArrowUp opens and focuses the last item (both preventDefault). Menu keydown (events bubble from items; use `button.ownerDocument.activeElement` to know the current item): ArrowDown/ArrowUp move focus to the next/previous item with wrap-around, Home/End to the first/last, Escape closes the menu and returns focus to the button; handled keys call preventDefault." + DOMNOTE,
   {"menu.js": stub("initMenu")},
   {"menu.js": """function initMenu(button, menu) {
  const doc = button.ownerDocument;
  const items = () => menu.querySelectorAll('.item');
  button.setAttribute('aria-haspopup', 'menu'); menu.setAttribute('role', 'menu');
  items().forEach((i) => { i.setAttribute('role', 'menuitem'); i.setAttribute('tabindex', '-1'); });
  function setOpen(o) { button.setAttribute('aria-expanded', String(o)); menu.hidden = !o; }
  setOpen(false);
  button.addEventListener('click', () => setOpen(menu.hidden));
  button.addEventListener('keydown', (e) => {
    const it = items();
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); it[0].focus(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setOpen(true); it[it.length - 1].focus(); }
  });
  menu.addEventListener('keydown', (e) => {
    const it = items(), n = it.length, i = it.indexOf(doc.activeElement);
    let j = null;
    if (e.key === 'ArrowDown') j = (i + 1) % n;
    else if (e.key === 'ArrowUp') j = (i - 1 + n) % n;
    else if (e.key === 'Home') j = 0;
    else if (e.key === 'End') j = n - 1;
    else if (e.key === 'Escape') { e.preventDefault(); setOpen(false); button.focus(); return; }
    if (j !== null) { e.preventDefault(); it[j].focus(); }
  });
}
module.exports = { initMenu };"""},
   """const { initMenu } = require('./menu.js');
function setup() { const doc = makeDom(); const b = doc.build(['button#b', 'Menu']); const m = doc.build(['ul#m', ['li.item', 'One'], ['li.item', 'Two'], ['li.item', 'Three']]); doc.body.append(b, m); initMenu(b, m); return { doc, b, m, it: m.querySelectorAll('.item') }; }
test('initial state', () => { const { b, m, it } = setup(); assert.equal(m.hidden, true); assert.equal(b.getAttribute('aria-expanded'), 'false'); assert.equal(b.getAttribute('aria-haspopup'), 'menu'); assert.equal(m.getAttribute('role'), 'menu'); it.forEach((i) => { assert.equal(i.getAttribute('role'), 'menuitem'); assert.equal(i.getAttribute('tabindex'), '-1'); }); });
test('click toggles', () => { const { b, m } = setup(); b.click(); assert.equal(m.hidden, false); assert.equal(b.getAttribute('aria-expanded'), 'true'); b.click(); assert.equal(m.hidden, true); assert.equal(b.getAttribute('aria-expanded'), 'false'); });
test('arrow down on button', () => { const { doc, b, m, it } = setup(); const e = key('ArrowDown'); b.dispatchEvent(e); assert.equal(e.defaultPrevented, true); assert.equal(m.hidden, false); assert.equal(doc.activeElement, it[0]); });
test('arrow up on button', () => { const { doc, b, it } = setup(); b.dispatchEvent(key('ArrowUp')); assert.equal(doc.activeElement, it[2]); });
test('arrows in menu wrap', () => { const { doc, b, it } = setup(); b.dispatchEvent(key('ArrowDown')); it[0].dispatchEvent(key('ArrowDown')); assert.equal(doc.activeElement, it[1]); it[1].dispatchEvent(key('ArrowDown')); it[2].dispatchEvent(key('ArrowDown')); assert.equal(doc.activeElement, it[0]); it[0].dispatchEvent(key('ArrowUp')); assert.equal(doc.activeElement, it[2]); });
test('home end', () => { const { doc, b, it } = setup(); b.dispatchEvent(key('ArrowDown')); it[0].dispatchEvent(key('End')); assert.equal(doc.activeElement, it[2]); it[2].dispatchEvent(key('Home')); assert.equal(doc.activeElement, it[0]); });
test('escape closes and refocuses button', () => { const { doc, b, m, it } = setup(); b.dispatchEvent(key('ArrowDown')); const e = key('Escape'); it[0].dispatchEvent(e); assert.equal(e.defaultPrevented, true); assert.equal(m.hidden, true); assert.equal(b.getAttribute('aria-expanded'), 'false'); assert.equal(doc.activeElement, b); });
test('unhandled key not prevented', () => { const { b, it } = setup(); b.dispatchEvent(key('ArrowDown')); const e = key('x'); it[0].dispatchEvent(e); assert.equal(e.defaultPrevented, false); });""")

js("ui-dom-tooltip", "write", "medium", "dom-component",
   "Implement `attachTooltip(trigger, tip, {delay = 300} = {})` in tooltip.js (`module.exports = { attachTooltip }`). `tip` always has an id. Set `role=\"tooltip\"` and `hidden` on the tip; add the tip id to the trigger's `aria-describedby` (keep ids already there, no duplicates, space separated). Pointer: `mouseenter` shows the tip after `delay` ms (global `setTimeout`), `mouseleave` hides it and cancels a pending show. Keyboard: `focus` shows immediately, `blur` hides. `keydown` with key Escape hides it immediately (without preventDefault)." + DOMNOTE,
   {"tooltip.js": stub("attachTooltip")},
   {"tooltip.js": """function attachTooltip(trigger, tip, { delay = 300 } = {}) {
  let t = null;
  tip.setAttribute('role', 'tooltip'); tip.hidden = true;
  const ids = (trigger.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean);
  if (!ids.includes(tip.id)) ids.push(tip.id);
  trigger.setAttribute('aria-describedby', ids.join(' '));
  const show = () => { clearTimeout(t); t = null; tip.hidden = false; };
  const hide = () => { clearTimeout(t); t = null; tip.hidden = true; };
  trigger.addEventListener('mouseenter', () => { clearTimeout(t); t = setTimeout(show, delay); });
  trigger.addEventListener('mouseleave', hide);
  trigger.addEventListener('focus', show);
  trigger.addEventListener('blur', hide);
  trigger.addEventListener('keydown', (e) => { if (e.key === 'Escape') hide(); });
}
module.exports = { attachTooltip };"""},
   """const { attachTooltip } = require('./tooltip.js');
function setup(attrs) { const doc = makeDom(); const b = doc.build(['button', attrs || {}, 'Help']); const t = doc.build(['div#tip', 'Hint']); doc.body.append(b, t); return { b, t }; }
test('setup attrs', () => { const { b, t } = setup(); attachTooltip(b, t); assert.equal(t.getAttribute('role'), 'tooltip'); assert.equal(t.hidden, true); assert.equal(b.getAttribute('aria-describedby'), 'tip'); });
test('keeps existing describedby', () => { const { b, t } = setup({ 'aria-describedby': 'other' }); attachTooltip(b, t); assert.equal(b.getAttribute('aria-describedby'), 'other tip'); });
test('no duplicate id', () => { const { b, t } = setup({ 'aria-describedby': 'tip' }); attachTooltip(b, t); assert.equal(b.getAttribute('aria-describedby'), 'tip'); });
test('hover delay', () => { const c = clock(); const { b, t } = setup(); attachTooltip(b, t, { delay: 200 }); b.dispatchEvent({ type: 'mouseenter' }); c.tick(199); assert.equal(t.hidden, true); c.tick(1); assert.equal(t.hidden, false); c.restore(); });
test('default delay 300', () => { const c = clock(); const { b, t } = setup(); attachTooltip(b, t); b.dispatchEvent({ type: 'mouseenter' }); c.tick(299); assert.equal(t.hidden, true); c.tick(1); assert.equal(t.hidden, false); c.restore(); });
test('leave cancels pending', () => { const c = clock(); const { b, t } = setup(); attachTooltip(b, t); b.dispatchEvent({ type: 'mouseenter' }); c.tick(100); b.dispatchEvent({ type: 'mouseleave' }); c.tick(1000); assert.equal(t.hidden, true); assert.equal(c.pending(), 0); c.restore(); });
test('leave hides', () => { const c = clock(); const { b, t } = setup(); attachTooltip(b, t); b.dispatchEvent({ type: 'mouseenter' }); c.tick(300); b.dispatchEvent({ type: 'mouseleave' }); assert.equal(t.hidden, true); c.restore(); });
test('focus immediate, blur hides', () => { const { b, t } = setup(); attachTooltip(b, t); b.focus(); assert.equal(t.hidden, false); b.dispatchEvent({ type: 'blur' }); assert.equal(t.hidden, true); });
test('escape', () => { const { b, t } = setup(); attachTooltip(b, t); b.focus(); const e = key('Escape'); b.dispatchEvent(e); assert.equal(t.hidden, true); assert.equal(e.defaultPrevented, false); });
test('re-enter restarts timer', () => { const c = clock(); const { b, t } = setup(); attachTooltip(b, t); b.dispatchEvent({ type: 'mouseenter' }); c.tick(200); b.dispatchEvent({ type: 'mouseenter' }); c.tick(200); assert.equal(t.hidden, true); c.tick(100); assert.equal(t.hidden, false); c.restore(); });""")

js("ui-dom-combobox", "write", "hard", "dom-component",
   "Implement `initCombobox(input, list, options)` in combo.js (`module.exports = { initCombobox }`) - an ARIA 1.2 list autocomplete. `list` has an id and starts hidden and empty. Set on the input `role=\"combobox\"`, `aria-autocomplete=\"list\"`, `aria-controls=<list.id>`, `aria-expanded=\"false\"`; on the list `role=\"listbox\"`. On `input` events: filter `options` (strings) by case-insensitive substring of the trimmed input value (blank query -> no results), render each match as an `li` child of the list with `role=\"option\"`, id `<list.id>-opt-<index>`, text = option and `aria-selected=\"false\"`, show the list only when there are matches (`hidden` removed) and keep `aria-expanded` in sync; no option is active. Input keydown: ArrowDown/ArrowUp move the active option (wrapping; ArrowUp from none goes to the last; ArrowDown when closed but results exist reopens), setting `aria-selected=\"true\"` on it only and `aria-activedescendant` on the input to its id (remove the attribute when none); Enter with an active option puts its text into `input.value`, closes the list, clears the active state and prevents default; Escape closes the list and clears active state (preventDefault only if it was open). Clicking an option behaves like choosing it. Re-rendering must replace old options." + DOMNOTE,
   {"combo.js": stub("initCombobox")},
   {"combo.js": """function initCombobox(input, list, options) {
  const doc = input.ownerDocument;
  let shown = [], active = -1;
  input.setAttribute('role', 'combobox'); input.setAttribute('aria-autocomplete', 'list'); input.setAttribute('aria-controls', list.id);
  list.setAttribute('role', 'listbox');
  function setOpen(o) { list.hidden = !o; input.setAttribute('aria-expanded', String(o)); }
  function paint() {
    list.children.slice().forEach((c) => c.remove());
    shown.forEach((o, i) => {
      const li = doc.createElement('li');
      li.setAttribute('role', 'option'); li.id = list.id + '-opt-' + i; li.textContent = o;
      li.setAttribute('aria-selected', String(i === active));
      li.addEventListener('click', () => choose(i));
      list.appendChild(li);
    });
    if (active >= 0) input.setAttribute('aria-activedescendant', list.id + '-opt-' + active); else input.removeAttribute('aria-activedescendant');
  }
  function choose(i) { input.value = shown[i]; active = -1; setOpen(false); paint(); input.dispatchEvent({ type: 'change' }); }
  setOpen(false);
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    shown = q ? options.filter((o) => o.toLowerCase().includes(q)) : [];
    active = -1; paint(); setOpen(shown.length > 0);
  });
  input.addEventListener('keydown', (e) => {
    const n = shown.length;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      if (!n) return;
      e.preventDefault();
      if (list.hidden) setOpen(true);
      active = e.key === 'ArrowDown' ? (active + 1) % n : active < 0 ? n - 1 : (active - 1 + n) % n;
      paint();
    } else if (e.key === 'Enter' && active >= 0 && !list.hidden) { e.preventDefault(); choose(active); }
    else if (e.key === 'Escape') { if (!list.hidden) e.preventDefault(); setOpen(false); active = -1; paint(); }
  });
}
module.exports = { initCombobox };"""},
   """const { initCombobox } = require('./combo.js');
function setup() { const doc = makeDom(); const i = doc.build(['input#q']); const l = doc.build(['ul#lst', { hidden: '' }]); doc.body.append(i, l); initCombobox(i, l, ['Apple', 'Apricot', 'Banana', 'Grape', 'Pineapple']); return { i, l, type(v) { i.value = v; i.dispatchEvent({ type: 'input' }); }, opts: () => l.querySelectorAll('[role=option]') }; }
test('static attrs', () => { const { i, l } = setup(); assert.equal(i.getAttribute('role'), 'combobox'); assert.equal(i.getAttribute('aria-autocomplete'), 'list'); assert.equal(i.getAttribute('aria-controls'), 'lst'); assert.equal(i.getAttribute('aria-expanded'), 'false'); assert.equal(l.getAttribute('role'), 'listbox'); });
test('filter renders options', () => { const { i, l, type, opts } = setup(); type(' AP '); assert.deepEqual(opts().map((o) => o.textContent), ['Apple', 'Apricot', 'Grape', 'Pineapple']); assert.equal(l.hidden, false); assert.equal(i.getAttribute('aria-expanded'), 'true'); assert.equal(opts()[1].id, 'lst-opt-1'); assert.equal(opts()[0].getAttribute('aria-selected'), 'false'); });
test('replaces old options', () => { const { type, opts } = setup(); type('ap'); type('ban'); assert.deepEqual(opts().map((o) => o.textContent), ['Banana']); });
test('no match / blank hides', () => { const { i, l, type, opts } = setup(); type('ap'); type('zzz'); assert.equal(opts().length, 0); assert.equal(l.hidden, true); assert.equal(i.getAttribute('aria-expanded'), 'false'); type('ap'); type('  '); assert.equal(l.hidden, true); });
test('arrow navigation + activedescendant', () => { const { i, type, opts } = setup(); type('ap'); i.dispatchEvent(key('ArrowDown')); assert.equal(i.getAttribute('aria-activedescendant'), 'lst-opt-0'); assert.equal(opts()[0].getAttribute('aria-selected'), 'true'); i.dispatchEvent(key('ArrowDown')); assert.equal(opts()[0].getAttribute('aria-selected'), 'false'); assert.equal(i.getAttribute('aria-activedescendant'), 'lst-opt-1'); });
test('wrapping and ArrowUp from none', () => { const { i, type } = setup(); type('ap'); i.dispatchEvent(key('ArrowUp')); assert.equal(i.getAttribute('aria-activedescendant'), 'lst-opt-3'); i.dispatchEvent(key('ArrowDown')); assert.equal(i.getAttribute('aria-activedescendant'), 'lst-opt-0'); });
test('enter chooses', () => { const { i, l, type } = setup(); type('ap'); i.dispatchEvent(key('ArrowDown')); i.dispatchEvent(key('ArrowDown')); const e = key('Enter'); i.dispatchEvent(e); assert.equal(i.value, 'Apricot'); assert.equal(e.defaultPrevented, true); assert.equal(l.hidden, true); assert.equal(i.hasAttribute('aria-activedescendant'), false); assert.equal(i.getAttribute('aria-expanded'), 'false'); });
test('enter without active ignored', () => { const { i, type } = setup(); type('ap'); const e = key('Enter'); i.dispatchEvent(e); assert.equal(e.defaultPrevented, false); assert.equal(i.value, 'ap'); });
test('escape', () => { const { i, l, type } = setup(); type('ap'); i.dispatchEvent(key('ArrowDown')); const e = key('Escape'); i.dispatchEvent(e); assert.equal(l.hidden, true); assert.equal(e.defaultPrevented, true); assert.equal(i.hasAttribute('aria-activedescendant'), false); const e2 = key('Escape'); i.dispatchEvent(e2); assert.equal(e2.defaultPrevented, false); });
test('reopen with arrow after escape', () => { const { i, l, type } = setup(); type('ap'); i.dispatchEvent(key('Escape')); i.dispatchEvent(key('ArrowDown')); assert.equal(l.hidden, false); assert.equal(i.getAttribute('aria-expanded'), 'true'); });
test('click option', () => { const { i, l, type, opts } = setup(); type('gr'); opts()[0].click(); assert.equal(i.value, 'Grape'); assert.equal(l.hidden, true); });""")
