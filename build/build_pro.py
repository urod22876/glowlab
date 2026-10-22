# Glow Lab Pro layer: python3 -I build_pro.py <site_dir>   (patches the built dark site in place)
# server-checked Pro after payment, 1 free analysis, personal plan + 30-day checklist, progress chart, honest texts
import sys, os, shutil
here = os.path.dirname(os.path.abspath(__file__))
site = sys.argv[1]
def rd(n): return open(os.path.join(here, n), encoding='utf-8').read()
def one(s, old, new):
    n = s.count(old)
    if n != 1: raise SystemExit('expected 1 match, got %d: %r' % (n, old[:90]))
    return s.replace(old, new)

p = os.path.join(site, 'index.html'); s = open(p, encoding='utf-8').read()

# config: free limit on, Pro comes from the server
s = one(s, "var ENFORCE_FREE_LIMIT = false;", "var ENFORCE_FREE_LIMIT = true; ")
s = one(s, "var PRO = false; // client-side gate for demo purposes; real gating needs a backend after payment",
           "var PRO = false; // set after sign-in from /api/pro (the server checks the Dodo Payments subscription)")
s = one(s, "// checkout link of your payment provider for the Pro trial ($1 for 3 days, then monthly), e.g. a Lemon Squeezy or Paddle checkout URL",
           "// Dodo Payments payment link of Glow Lab Pro ($9.99 per month); the buyer returns to /?checkout=done")

# live Dodo Payments product (Glow Lab Pro, live mode)
s = one(s, "https://test.checkout.dodopayments.com/buy/pdt_0NqA6l5LZVzhNuAMj4FdI?quantity=1", "https://checkout.dodopayments.com/buy/pdt_0NqA8SGEIuBYIVRvSEqPv?quantity=1")

# texts + plan content + Pro module, inside the app (before the hero scanner)
s = one(s, "  /* ---------- hero scanner ---------- */",
        rd('pro_i18n.js') + rd('pro_plan_db.js') + rd('pro_style_db.js') + rd('pro_core.js') + rd('pro_data.js') + rd('pro_views.js') + rd('pro_more.js') + "\n  /* ---------- hero scanner ---------- */")
s = one(s, "  function init() {\n    initAcct();", "  function init() {\n    proBoot();\n    initAcct();")
s = one(s, "    try { initAssistant(); } catch (e) {}\n  }", "    try { initAssistant(); } catch (e) {}\n    try { checkoutReturn(); } catch (e) {}\n  }")

# results: keep the score, the items and the scan in history
s = one(s, "S.rcI = rcI; S.rcPsl = psl;", "S.rcI = rcI; S.rcPsl = psl; S.rcSc = Math.round(sc * 10);")
s = one(s, "PLAN_CTX.areas = sm.areas.map(function (it) { return t('m_' + it.key + '_name'); }); PLAN_CTX.retake = rt; PLAN_CTX.scanned = true; renderPlan();",
           "PLAN_CTX.areas = sm.areas.map(function (it) { return t('m_' + it.key + '_name'); }); PLAN_CTX.retake = rt; PLAN_CTX.scanned = true;\n"
           "      PLAN_CTX.items = PLAN_CTX.items || {}; PLAN_CTX.items[kind] = items; S.items = items; lastSave(kind, items); renderPlan();")
s = one(s, "if (S.ok) { consume(); showGeo();", "if (S.ok) { consume(); histAdd(kind, S.rcPsl, S.rcSc, S.items, { img: R.photo, pn: S.pn, lm: S.lm, aspect: S.aspect, root: root, tier: TIERS[tierIdx(S.rcPsl)].k }); showGeo();")

# results block "areas to improve": Pro sees its plan instead of the price
s = one(s, "$('.ups-list', root).hidden = !sum.areas.length; $('.upsell h4', root).hidden = !sum.areas.length;",
           "$('.ups-list', root).hidden = !sum.areas.length; $('.upsell h4', root).hidden = !sum.areas.length; paintUps(root);")
s = one(s, "upsBtn.addEventListener('click', function (e) { e.preventDefault(); openPricing(); });",
           "upsBtn.addEventListener('click', function (e) { e.preventDefault(); if (PRO) goPlan(); else openPricing(); });")

