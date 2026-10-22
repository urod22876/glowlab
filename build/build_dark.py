# Build the dark site: python3 -I build_dark.py <src_dir> <dst_dir>
# 1) hero restructure (text + photo with measurement lines), 2) palette conversion, 3) fonts, 4) manual dark layer
import sys, os, shutil, re, importlib.util
src, dst = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(src, dst)
spec = importlib.util.spec_from_file_location('darkify', os.path.join(here, 'darkify.py')); dk = importlib.util.module_from_spec(spec); spec.loader.exec_module(dk)
layer = open(os.path.join(here, 'dark_layer.css'), encoding='utf-8').read()
legal_layer = open(os.path.join(here, 'dark_legal.css'), encoding='utf-8').read() if os.path.exists(os.path.join(here, 'dark_legal.css')) else ''

def one(s, old, new):
    n = s.count(old); assert n == 1, (n, old[:80]); return s.replace(old, new)

def style_blocks(s, fn):
    out, pos = [], 0
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', s, re.S):
        out.append(s[pos:m.start(1)]); out.append(fn(m.group(1))); pos = m.end(1)
    out.append(s[pos:]); return ''.join(out)

def fonts(css):
    return css.replace("'Playfair Display','Times New Roman',Georgia,serif", "'Manrope',system-ui,sans-serif").replace("'Playfair Display'", "Manrope").replace("Manrope,serif", "Manrope,system-ui,sans-serif")

# ---------- index.html ----------
p = os.path.join(dst, 'index.html'); s = open(p, encoding='utf-8').read()
# hero: move the measurement figure into the hero, keep the showcase text as its own block
i0 = s.index('<section class="hv vland" id="hv" aria-labelledby="hvH">')
f0 = s.index('    <figure class="hv-fig">', i0); f1 = s.index('    </figure>\n', f0) + len('    </figure>\n')
fig = s[f0:f1]
s = s[:f0] + s[f1:]
s = one(s, '<section class="hv vland" id="hv" aria-labelledby="hvH">', '<section class="hv-info vland" aria-labelledby="hvH">')
h0 = s.index('  <section class="hero vland">'); h1 = s.index('  </section>', h0)
hero_inner = s[h0 + len('  <section class="hero vland">'):h1]
s = s[:h0] + '  <section class="hero hv vland" id="hv">\n    <div class="hero-txt">' + hero_inner + '    </div>\n' + fig + s[h1:]
# methods strip: endless moving line (content doubled for a seamless loop)
LOGOS = '<div class="hv-logos"><span>Farkas <i>anthropometry</i></span><span>Golden ratio <i>φ</i></span><span>Neoclassical <i>canons</i></span><span>Facial <i>thirds</i></span><span>Frankfurt <i>plane</i></span></div>'
items = LOGOS[len('<div class="hv-logos">'):-len('</div>')]
dup = items.replace('<span>', '<span aria-hidden="true">')
s = one(s, LOGOS, '<div class="hv-marq"><div class="hv-logos">' + items + dup + '</div></div>')
# measurement overlay: small labels sitting next to the measured points (reference style), no side column
i = s.index('<svg class="hz"'); j = s.index('</svg>', i) + 6
HZ = """<svg class="hz" viewBox="0 0 766 880" aria-hidden="true">
<g class="hz-l"><path pathLength="1" d="M332 468L405 586L592 640" style="--t:0.8s"/><path class="arc" pathLength="1" d="M384 552A40 40 0 0 0 441 597" style="--t:1.9s"/></g>
<g class="hz-l hz-th"><path pathLength="1" d="M470 325H745" style="--t:2.6s"/><path pathLength="1" d="M470 470H745" style="--t:2.8s"/><path pathLength="1" d="M470 640H745" style="--t:3.0s"/><path class="tick" pathLength="1" d="M745 325V640" style="--t:3.1s"/></g>
<g class="hz-l"><path pathLength="1" d="M522 361L568 352" style="--t:3.8s"/></g>
<g class="hz-l"><path pathLength="1" d="M665 440L612 612" style="--t:4.9s"/></g>
<g class="hz-l"><path pathLength="1" d="M470 646L590 642" style="--t:5.9s"/><path pathLength="1" d="M470 646L428 840" style="--t:6.1s"/></g>
<g class="hz-pts"><circle class="hz-d" cx="332" cy="468" r="4" style="--t:1.0s"/><circle class="hz-d" cx="405" cy="586" r="4" style="--t:1.3s"/><circle class="hz-r" cx="405" cy="586" r="5" style="--t:1.3s"/><circle class="hz-d" cx="592" cy="640" r="4" style="--t:1.6s"/><circle class="hz-d" cx="522" cy="361" r="4" style="--t:4.0s"/><circle class="hz-d" cx="568" cy="352" r="4" style="--t:4.1s"/><circle class="hz-r" cx="568" cy="352" r="5" style="--t:4.1s"/><circle class="hz-d" cx="665" cy="440" r="4" style="--t:5.1s"/><circle class="hz-d" cx="612" cy="612" r="4" style="--t:5.2s"/><circle class="hz-r" cx="612" cy="612" r="5" style="--t:5.2s"/><circle class="hz-d" cx="470" cy="646" r="4" style="--t:6.1s"/><circle class="hz-r" cx="470" cy="646" r="5" style="--t:6.1s"/></g>
<g transform="translate(748 284)"><g class="hz-t" style="--t:3.2s"><text class="ti" text-anchor="end" data-i18n="hv_thi"></text><text class="va" y="24" text-anchor="end">1 : 1 : 1</text></g></g>
<g transform="translate(506 340)"><g class="hz-t" style="--t:4.3s"><text class="ti" text-anchor="end" data-i18n="hv_can"></text><text class="va" y="24" text-anchor="end" data-count="5" data-pre="+" data-suf="°" data-at="4.3">+5°</text></g></g>
<g transform="translate(390 604)"><g class="hz-t" style="--t:2.2s"><text class="ti" text-anchor="end" data-i18n="hv_gon"></text><text class="va" y="24" text-anchor="end" data-count="126" data-pre="~" data-suf="°" data-at="2.2">~126°</text></g></g>
<g transform="translate(752 668)"><g class="hz-t" style="--t:5.4s"><text class="ti" text-anchor="end" data-i18n="hv_el"></text><text class="va" y="24" text-anchor="end">−2 mm</text></g></g>
<g transform="translate(418 740)"><g class="hz-t" style="--t:6.6s"><text class="ti" text-anchor="end" data-i18n="hv_nk"></text><text class="va" y="24" text-anchor="end" data-count="104" data-pre="" data-suf="°" data-at="6.6">104°</text></g></g>
</svg>"""
s = s[:i] + HZ + s[j:]
# the sample analysis window under the hero is removed (the user asked); its script stops early without it
w0 = s.index('  <section class="scanwin vland"'); w1 = s.index('  </section>', w0) + len('  </section>\n')
s = s[:w0] + s[w1:]
s = one(s, "var card = $('#scanCard'), tag = $('#scanTag'), rows = $('#ratioRows'), rt = $('#ratiosTitle'), vid = $('#heroVid'), ov = $('#scanOv'), ln = $('#scanLines');",
        "var card = $('#scanCard'), tag = $('#scanTag'), rows = $('#ratioRows'), rt = $('#ratiosTitle'), vid = $('#heroVid'), ov = $('#scanOv'), ln = $('#scanLines');\n    if (!card) return;")
