from tb import js, stub

js("ui-js-listbox-nav", "write", "medium", "keyboard",
   "Implement `nextIndex(current, key, len, opts)` in nav.js (`module.exports = { nextIndex }`) for keyboard navigation of a listbox/menu. `current` is the active index or -1 for none. Keys: ArrowDown (+1), ArrowUp (-1), Home (first enabled), End (last enabled), PageDown (+10), PageUp (-10); any other key returns `current` unchanged. `opts = {wrap = true, disabled = []}`. With wrap, ArrowDown/ArrowUp wrap around the ends; PageUp/PageDown never wrap, they clamp to the first/last enabled item. Disabled indices are skipped (a stepping key moves to the next enabled one in that direction). From -1 ArrowDown goes to the first enabled item and ArrowUp to the last enabled one. If `len` is 0 or every item is disabled, return -1. Without wrap, stepping beyond the ends returns `current`.",
   {"nav.js": stub("nextIndex")},
   {"nav.js": """function nextIndex(cur, key, len, { wrap = true, disabled = [] } = {}) {
  const on = (i) => i >= 0 && i < len && !disabled.includes(i);
  let first = -1, last = -1;
  for (let i = 0; i < len; i++) if (on(i)) { if (first < 0) first = i; last = i; }
  if (first < 0) return -1;
  const step = (dir) => {
    if (cur < 0) return dir > 0 ? first : last;
    for (let k = 1; k <= len; k++) {
      let j = cur + dir * k;
      if (wrap) j = ((j % len) + len) % len; else if (j < 0 || j >= len) return cur;
      if (on(j)) return j;
    }
    return cur;
  };
  const jump = (dir) => {
    let j = Math.min(Math.max((cur < 0 ? (dir > 0 ? -1 : len) : cur) + dir * 10, 0), len - 1);
    for (let k = j; k >= 0 && k < len; k -= dir) if (on(k)) return k;
    return dir > 0 ? last : first;
  };
  switch (key) {
    case 'ArrowDown': return step(1);
    case 'ArrowUp': return step(-1);
    case 'Home': return first;
    case 'End': return last;
    case 'PageDown': return jump(1);
    case 'PageUp': return jump(-1);
    default: return cur;
  }
}
module.exports = { nextIndex };"""},
   """const { nextIndex: n } = require('./nav.js');
test('basic steps', () => { assert.equal(n(0, 'ArrowDown', 3), 1); assert.equal(n(2, 'ArrowUp', 3), 1); });
test('wrap', () => { assert.equal(n(2, 'ArrowDown', 3), 0); assert.equal(n(0, 'ArrowUp', 3), 2); });
test('no wrap', () => { assert.equal(n(2, 'ArrowDown', 3, { wrap: false }), 2); assert.equal(n(0, 'ArrowUp', 3, { wrap: false }), 0); });
test('from none', () => { assert.equal(n(-1, 'ArrowDown', 3), 0); assert.equal(n(-1, 'ArrowUp', 3), 2); assert.equal(n(-1, 'ArrowDown', 3, { disabled: [0] }), 1); });
test('skip disabled', () => { assert.equal(n(0, 'ArrowDown', 4, { disabled: [1, 2] }), 3); assert.equal(n(3, 'ArrowDown', 4, { disabled: [0, 1, 2] }), 3); assert.equal(n(3, 'ArrowDown', 4, { disabled: [0, 1] }), 2); });
test('skip disabled backwards wrap', () => assert.equal(n(0, 'ArrowUp', 4, { disabled: [3] }), 2));
test('home end', () => { assert.equal(n(2, 'Home', 5, { disabled: [0] }), 1); assert.equal(n(2, 'End', 5, { disabled: [4] }), 3); });
test('page', () => { assert.equal(n(0, 'PageDown', 30), 10); assert.equal(n(25, 'PageDown', 30), 29); assert.equal(n(12, 'PageUp', 30), 2); assert.equal(n(3, 'PageUp', 30), 0); });
test('page with disabled', () => { assert.equal(n(0, 'PageDown', 30, { disabled: [10, 11] }), 9); assert.equal(n(25, 'PageUp', 30, { disabled: [15] }), 16); });
test('empty/all disabled', () => { assert.equal(n(-1, 'ArrowDown', 0), -1); assert.equal(n(0, 'Home', 2, { disabled: [0, 1] }), -1); });
test('other key', () => assert.equal(n(1, 'a', 3), 1));""")

js("ui-js-virtual-range", "write", "easy", "layout",
   "Implement `visibleRange({scrollTop, viewportHeight, itemHeight, total, overscan = 3})` in virtual.js (`module.exports = { visibleRange }`) for a virtualised list. Return `{start, end, offsetTop, totalHeight}` where `start` (inclusive) = max(0, floor(scrollTop/itemHeight) - overscan), `end` (exclusive) = min(total, ceil((scrollTop+viewportHeight)/itemHeight) + overscan), `offsetTop = start*itemHeight`, `totalHeight = total*itemHeight`. Negative scrollTop counts as 0. total 0 gives start 0, end 0. `itemHeight <= 0` throws RangeError.",
   {"virtual.js": stub("visibleRange")},
   {"virtual.js": """function visibleRange({ scrollTop, viewportHeight, itemHeight, total, overscan = 3 }) {
  if (!(itemHeight > 0)) throw new RangeError('itemHeight');
  const top = Math.max(0, scrollTop);
  const start = Math.min(Math.max(0, Math.floor(top / itemHeight) - overscan), total);
  const end = Math.min(total, Math.ceil((top + viewportHeight) / itemHeight) + overscan);
  return { start, end: Math.max(start, end), offsetTop: start * itemHeight, totalHeight: total * itemHeight };
}
module.exports = { visibleRange };"""},
   """const { visibleRange: v } = require('./virtual.js');
test('top', () => assert.deepEqual(v({ scrollTop: 0, viewportHeight: 100, itemHeight: 20, total: 1000 }), { start: 0, end: 8, offsetTop: 0, totalHeight: 20000 }));
test('middle', () => assert.deepEqual(v({ scrollTop: 400, viewportHeight: 100, itemHeight: 20, total: 1000 }), { start: 17, end: 28, offsetTop: 340, totalHeight: 20000 }));
test('partial row', () => assert.deepEqual(v({ scrollTop: 410, viewportHeight: 95, itemHeight: 20, total: 1000, overscan: 0 }), { start: 20, end: 26, offsetTop: 400, totalHeight: 20000 }));
test('bottom clamp', () => { const r = v({ scrollTop: 99900, viewportHeight: 100, itemHeight: 20, total: 5000 }); assert.equal(r.end, 5000); });
test('negative scroll', () => assert.equal(v({ scrollTop: -50, viewportHeight: 40, itemHeight: 20, total: 10, overscan: 0 }).start, 0));
test('empty', () => assert.deepEqual(v({ scrollTop: 0, viewportHeight: 100, itemHeight: 20, total: 0 }), { start: 0, end: 0, offsetTop: 0, totalHeight: 0 }));
test('overscroll past end', () => { const r = v({ scrollTop: 5000, viewportHeight: 100, itemHeight: 20, total: 10 }); assert.ok(r.start <= r.end && r.end === 10 && r.start <= 10); });
test('bad height', () => assert.throws(() => v({ scrollTop: 0, viewportHeight: 1, itemHeight: 0, total: 1 }), RangeError));""")

