from tb import js, stub

# ---- timing -----------------------------------------------------------------
js("ui-js-debounce", "write", "easy", "timing",
   "Implement `debounce(fn, wait)` in debounce.js (CommonJS, `module.exports = { debounce }`). The returned function delays calling `fn` until `wait` ms have passed since the last call, then calls it once with the latest arguments and `this`. It must have a `.cancel()` method that drops a pending call. Use the global `setTimeout`/`clearTimeout` (looked up at call time).",
   {"debounce.js": stub("debounce")},
   {"debounce.js": """function debounce(fn, wait) {
  let t = null;
  function d(...args) {
    clearTimeout(t);
    t = setTimeout(() => { t = null; fn.apply(this, args); }, wait);
  }
  d.cancel = () => { clearTimeout(t); t = null; };
  return d;
}
module.exports = { debounce };"""},
   """const { debounce } = require('./debounce.js');
test('calls once with last args', () => {
  const c = clock(); const calls = [];
  const d = debounce((x) => calls.push(x), 100);
  d(1); c.tick(50); d(2); c.tick(50); assert.deepEqual(calls, []); c.tick(50); assert.deepEqual(calls, [2]); c.restore();
});
test('separate bursts', () => {
  const c = clock(); let n = 0; const d = debounce(() => n++, 10);
  d(); c.tick(10); d(); c.tick(10); assert.equal(n, 2); c.restore();
});
test('cancel', () => {
  const c = clock(); let n = 0; const d = debounce(() => n++, 10);
  d(); d.cancel(); c.tick(100); assert.equal(n, 0); c.restore();
});
test('this preserved', () => {
  const c = clock(); const o = { v: 7, f: debounce(function () { this.got = this.v; }, 5) };
  o.f(); c.tick(5); assert.equal(o.got, 7); c.restore();
});""")

js("ui-js-throttle", "write", "medium", "timing",
   "Implement `throttle(fn, wait)` in throttle.js (`module.exports = { throttle }`). Leading and trailing edge: the first call runs `fn` immediately; further calls during the next `wait` ms are collapsed into ONE trailing call (with the latest args) that fires when the window ends; after a trailing call a new window of `wait` ms begins. If no extra call arrived, no trailing call happens. Add `.cancel()` to drop a pending trailing call and reset the window. Use global `setTimeout`, `clearTimeout` and `Date.now` looked up at call time.",
   {"throttle.js": stub("throttle")},
   {"throttle.js": """function throttle(fn, wait) {
  let timer = null, pending = null;
  function start() {
    timer = setTimeout(() => {
      timer = null;
      if (pending) { const p = pending; pending = null; fn.apply(p.ctx, p.args); start(); }
    }, wait);
  }
  function t(...args) {
    if (timer === null) { fn.apply(this, args); start(); }
    else pending = { ctx: this, args };
  }
  t.cancel = () => { clearTimeout(timer); timer = null; pending = null; };
  return t;
}
module.exports = { throttle };"""},
   """const { throttle } = require('./throttle.js');
test('leading call immediate', () => {
  const c = clock(); const out = []; const t = throttle((x) => out.push(x), 100);
  t('a'); assert.deepEqual(out, ['a']); c.restore();
});
test('collapses to one trailing with last args', () => {
  const c = clock(); const out = []; const t = throttle((x) => out.push(x), 100);
  t(1); c.tick(10); t(2); c.tick(10); t(3); assert.deepEqual(out, [1]); c.tick(80); assert.deepEqual(out, [1, 3]); c.restore();
});
test('no trailing without extra call', () => {
  const c = clock(); const out = []; const t = throttle((x) => out.push(x), 100);
  t(1); c.tick(500); assert.deepEqual(out, [1]); c.restore();
});
test('trailing starts a new window', () => {
  const c = clock(); const out = []; const t = throttle((x) => out.push(x), 100);
  t(1); t(2); c.tick(100); assert.deepEqual(out, [1, 2]); t(3); assert.deepEqual(out, [1, 2]); c.tick(100); assert.deepEqual(out, [1, 2, 3]); c.restore();
});
test('call after quiet period is leading again', () => {
  const c = clock(); const out = []; const t = throttle((x) => out.push(x), 100);
  t(1); c.tick(300); t(2); assert.deepEqual(out, [1, 2]); c.restore();
});
test('cancel', () => {
  const c = clock(); const out = []; const t = throttle((x) => out.push(x), 100);
  t(1); t(2); t.cancel(); c.tick(300); assert.deepEqual(out, [1]); t(9); assert.deepEqual(out, [1, 9]); c.restore();
});""")

