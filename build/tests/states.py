# usage: python3 states.py <site_dir> <out_dir> [phone|desk]
# Screenshots of overlays and app states: sign-in gate, age gate, onboarding, pricing, profile, assistant, guide reader,
# analysis result, legal page. Prints page errors.
import sys, threading, http.server, functools, socketserver, os
from playwright.sync_api import sync_playwright
site, out = sys.argv[1], sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else 'phone'
os.makedirs(out, exist_ok=True)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site); H.func.log_message = lambda *a: None
class Q(socketserver.ThreadingTCPServer): allow_reuse_address = True
srv = Q(('127.0.0.1', 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{port}/'
VP = {'phone': ({'width': 390, 'height': 844}, True), 'desk': ({'width': 1280, 'height': 860}, False)}[mode]
SIGNED = "localStorage.setItem('gl_user',JSON.stringify({n:'Idris',e:'t@t.t',u:'tst'}));"
PROF = "localStorage.setItem('gl_prof_tst',JSON.stringify({done:true,name:'Idris',sex:'m',dob:'2000-01-01',bother:['bt_3','bt_5','bt_6']}));"
errs = []
def page(b, init):
    ctx = b.new_context(viewport=VP[0], is_mobile=VP[1], has_touch=VP[1])
    ctx.add_init_script("try{localStorage.setItem('gl_lang','ru');" + init + "}catch(e){}")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    return ctx, pg
def shot(pg, name): pg.wait_for_timeout(900); pg.screenshot(path=f'{out}/{mode}_{name}.png')
def click_js(pg, js): pg.evaluate("()=>{" + js + "}")
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    # 1. signed out: click the main CTA -> sign-in gate / age
    ctx, pg = page(b, "localStorage.setItem('gl_age18','1');")
    pg.goto(URL, wait_until='load'); pg.wait_for_timeout(1500)
    click_js(pg, "var e=document.querySelector('.hero [data-signup]'); e&&e.click();")
    pg.wait_for_timeout(1200); shot(pg, 'signin')
    ctx.close()
    # 2. age gate (signed in dev mode, no age yet) -> click upload
    ctx, pg = page(b, "localStorage.setItem('gl_dev','1');" + SIGNED + PROF)
    pg.goto(URL, wait_until='load'); pg.wait_for_timeout(1500)
    click_js(pg, "var e=document.querySelector('#demo .up'); if(!e) e=document.querySelector('#demo [class*=drop]'); e&&e.click();")
    pg.wait_for_timeout(800); shot(pg, 'age')
    ctx.close()
    # 3. onboarding: signed in without a saved profile
    ctx, pg = page(b, "localStorage.setItem('gl_dev','1');localStorage.setItem('gl_age18','1');" + SIGNED)
    pg.goto(URL, wait_until='load'); pg.wait_for_timeout(2500); shot(pg, 'onboarding')
    ctx.close()
    ctx, pg = page(b, "localStorage.setItem('gl_dev','1');localStorage.setItem('gl_age18','1');" + SIGNED + PROF)
    pg.goto(URL, wait_until='load'); pg.wait_for_timeout(2000)
    click_js(pg, "var e=document.querySelector('.pz-edit'); e&&e.click();"); pg.wait_for_timeout(900); shot(pg, 'wizard')
    click_js(pg, "var e=[...document.querySelectorAll('.wz-opt')][0]; e&&e.click();"); pg.wait_for_timeout(500); shot(pg, 'wizard2')
    ctx.close()
    # 4. app view signed in with profile: pricing, profile, assistant, guide reader
    ctx, pg = page(b, "localStorage.setItem('gl_dev','1');localStorage.setItem('gl_age18','1');" + SIGNED + PROF)
    pg.goto(URL, wait_until='load'); pg.wait_for_timeout(2000); shot(pg, 'app_home')
    click_js(pg, "var e=document.querySelector('[data-plan=pro]'); e&&e.click();"); pg.wait_for_timeout(600); shot(pg, 'pricing')
    pg.keyboard.press('Escape'); click_js(pg, "document.querySelectorAll('.gm .gm-x, .gm [class*=close]').forEach(x=>x.click());"); pg.wait_for_timeout(400)
    click_js(pg, "var a=document.querySelector('.acct'); a&&a.click();"); pg.wait_for_timeout(400); shot(pg, 'acctmenu')
    click_js(pg, "var a=document.querySelector('.am-prof'); a&&a.click();"); pg.wait_for_timeout(600); shot(pg, 'profile')
    pg.keyboard.press('Escape'); click_js(pg, "document.querySelectorAll('.gm-x').forEach(x=>x.click());"); pg.wait_for_timeout(400)
    click_js(pg, "var a=document.querySelector('.as-fab'); a&&a.click();"); pg.wait_for_timeout(900); shot(pg, 'assistant')
    click_js(pg, "var a=document.querySelector('.as-fab'); a&&a.click(); document.querySelectorAll('.as-x,.as-close').forEach(x=>x.click());"); pg.wait_for_timeout(400)
    click_js(pg, "var b=document.querySelector('[data-go=guides]'); b&&b.click();"); pg.wait_for_timeout(1500); shot(pg, 'guides')
    click_js(pg, "var c=document.querySelector('.pl-card'); c&&c.click();"); pg.wait_for_timeout(1200); shot(pg, 'reader')
    ctx.close()
    # 5. legal page
    ctx, pg = page(b, "")
    pg.goto(URL + 'terms.html', wait_until='load'); pg.wait_for_timeout(800); shot(pg, 'terms')
    ctx.close()
    b.close()
print('errors', errs[:8])
srv.shutdown()
