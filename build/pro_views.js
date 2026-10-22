
  /* ---------- personal plan helpers ---------- */
  function planItems() { var uid = proUid(); return uid ? faceData(faceSel(uid)).items : (PLAN_CTX.items ? [].concat(PLAN_CTX.items.front || [], PLAN_CTX.items.profile || []) : null); }
  function planEntry(key) { var e = PLAN_DB[key]; if (!e) return null; var base = e.alias ? PLAN_DB[e.alias] : e; return { ch: e.ch || base.ch, g: e.g || base.g, low: base.low, high: base.high, any: base.any }; }
  function planText(it) { var e = planEntry(it.key); if (!e) return null; var d = e[it.dir] || e.any || e.high || e.low; return d ? { ch: e.ch, g: e.g, what: d.what, act: d.act } : null; }
  function planWeak(items) { return (items || []).filter(function (i) { return i.status !== 'ok' && planText(i); }).sort(function (a, b) { return b.dev - a.dev; }).slice(0, 5); }
  function valStr(key, v) { var d = GL.DEFS[key]; return fmt(v, d.dec) + d.unit; }
  function rangeStr(key) { var d = GL.DEFS[key]; return fmt(d.lo, d.dec) + '–' + fmt(d.hi, d.dec) + d.unit; }
  function guideById(id) { return (window.GUIDES || []).filter(function (g) { return g.id === id; })[0]; }
  function planGuideOrder() { var o = []; planWeak(planItems()).forEach(function (it) { (planText(it).g || []).forEach(function (g) { if (o.indexOf(g) < 0) o.push(g); }); }); return o; }
  function lockBtn(parent, label) { var b = h('button', 'btn big', label, parent); b.type = 'button'; b.addEventListener('click', function () { openPricing(); }); return b; }
  /* how much the score would rise if this one area moved into its usual range (other areas unchanged) */
  function zoneGain(D, it) {
    if (!window.GL_PSL) return 0;
    var side = (D.items || []).filter(function (i) { return i.side === it.side; }); if (side.length < 3) return 0;
    var base = GL.harmony(side), mod = GL.harmony(side.map(function (i) { return i.key === it.key ? Object.assign({}, i, { status: 'ok', dev: 0, closeness: 1 }) : i; }));
    if (base == null || mod == null) return 0;
    return Math.max(0, Math.round((window.GL_PSL(mod) - window.GL_PSL(base)) * 10) / 10);
  }
  function askAI(q) { if (window.GL_ASK) window.GL_ASK(q); }
  function isMale() { var p = window.GL_PROFILE; return !p || p.sex !== 'f'; }
  function fold(parent, cls, open, sumFn) { var d = h('details', 'fx ' + (cls || ''), null, parent); d.open = !!open; var s = h('summary', null, null, d); sumFn(s); return d; }
  function lockNote(parent, key) { var l = h('div', 'mp-lk', null, parent); l.insertAdjacentHTML('afterbegin', '<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="4" y="9" width="12" height="9" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M7 9V6a3 3 0 0 1 6 0v3" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>'); h('span', null, t(key), l); var b = h('button', 'g-link', t('mp_unlock_s'), l); b.type = 'button'; b.addEventListener('click', function () { openPricing(); }); }

  /* ---------- Guides tab: "My plan · Progress · Guides" ---------- */
  var gtCur = null;
  function gtSet(name) {
    var sec = $('#plan'); if (!sec) return;
    gtCur = name; try { sessionStorage.setItem('gl_gt', name); } catch (e) {}
    sec.setAttribute('data-gt', name);
    $$('.gt button', sec).forEach(function (b) { var on = b.getAttribute('data-gt') === name; b.classList.toggle('on', on); b.setAttribute('aria-selected', on ? 'true' : 'false'); });
  }
  function gtInit() {
    var sec = $('#plan'), bar = $('.gt', sec || document); if (!sec || !bar) return;
    $$('button', bar).forEach(function (b) { b.addEventListener('click', function () { gtSet(b.getAttribute('data-gt')); try { sec.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {} }); });
    var s0 = null; try { s0 = sessionStorage.getItem('gl_gt'); } catch (e) {}
    gtSet(s0 || 'plan');
    hooks.push(function () { $$('button', bar).forEach(function (b) { b.textContent = t('gt_' + b.getAttribute('data-gt')); }); });
    $$('button', bar).forEach(function (b) { b.textContent = t('gt_' + b.getAttribute('data-gt')); });
  }
  function goPlan() { try { if (viewNow() === 'app') { showPane('guides'); gtSet('plan'); } else { var p = $('#plan'); if (p) p.scrollIntoView({ behavior: 'smooth' }); } } catch (e) {} }

  /* ---------- My plan ---------- */
  function renderMyPlan() {
    var box = $('#mp'); if (!box) return;
    box.innerHTML = '';
    faceBar(box);
    var uid = proUid(), fid = uid ? faceSel(uid) : 'me', fc = uid ? faceById(uid, fid) : null, D = uid ? faceData(fid) : { items: planItems() };
    var hd = h('div', 'mp-hd', null, box), ht = h('div', null, null, hd);
    h('span', 'eyebrow', t('mp_eb'), ht); h('h3', null, fid === 'me' ? t('mp_h') : t('mp_h_of', { n: faceName(fc) }), ht);
    if (!D.items) { h('p', 'mp-empty', t('mp_none'), box); var gb = h('button', 'btn ghost', t('mp_go'), box); gb.type = 'button'; gb.addEventListener('click', function () { try { showPane('analysis'); } catch (e) {} }); return; }
    /* scores */
    var sc = h('div', 'mp-sc', null, box);
    [['front', 'pg_front'], ['profile', 'pg_prof']].forEach(function (s) { var e = D[s[0]]; if (!e) return; var c = h('div', 'mp-sc-i', null, sc); h('span', null, t(s[1]), c); h('b', null, fmt(e.p, 1), c); h('small', null, '/8', c); if (e.tr) h('em', null, t('tier_' + e.tr), c); });
    if (PRO && D.front) { var rb = h('button', 'mp-rep', null, sc); rb.type = 'button'; rb.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 19h14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'; h('span', null, t('rep_btn'), rb); rb.addEventListener('click', function () { makeReport(fid, rb); }); }
    var list = h('div', 'mp-acc', null, box);
    /* face shape */
    if (D.sh && SHAPE_DB[D.sh]) {
      var S = SHAPE_DB[D.sh], d1 = fold(list, 'mp-row', false, function (s) { h('i', 'mp-ic sh', null, s); var tx = h('span', 'mp-rt', null, s); h('b', null, t('sh_h'), tx); h('em', null, gTxt(S.n), tx); });
      var b1 = h('div', 'fx-b', null, d1);
      if (!PRO) lockNote(b1, 'sh_lock');
      else {
        h('p', 'mp-what', gTxt(S.d), b1);
        var tips = [['sh_hair', S.hair], ['sh_glasses', S.glasses]]; if (isMale()) tips.splice(1, 0, ['sh_beard', S.beard]);
        var ul = h('dl', 'mp-dl', null, b1); tips.forEach(function (x) { h('dt', null, t(x[0]), ul); h('dd', null, gTxt(x[1]), ul); });
        h('p', 'tips', t('sh_note'), b1);
      }
    }
    /* best side */
    if (D.sd) {
      var sd = D.sd, d2 = fold(list, 'mp-row', false, function (s) { h('i', 'mp-ic sd', null, s); var tx = h('span', 'mp-rt', null, s); h('b', null, t('sd_h'), tx); h('em', null, t('sd_' + sd.k), tx); });
      var b2 = h('div', 'fx-b', null, d2);
      if (!PRO) lockNote(b2, 'sd_lock');
      else {
        if (sd.k === 'eq') h('p', 'mp-what', t('sd_eq_p'), b2);
        else {
          h('p', 'mp-what', t('sd_why', { w: (sd.why || []).map(function (k) { return gTxt(SIDE_WHY[k]); }).join(', ') || t('sd_why0') }), b2);
          var u2 = h('ul', 'mp-act', null, b2); ['sd_t1', 'sd_t2', 'sd_t3'].forEach(function (k) { h('li', null, t(k), u2); });
        }
        h('p', 'tips', t('sd_note'), b2);
      }
    }
    /* areas to work on */
    var weak = planWeak(D.items);
    weak.forEach(function (it) { var tx0 = planText(it); it._g = tx0 && tx0.ch !== 'no' ? zoneGain(D, it) : 0; });
    var best = weak.filter(function (it) { return it._g > 0; }).sort(function (a, b) { return b._g - a._g; })[0];
    if (best && PRO) { var bc = h('div', 'mp-best', null, list); h('span', null, t('gain_best'), bc); h('b', null, t('m_' + best.key + '_name'), bc); h('em', null, t('gain_v', { v: fmt(best._g, 1) }), bc); }
    h('b', 'mp-sub', weak.length ? t('mp_weak_n', { n: weak.length }) : t('mp_weak'), list);
    if (!weak.length) h('p', 'mp-empty', t('mp_allok'), list);
    weak.forEach(function (it, n) {
      var tx = planText(it), d = fold(list, 'mp-row zone', false, function (s) {
        h('span', 'mp-n', String(n + 1), s); var r = h('span', 'mp-rt', null, s); h('b', null, t('m_' + it.key + '_name'), r);
        h('em', null, t(it.status === 'near' ? 'mp_near' : 'mp_off') + ' · ' + t('mp_chs_' + tx.ch), r);
        if (PRO && it._g > 0) h('span', 'mp-gain', '+' + fmt(it._g, 1), s);
      });
      var b = h('div', 'fx-b', null, d);
      if (!PRO) { lockNote(b, 'mp_lock_z'); return; }
      h('p', 'mp-val', t('mp_val', { v: valStr(it.key, it.value), r: rangeStr(it.key) }), b);
      h('p', 'mp-what', gTxt(tx.what), b);
      var ul2 = h('ul', 'mp-act', null, b); tx.act.forEach(function (a) { h('li', null, gTxt(a), ul2); });
      h('p', 'mp-gn', tx.ch === 'no' ? t('gain_no') : it._g > 0 ? t('gain_p', { v: fmt(it._g, 1) }) : t('gain_0'), b);
      var gl = h('div', 'mp-gl', null, b);
      var ai = h('button', 'mp-g ai', t('ai_ask'), gl); ai.type = 'button';
      ai.addEventListener('click', function () { askAI(t('ai_q_zone', { n: t('m_' + it.key + '_name'), v: valStr(it.key, it.value), r: rangeStr(it.key) })); });
      (tx.g || []).forEach(function (gid) { var g = guideById(gid); if (!g) return; var gb2 = h('button', 'mp-g', t('mp_read') + ': ' + gTxt(g.t), gl); gb2.type = 'button'; gb2.addEventListener('click', function () { openGuide(g); }); });
    });
    var str = D.items.filter(function (i) { return i.status === 'ok'; }).sort(function (a, b) { return a.closeness - b.closeness; }).slice(0, 4);
    if (str.length) { var sb = h('div', 'mp-str', null, box); h('b', null, t('mp_str'), sb); var cl = h('div', 'mp-chips', null, sb); str.forEach(function (i) { h('span', 'mp-chip ok', t('m_' + i.key + '_name'), cl); }); }
    if (!PRO) { var lk = h('div', 'mp-lock', null, box); h('p', null, t('mp_lock'), lk); lockBtn(lk, t('mp_unlock')); return; }
    render30(box, weak);
    h('p', 'tips mp-note', t('mp_note'), box);
  }
  function render30(box, weak) {
    var uid = proUid() || 'dev', st = p30Get(uid);
    if (!st.start) { st.start = Date.now(); st.done = st.done || {}; p30Set(uid, st); }
    st.done = st.done || {};
    var weeks = PLAN30.map(function (w) { return w.slice(); });
    weak.slice(0, 3).forEach(function (it, n) { var tx = planText(it); weeks[n < 2 ? 1 : 2].push({ id: 'a_' + it.key, t: tx.act[0], pre: t('m_' + it.key + '_name') }); });
    var total = 0, done = 0; weeks.forEach(function (w) { w.forEach(function (x) { total++; if (st.done[x.id]) done++; }); });
    var day = Math.min(30, Math.max(1, Math.floor((Date.now() - st.start) / 864e5) + 1)), cur = Math.min(3, Math.floor((day - 1) / 7.5));
    var wrap = h('div', 'p30', null, box), hd = h('div', 'p30-hd', null, wrap);
    h('h4', null, t('p30_h'), hd); h('span', null, t('p30_day', { n: day }) + ' · ' + t('p30_done', { a: done, b: total }), hd);
    var bar = h('i', 'p30-bar', null, wrap), u = h('u', null, null, bar); u.style.width = Math.round(done / Math.max(1, total) * 100) + '%';
    weeks.forEach(function (w, wi) {
      var dn = w.filter(function (x) { return st.done[x.id]; }).length;
      var wk = fold(wrap, 'p30-w' + (wi === cur ? ' now' : ''), wi === cur, function (s) { h('b', null, t('p30_w', { n: wi + 1 }), s); h('em', null, dn + '/' + w.length, s); });
      w.forEach(function (x) {
        var lb = h('label', 'p30-i' + (st.done[x.id] ? ' on' : ''), null, wk), cb = h('input', null, null, lb); cb.type = 'checkbox'; cb.checked = !!st.done[x.id];
        var sp = h('span', null, null, lb); if (x.pre) h('em', null, x.pre + ': ', sp); sp.appendChild(document.createTextNode(gTxt(x.t)));
        if (x.g && guideById(x.g)) { var gb = h('button', 'p30-g', t('mp_read'), lb); gb.type = 'button'; gb.addEventListener('click', function (e) { e.preventDefault(); openGuide(guideById(x.g)); }); }
        cb.addEventListener('change', function () { var s2 = p30Get(uid); s2.done = s2.done || {}; if (cb.checked) s2.done[x.id] = 1; else delete s2.done[x.id]; p30Set(uid, s2); renderMyPlan(); });
      });
    });
    var rs = h('button', 'g-link p30-rs', t('p30_reset'), wrap); rs.type = 'button';
    rs.addEventListener('click', function () { p30Set(uid, { start: Date.now(), done: {} }); renderMyPlan(); });
  }

  /* ---------- Progress ---------- */
  var baSide = 'front';
  function renderProgress() {
    var box = $('#pg'); if (!box) return;
    box.innerHTML = '';
    faceBar(box);
    var hd = h('div', 'mp-hd', null, box), ht = h('div', null, null, hd); h('span', 'eyebrow', t('pg_eb'), ht); h('h3', null, t('pg_h'), ht);
    var uid = proUid(), fid = uid ? faceSel(uid) : 'me', a = uid ? histGet(uid).filter(function (x) { return x.f === fid; }) : [];
    if (!a.length) { h('p', 'mp-empty', t('pg_none'), box); return; }
    if (!PRO) { var lk = h('div', 'mp-lock', null, box); h('p', null, t('pg_lock', { n: a.length }), lk); lockBtn(lk, t('mp_unlock')); return; }
    var sides = [['front', 'pg_front'], ['profile', 'pg_prof']];
    var sum = h('div', 'pg-sum', null, box);
    sides.forEach(function (s) {
      var xs = a.filter(function (x) { return x.k === s[0]; }); if (!xs.length) return;
      var f = xs[0], l = xs[xs.length - 1], d = Math.round((l.p - f.p) * 10) / 10, c = h('div', 'pg-c', null, sum);
      h('span', null, t(s[1]), c); h('b', null, fmt(l.p, 1) + '/8', c);
      h('em', d > 0 ? 'up' : d < 0 ? 'dn' : '', xs.length > 1 ? (d === 0 ? t('pg_same') : (d > 0 ? '+' : '') + fmt(d, 1)) + ' · ' + t('pg_first') + ' ' + fmt(f.p, 1) : t('pg_scans', { n: xs.length }), c);
    });
    if (a.length < 2) h('p', 'mp-empty', t('pg_one'), box);
    else { drawChart(box, a, sides); changes(box, a); }
    /* before / after */
    var ba = h('div', 'ba', null, box), bh = h('div', 'ba-hd', null, ba); h('h4', null, t('ba_h'), bh);
    var tg = h('div', 'ba-tg', null, bh);
    sides.forEach(function (s) { var b = h('button', baSide === s[0] ? 'on' : '', t(s[1]), tg); b.type = 'button'; b.addEventListener('click', function () { baSide = s[0]; renderProgress(); }); });
    var bb = h('div', 'ba-b', null, ba); h('p', 'mp-empty', '…', bb);
    phList(uid, fid, baSide).then(function (ps) { drawBA(bb, ps); });
    var all = fold(box, 'pg-all', false, function (s) { h('b', null, t('pg_all', { n: a.length }), s); });
    var ul = h('ul', 'pg-list', null, all);
    a.slice().reverse().forEach(function (x) { var li = h('li', null, null, ul); h('span', null, proDate(x.t), li); h('em', null, t(x.k === 'front' ? 'pg_front' : 'pg_prof'), li); h('b', null, fmt(x.p, 1) + '/8' + (x.s != null ? ' · ' + x.s + '/100' : ''), li); });
    h('p', 'tips', t('pg_tip'), box);
  }
  /* per measurement: first scan → latest scan of the same side, closer to or further from the usual range */
  function changes(box, a) {
    var rows = [];
    ['front', 'profile'].forEach(function (k) {
      var xs = a.filter(function (x) { return x.k === k && x.it && x.it.length; }); if (xs.length < 2) return;
      var f = {}, l = {}; xs[0].it.forEach(function (i) { f[i.key] = i; }); xs[xs.length - 1].it.forEach(function (i) { l[i.key] = i; });
      Object.keys(l).forEach(function (key) {
        var d = GL.DEFS[key]; if (!d || !f[key]) return;
        var half = (d.hi - d.lo) / 2 || 1, d0 = Math.abs(f[key].value - d.ideal) / half, d1 = Math.abs(l[key].value - d.ideal) / half, ch = d0 - d1;
        if (Math.abs(ch) < 0.08) return;
        rows.push({ key: key, v0: f[key].value, v1: l[key].value, ch: ch });
      });
    });
    var box2 = fold(box, 'pg-ch', false, function (s) { h('b', null, t('ch_h'), s); h('em', null, rows.length ? t('ch_n', { n: rows.length }) : t('ch_0'), s); });
    var b = h('div', 'fx-b', null, box2);
    if (!rows.length) { h('p', 'mp-empty', t('ch_none'), b); return; }
    rows.sort(function (x, y) { return Math.abs(y.ch) - Math.abs(x.ch); }).slice(0, 10).forEach(function (r) {
      var li = h('div', 'ch-r ' + (r.ch > 0 ? 'up' : 'dn'), null, b);
      h('b', null, t('m_' + r.key + '_name'), li); h('span', null, valStr(r.key, r.v0) + ' → ' + valStr(r.key, r.v1), li); h('em', null, t(r.ch > 0 ? 'ch_better' : 'ch_worse'), li);
    });
    h('p', 'tips', t('ch_note'), b);
  }
  function drawChart(box, a, sides) {
    var W0 = 600, H0 = 240, L0 = 44, R0 = 14, T0 = 16, B0 = 38, ps = a.map(function (x) { return x.p; });
    var lo = Math.min.apply(null, ps), hi = Math.max.apply(null, ps), mid = (lo + hi) / 2, span = Math.max(1, hi - lo + 0.4);
    lo = Math.max(0, mid - span / 2); hi = Math.min(8, lo + span); lo = Math.max(0, hi - span);
    var t0 = a[0].t, t1 = a[a.length - 1].t, X = function (i, x) { return L0 + (t1 > t0 ? (x.t - t0) / (t1 - t0) : i / Math.max(1, a.length - 1)) * (W0 - L0 - R0); }, Y = function (p) { return T0 + (1 - (p - lo) / (hi - lo)) * (H0 - T0 - B0); };
    var svg = sv('svg', { viewBox: '0 0 ' + W0 + ' ' + H0, 'class': 'pg-svg', role: 'img', 'aria-label': t('pg_h') }, box);
    for (var g = 0; g <= 4; g++) { var gv = lo + (hi - lo) * g / 4, gy = Y(gv); sv('line', { x1: L0, x2: W0 - R0, y1: gy, y2: gy, 'class': 'pg-grid' }, svg); var tl = sv('text', { x: L0 - 6, y: gy + 5, 'class': 'pg-ax', 'text-anchor': 'end' }, svg); tl.textContent = fmt(gv, 1); }
    sides.forEach(function (s, si) {
      var pts = []; a.forEach(function (x, i) { if (x.k === s[0]) pts.push([X(i, x), Y(x.p)]); }); if (!pts.length) return;
      if (pts.length > 1) sv('polyline', { points: pts.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' '), 'class': 'pg-ln s' + si }, svg);
      pts.forEach(function (p) { sv('circle', { cx: p[0], cy: p[1], r: 4.5, 'class': 'pg-pt s' + si }, svg); });
    });
    [[a[0], 'start'], [a[a.length - 1], 'end']].forEach(function (q) { var dt = new Date(q[0].t), tx = sv('text', { x: q[1] === 'start' ? L0 : W0 - R0, y: H0 - 8, 'class': 'pg-ax', 'text-anchor': q[1] }, svg); tx.textContent = ('0' + dt.getDate()).slice(-2) + '.' + ('0' + (dt.getMonth() + 1)).slice(-2) + '.' + dt.getFullYear(); });
    var lg = h('div', 'pg-lg', null, box); sides.forEach(function (s, si) { if (a.some(function (x) { return x.k === s[0]; })) { var it = h('span', 's' + si, null, lg); h('i', null, null, it); it.appendChild(document.createTextNode(t(s[1]))); } });
  }
  /* before/after: two photos of the same face with a draggable divider */
  function drawBA(bb, ps) {
    bb.innerHTML = '';
    if (ps.length < 2) { h('p', 'mp-empty', t(ps.length ? 'ba_one' : 'ba_none'), bb); return; }
    var ia = 0, ib = ps.length - 1;
    var sel = h('div', 'ba-sel', null, bb);
    function pick(lbl, cur, fn) { var w = h('label', null, null, sel); h('span', null, lbl, w); var s = h('select', null, null, w); ps.forEach(function (p, i) { var o = h('option', null, proDate(p.t), s); o.value = String(i); if (i === cur) o.selected = true; }); s.addEventListener('change', function () { fn(+s.value); }); }
    var view = h('div', 'ba-v', null, bb), A = h('img', 'ba-a', null, view), Bw = h('div', 'ba-bw', null, view), B = h('img', 'ba-bi', null, Bw), ln = h('i', 'ba-ln', null, view);
    A.alt = t('ba_before'); B.alt = t('ba_after');
    var la = h('span', 'ba-l a', null, view), lb = h('span', 'ba-l b', null, view);
    var rg = h('input', 'ba-r', null, bb); rg.type = 'range'; rg.min = '0'; rg.max = '100'; rg.value = '50'; rg.setAttribute('aria-label', t('ba_h'));
    function set(v) { Bw.style.clipPath = 'inset(0 0 0 ' + v + '%)'; ln.style.left = v + '%'; }
    function paint() { A.src = ps[ia].img; B.src = ps[ib].img; la.textContent = t('ba_before') + ' · ' + proDate(ps[ia].t); lb.textContent = t('ba_after') + ' · ' + proDate(ps[ib].t); }
    pick(t('ba_before'), ia, function (i) { ia = i; paint(); }); pick(t('ba_after'), ib, function (i) { ib = i; paint(); });
    rg.addEventListener('input', function () { set(+rg.value); });
    function drag(e) { var r = view.getBoundingClientRect(), x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left; var v = clamp(x / r.width * 100, 0, 100); rg.value = String(Math.round(v)); set(v); }
    view.addEventListener('pointerdown', function (e) { drag(e); view.setPointerCapture && view.setPointerCapture(e.pointerId); var mv = function (ev) { drag(ev); }, up = function () { view.removeEventListener('pointermove', mv); view.removeEventListener('pointerup', up); }; view.addEventListener('pointermove', mv); view.addEventListener('pointerup', up); });
    paint(); set(50);
    h('p', 'tips', t('ba_note'), bb);
  }

  /* ---------- report picture (1080 x 1350) ---------- */
  function makeReport(fid, btn) {
    var uid = proUid(); if (!uid) return;
    var D = faceData(fid), fc = faceById(uid, fid); if (!D.front && !D.profile) return;
    if (btn) btn.disabled = true;
    phList(uid, fid, 'front').then(function (ps) {
      var src = ps.length ? ps[ps.length - 1].img : (fc && fc.th) || null;
      return new Promise(function (ok) { if (!src) return ok(null); var im = new Image(); im.onload = function () { ok(im); }; im.onerror = function () { ok(null); }; im.src = src; });
    }).then(function (im) {
      var W = 1080, H = 1350, c = document.createElement('canvas'); c.width = W; c.height = H; var x = c.getContext('2d');
      var g = x.createRadialGradient(W * 0.8, -100, 50, W * 0.8, -100, 1100); g.addColorStop(0, '#2a2a2a'); g.addColorStop(1, '#070707'); x.fillStyle = g; x.fillRect(0, 0, W, H);
      var F = '"Manrope","Inter",system-ui,sans-serif';
      x.fillStyle = '#fff'; x.font = '800 40px ' + F; x.fillText('Glow Lab', 80, 110);
      x.fillStyle = '#8a8a8a'; x.font = '600 28px ' + F; x.textAlign = 'right'; x.fillText(proDate(Date.now()), W - 80, 110); x.textAlign = 'left';
      if (im) { x.save(); x.beginPath(); x.arc(220, 330, 140, 0, Math.PI * 2); x.clip(); x.drawImage(im, 80, 190, 280, 280); x.restore(); x.strokeStyle = 'rgba(255,255,255,.85)'; x.lineWidth = 4; x.beginPath(); x.arc(220, 330, 146, 0, Math.PI * 2); x.stroke(); }
      var nx = im ? 420 : 80;
      x.fillStyle = '#9a9a9a'; x.font = '700 26px ' + F; x.fillText((faceName(fc) || '').toUpperCase(), nx, 230);
      var e = D.front || D.profile;
      x.fillStyle = '#fff'; x.font = '800 150px ' + F; x.fillText(fmt(e.p, 1), nx, 380); var w1 = x.measureText(fmt(e.p, 1)).width;
      x.fillStyle = '#8a8a8a'; x.font = '700 48px ' + F; x.fillText('/8', nx + w1 + 10, 380);
      x.fillStyle = '#e6e6e6'; x.font = '700 34px ' + F; x.fillText((e.tr ? t('tier_' + e.tr) + ' · ' : '') + t(D.front ? 'pg_front' : 'pg_prof'), nx, 440);
      if (D.front && D.profile) { x.fillStyle = '#9a9a9a'; x.font = '600 28px ' + F; x.fillText(t('pg_prof') + ': ' + fmt(D.profile.p, 1) + '/8', nx, 485); }
      var y = 600;
      function row(k, v) { x.fillStyle = '#8a8a8a'; x.font = '700 24px ' + F; x.fillText(k.toUpperCase(), 80, y); x.fillStyle = '#fff'; x.font = '700 36px ' + F; x.fillText(v.charAt(0).toUpperCase() + v.slice(1), 80, y + 46); y += 112; }
      if (D.sh && SHAPE_DB[D.sh]) row(t('sh_h'), gTxt(SHAPE_DB[D.sh].n));
      if (D.sd) row(t('sd_h'), t('sd_' + D.sd.k));
      var str = (D.items || []).filter(function (i) { return i.status === 'ok'; }).sort(function (a, b) { return a.closeness - b.closeness; }).slice(0, 3);
      var wk = planWeak(D.items).slice(0, 3);
      function list(title, arr, mark) { x.fillStyle = '#8a8a8a'; x.font = '700 24px ' + F; x.fillText(title.toUpperCase(), 80, y); y += 50; arr.forEach(function (i) { x.fillStyle = '#fff'; x.font = '600 32px ' + F; x.fillText(mark + '  ' + t('m_' + i.key + '_name'), 80, y); y += 48; }); y += 30; }
      if (str.length) list(t('mp_str'), str, '+');
      if (wk.length) list(t('mp_weak'), wk, '–');
      x.fillStyle = 'rgba(255,255,255,.12)'; x.fillRect(80, H - 140, W - 160, 2);
      x.fillStyle = '#bdbdbd'; x.font = '600 28px ' + F; x.fillText('glow-lub.com', 80, H - 80);
      x.fillStyle = '#6f6f6f'; x.font = '500 22px ' + F; x.textAlign = 'right'; x.fillText(t('rep_note'), W - 80, H - 80); x.textAlign = 'left';
      c.toBlob(function (blob) {
        if (btn) btn.disabled = false; if (!blob) return;
        var nd = new Date(), name = 'glowlab-' + nd.getFullYear() + '-' + ('0' + (nd.getMonth() + 1)).slice(-2) + '-' + ('0' + nd.getDate()).slice(-2) + '.png', file = null;
        try { file = new File([blob], name, { type: 'image/png' }); } catch (er) {}
        if (file && navigator.canShare && navigator.canShare({ files: [file] }) && /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)) { navigator.share({ files: [file], title: 'Glow Lab' }).catch(function () {}); return; }
        var a2 = document.createElement('a'); a2.href = URL.createObjectURL(blob); a2.download = name; document.body.appendChild(a2); a2.click(); setTimeout(function () { URL.revokeObjectURL(a2.href); a2.remove(); }, 2000);
        toast(t('rep_ok'), 'ok', 4000);
      }, 'image/png');
    });
  }
  hooks.push(function () { try { renderMyPlan(); renderProgress(); } catch (e) {} });