# guides order follows the flagged areas (the old "read your scan" and "photo" guides were removed)
s = one(s, "    if (PLAN_CTX.scanned && PLAN_CTX.areas.length) bump('read');\n", "    planGuideOrder().reverse().forEach(bump);\n")
s = one(s, "    if (PLAN_CTX.retake.length) bump('photo');\n", "")
s = one(s, "    if (!open) { var cta = h('div', 'pl-cta', null, grid), b2 = h('a', 'btn big', U.unlock, cta); b2.href = '#plans'; b2.addEventListener('click', function (e) { e.preventDefault(); openPricing(); }); }\n  }",
           "    if (!open) { var cta = h('div', 'pl-cta', null, grid), b2 = h('a', 'btn big', U.unlock, cta); b2.href = '#plans'; b2.addEventListener('click', function (e) { e.preventDefault(); openPricing(); }); }\n    try { renderMyPlan(); renderProgress(); } catch (e) {}\n  }")
s = one(s, '<div class="pl-wrap"><div class="pl-ctx"></div>', '<div class="gt" role="tablist"><button type="button" data-gt="plan"></button><button type="button" data-gt="prog"></button><button type="button" data-gt="guides"></button></div><div class="mp-wrap"><div class="mp" id="mp"></div><div class="pg" id="pg"></div></div><div class="pl-wrap"><div class="pl-ctx"></div>')

# checkout: signed in first, e-mail pre-filled and locked (Pro is matched to the account), same tab
s = one(s, """  function startCheckout(url) {
    if (!url) return;
    try { var ai = Auth.info(); if (ai && ai.e) url += '&email=' + encodeURIComponent(ai.e); if (ai && ai.u) url += '&metadata_uid=' + encodeURIComponent(ai.u); } catch (e) {}
    if (window.GL_CHECKOUT) { try { window.GL_CHECKOUT(url); return; } catch (e) {} } /* provider overlay hook, e.g. Lemon.js / Dodo / Polar embed */
    window.open(url, '_blank', 'noopener');
  }""", """  function startCheckout(url) {
    if (!url) return;
    if (AUTH_ON && !isDev() && !Auth.signed()) { closePricing(); toast(t('pm_signin'), '', 6000); requestSignIn(function () { openPricing(); }, true); return; }
    try { var ai = Auth.info(); if (ai && ai.e) url += '&email=' + encodeURIComponent(ai.e) + '&disableEmail=true'; if (ai && ai.u) url += '&metadata_uid=' + encodeURIComponent(ai.u); } catch (e) {}
    if (window.GL_CHECKOUT) { try { window.GL_CHECKOUT(url); return; } catch (e) {} } /* provider overlay hook */
    location.assign(url);
  }""")
# the Pro window for a Pro user: status + manage subscription
s = one(s, "    var x = h('button', 'pr-x', '×', c); x.type = 'button'; x.setAttribute('aria-label', t('g_close')); x.addEventListener('click', closePricing);\n",
           "    var x = h('button', 'pr-x', '×', c); x.type = 'button'; x.setAttribute('aria-label', t('g_close')); x.addEventListener('click', closePricing);\n"
           "    if (PRO) { proCard(c); document.body.classList.add('gm-open'); try { x.focus({ preventScroll: true }); } catch (e) {} return; }\n")
# account page: plan status + manage button; cloud merge of history / plan
s = one(s, "$('.ac-up').addEventListener('click', function () { openPricing(); });", "$('.ac-up').addEventListener('click', function () { if (PRO && !devPro()) openPortal(this); else openPricing(); });")
s = one(s, "    sm.textContent = parts.length ? parts.join(' · ') : t('ac_noprof');\n  }", "    sm.textContent = parts.length ? parts.join(' · ') : t('ac_noprof');\n    paintProBits();\n  }")
s = one(s, "            if (r.used) Object.keys(r.used).forEach(function (k) { if (r.used[k]) lsSet('gl_used3_' + uid0 + '_' + k, '1'); });",
           "            if (r.used) Object.keys(r.used).forEach(function (k) { if (r.used[k]) lsSet('gl_used3_' + uid0 + '_' + k, '1'); });\n            try { proMerge(uid0, r); } catch (e) {}")


