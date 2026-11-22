from tb import py

def PAGE(body, title="Demo", head="", lang="en"):
    return (f'<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{title}</title>\n{head}</head>\n<body>\n{body}\n</body>\n</html>\n')

def RAW(body, title="Demo", head=""):
    return f'<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>{title}</title>\n{head}</head>\n<body>\n{body}\n</body>\n</html>\n'

SKEL = '<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<title></title>\n</head>\n<body>\n</body>\n</html>\n'
LOAD = "doc = Doc(open('index.html').read())\n"
FMT = " Return the complete index.html."

# ------------------------------------------------------------- fix existing markup
py("ui-html-fix-alt", "a11y", "html", "easy", "a11y",
   "Fix the image accessibility problems in index.html. The logo and the chart are informative images (give them a meaningful alt that describes them; do not start with 'image of'/'picture of' and do not use the file name). The spacer is purely decorative (empty alt)." + FMT,
   {"index.html": RAW('<header><img class="logo" src="logo.svg"><h1>Acme Reports</h1></header>\n<main>\n<img class="chart" src="q3-revenue.png">\n<p>Revenue grew in Q3.</p>\n<img class="decor" src="spacer.gif">\n</main>')},
   {"index.html": RAW('<header><img class="logo" src="logo.svg" alt="Acme Corp logo"><h1>Acme Reports</h1></header>\n<main>\n<img class="chart" src="q3-revenue.png" alt="Bar chart of quarterly revenue showing growth in Q3">\n<p>Revenue grew in Q3.</p>\n<img class="decor" src="spacer.gif" alt="">\n</main>')},
   LOAD + """
imgs = doc.all('img')
ok(len(imgs) == 3, 'keeps 3 images')
ok(all(i.has('alt') for i in imgs), 'every img has an alt attribute')
by = {c: doc.first('img', **{'class': c}) for c in ('logo', 'chart', 'decor')}
ok(all(by.values()), 'images keep their classes')
ok(by['logo'] and len(by['logo'].get('alt', '').strip()) >= 4, 'logo has meaningful alt')
ok(by['chart'] and len(by['chart'].get('alt', '').strip()) >= 12, 'chart alt describes it')
ok(by['decor'] and by['decor'].get('alt') == '', 'decorative image has empty alt')
for i in imgs:
    a = i.get('alt', '').lower()
    ok(not a.startswith(('image of', 'picture of', 'photo of', 'graphic of')) and not a.endswith(('.png', '.svg', '.gif')), 'alt is not redundant/filename: ' + a)
ok(doc.first('img', src='q3-revenue.png') is not None, 'src unchanged')
""")

py("ui-html-fix-heading-order", "a11y", "html", "easy", "a11y",
   "The heading levels in index.html skip levels and there are two h1 elements. Fix the heading structure: exactly one h1 (the page title 'Garden Guide'), levels never jump down by more than one, and the headings keep their text and order. Do not turn headings into non-headings." + FMT,
   {"index.html": RAW('<h1>Garden Guide</h1>\n<h1>Spring</h1>\n<h4>Planting</h4>\n<p>Sow early.</p>\n<h4>Watering</h4>\n<h2>Summer</h2>\n<h5>Shade</h5>\n<h2>Autumn</h2>')},
   {"index.html": RAW('<h1>Garden Guide</h1>\n<h2>Spring</h2>\n<h3>Planting</h3>\n<p>Sow early.</p>\n<h3>Watering</h3>\n<h2>Summer</h2>\n<h3>Shade</h3>\n<h2>Autumn</h2>')},
   LOAD + """
h = doc.headings()
ok([t for _, t in h] == ['Garden Guide', 'Spring', 'Planting', 'Watering', 'Summer', 'Shade', 'Autumn'], 'headings keep text and order: %r' % [t for _, t in h])
ok(sum(1 for l, _ in h if l == 1) == 1, 'exactly one h1')
ok(h and h[0][0] == 1, 'starts with h1')
ok(all(h[i + 1][0] - h[i][0] <= 1 for i in range(len(h) - 1)), 'no skipped levels: %r' % [l for l, _ in h])
ok(h[1][0] == 2 and h[2][0] >= 3, 'Spring is a section under the title, Planting under Spring')
""")

