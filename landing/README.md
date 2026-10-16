# Voicy website and admin

Next.js website for usevoicy.app. Static marketing pages, a prerecorded A/B player, and server-side administration. Uses self-hosted Inter (SIL OFL). No microphone permission is requested.

## Local development

Use Node.js 22 or newer. Run `npm ci`, then `npm run dev`. The site is served on port 3007. Copy configuration into a private `.env.local`; never commit it.

Required server-only environment variables:

- `SITE_URL`: production HTTPS origin.
- `ADMIN_EMAIL`: admin identity.
- `ADMIN_PASSWORD_HASH`: `salt:hex` using Node scrypt(password,salt,64).
- `SESSION_SECRET`: random signing secret, at least 32 random bytes.
- `METRICS_URL`: deployed download worker origin.
- `METRICS_KEY`: private shared key matching the worker's `ADMIN_KEY`.
- `DOWNLOAD_URL`: worker `/download` URL.

## Deployment

The website is hosted on Vercel. Link to your own project, set encrypted production environment variables, and deploy with `vercel --prod`. Attach your domain. No credentials or customer recordings belong in this repository.

The Cloudflare worker serves the R2 release artifact and keeps daily aggregates in a SQLite-backed Durable Object. Adjust account ID and bucket name in `worker/wrangler.jsonc` for your account, then deploy with Wrangler. Set `ADMIN_KEY` using Wrangler secrets. Do not expose the internal API key to the client.

The worker records full-file download starts, not completed installs or unique people. Byte-range resumes are excluded. Page views can include repeats and bots. Network infrastructure still handles standard network metadata. Admin login uses a 15-minute rate limit with keyed IP hashes, secure HTTP-only cookies, HMAC-signed 8-hour sessions and origin checks.

## Change the admin password

Use Node's `crypto.randomBytes(16).toString('hex')` for a fresh salt and `crypto.scryptSync(newPassword,salt,64).toString('hex')` for the hash. Store only `salt:hash` as encrypted `ADMIN_PASSWORD_HASH` on Vercel. Rotate `SESSION_SECRET` to invalidate existing sessions, then deploy again. Do not enter passwords as command-line arguments or commit them. See the private release handoff for the initial password; it is intentionally absent here.

## Search and AI readability

The website includes canonical URLs, Open Graph and social images, SoftwareApplication and FAQ JSON-LD, robots.txt, sitemap.xml and llms.txt. These help discovery and interpretation; they do not guarantee rankings, rich results or citation by AI systems. Admin and API routes are excluded from indexing. FAQ claims match visible content.

## IndexNow notifications

`INDEXNOW_KEY` is an optional server-only production variable (8–128 letters, digits or hyphens). Generate a fresh random value; keep it and the exact file URL out of Git, public logs, sitemaps and client bundles. The root path `/{INDEXNOW_KEY}.txt` intentionally serves the value as plain text for search-engine ownership verification, with `noindex` and no caching. There is no fixed alias or directory listing. Other unknown root paths and missing/invalid configuration return an empty 404; HEAD has no body. This proof only authorizes search-engine URL notifications, not admin access. Do not reuse another service's secret.

After a meaningful public content change is deployed and verified, send only the changed canonical URLs in one JSON POST to `https://api.indexnow.org/indexnow`, using `host: "usevoicy.app"`, the configured `key`, and the matching root `.txt` URL as `keyLocation`. Keep the request payload and dated response outside public Git. Do not notify on every heartbeat, documentation-only commit or unchanged check. Do not include admin/API/download-status URLs or preview domains. HTTP 200 acknowledges receipt; 202 means verification is pending. Neither proves crawling, indexing, ranking or an AI citation. See the [protocol](https://www.indexnow.org/documentation) and [FAQ](https://www.indexnow.org/faq).

## Release artifact

Upload the signed, notarized and stapled DMG to the release bucket using [R2 multipart upload](https://developers.cloudflare.com/r2/objects/upload-objects/#multipart-upload). Keep the object filename in `worker/index.js` consistent with the release version. The public Worker exposes downloads and authenticated metrics, not upload endpoints. Verify the artifact size, transport checksums and resumed downloads before publishing a GitHub release. Attach the final SHA-256 checksum to the release.
