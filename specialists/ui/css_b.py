from tb import py
from css_a import LOAD, HELP

FMT = " Return the complete style.css."

py("ui-css-fix-outline-none", "css", "css", "easy", "a11y",
   "style.css removes the focus outline on all interactive elements, so keyboard users cannot see where they are. Fix it: remove the blanket removal, and give `a`, `button`, `input`, `select`, `textarea` a visible `:focus-visible` outline (at least 2px solid, with a non-transparent colour and `outline-offset: 2px`). Keep the other declarations (colours, sizes)." + FMT,
   {"style.css": "a, button, input, select, textarea {\n  outline: none;\n}\nbutton {\n  background: #0b5fff;\n  color: #fff;\n  padding: 8px 12px;\n}\na { color: #0b5fff; }\n"},
   {"style.css": "a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {\n  outline: 2px solid #0b5fff;\n  outline-offset: 2px;\n}\nbutton {\n  background: #0b5fff;\n  color: #fff;\n  padding: 8px 12px;\n}\na { color: #0b5fff; }\n"},
   LOAD + HELP + """
bad = [r.sels for r in css.rules if r.decls.get('outline') in ('none', '0', '0px') or r.decls.get('outline-style') == 'none']
ok(not bad, 'no outline removal left: %r' % bad)
for t in ('a', 'button', 'input', 'select', 'textarea'):
    o = css.get(t + ':focus-visible', 'outline') or ''
    m = re.match(r'(\\d+(?:\\.\\d+)?)px\\s+(solid|dashed|double)\\s+(\\S+)$', o)
    ok(m is not None and float(m.group(1)) >= 2 and m.group(3) not in ('transparent',), t + ':focus-visible outline %r' % o)
    ok(num(css.get(t + ':focus-visible', 'outline-offset')) is not None and num(css.get(t + ':focus-visible', 'outline-offset')) >= 1, t + ' offset')
ok(css.get('button', 'background') == '#0b5fff' and css.get('button', 'color') == '#fff' and css.get('button', 'padding') == '8px 12px' and css.get('a', 'color') == '#0b5fff', 'other declarations kept')
""")

py("ui-css-fix-fixed-widths", "css", "css", "medium", "responsive",
   "On phones the page in style.css scrolls horizontally because of fixed pixel widths. Fix it without removing the desktop look: `.wrap` (was `width: 960px`) must be at most 960px wide but shrink on small screens (`max-width: 960px; width: 100%`), `.card` (was `width: 600px`) likewise (`max-width: 600px; width: 100%`), `img` must never overflow (`max-width: 100%; height: auto`), `.sidebar` (was `float: left; width: 300px`) should stack on screens up to 700px (`@media (max-width: 700px)` -> `float: none; width: 100%`), and `pre` must scroll internally (`overflow-x: auto`). Keep `.wrap { margin: 0 auto }`." + FMT,
   {"style.css": ".wrap { width: 960px; margin: 0 auto; }\n.card { width: 600px; padding: 16px; }\nimg { width: 800px; }\n.sidebar { float: left; width: 300px; }\npre { white-space: pre; }\n"},
   {"style.css": ".wrap { max-width: 960px; width: 100%; margin: 0 auto; }\n.card { max-width: 600px; width: 100%; padding: 16px; }\nimg { max-width: 100%; height: auto; }\n.sidebar { float: left; width: 300px; }\npre { white-space: pre; overflow-x: auto; }\n@media (max-width: 700px) {\n  .sidebar { float: none; width: 100%; }\n}\n"},
   LOAD + """
for s, mw in (('.wrap', '960px'), ('.card', '600px')):
    ok(css.get(s, 'max-width') == mw and css.get(s, 'width') in ('100%', 'auto'), s + ' max-width %s, fluid width: %r/%r' % (mw, css.get(s, 'max-width'), css.get(s, 'width')))
ok(css.get('.wrap', 'margin') == '0 auto', '.wrap centred')
ok(css.get('.card', 'padding') == '16px', '.card padding kept')
ok(css.get('img', 'max-width') == '100%' and css.get('img', 'height') == 'auto', 'img fluid')
ok(css.get('img', 'width') in (None, '100%', 'auto'), 'img has no fixed px width: %r' % css.get('img', 'width'))
ok(css.get('.sidebar', 'float') == 'left' and css.get('.sidebar', 'width') == '300px', 'sidebar desktop unchanged')
ok(css.get('.sidebar', 'float', '(max-width:700px)') == 'none' and css.get('.sidebar', 'width', '(max-width:700px)') == '100%', 'sidebar stacks')
ok(css.order('.sidebar', 'float', '(max-width:700px)') > css.order('.sidebar', 'float'), 'media after base rule')
ok(css.get('pre', 'overflow-x') == 'auto' or css.get('pre', 'overflow') == 'auto', 'pre scrolls')
""")