# decorative art recoloured to gold (no CSS invert: it turned the snow peak into a black spot)
import base64 as _b64
ART = os.path.join(here, 'assets')
for k in ('mtn', 'dna', 'cld', 'col'):
    data = _b64.b64encode(open(os.path.join(ART, 'gold_' + k + '.webp'), 'rb').read()).decode()
    m = re.search(r'--img-' + k + r':url\(data:image/webp;base64,[^)]+\)', s)
    s = s[:m.start()] + '--img-' + k + ':url(data:image/webp;base64,' + data + ')' + s[m.end():]
# guide thumbnails replaced with the user's photos (sleep = guide 02, jaw = guide 04, read = guide 06)
for k in ('sleep', 'jaw'):
    data = _b64.b64encode(open(os.path.join(ART, 'new_' + k + '.webp'), 'rb').read()).decode()
    m = re.search(r'--gi-' + k + r':url\(data:image/\w+;base64,[^)]+\)', s)
    s = s[:m.start()] + '--gi-' + k + ':url(data:image/webp;base64,' + data + ')' + s[m.end():]
# guides: guide 5 (photo) and the whole Method tab removed; remaining guides expanded with sourced content
g0 = s.index('var SRC = {'); g1 = s.index('];', s.index('var GUIDES = [')) + 2
s = s[:g0] + open(os.path.join(here, 'guides_new.js'), encoding='utf-8').read().rstrip() + s[g1:]
s = one(s, "pl_sub:'Careful, sourced guides on skin, habits and how to read your scan. Your scan decides what comes first.'", "pl_sub:'Sourced guides on skin, sleep, posture, jaw and grooming. Your scan decides what comes first.'")
s = one(s, "pl_sub:'Аккуратные гиды с источниками о коже, привычках и о том, как читать свой скан. Скан определяет, что показать первым.'", "pl_sub:'Гиды с источниками о коже, сне, осанке, челюсти и уходе. Скан определяет, что показать первым.'")
s = one(s, "tabs: ['All', 'Skin', 'Habits', 'Structure', 'Method']", "tabs: ['All', 'Skin', 'Habits', 'Structure']")
s = one(s, "tabs: ['Все', 'Кожа', 'Привычки', 'Строение', 'Метод']", "tabs: ['Все', 'Кожа', 'Привычки', 'Строение']")
s = one(s, "ctx_areas: 'Your scan flagged: {a}. Start with \"Reading your scan\".'", "ctx_areas: 'Your scan flagged: {a}. The guides below are ordered for you.'")
s = one(s, "ctx_areas: 'В скане отмечено: {a}. Начните с гида «Как читать свой скан».'", "ctx_areas: 'В скане отмечено: {a}. Гиды ниже расставлены под вас.'")
s = one(s, "В разделе «Ваш план» 7 гайдов с источниками: кожа (бесплатный), сон, шея и осанка, челюсть и подбородок, как делать фото, как читать скан и работа со специалистами.", "В разделе «Ваш план» гайды с источниками: кожа (бесплатный), сон, шея и осанка, челюсть и подбородок, уход и работа со специалистами.")
s = one(s, "The “Your plan” section has 7 sourced guides: skin (free), sleep, neck and posture, jaw and chin, how to take the photo, how to read your scan and working with professionals.", "The “Your plan” section has sourced guides: skin (free), sleep, neck and posture, jaw and chin, grooming and working with professionals.")
s = one(s, "rw[1][0] === 'Avoid' ? 'a' : rw[1][0] === 'Recommended' ? 'r' : 'q'", "(rw[1][0] === 'Avoid' || rw[1][0] === 'No evidence') ? 'a' : /^(Recommended|Evidence-based|Measured|Changeable)$/.test(rw[1][0]) ? 'r' : 'q'")
# "why looks matter" block with a photo, right after the methods strip
WHY = _b64.b64encode(open(os.path.join(ART, 'why.webp'), 'rb').read()).decode()
WHYSEC = ('  <section class="why vland" aria-labelledby="whyH">\n'
  '    <figure class="why-fig"><img src="data:image/webp;base64,' + WHY + '" alt="" loading="lazy" decoding="async"></figure>\n'
  '    <div class="why-txt">\n      <p class="eyebrow" data-i18n="why_k"></p>\n      <h2 id="whyH" data-i18n="why_h"></h2>\n'
  '      <p data-i18n="why_p1"></p>\n      <p data-i18n="why_p2"></p>\n'
  '      <div class="why-stats"><div><b>919</b><span data-i18n="why_s1"></span></div><div><b>~5%</b><span data-i18n="why_s2"></span></div></div>\n'
  '      <p data-i18n="why_p3"></p>\n      <a class="btn" data-signup href="#demo"></a>\n'
  '      <p class="why-src" data-i18n="why_src"></p>\n    </div>\n  </section>\n')
