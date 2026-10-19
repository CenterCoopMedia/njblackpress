import test from 'node:test';
import assert from 'node:assert/strict';
import worker from './worker.mjs';

const body = { request_id: 'a'.repeat(32), url: 'https://centercoopmedia.github.io/njblackpress/publication.html?id=69',
  title: 'The Cricket', description: 'The founding date needs a cited correction.', suggested_fix: '', source_url: '', website: '' };
const env = { REPORT_LIMITER: { limit: async () => ({ success: true }) }, BLACKPRESS_REPORT_INTAKE_SECRET: 'test-intake',
  ACCESS_CLIENT_ID: 'test-client', ACCESS_CLIENT_SECRET: 'test-access' };
const request = (data = body, origin = 'https://centercoopmedia.github.io') => new Request('https://corrections.example/report', {
  method: 'POST', headers: { 'Content-Type': 'application/json', Origin: origin }, body: JSON.stringify(data),
});

test('the relay confirms only the exact durable receipt and keeps secrets server-side', async () => {
  const original = globalThis.fetch;
  const received = [];
  globalThis.fetch = async (url, options) => {
    received.push(JSON.parse(options.body));
    assert.equal(url, 'https://pi.amditis.tech/api/njpbs/blackpress/report');
    assert.equal(options.headers.Authorization, 'Bearer test-intake');
    assert.equal(options.redirect, 'manual');
    return Response.json({ success: true, id: 'bp_' + body.request_id });
  };
  try {
    const response = await worker.fetch(request(), env);
    assert.deepEqual(await response.json(), { success: true, id: 'bp_' + body.request_id });
    assert.equal(received[0].website, undefined);
    assert.equal(received[0].url, body.url);
    assert.equal(response.headers.get('Access-Control-Allow-Origin'), 'https://centercoopmedia.github.io');
    globalThis.fetch = async () => Response.json({ success: true, id: 'wrong' });
    assert.equal((await worker.fetch(request(), env)).status, 502);
  } finally { globalThis.fetch = original; }
});

test('invalid origin, honeypot, size, rate, and missing configuration fail before upstream', async () => {
  assert.equal((await worker.fetch(request(body, 'https://evil.example'), env)).status, 403);
  assert.equal((await worker.fetch(request({ ...body, website: 'bot' }), env)).status, 400);
  assert.equal((await worker.fetch(request({ ...body, description: 'x'.repeat(60001) }), env)).status, 400);
  assert.equal((await worker.fetch(request(), {})).status, 503);
  assert.equal((await worker.fetch(request(), { ...env, REPORT_LIMITER: { limit: async () => ({ success: false }) } })).status, 429);
});