py("ui-css-fix-contrast", "css", "css", "medium", "a11y",
   "Several colour pairs in style.css fail WCAG AA contrast (4.5:1 for normal text). The page background is `#ffffff`. Fix the text/background colours so that: `.btn` (colour on its background), `.muted` (colour on the white page), `.error` (colour on white) and `.badge` (colour on its background) all reach at least 4.5:1. Keep the same hues roughly (darken light text, or darken button background), use plain hex colours (#rgb or #rrggbb), keep all the non-colour declarations." + FMT,
   {"style.css": "body { background: #ffffff; color: #222222; }\n.btn { background: #8ab4f8; color: #ffffff; padding: 8px 16px; }\n.muted { color: #aaaaaa; font-size: 14px; }\n.error { color: #ff6666; }\n.badge { background: #ffd54f; color: #ffffff; border-radius: 4px; }\n"},
   {"style.css": "body { background: #ffffff; color: #222222; }\n.btn { background: #1a56db; color: #ffffff; padding: 8px 16px; }\n.muted { color: #595959; font-size: 14px; }\n.error { color: #b00020; }\n.badge { background: #ffd54f; color: #3d2f00; border-radius: 4px; }\n"},
   LOAD + """
hexre = re.compile(r'^#[0-9a-f]{3}$|^#[0-9a-f]{6}$')
def cc(fg, bg, name):
    ok(bool(fg and bg and hexre.match(fg) and hexre.match(bg)), name + ' uses plain hex colours: %r on %r' % (fg, bg))
    if fg and bg and hexre.match(fg) and hexre.match(bg):
        r = contrast(fg, bg)
        ok(r >= 4.5, '%s contrast %.2f >= 4.5' % (name, r))
cc(css.get('.btn', 'color'), css.get('.btn', 'background'), '.btn')
cc(css.get('.muted', 'color'), css.get('body', 'background'), '.muted')
cc(css.get('.error', 'color'), css.get('body', 'background'), '.error')
cc(css.get('.badge', 'color'), css.get('.badge', 'background'), '.badge')
ok(css.get('body', 'background') == '#ffffff', 'page background unchanged')
ok(css.get('.btn', 'padding') == '8px 16px' and css.get('.muted', 'font-size') == '14px' and css.get('.badge', 'border-radius') == '4px', 'non-colour declarations kept')
""")

py("ui-css-fix-important", "css", "css", "hard", "specificity",
   "style.css wins specificity fights with `!important`, which makes it unmaintainable. Remove every `!important` and make the intended results come from selector specificity instead: the active nav link must still be blue (`#0b5fff`) despite the `#nav a` rule that makes links grey (`#555`), the `.btn.primary` must keep its white text over the generic `a.btn` colour, and `.hidden` must still hide (`display: none`) even for elements that also match `.card`. Specificity of the intended rule must be HIGHER than the conflicting one (or equal and later in the file). Keep all declared values." + FMT,
   {"style.css": "#nav a { color: #555; }\n.nav a.active { color: #0b5fff !important; }\na.btn { color: #222; }\n.btn.primary { color: #fff !important; }\n.card { display: block; }\n.hidden { display: none !important; }\n"},
   {"style.css": "#nav a { color: #555; }\n#nav a.active { color: #0b5fff; }\na.btn { color: #222; }\na.btn.primary { color: #fff; }\n.card { display: block; }\n.card.hidden, .hidden { display: none; }\n"},
   LOAD + """
ok('!important' not in open('style.css').read(), 'no !important left')
def winner(sels_props, prop):
    best = None
    for r in css.rules:
        for s in r.sels:
            if s in sels_props and prop in r.decls:
                key = (specificity(s), r.order)
                if best is None or key > best[0]:
                    best = (key, r.decls[prop], s)
    return best
# active link inside #nav: candidate selectors that match <a class="active"> inside #nav.nav
cand = ['#nav a', '.nav a.active', '#nav a.active', '#nav .active', '#nav a[class~="active"]', '.nav .active', '#nav.nav a.active', '.nav a:not(.x)']
w = winner(cand, 'color')
ok(w is not None and w[1] == '#0b5fff', 'active link ends up blue (winner %r)' % (w,))
w2 = winner(['a.btn', '.btn.primary', 'a.btn.primary', '.btn.primary:is(a)', '.primary'], 'color')
ok(w2 is not None and w2[1] == '#fff', 'primary button text stays white (winner %r)' % (w2,))
w3 = winner(['.card', '.hidden', '.card.hidden'], 'display')
ok(w3 is not None and w3[1] == 'none', '.hidden still hides cards (winner %r)' % (w3,))
ok(css.get('#nav a', 'color') == '#555' and css.get('a.btn', 'color') == '#222' and css.get('.card', 'display') == 'block', 'base rules kept')
""")