k0 = s.index('  <section class="hv-strip vland"'); k1 = s.index('  </section>', k0) + len('  </section>\n')
s = s[:k1] + WHYSEC + s[k1:]
s = one(s, "Object.assign(I18N.en, { pc_k:", """Object.assign(I18N.en, { why_k:'Why it matters', why_h:'Looks matter more than people admit',
  why_p1:'It is common to say that appearance is a matter of taste and changes nothing. The research says otherwise. A meta-analysis of 919 studies found that attractive people are judged and treated more favourably, even by people who know them well.',
  why_p2:'It shows up in money too: people with above-average looks earn more than people with below-average looks, in a classic study across occupations.',
  why_s1:'studies in the meta-analysis', why_s2:'higher pay for above-average looks (Hamermesh and Biddle)',
  why_p3:'The good news: a large part of how others see you is skin, sleep, posture, body fat, haircut and grooming. These change. Glow Lab shows you where to start.',
  why_src:'Sources: Langlois et al. (2000), Psychological Bulletin; Hamermesh and Biddle (1994), American Economic Review.' });
Object.assign(I18N.ru, { why_k:'Почему это важно', why_h:'Внешность важнее, чем принято говорить',
  why_p1:'Принято говорить, что внешность это дело вкуса и ни на что не влияет. Исследования говорят обратное. Метаанализ 919 работ показал: привлекательных людей оценивают лучше и относятся к ним лучше, даже те, кто хорошо их знает.',
  why_p2:'Это видно и в деньгах: в классическом исследовании люди с внешностью выше средней зарабатывали больше, чем люди с внешностью ниже средней, в самых разных профессиях.',
  why_s1:'исследований в метаанализе', why_s2:'выше зарплата при внешности выше средней (Hamermesh и Biddle)',
  why_p3:'Хорошая новость: большая часть того, как вас видят, это кожа, сон, осанка, процент жира, стрижка и уход. Это меняется. Glow Lab показывает, с чего начать.',
  why_src:'Источники: Langlois и соавт. (2000), Psychological Bulletin; Hamermesh и Biddle (1994), American Economic Review.' });
Object.assign(I18N.en, { pc_k:""")
# result as a full-screen pop-up after the analysis (close with the cross, then the page scrolls to the breakdown)
s = one(s, """      if ('IntersectionObserver' in window) {
        pcObs = new IntersectionObserver(function (en) { if (en.some(function (x) { return x.isIntersecting; })) { pcObs.disconnect(); pcObs = null; pcPlay(c); } }, { threshold: 0.35 });
        pcObs.observe(c);
      } else pcPlay(c);
    }""", """      var tok0 = S.token;
      setTimeout(function () {
        if (tok0 !== S.token) return;
        var hiddenNow = c.hidden || c.closest('[hidden]') || (R.results && R.results.classList.contains('gated'));
        if (hiddenNow) { c.classList.add('done'); $$('.pc-n', c).forEach(function (n) { n.textContent = fmt(+n.dataset.v, 1); }); return; }
        pcModal(c);
      }, 1300);
    }
    function pcModal(c) {
      c.classList.add('done'); $$('.pc-n', c).forEach(function (n) { n.textContent = fmt(+n.dataset.v, 1); });
      var old = document.querySelector('.rm'); if (old) old.remove();
      var m = document.createElement('div'); m.className = 'rm'; m.setAttribute('role', 'dialog'); m.setAttribute('aria-modal', 'true');
      var box = h('div', 'rm-box', null, m);
      h('i', 'rm-glow', null, box);
      var x = h('button', 'rm-x', null, box); x.type = 'button'; x.setAttribute('aria-label', t('g_close'));
      x.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
      var cl = c.cloneNode(true); cl.classList.remove('done', 'play'); cl.classList.add('rm-card'); cl.hidden = false; box.appendChild(cl);
      var src = c.querySelector('canvas'), dst = cl.querySelector('canvas'); try { dst.getContext('2d').drawImage(src, 0, 0); } catch (e) {}
      var ph = cl.querySelector('.pc-ph'); if (ph) { ph.insertBefore(h('b', 'rm-ring r0', null, ph), ph.firstChild); h('b', 'rm-ring r1', null, ph); h('b', 'rm-ring r2', null, ph); h('b', 'rm-ring r3', null, ph); }
      var more = cl.querySelector('.pc-more'); if (more) { more.textContent = t('pc_more'); more.addEventListener('click', function () { close(true); }); }
      document.body.appendChild(m); document.body.classList.add('rm-open');
      requestAnimationFrame(function () { m.classList.add('on'); setTimeout(function () { pcPlay(cl); }, 350); });
      function close(go) {
        m.classList.remove('on'); m.classList.add('off'); document.body.classList.remove('rm-open'); document.removeEventListener('keydown', esc);
        setTimeout(function () { m.remove(); }, 380);
        if (go) setTimeout(function () { var r = $('.rating', root) || c; try { r.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {} }, 300);
      }
      function esc(e) { if (e.key === 'Escape') close(false); }
      x.addEventListener('click', function () { close(true); });
      m.addEventListener('click', function (e) { if (e.target === m) close(true); });
      document.addEventListener('keydown', esc);
      try { x.focus({ preventScroll: true }); } catch (e) {}
    }""")
