export async function GET() {
  const url = process.env.DOWNLOAD_URL;
  if (!url)
    return Response.json(
      { error: "The download is being prepared. Please try again shortly." },
      { status: 503 },
    );
  return new Response(null, {
    status: 302,
    headers: { Location: url, "Cache-Control": "no-store" },
  });
}
export const HEAD = GET;
