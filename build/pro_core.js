
  /* ---------- Glow Lab Pro: status from the server (it asks Dodo Payments), checkout return, subscription management ---------- */
  var ProSt = { pro: false, until: null, renews: false, known: false };
  function devPro() { return isDev() && lsGet('gl_dev_pro') === '1'; }
  function proUid() { var i = Auth.signed() ? Auth.info() : null; return i && i.u ? i.u : null; }
  function proDate(d) { var x = new Date(d); if (isNaN(x)) return ''; try { return x.toLocaleDateString(lang === 'ru' ? 'ru-RU' : 'en-US', { day: 'numeric', month: 'long', year: 'numeric' }).replace(/\s?г\.$/, ''); } catch (e) { return x.toISOString().slice(0, 10); } }
  function proRefresh() {
    try { hooks.forEach(function (f) { f(); }); } catch (e) {}
    try { window.dispatchEvent(new Event('gl-synced')); } catch (e) {}
    paintProBits();
  }
  function proApply(st, uid) {
    var was = PRO;
    ProSt = { pro: !!st.pro, until: st.until || null, renews: !!st.renews, known: true };
    PRO = ProSt.pro || devPro();
    if (uid) lsSet('gl_pro_' + uid, JSON.stringify({ pro: ProSt.pro, until: ProSt.until, renews: ProSt.renews, t: Date.now() }));
    if (was !== PRO) proRefresh(); else paintProBits();
  }
  /* before the server answers: a recent "Pro" answer saved on this device keeps the page from flashing locks */
  function proBoot() {
    if (devPro()) { PRO = true; ProSt = { pro: true, until: lsGet('gl_dev_until') || null, renews: lsGet('gl_dev_until') ? false : true, known: true }; }
    else {
      var uid = proUid();
      if (uid) { try { var c = JSON.parse(lsGet('gl_pro_' + uid) || 'null'); if (c && c.pro && Date.now() - c.t < 3 * 864e5 && (!c.until || Date.parse(c.until) > Date.now())) { PRO = true; ProSt = { pro: true, until: c.until, renews: !!c.renews, known: false }; } } catch (e) {} }
    }
    hooks.push(paintProBits);
    if (AUTH_ON) Auth.on(function (u) { if (u) proCheck(); else if (PRO && !devPro()) { PRO = false; ProSt = { pro: false, until: null, renews: false, known: true }; proRefresh(); } });
  }
  function waitUser(ms) {
    return Auth.boot().then(function (a) {
      return new Promise(function (ok, no) { var t0 = Date.now(); (function p() { if (a.currentUser) return ok(a.currentUser); if (Date.now() - t0 > ms) return no({ error: 'auth' }); setTimeout(p, 200); })(); });
    });
  }
  function proApi(path) {
    return waitUser(8000).then(function (u) { return u.getIdToken(); }).then(function (tk) {
      return fetch(path, { method: 'POST', headers: { authorization: 'Bearer ' + tk } });
    }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) { j.status = r.status; throw j; } return j; }); });
  }
  var proBusy = null;
  function proCheck() {
    if (!AUTH_ON || devPro()) return Promise.resolve(null);
    if (proBusy) return proBusy;
    var uid = proUid();
    proBusy = proApi('/api/pro').then(function (j) { proBusy = null; proApply(j, uid); return j; }, function (e) {
      proBusy = null;
      /* a rejected sign-in means no Pro; a server or network problem keeps a recent saved answer */
      if (e && e.error === 'auth' && e.status === 401) proApply({ pro: false }, uid);
      return null;
    });
    return proBusy;
  }
  var toastEl = null, toastTm = null;
  function toast(msg, kind, ms) {
    if (!toastEl) { toastEl = h('div', 'pt', null, document.body); toastEl.setAttribute('role', 'status'); toastEl.setAttribute('aria-live', 'polite'); }
    clearTimeout(toastTm);
    toastEl.className = 'pt on ' + (kind || '');
    toastEl.innerHTML = '';
    if (kind === 'wait') h('i', 'pt-sp', null, toastEl);
    h('span', null, msg, toastEl);
    var x = h('button', 'pt-x', '×', toastEl); x.type = 'button'; x.setAttribute('aria-label', t('g_close')); x.addEventListener('click', function () { toastEl.className = 'pt'; });
    if (ms) toastTm = setTimeout(function () { toastEl.className = 'pt'; }, ms);
  }
  /* the payment page sends the buyer back to /?checkout=done&status=... */
  function checkoutReturn() {
    var q; try { q = new URLSearchParams(location.search); } catch (e) { return; }
    if (q.get('checkout') !== 'done') return;
    var st = (q.get('status') || '').toLowerCase();
    try { history.replaceState(null, '', location.pathname + (location.hash || '')); } catch (e) {}
    if (st && st !== 'succeeded' && st !== 'active' && st !== 'processing') { toast(t('pay_fail'), 'bad', 12000); return; }
    toast(t('pay_wait'), 'wait', 0);
    var n = 0;
    function again() {
      if (!AUTH_ON) return;
      if (!proUid()) { if (++n < 15) setTimeout(again, 1000); else toast(t('pay_signin'), 'bad', 0); return; }
      proCheck().then(function () {
        if (PRO) { toast(t('pay_ok'), 'ok', 9000); goPlan(); }
        else if (++n < 30) setTimeout(again, 3000);
        else toast(t('pay_slow'), 'bad', 0);
      });
    }
    again();
  }
  function openPortal(btn) {
    if (btn) btn.disabled = true;
    proApi('/api/portal').then(function (j) { if (j && j.link) location.assign(j.link); else throw j; }, function () { if (btn) btn.disabled = false; toast(t('pay_portal_err'), 'bad', 7000); });
  }
  function proLine(pfx) { return ProSt.until ? t(pfx + (ProSt.renews ? '_r' : '_c'), { d: proDate(ProSt.until) }) : ''; }
  /* the Pro window for someone who already has Pro */
  function proCard(c) {
    h('p', 'pr-eb', 'Glow Lab Pro', c); h('h3', null, t('pm_have'), c);
    var pro = h('div', 'pr-pro', null, c);
    h('p', 'pr-name', 'Glow Lab Pro', pro);
    var ln = proLine('pm_until'); if (ln) h('p', 'pr-trial', ln, pro);
    var ul = h('ul', 'pr-list', null, pro); ['pm_f1', 'pm_f2', 'pm_f3', 'pm_f4'].forEach(function (k) { h('li', null, t(k), ul); });
    var go = h('button', 'pr-go', t('pm_open_plan'), pro); go.type = 'button';
    go.addEventListener('click', function () { closePricing(); goPlan(); });
    if (!devPro()) {
      var mg = h('button', 'pr-free', null, c); mg.type = 'button';
      h('b', null, t('pm_manage'), mg); h('span', null, t('pm_manage_d'), mg);
      mg.addEventListener('click', function () { openPortal(mg); });
    }
  }
  /* account page: plan card and the three usage rows */
  function paintProBits() {
    var pl = $('.ac-pl'), up = $('.ac-up');
    if (pl) pl.textContent = PRO ? (proLine('ac_plpro') || t('ac_plpro')) : t('ac_plfree');
    if (up) up.textContent = PRO ? t('ac_manage') : t('ac_upg');
    var rows = $$('.ac-rows li b');
    if (rows.length === 3) { rows[0].textContent = PRO ? t('ac_unl') : t('ac_u1v'); rows[1].textContent = PRO ? t('ac_open') : 'Pro'; rows[2].textContent = PRO ? t('ac_open') : 'Pro'; }
  }

  /* results block "areas to improve": for Pro it leads to the personal plan instead of the price */
  function paintUps(root) {
    var u = $('.upsell', root); if (!u) return;
    u.classList.toggle('is-pro', !!PRO);
    var hs = $('h4 span', u), b = $('.ups-btn', u), n = $('.tips', u);
    if (hs) hs.textContent = t(PRO ? 'ups_h_pro' : 'ups_h');
    if (b) { b.textContent = t(PRO ? 'ups_btn_pro' : 'ups_btn'); b.setAttribute('href', PRO ? '#plan' : '#plans'); } /* in the app, #plan opens the Guides tab */
    if (n) n.textContent = t(PRO ? 'ups_note_pro' : 'ups_note');
    var pn = $('[data-i18n="pot_note"]', root); if (pn) pn.textContent = t(PRO ? 'pot_note_p' : 'pot_note');
    if (PRO) { var lh = $('.lk-how', root); if (lh) lh.remove(); var al = $('.lk-all', root); if (al) al.hidden = false; }
  }

