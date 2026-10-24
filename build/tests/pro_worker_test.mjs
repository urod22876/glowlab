// node pro_worker_test.mjs <worker.js>: /api/pro and /api/portal against a fake Google key server and a fake Dodo API
import { pathToFileURL } from 'url';
const W = (await import(pathToFileURL(process.argv[2]).href)).default;
const enc = (o) => Buffer.from(typeof o === 'string' ? o : JSON.stringify(o)).toString('base64url');
const kp = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
const pub = await crypto.subtle.exportKey('jwk', kp.publicKey);
const kp2 = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
async function tok(claims, key = kp.privateKey, kid = 'k1') {
  const now = Math.floor(Date.now() / 1000);
  const c = Object.assign({ iss: 'https://securetoken.google.com/glowlab-e39b2', aud: 'glowlab-e39b2', iat: now - 10, exp: now + 3000, sub: 'uidA', email: 'a@x.com', email_verified: true }, claims);
  const h = enc({ alg: 'RS256', kid, typ: 'JWT' }) + '.' + enc(c);
  const sig = Buffer.from(await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(h))).toString('base64url');
  return h + '.' + sig;
}
const future = new Date(Date.now() + 20 * 864e5).toISOString(), past = new Date(Date.now() - 2 * 864e5).toISOString();
let SUBS = [], CUST = [], calls = [];
globalThis.fetch = async (url, init = {}) => {
  url = String(url); calls.push((init.method || 'GET') + ' ' + url);
  if (url.startsWith('https://glowlab-e39b2.firebaseapp.com/')) return new Response('firebase:' + new URL(url).pathname + new URL(url).search, { status: 200, headers: { 'x-test': '1' } });
  if (url.startsWith('https://www.googleapis.com/')) return new Response(JSON.stringify({ keys: [Object.assign({ kid: 'k1', alg: 'RS256', use: 'sig' }, pub)] }), { headers: { 'cache-control': 'public, max-age=20000' } });
  if (url.startsWith('https://api.anthropic.com/')) { const b = JSON.parse(init.body); return Response.json({ content: [{ type: 'text', text: (/^You are "Glow ?Lab Assistant", a friendly/.test(b.system) ? 'GENERAL' : 'SITE') + ':' + b.max_tokens + ':' + b.messages.length }] }); }
  if (url.startsWith('https://generativelanguage.googleapis.com/')) {
    const k = init.headers['x-goog-api-key'];
    if (k === 'BAD') return new Response(JSON.stringify({ error: { message: 'API key not valid. Please pass a valid API key.' } }), { status: 400 });
    const bd = JSON.parse(init.body), mdl = url.split('/models/')[1].split(':')[0];
    globalThis.__g = (globalThis.__g || []).concat([mdl + ':' + ((bd.generationConfig.thinkingConfig || {}).thinkingLevel || '-')]);
    if (k === 'SLOW' && mdl === 'slow-model') return new Response(JSON.stringify({ error: { message: 'Resource exhausted' } }), { status: 429 });
    if (k === 'NOTHINK' && bd.generationConfig.thinkingConfig) return new Response(JSON.stringify({ error: { message: 'thinking_level is not supported for this model' } }), { status: 400 });
    if (k === 'EMPTY') return Response.json({ candidates: [{ finishReason: 'MAX_TOKENS', content: { parts: [{ thought: true, text: 'thinking...' }] } }] });
    return Response.json({ candidates: [{ content: { parts: [{ thought: true, text: 'hidden' }, { text: 'Gemini ok' }] } }] });
  }
  const u = new URL(url);
  if (init.headers.authorization !== 'Bearer KEY') return new Response('{}', { status: 401 });
  if (u.pathname === '/customers') return Response.json({ items: CUST.filter((c) => c.email === u.searchParams.get('email')) });
  if (u.pathname === '/subscriptions') {
    const cid = u.searchParams.get('customer_id');
    return Response.json({ items: cid ? SUBS.filter((s) => s.customer.customer_id === cid) : SUBS });
  }
  const m = u.pathname.match(/^\/customers\/([^/]+)\/customer-portal\/session$/);
  if (m && init.method === 'POST') return Response.json({ link: 'https://portal.example/' + m[1] + '?back=' + u.searchParams.get('return_url') });
  return new Response('{}', { status: 404 });
};
const env = { DODO_API_KEY: 'KEY', DODO_MODE: 'test', ASSETS: { fetch: () => new Response('asset') } };
async function call(path, t, e = env, origin = 'https://glow-lub.com') {
  const r = await W.fetch(new Request('https://glow-lub.com' + path, { method: 'POST', headers: Object.assign({ origin }, t ? { authorization: 'Bearer ' + t } : {}) }), e);
  return [r.status, await r.json()];
}
let fails = 0;
function check(name, got, want) { const ok = JSON.stringify(got) === JSON.stringify(want); if (!ok) fails++; console.log(ok ? 'ok  ' : 'FAIL', name, ok ? '' : JSON.stringify(got) + ' != ' + JSON.stringify(want)); }
const cA = { customer_id: 'cus_A', email: 'a@x.com', name: 'A' };
const sub = (o) => Object.assign({ subscription_id: 's', product_id: 'pdt_1', status: 'active', next_billing_date: future, cancel_at_next_billing_date: false, metadata: {}, customer: cA }, o);