py("ui-css-fix-media-order", "css", "css", "medium", "responsive",
   "The responsive rules in style.css never take effect because they are written BEFORE the base rules they override (same specificity, later rule wins). Fix the ordering so that on screens up to 600px the sidebar is hidden, the layout is a single column and the font is smaller, while desktop keeps its values. Keep the declarations; only the structure/order may change. Do not use `!important`." + FMT,
   {"style.css": "@media (max-width: 600px) {\n  .sidebar { display: none; }\n  .layout { grid-template-columns: 1fr; }\n  body { font-size: 15px; }\n}\n.sidebar { display: block; width: 240px; }\n.layout { display: grid; grid-template-columns: 240px 1fr; }\nbody { font-size: 17px; }\n"},
   {"style.css": ".sidebar { display: block; width: 240px; }\n.layout { display: grid; grid-template-columns: 240px 1fr; }\nbody { font-size: 17px; }\n@media (max-width: 600px) {\n  .sidebar { display: none; }\n  .layout { grid-template-columns: 1fr; }\n  body { font-size: 15px; }\n}\n"},
   LOAD + """
m = '(max-width:600px)'
for sel, prop, base, small in (('.sidebar', 'display', 'block', 'none'), ('.layout', 'grid-template-columns', '240px 1fr', '1fr'), ('body', 'font-size', '17px', '15px')):
    ok(css.get(sel, prop) == base, '%s %s desktop value kept' % (sel, prop))
    ok(css.get(sel, prop, m) == small, '%s %s mobile value' % (sel, prop))
    ok(css.order(sel, prop, m) > css.order(sel, prop), '%s: media rule comes after base rule' % sel)
ok(css.get('.sidebar', 'width') == '240px' and css.get('.layout', 'display') == 'grid', 'other declarations kept')
ok('!important' not in open('style.css').read(), 'no !important')
""")

py("ui-css-fix-hover-only", "css", "css", "medium", "a11y",
   "Interactions in style.css only exist on `:hover`, so keyboard and touch users miss them. For every rule that styles `:hover`, add the same declarations for keyboard focus (`:focus-visible` for `.btn` and `.menu a`; `:focus-within` for `.card`) by extending the selector list (e.g. `.btn:hover, .btn:focus-visible`). Also wrap the hover effects in `@media (hover: hover)` so touch devices do not get stuck hover states: the `:hover` and `:focus-*` rules should live inside that media query. Keep base rules outside." + FMT,
   {"style.css": ".btn { background: #0b5fff; color: #fff; }\n.btn:hover { background: #0846c4; }\n.menu a { color: #333; text-decoration: none; }\n.menu a:hover { text-decoration: underline; }\n.card { box-shadow: none; }\n.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.2); }\n"},
   {"style.css": ".btn { background: #0b5fff; color: #fff; }\n.menu a { color: #333; text-decoration: none; }\n.card { box-shadow: none; }\n@media (hover: hover) {\n  .btn:hover, .btn:focus-visible { background: #0846c4; }\n  .menu a:hover, .menu a:focus-visible { text-decoration: underline; }\n  .card:hover, .card:focus-within { box-shadow: 0 4px 12px rgba(0,0,0,.2); }\n}\n"},
   LOAD + """
m = '(hover:hover)'
for base, state, prop, val in (('.btn', ':focus-visible', 'background', '#0846c4'), ('.menu a', ':focus-visible', 'text-decoration', 'underline'), ('.card', ':focus-within', 'box-shadow', '0 4px 12px rgba(0,0,0,.2)')):
    ok(css.get(base + ':hover', prop, m) == val, base + ':hover inside @media (hover: hover)')
    ok(css.get(base + state, prop, m) == val, base + state + ' mirrors hover')
    ok(css.get(base + ':hover', prop) is None and css.get(base + ':hover', prop, '*') == val, base + ':hover only exists inside the media query')
ok(css.get('.btn', 'background') == '#0b5fff' and css.get('.menu a', 'text-decoration') == 'none' and css.get('.card', 'box-shadow') == 'none', 'base rules stay at top level')
""")

