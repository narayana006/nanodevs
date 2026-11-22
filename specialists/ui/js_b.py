from tb import js, stub

# ---- validation -------------------------------------------------------------
js("ui-js-validate-email", "write", "easy", "forms",
   "Implement `isEmail(s)` in email.js (`module.exports = { isEmail }`) for a sign-up form (not full RFC 5322). Valid: exactly one '@'; non-empty local part without spaces and not starting/ending with '.' and without '..'; domain made of at least two dot-separated labels, each 1-63 chars of letters, digits or hyphen, not starting/ending with hyphen; final label (TLD) letters only, 2+ chars. Surrounding whitespace is trimmed first. Non-strings are invalid.",
   {"email.js": stub("isEmail")},
   {"email.js": """function isEmail(s) {
  if (typeof s !== 'string') return false;
  s = s.trim();
  const parts = s.split('@');
  if (parts.length !== 2) return false;
  const [local, domain] = parts;
  if (!local || /\\s/.test(local) || local.startsWith('.') || local.endsWith('.') || local.includes('..')) return false;
  const labels = domain.split('.');
  if (labels.length < 2) return false;
  if (!labels.every((l) => /^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/.test(l))) return false;
  return /^[A-Za-z]{2,}$/.test(labels[labels.length - 1]);
}
module.exports = { isEmail };"""},
   """const { isEmail: e } = require('./email.js');
test('valid', () => { for (const s of ['a@b.co', 'first.last+tag@sub.example.org', ' me@x-y.io ', 'a_b@c1.dev']) assert.equal(e(s), true, s); });
test('missing parts', () => { for (const s of ['', 'a', 'a@', '@b.co', 'a@b', 'a@@b.co', 'a@b@c.co']) assert.equal(e(s), false, s); });
test('dots', () => { for (const s of ['.a@b.co', 'a.@b.co', 'a..b@c.co', 'a@.co', 'a@b..co', 'a@b.co.']) assert.equal(e(s), false, s); });
test('spaces', () => assert.equal(e('a b@c.co'), false));
test('hyphen labels', () => { assert.equal(e('a@-b.co'), false); assert.equal(e('a@b-.co'), false); assert.equal(e('a@b-c.co'), true); });
test('tld', () => { assert.equal(e('a@b.c'), false); assert.equal(e('a@b.c0'), false); });
test('non-string', () => { assert.equal(e(null), false); assert.equal(e(5), false); });""")

js("ui-js-validate-password", "write", "easy", "forms",
   "Implement `passwordErrors(pw)` in pw.js (`module.exports = { passwordErrors }`). Return an array of error codes (empty array = valid) in this exact order: 'min8' (fewer than 8 chars), 'lower' (no a-z), 'upper' (no A-Z), 'digit' (no 0-9), 'symbol' (no character that is not a letter, digit or whitespace), 'space' (contains any whitespace). Non-strings return ['min8','lower','upper','digit','symbol'].",
   {"pw.js": stub("passwordErrors")},
   {"pw.js": """function passwordErrors(pw) {
  if (typeof pw !== 'string') pw = '';
  const e = [];
  if (pw.length < 8) e.push('min8');
  if (!/[a-z]/.test(pw)) e.push('lower');
  if (!/[A-Z]/.test(pw)) e.push('upper');
  if (!/[0-9]/.test(pw)) e.push('digit');
  if (!/[^A-Za-z0-9\\s]/.test(pw)) e.push('symbol');
  if (/\\s/.test(pw)) e.push('space');
  return e;
}
module.exports = { passwordErrors };"""},
   """const { passwordErrors: p } = require('./pw.js');
test('valid', () => assert.deepEqual(p('Abcdef1!'), []));
test('short', () => assert.deepEqual(p('Ab1!'), ['min8']));
test('all missing', () => assert.deepEqual(p('        '), ['lower', 'upper', 'digit', 'symbol', 'space']));
test('order', () => assert.deepEqual(p('abc'), ['min8', 'upper', 'digit', 'symbol']));
test('digits only', () => assert.deepEqual(p('12345678'), ['lower', 'upper', 'symbol']));
test('space ok otherwise', () => assert.deepEqual(p('Abc def1!'), ['space']));
test('non-string', () => assert.deepEqual(p(undefined), ['min8', 'lower', 'upper', 'digit', 'symbol']));""")

