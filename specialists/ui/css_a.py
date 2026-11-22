from tb import py

LOAD = "css = Css(open('style.css').read())\nimport re\n"
HELP = """
def ncols(v):
    if not v: return 0
    m = re.match(r'repeat\\((\\d+),', v)
    if m: return int(m.group(1))
    return len([t for t in re.split(r'\\s+(?![^()]*\\))', v.strip()) if t])
def num(v):
    m = re.match(r'(-?[0-9.]+)', v or '')
    return float(m.group(1)) if m else None
"""
FMT = " Return the complete style.css."
EMPTYCSS = "/* TODO */\n"

py("ui-css-grid-responsive", "css", "css", "easy", "responsive",
   "Write style.css for a card grid: `.grid` is a CSS grid with 3 equal columns and a `16px` gap; at viewport widths up to 768px it has 2 equal columns; up to 480px just 1 column. Use `@media (max-width: 768px)` and `@media (max-width: 480px)` (desktop-first, written in that order so the narrower rule wins)." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".grid {\n  display: grid;\n  grid-template-columns: repeat(3, 1fr);\n  gap: 16px;\n}\n@media (max-width: 768px) {\n  .grid { grid-template-columns: repeat(2, 1fr); }\n}\n@media (max-width: 480px) {\n  .grid { grid-template-columns: 1fr; }\n}\n"},
   LOAD + HELP + """
ok(css.get('.grid', 'display') == 'grid', 'display grid')
ok(ncols(css.get('.grid', 'grid-template-columns')) == 3, 'three columns on desktop: %r' % css.get('.grid', 'grid-template-columns'))
ok(css.get('.grid', 'gap') in ('16px', '16px 16px') or css.get('.grid', 'grid-gap') == '16px', 'gap 16px')
ok(ncols(css.get('.grid', 'grid-template-columns', '(max-width:768px)')) == 2, 'two columns at 768')
ok(ncols(css.get('.grid', 'grid-template-columns', '(max-width:480px)')) == 1, 'one column at 480')
ok(css.order('.grid', 'grid-template-columns', '(max-width:480px)') > css.order('.grid', 'grid-template-columns', '(max-width:768px)') > css.order('.grid', 'grid-template-columns'), 'source order lets narrower rule win')
""")

py("ui-css-mobile-first-nav", "css", "css", "medium", "responsive",
   "Write mobile-first CSS for a nav in style.css: by default `.nav` is `display: flex` with `flex-direction: column` and `gap: 8px`, and `.nav a` has `padding: 12px 16px` and `display: block`. From 768px up (`@media (min-width: 768px)`) `.nav` becomes a row (`flex-direction: row`, `gap: 24px`, `align-items: center`) and `.nav a` gets `padding: 8px 12px`. Do not use max-width queries." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".nav {\n  display: flex;\n  flex-direction: column;\n  gap: 8px;\n}\n.nav a {\n  display: block;\n  padding: 12px 16px;\n}\n@media (min-width: 768px) {\n  .nav {\n    flex-direction: row;\n    gap: 24px;\n    align-items: center;\n  }\n  .nav a { padding: 8px 12px; }\n}\n"},
   LOAD + """
ok(css.get('.nav', 'display') == 'flex' and css.get('.nav', 'flex-direction') == 'column' and css.get('.nav', 'gap') == '8px', 'base nav column')
ok(css.get('.nav a', 'display') == 'block' and css.get('.nav a', 'padding') == '12px 16px', 'base links')
m = '(min-width:768px)'
ok(css.get('.nav', 'flex-direction', m) == 'row' and css.get('.nav', 'gap', m) == '24px' and css.get('.nav', 'align-items', m) == 'center', 'desktop row')
ok(css.get('.nav a', 'padding', m) == '8px 12px', 'desktop link padding')
ok(not [c for c in css.medias() if 'max-width' in c], 'no max-width queries')
ok(css.order('.nav', 'flex-direction', m) > css.order('.nav', 'flex-direction'), 'media after base')
""")