js("ui-js-star-fill", "write", "easy", "components",
   "Implement `starFill(rating, max = 5)` in stars.js (`module.exports = { starFill }`) returning an array of `max` strings 'full' | 'half' | 'empty' for a star-rating display. The rating is first clamped to [0, max] and rounded to the nearest 0.5 (halves round up: 3.25 -> 3.5, 3.75 -> 4); NaN counts as 0. Example: starFill(3.5) -> ['full','full','full','half','empty'].",
   {"stars.js": stub("starFill")},
   {"stars.js": """function starFill(rating, max = 5) {
  let r = Number.isFinite(rating) ? Math.min(Math.max(rating, 0), max) : 0;
  r = Math.round(r * 2) / 2;
  return Array.from({ length: max }, (_, i) => (r >= i + 1 ? 'full' : r >= i + 0.5 ? 'half' : 'empty'));
}
module.exports = { starFill };"""},
   """const { starFill: s } = require('./stars.js');
test('half', () => assert.deepEqual(s(3.5), ['full', 'full', 'full', 'half', 'empty']));
test('zero', () => assert.deepEqual(s(0), ['empty', 'empty', 'empty', 'empty', 'empty']));
test('full', () => assert.deepEqual(s(5), ['full', 'full', 'full', 'full', 'full']));
test('rounding', () => { assert.deepEqual(s(3.25).slice(3, 4), ['half']); assert.deepEqual(s(3.75).slice(3, 4), ['full']); assert.deepEqual(s(3.2).slice(3, 4), ['empty']); });
test('clamp', () => { assert.deepEqual(s(9), s(5)); assert.deepEqual(s(-2), s(0)); assert.deepEqual(s(NaN), s(0)); });
test('custom max', () => assert.deepEqual(s(1.5, 3), ['full', 'half', 'empty']));""")

js("ui-js-tooltip-position", "write", "hard", "layout",
   "Implement `computePosition(anchor, tip, viewport, opts)` in pos.js (`module.exports = { computePosition }`) for a tooltip/popover. `anchor = {x, y, width, height}`, `tip = {width, height}`, `viewport = {width, height}`, `opts = {placement = 'top', gap = 8, margin = 4}`. Placement 'top'/'bottom' centre the tip horizontally on the anchor and put it above (y = anchor.y - tip.height - gap) / below (y = anchor.y + anchor.height + gap); 'left'/'right' centre it vertically and put it left (x = anchor.x - tip.width - gap) / right (x = anchor.x + anchor.width + gap). If the preferred side does not fit inside the viewport (respecting `margin` on that side) but the opposite side does, flip to the opposite side; if neither fits keep the preferred one. After placing, clamp the position so the tip stays within [margin, viewport - size - margin] on both axes (if the tip is larger than the space, the min bound wins). Return `{x, y, placement}` where placement is the final side.",
   {"pos.js": stub("computePosition")},
   {"pos.js": """function computePosition(a, t, vp, { placement = 'top', gap = 8, margin = 4 } = {}) {
  const at = (p) => {
    switch (p) {
      case 'top': return { x: a.x + a.width / 2 - t.width / 2, y: a.y - t.height - gap };
      case 'bottom': return { x: a.x + a.width / 2 - t.width / 2, y: a.y + a.height + gap };
      case 'left': return { x: a.x - t.width - gap, y: a.y + a.height / 2 - t.height / 2 };
      default: return { x: a.x + a.width + gap, y: a.y + a.height / 2 - t.height / 2 };
    }
  };
  const fits = (p) => {
    const q = at(p);
    if (p === 'top') return q.y >= margin;
    if (p === 'bottom') return q.y + t.height <= vp.height - margin;
    if (p === 'left') return q.x >= margin;
    return q.x + t.width <= vp.width - margin;
  };
  const opp = { top: 'bottom', bottom: 'top', left: 'right', right: 'left' };
  let p = placement;
  if (!fits(p) && fits(opp[p])) p = opp[p];
  const q = at(p);
  const clamp = (v, size, max) => Math.max(margin, Math.min(v, max - size - margin));
  return { x: clamp(q.x, t.width, vp.width), y: clamp(q.y, t.height, vp.height), placement: p };
}
module.exports = { computePosition };"""},
   """const { computePosition: c } = require('./pos.js');
const vp = { width: 800, height: 600 }, tip = { width: 100, height: 40 };
test('top centred', () => assert.deepEqual(c({ x: 300, y: 300, width: 80, height: 20 }, tip, vp), { x: 290, y: 252, placement: 'top' }));
test('bottom', () => assert.deepEqual(c({ x: 300, y: 300, width: 80, height: 20 }, tip, vp, { placement: 'bottom' }), { x: 290, y: 328, placement: 'bottom' }));
test('right and left', () => {
  assert.deepEqual(c({ x: 300, y: 300, width: 80, height: 20 }, tip, vp, { placement: 'right' }), { x: 388, y: 290, placement: 'right' });
  assert.deepEqual(c({ x: 300, y: 300, width: 80, height: 20 }, tip, vp, { placement: 'left' }), { x: 192, y: 290, placement: 'left' });
});
test('flip top to bottom', () => assert.deepEqual(c({ x: 300, y: 20, width: 80, height: 20 }, tip, vp), { x: 290, y: 48, placement: 'bottom' }));
test('flip bottom to top', () => assert.deepEqual(c({ x: 300, y: 560, width: 80, height: 20 }, tip, vp, { placement: 'bottom' }), { x: 290, y: 512, placement: 'top' }));
test('flip right to left', () => assert.equal(c({ x: 700, y: 300, width: 80, height: 20 }, tip, vp, { placement: 'right' }).placement, 'left'));
test('no flip when neither fits', () => assert.equal(c({ x: 300, y: 5, width: 10, height: 590 }, tip, { width: 800, height: 600 }).placement, 'top'));
test('clamp x', () => { assert.equal(c({ x: 0, y: 300, width: 20, height: 20 }, tip, vp).x, 4); assert.equal(c({ x: 790, y: 300, width: 10, height: 20 }, tip, vp).x, 696); });
test('clamp y for side placement', () => assert.equal(c({ x: 300, y: 0, width: 80, height: 10 }, tip, vp, { placement: 'right' }).y, 4));
test('options', () => assert.deepEqual(c({ x: 300, y: 300, width: 80, height: 20 }, tip, vp, { gap: 0, margin: 0 }), { x: 290, y: 260, placement: 'top' }));""")