# ----- v2 -----
# results in plain words; ladder and technical list fold away
s = one(s, """    items.forEach(function (it) {
      var d = GL.DEFS[it.key], span = d.hi - d.lo, mn = d.lo - span, mx = d.hi + span;
      var r = h('div', 'mrow' + (FK.indexOf(it.key) >= 0 ? ' focus' : ''), null, T), c1 = h('div', null, null, r);
      h('span', 'nm', t('m_' + it.key + '_name'), c1); h('span', 'rg', rangeText(it.key), c1);
      var rb = h('div', 'rb', null, r), band = h('span', 'band', null, rb), kn = h('i', null, null, rb);
      band.style.left = '33.33%'; band.style.width = '33.33%';
      kn.style.left = clamp((it.value - mn) / (mx - mn) * 100, 2, 98) + '%';
      var c3 = h('div', null, null, r);
      h('span', 'num', valText(it.key, it.value), c3);
      h('span', 'chip ' + it.status, t(it.status === 'ok' ? 'chip_ok' : it.status === 'near' ? 'chip_near' : 'chip_off'), c3);
    });
""", "    plainRows(T, items, FK);\n")
s = one(s, "var ld = $('.rt-ladder', root); ld.innerHTML = ''; ld.hidden = true;", "var ld = $('.rt-ladder', root); ld.innerHTML = ''; ld.hidden = true; tierFold(root);")
s = one(s, "            h('div', 'mx-note', mxu('canon'), row);\n", "")
s = one(s, "          h('div', null, mxu('lm') + ': ' + m.lms.map(mxLmName).join(', '), dt);\n", "")
s = one(s, "      mxDrawOv(mxShowSec, d);\n    }\n    hooks.push(function () { if (!PRO)",
           "      mxDrawOv(mxShowSec, d);\n      mxFold(box, d.secs.reduce(function (n, x) { return n + x.items.length; }, 0));\n    }\n    hooks.push(function () { if (!PRO)")
s = one(s, "var box = $('.mx', side); if (!box) return;\n      var al = $('.lk-all', side);", "var box = $('.mx', side); if (!box) return; box.classList.remove('mx-fold', 'open');\n      var al = $('.lk-all', side);")
# result window fits the screen and does not scroll
s = one(s, "document.body.appendChild(m); document.body.classList.add('rm-open');", "document.body.appendChild(m); document.body.classList.add('rm-open'); rmFit(m, box);")
# avatar saved in the account
s = one(s, "shrinkImage(f, 256).then(function (d) { lsSet('gl_av_' + uid, d);", "shrinkImage(f, 256).then(function (d) { lsSet('gl_av_' + uid, d); Cloud.push(uid, { av: d });")
s = one(s, "rm.addEventListener('click', function () { lsSet('gl_av_' + uid, null);", "rm.addEventListener('click', function () { lsSet('gl_av_' + uid, null); Cloud.push(uid, { av: '' });")
# account page: settings card
s = one(s, "    sm.textContent = parts.length ? parts.join(' · ') : t('ac_noprof');\n    paintProBits();\n  }", "    sm.textContent = parts.length ? parts.join(' · ') : t('ac_noprof');\n    paintProBits(); paintSettings();\n  }")
# init: tabs and settings
s = one(s, "    proBoot();\n    initAcct();", "    proBoot();\n    try { applySettings(); } catch (e) {}\n    initAcct();")
s = one(s, "    initScan(); renderPlan();", "    initScan(); renderPlan(); gtInit();")
# assistant: send the sign-in so the server can answer general questions
s = one(s, "      return fetch(ASSISTANT_URL, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ messages: msgs, lang: lang }) })",
           "      return asTimeout(asHeaders().then(function (hd) { return fetch(ASSISTANT_URL, { method: 'POST', headers: hd, body: JSON.stringify({ messages: msgs.slice(-14), lang: lang, ctx: asCtx(), stream: true }) }); }), 50000).then(function (r) { return asRead(r, onPart); })")
s = one(s, "        .then(function (r) { if (!r.ok) throw new Error('x'); return r.json(); })\n        .then(function (j) { if (!j || !j.reply) throw new Error('x'); return j.reply; });\n    }\n", "    }\n")
s = one(s, "    function remote(q) {", "    function remote(q, onPart) {")
s = one(s, "      remote(q).then(function (txt) { done(txt, null, false); }, function () { remoteOff = true; go(); });",
           "      remote(q, function (part) { if (wait.classList.contains('typing')) wait.classList.remove('typing'); var wb = $('.as-b', wait); wb.innerHTML = ''; rich(wb, part); box.scrollTop = box.scrollHeight; }).then(function (txt) { done(txt, null, false); }, function () { var r0 = local(q); if (r0.off) done(t('as_down'), null, true); else go(); });")