js("ui-js-debounce-opts", "write", "hard", "timing",
   "Implement `debounce(fn, wait, options)` in debounce.js (`module.exports = { debounce }`). Options: `leading` (default false) and `trailing` (default true), plus `maxWait` (optional number). With `leading: true` the first call of a burst runs immediately; with `trailing: true` a call runs after `wait` ms of silence, but only if there was at least one call since the last invocation (so a single leading-only call does not fire twice). If `maxWait` is set, `fn` must be invoked (trailing) at latest `maxWait` ms after the first call of a burst even if calls keep arriving. Provide `.cancel()` and `.flush()` (runs a pending trailing call now and returns its result, otherwise returns undefined). Calls return the last result of `fn`. Use global `setTimeout`/`clearTimeout`/`Date.now` at call time.",
   {"debounce.js": stub("debounce")},
   {"debounce.js": """function debounce(fn, wait, options = {}) {
  const leading = !!options.leading, trailing = options.trailing !== false;
  const maxWait = options.maxWait;
  let timer = null, maxTimer = null, lastArgs = null, lastCtx = null, result;
  function invoke() {
    const a = lastArgs, c = lastCtx; lastArgs = lastCtx = null;
    result = fn.apply(c, a); return result;
  }
  function clear() { clearTimeout(timer); clearTimeout(maxTimer); timer = maxTimer = null; }
  function end() {
    const had = lastArgs !== null; clear();
    if (trailing && had) invoke();
  }
  function d(...args) {
    const burstStart = timer === null;
    lastArgs = args; lastCtx = this;
    clearTimeout(timer);
    timer = setTimeout(end, wait);
    if (burstStart) {
      if (maxWait !== undefined) maxTimer = setTimeout(() => { clearTimeout(timer); timer = null; const had = lastArgs !== null; maxTimer = null; if (trailing && had) invoke(); }, maxWait);
      if (leading) invoke();
    }
    return result;
  }
  d.cancel = () => { clear(); lastArgs = lastCtx = null; };
  d.flush = () => { if (lastArgs !== null && trailing) { clear(); return invoke(); } clear(); return undefined; };
  return d;
}
module.exports = { debounce };"""},
   """const { debounce } = require('./debounce.js');
test('default trailing', () => {
  const c = clock(); const o = []; const d = debounce((x) => o.push(x), 100);
  d(1); d(2); c.tick(99); assert.deepEqual(o, []); c.tick(1); assert.deepEqual(o, [2]); c.restore();
});
test('leading only', () => {
  const c = clock(); const o = []; const d = debounce((x) => o.push(x), 100, { leading: true, trailing: false });
  d(1); d(2); assert.deepEqual(o, [1]); c.tick(200); assert.deepEqual(o, [1]); d(3); assert.deepEqual(o, [1, 3]); c.restore();
});
test('leading + trailing, single call fires once', () => {
  const c = clock(); const o = []; const d = debounce((x) => o.push(x), 100, { leading: true });
  d(1); c.tick(200); assert.deepEqual(o, [1]); d(2); d(3); c.tick(100); assert.deepEqual(o, [1, 2, 3]);
  c.restore();
});
test('leading+trailing burst gives first and last', () => {
  const c = clock(); const o = []; const d = debounce((x) => o.push(x), 100, { leading: true });
  d('a'); d('b'); d('c'); c.tick(100); assert.deepEqual(o, ['a', 'c']); c.restore();
});
test('maxWait forces call', () => {
  const c = clock(); const o = []; const d = debounce((x) => o.push(x), 100, { maxWait: 250 });
  for (let i = 0; i < 6; i++) { d(i); c.tick(60); }
  assert.deepEqual(o, [4]); c.tick(100); assert.deepEqual(o, [4, 5]); c.restore();
});
test('flush', () => {
  const c = clock(); const o = []; const d = debounce((x) => { o.push(x); return x * 2; }, 100);
  d(4); assert.equal(d.flush(), 8); assert.deepEqual(o, [4]); c.tick(500); assert.deepEqual(o, [4]); assert.equal(d.flush(), undefined); c.restore();
});
test('cancel', () => {
  const c = clock(); const o = []; const d = debounce((x) => o.push(x), 100);
  d(1); d.cancel(); c.tick(500); assert.deepEqual(o, []); c.restore();
});""")