py("ui-css-sr-only", "css", "css", "medium", "a11y",
   "Write the standard visually-hidden utility in style.css. `.sr-only` must remove the element visually but keep it available to screen readers: `position: absolute`, `width: 1px`, `height: 1px`, `padding: 0`, `margin: -1px`, `overflow: hidden`, a clipping rule (`clip: rect(0, 0, 0, 0)` or `clip-path: inset(50%)`), `white-space: nowrap`, `border: 0`. It must NOT use `display: none`, `visibility: hidden`, or `width/height: 0`. Also write `.sr-only-focusable:focus, .sr-only-focusable:active` which undoes it for skip links: `position: static`, `width: auto`, `height: auto`, `margin: 0`, `overflow: visible`, `white-space: normal`, and `clip: auto` (and `clip-path: none`)." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".sr-only {\n  position: absolute;\n  width: 1px;\n  height: 1px;\n  padding: 0;\n  margin: -1px;\n  overflow: hidden;\n  clip: rect(0, 0, 0, 0);\n  clip-path: inset(50%);\n  white-space: nowrap;\n  border: 0;\n}\n.sr-only-focusable:focus,\n.sr-only-focusable:active {\n  position: static;\n  width: auto;\n  height: auto;\n  margin: 0;\n  overflow: visible;\n  clip: auto;\n  clip-path: none;\n  white-space: normal;\n}\n"},
   LOAD + """
g = lambda p: css.get('.sr-only', p)
ok(g('position') == 'absolute', 'position absolute')
ok(g('width') == '1px' and g('height') == '1px', '1px box')
ok(g('padding') in ('0', '0px') and g('margin') == '-1px', 'padding 0, margin -1px')
ok(g('overflow') == 'hidden', 'overflow hidden')
ok((g('clip') or '').replace(' ', '') in ('rect(0,0,0,0)', 'rect(0px,0px,0px,0px)') or (g('clip-path') or '').startswith('inset(50%'), 'clip')
ok(g('white-space') == 'nowrap', 'nowrap')
ok(g('border') in ('0', '0px', 'none'), 'border 0')
ok(g('display') != 'none' and g('visibility') != 'hidden', 'not display none / hidden')
for sel in ('.sr-only-focusable:focus', '.sr-only-focusable:active'):
    ok(css.get(sel, 'position') == 'static', sel + ' position static')
    ok(css.get(sel, 'width') == 'auto' and css.get(sel, 'height') == 'auto', sel + ' auto size')
    ok(css.get(sel, 'margin') in ('0', '0px'), sel + ' margin 0')
    ok(css.get(sel, 'overflow') == 'visible' and css.get(sel, 'white-space') == 'normal', sel + ' overflow/white-space')
    ok(css.get(sel, 'clip') == 'auto' and css.get(sel, 'clip-path') == 'none', sel + ' clip reset')
""")

py("ui-css-focus-visible", "css", "css", "medium", "a11y",
   "Write focus styles in style.css for buttons and links. `.btn:focus-visible` and `a:focus-visible` must show a clear outline: `outline` of at least 2px solid in colour `#1a56db`, with `outline-offset: 2px`. Mouse users should not get a ring on click: `.btn:focus:not(:focus-visible)` has `outline: none`. Never remove the outline globally (no bare `.btn:focus { outline: none }` and no `* { outline: 0 }`). Also give `.btn` a base style: `background: #1a56db; color: #fff; padding: 8px 16px; border: 0; border-radius: 4px`." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".btn {\n  background: #1a56db;\n  color: #fff;\n  padding: 8px 16px;\n  border: 0;\n  border-radius: 4px;\n}\n.btn:focus-visible,\na:focus-visible {\n  outline: 3px solid #1a56db;\n  outline-offset: 2px;\n}\n.btn:focus:not(:focus-visible) {\n  outline: none;\n}\n"},
   LOAD + HELP + """
for sel in ('.btn:focus-visible', 'a:focus-visible'):
    o = css.get(sel, 'outline') or ''
    m = re.match(r'(\\d+(?:\\.\\d+)?)px\\s+solid\\s+(#[0-9a-f]{3,6})$', o)
    ok(m is not None and float(m.group(1)) >= 2 and m.group(2) == '#1a56db', sel + ' outline: %r' % o)
    ok(css.get(sel, 'outline-offset') == '2px', sel + ' offset')
ok(css.get('.btn:focus:not(:focus-visible)', 'outline') in ('none', '0'), 'mouse focus ring removed only for :not(:focus-visible)')
bad = [r for r in css.rules for s in r.sels if r.decls.get('outline') in ('none', '0', '0px') and ':focus-visible' not in s and ':not(:focus-visible)' not in s]
ok(not bad, 'no unconditional outline removal')
ok(css.get('.btn', 'background') == '#1a56db' and css.get('.btn', 'color') == '#fff' and css.get('.btn', 'padding') == '8px 16px' and css.get('.btn', 'border') in ('0', '0px', 'none') and css.get('.btn', 'border-radius') == '4px', '.btn base')
""")

