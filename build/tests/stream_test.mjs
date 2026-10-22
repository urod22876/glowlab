// node stream_test.mjs <worker.js>: streaming answers, model switching on overload / silence
import { pathToFileURL } from 'url';
const W = (await import(pathToFileURL(process.argv[2]).href)).default;
const enc = new TextEncoder(); let calls = [];
function sse(chunks, delayMs, signal) {
  return new ReadableStream({ async start(c) {
    for (const t of chunks) { await new Promise((r) => setTimeout(r, delayMs)); if (signal && signal.aborted) { c.error(new DOMException('aborted', 'AbortError')); return; }
      c.enqueue(enc.encode('data: ' + JSON.stringify({ candidates: [{ content: { parts: t === '#think' ? [{ thought: true, text: 'hmm' }] : [{ text: t }] } }] }) + '\r\n\r\n')); }
    c.close(); } });
}
globalThis.fetch = async (url, init = {}) => {
  url = String(url); const m = url.split('/models/')[1].split(':')[0]; calls.push(m + (url.includes('stream') ? ':s' : ':n'));
  if (m === 'busy') return new Response(JSON.stringify({ error: { message: 'This model is currently experiencing high demand.' } }), { status: 503 });
  if (m === 'silent') return new Response(new ReadableStream({ start(c) { init.signal.addEventListener('abort', () => c.error(new DOMException('aborted', 'AbortError'))); } }), { status: 200 });
  return new Response(sse(['#think', 'Привет', ', это', ' ответ.'], 20, init.signal), { status: 200 });
};
const env = { GEMINI_API_KEY: 'K', ASSETS: { fetch: () => new Response('') } };
async function ask(e) {
  const t0 = Date.now(), r = await W.fetch(new Request('https://glow-lub.com/api/assistant', { method: 'POST', headers: { origin: 'https://glow-lub.com' }, body: JSON.stringify({ messages: [{ role: 'user', content: 'hi' }], stream: true }) }), Object.assign({}, env, e));
  const reader = r.body.getReader(), dec = new TextDecoder(); let txt = '', parts = 0, firstMs = null;
  for (;;) { const { done, value } = await reader.read(); if (done) break; if (firstMs == null) firstMs = Date.now() - t0; txt += dec.decode(value, { stream: true }); parts++; }
  return { status: r.status, type: r.headers.get('content-type'), model: r.headers.get('x-model'), txt, parts, firstMs, total: Date.now() - t0 };
}
let fails = 0; const check = (n, ok, info) => { if (!ok) fails++; console.log(ok ? 'ok  ' : 'FAIL', n, ok ? '' : JSON.stringify(info)); };
calls = []; let a = await ask({ GEMINI_MODEL: 'good' });
check('streams in pieces, thoughts hidden', a.status === 200 && a.txt === 'Привет, это ответ.' && a.parts >= 2 && a.model === 'good' && calls[0] === 'good:s', a);
calls = []; a = await ask({ GEMINI_MODEL: 'busy', GEMINI_FALLBACK: 'good' });
check('overloaded model -> next model', a.txt === 'Привет, это ответ.' && a.model === 'good' && calls.join() === 'busy:s,good:s', { a, calls });
calls = []; a = await ask({ GEMINI_MODEL: 'busy', GEMINI_FALLBACK: 'good' });
check('overloaded model rested next time', calls[0] === 'good:s', calls);
calls = []; const t0 = Date.now(); a = await ask({ GEMINI_MODEL: 'silent', GEMINI_FALLBACK: 'good' });
check('silent model abandoned after ~12 s', a.model === 'good' && a.total < 14000 && a.total > 11000, { a, calls });
calls = []; { const r = await W.fetch(new Request('https://glow-lub.com/api/assistant', { method: 'POST', headers: { origin: 'https://glow-lub.com' }, body: JSON.stringify({ messages: [{ role: 'user', content: 'hi' }], stream: true }) }), Object.assign({}, env, { GEMINI_MODEL: 'busy2', GEMINI_FALLBACK: 'busy' })); }
globalThis.fetch = async () => new Response(JSON.stringify({ error: { message: 'API key not valid' } }), { status: 400 });
{ const r = await W.fetch(new Request('https://glow-lub.com/api/assistant', { method: 'POST', headers: { origin: 'https://glow-lub.com' }, body: JSON.stringify({ messages: [{ role: 'user', content: 'hi' }], stream: true }) }), Object.assign({}, env, { GEMINI_MODEL: 'x' }));
  check('bad key -> json error, no endless tries', r.status === 502 && (r.headers.get('content-type') || '').includes('json'), r.status); }
console.log(fails ? fails + ' FAILED' : 'all passed');