check('owner free pro', await call('/api/pro', await tok({ email: 'Owner@x.com' }), { PRO_EMAILS: 'owner@x.com, t@y.com', ASSETS: env.ASSETS }), [200, { pro: true, until: null, renews: true }]);
check('owner unverified email refused', await call('/api/pro', await tok({ email: 'owner@x.com', email_verified: false }), { PRO_EMAILS: 'owner@x.com', ASSETS: env.ASSETS }), [501, { error: 'not_configured' }]);
check('owner list, other user', await call('/api/pro', await tok({ email: 'z@x.com' }), Object.assign({}, env, { PRO_EMAILS: 'owner@x.com' })), [200, { pro: false, until: null, renews: false }]);
check('no token', await call('/api/pro', null), [401, { error: 'auth' }]);
check('not configured', await call('/api/pro', await tok({}), { ASSETS: env.ASSETS }), [501, { error: 'not_configured' }]);
check('wrong origin', await call('/api/pro', await tok({}), env, 'https://evil.com'), [403, { error: 'origin' }]);
check('bad signature', await call('/api/pro', await tok({}, kp2.privateKey)), [401, { error: 'auth' }]);
check('wrong project', await call('/api/pro', await tok({ aud: 'other' })), [401, { error: 'auth' }]);
check('expired', await call('/api/pro', await tok({ exp: Math.floor(Date.now() / 1000) - 100 })), [401, { error: 'auth' }]);
check('free user', await call('/api/pro', await tok({})), [200, { pro: false, until: null, renews: false }]);
CUST = [cA]; SUBS = [sub({})];
check('active by email', await call('/api/pro', await tok({})), [200, { pro: true, until: future, renews: true }]);
SUBS = [sub({ cancel_at_next_billing_date: true })];
check('cancelling, still paid', await call('/api/pro', await tok({})), [200, { pro: true, until: future, renews: false }]);
SUBS = [sub({ status: 'cancelled', next_billing_date: future })];
check('cancelled, period left', await call('/api/pro', await tok({})), [200, { pro: true, until: future, renews: false }]);
SUBS = [sub({ status: 'cancelled', next_billing_date: past })];
check('cancelled, period over', await call('/api/pro', await tok({})), [200, { pro: false, until: null, renews: false }]);
SUBS = [sub({ status: 'on_hold' })];
check('payment failed (on hold)', await call('/api/pro', await tok({})), [200, { pro: false, until: null, renews: false }]);
SUBS = [sub({})];
check('other product filtered', await call('/api/pro', await tok({}), Object.assign({}, env, { DODO_PRODUCT_IDS: 'pdt_9' })), [200, { pro: false, until: null, renews: false }]);
check('other user, same db', await call('/api/pro', await tok({ sub: 'uidB', email: 'b@x.com' })), [200, { pro: false, until: null, renews: false }]);
SUBS = [sub({ customer: { customer_id: 'cus_C', email: 'c@other.com' }, metadata: { uid: 'uidB' } })]; CUST = [];
check('paid with another email, matched by uid', await call('/api/pro', await tok({ sub: 'uidB', email: 'b@x.com' })), [200, { pro: true, until: future, renews: true }]);
check('portal link', await call('/api/portal', await tok({ sub: 'uidB', email: 'b@x.com' })), [200, { link: 'https://portal.example/cus_C?back=https://glow-lub.com/#account' }]);
check('portal for free user', await call('/api/portal', await tok({ sub: 'uidZ', email: 'z@x.com' })), [404, { error: 'no_customer' }]);
check('bad dodo key', await call('/api/pro', await tok({}), Object.assign({}, env, { DODO_API_KEY: 'WRONG' })), [502, { error: 'dodo_key' }]);
calls = []; await call('/api/pro', await tok({}), Object.assign({}, env, { DODO_MODE: undefined }));
check('live base by default', calls.filter((c) => c.includes('dodopayments')).every((c) => c.includes('https://live.dodopayments.com/')), true);
const r = await W.fetch(new Request('https://glow-lub.com/index.html'), env); check('assets', await r.text(), 'asset');
const g = await W.fetch(new Request('https://glow-lub.com/api/pro'), env); check('GET refused', g.status, 405);
async function chat(t, n = 1) {
  const msgs = []; for (let i = 0; i < n; i++) msgs.push({ role: i % 2 ? 'assistant' : 'user', content: 'q' + i });
  const r = await W.fetch(new Request('https://glow-lub.com/api/assistant', { method: 'POST', headers: Object.assign({ origin: 'https://glow-lub.com', 'content-type': 'application/json' }, t ? { authorization: 'Bearer ' + t } : {}), body: JSON.stringify({ messages: msgs, lang: 'ru' }) }), { ANTHROPIC_API_KEY: 'A', ASSETS: env.ASSETS });
  return [r.status, (await r.json()).reply];
}
check('assistant visitor = site help', await chat(null), [200, 'SITE:400:1']);
check('assistant signed in = general', await chat(await tok({})), [200, 'GENERAL:1200:1']);
check('assistant forged token = site help', await chat(await tok({}, kp2.privateKey)), [200, 'SITE:400:1']);
check('assistant longer memory when signed in', await chat(await tok({}), 21), [200, 'GENERAL:1200:13']);
async function gchat(key) {
  const r = await W.fetch(new Request('https://glow-lub.com/api/assistant', { method: 'POST', headers: { origin: 'https://glow-lub.com', 'content-type': 'application/json' }, body: JSON.stringify({ messages: [{ role: 'user', content: 'hi' }], lang: 'ru' }) }), { GEMINI_API_KEY: key, ASSETS: env.ASSETS });
  return [r.status, await r.json()];
}
{ globalThis.__g = []; const r = await W.fetch(new Request('https://glow-lub.com/api/assistant', { method: 'POST', headers: { origin: 'https://glow-lub.com' }, body: JSON.stringify({ messages: [{ role: 'user', content: 'hi' }] }) }), { GEMINI_API_KEY: 'SLOW', GEMINI_MODEL: 'slow-model', ASSETS: env.ASSETS });
  check('gemini rate limit -> fallback model', [r.status, (await r.json()).reply, globalThis.__g], [200, 'Gemini ok', ['slow-model:low', 'gemini-3.6-flash:low']]); }
{ globalThis.__g = []; const r = await W.fetch(new Request('https://glow-lub.com/api/assistant', { method: 'POST', headers: { origin: 'https://glow-lub.com' }, body: JSON.stringify({ messages: [{ role: 'user', content: 'hi' }] }) }), { GEMINI_API_KEY: 'NOTHINK', GEMINI_MODEL: 'm1', ASSETS: env.ASSETS });
  check('thinking setting refused -> retry without it', [r.status, (await r.json()).reply, globalThis.__g], [200, 'Gemini ok', ['m1:low', 'm1:-']]); }
