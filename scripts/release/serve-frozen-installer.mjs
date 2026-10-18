/** Temporary loopback host for the two explicitly qualified Voicy release files. */
import { createHash } from 'node:crypto';
import { constants, createReadStream } from 'node:fs';
import { open, readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { parseRange } from '../../landing/worker/range.js';

const sameFile = (a, b) => a.ino === b.ino && a.size === b.size && a.mtimeNs === b.mtimeNs;

export async function freezeFile(path, sha256, bytes, contentType, filename) {
  if (!/^[a-f0-9]{64}$/.test(sha256) || !Number.isSafeInteger(bytes) || bytes <= 0)
    throw new Error('Invalid frozen identity');
  const handle = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const before = await handle.stat({ bigint: true });
    if (!before.isFile() || before.size !== BigInt(bytes)) throw new Error('Wrong artifact type/size');
    const hash = createHash('sha256');
    for await (const block of handle.createReadStream({ autoClose: false })) hash.update(block);
    const after = await handle.stat({ bigint: true });
    if (!sameFile(before, after) || hash.digest('hex') !== sha256) throw new Error('Frozen artifact differs');
    return { path, sha256, bytes, contentType, filename, baseline: before };
  } finally { await handle.close(); }
}

export function createInstallerServer(entries) {
  return createServer(async (req, res) => {
    const end = (status, headers = {}) => { res.writeHead(status, { 'Content-Length': '0', 'Cache-Control': 'no-store', ...headers }); res.end(); };
    if (!['GET', 'HEAD'].includes(req.method)) return end(405, { Allow: 'GET, HEAD' });
    let pathname;
    try { pathname = new URL(req.url, 'http://127.0.0.1').pathname; }
    catch { return end(400); }
    const file = entries.get(pathname);
    if (!file) return end(404);
    let handle;
    try {
      handle = await open(file.path, constants.O_RDONLY | constants.O_NOFOLLOW);
      if (!sameFile(file.baseline, await handle.stat({ bigint: true }))) return end(503);
      const etag = '"sha256-' + file.sha256 + '"';
      const range = req.method === 'GET' && (!req.headers['if-range'] || req.headers['if-range'] === etag)
        ? parseRange(req.headers.range, file.bytes) : null;
      if (range?.invalid) return end(416, { 'Content-Range': 'bytes */' + file.bytes });
      const offset = range?.offset ?? 0, length = range?.length ?? file.bytes;
      const headers = {
        'Content-Type': file.contentType, 'Content-Length': String(length),
        'Content-Disposition': 'attachment; filename="' + file.filename + '"',
        'Accept-Ranges': 'bytes', ETag: etag, 'X-Voicy-SHA256': file.sha256,
        'X-Content-Type-Options': 'nosniff', 'X-Robots-Tag': 'noindex', 'Cache-Control': 'no-store',
      };
      if (range) headers['Content-Range'] = `bytes ${offset}-${offset + length - 1}/${file.bytes}`;
      res.writeHead(range ? 206 : 200, headers);
      if (req.method === 'HEAD') { res.end(); return; }
      const stream = handle.createReadStream({ start: offset, end: offset + length - 1 });
      handle = null; // The stream now owns and closes this request's descriptor.
      stream.on('error', () => res.destroy());
      res.on('close', () => stream.destroy());
      stream.pipe(res);
    } catch { if (!res.headersSent) end(503); else res.destroy(); }
    finally { if (handle) await handle.close(); }
  });
}

async function main() {
  const root = '/Users/giuseppe/Documents/voicy-growth-evidence';
  const proof = JSON.parse(await readFile(root + '/checkpoints/2026-10-18-release-recovery/FROZEN-DMG.json', 'utf8'));
  if (proof.version !== '0.3.3' || proof.new_app_and_dmg_notarization !== 'Accepted' || proof.local_signature_ticket_gatekeeper !== true)
    throw new Error('Installer has not passed the local release gates');
  const installer = await freezeFile(root + '/release-0.3.3-baseline14/Voicy-0.3.3-arm64.dmg', proof.sha256, proof.bytes,
    'application/x-apple-diskimage', 'Voicy-0.3.3-arm64.dmg');
  const fixture = await freezeFile(root + '/checkpoints/2026-10-18-afternoon/voicy-baseline14-native-fan.wav',
    '75e626fae7dbd8ece6b057881bc0584c798cc79eae97ca517bbca3e000458d02', 941818, 'audio/wav', 'voicy-e03-fan.wav');
  const port = Number(process.env.VOICY_INSTALLER_PORT ?? 54831);
  if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid local port');
  const server = createInstallerServer(new Map([['/Voicy-0.3.3-arm64.dmg', installer], ['/voicy-e03-fan.wav', fixture]]));
  server.listen(port, '127.0.0.1', () => console.log(JSON.stringify({ ready: true, bind: '127.0.0.1', port, sha256: installer.sha256, bytes: installer.bytes })));
  for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => server.close());
}
if (process.argv[1] === fileURLToPath(import.meta.url)) await main();
