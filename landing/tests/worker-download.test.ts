import test from "node:test";
import assert from "node:assert/strict";
import { download } from "../worker/download.js";
function fixture() {
  let reads = 0;
  const metadata = {
    size: 10,
    httpEtag: '"test"',
    range: { offset: 0, length: 10 },
    writeHttpMetadata: () => {},
  };
  return {
    get reads() {
      return reads;
    },
    async head() {
      return metadata;
    },
    async get(
      _key: string,
      options?: { range: { offset: number; length: number } },
    ) {
      reads++;
      const range = options?.range ?? metadata.range;
      return {
        ...metadata,
        range,
        body: "0123456789".slice(range.offset, range.offset + range.length),
      };
    },
  };
}
test("HEAD remains 200 and does not fetch a body even when R2 exposes a full-object range", async () => {
  const bucket = fixture();
  const r = await download(
    new Request("https://test/download", {
      method: "HEAD",
      headers: { Range: "bytes=0-2" },
    }),
    bucket,
    "Voicy.dmg",
  );
  assert.equal(r.status, 200);
  assert.equal(r.headers.get("Content-Length"), "10");
  assert.equal(r.headers.get("Content-Range"), null);
  assert.equal(await r.text(), "");
  assert.equal(bucket.reads, 0);
});
test("ordinary download remains 200 and records exactly one start", async () => {
  const bucket = fixture();
  let starts = 0;
  const r = await download(
    new Request("https://test/download"),
    bucket,
    "Voicy.dmg",
    () => {
      starts++;
    },
  );
  assert.equal(r.status, 200);
  assert.equal(r.headers.get("Content-Range"), null);
  assert.equal(await r.text(), "0123456789");
  assert.equal(starts, 1);
});
test("resumed download returns 206 with exact body and is not counted again", async () => {
  let starts = 0;
  const r = await download(
    new Request("https://test/download", {
      headers: { Range: "bytes=3-5", "If-Range": '"test"' },
    }),
    fixture(),
    "Voicy.dmg",
    () => {
      starts++;
    },
  );
  assert.equal(r.status, 206);
  assert.equal(r.headers.get("Content-Range"), "bytes 3-5/10");
  assert.equal(await r.text(), "345");
  assert.equal(starts, 0);
});
test("stale If-Range restarts the complete file; unsatisfiable ranges return 416", async () => {
  const full = await download(
    new Request("https://test/download", {
      headers: { Range: "bytes=3-5", "If-Range": '"old"' },
    }),
    fixture(),
    "Voicy.dmg",
  );
  assert.equal(full.status, 200);
  assert.equal(await full.text(), "0123456789");
  const missing = await download(
    new Request("https://test/download", { headers: { Range: "bytes=10-" } }),
    fixture(),
    "Voicy.dmg",
  );
  assert.equal(missing.status, 416);
  assert.equal(missing.headers.get("Content-Range"), "bytes */10");
});