s = one(s, "setTimeout(function () { if (token === S.token) { var rt = $('.psl-card', root); if (!rt || rt.hidden || rt.closest('[hidden]')) rt = $('.rating', root); if (rt && !rt.closest('[hidden]')) try { rt.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {} } }, 1600);", "")
# Pro buttons open the full-screen Pro window; the window leads with $1 for 3 days
s = one(s, "a.addEventListener('click', function (e) { if (!url) { e.preventDefault(); note.hidden = false; note.scrollIntoView({ block: 'center' }); } });",
        "a.addEventListener('click', function (e) { e.preventDefault(); openPricing(); });")
s = one(s, "  function initPay() {\n    var note = $('#payNote');", "  function initPay() {\n    var note = $('#payNote');\n    $$('.used .btn').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); openPricing(); }); });")
s = one(s, "var pr = h('p', 'pr-price', pl.price, pro); h('small', null, ' /' + t('pm_per_' + pl.per), pr);\n    h('p', 'pr-trial', t('pm_trial'), pro);",
        "var pr = h('p', 'pr-price', pl.price, pro); h('small', null, ' / ' + t('pm_per_' + pl.per), pr);\n    h('p', 'pr-trial', t('pm_then', { p: pl.price }), pro);")
s = one(s, "Object.assign(I18N.en, { pc_k:", "Object.assign(I18N.en, { pm_first3:'for 3 days', pm_then:'Billed monthly. Cancel any time, future charges stop.' });\nObject.assign(I18N.ru, { pm_first3:'за 3 дня', pm_then:'Списание раз в месяц. Отменить можно в любой момент, дальше списаний не будет.' });\nObject.assign(I18N.en, { pc_k:")
# pricing cards like the reference: small line icon on top of each plan
IC_FREE = '<span class="plan-ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></span>'
IC_PRO = '<span class="plan-ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z M4 7.5l8 4.5 8-4.5M12 12v9" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg></span>'
s = one(s, '<div class="plan-head"><h3 data-i18n="free_t"></h3></div>', IC_FREE + '<div class="plan-head"><h3 data-i18n="free_t"></h3></div>')
s = one(s, '<div class="plan-head"><h3 data-i18n="pro_t"></h3>', IC_PRO + '<div class="plan-head"><h3 data-i18n="pro_t"></h3>')
# face analysis accuracy: higher working resolution, second pass on a crop around a small face, head turn from the 3D mesh
s = one(s, "var w = im.naturalWidth, hh = im.naturalHeight, s = Math.min(1, 1280 / Math.max(w, hh));", "var w = im.naturalWidth, hh = im.naturalHeight, s = Math.min(1, 1920 / Math.max(w, hh));")
s = one(s, """      var r = E.lm.detect(canvas);
      if (!r || !r.faceLandmarks || !r.faceLandmarks.length) return { engine: true, lm: null };
      return { engine: true, lm: r.faceLandmarks[0].map(function (p) { return { x: p.x, y: p.y, z: p.z }; }) };""",
"""      var r = E.lm.detect(canvas), lm = null;
      if (r && r.faceLandmarks && r.faceLandmarks.length) lm = r.faceLandmarks[0].map(function (p) { return { x: p.x, y: p.y, z: p.z }; });
      /* no face on the full frame (face too small or far away): search overlapping crops, centre first */
      if (!lm) {
        var CW = canvas.width, CH = canvas.height, regs = [[.2, .1, .6, .6], [.25, 0, .5, .5], [.25, .25, .5, .5], [0, 0, .5, .5], [.5, 0, .5, .5], [0, .3, .5, .5], [.5, .3, .5, .5], [.15, .4, .7, .6]], q;
        for (q = 0; q < regs.length && !lm; q++) {
          var rg = regs[q], rx = Math.round(rg[0] * CW), ry = Math.round(rg[1] * CH), rw = Math.round(rg[2] * CW), rh = Math.round(rg[3] * CH);
          var sc = Math.min(2.5, 1024 / Math.max(rw, rh)), cc = document.createElement('canvas'); cc.width = Math.round(rw * sc); cc.height = Math.round(rh * sc);
          var gc = cc.getContext('2d'); gc.imageSmoothingQuality = 'high'; gc.drawImage(canvas, rx, ry, rw, rh, 0, 0, cc.width, cc.height);
          var rr = E.lm.detect(cc);
          if (rr && rr.faceLandmarks && rr.faceLandmarks.length) lm = rr.faceLandmarks[0].map(function (p) { return { x: (rx + p.x * rw) / CW, y: (ry + p.y * rh) / CH, z: p.z * rw / CW }; });
        }
      }
      if (!lm) return { engine: true, lm: null };
      /* second pass: when the face is small in the frame, crop around it and run the landmarker again on the enlarged face,
         then map the points back. Small faces otherwise get few pixels per landmark. */
      try {
        var W = canvas.width, H = canvas.height, x0 = 1, y0 = 1, x1 = 0, y1 = 0;
        lm.forEach(function (p) { if (p.x < x0) x0 = p.x; if (p.x > x1) x1 = p.x; if (p.y < y0) y0 = p.y; if (p.y > y1) y1 = p.y; });
        var bw = (x1 - x0) * W, bh = (y1 - y0) * H;
        if (Math.max(bw, bh) < 0.5 * Math.min(W, H)) {
          var side = Math.min(Math.max(W, H), Math.round(Math.max(bw, bh) * 1.9)), cx = (x0 + x1) / 2 * W, cy = (y0 + y1) / 2 * H;
          var sx = Math.max(0, Math.min(W - side, Math.round(cx - side / 2))), sy = Math.max(0, Math.min(H - side, Math.round(cy - side / 2)));
          var sw = Math.min(side, W), sh = Math.min(side, H), out = Math.min(1024, Math.max(512, Math.round(Math.max(sw, sh) * 2)));
          var c2 = document.createElement('canvas'); c2.width = Math.round(out * sw / Math.max(sw, sh)); c2.height = Math.round(out * sh / Math.max(sw, sh));
          var g2 = c2.getContext('2d'); g2.imageSmoothingQuality = 'high'; g2.drawImage(canvas, sx, sy, sw, sh, 0, 0, c2.width, c2.height);
          var r2 = E.lm.detect(c2);
          if (r2 && r2.faceLandmarks && r2.faceLandmarks.length) {
            lm = r2.faceLandmarks[0].map(function (p) { return { x: (sx + p.x * sw) / W, y: (sy + p.y * sh) / H, z: p.z * sw / W }; });
          }
        }
      } catch (e2) {}
      return { engine: true, lm: lm };""")
