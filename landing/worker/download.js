import { parseRange } from "./range.js";
const unavailable = () =>
  Response.json(
    { error: "Release not available yet" },
    { status: 503, headers: { "Cache-Control": "no-store" } },
  );
export async function download(req, bucket, artifact, onStart = () => {}) {
  const metadata = await bucket.head(artifact);
  if (!metadata) return unavailable();
  const requestedRange =
    req.method === "GET" &&
    (!req.headers.has("If-Range") ||
      req.headers.get("If-Range") === metadata.httpEtag)
      ? parseRange(req.headers.get("Range"), metadata.size)
      : null;
  if (requestedRange?.invalid)
    return new Response(null, {
      status: 416,
      headers: {
        "Content-Range": `bytes */${metadata.size}`,
        "Cache-Control": "no-store",
      },
    });
  const object =
    req.method === "HEAD"
      ? metadata
      : await bucket.get(
          artifact,
          requestedRange ? { range: requestedRange } : undefined,
        );
  if (!object) return unavailable();
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("Content-Type", "application/x-apple-diskimage");
  headers.set("Content-Disposition", `attachment; filename="${artifact}"`);
  headers.set("ETag", object.httpEtag);
  headers.set("Accept-Ranges", "bytes");
  headers.set("Cache-Control", "public, max-age=3600");
  headers.set("X-Content-Type-Options", "nosniff");
  let status = 200;
  // R2 can report a range for the whole object. Only an accepted client range
  // makes this a 206 response; HEAD and ordinary downloads must remain 200.
  if (requestedRange) {
    const { offset: start, length } = requestedRange;
    headers.set(
      "Content-Range",
      `bytes ${start}-${start + length - 1}/${object.size}`,
    );
    headers.set("Content-Length", String(length));
    status = 206;
  } else headers.set("Content-Length", String(object.size));
  if (req.method === "GET" && !req.headers.has("Range")) onStart();
  return new Response(req.method === "HEAD" ? null : object.body, {
    status,
    headers,
  });
}
