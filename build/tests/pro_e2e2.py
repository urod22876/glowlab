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
    # ---------- free user ----------
    ctx, pg = page(b, False)
    pg.goto(URL, wait_until='domcontentloaded'); pg.wait_for_timeout(2500)
    scan(pg, 'front', IMG_F, close=False)
    res['modal'] = pg.evaluate("()=>{var b=document.querySelector('.rm-box');var r=b.getBoundingClientRect();return {fit:getComputedStyle(b).getPropertyValue('--fit'),h:Math.round(r.height),vh:innerHeight,top:Math.round(r.top),w:Math.round(r.width)}}")
    y0 = pg.evaluate("()=>scrollY"); pg.mouse.wheel(0, 700); pg.wait_for_timeout(300)
    res['modal_no_scroll'] = pg.evaluate("y=>scrollY===y && Math.round(document.querySelector('.rm-box').getBoundingClientRect().top)", y0)
    shot(pg, 'free_modal')
    pg.evaluate("()=>document.querySelector('.rm .rm-x').click()"); pg.wait_for_timeout(700)
    res['modal_closed'] = pg.evaluate("()=>!document.querySelector('.rm') && !document.body.classList.contains('rm-open')")
    res['free_results'] = pg.evaluate("""()=>({fc:!!document.querySelector('#hostFront .fc'), table_hidden:document.querySelector('#hostFront .lk-all').hidden, fold:!!document.querySelector('#hostFront .rt-fold'),
      locked:!!document.querySelector('#hostFront .mx .lk'), upsell:document.querySelector('#hostFront .ups-btn').textContent})""")
    shot(pg, 'free_results', '#hostFront .results')
    go(pg, 'guides')
    res['free_plan'] = pg.evaluate("""()=>({tab:document.querySelector('#plan').getAttribute('data-gt'), rows:[...document.querySelectorAll('#mp details.mp-row summary')].map(s=>s.textContent.trim().slice(0,60)), lock:!!document.querySelector('#mp .mp-lock'),
      guidesHidden:getComputedStyle(document.querySelector('.pl-wrap')).display==='none'})""")
    pg.evaluate("()=>{var d=document.querySelector('#mp details.mp-row'); if(d) d.open=true;}"); pg.wait_for_timeout(200)
    res['free_row_locked'] = pg.evaluate("()=>!!document.querySelector('#mp details.mp-row[open] .mp-lk')")
    shot(pg, 'free_plan', '#mp')
    tab(pg, 'guides'); res['free_guides_tab'] = pg.evaluate("()=>[getComputedStyle(document.querySelector('.pl-wrap')).display, getComputedStyle(document.querySelector('.mp-wrap')).display]")
    ctx.close()

    # ---------- Pro user ----------
    ctx, pg = page(b, True)
    asst = []
    pg.route('**/.netlify/functions/assistant', lambda r: (asst.append(r.request.headers.get('authorization')), r.fulfill(status=200, content_type='application/json', body=json.dumps({'reply': 'Ответ ИИ: **да**'}))))
    pg.goto(URL, wait_until='domcontentloaded'); pg.wait_for_timeout(3000)
    res['pro_on'] = pg.evaluate("()=>document.querySelector('.ac-pl').textContent")
    scan(pg, 'front', IMG_F)
    res['pro_results'] = pg.evaluate("""()=>({rows:document.querySelectorAll('#hostFront .pr-row').length, first:(document.querySelector('#hostFront .pr-row .pr-p')||{}).textContent,
      table_visible:!document.querySelector('#hostFront .lk-all').hidden, mxFolded:document.querySelector('#hostFront .mx').classList.contains('mx-fold') && !document.querySelector('#hostFront .mx').classList.contains('open'),
      mxHead:document.querySelector('#hostFront .mx-h').textContent, mxBodyHidden:getComputedStyle(document.querySelector('#hostFront .mx-body')).display==='none', noLm:!/Ориентир|#33/.test(document.querySelector('#hostFront .mx-body').textContent)})""")
    pg.evaluate("()=>document.querySelector('#hostFront .mx-h').click()"); pg.wait_for_timeout(200)
    res['mx_opens'] = pg.evaluate("()=>getComputedStyle(document.querySelector('#hostFront .mx-body')).display!=='none'")
    pg.evaluate("()=>document.querySelector('#hostFront .mx-h').click()")
    shot(pg, 'pro_results', '#hostFront .results')
    # whose face: create "Аня" for this scan
    res['fc_before'] = pg.evaluate("()=>[...document.querySelectorAll('#hostFront .fc-chip')].map(x=>x.textContent+(x.classList.contains('on')?'*':''))")
    pg.evaluate("()=>[...document.querySelectorAll('#hostFront .fc-chip')].find(x=>x.classList.contains('add')).click()"); pg.wait_for_timeout(200)
    pg.fill('#hostFront .fc-new input', 'Аня'); pg.evaluate("()=>document.querySelector('#hostFront .fc-new button[type=submit]').click()"); pg.wait_for_timeout(500)
    res['fc_after'] = pg.evaluate("()=>[...document.querySelectorAll('#hostFront .fc-chip')].map(x=>x.textContent+(x.classList.contains('on')?'*':''))")
    shot(pg, 'pro_fc', '#hostFront .fc')
    scan(pg, 'front', IMG_F2)   # second scan goes to the selected face (Аня)
    scan(pg, 'profile', IMG_P)
    res['hist'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_hist_tst')).map(x=>x.k+':'+x.f.slice(0,1)+':'+x.p+':'+(x.sh||'-')+':'+(x.sd?x.sd.k:'-'))")
    res['faces'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_faces_tst')).map(f=>f.id.slice(0,1)+':'+(f.n||'')+':'+(f.th?'th':'-'))")
    go(pg, 'guides'); tab(pg, 'plan')
    res['pro_plan'] = pg.evaluate("""()=>({bar:[...document.querySelectorAll('#mp .fb-i')].map(x=>x.textContent+(x.classList.contains('on')?'*':'')), h:document.querySelector('#mp h3').textContent,
      sc:[...document.querySelectorAll('#mp .mp-sc-i')].map(x=>x.textContent), rows:[...document.querySelectorAll('#mp details.mp-row summary')].map(s=>s.textContent.trim().slice(0,70)),
      rep:!!document.querySelector('#mp .mp-rep'), weeks:document.querySelectorAll('#mp .p30 details').length, openWeeks:document.querySelectorAll('#mp .p30 details[open]').length})""")
    pg.evaluate("()=>document.querySelectorAll('#mp details.mp-row').forEach((d,i)=>{if(i<3)d.open=true})"); pg.wait_for_timeout(300)
    res['pro_rows_open'] = pg.evaluate("()=>[...document.querySelectorAll('#mp details.mp-row[open] .fx-b')].map(b=>b.textContent.slice(0,90))")
    shot(pg, 'pro_plan', '#mp')
    with pg.expect_download(timeout=15000) as dl:
        pg.evaluate("()=>document.querySelector('#mp .mp-rep').click()")
    d = dl.value; d.save_as(f'{out}/{mode}_report.png'); res['report'] = d.suggested_filename
    # switch to "me"
    pg.evaluate("()=>[...document.querySelectorAll('#mp .fb-i')][0].click()"); pg.wait_for_timeout(400)
    res['pro_plan_me'] = pg.evaluate("()=>({h:document.querySelector('#mp h3').textContent, sc:[...document.querySelectorAll('#mp .mp-sc-i')].map(x=>x.textContent)})")
    pg.evaluate("()=>[...document.querySelectorAll('#mp .fb-i')][1].click()"); pg.wait_for_timeout(300)
    tab(pg, 'prog'); pg.wait_for_timeout(800)
    res['pro_prog'] = pg.evaluate("""()=>({sum:[...document.querySelectorAll('#pg .pg-c')].map(x=>x.textContent), chart:document.querySelectorAll('#pg .pg-pt').length, ba:!!document.querySelector('#pg .ba-v'),
      baImgs:[...document.querySelectorAll('#pg .ba-v img')].map(i=>i.src.slice(0,22)), all:(document.querySelector('#pg .pg-all summary')||{}).textContent})""")
    shot(pg, 'pro_prog', '#pg')
    # account settings + avatar
    go(pg, 'account')
    res['settings'] = pg.evaluate("()=>({h:(document.querySelector('.ac-set h3')||{}).textContent, sw:document.querySelectorAll('.ac-set .sw').length, faces:[...document.querySelectorAll('.set-face input')].map(i=>i.value)})")
    pg.evaluate("()=>document.querySelectorAll('.ac-set .sw')[2].click()"); pg.wait_for_timeout(200)
    res['acc'] = pg.evaluate("()=>getComputedStyle(document.documentElement).getPropertyValue('--acc').trim()")
    pg.evaluate("()=>{var i=[...document.querySelectorAll('.set-face input')][1]; i.value='Анна'; i.dispatchEvent(new Event('change'));}"); pg.wait_for_timeout(200)
    res['renamed'] = pg.evaluate("()=>JSON.parse(localStorage.getItem('gl_faces_tst'))[1].n")
    shot(pg, 'pro_settings', '.ac-set')
    pg.evaluate("()=>{var a=document.querySelector('.acct'); a&&a.click();}"); pg.wait_for_timeout(300)
    pg.evaluate("()=>{var a=document.querySelector('.am-prof'); a&&a.click();}"); pg.wait_for_timeout(500)
    pg.locator('.pf-card input[type=file]').set_input_files(IMG_F); pg.wait_for_timeout(1200)
    res['cloud_keys'] = pg.evaluate("()=>[...new Set(window.__fbset.flatMap(d=>Object.keys(d)).filter(k=>k!=='upd'))]")
    res['av_synced'] = pg.evaluate("()=>window.__fbset.some(d=>typeof d.av==='string'&&d.av.indexOf('data:image/jpeg')===0)")
    pg.keyboard.press('Escape'); pg.evaluate("()=>document.querySelectorAll('.gm-x').forEach(x=>x.click())"); pg.wait_for_timeout(300)
    # assistant sends the sign-in
    pg.evaluate("()=>document.querySelector('.as-fab').click()"); pg.wait_for_timeout(500)
    pg.fill('.as-panel input', 'Как стать увереннее?'); pg.evaluate("()=>document.querySelector('.as-form button').click()"); pg.wait_for_timeout(1500)
    res['assistant'] = {'auth': asst[:1], 'reply': pg.evaluate("()=>[...document.querySelectorAll('.as-m.b .as-b')].pop().textContent"), 'sub': pg.evaluate("()=>document.querySelector('.as-ht span').textContent")}
    ctx.close()

    # ---------- another device: avatar, faces and history come from the account ----------
    cloud = {'av': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k=',
             'faces': [{'id': 'me', 'n': ''}, {'id': 'fx', 'n': 'Друг'}], 'hist': [{'t': 1792000000000, 'k': 'front', 'f': 'fx', 'p': 4.2, 's': 61}], 'prof': {'done': True, 'name': 'Idris', 'sex': 'm', 'dob': '2000-01-01'}}
    ctx, pg = page(b, True, cloud)
    pg.add_init_script("try{localStorage.removeItem('gl_av_tst');localStorage.removeItem('gl_hist_tst');localStorage.removeItem('gl_faces_tst');}catch(e){}")
    pg.goto(URL, wait_until='domcontentloaded'); pg.wait_for_timeout(4000)
    res['device2'] = pg.evaluate("()=>({av:(localStorage.getItem('gl_av_tst')||'').slice(0,15), faces:JSON.parse(localStorage.getItem('gl_faces_tst')||'[]').map(f=>f.n), hist:JSON.parse(localStorage.getItem('gl_hist_tst')||'[]').length, img:!!document.querySelector('.acct .acct-av img')})")
    ctx.close()
    b.close()
for k, v in res.items(): print(k, '=>', json.dumps(v, ensure_ascii=False))
print('errors', [e for e in errs if 'XNNPACK' not in e][:10])
srv.shutdown()