py("ui-css-reduced-motion", "css", "css", "medium", "a11y",
   "style.css has a spinner and a hover transition. Add a `prefers-reduced-motion` section: inside `@media (prefers-reduced-motion: reduce)` disable the spinner animation (`.spinner { animation: none }`), and for every element (`*`, `*::before`, `*::after`) shorten transitions and animations to effectively none (`transition-duration: 0.01ms !important` and `animation-duration: 0.01ms !important`, `animation-iteration-count: 1 !important`, `scroll-behavior: auto !important`). Keep the existing rules untouched.", 
   {"style.css": "@keyframes spin {\n  to { transform: rotate(360deg); }\n}\n.spinner {\n  width: 24px;\n  height: 24px;\n  border: 3px solid #ccc;\n  border-top-color: #333;\n  border-radius: 50%;\n  animation: spin 1s linear infinite;\n}\n.card { transition: transform 0.3s ease; }\n.card:hover { transform: translateY(-4px); }\nhtml { scroll-behavior: smooth; }\n"},
   {"style.css": "@keyframes spin {\n  to { transform: rotate(360deg); }\n}\n.spinner {\n  width: 24px;\n  height: 24px;\n  border: 3px solid #ccc;\n  border-top-color: #333;\n  border-radius: 50%;\n  animation: spin 1s linear infinite;\n}\n.card { transition: transform 0.3s ease; }\n.card:hover { transform: translateY(-4px); }\nhtml { scroll-behavior: smooth; }\n@media (prefers-reduced-motion: reduce) {\n  .spinner { animation: none; }\n  *, *::before, *::after {\n    animation-duration: 0.01ms !important;\n    animation-iteration-count: 1 !important;\n    transition-duration: 0.01ms !important;\n    scroll-behavior: auto !important;\n  }\n}\n"},
   LOAD + """
m = '(prefers-reduced-motion:reduce)'
ok(m in [c.replace('@media ', '') for c in css.medias()], 'reduced-motion media query present')
ok(css.get('.spinner', 'animation', m) == 'none' or css.get('.spinner', 'animation-name', m) == 'none', 'spinner animation disabled')
for sel in ('*', '*::before', '*::after'):
    ok(css.get(sel, 'transition-duration', m) in ('0.01ms !important', '0s !important', '0.001ms !important', '1ms !important'), sel + ' transition-duration')
    ok(css.get(sel, 'animation-duration', m) in ('0.01ms !important', '0s !important', '0.001ms !important', '1ms !important'), sel + ' animation-duration')
ok(css.get('*', 'animation-iteration-count', m) == '1 !important', 'iteration count 1')
ok(css.get('*', 'scroll-behavior', m) == 'auto !important', 'scroll-behavior auto')
ok(css.get('.spinner', 'animation') == 'spin 1s linear infinite', 'base spinner untouched')
ok(css.get('.card', 'transition') == 'transform 0.3s ease' and css.get('.card:hover', 'transform') == 'translatey(-4px)', 'card rules untouched')
ok(css.get('html', 'scroll-behavior') == 'smooth', 'html scroll-behavior untouched')
ok(css.has_atrule('@keyframes spin'), 'keyframes kept')
""")

