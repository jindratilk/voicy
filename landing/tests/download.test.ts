import test from "node:test";
import assert from "node:assert/strict";
import { site } from "../lib/site";
import { GET, HEAD } from "../app/api/download/route";
test("download redirects only when the artifact is available", async (t) => {
  const previous = process.env.DOWNLOAD_URL;
  const previousPause = site.downloadPaused;
  site.downloadPaused = false;
  process.env.DOWNLOAD_URL = "https://example.com/download";
  t.after(() => {
    site.downloadPaused = previousPause;
    if (previous === undefined) delete process.env.DOWNLOAD_URL;
    else process.env.DOWNLOAD_URL = previous;
  });
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response(null, { status: 200 }),
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
  site.downloadPaused = false;
  process.env.DOWNLOAD_URL = "https://example.com/download";
  t.after(() => {
    site.downloadPaused = previousPause;
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
