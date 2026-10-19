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
      <p>Last updated: 19 October 2026.</p>
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
        The site is hosted on Vercel. The current installer and its app-image
        files are downloaded from GitHub Releases; initial setup needs the
        Internet. Cloudflare hosts the legacy download route and aggregate
        website counters. These providers process network information to deliver
        and protect their services, under their own privacy policies:
        {" "}<a href="https://vercel.com/legal/privacy-notice">Vercel</a>,{" "}
        <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub</a>
        {" "}and <a href="https://www.cloudflare.com/privacypolicy/">Cloudflare</a>.
        Downloading the app does not send them your recordings.
      </p>
      <p>
        Voicy’s own aggregate counters store daily page-view events and legacy
        Cloudflare download starts, without visitor IP addresses, fingerprints
        or audio. Page-view events currently come from the homepage, not the
        comparison or privacy pages. Legacy download counts exclude the current
        GitHub installer and are not install counts or unique-person counts.
        Repeats, bots and our own checks can contribute to the totals. No
        advertising or cross-site tracking cookies are used on this website.
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
