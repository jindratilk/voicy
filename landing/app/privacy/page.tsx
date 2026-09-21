import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "Privacy",
  alternates: { canonical: "/privacy" },
};
export default function Page() {
  return (
    <main className="prose">
      <a href="/">← Voicy</a>
      <h1>Your audio stays yours.</h1>
      <p>Last updated: 22 September 2026.</p>
      <h2>The desktop application</h2>
      <p>
        Voicy processes audio on your Mac. The downloadable app includes its
        speech enhancement models and works offline. It does not upload
        recordings, require an account, or send usage analytics. Files you
        import, results, and local processing logs remain on your device. You
        control exports and deletion.
      </p>
      <h2>This website</h2>
      <p>
        The site is hosted on Vercel and downloads are served through
        Cloudflare. Those providers process standard network information to
        deliver and protect their services, subject to their own privacy
        policies. Voicy stores aggregate daily page-view and download-start
        counts, without recording visitors’ IP addresses, fingerprints, or
        audio. Counts are not unique-person counts. No advertising or cross-site
        tracking cookies are used.
      </p>
      <h2>Administration</h2>
      <p>
        The private admin uses a secure, HTTP-only session cookie. For sign-in
        rate limiting, a keyed hash of the requesting IP is temporarily stored
        for up to 15 minutes. Passwords are stored as salted hashes in
        server-side configuration. Administrator credentials are never sent to
        the public website.
      </p>
      <h2>The demo</h2>
      <p>
        The demo is prerecorded. Its voice was generated with ElevenLabs, mixed
        with simulated computer-fan noise and light room reflections, then
        processed by Voicy using AuK with 32 steps. Both listening examples are
        loudness-normalized. Playing it does not record your microphone or
        upload audio.
      </p>
      <h2>Contact</h2>
      <p>
        Questions about privacy:{" "}
        <a href="mailto:jindra@cutagent.ai">jindra@cutagent.ai</a>.
      </p>
    </main>
  );
}
