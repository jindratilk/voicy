import { DurableObject } from "cloudflare:workers";
import { parseRange } from "./range.js";
const artifact = "Voicy-0.3.0-arm64.dmg";
const json = (data, status = 200) =>
  Response.json(data, { status, headers: { "Cache-Control": "no-store" } });
export class Metrics extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(
      "CREATE TABLE IF NOT EXISTS daily (day TEXT PRIMARY KEY, views INTEGER NOT NULL DEFAULT 0, downloads INTEGER NOT NULL DEFAULT 0)",
    );
    this.sql.exec(
      "CREATE TABLE IF NOT EXISTS attempts (key TEXT PRIMARY KEY, count INTEGER, expires INTEGER)",
    );
  }
  async fetch(req) {
    const u = new URL(req.url),
      day = new Date().toISOString().slice(0, 10);
    if (u.pathname === "/event") {
      const { event } = await req.json();
      if (!["pageview", "download"].includes(event)) return json({}, 400);
      const col = event === "download" ? "downloads" : "views";
      this.sql.exec(
        `INSERT INTO daily(day,${col}) VALUES(?,1) ON CONFLICT(day) DO UPDATE SET ${col}=${col}+1`,
        day,
      );
      return json({ ok: true });
    }
    if (u.pathname === "/limit") {
      const { key } = await req.json();
      if (typeof key !== "string" || key.length > 128) return json({}, 400);
      const now = Date.now();
      this.sql.exec("DELETE FROM attempts WHERE expires < ?", now);
      this.sql.exec(
        "INSERT INTO attempts(key,count,expires) VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1",
        key,
        now + 900000,
      );
      const row = this.sql
        .exec("SELECT count FROM attempts WHERE key=?", key)
        .toArray()[0];
      return json({ allowed: row.count <= 8 });
    }
    const rows = this.sql
      .exec("SELECT day,views,downloads FROM daily ORDER BY day DESC LIMIT 90")
      .toArray();
    const total = this.sql
      .exec(
        "SELECT COALESCE(SUM(views),0) views,COALESCE(SUM(downloads),0) downloads FROM daily",
      )
      .toArray()[0];
    return json({ days: rows, total, updatedAt: new Date().toISOString() });
  }
}
export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    const metrics = () => env.METRICS.get(env.METRICS.idFromName("global"));
    if (u.pathname === "/health") return json({ ok: true, product: "Voicy" });
    if (u.pathname === "/download" && ["GET", "HEAD"].includes(req.method)) {
      const metadata = await env.RELEASES.head(artifact);
      if (!metadata) return json({ error: "Release not available yet" }, 503);
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
          : await env.RELEASES.get(
              artifact,
              requestedRange ? { range: requestedRange } : undefined,
            );
      if (!object) return json({ error: "Release not available yet" }, 503);
      const headers = new Headers();
      object.writeHttpMetadata(headers);
      headers.set("Content-Type", "application/x-apple-diskimage");
      headers.set("Content-Disposition", `attachment; filename="${artifact}"`);
      headers.set("ETag", object.httpEtag);
      headers.set("Accept-Ranges", "bytes");
      headers.set("Cache-Control", "public, max-age=3600");
      headers.set("X-Content-Type-Options", "nosniff");
      let status = 200;
      if (object.range) {
        const start =
          object.range.offset ?? Math.max(0, object.size - object.range.suffix);
        const length = object.range.length ?? object.size - start;
        headers.set(
          "Content-Range",
          `bytes ${start}-${start + length - 1}/${object.size}`,
        );
        headers.set("Content-Length", String(length));
        status = 206;
      } else headers.set("Content-Length", String(object.size));
      if (req.method === "GET" && !req.headers.has("Range"))
        ctx.waitUntil(
          metrics()
            .fetch(
              new Request("https://internal/event", {
                method: "POST",
                body: JSON.stringify({ event: "download" }),
              }),
            )
            .catch(() => {}),
        );
      return new Response(req.method === "HEAD" ? null : object.body, {
        status,
        headers,
      });
    }
    if (
      req.headers.get("Authorization") !== `Bearer ${env.ADMIN_KEY}` ||
      !env.ADMIN_KEY
    )
      return json({ error: "Unauthorized" }, 401);
    if (u.pathname === "/stats")
      return metrics().fetch("https://internal/stats");
    if (u.pathname === "/event" && req.method === "POST") {
      const body = await req.json();
      if (body.event !== "pageview") return json({}, 400);
      return metrics().fetch(
        new Request("https://internal/event", {
          method: "POST",
          body: JSON.stringify(body),
        }),
      );
    }
    if (u.pathname === "/limit" && req.method === "POST")
      return metrics().fetch(
        new Request("https://internal/limit", {
          method: "POST",
          body: await req.text(),
        }),
      );
    // Upload routes are removed from the public release worker after publication.
    if (u.pathname === "/upload/start" && req.method === "POST") {
      const upload = await env.RELEASES.createMultipartUpload(artifact, {
        httpMetadata: { contentType: "application/x-apple-diskimage" },
      });
      return json({ key: upload.key, uploadId: upload.uploadId });
    }
    if (u.pathname === "/upload/part" && req.method === "PUT") {
      const n = Number(u.searchParams.get("part"));
      if (!Number.isInteger(n) || n < 1 || n > 10000) return json({}, 400);
      const upload = env.RELEASES.resumeMultipartUpload(
        artifact,
        u.searchParams.get("id"),
      );
      return json(await upload.uploadPart(n, req.body));
    }
    if (u.pathname === "/upload/complete" && req.method === "POST") {
      const { uploadId, parts } = await req.json();
      const upload = env.RELEASES.resumeMultipartUpload(artifact, uploadId);
      const obj = await upload.complete(parts);
      return json({ size: obj.size, etag: obj.etag });
    }
    return json({ error: "Not found" }, 404);
  },
};