# ---- formatting -----------------------------------------------------------------
js("ui-js-format-date", "write", "medium", "formatting",
   "Implement `formatDate(date, pattern)` in dates.js (`module.exports = { formatDate }`). `date` is a Date; use UTC getters. Pattern tokens: YYYY, YY, MMMM (January), MMM (Jan), MM, M, DD, D, HH (00-23), H, hh (01-12), h, mm, ss, A (AM/PM). Text inside square brackets is output literally, brackets removed, e.g. `[at] HH:mm`. Any other character is copied as is. Longer tokens win over shorter ones.",
   {"dates.js": stub("formatDate")},
   {"dates.js": """const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const p2 = (n) => String(n).padStart(2, '0');
function formatDate(d, pattern) {
  return pattern.replace(/\\[([^\\]]*)\\]|YYYY|YY|MMMM|MMM|MM|M|DD|D|HH|H|hh|h|mm|ss|A/g, (m, lit) => {
    if (lit !== undefined) return lit;
    const h12 = d.getUTCHours() % 12 || 12;
    switch (m) {
      case 'YYYY': return String(d.getUTCFullYear());
      case 'YY': return String(d.getUTCFullYear()).slice(-2);
      case 'MMMM': return MONTHS[d.getUTCMonth()];
      case 'MMM': return MONTHS[d.getUTCMonth()].slice(0, 3);
      case 'MM': return p2(d.getUTCMonth() + 1);
      case 'M': return String(d.getUTCMonth() + 1);
      case 'DD': return p2(d.getUTCDate());
      case 'D': return String(d.getUTCDate());
      case 'HH': return p2(d.getUTCHours());
      case 'H': return String(d.getUTCHours());
      case 'hh': return p2(h12);
      case 'h': return String(h12);
      case 'mm': return p2(d.getUTCMinutes());
      case 'ss': return p2(d.getUTCSeconds());
      case 'A': return d.getUTCHours() < 12 ? 'AM' : 'PM';
    }
  });
}
module.exports = { formatDate };"""},
   """const { formatDate } = require('./dates.js');
const d = new Date(Date.UTC(2024, 2, 5, 14, 7, 9));
test('iso-ish', () => assert.equal(formatDate(d, 'YYYY-MM-DD HH:mm:ss'), '2024-03-05 14:07:09'));
test('short', () => assert.equal(formatDate(d, 'D/M/YY'), '5/3/24'));
test('names', () => assert.equal(formatDate(d, 'MMMM D, YYYY'), 'March 5, 2024'));
test('mmm', () => assert.equal(formatDate(d, 'MMM DD'), 'Mar 05'));
test('12h', () => assert.equal(formatDate(d, 'h:mm A'), '2:07 PM'));
test('midnight', () => assert.equal(formatDate(new Date(Date.UTC(2024, 0, 1, 0, 5)), 'hh:mm A'), '12:05 AM'));
test('noon', () => assert.equal(formatDate(new Date(Date.UTC(2024, 0, 1, 12, 0)), 'h A'), '12 PM'));
test('literal', () => assert.equal(formatDate(d, '[Day] D [of] MMMM'), 'Day 5 of March'));
test('literal with tokens inside', () => assert.equal(formatDate(d, '[YYYY] YYYY'), 'YYYY 2024'));""",
   visible="formatDate(new Date(Date.UTC(2024, 2, 5, 14, 7, 9)), 'YYYY-MM-DD HH:mm') // '2024-03-05 14:07'")