py("ui-css-center-flex", "css", "css", "easy", "layout",
   "Write style.css that centres a `.hero` both horizontally and vertically in the viewport using flexbox: `display: flex`, `align-items: center`, `justify-content: center`, at least full viewport height (`min-height: 100vh`, or `100dvh`/`100svh`), `text-align: center`, `padding: 24px`. Its child `.hero__title` has `max-width: 20ch` and `margin: 0`." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".hero {\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  min-height: 100vh;\n  text-align: center;\n  padding: 24px;\n}\n.hero__title {\n  max-width: 20ch;\n  margin: 0;\n}\n"},
   LOAD + """
g = lambda p: css.get('.hero', p)
ok(g('display') == 'flex' and g('align-items') == 'center' and g('justify-content') == 'center', 'flex centring')
ok(g('min-height') in ('100vh', '100dvh', '100svh') and g('height') not in ('100vh',), 'min-height full viewport (not fixed height)')
ok(g('text-align') == 'center' and g('padding') == '24px', 'text-align, padding')
ok(css.get('.hero__title', 'max-width') == '20ch' and css.get('.hero__title', 'margin') in ('0', '0px'), 'title')
""")

py("ui-css-sticky-header", "css", "css", "easy", "layout",
   "Write style.css for a sticky site header: `.site-header` is `position: sticky`, `top: 0`, `z-index: 100`, has an opaque `background: #fff` and `border-bottom: 1px solid #e5e7eb`. The in-page anchors must not hide under it: `html` has `scroll-padding-top: 72px`, and `.site-header` is `height: 64px` with `display: flex; align-items: center; padding: 0 16px`. The `main` element has `min-height: calc(100vh - 64px)`." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".site-header {\n  position: sticky;\n  top: 0;\n  z-index: 100;\n  background: #fff;\n  border-bottom: 1px solid #e5e7eb;\n  height: 64px;\n  display: flex;\n  align-items: center;\n  padding: 0 16px;\n}\nhtml { scroll-padding-top: 72px; }\nmain { min-height: calc(100vh - 64px); }\n"},
   LOAD + """
g = lambda p: css.get('.site-header', p)
ok(g('position') == 'sticky' and g('top') in ('0', '0px'), 'sticky top 0')
ok(g('z-index') == '100', 'z-index')
ok(g('background') == '#fff' or g('background-color') == '#fff', 'opaque background')
ok(g('border-bottom') == '1px solid #e5e7eb', 'border-bottom')
ok(g('height') == '64px' and g('display') == 'flex' and g('align-items') == 'center' and g('padding') in ('0 16px',), 'layout')
ok(css.get('html', 'scroll-padding-top') == '72px', 'scroll-padding-top')
ok(css.get('main', 'min-height') == 'calc(100vh - 64px)', 'main min-height')
""")