js("ui-js-validate-form", "write", "hard", "forms",
   "Implement `validateForm(values, rules)` in form.js (`module.exports = { validateForm }`). `rules` maps field name -> rule object with optional keys `required`, `minLength`, `maxLength`, `pattern` (RegExp), `min`, `max` (numbers), `custom` (function(value, allValues) returning an error string or null/undefined) and `messages` (object overriding default messages by rule name). String values are trimmed before checking. Rules run in the order required, minLength, maxLength, pattern, min, max, custom and the FIRST failing rule produces the field's error. Default messages: required 'Required', minLength 'Too short', maxLength 'Too long', pattern 'Invalid format', min 'Too small', max 'Too large'. A non-required field that is empty (after trim, or undefined/null) skips every other rule. min/max compare Number(value); a non-numeric value fails with 'Invalid number' (override key `number`). The `custom` message is whatever the function returns. Return `{ valid, errors }` where errors only has keys for failing fields and `valid` is true when there are none.",
   {"form.js": stub("validateForm")},
   {"form.js": """const DEFAULTS = { required: 'Required', minLength: 'Too short', maxLength: 'Too long', pattern: 'Invalid format', min: 'Too small', max: 'Too large', number: 'Invalid number' };
function validateForm(values, rules) {
  const errors = {};
  for (const field of Object.keys(rules)) {
    const r = rules[field], msg = (k) => (r.messages && r.messages[k]) || DEFAULTS[k];
    let v = values[field];
    if (typeof v === 'string') v = v.trim();
    const empty = v === undefined || v === null || v === '';
    let err = null;
    if (empty) { if (r.required) err = msg('required'); }
    else {
      const s = String(v);
      if (r.minLength !== undefined && s.length < r.minLength) err = msg('minLength');
      else if (r.maxLength !== undefined && s.length > r.maxLength) err = msg('maxLength');
      else if (r.pattern && !new RegExp(r.pattern.source, r.pattern.flags.replace(/[gy]/g, '')).test(s)) err = msg('pattern');
      else if (r.min !== undefined || r.max !== undefined) {
        const n = Number(v);
        if (Number.isNaN(n)) err = msg('number');
        else if (r.min !== undefined && n < r.min) err = msg('min');
        else if (r.max !== undefined && n > r.max) err = msg('max');
      }
      if (!err && r.custom) err = r.custom(v, values) || null;
    }
    if (err) errors[field] = err;
  }
  return { valid: Object.keys(errors).length === 0, errors };
}
module.exports = { validateForm };"""},
   """const { validateForm: v } = require('./form.js');
test('required', () => {
  const r = v({ a: '  ', b: 'x' }, { a: { required: true }, b: { required: true } });
  assert.deepEqual(r, { valid: false, errors: { a: 'Required' } });
});
test('optional empty skips rules', () => assert.deepEqual(v({ a: '' }, { a: { minLength: 5, pattern: /x/ } }), { valid: true, errors: {} }));
test('order: minLength before pattern', () => assert.equal(v({ a: 'ab' }, { a: { minLength: 3, pattern: /^\\d+$/ } }).errors.a, 'Too short'));
test('maxLength', () => assert.equal(v({ a: 'abcd' }, { a: { maxLength: 3 } }).errors.a, 'Too long'));
test('pattern with g flag is stateless', () => {
  const rule = { a: { pattern: /^\\d+$/g } };
  for (let i = 0; i < 3; i++) assert.equal(v({ a: '123' }, rule).valid, true);
});
test('min max', () => {
  const rules = { n: { min: 1, max: 10 } };
  assert.equal(v({ n: '0' }, rules).errors.n, 'Too small'); assert.equal(v({ n: 11 }, rules).errors.n, 'Too large');
  assert.equal(v({ n: 'abc' }, rules).errors.n, 'Invalid number'); assert.equal(v({ n: '10' }, rules).valid, true); assert.equal(v({ n: 0 }, { n: { min: 0 } }).valid, true);
});
test('custom gets all values', () => {
  const rules = { c: { custom: (val, all) => (val === all.p ? null : 'Mismatch') } };
  assert.deepEqual(v({ p: 'x', c: 'y' }, rules).errors, { c: 'Mismatch' }); assert.equal(v({ p: 'x', c: 'x' }, rules).valid, true);
});
test('custom messages', () => assert.equal(v({ a: '' }, { a: { required: true, messages: { required: 'Enter a name' } } }).errors.a, 'Enter a name'));
test('trim before length', () => assert.equal(v({ a: '  ab  ' }, { a: { minLength: 3 } }).errors.a, 'Too short'));
test('missing key', () => assert.equal(v({}, { a: { required: true } }).errors.a, 'Required'));""")