js("ui-js-masonry", "write", "easy", "layout",
   "Implement `assignColumns(heights, n)` in masonry.js (`module.exports = { assignColumns }`). Distribute items (given by their heights, in order) into `n` columns, always putting the next item into the currently shortest column; ties go to the lowest column index. Return `{columns, totals}` where columns is an array of n arrays of item indices and totals the summed height per column. n < 1 or non-integer throws RangeError.",
   {"masonry.js": stub("assignColumns")},
   {"masonry.js": """function assignColumns(heights, n) {
  if (!Number.isInteger(n) || n < 1) throw new RangeError('n');
  const columns = Array.from({ length: n }, () => []), totals = new Array(n).fill(0);
  heights.forEach((h, i) => {
    let best = 0;
    for (let c = 1; c < n; c++) if (totals[c] < totals[best]) best = c;
    columns[best].push(i); totals[best] += h;
  });
  return { columns, totals };
}
module.exports = { assignColumns };"""},
   """const { assignColumns: a } = require('./masonry.js');
test('basic', () => assert.deepEqual(a([100, 50, 50, 80], 2), { columns: [[0, 3], [1, 2]], totals: [180, 100] }));
test('ties lowest', () => assert.deepEqual(a([10, 10, 10, 10], 3), { columns: [[0, 3], [1], [2]], totals: [20, 10, 10] }));
test('one col', () => assert.deepEqual(a([1, 2, 3], 1), { columns: [[0, 1, 2]], totals: [6] }));
test('empty', () => assert.deepEqual(a([], 2), { columns: [[], []], totals: [0, 0] }));
test('bad n', () => { assert.throws(() => a([1], 0), RangeError); assert.throws(() => a([1], 1.5), RangeError); });""")

js("ui-js-month-grid", "write", "hard", "dates",
   "Implement `getMonthGrid(year, month, weekStart = 0)` in cal.js (`module.exports = { getMonthGrid }`) for a calendar widget. `month` is 0-11, `weekStart` 0 = Sunday ... 6 = Saturday. Return an array of weeks; each week is 7 cells `{date: 'YYYY-MM-DD', day: <number>, inMonth: <boolean>}`. The grid starts on the first `weekStart` day on or before the 1st of the month and ends on the last day-of-week before the next week start after the last of the month, so it contains only as many weeks as needed (4 to 6). Leading/trailing cells are the neighbouring months' days with inMonth false. Use UTC arithmetic only (no local time).",
   {"cal.js": stub("getMonthGrid")},
   {"cal.js": """function getMonthGrid(year, month, weekStart = 0) {
  const first = new Date(Date.UTC(year, month, 1));
  const lead = (first.getUTCDay() - weekStart + 7) % 7;
  const dim = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
  const weeks = Math.ceil((lead + dim) / 7);
  const out = [];
  for (let w = 0; w < weeks; w++) {
    const row = [];
    for (let d = 0; d < 7; d++) {
      const dt = new Date(Date.UTC(year, month, 1 - lead + w * 7 + d));
      row.push({ date: dt.toISOString().slice(0, 10), day: dt.getUTCDate(), inMonth: dt.getUTCMonth() === ((month % 12) + 12) % 12 });
    }
    out.push(row);
  }
  return out;
}
module.exports = { getMonthGrid };"""},
   """const { getMonthGrid: g } = require('./cal.js');
const flat = (w) => w.map((r) => r.map((c) => c.date));
test('feb 2026 starts sunday is 4 weeks', () => { const w = g(2026, 1); assert.equal(w.length, 4); assert.equal(w[0][0].date, '2026-02-01'); assert.equal(w[3][6].date, '2026-02-28'); assert.ok(w.flat().every((c) => c.inMonth)); });
test('march 2024 sunday start', () => { const w = g(2024, 2); assert.equal(w.length, 6); assert.deepEqual(w[0].map((c) => c.date), ['2024-02-25', '2024-02-26', '2024-02-27', '2024-02-28', '2024-02-29', '2024-03-01', '2024-03-02']); assert.deepEqual(w[0].map((c) => c.inMonth), [false, false, false, false, false, true, true]); assert.equal(w[5][6].date, '2024-04-06'); assert.equal(w[5][6].inMonth, false); });
test('monday start', () => { const w = g(2024, 2, 1); assert.equal(w[0][0].date, '2024-02-26'); assert.equal(w[0][5].date, '2024-03-02'); assert.equal(w.length, 5); assert.equal(w[4][6].date, '2024-03-31'); });
test('day field', () => { const c = g(2024, 2)[0][4]; assert.deepEqual(c, { date: '2024-02-29', day: 29, inMonth: false }); });
test('every week has 7', () => { for (let m = 0; m < 12; m++) for (const ws of [0, 1, 6]) { const w = g(2025, m, ws); assert.ok(w.length >= 4 && w.length <= 6); assert.ok(w.every((r) => r.length === 7)); } });
test('december/january boundaries', () => { const w = g(2024, 11); assert.equal(w[w.length - 1][6].date, '2025-01-04'); const j = g(2025, 0); assert.equal(j[0][0].date, '2024-12-29'); });
test('consecutive days', () => { const f = flat(g(2023, 6, 3)).flat(); for (let i = 1; i < f.length; i++) assert.equal(new Date(f[i]) - new Date(f[i - 1]), 86400000); });
test('weekStart saturday', () => assert.equal(g(2024, 2, 6)[0][0].date, '2024-02-24'));""")

