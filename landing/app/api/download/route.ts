const unavailable = () =>
  new Response(
    `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Download · Voicy</title><style>html{color-scheme:dark}body{margin:0;background:#080808;color:#f5f5f5;font:16px -apple-system,BlinkMacSystemFont,sans-serif;min-height:100svh;display:grid;place-items:center}main{max-width:440px;padding:40px}img{width:52px;height:52px}h1{font-size:32px;letter-spacing:-1px;font-weight:500;margin:28px 0 12px}p{color:#999;line-height:1.7}a{color:inherit;text-decoration:none}nav{display:flex;gap:24px;margin-top:30px}a:focus-visible{outline:2px solid white;outline-offset:6px}</style><main><img src="/icon.png" alt="Voicy"><h1>Almost ready.</h1><p>The download is temporarily unavailable. Please try again shortly.</p><nav><a href="/api/download">Try again ↗</a><a href="/">Back to Voicy</a></nav></main></html>`,
    {
      status: 503,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store",
        "Retry-After": "60",
        "X-Robots-Tag": "noindex",
      },
    },
  );
export async function GET() {
  const url = process.env.DOWNLOAD_URL;
  if (!url) return unavailable();
  try {
    const check = await fetch(url, {
      method: "HEAD",
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (!check.ok) return unavailable();
  } catch {
    return unavailable();
  }
  return new Response(null, {
    status: 302,
    headers: { Location: url, "Cache-Control": "no-store" },
  });
}
export async function HEAD() {
  const response = await GET();
  return new Response(null, {
    status: response.status,
    headers: response.headers,
  });
}