py("ui-css-theme-variables", "css", "css", "medium", "theming",
   "Write a themeable style.css with custom properties. On `:root` define `--color-bg: #ffffff`, `--color-text: #111827`, `--color-primary: #2563eb`, `--space-1: 4px`, `--space-2: 8px`, `--space-3: 16px`. `body` uses them: `background: var(--color-bg)`, `color: var(--color-text)`; `.btn` uses `background: var(--color-primary)` and `padding: var(--space-2) var(--space-3)`. Add dark mode inside `@media (prefers-color-scheme: dark)`: redefine on `:root` `--color-bg: #0b1220`, `--color-text: #e5e7eb`, `--color-primary: #60a5fa`. Add `color-scheme: light dark` on `:root`. No hard-coded colours outside `:root` blocks." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ":root {\n  color-scheme: light dark;\n  --color-bg: #ffffff;\n  --color-text: #111827;\n  --color-primary: #2563eb;\n  --space-1: 4px;\n  --space-2: 8px;\n  --space-3: 16px;\n}\nbody {\n  background: var(--color-bg);\n  color: var(--color-text);\n}\n.btn {\n  background: var(--color-primary);\n  padding: var(--space-2) var(--space-3);\n}\n@media (prefers-color-scheme: dark) {\n  :root {\n    --color-bg: #0b1220;\n    --color-text: #e5e7eb;\n    --color-primary: #60a5fa;\n  }\n}\n"},
   LOAD + """
v = lambda p, m=None: css.get(':root', p, m)
for k, val in (('--color-bg', '#ffffff'), ('--color-text', '#111827'), ('--color-primary', '#2563eb'), ('--space-1', '4px'), ('--space-2', '8px'), ('--space-3', '16px')):
    ok(v(k) == val, 'root ' + k)
ok(v('color-scheme') == 'light dark', 'color-scheme')
ok(css.get('body', 'background') == 'var(--color-bg)' and css.get('body', 'color') == 'var(--color-text)', 'body uses vars')
ok(css.get('.btn', 'background') == 'var(--color-primary)' and css.get('.btn', 'padding') == 'var(--space-2) var(--space-3)', 'btn uses vars')
d = '(prefers-color-scheme:dark)'
ok(v('--color-bg', d) == '#0b1220' and v('--color-text', d) == '#e5e7eb' and v('--color-primary', d) == '#60a5fa', 'dark overrides')
hard = [(r.sels, p) for r in css.rules if r.sels != [':root'] for p, val in r.decls.items() if re.search(r'#[0-9a-f]{3,6}\\b|rgba?\\(', val)]
ok(not hard, 'no hard-coded colours outside :root: %r' % hard)
""")

py("ui-css-truncate", "css", "css", "medium", "text",
   "Write style.css text-truncation utilities. `.truncate`: single-line ellipsis (`overflow: hidden`, `text-overflow: ellipsis`, `white-space: nowrap`). `.clamp-3`: multi-line clamp to 3 lines using the line-clamp technique (`display: -webkit-box`, `-webkit-line-clamp: 3`, `-webkit-box-orient: vertical`, `overflow: hidden`) plus the standard `line-clamp: 3`. `.break-words`: `overflow-wrap: anywhere`. In a flex row `.row` with children `.row__text`, text must be allowed to shrink: `.row__text { min-width: 0; flex: 1 }`." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".truncate {\n  overflow: hidden;\n  text-overflow: ellipsis;\n  white-space: nowrap;\n}\n.clamp-3 {\n  display: -webkit-box;\n  -webkit-line-clamp: 3;\n  -webkit-box-orient: vertical;\n  line-clamp: 3;\n  overflow: hidden;\n}\n.break-words { overflow-wrap: anywhere; }\n.row__text {\n  min-width: 0;\n  flex: 1;\n}\n"},
   LOAD + """
t = lambda p: css.get('.truncate', p)
ok(t('overflow') == 'hidden' and t('text-overflow') == 'ellipsis' and t('white-space') == 'nowrap', '.truncate')
c = lambda p: css.get('.clamp-3', p)
ok(c('display') == '-webkit-box' and c('-webkit-line-clamp') == '3' and c('-webkit-box-orient') == 'vertical' and c('overflow') == 'hidden', '.clamp-3 webkit technique')
ok(c('line-clamp') == '3', 'standard line-clamp')
ok(css.get('.break-words', 'overflow-wrap') == 'anywhere', '.break-words')
ok(css.get('.row__text', 'min-width') in ('0', '0px') and css.get('.row__text', 'flex') in ('1', '1 1 0%', '1 1 0'), 'flex child can shrink')
""")