js("ui-js-date-utils", "write", "medium", "dates",
   "Implement UTC date helpers in dateutil.js (`module.exports = { addDays, isSameDay, daysBetween, startOfWeek, isWeekend }`). All use UTC fields. `addDays(date, n)` returns a NEW Date n days later (n may be negative or large; the input is not mutated). `isSameDay(a, b)` compares UTC year/month/day. `daysBetween(a, b)` = number of whole calendar days from a to b (UTC dates, ignoring time of day; negative if b is earlier). `startOfWeek(date, weekStart = 0)` returns a new Date at 00:00:00.000 UTC of the most recent weekStart day (0 = Sunday) on or before date. `isWeekend(date)` is true for Saturday and Sunday.",
   {"dateutil.js": stub("addDays", "isSameDay", "daysBetween", "startOfWeek", "isWeekend")},
   {"dateutil.js": """const DAY = 86400000;
const day0 = (d) => Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
function addDays(d, n) { const r = new Date(d.getTime()); r.setUTCDate(r.getUTCDate() + n); return r; }
function isSameDay(a, b) { return day0(a) === day0(b); }
function daysBetween(a, b) { return Math.round((day0(b) - day0(a)) / DAY); }
function startOfWeek(d, weekStart = 0) { const back = (d.getUTCDay() - weekStart + 7) % 7; return new Date(day0(d) - back * DAY); }
function isWeekend(d) { const x = d.getUTCDay(); return x === 0 || x === 6; }
module.exports = { addDays, isSameDay, daysBetween, startOfWeek, isWeekend };"""},
   """const u = require('./dateutil.js');
const D = (s) => new Date(s);
test('addDays', () => { const d = D('2024-02-28T10:00:00Z'); assert.equal(u.addDays(d, 2).toISOString(), '2024-03-01T10:00:00.000Z'); assert.equal(d.toISOString(), '2024-02-28T10:00:00.000Z'); assert.equal(u.addDays(d, -28).toISOString(), '2024-01-31T10:00:00.000Z'); assert.equal(u.addDays(d, 366).toISOString(), '2025-02-28T10:00:00.000Z'); });
test('isSameDay', () => { assert.equal(u.isSameDay(D('2024-05-01T00:00:00Z'), D('2024-05-01T23:59:59Z')), true); assert.equal(u.isSameDay(D('2024-05-01T23:59:59Z'), D('2024-05-02T00:00:00Z')), false); assert.equal(u.isSameDay(D('2024-05-01Z'), D('2023-05-01Z')), false); });
test('daysBetween', () => { assert.equal(u.daysBetween(D('2024-05-01T23:00:00Z'), D('2024-05-02T01:00:00Z')), 1); assert.equal(u.daysBetween(D('2024-03-01Z'), D('2024-02-01Z')), -29); assert.equal(u.daysBetween(D('2024-05-01T08:00:00Z'), D('2024-05-01T20:00:00Z')), 0); });
test('startOfWeek', () => { const w = D('2024-05-15T13:45:10Z'); assert.equal(u.startOfWeek(w).toISOString(), '2024-05-12T00:00:00.000Z'); assert.equal(u.startOfWeek(w, 1).toISOString(), '2024-05-13T00:00:00.000Z'); assert.equal(u.startOfWeek(D('2024-05-13T00:00:00Z'), 1).toISOString(), '2024-05-13T00:00:00.000Z'); assert.equal(u.startOfWeek(D('2024-05-12T05:00:00Z'), 1).toISOString(), '2024-05-06T00:00:00.000Z'); });
test('isWeekend', () => { assert.equal(u.isWeekend(D('2024-05-11T12:00:00Z')), true); assert.equal(u.isWeekend(D('2024-05-12T12:00:00Z')), true); assert.equal(u.isWeekend(D('2024-05-13T12:00:00Z')), false); });""")

js("ui-js-contrast", "write", "medium", "a11y",
   "Implement WCAG colour contrast helpers in contrast.js (`module.exports = { contrastRatio, passesAA }`). `contrastRatio(fg, bg)` takes hex colours '#rgb' or '#rrggbb' (with or without '#', any case) and returns the WCAG 2.x ratio (L1+0.05)/(L2+0.05) with L1 the lighter relative luminance; sRGB channels are linearised with c <= 0.03928 ? c/12.92 : ((c+0.055)/1.055)^2.4. `passesAA(fg, bg, {large = false})` is true when the ratio is >= 4.5 (>= 3 for large text). Invalid colour strings throw a TypeError.",
   {"contrast.js": stub("contrastRatio", "passesAA")},
   {"contrast.js": """function parse(h) {
  const m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(String(h).trim());
  if (!m) throw new TypeError('bad colour');
  let s = m[1]; if (s.length === 3) s = s.split('').map((c) => c + c).join('');
  return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16));
}
function lum([r, g, b]) {
  const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
function contrastRatio(fg, bg) {
  const a = lum(parse(fg)), b = lum(parse(bg));
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}
function passesAA(fg, bg, { large = false } = {}) { return contrastRatio(fg, bg) >= (large ? 3 : 4.5); }
module.exports = { contrastRatio, passesAA };"""},
   """const { contrastRatio: c, passesAA: p } = require('./contrast.js');
test('black on white', () => assert.equal(Math.round(c('#000', '#fff') * 100) / 100, 21));
test('same', () => assert.equal(c('#abcdef', '#ABCDEF'), 1));
test('order independent', () => assert.equal(c('#fff', '#000'), c('#000', '#fff')));
test('known', () => { assert.equal(c('#777777', '#ffffff').toFixed(2), '4.48'); assert.equal(c('#767676', '#fff').toFixed(2), '4.54'); });
test('no hash short', () => assert.equal(c('fff', '000').toFixed(1), '21.0'));
test('AA normal', () => { assert.equal(p('#777', '#fff'), false); assert.equal(p('#767676', '#fff'), true); });
test('AA large', () => { assert.equal(p('#777', '#fff', { large: true }), true); assert.equal(p('#999', '#fff', { large: true }), false); });
test('invalid', () => { assert.throws(() => c('#12', '#fff'), TypeError); assert.throws(() => c('red', '#fff'), TypeError); });""")