py("ui-html-fix-form-labels", "a11y", "html", "medium", "a11y",
   "Every form control in index.html lacks an accessible label (only placeholders). Add a visible `<label>` for each control, correctly associated (use `for`/`id`, make ids unique), keep the placeholders, names and types, and keep the submit button as it is." + FMT,
   {"index.html": PAGE('<form action="/join" method="post">\n<input type="text" name="first" placeholder="First name">\n<input type="text" name="last" placeholder="Last name">\n<input type="email" name="email" placeholder="Email">\n<select name="plan"><option>Free</option><option>Pro</option></select>\n<textarea name="bio" placeholder="About you"></textarea>\n<button type="submit">Join</button>\n</form>')},
   {"index.html": PAGE('<form action="/join" method="post">\n<label for="first">First name</label> <input type="text" id="first" name="first" placeholder="First name">\n<label for="last">Last name</label> <input type="text" id="last" name="last" placeholder="Last name">\n<label for="email">Email</label> <input type="email" id="email" name="email" placeholder="Email">\n<label for="plan">Plan</label> <select id="plan" name="plan"><option>Free</option><option>Pro</option></select>\n<label for="bio">About you</label> <textarea id="bio" name="bio" placeholder="About you"></textarea>\n<button type="submit">Join</button>\n</form>')},
   LOAD + """
controls = doc.all('input') + doc.all('select') + doc.all('textarea')
ok(len(controls) == 5, 'five controls kept')
ids = doc.ids()
ok(len(ids) == len(set(ids)), 'ids are unique')
for c in controls:
    ok(doc.label_text(c).strip() != '', 'control %s has label text' % c.get('name'))
    ok(c.get('name') in ('first', 'last', 'email', 'plan', 'bio'), 'name kept')
for l in doc.all('label'):
    if l.get('for'):
        t = doc.by_id(l.get('for'))
        ok(t is not None and t.tag in ('input', 'select', 'textarea'), 'label for -> existing control')
ok(doc.first('input', type='email') is not None, 'email type kept')
ok(all(i.has('placeholder') for i in doc.all('input', type='text')), 'placeholders kept')
ok(doc.first('button', type='submit') is not None, 'submit kept')
""")

py("ui-html-fix-button-div", "a11y", "html", "medium", "a11y",
   "The 'buttons' in index.html are clickable `div`/`span` elements with onclick handlers: not focusable and not announced as buttons. Replace them with real `<button type=\"button\">` elements (keep the text, the classes and the onclick attributes). Links that navigate must stay `<a href>`." + FMT,
   {"index.html": PAGE('<div class="toolbar">\n<div class="btn" onclick="save()">Save</div>\n<div class="btn" onclick="undo()">Undo</div>\n<span class="btn danger" onclick="del()">Delete</span>\n</div>\n<a href="/help">Help</a>')},
   {"index.html": PAGE('<div class="toolbar">\n<button type="button" class="btn" onclick="save()">Save</button>\n<button type="button" class="btn" onclick="undo()">Undo</button>\n<button type="button" class="btn danger" onclick="del()">Delete</button>\n</div>\n<a href="/help">Help</a>')},
   LOAD + """
ok(not [e for e in doc.all() if e.tag in ('div', 'span') and e.has('onclick')], 'no div/span with onclick')
b = doc.all('button')
ok(len(b) == 3, 'three buttons')
ok([x.text() for x in b] == ['Save', 'Undo', 'Delete'], 'button texts in order')
ok(all(x.get('type') == 'button' for x in b), 'type=button')
ok(all(x.get('onclick') for x in b), 'onclick kept')
ok(all('btn' in x.classes() for x in b), 'class btn kept')
ok(doc.first('button', onclick='del()') is not None and 'danger' in doc.first('button', onclick='del()').classes(), 'danger class kept')
ok(doc.first('a', href='/help') is not None, 'link stays a link')
""")

