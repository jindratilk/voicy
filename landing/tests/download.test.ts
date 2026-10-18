import test from "node:test";
import assert from "node:assert/strict";
import { site } from "../lib/site";
import { GET, HEAD } from "../app/api/download/route";
test("download redirects only when the artifact is available", async (t) => {
  const previous = process.env.DOWNLOAD_URL;
  const previousPause = site.downloadPaused;
  const previousBytes = site.downloadBytes;
  site.downloadBytes = 123;
  site.downloadPaused = false;
  process.env.DOWNLOAD_URL = "https://example.com/download";
  t.after(() => {
    site.downloadPaused = previousPause;
    site.downloadBytes = previousBytes;
    if (previous === undefined) delete process.env.DOWNLOAD_URL;
    else process.env.DOWNLOAD_URL = previous;
  });
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response(null, { status: 200, headers: { "Content-Length": "123", "Content-Disposition": `attachment; filename="Voicy-${site.version}-arm64.dmg"` } }),
  );
  const response = await GET();
  assert.equal(response.status, 302);
  assert.equal(
    response.headers.get("Location"),
    `https://example.com/download?v=${site.version}`,
  );
});
test("unavailable artifact produces a human-readable retry page and bodyless HEAD", async (t) => {
  const previous = process.env.DOWNLOAD_URL;
  const previousPause = site.downloadPaused;
  const previousBytes = site.downloadBytes;
  site.downloadBytes = 123;
  site.downloadPaused = false;
  process.env.DOWNLOAD_URL = "https://example.com/download";
  t.after(() => {
    site.downloadPaused = previousPause;
    site.downloadBytes = previousBytes;
    if (previous === undefined) delete process.env.DOWNLOAD_URL;
    else process.env.DOWNLOAD_URL = previous;
  });
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response(null, { status: 503 }),
  );
  const response = await GET();
  assert.equal(response.status, 503);
  assert.equal(response.headers.get("Retry-After"), "60");
  assert.match(await response.text(), /Back to Voicy/);
  const head = await HEAD();
  assert.equal(head.status, 503);
  assert.equal(await head.text(), "");
});

test("paused release explains the startup issue without probing or redirecting to the artifact", async (t) => {
  const previous = site.downloadPaused;
  const previousUrl = process.env.DOWNLOAD_URL;
  site.downloadPaused = true;
  process.env.DOWNLOAD_URL = "https://example.com/available-but-broken-release";
  t.after(() => {
    site.downloadPaused = previous;
    if (previousUrl === undefined) delete process.env.DOWNLOAD_URL;
    else process.env.DOWNLOAD_URL = previousUrl;
  });
  const fetch = t.mock.method(globalThis, "fetch", async () => { throw new Error("Paused download must not probe the artifact"); });
  const response = await GET();
  assert.equal(response.status, 503);
  assert.equal(response.headers.get("Location"), null);
  assert.equal(response.headers.get("Retry-After"), "3600");
  assert.match(await response.text(), /Version 0\.3\.2 has a startup issue/);
  const head = await HEAD();
  assert.equal(head.status, 503);
  assert.equal(await head.text(), "");
  assert.equal(fetch.mock.calls.length, 0);
});


test("a legacy or mismatched installer stays unavailable even when its server returns 200", async (t) => {
  const previous = { paused: site.downloadPaused, bytes: site.downloadBytes, version: site.version, url: process.env.DOWNLOAD_URL };
  site.downloadPaused = false;
  site.downloadBytes = 123;
  site.version = "0.3.3";
  process.env.DOWNLOAD_URL = "https://example.com/download";
  t.after(() => {
    site.downloadPaused = previous.paused; site.downloadBytes = previous.bytes; site.version = previous.version;
    if (previous.url === undefined) delete process.env.DOWNLOAD_URL; else process.env.DOWNLOAD_URL = previous.url;
  });
  const artifactHeaders: Record<string, string>[] = [
    { "Content-Length": "123", "Content-Disposition": 'attachment; filename="Voicy-0.3.2-arm64.dmg"' },
    { "Content-Length": "124", "Content-Disposition": 'attachment; filename="Voicy-0.3.3-arm64.dmg"' },
    {},
  ];
  for (const headers of artifactHeaders) {
    t.mock.method(globalThis, "fetch", async () => new Response(null, { status: 200, headers }));
    const response = await GET();
    assert.equal(response.status, 503); assert.equal(response.headers.get("Location"), null);
    const head = await HEAD(); assert.equal(head.status, 503); assert.equal(await head.text(), "");
    t.mock.restoreAll();
  }
});

test("an unqualified installer size fails closed without contacting the download host", async (t) => {
  const paused = site.downloadPaused, bytes = site.downloadBytes;
  site.downloadPaused = false; site.downloadBytes = null;
  t.after(() => { site.downloadPaused = paused; site.downloadBytes = bytes; });
  const probe = t.mock.method(globalThis, "fetch", async () => { throw new Error("Unqualified artifact must not be probed"); });
  assert.equal((await GET()).status, 503); assert.equal(probe.mock.calls.length, 0);
});


test("GitHub's exact unquoted filename is accepted with the qualified byte count", async (t) => {
  const previous = { paused: site.downloadPaused, bytes: site.downloadBytes, url: process.env.DOWNLOAD_URL };
  site.downloadPaused = false; site.downloadBytes = 123;
  process.env.DOWNLOAD_URL = "https://github.com/jindratilk/voicy/releases/download/v0.3.3/Voicy-0.3.3-arm64.dmg";
  t.after(() => {
    site.downloadPaused = previous.paused; site.downloadBytes = previous.bytes;
    if (previous.url === undefined) delete process.env.DOWNLOAD_URL; else process.env.DOWNLOAD_URL = previous.url;
  });
  t.mock.method(globalThis, "fetch", async () => new Response(null, { status: 200, headers: {
    "Content-Length": "123", "Content-Disposition": `attachment; filename=Voicy-${site.version}-arm64.dmg`,
  } }));
  assert.equal((await GET()).status, 302);
  const head = await HEAD(); assert.equal(head.status, 302); assert.equal(await head.text(), "");
});
