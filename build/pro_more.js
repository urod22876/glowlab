
  /* ---------- account settings (saved in the account, applied on every device) ---------- */
  var ACC = ['#ffffff', '#c9d1db', '#9ec9ff', '#9fe3c4', '#f2a9c4', '#f4c76a'];
  function setGet() { var uid = proUid(); if (!uid) return {}; try { return JSON.parse(lsGet('gl_set_' + uid) || 'null') || {}; } catch (e) { return {}; } }
  function setPut(o) { var uid = proUid(); if (!uid) return; lsSet('gl_set_' + uid, JSON.stringify(o)); Cloud.push(uid, { set: o }); applySettings(); }
  var remShown = false;
  function applySettings() {
    var s = setGet(); document.documentElement.style.setProperty('--acc', s.acc || '#ffffff');
    var uid = proUid(); if (!uid || remShown || !s.rem) return;
    var a = histGet(uid).filter(function (x) { return x.f === faceSel(uid); }); if (!a.length) return;
    if (Date.now() - a[a.length - 1].t > s.rem * 864e5) { remShown = true; setTimeout(function () { toast(t('rem_due', { d: s.rem }), '', 10000); }, 2500); }
  }
  function twoStep(btn, label, fn) {
    var armed = false, tm = null;
    btn.addEventListener('click', function () {
      if (!armed) { armed = true; btn.classList.add('arm'); btn.textContent = t('set_sure'); tm = setTimeout(function () { armed = false; btn.classList.remove('arm'); btn.textContent = label; }, 4000); return; }
      clearTimeout(tm); armed = false; btn.classList.remove('arm'); btn.textContent = label; fn();
    });
  }
  function paintSettings() {
    var grid = $('.ac-grid'), uid = proUid(); if (!grid || !uid) return;
    var card = $('.ac-set', grid);
    if (!card) { card = h('div', 'ac-card ac-set'); var out = $('.ac-out', grid); grid.insertBefore(card, out || null); }
    card.innerHTML = '';
    var s = setGet();
    h('h3', null, t('set_h'), card);
    function row(title, sub) { var r = h('div', 'set-r', null, card), l = h('div', 'set-l', null, r); h('b', null, title, l); if (sub) h('span', null, sub, l); return h('div', 'set-c', null, r); }
    /* profile colour */
    var c1 = row(t('set_acc'), t('set_acc_d'));
    ACC.forEach(function (col) { var b = h('button', 'sw' + ((s.acc || '#ffffff') === col ? ' on' : ''), null, c1); b.type = 'button'; b.style.setProperty('--c', col); b.setAttribute('aria-label', col); b.addEventListener('click', function () { var o = setGet(); o.acc = col; setPut(o); paintSettings(); }); });
    /* rescan reminder */
    var c2 = row(t('set_rem'), t('set_rem_d')), sg = h('div', 'seg', null, c2);
    [[0, 'set_off'], [14, 'set_2w'], [28, 'set_4w']].forEach(function (o) { var b = h('button', (s.rem || 0) === o[0] ? 'on' : '', t(o[1]), sg); b.type = 'button'; b.addEventListener('click', function () { var x = setGet(); x.rem = o[0]; setPut(x); paintSettings(); }); });
    /* faces: rename, change or remove the picture, delete, add */
    var c3 = row(t('set_faces'), t('set_faces_d')), fl = h('div', 'set-faces', null, c3);
    function upd(id, fn) { var fs = facesGet(uid); fs.forEach(function (x) { if (x.id === id) fn(x); }); facesSet(uid, fs); }
    function pickPhoto(cb) { var fi = document.createElement('input'); fi.type = 'file'; fi.accept = 'image/*'; fi.addEventListener('change', function () { var f0 = fi.files && fi.files[0]; if (f0) shrinkImage(f0, 96).then(cb, function () { toast(t('pf_bad'), 'bad', 4000); }); }); fi.click(); }
    function refresh() { paintSettings(); renderMyPlan(); renderProgress(); }
    facesGet(uid).forEach(function (f) {
      var it = h('div', 'set-face', null, fl), avb = h('button', 'set-av', null, it); avb.type = 'button'; avb.title = t('set_ph_ch'); faceAv(avb, f);
      avb.addEventListener('click', function () { pickPhoto(function (d) { upd(f.id, function (x) { x.th = d; }); refresh(); }); });
      var n = h('input', 'ob-in', null, it); n.maxLength = 24; n.value = faceName(f); n.setAttribute('aria-label', t('set_faces'));
      n.addEventListener('change', function () { var v = n.value.trim(); upd(f.id, function (x) { x.n = (f.id === 'me' && (!v || v === t('fc_me'))) ? '' : (v || x.n); }); refresh(); });
      var acts = h('div', 'set-fa', null, it);
      var pb = h('button', 'g-link', t('set_ph_ch'), acts); pb.type = 'button'; pb.addEventListener('click', function () { avb.click(); });
      if (f.th) { var rb = h('button', 'g-link', t('set_ph_rm'), acts); rb.type = 'button'; rb.addEventListener('click', function () { upd(f.id, function (x) { x.th = null; }); refresh(); }); }
      var del = h('button', 'g-link danger', t(f.id === 'me' ? 'set_clear' : 'set_del'), acts); del.type = 'button';
      twoStep(del, t(f.id === 'me' ? 'set_clear' : 'set_del'), function () {
        if (f.id === 'me') upd('me', function (x) { x.n = ''; x.th = null; });
        else facesSet(uid, facesGet(uid).filter(function (x) { return x.id !== f.id; }));
        histSet(uid, histGet(uid).filter(function (x) { return x.f !== f.id; }));
        phDel(function (x) { return x.u === uid && x.f === f.id; });
        if (PLAN_CTX.face === f.id) { PLAN_CTX.items = null; PLAN_CTX.face = null; }
        if (f.id === 'me') lsSet('gl_last_' + uid, null);
        if (faceSel(uid) === f.id) faceSelSet(uid, 'me');
        toast(t('set_done'), 'ok', 2500); refresh();
      });
    });
    var add = h('form', 'set-add', null, fl), ai = h('input', 'ob-in', null, add); ai.maxLength = 24; ai.placeholder = t('fc_name_ph');
    var ab = h('button', 'btn ghost small', '+ ' + t('fc_new'), add); ab.type = 'submit';
    add.addEventListener('submit', function (e) { e.preventDefault(); var v = ai.value.trim(); if (!v) { ai.focus(); return; } var fs = facesGet(uid); fs.push({ id: 'f' + Date.now().toString(36), n: v, th: null }); facesSet(uid, fs); toast(t('set_done'), 'ok', 2000); refresh(); });
    /* before/after photos on this device */
    var c4 = row(t('set_ph'), t('set_ph_d')), lb = h('label', 'set-tg', null, c4), cb = h('input', null, null, lb); cb.type = 'checkbox'; cb.checked = keepPhotos(uid); h('span', null, t('set_ph_keep'), lb);
    cb.addEventListener('change', function () { lsSet('gl_keepph_' + uid, cb.checked ? '1' : '0'); });
    var cnt = h('span', 'set-cnt', null, c4); phList(uid).then(function (a) { cnt.textContent = t('set_ph_n', { n: a.length }); });
    var dp = h('button', 'g-link danger', t('set_ph_del'), c4); dp.type = 'button';
    twoStep(dp, t('set_ph_del'), function () {
      phDel(function (x) { return x.u === uid; }).then(function () {
        var fs = facesGet(uid); fs.forEach(function (x) { x.th = null; }); facesSet(uid, fs); /* face pictures are photo copies too */
        toast(t('set_done'), 'ok', 3000); refresh();
      });
    });
    /* my data */
    var c5 = row(t('set_data'), t('set_data_d'));
    var ex = h('button', 'btn ghost small', t('set_export'), c5); ex.type = 'button';
    ex.addEventListener('click', function () {
      var i = Auth.info() || {}, data = { exported: new Date().toISOString(), account: { name: i.n, email: i.e }, profile: profGet(uid), settings: setGet(), faces: facesGet(uid).map(function (f) { return { id: f.id, name: faceName(f) }; }), scans: histGet(uid), plan30: p30Get(uid) };
      var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })); a.download = 'glowlab-my-data.json'; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
    });
    var dh = h('button', 'g-link danger', t('set_hist_del'), c5); dh.type = 'button';
    twoStep(dh, t('set_hist_del'), function () { histSet(uid, []); lsSet('gl_last_' + uid, null); PLAN_CTX.items = null; PLAN_CTX.face = null; phDel(function (x) { return x.u === uid; }); p30Set(uid, {}); toast(t('set_done'), 'ok', 3000); paintSettings(); renderMyPlan(); renderProgress(); });
  }

  /* ---------- results in plain words ---------- */
  function plainMeaning(key) { var s = gTxt(PLAIN[key]).replace(/^[^:.]{0,40}:\s*/, ''); return s.charAt(0).toUpperCase() + s.slice(1); }
  function plainRows(T, items, FK) {
    T.innerHTML = '';
    /* what is outside the usual range comes first; the rest folds into one line */
    var off = items.filter(function (i) { return i.status !== 'ok'; }).sort(function (a, b) { return b.dev - a.dev; }), ok = items.filter(function (i) { return i.status === 'ok'; });
    var okBox = null;
    off.concat(ok).forEach(function (it) {
      if (it.status === 'ok' && !okBox) { okBox = fold(T, 'pr-ok', !off.length, function (s) { h('b', null, t('pr_ok_n', { n: ok.length }), s); }); okBox = h('div', 'fx-b mtable', null, okBox); }
      var host = it.status === 'ok' && okBox ? okBox : T;
      var d = GL.DEFS[it.key], r = h('div', 'pr-row ' + it.status + (FK.indexOf(it.key) >= 0 ? ' focus' : ''), null, host);
      var top = h('div', 'pr-top', null, r); h('b', null, t('m_' + it.key + '_name'), top);
      var v = h('span', 'pr-v', null, top); h('span', 'num', valText(it.key, it.value), v);
      h('span', 'chip ' + it.status, t(it.status === 'ok' ? 'chip_ok' : it.status === 'near' ? 'chip_near' : 'chip_off'), v);
      var span = d.hi - d.lo, mn = d.lo - span, mx = d.hi + span, rb = h('div', 'rb', null, r), band = h('span', 'band', null, rb), kn = h('i', null, null, rb);
      band.style.left = '33.33%'; band.style.width = '33.33%'; kn.style.left = clamp((it.value - mn) / (mx - mn) * 100, 2, 98) + '%';
      var p = h('p', 'pr-p', null, r);
      if (PLAIN[it.key]) p.appendChild(document.createTextNode(plainMeaning(it.key) + ' '));
      h('span', 'pr-n', t('pr_norm', { r: rangeStr(it.key) }) + ' ', p);
      h('b', 'pr-d', descOf(it), p);
    });
  }
  /* the score ladder and the long technical list fold away; the important part stays on top */
  function tierFold(root) {
    var tb = $('.rt-tiers', root); if (!tb || tb.closest('.rt-fold')) return;
    var th = tb.previousElementSibling, d = document.createElement('details'); d.className = 'fx rt-fold';
    var s = h('summary', null, null, d); h('b', 'rt-fold-t', null, s);
    tb.parentNode.insertBefore(d, tb); if (th && th.classList.contains('rt-th')) th.hidden = true; d.appendChild(tb);
    hooks.push(function () { var b = $('.rt-fold-t', d); if (b) b.textContent = t('tr_h'); });
    $('.rt-fold-t', d).textContent = t('tr_h');
  }
  function mxFold(box, n) {
    if (!box) return;
    box.classList.add('mx-fold');
    var hh = $('.mx-h', box); if (!hh) return;
    var open = box.classList.contains('open');
    hh.textContent = t('mx_adv', { n: n }); hh.setAttribute('role', 'button'); hh.tabIndex = 0; hh.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (!hh._fold) { hh._fold = 1; var tg = function () { box.classList.toggle('open'); hh.setAttribute('aria-expanded', box.classList.contains('open') ? 'true' : 'false'); }; hh.addEventListener('click', tg); hh.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); tg(); } }); }
    var sub = $('.mx-sub', box); if (sub) sub.textContent = t('mx_adv_d');
  }

  /* ---------- result window: fits the screen, does not scroll ---------- */
  function rmFit(m, box) {
    function fit() {
      box.style.setProperty('--fit', '1');
      var hgt = box.offsetHeight, avail = window.innerHeight - 24; /* offsetHeight: the glow layer around the box must not count */
      box.style.setProperty('--fit', String(Math.min(1, avail / Math.max(1, hgt))));
    }
    fit(); setTimeout(fit, 60); setTimeout(fit, 400);
    window.addEventListener('resize', fit);
    var stop = function (e) { e.preventDefault(); };
    m.addEventListener('wheel', stop, { passive: false });
    m.addEventListener('touchmove', stop, { passive: false });
    var mo = new MutationObserver(function () { if (!m.isConnected) { window.removeEventListener('resize', fit); mo.disconnect(); } });
    mo.observe(document.body, { childList: true });
  }

  /* ---------- result window: GlowLab name badge under the photo (visible in screen recordings / ads) ---------- */
  function rmBrand(box) {
    var ph = box.querySelector('.rm-card .pc-ph');
    if (!ph || ph.querySelector('.rm-brand')) return;
    var b = document.createElement('span'); b.className = 'rm-brand'; b.setAttribute('aria-label', 'GlowLab');
    var sp = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); sp.setAttribute('viewBox', '0 0 24 24'); sp.setAttribute('aria-hidden', 'true'); sp.setAttribute('class', 'rm-spark');
    sp.innerHTML = '<path d="M12 1.5c.6 4.9 2.6 8.3 10.5 10.5-7.9 2.2-9.9 5.6-10.5 10.5C11.4 17.6 9.4 14.2 1.5 12 9.4 9.8 11.4 6.4 12 1.5Z" fill="#fff"/>';
    b.appendChild(sp);
    var w = document.createElement('b'); w.setAttribute('aria-hidden', 'true');
    w.innerHTML = 'Glow<span>Lab</span>';
    b.appendChild(w); ph.appendChild(b);
  }

  /* ---------- result window: category bars (eyes, jaw, harmony...) under the scores, read from this scan's breakdown ---------- */
  function rmBars(box, c) {
    var card = box.querySelector('.rm-card'), res = c && c.closest ? c.closest('.results') : null;
    if (!card || !res) return;
    var tries = 0;
    (function fill() {
      var li = [].slice.call(res.querySelectorAll('.rt-bars li'));
      if (!li.length) { if (++tries < 8) setTimeout(fill, 150); return; }
      if (card.querySelector('.rm-bars')) return;
      var ul = document.createElement('ul'); ul.className = 'rm-bars';
      li.slice(0, 4).forEach(function (r, i) {
        var n = r.querySelector('.bh b'), v = r.querySelector('.bh span');
        if (!n || !v) return;
        var sc = Math.max(0, Math.min(100, parseFloat(v.textContent) || 0));
        var row = document.createElement('li'); row.style.setProperty('--d', (1.5 + i * 0.12) + 's');
        var hd = document.createElement('div'); hd.className = 'rb-h';
        var b = document.createElement('b'); b.textContent = n.textContent; hd.appendChild(b);
        var s = document.createElement('span'); s.textContent = fmt(sc / 10, 1); hd.appendChild(s);
        var bar = document.createElement('i'), u = document.createElement('u'); u.style.setProperty('--w', sc + '%'); bar.appendChild(u);
        row.appendChild(hd); row.appendChild(bar); ul.appendChild(row);
      });
      if (!ul.children.length) return;
      var more = card.querySelector('.pc-more');
      if (more) card.insertBefore(ul, more); else card.appendChild(ul);
      window.dispatchEvent(new Event('resize')); /* the window re-fits to the screen */
    })();
  }

  /* ---------- assistant: signed-in users get the general assistant (the server checks the sign-in) ---------- */
  /* Pro: the assistant gets a short summary of the latest scan, so it can answer about this face */
  function asCtx() {
    if (!PRO) return '';
    try {
      var uid = proUid(); if (!uid) return '';
      var fid = faceSel(uid), D = faceData(fid); if (!D.items) return '';
      var p = window.GL_PROFILE || {}, en = function (x) { return x[0]; }, nm = function (k) { return I18N.en['m_' + k + '_name'] || k; }, out = [];
      out.push('Face: ' + (fid === 'me' ? 'the user' : 'another person the user tracks') + (p.sex ? ', sex ' + (p.sex === 'm' ? 'male' : 'female') : ''));
      if (D.front) out.push('Front score ' + D.front.p + '/8 (' + (D.front.tr || '') + ')');
      if (D.profile) out.push('Profile score ' + D.profile.p + '/8 (' + (D.profile.tr || '') + ')');
      if (D.sh && SHAPE_DB[D.sh]) out.push('Face shape: ' + en(SHAPE_DB[D.sh].n));
      if (D.sd) out.push('Better side on photo: ' + D.sd.k);
      var wk = planWeak(D.items); if (wk.length) out.push('Areas outside the usual range: ' + wk.map(function (i) { var d = GL.DEFS[i.key]; return nm(i.key) + ' ' + valStr(i.key, i.value) + ' (usual ' + rangeStr(i.key) + ', ' + i.dir + ', ' + (planEntry(i.key) || {}).ch + ' changeable)'; }).join('; '));
      var st = D.items.filter(function (i) { return i.status === 'ok'; }).sort(function (a, b) { return a.closeness - b.closeness; }).slice(0, 4);
      if (st.length) out.push('Strengths: ' + st.map(function (i) { return nm(i.key); }).join(', '));
      if (p.bother && p.bother.length) out.push('User concerns (questionnaire codes): ' + p.bother.join(', '));
      return out.join('. ').slice(0, 1500);
    } catch (e) { return ''; }
  }
  /* reads the answer: a stream of text pieces (shown as they come) or a JSON { reply } */
  function asRead(r, onPart) {
    if (!r.ok) throw new Error('x');
    var ct = r.headers.get('content-type') || '';
    if (ct.indexOf('json') >= 0 || !r.body || !r.body.getReader) return r.json().then(function (j) { if (!j || !j.reply) throw new Error('x'); return j.reply; });
    var rd = r.body.getReader(), dec = new TextDecoder(), acc = '';
    return new Promise(function (ok, no) {
      var stop = setTimeout(function () { try { rd.cancel(); } catch (e) {} if (acc.trim()) ok(acc.trim()); else no(new Error('timeout')); }, 70000);
      (function pump() {
        rd.read().then(function (x) {
          if (x.done) { clearTimeout(stop); acc += dec.decode(); if (acc.trim()) ok(acc.trim()); else no(new Error('empty')); return; }
          acc += dec.decode(x.value, { stream: true }); if (onPart) { try { onPart(acc); } catch (e) {} } pump();
        }, function (e) { clearTimeout(stop); if (acc.trim()) ok(acc.trim()); else no(e); });
      })();
    });
  }
  function asTimeout(p, ms) { return Promise.race([p, new Promise(function (ok, no) { setTimeout(function () { no(new Error('timeout')); }, ms); })]); }
  function asHeaders() {
    var hd = { 'content-type': 'application/json' };
    if (!AUTH_ON || !Auth.signed()) return Promise.resolve(hd);
    return waitUser(3000).then(function (u) { return u.getIdToken(); }).then(function (tk) { hd.authorization = 'Bearer ' + tk; return hd; }, function () { return hd; });
  }