py("ui-html-fix-landmarks", "a11y", "html", "medium", "a11y",
   "index.html is all `div`s. Give it semantic landmarks: a single `header` (containing the h1), a `nav` (with an accessible name via aria-label) holding the links, one `main` with id `main` holding the content, and a `footer`. Add a skip link `<a href=\"#main\">Skip to content</a>` as the FIRST focusable element in the body. Keep all text." + FMT,
   {"index.html": PAGE('<div class="top"><h1>Bakery</h1></div>\n<div class="menu"><a href="/">Home</a> <a href="/bread">Bread</a> <a href="/contact">Contact</a></div>\n<div class="content"><h2>Fresh daily</h2><p>Sourdough and rye.</p></div>\n<div class="bottom">(c) 2026 Bakery</div>')},
   {"index.html": PAGE('<a class="skip" href="#main">Skip to content</a>\n<header class="top"><h1>Bakery</h1></header>\n<nav class="menu" aria-label="Main"><a href="/">Home</a> <a href="/bread">Bread</a> <a href="/contact">Contact</a></nav>\n<main id="main" class="content"><h2>Fresh daily</h2><p>Sourdough and rye.</p></main>\n<footer class="bottom">(c) 2026 Bakery</footer>')},
   LOAD + """
for t in ('header', 'nav', 'main', 'footer'):
    ok(len(doc.all(t)) == 1, 'exactly one <%s>' % t)
main = doc.first('main')
ok(main is not None and main.get('id') == 'main', 'main has id=main')
h1 = doc.first('h1')
ok(h1 is not None and any(a.tag == 'header' for a in h1.ancestors()), 'h1 inside header')
nav = doc.first('nav')
ok(nav is not None and nav.get('aria-label', '').strip() != '', 'nav has aria-label')
ok(nav is not None and len(nav.find_all('a')) == 3, 'three links inside nav')
ok(main is not None and 'Fresh daily' in main.text() and 'Sourdough' in main.text(), 'content inside main')
body = doc.first('body')
focusables = [e for e in body.walk() if e.tag in ('a', 'button', 'input') ]
ok(focusables and focusables[0].tag == 'a' and focusables[0].get('href') == '#main', 'skip link is first focusable')
ok(focusables and 'skip' in focusables[0].text().lower(), 'skip link text')
ok('2026 Bakery' in doc.first('footer').text(), 'footer text kept')
""")

py("ui-html-fix-lang-viewport", "a11y", "html", "easy", "a11y",
   "Fix the document-level accessibility/responsiveness problems in index.html: declare the language (`lang=\"en\"` on html), give the page a real, non-empty `<title>` (use 'Pricing - Acme'), and fix the viewport meta so it is `width=device-width, initial-scale=1` WITHOUT disabling zoom (no user-scalable=no, no maximum-scale below 5). Keep the existing h1 and charset." + FMT,
   {"index.html": '<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=1024, user-scalable=no, maximum-scale=1">\n<title></title>\n</head>\n<body>\n<h1>Pricing</h1>\n</body>\n</html>\n'},
   {"index.html": '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Pricing - Acme</title>\n</head>\n<body>\n<h1>Pricing</h1>\n</body>\n</html>\n'},
   LOAD + """
import re
html = doc.first('html')
ok(html.get('lang', '').strip().lower().startswith('en'), 'html lang=en')
t = doc.first('title')
ok(t is not None and t.text() == 'Pricing - Acme', 'title text')
vp = doc.first('meta', name='viewport')
c = (vp.get('content') if vp else '').replace(' ', '').lower()
ok('width=device-width' in c, 'width=device-width')
ok('initial-scale=1' in c, 'initial-scale=1')
ok('user-scalable=no' not in c and 'user-scalable=0' not in c, 'zoom not disabled')
m = re.search(r'maximum-scale=([0-9.]+)', c)
ok(m is None or float(m.group(1)) >= 5, 'no restrictive maximum-scale')
ok(doc.first('meta', charset='utf-8') is not None, 'charset kept')
ok(doc.first('h1') is not None and doc.first('h1').text() == 'Pricing', 'h1 kept')
""")

