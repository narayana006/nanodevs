from tb import py
from html_a import PAGE, SKEL, LOAD

FMT = " Return the complete index.html."
EMPTY = '<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<title></title>\n</head>\n<body>\n</body>\n</html>\n'
BASE = ' The page must have `lang="en"` on html, a viewport meta (`width=device-width, initial-scale=1`) and a non-empty title.'
BASECHK = """
ok(doc.first('html') is not None and doc.first('html').get('lang', '').startswith('en'), 'html lang')
vp = doc.first('meta', name='viewport')
ok(vp is not None and 'width=device-width' in vp.get('content', ''), 'viewport meta')
ok(doc.first('title') is not None and doc.first('title').text() != '', 'title')
"""

py("ui-html-write-login", "write", "html", "easy", "forms",
   "Write the body of a login page in index.html: an `h1` 'Sign in', then a `form` (method post, action /login) with a labelled email field (`type=\"email\"`, name email, `autocomplete=\"username\"`, required), a labelled password field (`type=\"password\"`, name password, `autocomplete=\"current-password\"`, required), a labelled checkbox 'Remember me' (name remember), and a `<button type=\"submit\">` 'Sign in'. Labels must be associated with `for`/`id`." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<main>\n<h1>Sign in</h1>\n<form method="post" action="/login">\n<p><label for="email">Email</label>\n<input id="email" name="email" type="email" autocomplete="username" required></p>\n<p><label for="password">Password</label>\n<input id="password" name="password" type="password" autocomplete="current-password" required></p>\n<p><input id="remember" name="remember" type="checkbox"> <label for="remember">Remember me</label></p>\n<button type="submit">Sign in</button>\n</form>\n</main>', "Sign in")},
   LOAD + BASECHK + """
h = doc.headings(); ok(h and h[0] == (1, 'Sign in'), 'h1 Sign in')
f = doc.first('form')
ok(f is not None and f.get('method', '').lower() == 'post' and f.get('action') == '/login', 'form method/action')
e = doc.first('input', name='email'); p = doc.first('input', name='password'); r = doc.first('input', name='remember')
ok(e is not None and e.get('type') == 'email' and e.get('autocomplete') == 'username' and e.has('required'), 'email field')
ok(p is not None and p.get('type') == 'password' and p.get('autocomplete') == 'current-password' and p.has('required'), 'password field')
ok(r is not None and r.get('type') == 'checkbox', 'remember checkbox')
for c, t in ((e, 'email'), (p, 'password'), (r, 'remember me')):
    ok(c is not None and t in doc.label_text(c).lower(), 'label for ' + t)
    ok(c is not None and c.has('id') and any(l.get('for') == c.get('id') for l in doc.all('label')), 'explicit for/id for ' + t)
b = doc.all('button')
ok(len(b) == 1 and b[0].get('type') == 'submit' and b[0].text() == 'Sign in', 'submit button')
ids = doc.ids(); ok(len(ids) == len(set(ids)), 'unique ids')
""")

py("ui-html-write-signup", "write", "html", "medium", "forms",
   "Write a sign-up page in index.html with an h1 and a `form` containing: Full name (`autocomplete=\"name\"`), Email (`type=\"email\"`, `autocomplete=\"email\"`), Phone (`type=\"tel\"`, `autocomplete=\"tel\"`, optional), Password (`type=\"password\"`, `minlength=\"8\"`, `autocomplete=\"new-password\"`) with a hint paragraph ('At least 8 characters') linked through `aria-describedby`, and a fieldset with legend 'Notifications' containing two labelled checkboxes ('Product news', 'Security alerts'). All text fields except Phone are `required`. Every control needs an associated label; include a submit button." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<main>\n<h1>Create account</h1>\n<form action="/signup" method="post">\n<p><label for="name">Full name</label> <input id="name" name="name" autocomplete="name" required></p>\n<p><label for="email">Email</label> <input id="email" name="email" type="email" autocomplete="email" required></p>\n<p><label for="phone">Phone</label> <input id="phone" name="phone" type="tel" autocomplete="tel"></p>\n<p><label for="pw">Password</label> <input id="pw" name="password" type="password" minlength="8" autocomplete="new-password" required aria-describedby="pw-hint"></p>\n<p id="pw-hint">At least 8 characters</p>\n<fieldset><legend>Notifications</legend>\n<input type="checkbox" id="n-news" name="news"> <label for="n-news">Product news</label>\n<input type="checkbox" id="n-sec" name="security"> <label for="n-sec">Security alerts</label>\n</fieldset>\n<button type="submit">Sign up</button>\n</form>\n</main>', "Sign up")},
   LOAD + BASECHK + """
ok(len(doc.all('h1')) == 1, 'one h1')
f = doc.first('form'); ok(f is not None, 'form')
def field(**kw):
    return doc.first('input', **kw)
name = [i for i in doc.all('input') if i.get('autocomplete') == 'name']
email = field(type='email'); phone = field(type='tel'); pw = field(type='password')
ok(len(name) == 1 and name[0].has('required'), 'name field required, autocomplete=name')
ok(email is not None and email.get('autocomplete') == 'email' and email.has('required'), 'email')
ok(phone is not None and phone.get('autocomplete') == 'tel' and not phone.has('required'), 'phone optional')
ok(pw is not None and pw.get('minlength') == '8' and pw.get('autocomplete') == 'new-password' and pw.has('required'), 'password')
hint = doc.by_id(pw.get('aria-describedby', '').split()[0]) if pw and pw.get('aria-describedby') else None
ok(hint is not None and hint.text() == 'At least 8 characters', 'password hint linked')
fs = doc.all('fieldset')
ok(len(fs) == 1 and fs[0].first('legend') is not None and fs[0].first('legend').text() == 'Notifications', 'fieldset legend')
cbs = fs[0].find_all('input', type='checkbox') if fs else []
ok(len(cbs) == 2 and sorted(doc.label_text(c) for c in cbs) == ['Product news', 'Security alerts'], 'checkbox labels')
for c in doc.all('input'):
    ok(doc.label_text(c) != '', 'labelled: %s' % (c.get('name') or c.get('type')))
ok(doc.first('button', type='submit') is not None, 'submit')
ids = doc.ids(); ok(len(ids) == len(set(ids)), 'unique ids')
""")