js("ui-js-relative-time", "write", "medium", "formatting",
   "Implement `relativeTime(then, now)` in rel.js (`module.exports = { relativeTime }`); both arguments are epoch milliseconds. Return 'just now' if the absolute difference is under 60 seconds. Otherwise pick the largest unit among minute, hour, day (24h), month (30 days), year (365 days) whose floor value is >= 1, and return `'N unit(s) ago'` for the past or `'in N unit(s)'` for the future; use the singular for N = 1 ('1 hour ago', 'in 1 day').",
   {"rel.js": stub("relativeTime")},
   {"rel.js": """function relativeTime(then, now) {
  const diff = then - now, abs = Math.abs(diff);
  const S = 1000, M = 60 * S, H = 60 * M, D = 24 * H;
  if (abs < M) return 'just now';
  const units = [['year', 365 * D], ['month', 30 * D], ['day', D], ['hour', H], ['minute', M]];
  for (const [name, ms] of units) {
    const n = Math.floor(abs / ms);
    if (n >= 1) { const label = n + ' ' + name + (n === 1 ? '' : 's'); return diff < 0 ? label + ' ago' : 'in ' + label; }
  }
}
module.exports = { relativeTime };"""},
   """const { relativeTime } = require('./rel.js');
const now = 1700000000000, M = 60000, H = 3600000, D = 86400000;
test('just now', () => { assert.equal(relativeTime(now - 59000, now), 'just now'); assert.equal(relativeTime(now + 30000, now), 'just now'); });
test('minutes', () => { assert.equal(relativeTime(now - M, now), '1 minute ago'); assert.equal(relativeTime(now - 5 * M - 10, now), '5 minutes ago'); });
test('future', () => { assert.equal(relativeTime(now + 2 * H + 5, now), 'in 2 hours'); assert.equal(relativeTime(now + D, now), 'in 1 day'); });
test('hours edge', () => { assert.equal(relativeTime(now - 59 * M, now), '59 minutes ago'); assert.equal(relativeTime(now - H, now), '1 hour ago'); });
test('days/months/years', () => {
  assert.equal(relativeTime(now - 29 * D, now), '29 days ago'); assert.equal(relativeTime(now - 30 * D, now), '1 month ago');
  assert.equal(relativeTime(now - 400 * D, now), '1 year ago'); assert.equal(relativeTime(now + 800 * D, now), 'in 2 years');
});""")

js("ui-js-currency", "write", "medium", "formatting",
   "Implement `formatCurrency(amount, opts)` in money.js (`module.exports = { formatCurrency }`) without Intl. Options: `symbol` (default '$'), `decimals` (default 2), `thousands` (default ','), `decimal` (default '.'). Round half away from zero to `decimals`, group the integer part in threes, and put the minus sign before the symbol: `-$1,234.50`. Never output '-$0.00' (a negative amount that rounds to zero is formatted as positive).",
   {"money.js": stub("formatCurrency")},
   {"money.js": """function formatCurrency(amount, opts = {}) {
  const { symbol = '$', decimals = 2, thousands = ',', decimal = '.' } = opts;
  const f = 10 ** decimals;
  const r = Math.round(Math.abs(amount) * f + 1e-9);
  const neg = amount < 0 && r > 0;
  const s = String(r).padStart(decimals + 1, '0');
  const int = decimals ? s.slice(0, -decimals) : s, frac = decimals ? s.slice(-decimals) : '';
  const grouped = int.replace(/\\B(?=(\\d{3})+(?!\\d))/g, thousands);
  return (neg ? '-' : '') + symbol + grouped + (decimals ? decimal + frac : '');
}
module.exports = { formatCurrency };"""},
   """const { formatCurrency: f } = require('./money.js');
test('basic', () => { assert.equal(f(5), '$5.00'); assert.equal(f(1234.5), '$1,234.50'); });
test('big', () => assert.equal(f(1234567.891), '$1,234,567.89'));
test('negative', () => assert.equal(f(-1234.5), '-$1,234.50'));
test('negative zero', () => { assert.equal(f(-0.001), '$0.00'); assert.equal(f(0), '$0.00'); });
test('small', () => assert.equal(f(0.07), '$0.07'));
test('options', () => assert.equal(f(1234567.5, { symbol: '€', thousands: '.', decimal: ',' }), '€1.234.567,50'));
test('no decimals', () => { assert.equal(f(1999.5, { decimals: 0 }), '$2,000'); assert.equal(f(999, { decimals: 0 }), '$999'); });
test('rounding', () => { assert.equal(f(2.675, { decimals: 2 }), '$2.68'); assert.equal(f(0.999), '$1.00'); });""")

