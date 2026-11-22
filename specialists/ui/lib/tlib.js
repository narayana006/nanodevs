'use strict';
// Test helpers for UI tasks. DOM-free; includes fake clock and a tiny DOM stub.
const assert = require('node:assert/strict');
let failed = 0, n = 0; const pending = [];
function report(name, e) { failed++; console.log('FAIL ' + name + ' - ' + String(e && e.message).split('\n')[0].slice(0, 200)); }
// test(name, fn): fn may be async; finish() waits for all of them.
function test(name, fn) {
  n++;
  try { const r = fn(); if (r && typeof r.then === 'function') pending.push(r.catch((e) => report(name, e))); } catch (e) { report(name, e); }
}
function finish() {
  Promise.all(pending).then(() => { console.log((n - failed) + '/' + n + ' passed'); process.exit(failed || n === 0 ? 1 : 0); });
}

// Fake clock: replaces global setTimeout/clearTimeout/setInterval/clearInterval/Date.now.
function clock() {
  let now = 1000, id = 0, timers = [];
  const real = { st: globalThis.setTimeout, ct: globalThis.clearTimeout, si: globalThis.setInterval, ci: globalThis.clearInterval, now: Date.now };
  globalThis.setTimeout = (fn, ms = 0, ...a) => { timers.push({ id: ++id, at: now + Math.max(0, ms), fn, a }); return id; };
  globalThis.setInterval = (fn, ms = 0, ...a) => { timers.push({ id: ++id, at: now + Math.max(1, ms), fn, a, every: Math.max(1, ms) }); return id; };
  globalThis.clearTimeout = globalThis.clearInterval = (i) => { timers = timers.filter(t => t.id !== i); };
  Date.now = () => now;
  return {
    now: () => now,
    pending: () => timers.length,
    tick(ms) {
      const end = now + ms;
      for (;;) {
        timers.sort((a, b) => a.at - b.at || a.id - b.id);
        const t = timers[0];
        if (!t || t.at > end) break;
        now = t.at;
        if (t.every) t.at += t.every; else timers.shift();
        t.fn(...t.a);
      }
      now = end;
    },
    restore() { Object.assign(globalThis, { setTimeout: real.st, clearTimeout: real.ct, setInterval: real.si, clearInterval: real.ci }); Date.now = real.now; },
  };
}