py("ui-html-write-tabs-markup", "write", "html", "hard", "aria",
   "Write the static ARIA markup for a tab interface in index.html (no scripts needed): a `div` with `role=\"tablist\"` and `aria-label=\"Account\"` holding three `<button>` elements with `role=\"tab\"` and ids `tab-profile`, `tab-billing`, `tab-security` (texts Profile, Billing, Security), then three `div` panels with `role=\"tabpanel\"`, ids `panel-profile`, `panel-billing`, `panel-security`. Link them: each tab has `aria-controls` -> its panel, each panel has `aria-labelledby` -> its tab. The Profile tab is selected: `aria-selected=\"true\"` and `tabindex=\"0\"`; the others `aria-selected=\"false\"` and `tabindex=\"-1\"`; the non-selected panels have the `hidden` attribute. Each panel contains a short paragraph." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<div role="tablist" aria-label="Account">\n<button type="button" role="tab" id="tab-profile" aria-selected="true" aria-controls="panel-profile" tabindex="0">Profile</button>\n<button type="button" role="tab" id="tab-billing" aria-selected="false" aria-controls="panel-billing" tabindex="-1">Billing</button>\n<button type="button" role="tab" id="tab-security" aria-selected="false" aria-controls="panel-security" tabindex="-1">Security</button>\n</div>\n<div role="tabpanel" id="panel-profile" aria-labelledby="tab-profile"><p>Your profile.</p></div>\n<div role="tabpanel" id="panel-billing" aria-labelledby="tab-billing" hidden><p>Your invoices.</p></div>\n<div role="tabpanel" id="panel-security" aria-labelledby="tab-security" hidden><p>Passwords and keys.</p></div>', "Account")},
   LOAD + BASECHK + """
tl = doc.first('div', role='tablist')
ok(tl is not None and tl.get('aria-label') == 'Account', 'tablist with label')
tabs = doc.all('button', role='tab')
ok([t.get('id') for t in tabs] == ['tab-profile', 'tab-billing', 'tab-security'], 'tab ids in order')
ok([t.text() for t in tabs] == ['Profile', 'Billing', 'Security'], 'tab texts')
ok(tl is not None and all(t in tl.children for t in tabs), 'tabs inside tablist')
panels = doc.all('div', role='tabpanel')
ok([p.get('id') for p in panels] == ['panel-profile', 'panel-billing', 'panel-security'], 'panel ids')
for t, p in zip(tabs, panels):
    ok(t.get('aria-controls') == p.get('id'), 'aria-controls ' + t.get('id'))
    ok(p.get('aria-labelledby') == t.get('id'), 'aria-labelledby ' + p.get('id'))
    ok(p.first('p') is not None and p.first('p').text(), 'panel has paragraph')
ok([t.get('aria-selected') for t in tabs] == ['true', 'false', 'false'], 'aria-selected')
ok([t.get('tabindex') for t in tabs] == ['0', '-1', '-1'], 'roving tabindex')
ok([p.has('hidden') for p in panels] == [False, True, True], 'only first panel visible')
ok(all(t.get('type') == 'button' for t in tabs), 'type=button')
""")

py("ui-html-write-accordion-markup", "write", "html", "medium", "aria",
   "Write an accordion in index.html with three sections (Shipping, Returns, Warranty). Each section heading is an `h2` containing a `<button type=\"button\" class=\"acc-trigger\">` with `aria-expanded` and `aria-controls` pointing at the panel id (`acc-shipping`, `acc-returns`, `acc-warranty`), followed by a `div.acc-panel` with that id, `role=\"region\"` and `aria-labelledby` pointing at the button's id (`btn-shipping`, ...). Only Shipping is expanded (`aria-expanded=\"true\"`); the other panels have the `hidden` attribute. Put an `h1` 'Help centre' above the accordion. To keep the heading order valid use `h2` (not h3) for the three section headings." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1>Help centre</h1>\n<div class="acc">\n<h2><button type="button" class="acc-trigger" id="btn-shipping" aria-expanded="true" aria-controls="acc-shipping">Shipping</button></h2>\n<div class="acc-panel" id="acc-shipping" role="region" aria-labelledby="btn-shipping"><p>Ships in 2 days.</p></div>\n<h2><button type="button" class="acc-trigger" id="btn-returns" aria-expanded="false" aria-controls="acc-returns">Returns</button></h2>\n<div class="acc-panel" id="acc-returns" role="region" aria-labelledby="btn-returns" hidden><p>30 day returns.</p></div>\n<h2><button type="button" class="acc-trigger" id="btn-warranty" aria-expanded="false" aria-controls="acc-warranty">Warranty</button></h2>\n<div class="acc-panel" id="acc-warranty" role="region" aria-labelledby="btn-warranty" hidden><p>2 year warranty.</p></div>\n</div>', "Help centre")},
   LOAD + BASECHK + """
h = doc.headings()
ok(h[:1] == [(1, 'Help centre')], 'h1 first')
ok([l for l, _ in h[1:]] == [2, 2, 2], 'section headings are h2: %r' % h)
btns = doc.all('button', **{'class': 'acc-trigger'})
ok([b.text() for b in btns] == ['Shipping', 'Returns', 'Warranty'], 'trigger texts')
ok(all(b.parent is not None and b.parent.tag == 'h2' for b in btns), 'button inside heading')
ok([b.get('id') for b in btns] == ['btn-shipping', 'btn-returns', 'btn-warranty'], 'button ids')
ok(all(b.get('type') == 'button' for b in btns), 'type=button')
panels = doc.all('div', **{'class': 'acc-panel'})
ok([p.get('id') for p in panels] == ['acc-shipping', 'acc-returns', 'acc-warranty'], 'panel ids')
for b, p in zip(btns, panels):
    ok(b.get('aria-controls') == p.get('id'), 'controls ' + p.get('id'))
    ok(p.get('role') == 'region' and p.get('aria-labelledby') == b.get('id'), 'region labelled by ' + b.get('id'))
ok([b.get('aria-expanded') for b in btns] == ['true', 'false', 'false'], 'expanded states')
ok([p.has('hidden') for p in panels] == [False, True, True], 'hidden panels')
""")