js("ui-js-bytes", "write", "easy", "formatting",
   "Implement `formatBytes(n, decimals = 1)` in bytes.js (`module.exports = { formatBytes }`): base 1024, units B, KB, MB, GB, TB. 0 -> '0 B'; values below 1024 print as integers with ' B'. Otherwise round to `decimals` places and drop trailing zeros ('1 KB', '1.5 KB'). Values >= 1024 TB stay in TB. Throw a RangeError for negative or non-finite input.",
   {"bytes.js": stub("formatBytes")},
   {"bytes.js": """function formatBytes(n, decimals = 1) {
  if (!Number.isFinite(n) || n < 0) throw new RangeError('invalid size');
  if (n < 1024) return Math.round(n) + ' B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0, v = n;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return String(Number(v.toFixed(decimals))) + ' ' + units[i];
}
module.exports = { formatBytes };"""},
   """const { formatBytes: f } = require('./bytes.js');
test('small', () => { assert.equal(f(0), '0 B'); assert.equal(f(1023), '1023 B'); });
test('kb', () => { assert.equal(f(1024), '1 KB'); assert.equal(f(1536), '1.5 KB'); });
test('mb gb', () => { assert.equal(f(1048576), '1 MB'); assert.equal(f(5 * 1024 ** 3), '5 GB'); });
test('decimals', () => { assert.equal(f(1234567, 2), '1.18 MB'); assert.equal(f(1234567, 0), '1 MB'); });
test('tb cap', () => assert.equal(f(2048 * 1024 ** 4), '2048 TB'));
test('invalid', () => { assert.throws(() => f(-1), RangeError); assert.throws(() => f(NaN), RangeError); });""")

js("ui-js-duration", "write", "easy", "formatting",
   "Implement `formatDuration(seconds)` in dur.js (`module.exports = { formatDuration }`). Floor to whole seconds. Under a minute: '45s'. Under an hour: '1m 05s' (seconds zero-padded). One hour or more: '1h 02m 03s' (minutes and seconds zero-padded). 0 -> '0s'. Negative input throws RangeError.",
   {"dur.js": stub("formatDuration")},
   {"dur.js": """function formatDuration(sec) {
  if (!(sec >= 0)) throw new RangeError('negative');
  const s = Math.floor(sec), p = (n) => String(n).padStart(2, '0');
  if (s < 60) return s + 's';
  if (s < 3600) return Math.floor(s / 60) + 'm ' + p(s % 60) + 's';
  return Math.floor(s / 3600) + 'h ' + p(Math.floor(s % 3600 / 60)) + 'm ' + p(s % 60) + 's';
}
module.exports = { formatDuration };"""},
   """const { formatDuration: f } = require('./dur.js');
test('s', () => { assert.equal(f(0), '0s'); assert.equal(f(45.9), '45s'); });
test('m', () => { assert.equal(f(60), '1m 00s'); assert.equal(f(65), '1m 05s'); assert.equal(f(3599), '59m 59s'); });
test('h', () => { assert.equal(f(3600), '1h 00m 00s'); assert.equal(f(3723), '1h 02m 03s'); assert.equal(f(100000), '27h 46m 40s'); });
test('neg', () => assert.throws(() => f(-1), RangeError));""")

