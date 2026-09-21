import test from "node:test";
import assert from "node:assert/strict";
import { GET, HEAD } from "../app/api/download/route";
test("download redirects only when the artifact is available", async (t) => {
  const previous = process.env.DOWNLOAD_URL;
  process.env.DOWNLOAD_URL = "https://example.com/download";
  t.after(() => {
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
    "https://example.com/download",
  );
});
test("unavailable artifact produces a human-readable retry page and bodyless HEAD", async (t) => {
  const previous = process.env.DOWNLOAD_URL;
  process.env.DOWNLOAD_URL = "https://example.com/download";
  t.after(() => {
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