py("ui-html-write-modal-markup", "write", "html", "medium", "aria",
   "Write the markup of a confirmation dialog in index.html: a page with an h1 'Account', a button `#open-delete` (type button) 'Delete account', and a hidden dialog: `<div id=\"delete-dialog\" role=\"alertdialog\" aria-modal=\"true\" aria-labelledby=\"delete-title\" aria-describedby=\"delete-desc\" hidden>` containing `h2#delete-title` 'Delete account?', `p#delete-desc` 'This cannot be undone.', and two buttons: 'Cancel' (type button, id cancel-delete) and 'Delete' (type button, id confirm-delete, class danger). Also a close icon button with `aria-label=\"Close dialog\"` and an `aria-hidden` svg inside it, as the first focusable element in the dialog." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1>Account</h1>\n<button type="button" id="open-delete">Delete account</button>\n<div id="delete-dialog" role="alertdialog" aria-modal="true" aria-labelledby="delete-title" aria-describedby="delete-desc" hidden>\n<button type="button" class="close" aria-label="Close dialog"><svg viewBox="0 0 10 10" aria-hidden="true" focusable="false"><path d="M0 0L10 10"/></svg></button>\n<h2 id="delete-title">Delete account?</h2>\n<p id="delete-desc">This cannot be undone.</p>\n<button type="button" id="cancel-delete">Cancel</button>\n<button type="button" id="confirm-delete" class="danger">Delete</button>\n</div>', "Account")},
   LOAD + BASECHK + """
ok(doc.headings()[:1] == [(1, 'Account')], 'h1')
o = doc.by_id('open-delete')
ok(o is not None and o.tag == 'button' and o.get('type') == 'button' and o.text() == 'Delete account', 'open button')
d = doc.by_id('delete-dialog')
ok(d is not None and d.get('role') in ('alertdialog', 'dialog') and d.get('role') == 'alertdialog', 'alertdialog role')
ok(d is not None and d.get('aria-modal') == 'true' and d.has('hidden'), 'aria-modal and hidden')
t = doc.by_id('delete-title'); p = doc.by_id('delete-desc')
ok(t is not None and t.tag == 'h2' and t.text() == 'Delete account?', 'title h2')
ok(p is not None and p.tag == 'p' and p.text() == 'This cannot be undone.', 'description')
ok(d is not None and d.get('aria-labelledby') == 'delete-title' and d.get('aria-describedby') == 'delete-desc', 'labelled/described')
ok(d is not None and t in list(d.walk()) and p in list(d.walk()), 'title and description inside dialog')
btns = d.find_all('button') if d else []
ok(len(btns) == 3, 'three buttons in dialog')
ok(btns and btns[0].get('aria-label') == 'Close dialog', 'close button first with aria-label')
ok(btns and btns[0].first('svg') is not None and btns[0].first('svg').get('aria-hidden') == 'true', 'svg hidden')
ok(doc.by_id('cancel-delete') is not None and doc.by_id('cancel-delete').text() == 'Cancel', 'cancel')
c = doc.by_id('confirm-delete')
ok(c is not None and c.text() == 'Delete' and 'danger' in c.classes(), 'confirm')
ok(all(b.get('type') == 'button' for b in btns), 'type=button')
""")

py("ui-html-write-table", "write", "html", "medium", "tables",
   "Write an accessible data table in index.html showing this data: caption 'Monthly sales (EUR)'; columns Month, Online, Store, Total; rows Jan 1200 800 2000; Feb 1500 900 2400; Mar 1100 1000 2100. Use `caption`, `thead` with `th scope=col`, `tbody` where each Month cell is `th scope=row`, and a `tfoot` row with row header 'Quarter' and the sums (3800, 2700, 6500). Put the table in a `<div>` wrapper with `tabindex=\"0\"`, `role=\"region\"`, `aria-labelledby` pointing at an `h1` id for horizontal scrolling on small screens; the h1 text is 'Sales report'." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1 id="title">Sales report</h1>\n<div class="scroll" role="region" aria-labelledby="title" tabindex="0">\n<table>\n<caption>Monthly sales (EUR)</caption>\n<thead><tr><th scope="col">Month</th><th scope="col">Online</th><th scope="col">Store</th><th scope="col">Total</th></tr></thead>\n<tbody>\n<tr><th scope="row">Jan</th><td>1200</td><td>800</td><td>2000</td></tr>\n<tr><th scope="row">Feb</th><td>1500</td><td>900</td><td>2400</td></tr>\n<tr><th scope="row">Mar</th><td>1100</td><td>1000</td><td>2100</td></tr>\n</tbody>\n<tfoot><tr><th scope="row">Quarter</th><td>3800</td><td>2700</td><td>6500</td></tr></tfoot>\n</table>\n</div>', "Sales report")},
   LOAD + BASECHK + """
h1 = doc.first('h1'); ok(h1 is not None and h1.text() == 'Sales report' and h1.has('id'), 'h1 with id')
t = doc.first('table'); ok(t is not None, 'table')
w = t.parent if t else None
ok(w is not None and w.tag == 'div' and w.get('tabindex') == '0' and w.get('role') == 'region' and h1 is not None and w.get('aria-labelledby') == h1.get('id'), 'scroll region wrapper')
ok(t.first('caption') is not None and t.first('caption').text() == 'Monthly sales (EUR)', 'caption')
th = t.first('thead').find_all('th')
ok([x.text() for x in th] == ['Month', 'Online', 'Store', 'Total'] and all(x.get('scope') == 'col' for x in th), 'column headers')
rows = t.first('tbody').find_all('tr')
data = [('Jan', '1200', '800', '2000'), ('Feb', '1500', '900', '2400'), ('Mar', '1100', '1000', '2100')]
ok(len(rows) == 3, 'three rows')
for r, d in zip(rows, data):
    cells = [c for c in r.children if c.tag in ('th', 'td')]
    ok(cells and cells[0].tag == 'th' and cells[0].get('scope') == 'row' and tuple(c.text() for c in cells) == d, 'row ' + d[0])
tf = t.first('tfoot')
fr = [c for c in tf.first('tr').children if c.tag in ('th', 'td')] if tf else []
ok(tf is not None and tuple(c.text() for c in fr) == ('Quarter', '3800', '2700', '6500') and fr[0].tag == 'th' and fr[0].get('scope') == 'row', 'tfoot row')
""")