js("ui-js-luhn", "write", "easy", "forms",
   "Implement `isValidCard(input)` in card.js (`module.exports = { isValidCard }`): strip spaces and hyphens, the remainder must be 12 to 19 digits and pass the Luhn checksum. Anything else (letters, other separators, non-strings) is false. Also export `cardBrand(input)` returning 'visa' (starts with 4), 'mastercard' (51-55 or 2221-2720), 'amex' (34 or 37) or 'unknown'.",
   {"card.js": stub("isValidCard", "cardBrand")},
   {"card.js": """function isValidCard(input) {
  if (typeof input !== 'string') return false;
  const s = input.replace(/[ -]/g, '');
  if (!/^\\d{12,19}$/.test(s)) return false;
  let sum = 0;
  for (let i = 0; i < s.length; i++) {
    let d = Number(s[s.length - 1 - i]);
    if (i % 2 === 1) { d *= 2; if (d > 9) d -= 9; }
    sum += d;
  }
  return sum % 10 === 0;
}
function cardBrand(input) {
  const s = String(input).replace(/[ -]/g, '');
  if (/^4/.test(s)) return 'visa';
  if (/^5[1-5]/.test(s) || (/^\\d{4}/.test(s) && Number(s.slice(0, 4)) >= 2221 && Number(s.slice(0, 4)) <= 2720)) return 'mastercard';
  if (/^3[47]/.test(s)) return 'amex';
  return 'unknown';
}
module.exports = { isValidCard, cardBrand };"""},
   """const { isValidCard: v, cardBrand: b } = require('./card.js');
test('valid', () => { assert.equal(v('4539 1488 0343 6467'), true); assert.equal(v('4111-1111-1111-1111'), true); assert.equal(v('378282246310005'), true); });
test('bad checksum', () => assert.equal(v('4111 1111 1111 1112'), false));
test('format', () => { assert.equal(v('4111x111111111111'), false); assert.equal(v('411111111'), false); assert.equal(v(''), false); assert.equal(v(4111111111111111), false); });
test('length', () => assert.equal(v('0000000000000000000000'), false));
test('brand', () => { assert.equal(b('4111111111111111'), 'visa'); assert.equal(b('5500 0000 0000 0004'), 'mastercard'); assert.equal(b('2223000048400011'), 'mastercard'); assert.equal(b('378282246310005'), 'amex'); assert.equal(b('6011111111111117'), 'unknown'); });
test('brand edges', () => { assert.equal(b('2720999999999999'), 'mastercard'); assert.equal(b('2721000000000000'), 'unknown'); assert.equal(b('2220000000000000'), 'unknown'); });""")