py("ui-css-fix-flex-overflow", "css", "css", "hard", "layout",
   "In style.css the flex row `.row` overflows its container when a child contains a long word or URL, and the items never wrap on narrow screens. Fix: `.row` must wrap (`flex-wrap: wrap`) with a `gap: 12px`; the flexible text child `.row__text` must be allowed to shrink (`min-width: 0`) and break long words (`overflow-wrap: anywhere`); `.row__thumb` must not shrink (`flex: none` or `flex-shrink: 0`) and keep `width: 64px; height: 64px`. Keep `display: flex` and `align-items: center`." + FMT,
   {"style.css": ".row { display: flex; align-items: center; }\n.row__thumb { width: 64px; height: 64px; margin-right: 12px; }\n.row__text { flex: 1; }\n"},
   {"style.css": ".row { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; }\n.row__thumb { width: 64px; height: 64px; flex: none; }\n.row__text { flex: 1; min-width: 0; overflow-wrap: anywhere; }\n"},
   LOAD + """
r = lambda p: css.get('.row', p)
ok(r('display') == 'flex' and r('align-items') == 'center' and r('flex-wrap') == 'wrap' and r('gap') == '12px', '.row')
t = lambda p: css.get('.row__thumb', p)
ok(t('width') == '64px' and t('height') == '64px', 'thumb size kept')
ok(t('flex') in ('none', '0 0 auto', '0 0 64px') or t('flex-shrink') == '0', 'thumb does not shrink')
x = lambda p: css.get('.row__text', p)
ok(x('flex') in ('1', '1 1 0%', '1 1 0', '1 1 0px') and x('min-width') in ('0', '0px'), 'text shrinks (min-width: 0)')
ok(x('overflow-wrap') == 'anywhere' or x('word-break') == 'break-word' or x('word-break') == 'break-all', 'long words break')
ok(t('margin-right') in (None, '0'), 'gap replaces margin-right')
""")

py("ui-css-fix-readability", "css", "css", "easy", "typography",
   "The article text in style.css is hard to read. Fix `.prose`: font size at least 16px (use `1rem` or `1.0625rem`, not tiny px), line-height unitless between 1.4 and 1.8, line length limited with `max-width` between 55ch and 75ch, paragraph spacing `p + p { margin-top: 1em }` (use em), and `a` inside `.prose` underlined (`text-decoration: underline`) so links do not rely on colour alone. Keep `.prose { color: #1f2937 }`." + FMT,
   {"style.css": ".prose {\n  font-size: 11px;\n  line-height: 1;\n  color: #1f2937;\n}\n.prose a { text-decoration: none; color: #0b5fff; }\n.prose p + p { margin-top: 0; }\n"},
   {"style.css": ".prose {\n  font-size: 1rem;\n  line-height: 1.6;\n  max-width: 65ch;\n  color: #1f2937;\n}\n.prose a { text-decoration: underline; color: #0b5fff; }\n.prose p + p { margin-top: 1em; }\n"},
   LOAD + HELP + """
fs = css.get('.prose', 'font-size') or ''
v = num(fs)
ok(v is not None and ((fs.endswith('rem') or fs.endswith('em')) and v >= 1 or fs.endswith('px') and v >= 16), 'font-size >= 16px: %r' % fs)
lh = css.get('.prose', 'line-height') or ''
ok(re.fullmatch(r'[0-9.]+', lh) is not None and 1.4 <= float(lh) <= 1.8, 'unitless line-height 1.4-1.8: %r' % lh)
mw = css.get('.prose', 'max-width') or ''
ok(mw.endswith('ch') and 55 <= num(mw) <= 75, 'max-width 55-75ch: %r' % mw)
ok(css.get('.prose a', 'text-decoration') == 'underline' or (css.get('.prose a', 'text-decoration-line') == 'underline'), 'links underlined')
ok((css.get('.prose p+p', 'margin-top') or '').endswith('em') and num(css.get('.prose p+p', 'margin-top')) >= 0.75, 'paragraph spacing in em')
ok(css.get('.prose', 'color') == '#1f2937', 'colour kept')
""")