py("ui-html-write-breadcrumb-pagination", "write", "html", "medium", "aria",
   "Write two navigation landmarks in index.html. (1) A breadcrumb `nav` with `aria-label=\"Breadcrumb\"` containing an ordered list: Home (/), Shop (/shop), Shoes (/shop/shoes) where the LAST item is plain text (not a link) marked with `aria-current=\"page\"`. (2) A pagination `nav` with `aria-label=\"Pagination\"` containing a `ul` of links: Previous (disabled: render it as a `span` with `aria-disabled=\"true\"` instead of a link), pages 1, 2, 3 where page 2 is the current one (`aria-current=\"page\"`, link text '2', each other page link has `aria-label=\"Page N\"`), and Next (/page/3). Use an h1 'Shoes' between them." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<nav aria-label="Breadcrumb">\n<ol>\n<li><a href="/">Home</a></li>\n<li><a href="/shop">Shop</a></li>\n<li><span aria-current="page">Shoes</span></li>\n</ol>\n</nav>\n<h1>Shoes</h1>\n<nav aria-label="Pagination">\n<ul>\n<li><span aria-disabled="true">Previous</span></li>\n<li><a href="/page/1" aria-label="Page 1">1</a></li>\n<li><a href="/page/2" aria-current="page">2</a></li>\n<li><a href="/page/3" aria-label="Page 3">3</a></li>\n<li><a href="/page/3">Next</a></li>\n</ul>\n</nav>', "Shoes")},
   LOAD + BASECHK + """
navs = doc.all('nav'); ok(len(navs) == 2, 'two navs')
bc = doc.first('nav', **{'aria-label': 'Breadcrumb'}); pg = doc.first('nav', **{'aria-label': 'Pagination'})
ok(bc is not None and pg is not None, 'both navs labelled')
ol = bc.first('ol') if bc else None
items = ol.find_all('li') if ol else []
ok(len(items) == 3, 'three crumbs in an ol')
if len(items) == 3:
    ok(items[0].first('a') is not None and items[0].first('a').get('href') == '/' and items[0].text() == 'Home', 'Home link')
    ok(items[1].first('a') is not None and items[1].first('a').get('href') == '/shop' and items[1].text() == 'Shop', 'Shop link')
    ok(items[2].first('a') is None and items[2].text() == 'Shoes', 'last crumb is text')
    cur = [e for e in items[2].walk() if e.get('aria-current') == 'page'] + ([items[2]] if items[2].get('aria-current') == 'page' else [])
    ok(len(cur) == 1, 'last crumb has aria-current=page')
ok(doc.headings()[:1] == [(1, 'Shoes')], 'h1')
ul = pg.first('ul') if pg else None
li = ul.find_all('li') if ul else []
ok(len(li) == 5, 'five pagination items')
if len(li) == 5:
    ok(li[0].first('a') is None and li[0].first('span') is not None and li[0].first('span').get('aria-disabled') == 'true' and li[0].text() == 'Previous', 'previous disabled span')
    ok(li[1].first('a') is not None and li[1].first('a').get('aria-label') == 'Page 1' and li[1].first('a').get('href') == '/page/1', 'page 1')
    ok(li[2].first('a') is not None and li[2].first('a').get('aria-current') == 'page' and li[2].first('a').text() == '2', 'current page 2')
    ok(li[3].first('a') is not None and li[3].first('a').get('aria-label') == 'Page 3', 'page 3')
    ok(li[4].first('a') is not None and li[4].first('a').get('href') == '/page/3' and li[4].text() == 'Next', 'next')
ok(len([a for a in doc.all() if a.get('aria-current') == 'page']) == 2, 'exactly two aria-current=page (one per nav)')
""")

py("ui-html-write-search-form", "write", "html", "easy", "forms",
   "Write a site search in index.html: a `<form role=\"search\" action=\"/search\" method=\"get\">` with a visible-or-visually-hidden `<label for=\"q\">Search articles</label>`, an `<input type=\"search\" id=\"q\" name=\"q\" autocomplete=\"off\">` and a `<button type=\"submit\">Search</button>`. Place it inside a `<header>` together with an `h1` 'Articles' (the h1 comes first in the header). Below the header add a `<main>` with a `<p id=\"result-count\" role=\"status\">0 results</p>`." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<header>\n<h1>Articles</h1>\n<form role="search" action="/search" method="get">\n<label for="q">Search articles</label>\n<input type="search" id="q" name="q" autocomplete="off">\n<button type="submit">Search</button>\n</form>\n</header>\n<main>\n<p id="result-count" role="status">0 results</p>\n</main>', "Articles")},
   LOAD + BASECHK + """
hd = doc.first('header'); ok(hd is not None, 'header')
h1 = doc.first('h1')
ok(h1 is not None and h1.text() == 'Articles' and hd is not None and h1 in list(hd.walk()), 'h1 in header')
kids = [c for c in hd.children] if hd else []
ok(kids and kids[0].tag == 'h1', 'h1 first in header')
f = doc.first('form')
ok(f is not None and f.get('role') == 'search' and f.get('action') == '/search' and f.get('method', '').lower() == 'get', 'search form')
q = doc.by_id('q')
ok(q is not None and q.tag == 'input' and q.get('type') == 'search' and q.get('name') == 'q' and q.get('autocomplete') == 'off', 'input')
ok(q is not None and doc.label_text(q) == 'Search articles', 'label')
b = doc.first('button', type='submit'); ok(b is not None and b.text() == 'Search', 'submit')
m = doc.first('main'); rc = doc.by_id('result-count')
ok(m is not None and rc is not None and rc in list(m.walk()) and rc.get('role') == 'status' and rc.text() == '0 results', 'status paragraph in main')
ok(hd is not None and m is not None and hd.parent is m.parent, 'header and main are siblings')
""")

