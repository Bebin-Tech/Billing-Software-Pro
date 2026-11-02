// Same-origin gateway keeps refresh cookies on the frontend's HTTPS origin.
export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  const origin = process.env.BACKEND_URL;
  if (!origin) {
    return res.status(503).json({ detail: 'The backend is not configured yet. Render and managed MySQL must be connected before sign-in and billing are available.' });
  }
  const base = new URL(origin);
  if (base.protocol !== 'https:' || base.username || base.password || base.pathname !== '/') {
    return res.status(503).json({ detail: 'Backend configuration is invalid. Contact the administrator.' });
  }
  const query = new URL(req.url, 'https://gateway.invalid').searchParams;
  const path = query.get('path') || '';
  query.delete('path');
  if (!/^v1(?:\/[a-zA-Z0-9_.-]+)*$/.test(path) || path.split('/').some(part => part === '..' || part === '.')) {
    return res.status(404).json({ detail: 'API route not found' });
  }
  const url = new URL('/api/' + path, base);
  url.search = query.toString();
  const headers = {};
  for (const name of ['authorization', 'content-type', 'cookie', 'origin', 'x-company-id']) {
    if (req.headers[name]) headers[name] = req.headers[name];
  }
  try {
    const response = await fetch(url, {
      method: req.method, headers, redirect: 'manual',
      body: ['GET', 'HEAD'].includes(req.method) ? undefined : typeof req.body === 'string' ? req.body : req.body == null ? undefined : JSON.stringify(req.body),
      signal: AbortSignal.timeout(25000),
    });
    for (const name of ['content-type', 'content-disposition', 'retry-after']) {
      if (response.headers.has(name)) res.setHeader(name, response.headers.get(name));
    }
    const cookies = response.headers.getSetCookie();
    if (cookies.length) res.setHeader('Set-Cookie', cookies);
    return res.status(response.status).send(Buffer.from(await response.arrayBuffer()));
  } catch {
    return res.status(502).json({ detail: 'The backend is unavailable. Please retry shortly.' });
  }
}