check('gemini answer (thoughts hidden)', await gchat('GOOD'), [200, { reply: 'Gemini ok' }]);
check('gemini bad key', await gchat('BAD'), [502, { error: 'upstream' }]);
check('gemini empty', await gchat('EMPTY'), [502, { error: 'empty' }]);
{ const r = await W.fetch(new Request('https://glow-lub.com/api/diag'), { GEMINI_API_KEY: 'BAD', GEMINI_MODEL: 'gemini-x', DODO_API_KEY: 'KEY', DODO_MODE: 'test', PRO_EMAILS: 'a@b.c', ASSETS: env.ASSETS }); const j = await r.json();
  check('diag', [j.gemini.key_set, j.gemini.model, j.gemini.ok, j.gemini.models.length, j.gemini.models.every((m) => m.status === 400 && /API key not valid/.test(m.detail)), j.dodo.ok, j.pro_emails, JSON.stringify(j).includes('BAD')], [true, 'gemini-x', false, 4, true, true, 1, false]); }
{ const r = await W.fetch(new Request('https://glow-lub.com/__/auth/handler?apiKey=x&mode=signIn'), env); check('auth proxy', [r.status, await r.text(), r.headers.get('x-test')], [200, 'firebase:/__/auth/handler?apiKey=x&mode=signIn', '1']); }
{ const r = await W.fetch(new Request('https://glow-lub.com/__/firebase/init.json'), env); check('firebase init proxy', await r.text(), 'firebase:/__/firebase/init.json'); }
console.log(fails ? fails + ' FAILED' : 'all passed');