js("ui-js-color-utils", "write", "easy", "colors",
   "Implement colour helpers in color.js (`module.exports = { hexToRgb, rgbToHex, lighten }`). `hexToRgb('#abc' | 'aabbcc' | '#AABBCC')` returns `[r, g, b]`; invalid input returns null. `rgbToHex(r, g, b)` rounds and clamps each channel to 0..255 and returns lowercase '#rrggbb'. `lighten(hex, amount)` mixes the colour towards white by `amount` (0..1, clamped): channel = round(c + (255 - c) * amount); returns '#rrggbb' lowercase, null for invalid hex.",
   {"color.js": stub("hexToRgb", "rgbToHex", "lighten")},
   {"color.js": """function hexToRgb(h) {
  const m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(String(h).trim());
  if (!m) return null;
  let s = m[1]; if (s.length === 3) s = s.split('').map((c) => c + c).join('');
  return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16));
}
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map((v) => Math.min(255, Math.max(0, Math.round(v))).toString(16).padStart(2, '0')).join('');
}
function lighten(hex, amount) {
  const rgb = hexToRgb(hex); if (!rgb) return null;
  const a = Math.min(1, Math.max(0, amount));
  return rgbToHex(...rgb.map((c) => c + (255 - c) * a));
}
module.exports = { hexToRgb, rgbToHex, lighten };"""},
   """const { hexToRgb: h, rgbToHex: x, lighten: l } = require('./color.js');
test('hexToRgb', () => { assert.deepEqual(h('#abc'), [170, 187, 204]); assert.deepEqual(h('FF8000'), [255, 128, 0]); assert.equal(h('#12'), null); assert.equal(h('#gggggg'), null); });
test('rgbToHex', () => { assert.equal(x(255, 128, 0), '#ff8000'); assert.equal(x(0, 0, 0), '#000000'); assert.equal(x(300, -5, 7.6), '#ff0008'); });
test('lighten', () => { assert.equal(l('#000000', 0.5), '#808080'); assert.equal(l('#ff0000', 1), '#ffffff'); assert.equal(l('#336699', 0), '#336699'); assert.equal(l('#000', 2), '#ffffff'); assert.equal(l('nope', 0.5), null); });
test('roundtrip', () => assert.equal(x(...h('#1a2b3c')), '#1a2b3c'));""")

js("ui-js-autocomplete-rank", "write", "medium", "components",
   "Implement `rankSuggestions(items, query, limit = 5)` in suggest.js (`module.exports = { rankSuggestions }`). `items` are strings. Return up to `limit` items matching `query` (trimmed, case-insensitive substring), ordered by score: 0 exact match, 1 starts with the query, 2 a word inside starts with the query (word = after a space, '-' or '_'), 3 contains it elsewhere; ties are broken by shorter length, then alphabetically (case-insensitive, then original). Duplicates (case-insensitive) are listed once (keep the first). A blank query returns [].",
   {"suggest.js": stub("rankSuggestions")},
   {"suggest.js": """function rankSuggestions(items, query, limit = 5) {
  const q = String(query).trim().toLowerCase();
  if (!q) return [];
  const seen = new Set(), scored = [];
  for (const it of items) {
    const l = it.toLowerCase();
    if (seen.has(l) || !l.includes(q)) continue;
    seen.add(l);
    const score = l === q ? 0 : l.startsWith(q) ? 1 : new RegExp('[ _-]' + q.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')).test(l) ? 2 : 3;
    scored.push({ it, l, score });
  }
  scored.sort((a, b) => a.score - b.score || a.l.length - b.l.length || (a.l < b.l ? -1 : a.l > b.l ? 1 : 0) || (a.it < b.it ? -1 : a.it > b.it ? 1 : 0));
  return scored.slice(0, limit).map((s) => s.it);
}
module.exports = { rankSuggestions };"""},
   """const { rankSuggestions: r } = require('./suggest.js');
const items = ['New York', 'York', 'Yorkshire', 'Port-York', 'Newark', 'new york', 'Pyork', 'Yo'];
test('ranking', () => assert.deepEqual(r(items, 'york'), ['York', 'Yorkshire', 'New York', 'Port-York', 'Pyork']));
test('dedupe case-insens keeps first', () => assert.deepEqual(r(['New York', 'new york'], 'new'), ['New York']));
test('limit', () => assert.deepEqual(r(items, 'york', 2), ['York', 'Yorkshire']));
test('trim + case', () => assert.equal(r(['Apple'], '  APP ')[0], 'Apple'));
test('blank', () => { assert.deepEqual(r(items, ''), []); assert.deepEqual(r(items, '   '), []); });
test('no match', () => assert.deepEqual(r(items, 'zzz'), []));
test('regex chars', () => assert.deepEqual(r(['a.b', 'axb'], 'a.'), ['a.b']));
test('tie alphabetical', () => assert.deepEqual(r(['bb1', 'aa1', 'Ab1'], '1', 3), ['aa1', 'Ab1', 'bb1']));""")