py("ui-html-write-faq-details", "write", "html", "easy", "semantics",
   "Write a FAQ in index.html with native disclosure widgets: an h1 'FAQ', then three `<details>` elements, each with a `<summary>` question and a `<p>` answer. Questions: 'How do I reset my password?', 'Can I change my plan?', 'Where are invoices?'. The FIRST details is open (`open` attribute). Put the h1 (with id `faq-title`) first, then a `<section aria-labelledby=\"faq-title\">` after it (the h1 stays outside the section) containing the three details as direct children." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1 id="faq-title">FAQ</h1>\n<section aria-labelledby="faq-title">\n<details open><summary>How do I reset my password?</summary><p>Use the reset link.</p></details>\n<details><summary>Can I change my plan?</summary><p>Yes, any time.</p></details>\n<details><summary>Where are invoices?</summary><p>In Billing.</p></details>\n</section>', "FAQ")},
   LOAD + BASECHK + """
h1 = doc.first('h1'); ok(h1 is not None and h1.text() == 'FAQ' and h1.get('id') == 'faq-title', 'h1 id')
s = doc.first('section')
ok(s is not None and s.get('aria-labelledby') == 'faq-title', 'section labelled by h1')
ok(s is not None and h1 not in list(s.walk()), 'h1 outside section')
ds = doc.all('details')
ok(len(ds) == 3, 'three details')
qs = ['How do I reset my password?', 'Can I change my plan?', 'Where are invoices?']
for d, q in zip(ds, qs):
    sm = [c for c in d.children if c.tag == 'summary']
    ok(len(sm) == 1 and sm[0].text() == q, 'summary ' + q)
    ok(d.children and d.children[0].tag == 'summary', 'summary is first child')
    ok(d.first('p') is not None and d.first('p').text() != '', 'answer paragraph')
ok([d.has('open') for d in ds] == [True, False, False], 'only first open')
ok(s is not None and all(d in s.children for d in ds), 'details are direct children of section')
""")

py("ui-html-write-picture", "write", "html", "medium", "responsive",
   "Write a responsive hero image in index.html using `<picture>`: two `<source>` elements: (1) `media=\"(min-width: 800px)\" srcset=\"hero-wide.webp\"` and (2) `srcset=\"hero-narrow.webp\"` (no media), in that order, both `type=\"image/webp\"`; fallback `<img src=\"hero.jpg\" alt=\"A hiker on a ridge at sunrise\" width=\"1600\" height=\"900\" loading=\"lazy\" decoding=\"async\">`. The picture sits inside a `<figure>` with a `<figcaption>` 'Sunrise on the ridge'. Add an h1 'Trail notes' before it." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1>Trail notes</h1>\n<figure>\n<picture>\n<source media="(min-width: 800px)" srcset="hero-wide.webp" type="image/webp">\n<source srcset="hero-narrow.webp" type="image/webp">\n<img src="hero.jpg" alt="A hiker on a ridge at sunrise" width="1600" height="900" loading="lazy" decoding="async">\n</picture>\n<figcaption>Sunrise on the ridge</figcaption>\n</figure>', "Trail notes")},
   LOAD + BASECHK + """
ok(doc.headings()[:1] == [(1, 'Trail notes')], 'h1')
fig = doc.first('figure'); ok(fig is not None, 'figure')
pic = fig.first('picture') if fig else None
ok(pic is not None, 'picture in figure')
src = pic.find_all('source') if pic else []
ok(len(src) == 2, 'two sources')
if len(src) == 2:
    ok(src[0].get('media') == '(min-width: 800px)' and src[0].get('srcset') == 'hero-wide.webp' and src[0].get('type') == 'image/webp', 'wide source first')
    ok(not src[1].has('media') and src[1].get('srcset') == 'hero-narrow.webp' and src[1].get('type') == 'image/webp', 'narrow source second')
img = pic.first('img') if pic else None
ok(img is not None and pic.children[-1] is img, 'img is last child of picture')
ok(img is not None and img.get('src') == 'hero.jpg' and img.get('alt') == 'A hiker on a ridge at sunrise', 'img src/alt')
ok(img is not None and img.get('width') == '1600' and img.get('height') == '900', 'width/height set (avoids layout shift)')
ok(img is not None and img.get('loading') == 'lazy' and img.get('decoding') == 'async', 'lazy async')
fc = fig.first('figcaption') if fig else None
ok(fc is not None and fc.text() == 'Sunrise on the ridge', 'figcaption')
""")

py("ui-html-write-live-regions", "write", "html", "easy", "aria",
   "Write a page in index.html with an h1 'Upload' and two live regions that exist in the DOM from the start (empty): a polite status message `<div id=\"status\" role=\"status\" aria-live=\"polite\" aria-atomic=\"true\"></div>` and an assertive error `<div id=\"error\" role=\"alert\"></div>`. Add a file input `#file` (`type=\"file\"`, `accept=\".png,.jpg\"`, labelled 'Choose image') and a button `#upload` 'Upload' (type button) that is `aria-describedby=\"status\"`. A `<progress id=\"pct\" max=\"100\" value=\"0\" aria-labelledby=\"pct-label\">` with a `<span id=\"pct-label\">Upload progress</span>`." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1>Upload</h1>\n<p><label for="file">Choose image</label> <input type="file" id="file" accept=".png,.jpg"></p>\n<button type="button" id="upload" aria-describedby="status">Upload</button>\n<p><span id="pct-label">Upload progress</span> <progress id="pct" max="100" value="0" aria-labelledby="pct-label"></progress></p>\n<div id="status" role="status" aria-live="polite" aria-atomic="true"></div>\n<div id="error" role="alert"></div>', "Upload")},
   LOAD + BASECHK + """
ok(doc.headings()[:1] == [(1, 'Upload')], 'h1')
s = doc.by_id('status'); e = doc.by_id('error')
ok(s is not None and s.get('role') == 'status' and s.get('aria-live') == 'polite' and s.get('aria-atomic') == 'true' and s.text() == '', 'status region empty')
ok(e is not None and e.get('role') == 'alert' and e.text() == '', 'alert region empty')
ok(s is not None and not s.has('hidden') and e is not None and not e.has('hidden'), 'live regions not hidden')
f = doc.by_id('file')
ok(f is not None and f.get('type') == 'file' and f.get('accept') == '.png,.jpg' and doc.label_text(f) == 'Choose image', 'file input')
u = doc.by_id('upload')
ok(u is not None and u.tag == 'button' and u.get('type') == 'button' and u.text() == 'Upload' and u.get('aria-describedby') == 'status', 'upload button')
p = doc.by_id('pct')
ok(p is not None and p.tag == 'progress' and p.get('max') == '100' and p.get('value') == '0' and p.get('aria-labelledby') == 'pct-label', 'progress')
ok(doc.by_id('pct-label') is not None and doc.by_id('pct-label').text() == 'Upload progress', 'progress label')
""")

