# usage: python3 pro_e2e2.py <site_dir> <out_dir> [phone|desk]
# v2 features: fixed result window, plain results, faces, guide tabs, compact plan, shape/side, before/after, report,
# settings + avatar sync, general assistant. Fake Firebase + fake /api/pro, /api/assistant.
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
T = os.path.dirname(os.path.abspath(__file__))
IMG_F, IMG_F2, IMG_P = os.path.join(T, 'sample_front.jpg'), os.path.join(T, 'sample_front.jpg'), os.path.join(T, 'sample_profile.jpg')
BASE = "localStorage.setItem('gl_lang','ru');localStorage.setItem('gl_age18','1');localStorage.setItem('gl_user',JSON.stringify({n:'Idris',e:'t@t.t',u:'tst'}));localStorage.setItem('gl_prof_tst',JSON.stringify({done:true,name:'Idris',sex:'m',dob:'2000-01-01',bother:['bt_3']}));"
FB = """window.__fbset=[];window.firebase={apps:[],initializeApp:function(){return{}},app:function(){return{}},
auth:Object.assign(function(){return window.__auth||(window.__auth={languageCode:'ru',currentUser:{uid:'tst',email:'t@t.t',displayName:'Idris',photoURL:'',getIdToken:function(){return Promise.resolve('TOKEN')},updateProfile:function(){return Promise.resolve()}},
 onAuthStateChanged:function(cb){var s=this;setTimeout(function(){cb(s.currentUser)},60)},signOut:function(){return Promise.resolve()}})},{GoogleAuthProvider:function(){this.setCustomParameters=function(){}}}),
firestore:function(){return{collection:function(){return{doc:function(){return{get:function(){return Promise.resolve({exists:!!window.__cloud,data:function(){return window.__cloud||{}}})},set:function(d){window.__fbset.push(d);return Promise.resolve()}}}}}}}};"""
errs = []; res = {}
def page(b, pro, cloud=None):
    ctx = b.new_context(viewport=VP[0], is_mobile=VP[1], has_touch=VP[1], accept_downloads=True)
    ctx.add_init_script("try{" + BASE + "}catch(e){}" + ("window.__cloud=" + json.dumps(cloud) + ";" if cloud else ""))
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)[:300]))
    pg.on('console', lambda m: errs.append('CONSOLE ' + m.text[:200]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.route(lambda u: not u.startswith('http://127.0.0.1') and 'gstatic.com/firebasejs' not in u, lambda r: r.abort())
    pg.route('https://www.gstatic.com/firebasejs/**', lambda r: r.fulfill(status=200, content_type='application/javascript', body=FB if 'app-compat' in r.request.url else ''))
    pg.route('**/api/pro', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps({'pro': pro, 'until': None, 'renews': True})))
    return ctx, pg
def scan(pg, kind, img, close=True):
    if kind == 'profile': pg.click('[data-mode=profile]')
    else: pg.click('[data-mode=front]')
    host = '#hostFront' if kind == 'front' else '#hostProfile'
    pg.locator(host + ' .f-up').set_input_files([]); pg.locator(host + ' .f-up').set_input_files(img)
    pg.wait_for_function("h=>{var c=document.querySelector(h+' .psl-card');return c&&!c.hidden&&(c.classList.contains('play')||c.classList.contains('done'))}", arg=host, timeout=120000)
    pg.wait_for_timeout(1900)
    if close:
        try: pg.wait_for_selector('.rm.on .rm-x', timeout=6000)
        except Exception: pass
        pg.evaluate("()=>{var x=document.querySelector('.rm .rm-x'); if(x) x.click();}"); pg.wait_for_timeout(700)
        res.setdefault('_modal_left', []).append(pg.evaluate("()=>!!document.querySelector('.rm')"))
def go(pg, pane): pg.evaluate("p=>{var b=document.querySelector('.appbar [data-go='+p+']'); b&&b.click();}", pane); pg.wait_for_timeout(600)
def tab(pg, n): pg.evaluate("n=>{var b=document.querySelector('.gt [data-gt='+n+']'); b&&b.click();}", n); pg.wait_for_timeout(500)
def shot(pg, name, sel=None):
    if sel: pg.locator(sel).first.screenshot(path=f'{out}/{mode}_{name}.png')
    else: pg.screenshot(path=f'{out}/{mode}_{name}.png')

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    ctx, pg = page(b, True)
    asst = []
    def asst_route(r):
        asst.append(json.loads(r.request.post_data or '{}'))
        if len(asst) == 1: r.fulfill(status=502, content_type='application/json', body=json.dumps({'error': 'upstream'}))
        else: r.fulfill(status=200, content_type='application/json', body=json.dumps({'reply': 'Совет ИИ'}))
    pg.route('**/.netlify/functions/assistant', asst_route)
    pg.goto(URL, wait_until='domcontentloaded'); pg.wait_for_timeout(3000)
    scan(pg, 'front', IMG_F)
    scan(pg, 'front', os.path.join(T, 'sample_front.jpg'))
    res['hist'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_hist_tst')).map(x=>x.k+':'+x.f+':'+x.p)")
    go(pg, 'guides'); tab(pg, 'plan')
    res['gain'] = pg.evaluate("()=>({best:(document.querySelector('#mp .mp-best')||{}).textContent, chips:[...document.querySelectorAll('#mp .mp-gain')].map(x=>x.textContent)})")
    pg.evaluate("()=>{var d=document.querySelector('#mp details.mp-row.zone'); if(d) d.open=true;}"); pg.wait_for_timeout(200)
    res['zone_body'] = pg.evaluate("()=>{var d=document.querySelector('#mp details.mp-row.zone[open]'); return d? [(d.querySelector('.mp-gn')||{}).textContent, !!d.querySelector('.mp-g.ai')] : null}")
    # ask AI: first call fails -> honest message, second works and carries the scan context
    pg.evaluate("()=>document.querySelector('#mp .mp-g.ai').click()"); pg.wait_for_timeout(1800)
    res['ai_fail_msg'] = pg.evaluate("()=>[...document.querySelectorAll('.as-m.b .as-b')].pop().textContent")
    pg.evaluate("()=>document.querySelector('#mp .mp-g.ai').click()"); pg.wait_for_timeout(1800)
    res['ai_ok'] = pg.evaluate("()=>[...document.querySelectorAll('.as-m.b .as-b')].pop().textContent")
    res['ai_ctx'] = (asst[-1].get('ctx') or '')[:160] if asst else None
    res['ai_q'] = asst[-1]['messages'][-1]['content'][:90] if asst else None
    pg.evaluate("()=>document.querySelector('.as-x').click()"); pg.wait_for_timeout(300)
    tab(pg, 'prog'); pg.wait_for_timeout(600)
    pg.evaluate("()=>{var d=document.querySelector('#pg details.pg-ch'); if(d) d.open=true;}"); pg.wait_for_timeout(200)
    res['changes'] = pg.evaluate("()=>({sum:(document.querySelector('#pg .pg-ch summary')||{}).textContent, rows:[...document.querySelectorAll('#pg .ch-r')].slice(0,3).map(r=>r.textContent)})")
    shot(pg, 'prog3', '#pg')
    tab(pg, 'plan'); shot(pg, 'plan3', '#mp')
    # settings: faces editing
    go(pg, 'account')
    res['faces_ui'] = pg.evaluate("()=>[...document.querySelectorAll('.set-face')].map(f=>[f.querySelector('input').value, f.querySelector('input').disabled, [...f.querySelectorAll('.set-fa button')].map(b=>b.textContent)])")
    pg.evaluate("()=>{var i=document.querySelector('.set-face input'); i.value='Идрис'; i.dispatchEvent(new Event('change'));}"); pg.wait_for_timeout(300)
    res['me_renamed'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_faces_tst'))[0].n")
    with pg.expect_file_chooser() as fc:
        pg.evaluate("()=>[...document.querySelector('.set-face').querySelectorAll('.set-fa button')][0].click()")
    fc.value.set_files(IMG_F2); pg.wait_for_timeout(800)
    res['me_photo_set'] = pg.evaluate("()=>(JSON.parse(localStorage.getItem('gl_faces_tst'))[0].th||'').slice(0,15)")
    pg.evaluate("()=>{var b=[...document.querySelector('.set-face').querySelectorAll('.set-fa button')].find(x=>/Убрать/.test(x.textContent)); b&&b.click();}"); pg.wait_for_timeout(300)
    res['me_photo_removed'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_faces_tst'))[0].th||null")
    pg.fill('.set-add input', 'Мама'); pg.evaluate("()=>document.querySelector('.set-add button').click()"); pg.wait_for_timeout(300)
    res['face_added'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_faces_tst')).map(f=>f.n)")
    res['ph_count'] = pg.evaluate("()=>document.querySelector('.set-cnt').textContent")
    # delete photos (two taps) -> before/after photos and face pictures gone
    pg.evaluate("()=>{var b=[...document.querySelectorAll('.ac-set .g-link.danger')].find(x=>/фото/.test(x.textContent)); b.click(); b.click();}"); pg.wait_for_timeout(900)
    res['ph_after_delete'] = pg.evaluate("()=>[document.querySelector('.set-cnt').textContent, JSON.parse(localStorage.getItem('gl_faces_tst')).filter(f=>f.th).length]")
    # clear the scans of "me" (two taps)
    pg.evaluate("()=>{var b=[...document.querySelector('.set-face').querySelectorAll('.set-fa button')].find(x=>/Очистить/.test(x.textContent)); b.click(); b.click();}"); pg.wait_for_timeout(500)
    res['me_cleared'] = pg.evaluate("()=>[JSON.parse(localStorage.getItem('gl_hist_tst')).length, JSON.parse(localStorage.getItem('gl_faces_tst'))[0].n]")
    go(pg, 'guides'); tab(pg, 'plan')
    res['plan_after_clear'] = pg.evaluate("()=>(document.querySelector('#mp .mp-empty')||{}).textContent")
    go(pg, 'account'); shot(pg, 'settings3', '.ac-set')
    ctx.close()
    b.close()
for k, v in res.items(): print(k, '=>', json.dumps(v, ensure_ascii=False))
print('errors', [e for e in errs if 'XNNPACK' not in e][:10])
srv.shutdown()