py("ui-html-fix-link-text", "a11y", "html", "easy", "a11y",
   "The links in index.html all say 'click here' or 'read more', which is meaningless out of context (e.g. in a screen reader's links list). Rewrite each link so its accessible name is descriptive and the three names are different from each other (visible text is preferred; keep every href and the surrounding article headings)." + FMT,
   {"index.html": PAGE('<article><h2>Solar panel basics</h2><p>How panels turn light into power. <a href="/solar">Read more</a></p></article>\n<article><h2>Heat pump guide</h2><p>Heating without gas. <a href="/heatpump">Read more</a></p></article>\n<p>Questions? <a href="/contact">Click here</a></p>')},
   {"index.html": PAGE('<article><h2>Solar panel basics</h2><p>How panels turn light into power. <a href="/solar">Read more about solar panel basics</a></p></article>\n<article><h2>Heat pump guide</h2><p>Heating without gas. <a href="/heatpump">Read more about the heat pump guide</a></p></article>\n<p>Questions? <a href="/contact">Contact our support team</a></p>')},
   LOAD + """
links = doc.all('a')
ok(len(links) == 3, 'three links')
generic = {'click here', 'read more', 'here', 'more', 'link', 'learn more', 'details'}
names = [doc.name_of(a).strip().lower() for a in links]
ok(all(n not in generic for n in names), 'no generic names: %r' % names)
ok(all(len(n) >= 12 for n in names), 'names are descriptive (12+ chars)')
ok(len(set(names)) == 3, 'names are distinct')
ok(sorted(a.get('href') for a in links) == ['/contact', '/heatpump', '/solar'], 'hrefs kept')
ok(len(doc.all('h2')) == 2, 'headings kept')
""")

py("ui-html-fix-duplicate-ids", "a11y", "html", "medium", "a11y",
   "index.html has duplicate ids and labels whose `for` points at the wrong or a missing id, so clicking a label focuses the wrong field. Make all ids unique and every label point at its own control (keep the two address blocks: shipping and billing, each with Street and City). Keep names and visible label texts." + FMT,
   {"index.html": PAGE('<form>\n<fieldset><legend>Shipping</legend>\n<label for="street">Street</label><input id="street" name="ship_street">\n<label for="town">City</label><input id="city" name="ship_city">\n</fieldset>\n<fieldset><legend>Billing</legend>\n<label for="street">Street</label><input id="street" name="bill_street">\n<label for="city">City</label><input id="city" name="bill_city">\n</fieldset>\n</form>')},
   {"index.html": PAGE('<form>\n<fieldset><legend>Shipping</legend>\n<label for="ship-street">Street</label><input id="ship-street" name="ship_street">\n<label for="ship-city">City</label><input id="ship-city" name="ship_city">\n</fieldset>\n<fieldset><legend>Billing</legend>\n<label for="bill-street">Street</label><input id="bill-street" name="bill_street">\n<label for="bill-city">City</label><input id="bill-city" name="bill_city">\n</fieldset>\n</form>')},
   LOAD + """
ids = doc.ids()
ok(len(ids) == len(set(ids)), 'ids unique: %r' % ids)
inputs = doc.all('input')
ok(len(inputs) == 4, 'four inputs')
ok(all(i.has('id') for i in inputs), 'inputs have ids')
for i in inputs:
    ok(doc.label_text(i) in ('Street', 'City'), 'input %s labelled Street/City' % i.get('name'))
for l in doc.all('label'):
    ok(l.get('for') in ids, 'label for exists: %s' % l.get('for'))
# each label's target is in the same fieldset
for l in doc.all('label'):
    tgt = doc.by_id(l.get('for'))
    lf = [a for a in l.ancestors() if a.tag == 'fieldset']
    tf = [a for a in tgt.ancestors() if a.tag == 'fieldset'] if tgt else []
    ok(lf and tf and lf[0] is tf[0], 'label targets control in its own fieldset')
ok(sorted(i.get('name') for i in inputs) == ['bill_city', 'bill_street', 'ship_city', 'ship_street'], 'names kept')
""")

