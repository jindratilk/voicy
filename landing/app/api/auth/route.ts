import { NextResponse } from "next/server";
import {
  checkPassword,
  cookieName,
  rateKey,
  session,
  validOrigin,
  worker,
} from "@/lib/auth";
export async function POST(req: Request) {
  if (!validOrigin(req))
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  if (Number(req.headers.get("content-length")) > 2048)
    return NextResponse.json({ error: "Request too large" }, { status: 413 });
  try {
    const limit = await worker("/limit", { key: rateKey(req) });
    if (!limit.ok) throw new Error("Unavailable");
    if (!(await limit.json()).allowed)
      return NextResponse.json(
        { error: "Too many attempts. Try again in 15 minutes." },
        { status: 429 },
      );
    const { email, password } = await req.json();
    if (
      typeof email !== "string" ||
      typeof password !== "string" ||
      email.toLowerCase() !== process.env.ADMIN_EMAIL?.toLowerCase() ||
      !checkPassword(password)
    )
      return NextResponse.json(
        { error: "Email or password is incorrect." },
        { status: 401 },
      );
    const res = NextResponse.json({ ok: true });
    res.cookies.set(cookieName, session(), {
      httpOnly: true,
      secure: true,
      sameSite: "strict",
      path: "/",
      maxAge: 28800,
    });
    res.headers.set("Cache-Control", "no-store");
    return res;
  } catch {
    return NextResponse.json(
      { error: "Sign-in is temporarily unavailable." },
      { status: 503 },
    );
  }
}
export async function DELETE(req: Request) {
  if (!validOrigin(req))
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  const res = NextResponse.json({ ok: true });
  res.cookies.set(cookieName, "", {
    httpOnly: true,
    secure: true,
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  return res;
}