s = one(s, "var msgs = hist.slice(0, -1).filter(function (m) { return !m.off; }).slice(-8)", "var msgs = hist.slice(0, -1).filter(function (m) { return !m.off; }).slice(-13)")
for o, n in [("sub: 'Questions about the site'", "sub: 'Ask me anything'"), ("fabB: 'Ask about the site'", "fabB: 'Ask me anything'"), ("ph: 'Ask how the site works…'", "ph: 'Ask anything…'"),
             ("hi: 'Hi{n}! I’m the Glow Lab Assistant. I can explain how the site works: the free scan, photos, Pro, guides and your account. What would you like to know?'", "hi: 'Hi{n}! I’m the Glow Lab Assistant. Ask me anything: skin, style, fitness, the site, or any other question.'"),
             ("sub: 'Вопросы по сайту'", "sub: 'Спросите что угодно'"), ("fabB: 'Вопросы по сайту'", "fabB: 'Спросите что угодно'"), ("ph: 'Спросите, как работает сайт…'", "ph: 'Спросите что угодно…'"),
             ("hi: 'Привет{n}! Я Glow Lab Assistant. Подскажу, как работает сайт: бесплатный скан, фото, Pro, гайды и аккаунт. Что вас интересует?'", "hi: 'Привет{n}! Я Glow Lab Assistant. Спрашивайте что угодно: кожа, стиль, спорт, сайт или любой другой вопрос.'")]:
    s = one(s, o, n)

s = one(s, "$('.rt-pot', root).textContent = tp > ti ? t('rt_pot', { a: t('tier_' + TIERS[ti].k), b: t('tier_' + TIERS[tp].k) }) : psl >= 6.5 ? t('rt_pot0') : t('rt_pot1', { a: t('tier_' + TIERS[ti].k) });",
           "$('.rt-pot', root).textContent = tp > ti ? t(PRO ? 'rt_pot_p' : 'rt_pot', { a: t('tier_' + TIERS[ti].k), b: t('tier_' + TIERS[tp].k) }) : psl >= 6.5 ? t(PRO ? 'rt_pot0_p' : 'rt_pot0') : t(PRO ? 'rt_pot1_p' : 'rt_pot1', { a: t('tier_' + TIERS[ti].k) });")
s = one(s, "    function tierIdx(psl) { var n; for (n = 0; n < TIERS.length; n++) if (psl < TIERS[n].max) return n; return TIERS.length - 1; }",
           "    window.GL_PSL = pslOf;\n    function tierIdx(psl) { var n; for (n = 0; n < TIERS.length; n++) if (psl < TIERS[n].max) return n; return TIERS.length - 1; }")
s = one(s, "    hooks.push(function () { paint(); if (open) render(); });\n    paint();\n  }",
           "    hooks.push(function () { paint(); if (open) render(); });\n    window.GL_ASK = function (q) { if (!open) toggle(true); setTimeout(function () { ask(q); }, 150); };\n    paint();\n  }")
# Google sign-in: own-domain auth handler when the server sets window.GL_AUTH_SELF (AUTH_SELF = 1), exact error codes, redirect errors shown
s = one(s, "authDomain: 'glowlab-e39b2.firebaseapp.com'", "authDomain: (window.GL_AUTH_SELF && /(^|\\.)glow-lub\\.com$/.test(location.hostname)) ? location.hostname : 'glowlab-e39b2.firebaseapp.com'")
s = one(s, "return t(m[c] || 'au_e_gen');", "return t(m[c] || 'au_e_gen') + (!m[c] && c ? ' (' + c + ')' : '');")
s = one(s, "        fb = window.firebase.auth(app);", "        fb = window.firebase.auth(app);\n        try { fb.getRedirectResult().catch(function (e) { setTimeout(function () { try { var em = authErr(e); if (em) toast(em, 'bad', 12000); } catch (x) {} }, 800); }); } catch (e) {}")
# styles
if s.count('</style>') != 1: raise SystemExit('expected one <style> block')
s = s.replace('</style>', rd('pro.css') + '</style>', 1)
open(p, 'w', encoding='utf-8').write(s)

# server: assistant facts + Pro API
shutil.copy(os.path.join(here, '_worker.js'), os.path.join(site, '_worker.js'))
print('pro layer ok', site)
