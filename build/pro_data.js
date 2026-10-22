  /* ---------- saved scans, faces and photos, per account ----------
     numbers (history, faces without pictures, checklist) go to the account in Firestore;
     face pictures and before/after photos stay on this device only (the site promises photos are not uploaded) */
  function histGet(uid) { try { var a = JSON.parse(lsGet('gl_hist_' + uid) || '[]'); return Array.isArray(a) ? a.map(function (x) { if (!x.f) x.f = 'me'; return x; }) : []; } catch (e) { return []; } }
  function histSet(uid, a, noCloud) { a.sort(function (x, y) { return x.t - y.t; }); a = a.slice(-60); lsSet('gl_hist_' + uid, JSON.stringify(a)); if (!noCloud) Cloud.push(uid, { hist: a }); return a; }
  function compactItems(items) { return (items || []).map(function (i) { return { key: i.key, value: Math.round(i.value * 1000) / 1000, status: i.status, dir: i.dir, dev: Math.round((i.dev || 0) * 1000) / 1000, closeness: Math.round((i.closeness || 0) * 1000) / 1000 }; }); }
  function facesGet(uid) { try { var a = JSON.parse(lsGet('gl_faces_' + uid) || 'null'); if (Array.isArray(a) && a.length) { if (!a.some(function (f) { return f.id === 'me'; })) a.unshift({ id: 'me', n: '' }); return a; } } catch (e) {} return [{ id: 'me', n: '' }]; }
  function facesSet(uid, a) { lsSet('gl_faces_' + uid, JSON.stringify(a)); Cloud.push(uid, { faces: a.map(function (f) { return { id: f.id, n: f.n || '' }; }) }); }
  function faceName(f) { return f ? (f.id === 'me' && !f.n ? t('fc_me') : f.n) : ''; }
  function faceById(uid, id) { return facesGet(uid).filter(function (f) { return f.id === id; })[0]; }
  function faceSel(uid) { var id = lsGet('gl_fsel_' + uid) || 'me'; return faceById(uid, id) ? id : 'me'; }
  function faceSelSet(uid, id) { lsSet('gl_fsel_' + uid, id); }
  function keepPhotos(uid) { return lsGet('gl_keepph_' + uid) !== '0'; }
  /* square crop around the face, for thumbnails, before/after and the report */
  function faceCrop(img, pn, size) {
    try {
      var iw = img.naturalWidth, ih = img.naturalHeight; if (!iw) return null;
      var cx = iw / 2, cy = ih / 2, side = Math.min(iw, ih);
      if (pn && pn.length) {
        var xs = pn.map(function (q) { return q.x * iw; }), ys = pn.map(function (q) { return q.y * ih; });
        var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
        cx = (x0 + x1) / 2; cy = (y0 + y1) / 2 - 0.1 * (y1 - y0); side = Math.min(Math.min(iw, ih), 1.6 * Math.max(x1 - x0, y1 - y0));
      }
      var sx = clamp(cx - side / 2, 0, iw - side), sy = clamp(cy - side / 2, 0, ih - side);
      var c = document.createElement('canvas'); c.width = c.height = size;
      c.getContext('2d').drawImage(img, sx, sy, side, side, 0, 0, size, size);
      return c.toDataURL('image/jpeg', size > 200 ? 0.82 : 0.78);
    } catch (e) { return null; }
  }
  /* before/after photos: IndexedDB on this device */
  var idbP = null;
  function idb() {
    if (idbP) return idbP;
    idbP = new Promise(function (ok, no) {
      try { var r = indexedDB.open('glowlab', 1); r.onupgradeneeded = function () { if (!r.result.objectStoreNames.contains('ph')) r.result.createObjectStore('ph', { keyPath: 't' }); }; r.onsuccess = function () { ok(r.result); }; r.onerror = function () { no(r.error); }; } catch (e) { no(e); }
    });
    idbP.catch(function () { idbP = null; });
    return idbP;
  }
  function phTx(mode, fn) { return idb().then(function (db) { return new Promise(function (ok, no) { var tx = db.transaction('ph', mode), st = tx.objectStore('ph'), out = fn(st); tx.oncomplete = function () { ok(out && out.result !== undefined ? out.result : out); }; tx.onerror = function () { no(tx.error); }; }); }); }
  function phPut(o) { return phTx('readwrite', function (st) { st.put(o); }).catch(function () {}); }
  function phList(uid, fid, kind) { return phTx('readonly', function (st) { return st.getAll(); }).then(function (a) { return (a || []).filter(function (x) { return x.u === uid && (!fid || x.f === fid) && (!kind || x.k === kind); }).sort(function (x, y) { return x.t - y.t; }); }, function () { return []; }); }
  function phDel(pred) { return phTx('readwrite', function (st) { var r = st.getAll(); r.onsuccess = function () { (r.result || []).forEach(function (x) { if (pred(x)) st.delete(x.t); }); }; }).catch(function () {}); }
  function phMove(t0, fid) { return phTx('readwrite', function (st) { var r = st.get(t0); r.onsuccess = function () { if (r.result) { r.result.f = fid; st.put(r.result); } }; }).catch(function () {}); }

  /* ---------- face shape and best side, from the 478-point mesh (front photo) ---------- */
  function meshPx(lm, aspect) { var W0 = aspect * 1000; return function (i) { return { x: lm[i].x * W0, y: lm[i].y * 1000 }; }; }
  function yawOf(lm, aspect) { try { return window.GM ? Math.abs(GM.align(lm, aspect * 1000, 1000).yawDeg) : 0; } catch (e) { return 0; } }
  /* thresholds calibrated on the mesh: its outline is smoother than a real face, so the ratios sit in a narrow band
     (length/cheeks about 1.13-1.22, jaw/cheeks 0.77-0.84 on test photos) */
  function faceShape(lm, aspect) {
    if (!lm || lm.length < 400 || yawOf(lm, aspect) > 12) return null;
    var P = meshPx(lm, aspect), d = function (a, b) { var p = P(a), q = P(b); return Math.hypot(p.x - q.x, p.y - q.y); };
    var ch = d(234, 454); if (!(ch > 0)) return null;
    var L = d(10, 152) / ch, F = d(103, 332) / ch, J = d(172, 397) / ch, k;
    if (L >= 1.24) k = J >= 0.82 ? 'rect' : 'long';
    else if (F - J >= 0 && J <= 0.78) k = 'heart';
    else if (F <= 0.715 && J <= 0.8) k = 'diamond';
    else if (L <= 1.14) k = J >= 0.82 ? 'square' : 'round';
    else if (J >= 0.835) k = 'square';
    else k = 'oval';
    return { k: k, L: Math.round(L * 1000) / 1000, F: Math.round(F * 1000) / 1000, J: Math.round(J * 1000) / 1000 };
  }
  /* which half of the face looks better on this photo: eye openness, eye tilt, mouth corner and brow height.
     Sides are named as they appear on the photo (a selfie may be mirrored). */
  function bestSide(lm, aspect) {
    if (!lm || lm.length < 400 || yawOf(lm, aspect) > 10) return null;
    var P = meshPx(lm, aspect);
    var a = P(33), b = P(263), roll = Math.atan2(b.y - a.y, b.x - a.x), cs = Math.cos(-roll), sn = Math.sin(-roll), o = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    function R(i) { var p = P(i), x = p.x - o.x, y = p.y - o.y; return { x: x * cs - y * sn, y: x * sn + y * cs }; }
    var S0 = { out: 33, inn: 133, top: 159, bot: 145, brow: 105, mouth: 61 }, S1 = { out: 263, inn: 362, top: 386, bot: 374, brow: 334, mouth: 291 };
    var mc = { y: (R(13).y + R(14).y) / 2 };
    function feat(s) {
      var ew = Math.hypot(R(s.out).x - R(s.inn).x, R(s.out).y - R(s.inn).y) || 1;
      return { open: (R(s.bot).y - R(s.top).y) / ew, tilt: Math.atan2(R(s.inn).y - R(s.out).y, Math.abs(R(s.out).x - R(s.inn).x)) * 180 / Math.PI, mouth: (mc.y - R(s.mouth).y) / ew, brow: (R(s.top).y - R(s.brow).y) / ew };
    }
    var f0 = feat(S0), f1 = feat(S1), lim = function (v) { return Math.max(-2, Math.min(2, v)); };
    var parts = { open: lim((f0.open - f1.open) / 0.03), tilt: lim((f0.tilt - f1.tilt) / 2), mouth: lim((f0.mouth - f1.mouth) / 0.04), brow: lim((f0.brow - f1.brow) / 0.06) };
    var tot = parts.open + parts.tilt + parts.mouth + parts.brow;
    var leftIs0 = R(33).x < R(263).x; /* side 0 is on the left of the photo */
    if (Math.abs(tot) < 1.2) return { k: 'eq', why: [] };
    var win0 = tot > 0, why = Object.keys(parts).filter(function (n) { return win0 ? parts[n] > 0.4 : parts[n] < -0.4; }).sort(function (x, y) { return Math.abs(parts[y]) - Math.abs(parts[x]); });
    return { k: (win0 === leftIs0) ? 'l' : 'r', why: why.slice(0, 3) };
  }

  /* ---------- saving a scan ---------- */
  var lastEntry = null;
  function histAdd(kind, psl, sc, items, ex) {
    var uid = proUid(); if (!uid || !isFinite(psl)) return;
    ex = ex || {};
    var fid = faceSel(uid), e = { t: Date.now(), k: kind, f: fid, p: Math.round(psl * 10) / 10, s: sc || null, tr: ex.tier || null, it: compactItems(items) };
    if (kind === 'front' && ex.lm) { var shp = faceShape(ex.lm, ex.aspect), bs = bestSide(ex.lm, ex.aspect); if (shp) e.sh = shp.k; if (bs) e.sd = bs; }
    var a = histGet(uid); a.push(e); histSet(uid, a);
    lastEntry = e;
    PLAN_CTX.face = fid;
    var big = ex.img ? faceCrop(ex.img, ex.pn, 360) : null, th = ex.img ? faceCrop(ex.img, ex.pn, 96) : null;
    e._th = th;
    if (big && keepPhotos(uid)) phPut({ t: e.t, u: uid, f: fid, k: kind, img: big });
    if (th && kind === 'front') { var fs = facesGet(uid), fc = fs.filter(function (f) { return f.id === fid; })[0]; if (fc && !fc.th) { fc.th = th; facesSet(uid, fs); } }
    if (ex.root) faceChooser(ex.root, e);
    try { renderMyPlan(); renderProgress(); } catch (er) {}
  }
  /* "whose face is this?" under the result: moves the scan to another face or a new one */
  function faceChooser(root, e) {
    var uid = proUid(); if (!uid) return;
    var host = $('.fc', root);
    if (!host) { var anchor = $('.rating', root) || $('.results', root); if (!anchor || !anchor.parentNode) return; host = h('div', 'fc'); anchor.parentNode.insertBefore(host, anchor); }
    function draw(adding) {
      host.innerHTML = '';
      var hd = h('div', 'fc-hd', null, host); h('b', null, t('fc_q'), hd); h('span', null, t('fc_q_sub'), hd);
      var row = h('div', 'fc-row', null, host);
      facesGet(uid).forEach(function (f) {
        var b = h('button', 'fc-chip' + (f.id === e.f ? ' on' : ''), null, row); b.type = 'button';
        faceAv(b, f); h('span', null, faceName(f), b);
        b.addEventListener('click', function () { moveScan(e, f.id); draw(false); });
      });
      if (!adding) {
        var nb = h('button', 'fc-chip add', null, row); nb.type = 'button'; h('i', 'fc-plus', '+', nb); h('span', null, t('fc_new'), nb);
        nb.addEventListener('click', function () { draw(true); });
      } else {
        var fm = h('form', 'fc-new', null, host), inp = h('input', 'ob-in', null, fm); inp.maxLength = 24; inp.placeholder = t('fc_name_ph'); inp.required = true;
        var ok = h('button', 'btn small', t('fc_save'), fm); ok.type = 'submit';
        var cn = h('button', 'g-link', t('fc_cancel'), fm); cn.type = 'button'; cn.addEventListener('click', function () { draw(false); });
        fm.addEventListener('submit', function (ev) {
          ev.preventDefault(); var n = inp.value.trim(); if (!n) return;
          var fs = facesGet(uid), id = 'f' + Date.now().toString(36);
          fs.push({ id: id, n: n, th: e.k === 'front' ? e._th || null : null }); facesSet(uid, fs);
          moveScan(e, id); draw(false);
        });
        setTimeout(function () { try { inp.focus(); } catch (er) {} }, 30);
      }
    }
    draw(false);
  }
  function moveScan(e, fid) {
    var uid = proUid(); if (!uid || e.f === fid) { faceSelSet(uid, fid); return; }
    var a = histGet(uid); a.forEach(function (x) { if (x.t === e.t) x.f = fid; }); histSet(uid, a);
    e.f = fid; phMove(e.t, fid); faceSelSet(uid, fid); PLAN_CTX.face = fid;
    if (e.k === 'front' && e._th) { var fs = facesGet(uid), fc = fs.filter(function (f) { return f.id === fid; })[0]; if (fc && !fc.th) { fc.th = e._th; facesSet(uid, fs); } }
    try { renderMyPlan(); renderProgress(); } catch (er) {}
  }
  function faceAv(parent, f) {
    var s = h('span', 'fc-av', null, parent);
    if (f && f.th) { var im = document.createElement('img'); im.alt = ''; im.src = f.th; s.appendChild(im); }
    else if (f && f.id === 'me') paintAvatar(s, Auth.info());
    else h('b', null, (faceName(f) || '?').slice(0, 1).toUpperCase(), s);
    return s;
  }
  /* the face bar on top of "My plan" and "Progress" */
  function faceBar(box) {
    var uid = proUid(); if (!uid) return;
    var fs = facesGet(uid); if (fs.length < 2) return;
    var sel = faceSel(uid), bar = h('div', 'fb', null, box);
    fs.forEach(function (f) {
      var b = h('button', 'fb-i' + (f.id === sel ? ' on' : ''), null, bar); b.type = 'button'; b.setAttribute('aria-pressed', f.id === sel ? 'true' : 'false');
      faceAv(b, f); h('span', null, faceName(f), b);
      b.addEventListener('click', function () { faceSelSet(uid, f.id); renderMyPlan(); renderProgress(); });
    });
  }
  /* data of one face: the session scan if it belongs to this face, otherwise the latest saved scans */
  function faceData(fid) {
    var uid = proUid(), out = { items: null, front: null, profile: null, sh: null, sd: null };
    var a = uid ? histGet(uid).filter(function (x) { return x.f === fid; }) : [];
    ['front', 'profile'].forEach(function (k) { var xs = a.filter(function (x) { return x.k === k; }); if (xs.length) out[k] = xs[xs.length - 1]; });
    var src = {};
    if (PLAN_CTX.items && PLAN_CTX.face === fid) { src.front = PLAN_CTX.items.front; src.profile = PLAN_CTX.items.profile; }
    ['front', 'profile'].forEach(function (k) { if (!src[k] && out[k] && out[k].it) src[k] = out[k].it; });
    if (!src.front && !src.profile && fid === 'me' && uid) { var l = lastGet(uid); if (l) { src.front = l.front; src.profile = l.profile; } }
    var items = [];
    ['front', 'profile'].forEach(function (k) { (src[k] || []).forEach(function (i) { if (i && GL.DEFS[i.key]) items.push(Object.assign({ side: k }, i)); }); });
    out.items = items.length ? items : null;
    if (out.front) { out.sh = out.front.sh || null; out.sd = out.front.sd || null; }
    return out;
  }
  function lastGet(uid) { try { return JSON.parse(lsGet('gl_last_' + uid) || 'null'); } catch (e) { return null; } }
  function lastSave() {} /* kept for the analysis hook: the latest numbers now live in the scan history */
  function p30Get(uid) { try { return JSON.parse(lsGet('gl_p30_' + uid) || 'null') || {}; } catch (e) { return {}; } }
  function p30Set(uid, o) { lsSet('gl_p30_' + uid, JSON.stringify(o)); Cloud.push(uid, { p30: o }); }
  /* merge what the account has in the cloud (another device) into this device */
  function proMerge(uid, r) {
    if (!r) return;
    if (Array.isArray(r.hist)) { var seen = {}, a = histGet(uid).concat(r.hist).filter(function (x) { var k = x && x.t + x.k; if (!x || seen[k]) return false; seen[k] = 1; return true; }); histSet(uid, a, true); }
    if (Array.isArray(r.faces)) { var loc = facesGet(uid); r.faces.forEach(function (f) { var m = loc.filter(function (x) { return x.id === f.id; })[0]; if (m) { if (f.n && !m.n) m.n = f.n; } else loc.push({ id: f.id, n: f.n || '' }); }); lsSet('gl_faces_' + uid, JSON.stringify(loc)); }
    if (r.p30 && !lsGet('gl_p30_' + uid)) lsSet('gl_p30_' + uid, JSON.stringify(r.p30));
    if (typeof r.av === 'string' && r.av.indexOf('data:image/') === 0) lsSet('gl_av_' + uid, r.av);
    if (r.set && typeof r.set === 'object') lsSet('gl_set_' + uid, JSON.stringify(r.set));
    try { applySettings(); acctPaint(); paintAcctPane(); } catch (e) {}
    try { renderMyPlan(); renderProgress(); } catch (e) {}
  }