js("ui-js-form-diff", "write", "easy", "forms",
   "Implement `diffValues(initial, current)` in dirty.js (`module.exports = { diffValues }`) for form dirty tracking. Return `{changed, dirty}` where `changed` is the alphabetically sorted list of keys (from either object) whose values differ and `dirty` is `changed.length > 0`. Primitives compare with ===; arrays compare element-wise with ===; a key missing on one side counts as different from any value on the other side (including undefined only if the key is missing - a present key with value undefined equals a missing key).",
   {"dirty.js": stub("diffValues")},
   {"dirty.js": """function same(a, b) {
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((x, i) => x === b[i]);
  return a === b;
}
function diffValues(initial, current) {
  const keys = new Set([...Object.keys(initial), ...Object.keys(current)]);
  const changed = [...keys].filter((k) => !same(initial[k], current[k])).sort();
  return { changed, dirty: changed.length > 0 };
}
module.exports = { diffValues };"""},
   """const { diffValues: d } = require('./dirty.js');
test('clean', () => assert.deepEqual(d({ a: 1, b: 'x' }, { a: 1, b: 'x' }), { changed: [], dirty: false }));
test('changed sorted', () => assert.deepEqual(d({ b: 1, a: 1, c: 1 }, { b: 2, a: 2, c: 1 }), { changed: ['a', 'b'], dirty: true }));
test('arrays', () => { assert.deepEqual(d({ t: ['a', 'b'] }, { t: ['a', 'b'] }).changed, []); assert.deepEqual(d({ t: ['a', 'b'] }, { t: ['b', 'a'] }).changed, ['t']); assert.deepEqual(d({ t: ['a'] }, { t: ['a', 'b'] }).changed, ['t']); });
test('added/removed keys', () => assert.deepEqual(d({ a: 1 }, { b: 1 }).changed, ['a', 'b']));
test('type strictness', () => assert.deepEqual(d({ n: 1 }, { n: '1' }).changed, ['n']));
test('undefined equals missing', () => assert.deepEqual(d({ a: undefined }, {}).changed, []));
test('empty string differs from missing', () => assert.deepEqual(d({}, { a: '' }).changed, ['a']));""")

js("ui-js-safe-storage", "write", "medium", "utilities",
   "Implement `createStorage(store, prefix = '')` in storage.js (`module.exports = { createStorage }`), a safe JSON wrapper around a Web-Storage-like object (`getItem`, `setItem`, `removeItem`, and `length`/`key(i)` for enumeration). Methods: `get(key, fallback = null)` returns the parsed JSON value, or `fallback` when the key is missing, the stored text is invalid JSON, or the store throws; `set(key, value)` stores JSON and returns true, or returns false if the store throws (quota/private mode) or the value cannot be serialised (circular, undefined); `remove(key)` never throws; `keys()` returns the un-prefixed keys that start with the prefix (in store order). Real keys are `prefix + key`.",
   {"storage.js": stub("createStorage")},
   {"storage.js": """function createStorage(store, prefix = '') {
  return {
    get(key, fallback = null) {
      try { const raw = store.getItem(prefix + key); return raw === null || raw === undefined ? fallback : JSON.parse(raw); } catch (e) { return fallback; }
    },
    set(key, value) {
      try { const s = JSON.stringify(value); if (s === undefined) return false; store.setItem(prefix + key, s); return true; } catch (e) { return false; }
    },
    remove(key) { try { store.removeItem(prefix + key); } catch (e) { /* ignore */ } },
    keys() {
      const out = [];
      try { for (let i = 0; i < store.length; i++) { const k = store.key(i); if (k && k.startsWith(prefix)) out.push(k.slice(prefix.length)); } } catch (e) { /* ignore */ }
      return out;
    },
  };
}
module.exports = { createStorage };"""},
   """const { createStorage: mk } = require('./storage.js');
const mem = () => { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), get length() { return m.size; }, key: (i) => [...m.keys()][i] ?? null, _m: m }; };
test('roundtrip', () => { const s = mk(mem(), 'app:'); assert.equal(s.set('a', { x: [1, 2] }), true); assert.deepEqual(s.get('a'), { x: [1, 2] }); });
test('prefix used', () => { const m = mem(); mk(m, 'p.').set('k', 1); assert.equal(m.getItem('p.k'), '1'); });
test('fallback missing', () => { const s = mk(mem()); assert.equal(s.get('x'), null); assert.equal(s.get('x', 5), 5); });
test('false/0 values survive', () => { const s = mk(mem()); s.set('f', false); s.set('z', 0); assert.equal(s.get('f', 'fb'), false); assert.equal(s.get('z', 'fb'), 0); });
test('invalid json -> fallback', () => { const m = mem(); m.setItem('bad', '{oops'); assert.equal(mk(m).get('bad', 'fb'), 'fb'); });
test('quota error', () => { const m = mem(); m.setItem = () => { throw new Error('quota'); }; assert.equal(mk(m).set('a', 1), false); });
test('unserialisable', () => { const s = mk(mem()); const o = {}; o.self = o; assert.equal(s.set('c', o), false); assert.equal(s.set('u', undefined), false); });
test('throwing getItem', () => { const m = mem(); m.getItem = () => { throw new Error('denied'); }; assert.equal(mk(m).get('a', 'fb'), 'fb'); });
test('remove never throws', () => { const m = mem(); m.removeItem = () => { throw new Error('x'); }; mk(m).remove('a'); });
test('keys', () => { const m = mem(); m.setItem('other', '1'); const s = mk(m, 'p:'); s.set('a', 1); s.set('b', 2); assert.deepEqual(s.keys(), ['a', 'b']); });""")