py("ui-css-container-layout", "css", "css", "easy", "layout",
   "Write style.css for a centred page container: `.container` has `width: 100%`, `max-width: 1200px`, `margin-inline: auto` (or `margin: 0 auto`) and horizontal padding of `16px` (`padding-inline: 16px` or `padding: 0 16px`), `box-sizing: border-box`. From 1024px up (`min-width: 1024px`) the padding becomes `32px`. Add a global border-box reset: `*, *::before, *::after { box-sizing: border-box }` and `img { max-width: 100%; height: auto; display: block }`." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": "*, *::before, *::after { box-sizing: border-box; }\nimg { max-width: 100%; height: auto; display: block; }\n.container {\n  width: 100%;\n  max-width: 1200px;\n  margin-inline: auto;\n  padding-inline: 16px;\n  box-sizing: border-box;\n}\n@media (min-width: 1024px) {\n  .container { padding-inline: 32px; }\n}\n"},
   LOAD + """
g = lambda p, m=None: css.get('.container', p, m)
ok(g('width') == '100%' and g('max-width') == '1200px' and g('box-sizing') == 'border-box', 'width, max-width, box-sizing')
ok(g('margin-inline') == 'auto' or g('margin') in ('0 auto', 'auto'), 'centred')
ok(g('padding-inline') == '16px' or g('padding') == '0 16px', 'padding 16')
m = '(min-width:1024px)'
ok(g('padding-inline', m) == '32px' or g('padding', m) == '0 32px', 'padding 32 on desktop')
ok(css.get('*', 'box-sizing') == 'border-box' and css.get('*::before', 'box-sizing') == 'border-box' and css.get('*::after', 'box-sizing') == 'border-box', 'global border-box')
ok(css.get('img', 'max-width') == '100%' and css.get('img', 'height') == 'auto' and css.get('img', 'display') == 'block', 'responsive img')
""")

