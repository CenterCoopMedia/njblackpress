const ORIGIN = 'https://centercoopmedia.github.io';
const INTAKE = 'https://pi.amditis.tech/api/njpbs/blackpress/report';
const LIMIT = 60000;

function reply(status, body) {
  return new Response(body === null ? null : JSON.stringify(body), {
    status, headers: {
      'Content-Type': 'application/json', 'Cache-Control': 'no-store',
      'Access-Control-Allow-Origin': ORIGIN, 'Vary': 'Origin',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}

async function readBody(request) {
  const reader = request.body?.getReader();
  if (!reader) throw new Error('Empty request');
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > LIMIT) throw new Error('Request too large');
      chunks.push(value);
    }
  } finally {
    await reader.cancel();
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
}

export default {
  async fetch(request, env) {
    if (new URL(request.url).pathname !== '/report') return reply(404, { error: 'Not found' });
    if (request.headers.get('Origin') !== ORIGIN) return reply(403, { error: 'Invalid origin' });
    if (request.method === 'OPTIONS') return reply(204, null);
    if (request.method !== 'POST') return reply(405, { error: 'Use POST' });
    if (!env.REPORT_LIMITER || !env.BLACKPRESS_REPORT_INTAKE_SECRET ||
        !env.ACCESS_CLIENT_ID || !env.ACCESS_CLIENT_SECRET) {
      return reply(503, { error: 'Reporting is temporarily unavailable. Please try again later.' });
    }
    const { success } = await env.REPORT_LIMITER.limit({
      key: 'blackpress:' + (request.headers.get('CF-Connecting-IP') || 'unknown'),
    });
    if (!success) return reply(429, { error: 'Too many reports. Please try again in a minute.' });
    if (!/^application\/json(?:;|$)/i.test(request.headers.get('Content-Type') || '')) {
      return reply(415, { error: 'Use JSON' });
    }
    let body;
    try {
      body = await readBody(request);
      if (!body || typeof body !== 'object' || Array.isArray(body) || body.website !== '') throw new Error('Invalid form');
      delete body.website;
      const fields = ['request_id', 'url', 'title', 'description', 'suggested_fix', 'source_url'];
      if (Object.keys(body).length !== fields.length || fields.some(key => typeof body[key] !== 'string')) throw new Error('Invalid fields');
      if (!/^[a-f0-9]{32}$/.test(body.request_id)) throw new Error('Invalid receipt ID');
    } catch {
      return reply(400, { error: 'The correction form is invalid or too large.' });
    }
    try {
      const response = await fetch(INTAKE, {
        method: 'POST', redirect: 'error', signal: AbortSignal.timeout(15000),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + env.BLACKPRESS_REPORT_INTAKE_SECRET,
          'CF-Access-Client-Id': env.ACCESS_CLIENT_ID,
          'CF-Access-Client-Secret': env.ACCESS_CLIENT_SECRET,
        }, body: JSON.stringify(body),
      });
      const receipt = await response.json();
      if (response.ok && receipt.success === true && receipt.id === 'bp_' + body.request_id) {
        return reply(200, { success: true, id: receipt.id });
      }
      if (response.status === 409) return reply(409, { error: 'This receipt belongs to a different correction. Close and reopen the form.' });
      if (response.status === 400) return reply(400, { error: 'Check the page, description, and source link, then try again.' });
    } catch { /* A lost response may follow a committed intake; keep the same ID on retry. */ }
    return reply(502, { error: 'We could not confirm receipt. Your text is saved in this form. Please retry.' });
  },
};