js("ui-js-media-query", "write", "hard", "responsive",
   "Implement `matchesMedia(query, width)` in mq.js (`module.exports = { matchesMedia }`), a tiny evaluator for media queries against a viewport width in px. Supported: `(min-width: Npx)`, `(max-width: Npx)` (inclusive comparisons), conditions joined with `and`, alternatives joined with a comma (OR), an optional leading `screen` or `all` media type, case-insensitive, flexible whitespace. Any query containing a feature or media type it does not understand (e.g. `print`, `(orientation: portrait)`) is false (for that comma alternative). An empty query is true. Also support `min-width`/`max-width` values in `em` (1em = 16px).",
   {"mq.js": stub("matchesMedia")},
   {"mq.js": """function matchesMedia(query, width) {
  query = String(query).trim().toLowerCase();
  if (!query) return true;
  return query.split(',').some((alt) => {
    const parts = alt.trim().split(/\\s+and\\s+/);
    if (parts[0] === 'screen' || parts[0] === 'all') parts.shift();
    else if (!parts[0].startsWith('(')) return false;
    return parts.every((p) => {
      const m = /^\\(\\s*(min|max)-width\\s*:\\s*(\\d+(?:\\.\\d+)?)(px|em)\\s*\\)$/.exec(p);
      if (!m) return false;
      const v = Number(m[2]) * (m[3] === 'em' ? 16 : 1);
      return m[1] === 'min' ? width >= v : width <= v;
    });
  });
}
module.exports = { matchesMedia };"""},
   """const { matchesMedia: m } = require('./mq.js');
test('min', () => { assert.equal(m('(min-width: 600px)', 600), true); assert.equal(m('(min-width: 600px)', 599), false); });
test('max', () => { assert.equal(m('(max-width: 600px)', 600), true); assert.equal(m('(max-width:600px)', 601), false); });
test('and', () => { const q = '(min-width: 600px) and (max-width: 900px)'; assert.equal(m(q, 700), true); assert.equal(m(q, 500), false); assert.equal(m(q, 901), false); });
test('screen prefix', () => { assert.equal(m('screen and (min-width: 600px)', 700), true); assert.equal(m('all and (max-width: 100px)', 700), false); assert.equal(m('screen', 5), true); });
test('comma or', () => { const q = '(max-width: 400px), (min-width: 1000px)'; assert.equal(m(q, 300), true); assert.equal(m(q, 1200), true); assert.equal(m(q, 700), false); });
test('unknown', () => { assert.equal(m('print', 500), false); assert.equal(m('(orientation: portrait)', 500), false); assert.equal(m('screen and (min-width: 100px) and (hover: hover)', 500), false); assert.equal(m('print, (min-width: 100px)', 500), true); });
test('em', () => { assert.equal(m('(min-width: 40em)', 640), true); assert.equal(m('(min-width: 40em)', 639), false); });
test('case/space', () => assert.equal(m('  SCREEN   AND  ( MIN-WIDTH : 10PX ) ', 20), true));
test('empty', () => assert.equal(m('', 10), true));""")

js("ui-js-move-item", "write", "easy", "components",
   "Implement `moveItem(list, from, to)` in reorder.js (`module.exports = { moveItem }`) for drag-and-drop / keyboard reordering. Return a NEW array with the element at index `from` removed and inserted so that it ends up at index `to` of the result. Out-of-range or non-integer `from` returns an unchanged copy; `to` is clamped to [0, length-1]. Never mutate the input.",
   {"reorder.js": stub("moveItem")},
   {"reorder.js": """function moveItem(list, from, to) {
  const out = list.slice();
  if (!Number.isInteger(from) || from < 0 || from >= out.length || !Number.isInteger(to)) return out;
  const [x] = out.splice(from, 1);
  out.splice(Math.min(Math.max(to, 0), out.length), 0, x);
  return out;
}
module.exports = { moveItem };"""},
   """const { moveItem: m } = require('./reorder.js');
test('forward', () => assert.deepEqual(m(['a', 'b', 'c', 'd'], 0, 2), ['b', 'c', 'a', 'd']));
test('backward', () => assert.deepEqual(m(['a', 'b', 'c', 'd'], 3, 1), ['a', 'd', 'b', 'c']));
test('same', () => assert.deepEqual(m(['a', 'b'], 1, 1), ['a', 'b']));
test('clamp to', () => { assert.deepEqual(m(['a', 'b', 'c'], 0, 99), ['b', 'c', 'a']); assert.deepEqual(m(['a', 'b', 'c'], 2, -4), ['c', 'a', 'b']); });
test('bad from', () => { const a = ['a', 'b']; const o = m(a, 5, 0); assert.deepEqual(o, ['a', 'b']); assert.notEqual(o, a); assert.deepEqual(m(a, -1, 0), ['a', 'b']); assert.deepEqual(m(a, 0.5, 1), ['a', 'b']); });
test('no mutation', () => { const a = ['a', 'b', 'c']; m(a, 0, 2); assert.deepEqual(a, ['a', 'b', 'c']); });""")

js("ui-js-compact-number", "write", "hard", "formatting",
   "Implement `compactNumber(n)` in compact.js (`module.exports = { compactNumber }`) for counters ('1.2K views'). |n| < 1000 prints as is (rounded to an integer). Otherwise scale by 1000 steps with suffixes K, M, B, T and show at most one decimal, dropping '.0' ('1K', '1.2K', '15K', '999.9K'). Rounding that reaches 1000 in the current unit must promote to the next unit (999999 -> '1M', 999950 -> '1M', 999949 -> '999.9K'). Keep the sign ('-1.5K'). Above 999.9T keep T (e.g. '1500T'). Non-finite input returns '0'.",
   {"compact.js": stub("compactNumber")},
   {"compact.js": """function compactNumber(n) {
  if (!Number.isFinite(n)) return '0';
  const sign = n < 0 ? '-' : '';
  const a = Math.abs(n);
  if (a < 1000) return (Math.round(a) === 0 ? '' : sign) + String(Math.round(a));
  const units = ['K', 'M', 'B', 'T'];
  let i = 0, v = a / 1000;
  for (;;) {
    const r = Math.round(v * 10) / 10;
    if (r >= 1000 && i < units.length - 1) { v = r / 1000; i++; continue; }
    return sign + String(r) + units[i];
  }
}
module.exports = { compactNumber };"""},
   """const { compactNumber: c } = require('./compact.js');
test('small', () => { assert.equal(c(0), '0'); assert.equal(c(999), '999'); assert.equal(c(12.4), '12'); });
test('K', () => { assert.equal(c(1000), '1K'); assert.equal(c(1234), '1.2K'); assert.equal(c(15000), '15K'); assert.equal(c(15500), '15.5K'); });
test('M', () => { assert.equal(c(1500000), '1.5M'); assert.equal(c(2000000), '2M'); });
test('B T', () => { assert.equal(c(1e9), '1B'); assert.equal(c(3.4e12), '3.4T'); });
test('promotion', () => { assert.equal(c(999999), '1M'); assert.equal(c(999950), '1M'); assert.equal(c(999949), '999.9K'); assert.equal(c(999999999), '1B'); });
test('hundreds keep one decimal', () => { assert.equal(c(123456), '123.5K'); assert.equal(c(100400), '100.4K'); assert.equal(c(100000), '100K'); });
test('negative', () => { assert.equal(c(-1500), '-1.5K'); assert.equal(c(-0.2), '0'); assert.equal(c(-999999), '-1M'); });
test('huge', () => assert.equal(c(1.5e15), '1500T'));
test('non finite', () => { assert.equal(c(NaN), '0'); assert.equal(c(Infinity), '0'); });""")