py("ui-html-fix-data-table", "a11y", "html", "medium", "a11y",
   "index.html shows tabular data with bare `td` cells and no structure. Make it an accessible data table: a `<caption>` ('Team scores'), a `<thead>` whose header cells are `<th scope=\"col\">`, and a `<tbody>` where the first cell of every row is a `<th scope=\"row\">`. Keep all data values." + FMT,
   {"index.html": PAGE('<table>\n<tr><td><b>Team</b></td><td><b>Wins</b></td><td><b>Losses</b></td></tr>\n<tr><td>Owls</td><td>10</td><td>2</td></tr>\n<tr><td>Hawks</td><td>7</td><td>5</td></tr>\n</table>')},
   {"index.html": PAGE('<table>\n<caption>Team scores</caption>\n<thead><tr><th scope="col">Team</th><th scope="col">Wins</th><th scope="col">Losses</th></tr></thead>\n<tbody>\n<tr><th scope="row">Owls</th><td>10</td><td>2</td></tr>\n<tr><th scope="row">Hawks</th><td>7</td><td>5</td></tr>\n</tbody>\n</table>')},
   LOAD + """
t = doc.first('table')
ok(t is not None, 'table kept')
cap = t.first('caption') if t else None
ok(cap is not None and cap.text() == 'Team scores', 'caption')
thead = t.first('thead'); tbody = t.first('tbody')
ok(thead is not None and tbody is not None, 'thead and tbody')
ths = thead.find_all('th') if thead else []
ok([h.text() for h in ths] == ['Team', 'Wins', 'Losses'], 'column headers')
ok(all(h.get('scope') == 'col' for h in ths), 'scope=col')
ok(thead is not None and not thead.find_all('td'), 'no td in thead')
rows = tbody.find_all('tr') if tbody else []
ok(len(rows) == 2, 'two body rows')
for r, (n, w, l) in zip(rows, [('Owls', '10', '2'), ('Hawks', '7', '5')]):
    cells = [c for c in r.children if c.tag in ('th', 'td')]
    ok(len(cells) == 3 and cells[0].tag == 'th' and cells[0].get('scope') == 'row' and cells[0].text() == n, 'row header ' + n)
    ok([c.text() for c in cells[1:]] == [w, l] and all(c.tag == 'td' for c in cells[1:]), 'row data ' + n)
ok(not [b for b in t.find_all('b')], 'no bold hacks inside table')
""")

py("ui-html-fix-icon-buttons", "a11y", "html", "medium", "a11y",
   "The icon-only buttons in index.html have no accessible name. Give each button a distinct accessible name (via `aria-label`: 'Search', 'Settings', 'Close'), mark the decorative inline SVGs `aria-hidden=\"true\"` (and not focusable), and keep the buttons as `<button type=\"button\">` with their classes." + FMT,
   {"index.html": PAGE('<div class="bar">\n<button type="button" class="icon search"><svg viewBox="0 0 16 16"><circle cx="7" cy="7" r="5"/></svg></button>\n<button type="button" class="icon settings"><svg viewBox="0 0 16 16"><rect width="10" height="10"/></svg></button>\n<button type="button" class="icon close"><svg viewBox="0 0 16 16"><path d="M0 0L16 16"/></svg></button>\n</div>')},
   {"index.html": PAGE('<div class="bar">\n<button type="button" class="icon search" aria-label="Search"><svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><circle cx="7" cy="7" r="5"/></svg></button>\n<button type="button" class="icon settings" aria-label="Settings"><svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><rect width="10" height="10"/></svg></button>\n<button type="button" class="icon close" aria-label="Close"><svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M0 0L16 16"/></svg></button>\n</div>')},
   LOAD + """
bs = doc.all('button')
ok(len(bs) == 3, 'three buttons')
names = [doc.name_of(b).strip() for b in bs]
ok(all(names), 'every button has a name: %r' % names)
ok(len(set(n.lower() for n in names)) == 3, 'names are distinct')
want = {'search': 'search', 'settings': 'settings', 'close': 'close'}
for b in bs:
    c = [x for x in b.classes() if x in want][0]
    ok(want[c] in doc.name_of(b).lower(), 'name matches icon: ' + c)
    ok(all(b.get('type') == 'button' for _ in [0]), 'type=button')
svgs = doc.all('svg')
ok(len(svgs) == 3 and all(s.get('aria-hidden') == 'true' for s in svgs), 'svgs aria-hidden=true')
ok(all(s.get('focusable') in (None, 'false') for s in svgs), 'svg not focusable')
""")

