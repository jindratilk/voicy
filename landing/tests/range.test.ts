import test from "node:test";
import assert from "node:assert/strict";
import { parseRange } from "../worker/range.js";
test("resumes and bounded ranges return the exact bytes requested", () => {
  assert.deepEqual(parseRange("bytes=512-", 1024), {
    offset: 512,
    length: 512,
  });
  assert.deepEqual(parseRange("bytes=0-99", 1024), { offset: 0, length: 100 });
  assert.deepEqual(parseRange("bytes=1000-9999", 1024), {
    offset: 1000,
    length: 24,
  });
});
test("suffix ranges clamp to the available file", () => {
  assert.deepEqual(parseRange("bytes=-64", 1024), { offset: 960, length: 64 });
  assert.deepEqual(parseRange("bytes=-2048", 1024), {
    offset: 0,
    length: 1024,
  });
});
test("impossible byte ranges are rejected", () => {
  for (const value of [
    "bytes=1024-",
    "bytes=5-4",
    "bytes=-0",
    "bytes=9007199254740992-",
  ])
    assert.deepEqual(parseRange(value, 1024), { invalid: true });
});
test("unsupported units, malformed or multipart requests fall back to a full response", () => {
  for (const value of [
    null,
    "items=0-1",
    "bytes=-",
    "bytes=abc",
    "bytes=0-1,4-5",
  ])
    assert.equal(parseRange(value, 1024), null);
});