s = one(s, "quality = GL.frontQuality(S.pn, S.aspect, m, S.light, S.hairEst, S.faces);",
"""quality = GL.frontQuality(S.pn, S.aspect, m, S.light, S.hairEst, S.faces);
          /* head turn from the 3D face mesh: more reliable than left/right landmark balance, which flags natural asymmetry and small faces as a turned head */
          if (S.lm && window.GM) { try { var yw = Math.abs(GM.align(S.lm, S.aspect * 1000, 1000).yawDeg); quality.forEach(function (c) { if (c.id === 'turn') { c.level = yw <= 12 ? 'ok' : yw <= 20 ? 'warn' : 'bad'; c.key = 'c_turn_' + c.level; } }); } catch (e) {} }""")
# photo-guide animations: MP4 video instead of a 6 MB animated WebP (smooth decoding, no dark flashes on phones)
gv0 = s.index('var GUIDE_VIDEO = {'); gv1 = s.index('};', gv0) + 2
def _v(k, ext): return _b64.b64encode(open(os.path.join(ART, 'gv_' + k + '.' + ext), 'rb').read()).decode()
s = s[:gv0] + "var GUIDE_VIDEO = { front: 'data:video/mp4;base64," + _v('front', 'mp4') + "', profile: 'data:video/mp4;base64," + _v('profile', 'mp4') + "' };\n  var GUIDE_WEBM = { front: 'data:video/webm;base64," + _v('front', 'webm') + "', profile: 'data:video/webm;base64," + _v('profile', 'webm') + "' };" + s[gv1:]
s = one(s, """          R.vid = document.createElement('img');
          R.vid.src = GUIDE_VIDEO[kind]; R.vid.alt = t('g_' + kind + '_title'); R.vid.decoding = 'async';""",
"""          R.vid = document.createElement('video');
          R.vid.muted = true; R.vid.defaultMuted = true; R.vid.loop = true; R.vid.autoplay = true; R.vid.playsInline = true; R.vid.preload = 'auto';
          R.vid.setAttribute('muted', ''); R.vid.setAttribute('playsinline', ''); R.vid.setAttribute('aria-label', t('g_' + kind + '_title'));
          var sw1 = document.createElement('source'); sw1.src = GUIDE_WEBM[kind]; sw1.type = 'video/webm'; R.vid.appendChild(sw1); var sw2 = document.createElement('source'); sw2.src = GUIDE_VIDEO[kind]; sw2.type = 'video/mp4'; R.vid.appendChild(sw2); try { var pp = R.vid.play(); if (pp && pp.catch) pp.catch(function () {}); } catch (e) {}""")