js("ui-js-truncate", "write", "easy", "text",
   "Implement `truncate(text, max)` in text.js (`module.exports = { truncate }`). If `text.length <= max` return it unchanged. Otherwise the result (including a final '…' character) must be at most `max` characters long. Prefer cutting at the last whitespace within the first `max - 1` characters (and trim trailing whitespace before adding '…'); if there is no whitespace to cut at (index 0 or none), hard-cut at `max - 1`.",
   {"text.js": stub("truncate")},
   {"text.js": """function truncate(text, max) {
  if (text.length <= max) return text;
  const head = text.slice(0, max - 1);
  const i = head.search(/\\s\\S*$/);
  const cut = i > 0 ? head.slice(0, i) : head;
  return cut.trimEnd() + '…';
}
module.exports = { truncate };"""},
   """const { truncate: t } = require('./text.js');
test('short', () => assert.equal(t('hello', 5), 'hello'));
test('word boundary', () => assert.equal(t('The quick brown fox', 12), 'The quick…'));
test('hard cut', () => assert.equal(t('abcdefghij', 5), 'abcd…'));
test('length bound', () => { const r = t('lorem ipsum dolor sit amet consectetur', 20); assert.ok(r.length <= 20); assert.ok(r.endsWith('…')); assert.equal(r, 'lorem ipsum dolor…'); });
test('leading space only', () => assert.equal(t(' abcdefgh', 4), ' ab…'));
test('boundary exact', () => assert.equal(t('abc def', 7), 'abc def'));""")

js("ui-js-slugify", "write", "easy", "text",
   "Implement `slugify(s)` in slug.js (`module.exports = { slugify }`): lowercase, strip diacritics (NFD, remove combining marks), replace every run of non-alphanumeric ASCII characters with a single '-', and trim '-' from both ends. Non-strings are converted with String().",
   {"slug.js": stub("slugify")},
   {"slug.js": """function slugify(s) {
  return String(s).normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}
module.exports = { slugify };"""},
   """const { slugify: s } = require('./slug.js');
test('basic', () => assert.equal(s('Hello World'), 'hello-world'));
test('diacritics', () => assert.equal(s('Héllo,  Wörld!'), 'hello-world'));
test('trim', () => assert.equal(s('  --Hi--  '), 'hi'));
test('numbers', () => assert.equal(s('Top 10 tips & tricks'), 'top-10-tips-tricks'));
test('non-string', () => assert.equal(s(42), '42'));
test('empty', () => assert.equal(s('!!!'), ''));
test('repeated calls (no global regex state)', () => { for (let i = 0; i < 3; i++) assert.equal(s('A B'), 'a-b'); });""")

js("ui-js-escape-html", "write", "easy", "security",
   "Implement `escapeHtml(v)` in esc.js (`module.exports = { escapeHtml }`): escape & < > \" ' as &amp; &lt; &gt; &quot; &#39;. null and undefined become ''. Other values are converted with String() first. Also export `html` as a tagged template function that escapes every interpolated value but not the literal parts: html`<b>${name}</b>`.",
   {"esc.js": stub("escapeHtml", "html")},
   {"esc.js": """const MAP = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
function escapeHtml(v) {
  if (v === null || v === undefined) return '';
  return String(v).replace(/[&<>"']/g, (c) => MAP[c]);
}
function html(strings, ...vals) {
  return strings.reduce((out, s, i) => out + s + (i < vals.length ? escapeHtml(vals[i]) : ''), '');
}
module.exports = { escapeHtml, html };"""},
   """const { escapeHtml: e, html } = require('./esc.js');
test('all chars', () => assert.equal(e(`<a href="x">Tom & 'Jerry'</a>`), '&lt;a href=&quot;x&quot;&gt;Tom &amp; &#39;Jerry&#39;&lt;/a&gt;'));
test('no double-escape order', () => assert.equal(e('&lt;'), '&amp;lt;'));
test('null', () => { assert.equal(e(null), ''); assert.equal(e(undefined), ''); });
test('number', () => assert.equal(e(0), '0'));
test('tag', () => assert.equal(html`<b>${'<i>'}</b>${5}`, '<b>&lt;i&gt;</b>5'));
test('tag none', () => assert.equal(html`<p>x</p>`, '<p>x</p>'));""")