py("ui-html-fix-radio-group", "a11y", "html", "medium", "a11y",
   "The radio buttons in index.html are not grouped, so a screen reader cannot tell what question they answer. Wrap them in a `<fieldset>` with a `<legend>` ('Delivery speed'), keep all radios in the same group (same `name`), each with its own associated `<label>`, and make exactly one radio checked by default (the 'Standard' one)." + FMT,
   {"index.html": PAGE('<form>\n<p>Delivery speed</p>\n<input type="radio" name="speed" value="std"> Standard\n<input type="radio" name="speed" value="exp"> Express\n<input type="radio" name="speed" value="ovn"> Overnight\n</form>')},
   {"index.html": PAGE('<form>\n<fieldset>\n<legend>Delivery speed</legend>\n<input type="radio" id="s-std" name="speed" value="std" checked> <label for="s-std">Standard</label>\n<input type="radio" id="s-exp" name="speed" value="exp"> <label for="s-exp">Express</label>\n<input type="radio" id="s-ovn" name="speed" value="ovn"> <label for="s-ovn">Overnight</label>\n</fieldset>\n</form>')},
   LOAD + """
fs = doc.all('fieldset')
ok(len(fs) == 1, 'one fieldset')
lg = fs[0].first('legend') if fs else None
ok(lg is not None and lg.text() == 'Delivery speed', 'legend text')
ok(fs and lg in fs[0].children, 'legend is a direct child of fieldset')
radios = doc.all('input', type='radio')
ok(len(radios) == 3, 'three radios')
ok(fs and all(any(a is fs[0] for a in r.ancestors()) for r in radios), 'radios inside the fieldset')
ok(len({r.get('name') for r in radios}) == 1, 'same name')
ok([doc.label_text(r) for r in radios] == ['Standard', 'Express', 'Overnight'], 'labels: %r' % [doc.label_text(r) for r in radios])
checked = [r for r in radios if r.has('checked')]
ok(len(checked) == 1 and checked[0].get('value') == 'std', 'only Standard checked')
ids = doc.ids(); ok(len(ids) == len(set(ids)), 'unique ids')
ok(sorted(r.get('value') for r in radios) == ['exp', 'ovn', 'std'], 'values kept')
""")

py("ui-html-fix-form-errors", "a11y", "html", "hard", "a11y",
   "index.html shows server-side validation errors as plain red text that is not tied to the fields. Make the errors accessible: the invalid inputs (email and age) get `aria-invalid=\"true\"` and an `aria-describedby` pointing to the id of their error message element; give each error element a unique id and `role=\"alert\"`. The valid input (name) must NOT be marked invalid and must not point to an error. Keep the labels, texts and everything else." + FMT,
   {"index.html": PAGE('<form>\n<div><label for="name">Name</label><input id="name" name="name" value="Ann"></div>\n<div><label for="email">Email</label><input id="email" name="email" value="ann@">\n<span class="error">Enter a valid email address</span></div>\n<div><label for="age">Age</label><input id="age" name="age" value="-3">\n<span class="error">Age must be 0 or more</span></div>\n<button type="submit">Save</button>\n</form>')},
   {"index.html": PAGE('<form>\n<div><label for="name">Name</label><input id="name" name="name" value="Ann"></div>\n<div><label for="email">Email</label><input id="email" name="email" value="ann@" aria-invalid="true" aria-describedby="email-error">\n<span class="error" id="email-error" role="alert">Enter a valid email address</span></div>\n<div><label for="age">Age</label><input id="age" name="age" value="-3" aria-invalid="true" aria-describedby="age-error">\n<span class="error" id="age-error" role="alert">Age must be 0 or more</span></div>\n<button type="submit">Save</button>\n</form>')},
   LOAD + """
def desc(inp):
    return [doc.by_id(x) for x in (inp.get('aria-describedby') or '').split() if doc.by_id(x)]
name, email, age = doc.by_id('name'), doc.by_id('email'), doc.by_id('age')
ok(name and email and age, 'inputs kept')
ok(name.get('aria-invalid') in (None, 'false'), 'name not invalid')
ok(not desc(name), 'name has no error description')
for inp, txt in ((email, 'Enter a valid email address'), (age, 'Age must be 0 or more')):
    ok(inp.get('aria-invalid') == 'true', 'invalid: ' + inp.get('id'))
    d = desc(inp)
    ok(len(d) == 1 and d[0].text() == txt, 'describedby points at the error text for ' + inp.get('id'))
    ok(d and d[0].get('role') == 'alert', 'error has role=alert for ' + inp.get('id'))
errs = doc.all('span', **{'class': 'error'})
ok(len(errs) == 2 and all(e.has('id') for e in errs), 'error ids present')
ids = doc.ids(); ok(len(ids) == len(set(ids)), 'unique ids')
ok(doc.label_text(email) == 'Email' and doc.label_text(age) == 'Age' and doc.label_text(name) == 'Name', 'labels kept')
""")