js("ui-js-pluralize", "write", "easy", "text",
   "Implement `pluralize(count, singular, plural)` in plural.js (`module.exports = { pluralize }`) returning e.g. '1 item', '0 items', '2 items', '1,234 items'. If `plural` is omitted use `singular + 's'`; when singular ends in 's', 'x', 'z', 'ch' or 'sh' add 'es'; when it ends in a consonant + 'y' change to 'ies'. Absolute value 1 is singular (so -1 -> '-1 item'); 1.0 too; 1.5 -> '1.5 items'. Integers are grouped with thousands commas.",
   {"plural.js": stub("pluralize")},
   {"plural.js": """function pluralize(count, singular, plural) {
  let p = plural;
  if (p === undefined) {
    if (/(s|x|z|ch|sh)$/.test(singular)) p = singular + 'es';
    else if (/[^aeiou]y$/.test(singular)) p = singular.slice(0, -1) + 'ies';
    else p = singular + 's';
  }
  const text = Number.isInteger(count) ? String(count).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',') : String(count);
  return text + ' ' + (Math.abs(count) === 1 ? singular : p);
}
module.exports = { pluralize };"""},
   """const { pluralize: p } = require('./plural.js');
test('basic', () => { assert.equal(p(1, 'item'), '1 item'); assert.equal(p(0, 'item'), '0 items'); assert.equal(p(2, 'item'), '2 items'); });
test('explicit plural', () => { assert.equal(p(2, 'child', 'children'), '2 children'); assert.equal(p(1, 'child', 'children'), '1 child'); });
test('es', () => { assert.equal(p(2, 'box'), '2 boxes'); assert.equal(p(3, 'class'), '3 classes'); assert.equal(p(2, 'match'), '2 matches'); assert.equal(p(2, 'wish'), '2 wishes'); });
test('y', () => { assert.equal(p(2, 'city'), '2 cities'); assert.equal(p(2, 'day'), '2 days'); });
test('negative/decimal', () => { assert.equal(p(-1, 'point'), '-1 point'); assert.equal(p(1.5, 'hour'), '1.5 hours'); assert.equal(p(1.0, 'hour'), '1 hour'); });
test('grouping', () => { assert.equal(p(1234, 'view'), '1,234 views'); assert.equal(p(1234567, 'view'), '1,234,567 views'); assert.equal(p(999, 'view'), '999 views'); });""")

js("ui-js-memoize-last", "write", "easy", "utilities",
   "Implement `memoizeLast(fn)` in memo.js (`module.exports = { memoizeLast }`): returns a function that caches only the most recent call. If called again with the same number of arguments and every argument `===` the previous one (and the same `this`), return the cached result without calling `fn`; otherwise call `fn` and cache. If `fn` throws, nothing is cached. The wrapper has a `.clear()` method.",
   {"memo.js": stub("memoizeLast")},
   {"memo.js": """function memoizeLast(fn) {
  let has = false, lastArgs, lastCtx, lastResult;
  function m(...args) {
    if (has && lastCtx === this && args.length === lastArgs.length && args.every((a, i) => a === lastArgs[i])) return lastResult;
    const r = fn.apply(this, args);
    has = true; lastArgs = args; lastCtx = this; lastResult = r;
    return r;
  }
  m.clear = () => { has = false; lastArgs = lastCtx = lastResult = undefined; };
  return m;
}
module.exports = { memoizeLast };"""},
   """const { memoizeLast: mk } = require('./memo.js');
test('caches same args', () => { let n = 0; const f = mk((a, b) => { n++; return a + b; }); assert.equal(f(1, 2), 3); assert.equal(f(1, 2), 3); assert.equal(n, 1); });
test('only last', () => { let n = 0; const f = mk((a) => { n++; return a; }); f(1); f(2); f(1); assert.equal(n, 3); });
test('arg count matters', () => { let n = 0; const f = mk((...a) => { n++; return a.length; }); f(1); f(1, undefined); assert.equal(n, 2); });
test('object identity', () => { let n = 0; const f = mk((o) => { n++; return o.x; }); const o = { x: 1 }; f(o); f(o); f({ x: 1 }); assert.equal(n, 2); });
test('throw not cached', () => { let n = 0; const f = mk((a) => { n++; if (a === 0) throw new Error('x'); return a; }); assert.throws(() => f(0)); assert.throws(() => f(0)); assert.equal(n, 2); });
test('this', () => { const f = mk(function (a) { return this.k + a; }); assert.equal(f.call({ k: 1 }, 1), 2); assert.equal(f.call({ k: 10 }, 1), 11); });
test('clear', () => { let n = 0; const f = mk(() => ++n); f(); f.clear(); f(); assert.equal(n, 2); });
test('falsy cached result', () => { let n = 0; const f = mk(() => { n++; return 0; }); f(); f(); assert.equal(n, 1); });""")