js("ui-js-classnames", "write", "easy", "utilities",
   "Implement `classNames(...args)` in cx.js (`module.exports = { classNames }`): returns a space-joined class string. Strings and numbers (non-zero) are included as is; falsy values are ignored; arrays are flattened recursively; objects include each key whose value is truthy. No dedupe, no extra spaces.",
   {"cx.js": stub("classNames")},
   {"cx.js": """function classNames(...args) {
  const out = [];
  for (const a of args) {
    if (!a) continue;
    if (typeof a === 'string' || typeof a === 'number') out.push(String(a));
    else if (Array.isArray(a)) { const s = classNames(...a); if (s) out.push(s); }
    else if (typeof a === 'object') for (const k of Object.keys(a)) if (a[k]) out.push(k);
  }
  return out.join(' ');
}
module.exports = { classNames };"""},
   """const { classNames: cx } = require('./cx.js');
test('strings', () => assert.equal(cx('a', 'b'), 'a b'));
test('falsy', () => assert.equal(cx('a', null, undefined, false, 0, '', 'b'), 'a b'));
test('object', () => assert.equal(cx({ a: true, b: false, c: 1 }), 'a c'));
test('nested', () => assert.equal(cx('x', ['y', ['z', { w: true }]], [], [null]), 'x y z w'));
test('number', () => assert.equal(cx('a', 3), 'a 3'));
test('empty', () => assert.equal(cx(), ''));""")

js("ui-js-querystring", "write", "medium", "utilities",
   "Implement `parseQuery(str)` and `buildQuery(obj)` in qs.js (`module.exports = { parseQuery, buildQuery }`). parseQuery accepts strings with or without a leading '?', splits on '&', decodes keys and values with decodeURIComponent after turning '+' into space, a key without '=' has value ''; repeated keys produce an array in order of appearance (a single occurrence stays a string); empty segments are skipped. buildQuery encodes with encodeURIComponent, skips null/undefined values, emits arrays as repeated keys, and returns the string without a leading '?'.",
   {"qs.js": stub("parseQuery", "buildQuery")},
   {"qs.js": """function parseQuery(str) {
  const out = {};
  for (const part of str.replace(/^\\?/, '').split('&')) {
    if (!part) continue;
    const i = part.indexOf('=');
    const dec = (s) => decodeURIComponent(s.replace(/\\+/g, ' '));
    const k = dec(i < 0 ? part : part.slice(0, i)), v = i < 0 ? '' : dec(part.slice(i + 1));
    if (Object.prototype.hasOwnProperty.call(out, k)) out[k] = [].concat(out[k], v); else out[k] = v;
  }
  return out;
}
function buildQuery(obj) {
  const parts = [];
  for (const k of Object.keys(obj)) {
    for (const v of [].concat(obj[k])) if (v !== null && v !== undefined) parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
  }
  return parts.join('&');
}
module.exports = { parseQuery, buildQuery };"""},
   """const { parseQuery: p, buildQuery: b } = require('./qs.js');
test('parse basic', () => assert.deepEqual(p('?a=1&b=x%20y'), { a: '1', b: 'x y' }));
test('parse plus', () => assert.deepEqual(p('q=a+b'), { q: 'a b' }));
test('parse repeated', () => assert.deepEqual(p('a=1&a=2&a=3&b=0'), { a: ['1', '2', '3'], b: '0' }));
test('parse flag/empty', () => assert.deepEqual(p('x&&y='), { x: '', y: '' }));
test('parse value with =', () => assert.deepEqual(p('t=a=b'), { t: 'a=b' }));
test('parse empty', () => assert.deepEqual(p(''), {}));
test('build', () => assert.equal(b({ a: 1, b: 'x y', c: null, d: undefined }), 'a=1&b=x%20y'));
test('build arrays', () => assert.equal(b({ t: ['a', 'b&c'] }), 't=a&t=b%26c'));
test('hasOwnProperty key', () => assert.deepEqual(p('constructor=1'), { constructor: '1' }));""")