py("ui-css-print", "css", "css", "medium", "responsive",
   "Write the print stylesheet part of style.css: inside `@media print` hide navigation and chrome (`nav, .no-print, .site-footer { display: none !important }`), force readable colours (`body { color: #000; background: #fff }`), expand link targets (`a[href]::after { content: \" (\" attr(href) \")\" }` but not for in-page links: `a[href^=\"#\"]::after { content: \"\" }`), avoid breaking blocks (`h2, h3 { break-after: avoid }` and `figure, table, pre { break-inside: avoid }`), and `main { width: auto; margin: 0 }`. Outside the print query, only a screen rule is required: `body { font-family: system-ui, sans-serif }`." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": "body { font-family: system-ui, sans-serif; }\n@media print {\n  nav, .no-print, .site-footer { display: none !important; }\n  body { color: #000; background: #fff; }\n  a[href]::after { content: \" (\" attr(href) \")\"; }\n  a[href^=\"#\"]::after { content: \"\"; }\n  h2, h3 { break-after: avoid; }\n  figure, table, pre { break-inside: avoid; }\n  main { width: auto; margin: 0; }\n}\n"},
   LOAD + """
p = 'print'
ok(css.get('body', 'font-family') == 'system-ui,sans-serif', 'screen body font')
ok(css.get('nav,.no-print,.site-footer'.split(',')[0], 'display', p) == 'none !important', 'nav hidden in print')
ok(css.get('.no-print', 'display', p) == 'none !important' and css.get('.site-footer', 'display', p) == 'none !important', '.no-print and footer hidden')
ok(css.get('body', 'color', p) == '#000' and css.get('body', 'background', p) in ('#fff', None) or css.get('body', 'background-color', p) == '#fff', 'readable colours')
ok(css.get('a[href]::after', 'content', p) == '" ("attr(href)")"' or css.get('a[href]::after', 'content', p) == '" (" attr(href) ")"', 'link targets: %r' % css.get('a[href]::after', 'content', p))
ok(css.get('a[href^="#"]::after', 'content', p) in ('""', "''"), 'internal links not expanded')
ok(css.get('h2', 'break-after', p) == 'avoid' and css.get('h3', 'break-after', p) == 'avoid', 'headings keep with next')
ok(all(css.get(s, 'break-inside', p) == 'avoid' for s in ('figure', 'table', 'pre')), 'blocks not split')
ok(css.get('main', 'width', p) == 'auto' and css.get('main', 'margin', p) in ('0', '0px'), 'main full width')
""")

py("ui-css-touch-targets", "css", "css", "easy", "a11y",
   "Write style.css that makes controls comfortably tappable: `.btn`, `.icon-btn` and `.nav a` have `min-height: 44px` and `min-width: 44px`; `.icon-btn` is `display: inline-flex; align-items: center; justify-content: center`; form fields `input, select, textarea` have `min-height: 44px`, `font-size: 16px` (prevents iOS zoom on focus) and `padding: 8px 12px`; spacing between adjacent buttons: `.btn + .btn { margin-left: 8px }`. For coarse pointers (`@media (pointer: coarse)`) `.nav a` gets `padding: 12px 16px`." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".btn, .icon-btn, .nav a {\n  min-height: 44px;\n  min-width: 44px;\n}\n.icon-btn {\n  display: inline-flex;\n  align-items: center;\n  justify-content: center;\n}\ninput, select, textarea {\n  min-height: 44px;\n  font-size: 16px;\n  padding: 8px 12px;\n}\n.btn + .btn { margin-left: 8px; }\n@media (pointer: coarse) {\n  .nav a { padding: 12px 16px; }\n}\n"},
   LOAD + """
for s in ('.btn', '.icon-btn', '.nav a'):
    ok(css.get(s, 'min-height') == '44px' and css.get(s, 'min-width') == '44px', s + ' 44px target')
ok(css.get('.icon-btn', 'display') == 'inline-flex' and css.get('.icon-btn', 'align-items') == 'center' and css.get('.icon-btn', 'justify-content') == 'center', 'icon-btn centred')
for s in ('input', 'select', 'textarea'):
    ok(css.get(s, 'min-height') == '44px' and css.get(s, 'font-size') == '16px' and css.get(s, 'padding') == '8px 12px', s + ' field')
ok(css.get('.btn+.btn', 'margin-left') == '8px', 'button spacing')
ok(css.get('.nav a', 'padding', '(pointer:coarse)') == '12px 16px', 'coarse pointer padding')
""")

py("ui-css-fluid-type", "css", "css", "medium", "responsive",
   "Write fluid typography in style.css. `html { font-size: 100% }` (respect the user's browser setting; no px). `body { font-size: 1rem; line-height: 1.6 }`. `h1 { font-size: clamp(1.75rem, 1.2rem + 2.5vw, 3rem); line-height: 1.15 }`, `h2 { font-size: clamp(1.4rem, 1rem + 1.5vw, 2rem); line-height: 1.25 }`. `p, li { max-width: 65ch }`. Spacing in `rem`: `section { padding-block: clamp(2rem, 5vw, 4rem) }`. No `px` font sizes anywhere." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": "html { font-size: 100%; }\nbody {\n  font-size: 1rem;\n  line-height: 1.6;\n}\nh1 {\n  font-size: clamp(1.75rem, 1.2rem + 2.5vw, 3rem);\n  line-height: 1.15;\n}\nh2 {\n  font-size: clamp(1.4rem, 1rem + 1.5vw, 2rem);\n  line-height: 1.25;\n}\np, li { max-width: 65ch; }\nsection { padding-block: clamp(2rem, 5vw, 4rem); }\n"},
   LOAD + """
ok(css.get('html', 'font-size') == '100%', 'html 100%')
ok(css.get('body', 'font-size') == '1rem' and css.get('body', 'line-height') == '1.6', 'body')
ok(css.get('h1', 'font-size') == 'clamp(1.75rem,1.2rem + 2.5vw,3rem)' or css.get('h1', 'font-size') == 'clamp(1.75rem,1.2rem+2.5vw,3rem)', 'h1 clamp: %r' % css.get('h1', 'font-size'))
ok(css.get('h1', 'line-height') == '1.15', 'h1 line-height')
ok((css.get('h2', 'font-size') or '').replace(' ', '') == 'clamp(1.4rem,1rem+1.5vw,2rem)' and css.get('h2', 'line-height') == '1.25', 'h2')
ok(css.get('p,li'.split(',')[0], 'max-width') == '65ch' and css.get('li', 'max-width') == '65ch', 'measure')
ok((css.get('section', 'padding-block') or '').replace(' ', '') == 'clamp(2rem,5vw,4rem)', 'section padding')
ok(not [1 for r in css.rules for p, v in r.decls.items() if p == 'font-size' and v.endswith('px')], 'no px font sizes')
""")

py("ui-css-modal-overlay", "css", "css", "medium", "layout",
   "Write style.css for a modal: `.overlay` covers the viewport (`position: fixed`; `inset: 0` or top/right/bottom/left all 0), is a flex container centring its content, has a translucent dark backdrop `background: rgba(0, 0, 0, 0.6)` and `z-index: 1000`. `.modal` has `background: #fff`, `border-radius: 8px`, `padding: 24px`, `width: min(90vw, 480px)`, `max-height: 90vh` and `overflow: auto`, plus `overscroll-behavior: contain`. `body.modal-open { overflow: hidden }` locks page scroll." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".overlay {\n  position: fixed;\n  inset: 0;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  background: rgba(0, 0, 0, 0.6);\n  z-index: 1000;\n}\n.modal {\n  background: #fff;\n  border-radius: 8px;\n  padding: 24px;\n  width: min(90vw, 480px);\n  max-height: 90vh;\n  overflow: auto;\n  overscroll-behavior: contain;\n}\nbody.modal-open { overflow: hidden; }\n"},
   LOAD + """
g = lambda p: css.get('.overlay', p)
ok(g('position') == 'fixed', 'fixed')
ok(g('inset') in ('0', '0px') or all(g(s) in ('0', '0px') for s in ('top', 'right', 'bottom', 'left')), 'covers viewport')
ok(g('display') == 'flex' and g('align-items') == 'center' and g('justify-content') == 'center', 'centred')
ok((g('background') or g('background-color')) == 'rgba(0,0,0,0.6)', 'backdrop %r' % g('background'))
ok(g('z-index') == '1000', 'z-index')
m = lambda p: css.get('.modal', p)
ok(m('background') == '#fff' and m('border-radius') == '8px' and m('padding') == '24px', 'modal box')
ok(m('width') == 'min(90vw,480px)' and m('max-height') == '90vh' and m('overflow') == 'auto' and m('overscroll-behavior') == 'contain', 'modal sizing and scroll')
ok(css.get('body.modal-open', 'overflow') == 'hidden', 'scroll lock')
""")

