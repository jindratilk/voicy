export default function DemoTranscript() {
  return (
    <details className="demo-transcript" id="demo-transcript">
      <summary>Read the demo transcript and method</summary>
      <p>Spoken text (brand spelling from the source script):</p>
      <blockquote>
        Enhance your speech with Voicy. For free. Fully on your Mac. Turn noisy
        recordings into clear speech, without sending your audio to the cloud.
      </blockquote>
      <p>
        The original combines a synthetic voice with simulated fan noise and room
        reflections. The second sample is the Voicy AuK32 output. Both are
        loudness-normalized. These existing demo files predate 0.3.3; this is not
        an Adobe audio-quality comparison.
      </p>
      <p>
        <a href="https://github.com/jindratilk/voicy/blob/main/landing/public/audio/README.md">
          Audio files, settings and verification (GitHub)
        </a>
      </p>
    </details>
  );
}
