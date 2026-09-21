import { NextResponse } from "next/server";
import { authenticated, worker } from "@/lib/auth";
export async function GET() {
  if (!(await authenticated()))
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  try {
    const r = await worker("/stats");
    if (!r.ok) throw new Error();
    return NextResponse.json(await r.json(), {
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json(
      { error: "Statistics are temporarily unavailable." },
      { status: 503 },
    );
  }
}
