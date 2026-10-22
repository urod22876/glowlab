# usage: python3 pro_e2e.py <site_dir> <out_dir> [phone|desk]
# Free user: 1 free analysis then locked, plan/progress locked, checkout URL. Pro user (fake Firebase + fake /api/pro):
# activation after checkout return, plan, 30-day checklist, progress chart, Pro window, account page. Prints errors.
import sys, threading, http.server, functools, socketserver, os, json, time
from playwright.sync_api import sync_playwright
site, out = sys.argv[1], sys.argv[2]; mode = sys.argv[3] if len(sys.argv) > 3 else 'phone'
os.makedirs(out, exist_ok=True)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site); H.func.log_message = lambda *a: None
class Q(socketserver.ThreadingTCPServer): allow_reuse_address = True
srv = Q(('127.0.0.1', 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{port}/'
VP = {'phone': ({'width': 390, 'height': 844}, True), 'desk': ({'width': 1280, 'height': 900}, False)}[mode]
IMG_F = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_front.jpg')
IMG_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_profile.jpg')
BASE = "localStorage.setItem('gl_lang','ru');localStorage.setItem('gl_age18','1');localStorage.setItem('gl_user',JSON.stringify({n:'Idris',e:'t@t.t',u:'tst'}));localStorage.setItem('gl_prof_tst',JSON.stringify({done:true,name:'Idris',sex:'m',dob:'2000-01-01',bother:['bt_3']}));"
# fake Firebase: signed-in user tst, Firestore that stores nothing
FB = """window.__fbset=[];window.firebase={apps:[],initializeApp:function(){return{}},app:function(){return{}},
auth:Object.assign(function(){return window.__auth||(window.__auth={languageCode:'ru',currentUser:{uid:'tst',email:'t@t.t',displayName:'Idris',photoURL:'',getIdToken:function(){return Promise.resolve('TOKEN')}},
 onAuthStateChanged:function(cb){var s=this;setTimeout(function(){cb(s.currentUser)},60)},signOut:function(){return Promise.resolve()}})},{GoogleAuthProvider:function(){this.setCustomParameters=function(){}}}),
firestore:function(){return{collection:function(){return{doc:function(){return{get:function(){return Promise.resolve({exists:false,data:function(){return{}}})},set:function(d){window.__fbset.push(d);return Promise.resolve()}}}}}}}};"""
errs = []; res = {}
def ctxpage(b, init, fake_fb=False):
    ctx = b.new_context(viewport=VP[0], is_mobile=VP[1], has_touch=VP[1])
    ctx.add_init_script("try{" + BASE + init + "}catch(e){}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)[:300]))
    pg.on('console', lambda m: errs.append('CONSOLE ' + m.text[:200]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    if fake_fb:
        pg.route('https://www.gstatic.com/firebasejs/**', lambda r: r.fulfill(status=200, content_type='application/javascript', body=FB if 'app-compat' in r.request.url else ''))
    else:
        pg.route('https://www.gstatic.com/firebasejs/**', lambda r: r.abort())
    return ctx, pg
def scan(pg, kind, img):
    if kind == 'profile': pg.click('[data-mode=profile]')
    host = '#hostFront' if kind == 'front' else '#hostProfile'
    pg.locator(host + ' .f-up').set_input_files([])
    pg.locator(host + ' .f-up').set_input_files(img)
    pg.wait_for_function("h=>{var c=document.querySelector(h+' .psl-card');return c&&!c.hidden&&(c.classList.contains('play')||c.classList.contains('done'))}", arg=host, timeout=120000)
    pg.wait_for_timeout(1800)
    pg.evaluate("()=>{var x=document.querySelector('.rm .rm-x'); if(x) x.click();}"); pg.wait_for_timeout(500)
def go(pg, pane): pg.evaluate("p=>{var b=document.querySelector('.appbar [data-go='+p+']'); b&&b.click();}", pane); pg.wait_for_timeout(700)
def shot(pg, name, sel=None):
    if sel: pg.locator(sel).first.screenshot(path=f'{out}/{mode}_{name}.png')
    else: pg.screenshot(path=f'{out}/{mode}_{name}.png')

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    # ---------- 1. free user: one free analysis per side, then locked ----------
    ctx, pg = ctxpage(b, "")
    checkout = []
    pg.route('https://checkout.dodopayments.com/**', lambda r: (checkout.append(r.request.url), r.fulfill(status=200, body='checkout')))
    pg.goto(URL, wait_until='load'); pg.wait_for_timeout(1500)
    res['free_used_before'] = pg.evaluate("()=>document.querySelector('#hostFront .used').hidden")
    scan(pg, 'front', IMG_F)
    res['free_front_flag'] = pg.evaluate("()=>localStorage.getItem('gl_used3_tst_front')")
    res['free_used_after'] = pg.evaluate("()=>document.querySelector('#hostFront .used').hidden")
    res['free_upsell'] = pg.evaluate("()=>{var u=document.querySelector('#hostFront .upsell');return [u.classList.contains('is-pro'),u.querySelector('.ups-btn').textContent]}")
    res['free_mx_locked'] = pg.evaluate("()=>!!document.querySelector('#hostFront .lk') && !document.querySelector('#hostFront .mx-sec')")
    # try a second analysis: the file picker must not open, the "used" block shows
    pg.evaluate("()=>{document.querySelector('#hostFront .remove').click()}"); pg.wait_for_timeout(400)
    opened = []
    pg.on('filechooser', lambda fc: opened.append(1))
    pg.evaluate("()=>{document.querySelector('#hostFront .up').click()}"); pg.wait_for_timeout(600)
    res['free_second_blocked'] = (not opened) and pg.evaluate("()=>!document.querySelector('#hostFront .used').hidden")
    shot(pg, 'free_used', '#hostFront .used')
    res['hist_free'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_hist_tst')||'[]').length")
    go(pg, 'guides')
    res['free_plan'] = pg.evaluate("()=>({rows:document.querySelectorAll('#mp details.mp-row').length, lock:!!document.querySelector('#mp .mp-lock'), pg:(document.querySelector('#pg .mp-lock p')||{}).textContent})")
    shot(pg, 'free_plan', '.mp-wrap')
    go(pg, 'pro')
    pg.evaluate("()=>{var e=document.querySelector('[data-plan=pro]'); e&&e.click();}"); pg.wait_for_timeout(600)
    res['free_pricing'] = pg.evaluate("()=>({h:document.querySelector('.pr-card h3').textContent, li:[...document.querySelectorAll('.pr-list li')].map(x=>x.textContent)})")
    shot(pg, 'free_pricing')
    pg.evaluate("()=>document.querySelector('.pr-go').click()"); pg.wait_for_timeout(1500)
    res['checkout_url'] = checkout[:1]
    ctx.close()

    # ---------- 2. checkout return: failed payment ----------
    ctx, pg = ctxpage(b, "")
    pg.goto(URL + '?checkout=done&payment_id=pay_1&status=failed', wait_until='load'); pg.wait_for_timeout(1500)
    res['ret_failed'] = pg.evaluate("()=>({t:(document.querySelector('.pt.on')||{}).textContent, url:location.search})")
    ctx.close()

    # ---------- 3. checkout return: payment ok, the server sees the subscription on the 2nd check ----------
    ctx, pg = ctxpage(b, "", fake_fb=True)
    calls = []
    until = time.strftime('%Y-%m-%dT00:00:00Z', time.gmtime(time.time() + 30 * 86400))
    def api(r):
        calls.append((r.request.url, r.request.headers.get('authorization')))
        body = {'pro': False, 'until': None, 'renews': False} if len(calls) < 2 else {'pro': True, 'until': until, 'renews': True}
        r.fulfill(status=200, content_type='application/json', body=json.dumps(body))
    pg.route('**/api/pro', api)
    pg.route('**/api/portal', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps({'link': URL + '#portal-ok'})))
    hist = json.dumps([{'t': int(time.time() * 1000) - 20 * 86400000, 'k': 'front', 'p': 3.1, 's': 52, 'w': ['jaw']}, {'t': int(time.time() * 1000) - 10 * 86400000, 'k': 'front', 'p': 3.3, 's': 55, 'w': []}, {'t': int(time.time() * 1000) - 9 * 86400000, 'k': 'profile', 'p': 4.0, 's': 60, 'w': []}])
    pg.add_init_script("try{localStorage.setItem('gl_hist_tst'," + json.dumps(hist) + ")}catch(e){}")
    pg.goto(URL + '?checkout=done&payment_id=pay_1&status=succeeded', wait_until='load')
    pg.wait_for_timeout(800); res['ret_wait'] = pg.evaluate("()=>(document.querySelector('.pt.on')||{}).textContent")
    pg.wait_for_function("()=>{var t=document.querySelector('.pt.on');return t&&/активирован/.test(t.textContent)}", timeout=20000)
    res['ret_ok'] = pg.evaluate("()=>({t:document.querySelector('.pt.on').textContent, url:location.search, auth:true})")
    res['api_calls'] = [(u.split('/')[-1], a) for u, a in calls]
    pg.wait_for_timeout(1500)
    res['pro_pane'] = pg.evaluate("()=>document.querySelector('.pane-on')&&document.querySelector('.pane-on').id")
    shot(pg, 'pro_toast')
    # Pro user scans: unlimited, detailed measurements, plan, checklist, progress
    go(pg, 'analysis')
    scan(pg, 'front', IMG_F)
    pg.evaluate("()=>{document.querySelector('#hostFront .remove').click()}"); pg.wait_for_timeout(300)
    scan(pg, 'front', IMG_F)
    res['pro_second_ok'] = pg.evaluate("()=>document.querySelector('#hostFront .used').hidden && !!document.querySelector('#hostFront .mx-sec')")
    scan(pg, 'profile', IMG_P)
    res['pro_upsell'] = pg.evaluate("()=>{var u=document.querySelector('#hostFront .upsell');return {pro:u.classList.contains('is-pro'),btn:u.querySelector('.ups-btn').textContent,h:u.querySelector('h4 span').textContent,lockVisible:[...u.querySelectorAll('.lk')].some(x=>x.getBoundingClientRect().width>0),lkHow:!!document.querySelector('#hostFront .lk-how')}}")
    pg.evaluate("()=>document.querySelector('#hostFront .ups-btn').click()"); pg.wait_for_timeout(700)
    res['pro_upsell_goes'] = pg.evaluate("()=>document.querySelector('.pane-on').id + ' modal:' + !!document.querySelector('.pr-card')")
    go(pg, 'analysis'); pg.click('[data-mode=front]'); pg.wait_for_timeout(300)
    pg.locator('#hostFront .upsell').screenshot(path=f'{out}/{mode}_pro_upsell.png')
    res['pro_hist'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_hist_tst')||'[]').map(x=>x.k+':'+x.p)")
    go(pg, 'guides')
    pg.evaluate("()=>document.querySelector('.gt [data-gt=plan]').click()"); pg.wait_for_timeout(300)
    res['pro_plan'] = pg.evaluate("""()=>({cards:[...document.querySelectorAll('#mp details.mp-row.zone')].map(c=>[c.querySelector('summary').textContent,(c.querySelector('.mp-val')||{}).textContent,c.querySelectorAll('.mp-act li').length,c.querySelectorAll('.mp-g').length]),
      str:[...document.querySelectorAll('#mp .mp-chip')].map(x=>x.textContent), p30:document.querySelectorAll('#mp .p30-i').length, p30h:(document.querySelector('.p30-hd span')||{}).textContent,
      chart:document.querySelectorAll('#pg .pg-pt').length, tab:document.querySelector('#plan').getAttribute('data-gt'), sum:[...document.querySelectorAll('#pg .pg-c')].map(x=>x.textContent), firstGuide:(document.querySelector('.pl-card h3')||{}).textContent})""")
    pg.evaluate("()=>{var c=document.querySelector('#mp .p30-i input'); c.click();}"); pg.wait_for_timeout(300)
    res['p30_saved'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_p30_tst')).done")
    res['p30_after'] = pg.evaluate("()=>(document.querySelector('.p30-hd span')||{}).textContent")
    shot(pg, 'pro_plan', '#mp')
    pg.evaluate("()=>document.querySelector('.gt [data-gt=prog]').click()"); pg.wait_for_timeout(300); shot(pg, 'pro_progress', '#pg')
    pg.evaluate("()=>document.querySelector('.gt [data-gt=plan]').click()"); pg.wait_for_timeout(300)
    pg.evaluate("()=>{var d=document.querySelector('#mp details.mp-row.zone'); if(d) d.open=true; var b=document.querySelector('#mp .mp-g'); b&&b.click();}"); pg.wait_for_timeout(700)
    res['guide_opens'] = pg.evaluate("()=>{var r=document.querySelector('.rd'); return !!r && !r.hidden && r.querySelector('h1').textContent}")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    # Pro window and account page
    go(pg, 'pro')
    pg.evaluate("()=>{var e=document.querySelector('[data-plan=pro]'); e&&e.click();}"); pg.wait_for_timeout(600)
    res['pro_pricing'] = pg.evaluate("()=>({h:document.querySelector('.pr-card h3').textContent, t:(document.querySelector('.pr-card .pr-trial')||{}).textContent, manage:!!document.querySelector('.pr-card .pr-free')})")
    shot(pg, 'pro_pricing')
    pg.evaluate("()=>document.querySelector('.pr-x').click()"); pg.wait_for_timeout(300)
    go(pg, 'account')
    res['pro_account'] = pg.evaluate("()=>({pl:document.querySelector('.ac-pl').textContent, up:document.querySelector('.ac-up').textContent, rows:[...document.querySelectorAll('.ac-rows li b')].map(x=>x.textContent)})")
    shot(pg, 'pro_account', '#acct')
    pg.evaluate("()=>document.querySelector('.ac-up').click()"); pg.wait_for_timeout(1200)
    res['portal_nav'] = pg.evaluate("()=>location.hash")
    res['cloud_writes'] = pg.evaluate("()=>window.__fbset.map(d=>Object.keys(d).filter(k=>k!=='upd').join(','))")
    # language switch keeps everything working
    pg.evaluate("()=>{var e=[...document.querySelectorAll('[data-lang]')].find(x=>x.getAttribute('data-lang')==='en'); e&&e.click();}"); pg.wait_for_timeout(500)
    go(pg, 'guides')
    res['en_plan_h'] = pg.evaluate("()=>(document.querySelector('#mp h3')||{}).textContent")
    ctx.close()
    b.close()
for k, v in res.items(): print(k, '=>', json.dumps(v, ensure_ascii=False))
print('errors', errs[:10])
srv.shutdown()
