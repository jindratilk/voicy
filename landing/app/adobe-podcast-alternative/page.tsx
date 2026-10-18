import type { Metadata } from "next";
import Mark from "@/components/Mark";
import { site } from "@/lib/site";

const title = "Adobe Podcast Alternative — Free & Offline for Mac";
const description =
  "Compare Voicy with Adobe Podcast Enhance Speech: free local audio cleanup on Apple Silicon, no uploads or daily quota. Hear a sample and check the tradeoffs.";
export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: "/adobe-podcast-alternative" },
  openGraph: {
    title,
    description,
    url: `${site.url}/adobe-podcast-alternative`,
    type: "article",
    images: ["/og.png"],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: ["/og.png"],
  },
};

const rows = [
  [
    "Where audio is processed",
    "On your Mac, including offline",
    "In the browser workflow, after uploading your file",
  ],
  [
    "Cost",
    "Free; no account, credits, or subscription",
    "Free tier; Premium adds features and capacity",
  ],
  [
    "Daily enhancement allowance",
    "No app-imposed daily quota; processing time and hardware still limit throughput",
    "Free: 1 hour/day. Premium: 4 hours/day",
  ],
  [
    "File limits",
    "No fixed duration or size cap; available memory and storage apply",
    "Free: 30 minutes / 500 MB. Premium: 2 hours / 1 GB",
  ],
  [
    "Platform",
    "Apple Silicon Mac, macOS 14+",
    "Supported desktop and mobile browsers",
  ],
  [
    "Input and output",
    "WAV, MP3, M4A, FLAC, AIFF, OGG in; mono 48 kHz, 24-bit WAV out",
    "Audio; Premium also supports video",
  ],
  [
    "Broader editing workflow",
    "Focused speech enhancement with original/enhanced comparison",
    "Studio offers remote recording and transcript-based editing",
  ],
];