js("ui-js-phone", "write", "easy", "forms",
   "Implement `formatPhone(input)` in phone.js (`module.exports = { formatPhone }`) for US numbers: keep only digits; an 11-digit number must start with '1' (dropped); after that exactly 10 digits are required, the area code and exchange must not start with 0 or 1; return `(555) 123-4567`, otherwise return null.",
   {"phone.js": stub("formatPhone")},
   {"phone.js": """function formatPhone(input) {
  let d = String(input).replace(/\\D/g, '');
  if (d.length === 11 && d[0] === '1') d = d.slice(1);
  if (d.length !== 10 || /[01]/.test(d[0]) || /[01]/.test(d[3])) return null;
  return '(' + d.slice(0, 3) + ') ' + d.slice(3, 6) + '-' + d.slice(6);
}
module.exports = { formatPhone };"""},
   """const { formatPhone: f } = require('./phone.js');
test('plain', () => assert.equal(f('5552345678'), '(555) 234-5678'));
test('punct', () => assert.equal(f('555.234.5678'), '(555) 234-5678'));
test('country code', () => assert.equal(f('+1 (555) 234-5678'), '(555) 234-5678'));
test('too short/long', () => { assert.equal(f('555123456'), null); assert.equal(f('555234567889'), null); });
test('bad 11', () => assert.equal(f('25552345678'), null));
test('area code', () => { assert.equal(f('0551234567'), null); assert.equal(f('1551234567'), null); });
test('exchange', () => { assert.equal(f('5550234567'), null); assert.equal(f('5551234567'), null); assert.equal(f('5552234567'), '(555) 223-4567'); });
test('non-string', () => assert.equal(f(undefined), null));""")

# ---- tables / lists -------------------------------------------------------------
js("ui-js-sort-rows", "write", "medium", "tables",
   "Implement `sortRows(rows, key, dir = 'asc')` in sort.js (`module.exports = { sortRows }`). Return a NEW array (do not mutate the input) sorted by `row[key]`. Numbers compare numerically; everything else compares as case-insensitive strings. If both values are numeric strings of the form '12' or '3.5' compare them numerically too. `null`/`undefined`/'' values always sort LAST, for both directions. The sort is stable (ties keep original order, also for 'desc'). `dir` is 'asc' or 'desc'; anything else throws a TypeError.",
   {"sort.js": stub("sortRows")},
   {"sort.js": """const isNum = (v) => typeof v === 'number' || (typeof v === 'string' && /^-?\\d+(\\.\\d+)?$/.test(v.trim()));
function sortRows(rows, key, dir = 'asc') {
  if (dir !== 'asc' && dir !== 'desc') throw new TypeError('bad dir');
  const sign = dir === 'asc' ? 1 : -1;
  const blank = (v) => v === null || v === undefined || v === '';
  return rows.map((r, i) => [r, i]).sort(([a, i], [b, j]) => {
    const x = a[key], y = b[key];
    if (blank(x) || blank(y)) return blank(x) && blank(y) ? i - j : blank(x) ? 1 : -1;
    let c;
    if (isNum(x) && isNum(y)) c = Number(x) - Number(y);
    else { const s = String(x).toLowerCase(), t = String(y).toLowerCase(); c = s < t ? -1 : s > t ? 1 : 0; }
    return c * sign || i - j;
  }).map(([r]) => r);
}
module.exports = { sortRows };"""},
   """const { sortRows: s } = require('./sort.js');
const names = (rs) => rs.map((r) => r.n);
test('numbers not lexicographic', () => assert.deepEqual(names(s([{ n: 'a', v: 10 }, { n: 'b', v: 9 }, { n: 'c', v: 100 }], 'v')), ['b', 'a', 'c']));
test('strings case-insensitive', () => assert.deepEqual(names(s([{ n: 'b' }, { n: 'A' }, { n: 'c' }], 'n')), ['A', 'b', 'c']));
test('numeric strings', () => assert.deepEqual(s([{ v: '10' }, { v: '9' }, { v: '2.5' }], 'v').map((r) => r.v), ['2.5', '9', '10']));
test('desc', () => assert.deepEqual(s([{ v: 1 }, { v: 3 }, { v: 2 }], 'v', 'desc').map((r) => r.v), [3, 2, 1]));
test('blanks last both ways', () => {
  const rows = [{ n: 'x', v: null }, { n: 'y', v: 2 }, { n: 'z', v: '' }, { n: 'w', v: 1 }, { n: 'u' }];
  assert.deepEqual(names(s(rows, 'v')), ['w', 'y', 'x', 'z', 'u']); assert.deepEqual(names(s(rows, 'v', 'desc')), ['y', 'w', 'x', 'z', 'u']);
});
test('stable incl desc', () => {
  const rows = [{ n: '1', g: 'a' }, { n: '2', g: 'b' }, { n: '3', g: 'a' }, { n: '4', g: 'b' }];
  assert.deepEqual(names(s(rows, 'g')), ['1', '3', '2', '4']); assert.deepEqual(names(s(rows, 'g', 'desc')), ['2', '4', '1', '3']);
});
test('no mutation', () => { const rows = [{ v: 2 }, { v: 1 }]; const out = s(rows, 'v'); assert.notEqual(out, rows); assert.equal(rows[0].v, 2); });
test('bad dir', () => assert.throws(() => s([], 'v', 'up'), TypeError));""")