py("ui-html-write-card-list", "write", "html", "medium", "semantics",
   "Write a product list in index.html: h1 'Products', then a `<ul class=\"cards\">` with three `<li>`; each li holds an `<article class=\"card\">` with an `h2` (product name), an `<img>` (real alt describing the product, src `p1.jpg`/`p2.jpg`/`p3.jpg`, width and height attributes), a `<p class=\"price\">` containing a `<data value=\"19.99\">$19.99</data>`-style element (value = number, text = '$' + number) and a link `<a href=\"/p/1\">` whose accessible name contains the product name (e.g. 'View Desk Lamp'). Products: Desk Lamp 19.99, Notebook 4.5, Backpack 49. The first image is above the fold; the others get `loading=\"lazy\"`." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1>Products</h1>\n<ul class="cards">\n<li><article class="card"><h2>Desk Lamp</h2><img src="p1.jpg" alt="Black adjustable desk lamp" width="300" height="200"><p class="price"><data value="19.99">$19.99</data></p><a href="/p/1">View Desk Lamp</a></article></li>\n<li><article class="card"><h2>Notebook</h2><img src="p2.jpg" alt="Green hardcover notebook" width="300" height="200" loading="lazy"><p class="price"><data value="4.5">$4.5</data></p><a href="/p/2">View Notebook</a></article></li>\n<li><article class="card"><h2>Backpack</h2><img src="p3.jpg" alt="Grey canvas backpack" width="300" height="200" loading="lazy"><p class="price"><data value="49">$49</data></p><a href="/p/3">View Backpack</a></article></li>\n</ul>', "Products")},
   LOAD + BASECHK + """
ok(doc.headings()[0] == (1, 'Products') and [l for l, _ in doc.headings()[1:]] == [2, 2, 2], 'heading structure')
ul = doc.first('ul', **{'class': 'cards'}); ok(ul is not None, 'ul.cards')
lis = [c for c in ul.children if c.tag == 'li'] if ul else []
ok(len(lis) == 3 and len(ul.children) == 3, 'three li direct children')
items = [('Desk Lamp', '19.99'), ('Notebook', '4.5'), ('Backpack', '49')]
for i, (li, (name, price)) in enumerate(zip(lis, items), 1):
    a = li.first('article', **{'class': 'card'})
    ok(a is not None, 'article in li %d' % i)
    if a is None: continue
    ok(a.first('h2') is not None and a.first('h2').text() == name, 'h2 ' + name)
    im = a.first('img')
    ok(im is not None and im.get('src') == 'p%d.jpg' % i and len(im.get('alt', '')) >= 8 and im.has('width') and im.has('height'), 'img attrs ' + name)
    ok(im is not None and (im.get('loading') == 'lazy') == (i > 1), 'lazy only for images after the first')
    d = a.first('data')
    ok(d is not None and d.get('value') == price and d.text() == '$' + price and any(x.tag == 'p' and 'price' in x.classes() for x in d.ancestors()), 'price data ' + name)
    l = a.first('a', href='/p/%d' % i)
    ok(l is not None and name.lower() in doc.name_of(l).lower(), 'link name contains product name ' + name)
""")

py("ui-html-write-article-page", "write", "html", "hard", "semantics",
   "Write a blog post page in index.html using semantic elements: `header` (site name as a link to `/`, and a `nav` labelled 'Primary' with 3 links), then `main` containing an `article` with an `h1` 'Why we moved to vanilla JS', a `<p class=\"meta\">` with `<time datetime=\"2026-03-05\">March 5, 2026</time>`, two paragraphs, a `<figure>` with `<img>` (alt text) and `<figcaption>`, a `<blockquote>` with a `<cite>`-attributed footer, and a `<section aria-labelledby=\"comments-title\">` with `h2#comments-title` 'Comments (2)' and an ordered list of two comments each in an `<li>` with `<article>`. Add an `aside` with `aria-label=\"Related posts\"` containing a list of 2 links, and a page-level `footer` (a direct child of body). Exactly one `main`, one `h1`, and the first focusable element must be a skip link to `#content` (the `main` has id `content`)." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<a href="#content" class="skip">Skip to content</a>\n<header>\n<a href="/" class="site">Notes</a>\n<nav aria-label="Primary"><a href="/">Home</a> <a href="/archive">Archive</a> <a href="/about">About</a></nav>\n</header>\n<main id="content">\n<article>\n<h1>Why we moved to vanilla JS</h1>\n<p class="meta"><time datetime="2026-03-05">March 5, 2026</time></p>\n<p>First paragraph.</p>\n<p>Second paragraph.</p>\n<figure><img src="bundle.png" alt="Bundle size chart going down" width="600" height="300"><figcaption>Bundle size over time</figcaption></figure>\n<blockquote><p>Simple is better.</p><footer>- <cite>A. Dev</cite></footer></blockquote>\n<section aria-labelledby="comments-title">\n<h2 id="comments-title">Comments (2)</h2>\n<ol>\n<li><article><p>Nice!</p></article></li>\n<li><article><p>Agree.</p></article></li>\n</ol>\n</section>\n</article>\n<aside aria-label="Related posts"><ul><li><a href="/p/a">Post A</a></li><li><a href="/p/b">Post B</a></li></ul></aside>\n</main>\n<footer><p>(c) 2026 Notes</p></footer>', "Why we moved to vanilla JS")},
   LOAD + BASECHK + """
body = doc.first('body')
for t in ('header', 'main'):
    ok(len(doc.all(t)) == 1, 'one ' + t)
ok(len([f for f in doc.all('footer') if f.parent is body]) == 1, 'one page footer (direct child of body)')
ok(len(doc.all('h1')) == 1, 'one h1')
foc = [e for e in body.walk() if e.tag in ('a', 'button', 'input')]
ok(foc and foc[0].get('href') == '#content', 'skip link first')
m = doc.first('main'); ok(m is not None and m.get('id') == 'content', 'main#content')
hd = doc.first('header')
ok(hd is not None and hd.first('a', href='/') is not None, 'site link in header')
nav = hd.first('nav') if hd else None
ok(nav is not None and nav.get('aria-label') == 'Primary' and len(nav.find_all('a')) == 3, 'primary nav with 3 links')
art = m.first('article') if m else None
ok(art is not None and art.first('h1') is not None and art.first('h1').text() == 'Why we moved to vanilla JS', 'article h1')
tm = art.first('time') if art else None
ok(tm is not None and tm.get('datetime') == '2026-03-05' and tm.text() == 'March 5, 2026', 'time element')
ok(art is not None and len([p for p in art.children if p.tag == 'p' and 'meta' not in p.classes()]) >= 2, 'two body paragraphs')
fg = art.first('figure') if art else None
ok(fg is not None and fg.first('img') is not None and len(fg.first('img').get('alt', '')) >= 8 and fg.first('figcaption') is not None, 'figure with alt and caption')
bq = art.first('blockquote') if art else None
ok(bq is not None and bq.first('cite') is not None and bq.first('footer') is not None, 'blockquote attribution')
sec = art.first('section') if art else None
ok(sec is not None and sec.get('aria-labelledby') == 'comments-title', 'comments section')
h2 = doc.by_id('comments-title'); ok(h2 is not None and h2.tag == 'h2' and h2.text() == 'Comments (2)', 'comments heading')
ol = sec.first('ol') if sec else None
cs = ol.find_all('li') if ol else []
ok(len(cs) == 2 and all(c.first('article') is not None for c in cs), 'two comments as li>article')
asd = doc.first('aside')
ok(asd is not None and asd.get('aria-label') == 'Related posts' and len(asd.find_all('a')) == 2 and asd.first('ul') is not None, 'aside related posts')
ok([f for f in doc.all('footer') if f.parent is body][0].text() != '', 'footer text')
""")

