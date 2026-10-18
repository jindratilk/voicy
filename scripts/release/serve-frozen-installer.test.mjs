import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, rm, writeFile, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { freezeFile, createInstallerServer } from './serve-frozen-installer.mjs';

test('HTTP installer transport serves only frozen files, including resumed downloads', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'voicy-transport-test-'));
  const path = join(dir, 'Voicy-0.3.3-arm64.dmg');
  const bytes = Buffer.from('0123456789abcdef');
  const sha = createHash('sha256').update(bytes).digest('hex');
  let server;
  try {
    await writeFile(path, bytes);
    await assert.rejects(freezeFile(path, '0'.repeat(64), bytes.length, 'application/x-apple-diskimage', 'Voicy.dmg'));
    await symlink(path, join(dir, 'link.dmg'));
    await assert.rejects(freezeFile(join(dir, 'link.dmg'), sha, bytes.length, 'application/x-apple-diskimage', 'Voicy.dmg'));
    const file = await freezeFile(path, sha, bytes.length, 'application/x-apple-diskimage', 'Voicy.dmg');
    server = createInstallerServer(new Map([['/Voicy.dmg', file]]));
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const base = 'http://127.0.0.1:' + server.address().port;
    let r = await fetch(base + '/Voicy.dmg');
    assert.equal(r.status, 200); assert.equal(r.headers.get('content-length'), '16');
    assert.deepEqual(Buffer.from(await r.arrayBuffer()), bytes);
    r = await fetch(base + '/Voicy.dmg?v=0.3.3', { method: 'HEAD' });
    assert.equal(r.status, 200); assert.equal((await r.arrayBuffer()).byteLength, 0);
    assert.equal(r.headers.get('x-voicy-sha256'), sha);
    for (const [range, expected, contentRange] of [['bytes=1-4', '1234', 'bytes 1-4/16'], ['bytes=-4', 'cdef', 'bytes 12-15/16']]) {
      r = await fetch(base + '/Voicy.dmg', { headers: { Range: range } });
      assert.equal(r.status, 206); assert.equal(r.headers.get('content-range'), contentRange); assert.equal(await r.text(), expected);
    }
    r = await fetch(base + '/Voicy.dmg', { headers: { Range: 'bytes=999-' } });
    assert.equal(r.status, 416); assert.equal(r.headers.get('content-range'), 'bytes */16'); await r.arrayBuffer();
    r = await fetch(base + '/Voicy.dmg', { headers: { Range: 'bytes=1-4', 'If-Range': 'stale' } });
    assert.equal(r.status, 200); assert.equal(await r.text(), bytes.toString());
    r = await fetch(base + '/'); assert.equal(r.status, 404); await r.arrayBuffer();
    r = await fetch(base + '/private.txt'); assert.equal(r.status, 404); await r.arrayBuffer();
    r = await fetch(base + '/Voicy.dmg', { method: 'POST' }); assert.equal(r.status, 405); await r.arrayBuffer();
    await writeFile(path, 'changed');
    r = await fetch(base + '/Voicy.dmg'); assert.equal(r.status, 503); await r.arrayBuffer();
  } finally {
    if (server) await new Promise(resolve => { server.closeAllConnections(); server.close(resolve); });
    await rm(dir, { recursive: true, force: true });
  }
});