js("ui-js-filter-rows", "write", "medium", "tables",
   "Implement `filterRows(rows, query, keys)` in filter.js (`module.exports = { filterRows }`). Split `query` on whitespace into terms. A row matches when EVERY positive term occurs (case-insensitive substring) in at least one of the stringified `row[key]` values for `keys`, and NO term that starts with '-' (and has more characters, e.g. '-draft') occurs in any of them. A lone '-' is an ordinary term. An empty/blank query returns a shallow copy of all rows. null/undefined values count as ''.",
   {"filter.js": stub("filterRows")},
   {"filter.js": """function filterRows(rows, query, keys) {
  const terms = String(query).toLowerCase().split(/\\s+/).filter(Boolean);
  if (!terms.length) return rows.slice();
  return rows.filter((row) => {
    const vals = keys.map((k) => (row[k] === null || row[k] === undefined ? '' : String(row[k]).toLowerCase()));
    return terms.every((t) => {
      if (t.length > 1 && t[0] === '-') return !vals.some((v) => v.includes(t.slice(1)));
      return vals.some((v) => v.includes(t));
    });
  });
}
module.exports = { filterRows };"""},
   """const { filterRows: f } = require('./filter.js');
const rows = [{ id: 1, name: 'Alice Smith', role: 'admin', note: null }, { id: 2, name: 'Bob Stone', role: 'editor', note: 'draft' }, { id: 3, name: 'alice jones', role: 'editor', note: '' }];
const ids = (r) => r.map((x) => x.id);
test('empty returns copy', () => { const o = f(rows, '   ', ['name']); assert.deepEqual(ids(o), [1, 2, 3]); assert.notEqual(o, rows); });
test('case-insens substring', () => assert.deepEqual(ids(f(rows, 'ALI', ['name'])), [1, 3]));
test('terms AND across keys', () => assert.deepEqual(ids(f(rows, 'alice editor', ['name', 'role'])), [3]));
test('term order irrelevant', () => assert.deepEqual(ids(f(rows, 'editor alice', ['name', 'role'])), [3]));
test('negation', () => assert.deepEqual(ids(f(rows, 'editor -draft', ['name', 'role', 'note'])), [3]));
test('negation only', () => assert.deepEqual(ids(f(rows, '-alice', ['name'])), [2]));
test('lone dash is literal', () => assert.deepEqual(ids(f([{ id: 1, n: 'a-b' }, { id: 2, n: 'ab' }], '-', ['n'])), [1]));
test('numbers stringified', () => assert.deepEqual(ids(f(rows, '2', ['id'])), [2]));
test('null safe', () => assert.deepEqual(ids(f(rows, 'null', ['note'])), []));""")