py("ui-html-write-select-combo", "write", "html", "medium", "forms",
   "Write a shipping form fragment in index.html: a `<select id=\"country\" name=\"country\" required autocomplete=\"country\">` labelled 'Country' with a first disabled+selected empty-value placeholder option 'Select a country', then two `<optgroup>`s: label 'Europe' (options DE Germany, FR France, ES Spain) and label 'Americas' (US United States, CA Canada). Then a `<datalist id=\"carriers\">` with options DHL, UPS, FedEx and an `<input list=\"carriers\" id=\"carrier\" name=\"carrier\">` labelled 'Carrier (optional)'. Finally a `<textarea id=\"notes\" name=\"notes\" rows=\"3\" maxlength=\"200\" aria-describedby=\"notes-hint\">` labelled 'Delivery notes' with `<p id=\"notes-hint\">Max 200 characters</p>`. All in a form with a submit button." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1>Shipping</h1>\n<form action="/ship" method="post">\n<p><label for="country">Country</label>\n<select id="country" name="country" required autocomplete="country">\n<option value="" disabled selected>Select a country</option>\n<optgroup label="Europe"><option value="DE">Germany</option><option value="FR">France</option><option value="ES">Spain</option></optgroup>\n<optgroup label="Americas"><option value="US">United States</option><option value="CA">Canada</option></optgroup>\n</select></p>\n<p><label for="carrier">Carrier (optional)</label>\n<input list="carriers" id="carrier" name="carrier">\n<datalist id="carriers"><option value="DHL"><option value="UPS"><option value="FedEx"></datalist></p>\n<p><label for="notes">Delivery notes</label>\n<textarea id="notes" name="notes" rows="3" maxlength="200" aria-describedby="notes-hint"></textarea></p>\n<p id="notes-hint">Max 200 characters</p>\n<button type="submit">Continue</button>\n</form>', "Shipping")},
   LOAD + BASECHK + """
s = doc.by_id('country')
ok(s is not None and s.tag == 'select' and s.get('name') == 'country' and s.has('required') and s.get('autocomplete') == 'country' and doc.label_text(s) == 'Country', 'select')
opts = s.find_all('option') if s else []
ok(opts and opts[0].get('value') == '' and opts[0].has('disabled') and opts[0].has('selected') and opts[0].text() == 'Select a country', 'placeholder option')
ogs = s.find_all('optgroup') if s else []
ok([g.get('label') for g in ogs] == ['Europe', 'Americas'], 'optgroups')
if len(ogs) == 2:
    ok([(o.get('value'), o.text()) for o in ogs[0].find_all('option')] == [('DE', 'Germany'), ('FR', 'France'), ('ES', 'Spain')], 'Europe options')
    ok([(o.get('value'), o.text()) for o in ogs[1].find_all('option')] == [('US', 'United States'), ('CA', 'Canada')], 'Americas options')
c = doc.by_id('carrier'); dl = doc.by_id('carriers')
ok(c is not None and c.get('list') == 'carriers' and c.get('name') == 'carrier' and doc.label_text(c) == 'Carrier (optional)', 'carrier input')
ok(dl is not None and dl.tag == 'datalist' and [o.get('value') for o in dl.find_all('option')] == ['DHL', 'UPS', 'FedEx'], 'datalist')
n = doc.by_id('notes')
ok(n is not None and n.tag == 'textarea' and n.get('rows') == '3' and n.get('maxlength') == '200' and doc.label_text(n) == 'Delivery notes', 'textarea')
h = doc.by_id('notes-hint')
ok(n is not None and h is not None and n.get('aria-describedby') == 'notes-hint' and h.text() == 'Max 200 characters', 'hint')
ok(doc.first('form') is not None and doc.first('button', type='submit') is not None, 'form and submit')
""")

py("ui-html-write-combobox-markup", "write", "html", "hard", "aria",
   "Write the initial (closed) static markup of an ARIA 1.2 list-autocomplete combobox in index.html: `<label for=\"city\" id=\"city-label\">City</label>`, `<input id=\"city\" type=\"text\" role=\"combobox\" aria-autocomplete=\"list\" aria-expanded=\"false\" aria-controls=\"city-list\" autocomplete=\"off\">`, and `<ul id=\"city-list\" role=\"listbox\" aria-labelledby=\"city-label\" hidden>` with three options `<li role=\"option\" id=\"city-opt-0\">`.. (Berlin, Lisbon, Madrid), all `aria-selected=\"false\"`. No `aria-activedescendant` yet (nothing is active). Add a visually-hidden live region `<div id=\"city-status\" class=\"sr-only\" role=\"status\"></div>` after the list and an h1 'Where to?'." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1>Where to?</h1>\n<label for="city" id="city-label">City</label>\n<input id="city" type="text" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="city-list" autocomplete="off">\n<ul id="city-list" role="listbox" aria-labelledby="city-label" hidden>\n<li role="option" id="city-opt-0" aria-selected="false">Berlin</li>\n<li role="option" id="city-opt-1" aria-selected="false">Lisbon</li>\n<li role="option" id="city-opt-2" aria-selected="false">Madrid</li>\n</ul>\n<div id="city-status" class="sr-only" role="status"></div>', "Where to?")},
   LOAD + BASECHK + """
ok(doc.headings()[:1] == [(1, 'Where to?')], 'h1')
i = doc.by_id('city')
ok(i is not None and i.tag == 'input' and i.get('role') == 'combobox' and i.get('aria-autocomplete') == 'list' and i.get('aria-expanded') == 'false' and i.get('aria-controls') == 'city-list' and i.get('autocomplete') == 'off', 'combobox input')
ok(i is not None and not i.has('aria-activedescendant'), 'no activedescendant when closed')
ok(i is not None and doc.label_text(i) == 'City', 'input labelled City')
lb = doc.by_id('city-label'); ok(lb is not None and lb.tag == 'label' and lb.get('for') == 'city', 'label for')
l = doc.by_id('city-list')
ok(l is not None and l.get('role') == 'listbox' and l.get('aria-labelledby') == 'city-label' and l.has('hidden'), 'listbox hidden and labelled')
o = l.find_all('li') if l else []
ok([x.text() for x in o] == ['Berlin', 'Lisbon', 'Madrid'], 'option texts')
ok([x.get('id') for x in o] == ['city-opt-0', 'city-opt-1', 'city-opt-2'], 'option ids')
ok(all(x.get('role') == 'option' and x.get('aria-selected') == 'false' for x in o), 'option roles and selected=false')
s = doc.by_id('city-status')
ok(s is not None and s.get('role') == 'status' and 'sr-only' in s.classes() and s.text() == '', 'status region')
kids = [c for c in i.parent.children if c.tag in ('input', 'ul', 'div')] if i and i.parent else []
ok([k.get('id') for k in kids][:3] == ['city', 'city-list', 'city-status'], 'status after list')
""")