# face size: with the crop pass a smaller face is still measurable
s = one(s, "key: cut ? 'c_size_cut' : frac >= 0.38 ? 'c_size_ok' : frac >= 0.25 ? 'c_size_warn' : 'c_size_bad'", "key: cut ? 'c_size_cut' : frac >= 0.3 ? 'c_size_ok' : frac >= 0.16 ? 'c_size_warn' : 'c_size_bad'")
s = one(s, "level: cut ? 'bad' : frac >= 0.38 ? 'ok' : frac >= 0.25 ? 'warn' : 'bad'", "level: cut ? 'bad' : frac >= 0.3 ? 'ok' : frac >= 0.16 ? 'warn' : 'bad'")
# stricter overall harmony: the weakest features pull the score down (a face reads as a whole: one clearly
# off feature is not cancelled out by many average ones), plus two more mesh metrics
s = one(s, """    var avg = ws ? sum / ws : 0;
    return Math.round((4 + 6 * avg) * 10) / 10;""", """    var avg = ws ? sum / ws : 0;
    if (items.length >= 6) {
      var vals = items.map(itemValue).sort(function (p, q) { return p - q; }), k = Math.max(2, Math.round(items.length / 4)), low = 0, i;
      for (i = 0; i < k; i++) low += vals[i];
      avg = 0.7 * avg + 0.3 * (low / k);
    }
    return Math.round((4 + 6 * avg) * 10) / 10;""")
s = one(s, "    if (ok(m.sym_disp)) out.symd = m.sym_disp;", """    if (ok(m.sym_disp)) out.symd = m.sym_disp;
    if (ok(m.nose_icd)) out.nosew = m.nose_icd;
    if (ok(m.ear_r) && ok(m.ear_l) && !f.pose.mouthOpen) out.eyeo = (m.ear_r + m.ear_l) / 2;""")
s = one(s, "    symd: { lo: 0,    hi: 2.2,  ideal: 0,    unit: '%', dec: 1, side: 'front', fall: 3,    w: 1.5 }",
        """    symd: { lo: 0,    hi: 2.2,  ideal: 0,    unit: '%', dec: 1, side: 'front', fall: 3,    w: 1.5 },
    nosew:{ lo: 0.95, hi: 1.3,  ideal: 1.1,  unit: '',  dec: 2, side: 'front', fall: 0.3,  w: 0.8 },
    eyeo: { lo: 0.2,  hi: 0.33, ideal: 0.27, unit: '',  dec: 2, side: 'front', fall: 0.1,  w: 0.7 }""")
s = one(s, "['br_eye', ['tilt', 'eyesp', 'esr']]", "['br_eye', ['tilt', 'eyesp', 'esr', 'eyeo']]")
s = one(s, "['br_harm', ['ratio', 'midf']]", "['br_harm', ['ratio', 'midf', 'nosew']]")
s = one(s, "Object.assign(I18N.en, { pc_k:", """Object.assign(I18N.en, { m_nosew_name:'Nose width', m_nosew_ok:'Nose width fits the eye spacing.', m_nosew_low:'Nose is narrow for the eye spacing.', m_nosew_high:'Nose is wide for the eye spacing.',
  m_eyeo_name:'Eye shape', m_eyeo_ok:'Eye opening is balanced.', m_eyeo_low:'Eyes look narrow or half-closed.', m_eyeo_high:'Eyes look very round or wide open.' });
Object.assign(I18N.ru, { m_nosew_name:'Ширина носа', m_nosew_ok:'Ширина носа подходит к расстоянию между глазами.', m_nosew_low:'Нос узкий относительно расстояния между глазами.', m_nosew_high:'Нос широкий относительно расстояния между глазами.',
  m_eyeo_name:'Форма глаз', m_eyeo_ok:'Раскрытие глаз сбалансировано.', m_eyeo_low:'Глаза выглядят узкими или прищуренными.', m_eyeo_high:'Глаза очень круглые или широко раскрыты.' });
Object.assign(I18N.en, { pc_k:""")
s = one(s, "var PSL_MAP = [[0, 0.5], [0.3, 1.5], [0.45, 2.6], [0.6, 3.5], [0.72, 4.3], [0.82, 5.1], [0.9, 5.9], [0.95, 6.5], [1, 7.5]];",
        "var PSL_MAP = [[0, 0.5], [0.3, 2.0], [0.45, 2.8], [0.6, 3.5], [0.72, 4.4], [0.82, 5.4], [0.9, 6.1], [0.95, 6.6], [1, 7.5]];")