js("ui-js-paginate", "write", "easy", "tables",
   "Implement `paginate(items, page, size)` in page.js (`module.exports = { paginate }`). Pages are 1-based; `page` is clamped into [1, pages] (and non-integers/NaN count as 1); `pages = max(1, ceil(total/size))`. Return `{ items, page, pages, total, start, end, hasPrev, hasNext }` where start/end are the 1-based position of the first/last item shown (both 0 when there are no items). `size < 1` or non-integer throws RangeError.",
   {"page.js": stub("paginate")},
   {"page.js": """function paginate(items, page, size) {
  if (!Number.isInteger(size) || size < 1) throw new RangeError('size');
  const total = items.length, pages = Math.max(1, Math.ceil(total / size));
  let p = Number.isFinite(page) ? Math.trunc(page) : 1;
  p = Math.min(Math.max(p, 1), pages);
  const from = (p - 1) * size, slice = items.slice(from, from + size);
  return { items: slice, page: p, pages, total, start: slice.length ? from + 1 : 0, end: slice.length ? from + slice.length : 0, hasPrev: p > 1, hasNext: p < pages };
}
module.exports = { paginate };"""},
   """const { paginate: p } = require('./page.js');
const a = [1, 2, 3, 4, 5, 6, 7];
test('first', () => assert.deepEqual(p(a, 1, 3), { items: [1, 2, 3], page: 1, pages: 3, total: 7, start: 1, end: 3, hasPrev: false, hasNext: true }));
test('last partial', () => assert.deepEqual(p(a, 3, 3), { items: [7], page: 3, pages: 3, total: 7, start: 7, end: 7, hasPrev: true, hasNext: false }));
test('clamp', () => { assert.equal(p(a, 99, 3).page, 3); assert.equal(p(a, 0, 3).page, 1); assert.equal(p(a, -5, 3).page, 1); assert.equal(p(a, NaN, 3).page, 1); });
test('empty', () => assert.deepEqual(p([], 1, 10), { items: [], page: 1, pages: 1, total: 0, start: 0, end: 0, hasPrev: false, hasNext: false }));
test('exact multiple', () => assert.equal(p([1, 2, 3, 4], 1, 2).pages, 2));
test('bad size', () => { assert.throws(() => p(a, 1, 0), RangeError); assert.throws(() => p(a, 1, 1.5), RangeError); });""")