py("ui-html-fix-nav-current", "a11y", "html", "medium", "a11y",
   "index.html has two `nav` regions with no names, and the current page (Pricing, /pricing) is only styled with a class. Give each nav a distinct `aria-label` ('Main' for the top one, 'Footer' for the bottom one), mark the Pricing link in the main nav with `aria-current=\"page\"` (and no other link), and make the nav lists real lists (`ul`/`li`)." + FMT,
   {"index.html": PAGE('<nav>\n<a href="/">Home</a>\n<a href="/pricing" class="current">Pricing</a>\n<a href="/docs">Docs</a>\n</nav>\n<main><h1>Pricing</h1></main>\n<nav>\n<a href="/privacy">Privacy</a>\n<a href="/terms">Terms</a>\n</nav>')},
   {"index.html": PAGE('<nav aria-label="Main">\n<ul>\n<li><a href="/">Home</a></li>\n<li><a href="/pricing" class="current" aria-current="page">Pricing</a></li>\n<li><a href="/docs">Docs</a></li>\n</ul>\n</nav>\n<main><h1>Pricing</h1></main>\n<nav aria-label="Footer">\n<ul>\n<li><a href="/privacy">Privacy</a></li>\n<li><a href="/terms">Terms</a></li>\n</ul>\n</nav>')},
   LOAD + """
navs = doc.all('nav')
ok(len(navs) == 2, 'two navs')
labels = [n.get('aria-label', '').strip() for n in navs]
ok(all(labels) and len(set(l.lower() for l in labels)) == 2, 'distinct aria-labels: %r' % labels)
ok(labels[0].lower() == 'main' and labels[1].lower() == 'footer', 'Main then Footer')
cur = [a for a in doc.all('a') if a.has('aria-current')]
ok(len(cur) == 1 and cur[0].get('href') == '/pricing' and cur[0].get('aria-current') == 'page', 'only /pricing is aria-current=page')
for n in navs:
    ul = n.first('ul')
    ok(ul is not None, 'nav contains a ul')
    ok(ul is not None and len(ul.find_all('li')) == len(n.find_all('a')), 'one li per link')
ok(len(doc.all('a')) == 5, 'links kept')
""")

py("ui-html-fix-video", "a11y", "html", "medium", "a11y",
   "The video in index.html autoplays with sound, has no controls and no captions. Fix it: remove `autoplay`, add `controls`, add a captions track (`<track kind=\"captions\" src=\"talk.en.vtt\" srclang=\"en\" label=\"English\" default>`), add `preload=\"metadata\"`, and add a text alternative: a `<p>` immediately after the video starting with 'Transcript' that links to `/talk-transcript.html`. Keep the source." + FMT,
   {"index.html": PAGE('<h1>Conference talk</h1>\n<video autoplay width="640" poster="talk.jpg">\n<source src="talk.mp4" type="video/mp4">\n</video>')},
   {"index.html": PAGE('<h1>Conference talk</h1>\n<video controls preload="metadata" width="640" poster="talk.jpg">\n<source src="talk.mp4" type="video/mp4">\n<track kind="captions" src="talk.en.vtt" srclang="en" label="English" default>\n</video>\n<p>Transcript: <a href="/talk-transcript.html">read the full transcript</a></p>')},
   LOAD + """
v = doc.first('video')
ok(v is not None, 'video kept')
ok(v is not None and not v.has('autoplay'), 'no autoplay')
ok(v is not None and v.has('controls'), 'controls')
ok(v is not None and v.get('preload') == 'metadata', 'preload=metadata')
tr = v.first('track') if v else None
ok(tr is not None and tr.get('kind') == 'captions' and tr.get('srclang') == 'en' and tr.get('src') == 'talk.en.vtt', 'captions track')
ok(tr is not None and tr.get('label') and tr.has('default'), 'label and default')
ok(v is not None and v.first('source', src='talk.mp4') is not None, 'source kept')
p = None
if v is not None and v.parent is not None:
    sib = [c for c in v.parent.children]
    i = sib.index(v)
    p = sib[i + 1] if i + 1 < len(sib) else None
ok(p is not None and p.tag == 'p' and p.text().lower().startswith('transcript'), 'transcript paragraph right after video')
ok(p is not None and p.first('a', href='/talk-transcript.html') is not None, 'transcript link')
""")