py("ui-html-write-progress-meter", "write", "html", "easy", "semantics",
   "Write a dashboard fragment in index.html: h1 'Storage', a labelled `<progress id=\"upload\" max=\"100\" value=\"70\">` (label 'Upload progress', via `<label for=\"upload\">`) with fallback text '70%', and a `<meter id=\"disk\" min=\"0\" max=\"100\" low=\"50\" high=\"80\" optimum=\"20\" value=\"85\">` labelled 'Disk used' with fallback text '85%'. Each also has the visible value in a `<output for=\"upload\">`/`<output for=\"disk\">` ('70%' and '85%')." + BASE + FMT,
   {"index.html": EMPTY},
   {"index.html": PAGE('<h1>Storage</h1>\n<p><label for="upload">Upload progress</label> <progress id="upload" max="100" value="70">70%</progress> <output for="upload">70%</output></p>\n<p><label for="disk">Disk used</label> <meter id="disk" min="0" max="100" low="50" high="80" optimum="20" value="85">85%</meter> <output for="disk">85%</output></p>', "Storage")},
   LOAD + BASECHK + """
ok(doc.headings()[:1] == [(1, 'Storage')], 'h1')
p = doc.by_id('upload'); m = doc.by_id('disk')
ok(p is not None and p.tag == 'progress' and p.get('max') == '100' and p.get('value') == '70' and p.text() == '70%', 'progress')
ok(p is not None and doc.label_text(p) == 'Upload progress', 'progress label')
ok(m is not None and m.tag == 'meter' and [m.get(k) for k in ('min', 'max', 'low', 'high', 'optimum', 'value')] == ['0', '100', '50', '80', '20', '85'] and m.text() == '85%', 'meter')
ok(m is not None and doc.label_text(m) == 'Disk used', 'meter label')
outs = doc.all('output')
ok(sorted((o.get('for'), o.text()) for o in outs) == [('disk', '85%'), ('upload', '70%')], 'outputs')
""")

py("ui-html-extend-add-field", "extend", "html", "medium", "forms",
   "Extend the form in index.html: add a 'Phone number' field between Email and the submit button. It must be a labelled `<input type=\"tel\" id=\"phone\" name=\"phone\" autocomplete=\"tel\" inputmode=\"tel\" pattern=\"[0-9+() -]{7,}\" aria-describedby=\"phone-hint\">` (optional, not required) followed by `<small id=\"phone-hint\">Include country code, e.g. +49 30 1234567</small>`. Do not change the existing fields, labels or button." + FMT,
   {"index.html": PAGE('<form action="/contact" method="post">\n<p><label for="name">Name</label> <input id="name" name="name" required></p>\n<p><label for="email">Email</label> <input id="email" name="email" type="email" required></p>\n<button type="submit">Send</button>\n</form>', "Contact")},
   {"index.html": PAGE('<form action="/contact" method="post">\n<p><label for="name">Name</label> <input id="name" name="name" required></p>\n<p><label for="email">Email</label> <input id="email" name="email" type="email" required></p>\n<p><label for="phone">Phone number</label> <input type="tel" id="phone" name="phone" autocomplete="tel" inputmode="tel" pattern="[0-9+() -]{7,}" aria-describedby="phone-hint"> <small id="phone-hint">Include country code, e.g. +49 30 1234567</small></p>\n<button type="submit">Send</button>\n</form>', "Contact")},
   LOAD + """
f = doc.first('form')
ctrl = [e for e in f.walk() if e.tag in ('input', 'button')] if f else []
ok([c.get('name') or 'btn' for c in ctrl] == ['name', 'email', 'phone', 'btn'], 'order name, email, phone, button: %r' % [c.get('name') or 'btn' for c in ctrl])
ph = doc.by_id('phone')
ok(ph is not None and ph.get('type') == 'tel' and ph.get('name') == 'phone' and ph.get('autocomplete') == 'tel' and ph.get('inputmode') == 'tel', 'phone attributes')
ok(ph is not None and ph.get('pattern') == '[0-9+() -]{7,}' and not ph.has('required'), 'pattern, optional')
ok(ph is not None and doc.label_text(ph) == 'Phone number', 'label')
h = doc.by_id('phone-hint')
ok(h is not None and h.tag == 'small' and h.text() == 'Include country code, e.g. +49 30 1234567' and ph is not None and ph.get('aria-describedby') == 'phone-hint', 'hint linked')
n = doc.by_id('name'); e = doc.by_id('email')
ok(n is not None and n.has('required') and doc.label_text(n) == 'Name', 'name field untouched')
ok(e is not None and e.get('type') == 'email' and e.has('required') and doc.label_text(e) == 'Email', 'email field untouched')
b = doc.first('button', type='submit'); ok(b is not None and b.text() == 'Send', 'button untouched')
ids = doc.ids(); ok(len(ids) == len(set(ids)), 'unique ids')
""")