// ---- tiny DOM stub -------------------------------------------------------
function camelToData(k) { return 'data-' + k.replace(/[A-Z]/g, m => '-' + m.toLowerCase()); }
function matchSimple(el, sel) {
  // compound selector: tag#id.class[attr][attr=val]
  const re = /^([a-zA-Z0-9*-]+)?((?:[#.][\w-]+|\[[^\]]+\])*)$/;
  const m = re.exec(sel);
  if (!m) throw new Error('unsupported selector ' + sel);
  if (m[1] && m[1] !== '*' && el.tagName.toLowerCase() !== m[1].toLowerCase()) return false;
  const parts = m[2].match(/[#.][\w-]+|\[[^\]]+\]/g) || [];
  for (const p of parts) {
    if (p[0] === '#') { if (el.getAttribute('id') !== p.slice(1)) return false; }
    else if (p[0] === '.') { if (!el.classList.contains(p.slice(1))) return false; }
    else {
      const mm = /^\[([\w-]+)(?:=["']?([^\]"']*)["']?)?\]$/.exec(p);
      if (!mm) throw new Error('unsupported attr selector ' + p);
      if (!el.hasAttribute(mm[1])) return false;
      if (mm[2] !== undefined && el.getAttribute(mm[1]) !== mm[2]) return false;
    }
  }
  return true;
}
class El {
  constructor(tag, doc) {
    this.tagName = tag.toUpperCase(); this.ownerDocument = doc; this.attributes = {}; this.children = []; this.parentNode = null;
    this._l = {}; this._text = ''; this.style = {}; this.value = ''; this.checked = false; this.disabled = false;
    const self = this;
    this.classList = {
      _get: () => (self.attributes['class'] || '').split(/\s+/).filter(Boolean),
      contains(c) { return this._get().includes(c); },
      add(...cs) { const s = this._get(); for (const c of cs) if (!s.includes(c)) s.push(c); self.attributes['class'] = s.join(' '); },
      remove(...cs) { self.attributes['class'] = this._get().filter(c => !cs.includes(c)).join(' '); },
      toggle(c, force) { const has = this.contains(c); const want = force === undefined ? !has : !!force; want ? this.add(c) : this.remove(c); return want; },
    };
    this.dataset = new Proxy({}, {
      get: (_, k) => { const v = self.attributes[camelToData(String(k))]; return v === undefined ? undefined : v; },
      set: (_, k, v) => { self.attributes[camelToData(String(k))] = String(v); return true; },
    });
  }
  get id() { return this.getAttribute('id') || ''; } set id(v) { this.setAttribute('id', v); }
  get className() { return this.getAttribute('class') || ''; } set className(v) { this.setAttribute('class', v); }
  get hidden() { return this.hasAttribute('hidden'); } set hidden(v) { v ? this.setAttribute('hidden', '') : this.removeAttribute('hidden'); }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this.children.forEach(c => { c.parentNode = null; }); this.children = []; this._text = String(v); }
  get firstElementChild() { return this.children[0] || null; }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attributes, k) ? this.attributes[k] : null; }
  hasAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attributes, k); }
  removeAttribute(k) { delete this.attributes[k]; }
  appendChild(c) { if (c.parentNode) c.parentNode.removeChild(c); c.parentNode = this; this.children.push(c); return c; }
  append(...cs) { cs.forEach(c => this.appendChild(c)); }
  removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) { this.children.splice(i, 1); c.parentNode = null; } return c; }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
  addEventListener(t, f) { (this._l[t] = this._l[t] || []).push(f); }
  removeEventListener(t, f) { this._l[t] = (this._l[t] || []).filter(x => x !== f); }
  dispatchEvent(ev) {
    ev.target = ev.target || this; ev.defaultPrevented = !!ev.defaultPrevented;
    ev.preventDefault = ev.preventDefault || function () { this.defaultPrevented = true; };
    ev.stopPropagation = ev.stopPropagation || function () { this._stop = true; };
    for (let el = this; el && !ev._stop; el = el.parentNode) { ev.currentTarget = el; for (const f of (el._l[ev.type] || []).slice()) f.call(el, ev); }
    return !ev.defaultPrevented;
  }
  click() { return this.dispatchEvent({ type: 'click' }); }
  focus() { this.ownerDocument.activeElement = this; this.dispatchEvent({ type: 'focus' }); }
  matches(sel) { return sel.split(',').some(s => matchSimple(this, s.trim())); }
  querySelectorAll(sel) {
    const out = [];
    const alts = sel.split(',').map(s => s.trim());
    const walk = (el, ancestors) => {
      for (const c of el.children) {
        for (const a of alts) {
          const chain = a.split(/\s+/);
          if (!matchSimple(c, chain[chain.length - 1])) continue;
          let idx = chain.length - 2, ok = true;
          for (let p = c.parentNode; idx >= 0; p = p && p.parentNode) { if (!p || p === this.parentNode) { ok = false; break; } if (matchSimple(p, chain[idx])) idx--; }
          if (ok) { out.push(c); break; }
        }
        walk(c);
      }
    };
    walk(this);
    return out;
  }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
}
function makeDom() {
  const doc = { activeElement: null };
  doc.createElement = (t) => new El(t, doc);
  doc.body = doc.createElement('body');
  doc.querySelector = (s) => doc.body.querySelector(s);
  doc.querySelectorAll = (s) => doc.body.querySelectorAll(s);
  doc.getElementById = (id) => doc.body.querySelector('#' + id);
  // build(['div#x.c', {attr:'v'}, child, 'text'...])
  doc.build = function b(spec) {
    if (typeof spec === 'string') { const t = doc.createElement('span'); t._text = spec; return t; }
    const [head, ...rest] = spec; const m = /^([\w-]+)(#[\w-]+)?((?:\.[\w-]+)*)$/.exec(head);
    const el = doc.createElement(m[1]); if (m[2]) el.id = m[2].slice(1); if (m[3]) el.className = m[3].split('.').filter(Boolean).join(' ');
    for (const r of rest) { if (Array.isArray(r)) el.appendChild(b(r)); else if (typeof r === 'string') el._text += r; else for (const k in r) el.setAttribute(k, r[k]); }
    return el;
  };
  return doc;
}
function key(k, extra) { return Object.assign({ type: 'keydown', key: k }, extra || {}); }
module.exports = { test, finish, clock, makeDom, key, assert };