py("ui-html-fix-new-tab-links", "a11y", "html", "medium", "a11y",
   "External links in index.html open in a new tab silently and without `rel`. For every link with `target=\"_blank\"`: add `rel=\"noopener noreferrer\"` and tell users it opens in a new tab through its accessible name (e.g. visually-hidden text or aria-label containing 'opens in a new tab'). Internal links (without target) must stay unchanged." + FMT,
   {"index.html": PAGE('<ul>\n<li><a href="https://example.org/spec" target="_blank">The spec</a></li>\n<li><a href="https://example.com/tool" target="_blank">Online tool</a></li>\n<li><a href="/about">About us</a></li>\n</ul>')},
   {"index.html": PAGE('<ul>\n<li><a href="https://example.org/spec" target="_blank" rel="noopener noreferrer">The spec <span class="sr-only">(opens in a new tab)</span></a></li>\n<li><a href="https://example.com/tool" target="_blank" rel="noopener noreferrer">Online tool <span class="sr-only">(opens in a new tab)</span></a></li>\n<li><a href="/about">About us</a></li>\n</ul>')},
   LOAD + """
ext = [a for a in doc.all('a') if a.get('target') == '_blank']
ok(len(ext) == 2, 'two external links keep target')
for a in ext:
    rel = (a.get('rel') or '').lower().split()
    ok('noopener' in rel and 'noreferrer' in rel, 'rel for ' + a.get('href'))
    ok('new tab' in doc.name_of(a).lower() or 'new tab' in (a.get('aria-label') or '').lower() or 'new window' in doc.name_of(a).lower(), 'announces new tab for ' + a.get('href'))
    ok(doc.name_of(a).lower().startswith(('the spec', 'online tool')), 'visible name stays first')
about = doc.first('a', href='/about')
ok(about is not None and about.text() == 'About us' and not about.has('target') and not about.has('rel'), 'internal link unchanged')
""")

py("ui-html-fix-tabindex", "a11y", "html", "medium", "a11y",
   "index.html abuses `tabindex`: positive values hijack the tab order and a non-interactive `div` is in the tab order with a click handler. Remove every positive tabindex, make the div with the click handler a real `<button type=\"button\">` (keep its text 'Open menu', class and onclick) with no tabindex, and keep the two inputs and the link in natural order." + FMT,
   {"index.html": PAGE('<div class="trigger" tabindex="3" onclick="openMenu()">Open menu</div>\n<input type="text" name="q" aria-label="Search" tabindex="2">\n<input type="text" name="z" aria-label="Zip" tabindex="1">\n<a href="/help" tabindex="5">Help</a>')},
   {"index.html": PAGE('<button type="button" class="trigger" onclick="openMenu()">Open menu</button>\n<input type="text" name="q" aria-label="Search">\n<input type="text" name="z" aria-label="Zip">\n<a href="/help">Help</a>')},
   LOAD + """
bad = [e for e in doc.all() if e.has('tabindex') and e.get('tabindex').lstrip('-').isdigit() and int(e.get('tabindex')) > 0]
ok(not bad, 'no positive tabindex')
ok(not [e for e in doc.all() if e.tag == 'div' and (e.has('onclick') or e.has('tabindex'))], 'no interactive div')
b = doc.first('button')
ok(b is not None and b.text() == 'Open menu' and b.get('type') == 'button' and 'trigger' in b.classes() and b.get('onclick') == 'openMenu()', 'real button with same text/class/onclick')
ok(b is not None and not b.has('tabindex'), 'button has no tabindex')
order = [e.tag if e.tag != 'input' else 'input:' + e.get('name') for e in doc.root.walk() if e.tag in ('button', 'input', 'a')]
ok(order == ['button', 'input:q', 'input:z', 'a'], 'natural order kept: %r' % order)
""")