export default function ComparisonPage() {
  const data = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: title,
    description,
    url: `${site.url}/adobe-podcast-alternative`,
    datePublished: "2026-10-15",
    dateModified: "2026-10-15",
    about: { "@type": "SoftwareApplication", name: "Voicy", url: site.url },
    breadcrumb: {
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Voicy", item: site.url },
        {
          "@type": "ListItem",
          position: 2,
          name: "Adobe Podcast alternative",
          item: `${site.url}/adobe-podcast-alternative`,
        },
      ],
    },
  };
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(data).replace(/</g, "\\u003c"),
        }}
      />
      <a className="skip" href="#comparison">
        Skip to comparison
      </a>
      <header className="nav comparison-nav">
        <a className="brand" href="/" aria-label="Voicy home">
          <Mark size={20} />
          <span>voicy</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="/#demo">Audio demo</a>
          <a href={site.github}>Source</a>
        </nav>
        <a className="button primary small" href="/api/download">
          {site.downloadPaused ? "Status" : "Download"}
        </a>
      </header>
      <main className="comparison-page">
        <div className="comparison-glow" aria-hidden="true" />
        <section className="comparison-intro shell">
          <p className="eyebrow">Free · Local · Open source</p>
          <h1>
            An Adobe Podcast alternative.
            <br />
            <span>On your own Mac.</span>
          </h1>
          <p className="comparison-lead">
            Voicy is a free, open-source alternative to Adobe Podcast Enhance
            Speech for Apple Silicon Macs. It reduces background noise and room
            echo locally, without uploading your recordings.
          </p>
          <div className="hero-actions">
            <a className="button primary" href="/api/download">
              {site.downloadPaused ? "Download status" : "Download for Mac"}
            </a>
            <a className="text-link" href="/#demo">
              Hear the original and Voicy output ↗
            </a>
          </div>
          <p className="requirements">
            macOS 14+ · Apple Silicon · 6.5 GB setup download · 16 GB memory
            recommended
          </p>
          {site.downloadPaused && (
            <p className="download-notice">
              Downloads paused while we verify a startup fix.
            </p>
          )}
        </section>
        <article className="comparison-content shell">
          <div className="editorial-note">
            Published by the Voicy project ·{" "}
            <time dateTime="2026-10-15">15 October 2026</time>
            <br />
            This is our product comparison, not an independent review. Adobe
            facts are linked to official documentation below.
          </div>
          <section className="comparison-verdict">
            <h2>Choose the workflow that fits.</h2>
            <div className="verdict-grid">
              <div>
                <h3>Choose Voicy for local cleanup.</h3>
                <p>
                  You have a supported Mac, want to keep recordings on device,
                  and prefer a free app with models included. Allow time for
                  processing and a large initial download.
                </p>
              </div>
              <div>
                <h3>Choose Adobe for a browser workflow.</h3>
                <p>
                  You need supported devices beyond Apple Silicon, video
                  enhancement, or Studio’s remote recording and transcript
                  editing. Check which features and limits apply to your plan.
                </p>
              </div>
            </div>
          </section>
          <section id="comparison">
            <p className="eyebrow">The practical differences</p>
            <h2>Voicy vs Adobe Podcast.</h2>
            <p>
              Feature comparison for speech cleanup. These are documented
              capabilities, not a head-to-head audio-quality test.
            </p>
            <div
              className="comparison-table-wrap"
              role="region"
              aria-label="Voicy and Adobe Podcast feature comparison"
              tabIndex={0}
            >
              <table className="comparison-table">
                <caption>
                  Voicy {site.version} and Adobe Podcast Enhance Speech —
                  checked 15 October 2026
                </caption>
                <thead>
                  <tr>
                    <th scope="col">What matters</th>
                    <th scope="col">Voicy</th>
                    <th scope="col">Adobe Podcast</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(([feature, voicy, adobe]) => (
                    <tr key={feature}>
                      <th scope="row">{feature}</th>
                      <td>{voicy}</td>
                      <td>{adobe}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="source-note">
              Adobe limits:{" "}
              <a href="https://podcast.adobe.com/en/features">
                official plan comparison
              </a>
              . Device support:{" "}
              <a href="https://helpx.adobe.com/podcast/technical-requirements.html">
                Adobe system requirements
              </a>
              . Features and plans can change; confirm them before choosing.
            </p>
          </section>
          <section>
            <h2>Listen before you decide.</h2>
            <p>
              These are the same original and enhanced files used in our
              homepage demo. The sample uses an ElevenLabs synthetic voice,
              simulated fan noise and light room reflections, then Voicy
              enhancement with AuK at 32 steps. Both versions are
              loudness-normalized.
            </p>
            <div className="listening-grid">
              <figure>
                <figcaption>01 / Original recording</figcaption>
                <audio
                  controls
                  preload="none"
                  aria-label="Original recording with simulated fan noise"
                  src="/audio/before.wav"
                />
                <a href="/audio/before.wav">Open original WAV</a>
              </figure>
              <figure>
                <figcaption>02 / Enhanced with Voicy</figcaption>
                <audio
                  controls
                  preload="none"
                  aria-label="Recording enhanced with Voicy"
                  src="/audio/after.wav"
                />
                <a href="/audio/after.wav">Open enhanced WAV</a>
              </figure>
            </div>
            <p>
              This demonstrates Voicy on one synthetic example. It does not
              demonstrate superiority over Adobe. Try a copy of your own
              recording and listen for changed consonants, voice texture, or
              missing words before publishing.
            </p>
          </section>
          <section>
            <h2>The tradeoffs, up front.</h2>
            <ul className="comparison-list">
              <li>
                <strong>Hardware:</strong> Apple Silicon and macOS 14 or newer.
                This release does not support Intel Macs, Windows, Linux, or
                mobile devices.
              </li>
              <li>
                <strong>Storage:</strong> the small download assistant retrieves and verifies
                the complete 6.5 GB app image. Allow about 15 GB during setup
                for that image and the 8 GB installed app, plus your recordings.
                Setup needs the Internet; models are included for offline enhancement.
              </li>
              <li>
                <strong>Speed:</strong> not real time. The 8.7-second demo took
                about 60 seconds of model processing on one M5 Mac with 32 GB
                memory. This is a single example, not a speed guarantee or an
                Adobe comparison.
              </li>
              <li>
                <strong>Output:</strong> mono, 48 kHz, 24-bit WAV. The
                enhancement model operates at 24 kHz; export sample rate is not
                recovered high-frequency detail.
              </li>
              <li>
                <strong>Scope:</strong> speech cleanup, not a full recording
                studio or a music-restoration tool. Generative enhancement can
                change the recording; your original is preserved.
              </li>
              <li>
                <strong>License:</strong> MIT application code. Bundled models
                and dependencies retain{" "}
                <a href={`${site.github}/blob/main/THIRD_PARTY_NOTICES.md`}>
                  their own licenses
                </a>
                .
              </li>
            </ul>
          </section>
          <section>
            <h2>How to switch from an upload workflow.</h2>
            <ol className="comparison-list">
              <li>
                Download Voicy and install it on a supported Mac. Keep an
                untouched copy of your recording.
              </li>
              <li>
                Import an audio file, then run enhancement locally. No Adobe
                account or Voicy account is needed.
              </li>
              <li>
                Compare the original and enhanced versions. Check the entire
                result, especially difficult words and quiet passages.
              </li>
              <li>
                Export a WAV and bring it into your editor for further editing
                or publishing.
              </li>
            </ol>
          </section>
          <section>
            <h2>What if Voicy is not the right fit?</h2>
            <p>
              For audio post-production with loudness targets and publishing
              workflows, consider <a href="https://auphonic.com/">Auphonic</a>.
              Its <a href="https://auphonic.com/pricing">free allowance</a> is
              currently two hours per month and includes an Auphonic jingle. For
              transcript-based audio and video editing with noise and echo
              reduction, look at{" "}
              <a href="https://www.descript.com/studio-sound">
                Descript’s Studio Sound
              </a>
              . Neither is assessed for audio quality here.
            </p>
          </section>
          <section className="comparison-sources">
            <h2>Sources and method.</h2>
            <p>
              Voicy capabilities come from{" "}
              <a href={site.github}>the source and documentation</a> and{" "}
              <a href={`${site.github}/blob/main/docs/release/VALIDATION.md`}>
                release validation
              </a>{" "}
              for version {site.version}. Adobe capabilities come from its{" "}
              <a href="https://podcast.adobe.com/en/features">
                feature comparison
              </a>
              ,{" "}
              <a href="https://podcast.adobe.com/en/guides/whats-new-in-adobe-podcast-march-2026">
                March 2026 product guide
              </a>
              , and{" "}
              <a href="https://podcast.adobe.com/en/guides/enhance-speech-for-video">
                video enhancement guide
              </a>
              , checked on 15 October 2026.
            </p>
            <p>
              No affiliate links, sponsored placements, or comparative quality
              scores are used. Found an error?{" "}
              <a href={`${site.github}/issues`}>Report it on GitHub</a>.
            </p>
          </section>
          <section className="comparison-cta">
            <Mark size={30} />
            <h2>Your audio. Your machine.</h2>
            <p>
              Hear the sample, check the requirements, then try your own
              recording.
            </p>
            <a className="button primary" href="/api/download">
              {site.downloadPaused ? "Download status" : "Download Voicy for free"}
            </a>
          </section>
        </article>
      </main>
      <footer className="shell">
        <div className="footer-links">
          <a href="/">Voicy home</a>
          <a href="/#demo">Interactive demo</a>
          <a href="/privacy">Privacy</a>
          <a href={site.github}>GitHub</a>
        </div>
        <p className="fine">
          Independent software. Not affiliated with Adobe or Apple. Adobe
          Podcast is an Adobe product.
        </p>
      </footer>
    </>
  );
}