# Dodo Payments checkout (TEST mode product). Replace with the live product link before going live.
s = one(s, "var LINKS = { pro: '' };", "var LINKS = { pro: 'https://test.checkout.dodopayments.com/buy/pdt_0NqA6l5LZVzhNuAMj4FdI?quantity=1&redirect_url=' + encodeURIComponent('https://glow-lub.com/?checkout=done') };")
s = one(s, "    if (!url) return;\n    if (window.GL_CHECKOUT)", "    if (!url) return;\n    try { var ai = Auth.info(); if (ai && ai.e) url += '&email=' + encodeURIComponent(ai.e); if (ai && ai.u) url += '&metadata_uid=' + encodeURIComponent(ai.u); } catch (e) {}\n    if (window.GL_CHECKOUT)")
s = style_blocks(s, lambda css: fonts(dk.conv_css(css)))
s = one(s, '</style>', layer + '</style>') if s.count('</style>') == 1 else s.replace('</style>', layer + '</style>', 1)
# monochrome pass: the gold/amber accent and warm neutrals become pure black, greys and white light (reference look)
import colorsys as _cs
def _mono_col(m):
    p = dk.parse(m.group(0))
    if not p: return m.group(0)
    r, g, bb, al = p; hh, ll, ss = _cs.rgb_to_hls(r, g, bb); hue = hh * 360
    if not (12 <= hue <= 62): return m.group(0)
    if ss > .3 and ll > .35: ll = max(ll, .82)       # gold highlight -> soft white
    return dk.fmt(ll, ll, ll, al)
def mono(css):
    keep = []
    def k(mm): keep.append(mm.group(0)); return '\x01%d\x01' % (len(keep) - 1)
    css = re.sub(r'url\((?:[^()]|\([^()]*\))*\)', k, css)
    css = dk.COL.sub(_mono_col, css)
    return re.sub(r'\x01(\d+)\x01', lambda mm: keep[int(mm.group(1))], css)
s = style_blocks(s, mono)
# pricing without a trial: $9.99 per month from the first payment
NOTRIAL = [
 ("pm_badge:'3-day trial'", "pm_badge:'Monthly'"), ("pm_badge:'Пробные 3 дня'", "pm_badge:'Помесячно'"),
 ("pm_trial:'Start with 3 days for $1, then $9.99 per month.'", "pm_trial:'$9.99 per month. Cancel any time.'"),
 ("pm_trial:'Начните с 3 дней за $1, затем $9,99 в месяц.'", "pm_trial:'$9,99 в месяц. Отмена в любой момент.'"),
 ("pm_go:'Start trial for $1'", "pm_go:'Get Pro · $9.99/month'"), ("pm_go:'Начать пробный период за $1'", "pm_go:'Оформить Pro · $9.99/мес'"),
 ("pm_fine:'Secure checkout. Cancel any time, including during the trial.'", "pm_fine:'Secure checkout via Dodo Payments. Cancel any time.'"),
 ("pm_fine:'Безопасная оплата. Отмена в любой момент, в том числе во время пробного периода.'", "pm_fine:'Безопасная оплата через Dodo Payments. Отмена в любой момент.'"),
 ("ups_note:'Glow Lab Pro: 3 days for $1, then $9.99 per month. Cancel any time. Payments are handled by a secure payment provider.'", "ups_note:'Glow Lab Pro: $9.99 per month. Cancel any time. Payments are handled by a secure payment provider.'"),
 ("ups_note:'Glow Lab Pro: 3 дня за $1, затем $9,99 в месяц. Отмена в любой момент. Платежи проходят через защищённый платёжный сервис.'", "ups_note:'Glow Lab Pro: $9,99 в месяц. Отмена в любой момент. Платежи проходят через защищённый платёжный сервис.'"),
 ("used_p:'Start the 3-day Pro trial for $1 to analyse again and get your improvement plan.'", "used_p:'Get Pro for $9.99 per month to analyse again and get your improvement plan.'"),
 ("used_p:'Начните пробный период Pro на 3 дня за $1, чтобы анализировать снова и получить план улучшения.'", "used_p:'Оформите Pro за $9,99 в месяц, чтобы анализировать снова и получить план улучшения.'"),
 ("pro_btn:'Start trial for $1'", "pro_btn:'Get Pro · $9.99/month'"), ("pro_btn:'Начать пробный период за $1'", "pro_btn:'Оформить Pro'"),
 ("pro_for:' for 3 days'", "pro_for:' / month'"), ("pro_for:' за 3 дня'", "pro_for:' / мес'"),
 ("pro_badge:'3-day trial'", "pro_badge:'Popular'"), ("pro_badge:'Пробные 3 дня'", "pro_badge:'Популярный'"),
 ("pr_sub:'Approximate analysis is free and unlimited. For detailed results and guides, start the 3-day trial for $1.'", "pr_sub:'Approximate analysis is free and unlimited. Detailed results and guides come with Pro for $9.99 per month.'"),
 ("pr_sub:'Примерный анализ бесплатный и безлимитный. Для детальных результатов и гайдов начните пробный период на 3 дня за $1.'", "pr_sub:'Примерный анализ бесплатный и безлимитный. Детальные результаты и гайды входят в Pro за $9,99 в месяц.'"),
 ("pr_note:'The trial costs $1 for 3 days, then Pro renews monthly. You can cancel at any time.'", "pr_note:'Pro renews monthly at $9.99. You can cancel at any time and future charges stop.'"),
 ("pr_note:'Пробный период стоит $1 за 3 дня, затем Pro продлевается ежемесячно. Отменить можно в любой момент.'", "pr_note:'Pro продлевается ежемесячно за $9,99. Отменить можно в любой момент, дальше списаний не будет.'"),
 ("a7:'Yes, any time, including during the trial. Payments are handled by a secure payment provider.'", "a7:'Yes, any time. Payments are handled by a secure payment provider.'"),
 ("a7:'Да, в любой момент, в том числе во время пробного периода. Платежи проходят через защищённый платёжный сервис.'", "a7:'Да, в любой момент. Платежи проходят через защищённый платёжный сервис.'"),
 ("pl_price: '$1 for 3 days, then $9.99 / month. Cancel any time.'", "pl_price: '$9.99 / month. Cancel any time.'"),
 ("pl_go: 'Start trial for $1'", "pl_go: 'Get Pro · $9.99/month'"),
 ("pl_price: '$1 за 3 дня, затем $9.99 в месяц. Отмена в любой момент.'", "pl_price: '$9.99 в месяц. Отмена в любой момент.'"),
 ("pl_go: 'Начать пробный период за $1'", "pl_go: 'Оформить Pro · $9.99/мес'"),
 ("Glow Lab Pro: 3 дня за $1, затем $9,99 в месяц. Отменить можно в любой момент, в том числе во время пробного периода.", "Glow Lab Pro: $9,99 в месяц. Отменить можно в любой момент."),
 ("Glow Lab Pro: $1 for 3 days, then $9.99 per month. You can cancel at any time, including during the trial.", "Glow Lab Pro: $9.99 per month. You can cancel at any time."),
 ("Подписку можно отменить в любой момент, в том числе в пробный период.", "Подписку можно отменить в любой момент."),
 ("You can cancel any time, including during the trial.", "You can cancel any time."),
]
NOTRIAL += [('<div class="price">$1<small data-i18n="pro_for">', '<div class="price">$9.99<small data-i18n="pro_for">'),
 ("pro_then:'then $9.99 / month, cancel any time'", "pro_then:'Billed monthly. Cancel any time.'"),
 ("pro_then:'затем $9,99 в месяц, отмена в любой момент'", "pro_then:'Списание раз в месяц. Отмена в любой момент.'")]
