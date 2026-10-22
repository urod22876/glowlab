# python3 mx_shot.py <site> <out> [phone|desk] [pro|free]: result + detailed measurements screenshots
import sys, threading, http.server, functools, socketserver, os
from playwright.sync_api import sync_playwright
site, out = sys.argv[1], sys.argv[2]; mode = sys.argv[3] if len(sys.argv) > 3 else 'phone'; plan = sys.argv[4] if len(sys.argv) > 4 else 'pro'
os.makedirs(out, exist_ok=True)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site); H.func.log_message = lambda *a: None
class Q(socketserver.ThreadingTCPServer): allow_reuse_address = True
srv = Q(('127.0.0.1', 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
VP = {'phone': ({'width': 390, 'height': 844}, True), 'small': ({'width': 360, 'height': 600}, True), 'desk': ({'width': 1280, 'height': 900}, False), 'lowdesk': ({'width': 1366, 'height': 620}, False)}[mode]
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_front.jpg')
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    ctx = b.new_context(viewport=VP[0], is_mobile=VP[1], has_touch=VP[1])
    ctx.add_init_script("try{localStorage.setItem('gl_dev','1');" + ("localStorage.setItem('gl_dev_pro','1');" if plan == 'pro' else '') + "localStorage.setItem('gl_lang','ru');localStorage.setItem('gl_age18','1');localStorage.setItem('gl_user',JSON.stringify({n:'Idris',e:'t@t.t',u:'tst'}));localStorage.setItem('gl_prof_tst',JSON.stringify({done:true,name:'Idris',sex:'m',dob:'2000-01-01',bother:['bt_3']}));}catch(e){}")
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.route(lambda u: not u.startswith('http://127.0.0.1'), lambda r: r.abort())
    pg.goto(f'http://127.0.0.1:{port}/', wait_until='domcontentloaded'); pg.wait_for_timeout(2500)
    pg.locator('#hostFront .f-up').set_input_files(IMG)
    pg.wait_for_function("()=>{var c=document.querySelector('#hostFront .psl-card');return c&&!c.hidden&&(c.classList.contains('play')||c.classList.contains('done'))}", timeout=120000)
    pg.wait_for_timeout(2500); pg.screenshot(path=f'{out}/{mode}_{plan}_modal.png'); print('fit', pg.evaluate("()=>{var b=document.querySelector('.rm-box').getBoundingClientRect();return [getComputedStyle(document.querySelector('.rm-box')).getPropertyValue('--fit'),Math.round(b.top),Math.round(b.bottom),innerHeight]}"))
    pg.mouse.wheel(0, 600); pg.wait_for_timeout(400); pg.screenshot(path=f'{out}/{mode}_{plan}_modal_wheel.png')
    pg.evaluate("()=>{var x=document.querySelector('.rm .rm-x'); if(x) x.click();}"); pg.wait_for_timeout(900)
    pg.evaluate("()=>{document.querySelectorAll('#hostFront .mx details').forEach((d,i)=>{if(i<2)d.open=true})}"); pg.wait_for_timeout(300)
    for sel, name in [('#hostFront .results', 'results')]:
        pg.locator(sel).first.screenshot(path=f'{out}/{mode}_{plan}_{name}.png')
    print('errors', errs[:5])
    b.close()
srv.shutdown()