py("ui-css-aspect-media", "css", "css", "easy", "layout",
   "Write style.css for responsive media boxes: `.video` has `width: 100%` and `aspect-ratio: 16 / 9` and `background: #000`; `.video > iframe` fills it (`width: 100%; height: 100%; border: 0`); `.thumb` has `aspect-ratio: 1 / 1; overflow: hidden; border-radius: 8px`, and `.thumb img` is `width: 100%; height: 100%; object-fit: cover`." + FMT,
   {"style.css": EMPTYCSS},
   {"style.css": ".video {\n  width: 100%;\n  aspect-ratio: 16 / 9;\n  background: #000;\n}\n.video > iframe {\n  width: 100%;\n  height: 100%;\n  border: 0;\n}\n.thumb {\n  aspect-ratio: 1 / 1;\n  overflow: hidden;\n  border-radius: 8px;\n}\n.thumb img {\n  width: 100%;\n  height: 100%;\n  object-fit: cover;\n}\n"},
   LOAD + """
ok(css.get('.video', 'width') == '100%' and css.get('.video', 'aspect-ratio') in ('16 / 9', '16/9') and css.get('.video', 'background') == '#000', '.video')
i = '.video>iframe'
ok(css.get(i, 'width') == '100%' and css.get(i, 'height') == '100%' and css.get(i, 'border') in ('0', '0px', 'none'), 'iframe fills')
ok(css.get('.thumb', 'aspect-ratio') in ('1 / 1', '1/1', '1') and css.get('.thumb', 'overflow') == 'hidden' and css.get('.thumb', 'border-radius') == '8px', '.thumb')
ok(css.get('.thumb img', 'width') == '100%' and css.get('.thumb img', 'height') == '100%' and css.get('.thumb img', 'object-fit') == 'cover', '.thumb img')
""")