for o, n in NOTRIAL: s = one(s, o, n)
s = one(s, '<meta name="theme-color" content="#F2F3F5">', '<meta name="theme-color" content="#0a0908">')
open(p, 'w', encoding='utf-8').write(s)

# ---------- legal pages ----------
for name in ('terms.html', 'privacy.html', 'refund.html'):
    q = os.path.join(dst, name); t = open(q, encoding='utf-8').read()
    t = style_blocks(t, lambda css: fonts(dk.conv_css(css)))
    t = t.replace('</style>', legal_layer + '</style>', 1)
    t = style_blocks(t, mono)
    for o, n in [
      ("Glow Lab Pro costs $1 for a 3-day trial and then $9.99 per month", "Glow Lab Pro costs $9.99 per month"),
      ("<h2><i>07</i>Free trial</h2>", "<h2><i>07</i>No trial</h2>"),
      ("The $1 trial gives access to Glow Lab Pro for 3 days. Unless you cancel before it ends, the subscription renews at $9.99 per month. One trial per person.", "Glow Lab Pro has no trial period. The first $9.99 payment gives immediate access for one month, and the subscription renews monthly until you cancel."),
      ("Glow Lab Pro стоит $1 за пробный период 3 дня, затем $9.99 в месяц", "Glow Lab Pro стоит $9.99 в месяц"),
      ("<h2><i>07</i>Пробный период</h2>", "<h2><i>07</i>Без пробного периода</h2>"),
      ("Пробный период за $1 даёт доступ к Glow Lab Pro на 3 дня. Если не отменить его до окончания, подписка продлится за $9.99 в месяц. Один пробный период на человека.", "У Glow Lab Pro нет пробного периода. Первый платёж $9.99 сразу даёт доступ на месяц, далее подписка продлевается ежемесячно до отмены."),
      ("Glow Lab Pro is a digital subscription: $1 for a 3-day trial, then $9.99 per month", "Glow Lab Pro is a digital subscription: $9.99 per month"),
      (" To avoid the first $9.99 charge, cancel before the 3-day trial ends.", ""),
      ("<h2><i>03</i>The $1 trial</h2>", "<h2><i>03</i>First payment</h2>"),
      ("The $1 trial charge is not refundable once the trial has started, because access is provided immediately.", "The first $9.99 payment gives immediate access. The same rules as for monthly renewals below apply to it."),
      ("Glow Lab Pro это цифровая подписка: $1 за пробный период 3 дня, затем $9.99 в месяц", "Glow Lab Pro это цифровая подписка: $9.99 в месяц"),
      (" Чтобы не было первого списания $9.99, отмените подписку до окончания пробных 3 дней.", ""),
      ("<h2><i>03</i>Пробный период за $1</h2>", "<h2><i>03</i>Первый платёж</h2>"),
      ("Платёж $1 за пробный период не возвращается после начала пробного периода, так как доступ предоставляется сразу.", "Первый платёж $9.99 сразу открывает доступ. К нему применяются те же правила, что и к ежемесячным продлениям ниже."),
      ("Last updated: October 18, 2026", "Last updated: October 20, 2026"), ("Обновлено: 18 октября 2026", "Обновлено: 20 октября 2026")]:
        if o in t: t = t.replace(o, n)
    open(q, 'w', encoding='utf-8').write(t)
print('built', dst)
