import {
  createHmac,
  randomBytes,
  scryptSync,
  timingSafeEqual,
} from "node:crypto";
import { cookies } from "next/headers";
export const cookieName = "__Host-voicy_admin";
const equal = (a: string, b: string) => {
  const x = Buffer.from(a),
    y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
};
export function checkPassword(password: string) {
  const encoded = process.env.ADMIN_PASSWORD_HASH ?? "";
  const [salt, hash] = encoded.split(":");
  if (!salt || !hash || password.length > 256) return false;
  return equal(scryptSync(password, salt, 64).toString("hex"), hash);
}
export function session() {
  const key = process.env.SESSION_SECRET;
  if (!key) throw new Error("Authentication is not configured");
  const body = Buffer.from(
    JSON.stringify({
      exp: Date.now() + 8 * 3600e3,
      nonce: randomBytes(16).toString("hex"),
    }),
  ).toString("base64url");
  return (
    body + "." + createHmac("sha256", key).update(body).digest("base64url")
  );
}
export function verifySession(token: string) {
  const key = process.env.SESSION_SECRET;
  if (!key || token.length > 1000) return false;
  const [body, sig, ...rest] = token.split(".");
  if (!body || !sig || rest.length) return false;
  if (!equal(sig, createHmac("sha256", key).update(body).digest("base64url")))
    return false;
  try {
    const parsed = JSON.parse(Buffer.from(body, "base64url").toString());
    return (
      typeof parsed.exp === "number" &&
      parsed.exp > Date.now() &&
      parsed.exp < Date.now() + 8 * 3600e3 + 60000
    );
  } catch {
    return false;
  }
}
export async function authenticated() {
  return verifySession((await cookies()).get(cookieName)?.value ?? "");
}
export function validOrigin(req: Request) {
  const origin = req.headers.get("origin");
  return origin === new URL(req.url).origin || origin === process.env.SITE_URL;
}
export async function worker(path: string, body?: unknown) {
  if (!process.env.METRICS_URL || !process.env.METRICS_KEY)
    throw new Error("Metrics are not configured");
  return fetch(process.env.METRICS_URL + path, {
    method: body ? "POST" : "GET",
    headers: {
      Authorization: `Bearer ${process.env.METRICS_KEY}`,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
    signal: AbortSignal.timeout(8000),
  });
}
export function rateKey(req: Request) {
  const ip =
    req.headers.get("x-vercel-forwarded-for") ??
    req.headers.get("x-forwarded-for")?.split(",")[0] ??
    "unknown";
  return createHmac("sha256", process.env.SESSION_SECRET ?? "unconfigured")
    .update(ip)
    .digest("hex");
}
