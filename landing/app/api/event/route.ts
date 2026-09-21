import { NextResponse } from "next/server";
import { validOrigin, worker } from "@/lib/auth";
export async function POST(req: Request) {
  if (!validOrigin(req)) return new Response(null, { status: 403 });
  if (Number(req.headers.get("content-length")) > 256)
    return new Response(null, { status: 413 });
  try {
    const body = await req.json();
    if (body.event !== "pageview") return new Response(null, { status: 400 });
    await worker("/event", { event: "pageview" });
    return new Response(null, { status: 204 });
  } catch {
    return NextResponse.json({ ok: false }, { status: 503 });
  }
}