js("ui-js-page-range", "write", "hard", "tables",
   "Implement `pageRange(current, total, max = 7)` in range.js (`module.exports = { pageRange }`) for a pagination control with at most `max` slots (max >= 5). Return an array of page numbers and the string '…' (ellipsis). If total <= max return 1..total. Otherwise the first and last page are always shown and the array always has exactly `max` entries: near the start (current <= max-3) `[1..max-2, '…', total]`; near the end (current >= total-max+4) `[1, '…', total-max+3..total]`; otherwise `[1, '…', <max-4 pages around current>, '…', total]` where the window starts at `current - floor((max-5)/2)`. Example for max 7, total 10: current 1..4 -> [1,2,3,4,5,'…',10]; current 5 -> [1,'…',4,5,6,'…',10]; current 7..10 -> [1,'…',6,7,8,9,10].",
   {"range.js": stub("pageRange")},
   {"range.js": """function pageRange(current, total, max = 7) {
  const seq = (a, b) => Array.from({ length: Math.max(0, b - a + 1) }, (_, i) => a + i);
  if (total <= max) return seq(1, total);
  if (current <= max - 3) return [...seq(1, max - 2), '…', total];
  if (current >= total - max + 4) return [1, '…', ...seq(total - max + 3, total)];
  const start = current - Math.floor((max - 5) / 2);
  return [1, '…', ...seq(start, start + max - 5), '…', total];
}
module.exports = { pageRange };"""},
   """const { pageRange: r } = require('./range.js');
test('few pages', () => { assert.deepEqual(r(1, 1), [1]); assert.deepEqual(r(3, 5), [1, 2, 3, 4, 5]); assert.deepEqual(r(4, 7), [1, 2, 3, 4, 5, 6, 7]); });
test('start', () => { for (const c of [1, 2, 3, 4]) assert.deepEqual(r(c, 10), [1, 2, 3, 4, 5, '…', 10], 'c=' + c); });
test('middle', () => { assert.deepEqual(r(5, 10), [1, '…', 4, 5, 6, '…', 10]); assert.deepEqual(r(6, 10), [1, '…', 5, 6, 7, '…', 10]); });
test('end', () => { for (const c of [7, 8, 9, 10]) assert.deepEqual(r(c, 10), [1, '…', 6, 7, 8, 9, 10], 'c=' + c); });
test('long', () => { assert.deepEqual(r(50, 100), [1, '…', 49, 50, 51, '…', 100]); assert.deepEqual(r(1, 100), [1, 2, 3, 4, 5, '…', 100]); assert.deepEqual(r(100, 100), [1, '…', 96, 97, 98, 99, 100]); });
test('max 5', () => { assert.deepEqual(r(5, 10, 5), [1, '…', 5, '…', 10]); assert.deepEqual(r(1, 10, 5), [1, 2, 3, '…', 10]); assert.deepEqual(r(10, 10, 5), [1, '…', 8, 9, 10]); });
test('max 9 middle', () => assert.deepEqual(r(10, 20, 9), [1, '…', 8, 9, 10, 11, 12, '…', 20]));
test('constant length', () => { for (let c = 1; c <= 30; c++) assert.equal(r(c, 30).length, 7, 'c=' + c); });""")

js("ui-js-highlight", "write", "medium", "text",
   "Implement `highlight(text, query)` in hl.js (`module.exports = { highlight }`) returning an HTML string safe to assign to innerHTML: the text is HTML-escaped (& < > \" ') and every case-insensitive occurrence of `query` is wrapped in `<mark>...</mark>` (keeping the original casing). The query is literal text, not a regex (so '.' or '(' must work). Matches do not overlap. An empty query returns just the escaped text. A query containing '<' matches against the original text, not the escaped output.",
   {"hl.js": stub("highlight")},
   {"hl.js": """const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
function highlight(text, query) {
  text = String(text); query = String(query || '');
  if (!query) return esc(text);
  const re = new RegExp(query.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'), 'gi');
  let out = '', last = 0, m;
  while ((m = re.exec(text))) { out += esc(text.slice(last, m.index)) + '<mark>' + esc(m[0]) + '</mark>'; last = m.index + m[0].length; }
  return out + esc(text.slice(last));
}
module.exports = { highlight };"""},
   """const { highlight: h } = require('./hl.js');
test('basic', () => assert.equal(h('Hello hello', 'hel'), '<mark>Hel</mark>lo <mark>hel</mark>lo'));
test('escape', () => assert.equal(h('<b>a&b</b>', 'a'), '&lt;b&gt;<mark>a</mark>&amp;b&lt;/b&gt;'));
test('regex chars literal', () => assert.equal(h('a.b (c) a+b', '.'), 'a<mark>.</mark>b (c) a+b'));
test('parens', () => assert.equal(h('f(x)', '(x)'), 'f<mark>(x)</mark>'));
test('empty query', () => { assert.equal(h('<i>', ''), '&lt;i&gt;'); assert.equal(h('x', undefined), 'x'); });
test('no match', () => assert.equal(h('abc', 'z'), 'abc'));
test('query with <', () => assert.equal(h('a<b', '<'), 'a<mark>&lt;</mark>b'));
test('non overlapping', () => assert.equal(h('aaaa', 'aa'), '<mark>aa</mark><mark>aa</mark>'));
test('repeat calls', () => { assert.equal(h('aXa', 'a'), '<mark>a</mark>X<mark>a</mark>'); assert.equal(h('aXa', 'a'), '<mark>a</mark>X<mark>a</mark>'); });""")
