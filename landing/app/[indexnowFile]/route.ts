export const dynamic = "force-dynamic";

type Context = { params: Promise<{ indexnowFile: string }> };

export async function GET(_request: Request, context: Context) {
  const key = process.env.INDEXNOW_KEY?.trim();
  const { indexnowFile } = await context.params;
  // The unguessable filename is part of the ownership proof; never expose a fixed alias.
  const valid = key !== undefined && /^[a-zA-Z0-9-]{8,128}$/.test(key) && indexnowFile === `${key}.txt`;
  return new Response(valid ? key : null, {
    status: valid ? 200 : 404,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex",
    },
  });
}

export async function HEAD(request: Request, context: Context) {
  const response = await GET(request, context);
  return new Response(null, { status: response.status, headers: response.headers });
}