js("ui-js-template", "write", "medium", "text",
   "Implement `render(template, data)` in tpl.js (`module.exports = { render }`). `{{ path.to.value }}` (whitespace around the path allowed) inserts the value HTML-escaped (& < > \" '); `{{{ path }}}` inserts it raw. Paths use dots and may index arrays (`items.0.name`). Missing/null/undefined values render as ''. Numbers and booleans are stringified (false -> 'false', 0 -> '0'). Everything else in the template is literal.",
   {"tpl.js": stub("render")},
   {"tpl.js": """const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
function get(data, path) {
  let v = data;
  for (const k of path.split('.')) { if (v === null || v === undefined) return ''; v = v[k]; }
  return v === null || v === undefined ? '' : v;
}
function render(tpl, data) {
  return tpl.replace(/\\{\\{\\{\\s*([\\w.]+)\\s*\\}\\}\\}|\\{\\{\\s*([\\w.]+)\\s*\\}\\}/g, (m, raw, esced) => raw ? String(get(data, raw)) : esc(get(data, esced)));
}
module.exports = { render };"""},
   """const { render: r } = require('./tpl.js');
test('simple', () => assert.equal(r('Hi {{name}}!', { name: 'Ann' }), 'Hi Ann!'));
test('spaces', () => assert.equal(r('{{  a.b }}', { a: { b: 2 } }), '2'));
test('escape', () => assert.equal(r('{{x}}', { x: '<b>"&"</b>' }), '&lt;b&gt;&quot;&amp;&quot;&lt;/b&gt;'));
test('raw', () => assert.equal(r('{{{x}}}', { x: '<b>' }), '<b>'));
test('missing', () => assert.equal(r('[{{a.b.c}}][{{z}}]', { a: {} }), '[][]'));
test('array', () => assert.equal(r('{{items.1.n}}', { items: [{ n: 'a' }, { n: 'b' }] }), 'b'));
test('falsy values', () => assert.equal(r('{{a}}|{{b}}|{{c}}', { a: 0, b: false, c: null }), '0|false|'));
test('literal braces', () => assert.equal(r('{ {a} }', { a: 1 }), '{ {a} }'));""")

js("ui-js-route-match", "write", "medium", "routing",
   "Implement `matchRoute(pattern, path)` in router.js (`module.exports = { matchRoute }`). Return an object of params or null. Patterns are segment based: literal segments must match exactly, `:name` captures one non-empty segment (value decoded with decodeURIComponent), and a final `*` captures the rest of the path (joined with '/') as params['*'] (may be empty string). A trailing slash on either side is ignored. Ignore any `?query` or `#hash` part of `path`. A match without params returns {}.",
   {"router.js": stub("matchRoute")},
   {"router.js": """function matchRoute(pattern, path) {
  path = path.split(/[?#]/)[0];
  const pp = pattern.split('/').filter(Boolean), ps = path.split('/').filter(Boolean);
  const params = {};
  for (let i = 0; i < pp.length; i++) {
    const seg = pp[i];
    if (seg === '*' && i === pp.length - 1) { params['*'] = ps.slice(i).join('/'); return params; }
    if (i >= ps.length) return null;
    if (seg[0] === ':') params[seg.slice(1)] = decodeURIComponent(ps[i]);
    else if (seg !== ps[i]) return null;
  }
  return ps.length === pp.length ? params : null;
}
module.exports = { matchRoute };"""},
   """const { matchRoute: m } = require('./router.js');
test('literal', () => { assert.deepEqual(m('/about', '/about'), {}); assert.equal(m('/about', '/contact'), null); });
test('param', () => assert.deepEqual(m('/users/:id', '/users/42'), { id: '42' }));
test('two params', () => assert.deepEqual(m('/u/:a/p/:b', '/u/x/p/y/'), { a: 'x', b: 'y' }));
test('length mismatch', () => { assert.equal(m('/users/:id', '/users'), null); assert.equal(m('/users/:id', '/users/1/edit'), null); });
test('decode', () => assert.deepEqual(m('/t/:name', '/t/a%20b'), { name: 'a b' }));
test('wildcard', () => { assert.deepEqual(m('/files/*', '/files/a/b/c.txt'), { '*': 'a/b/c.txt' }); assert.deepEqual(m('/files/*', '/files'), { '*': '' }); });
test('query/hash ignored', () => assert.deepEqual(m('/s/:q', '/s/hi?x=1#top'), { q: 'hi' }));
test('root', () => { assert.deepEqual(m('/', '/'), {}); assert.equal(m('/', '/x'), null); });""")
