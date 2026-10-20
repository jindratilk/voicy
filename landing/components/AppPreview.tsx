"use client";
import { useRef } from "react";

export default function AppPreview() {
  const video = useRef<HTMLVideoElement>(null);
  return (
    <details
      className="app-preview"
      onToggle={(event) => {
        if (!event.currentTarget.open) video.current?.pause();
      }}
    >
      <summary>
        See the actual Mac app <span>30 seconds · silent</span>
      </summary>
      <div className="app-preview-body">
        <video
          ref={video}
          controls
          playsInline
          preload="none"
          width="1000"
          height="650"
          poster="/images/voicy-0.3.3-controls.png"
          aria-label="Silent walkthrough of Voicy comparison controls"
          aria-describedby="app-preview-note"
        >
          <source src="/videos/voicy-0.3.3-controls.mp4" type="video/mp4" />
          <a href="/videos/voicy-0.3.3-controls.mp4">Download the walkthrough.</a>
        </video>
        <p id="app-preview-note">
          Recorded in Voicy 0.3.3 with a saved result. This silent video shows
          controls, not a new enhancement or a sound-quality comparison.
        </p>
        <details className="app-preview-text">
          <summary>Read the walkthrough</summary>
          <p>
            Original is selected with playback paused partway through the file.
            Play moves the playback position. Enhanced switches to the saved
            result and its waveform. Match volume is turned off and back on.
            Play starts the result again, then Pause stops it. The tabs are
            switched once more while paused; the video ends on Enhanced. Export
            and WAV · 24-bit remain visible. No new export is performed.
          </p>
          <a href="https://github.com/jindratilk/voicy/blob/main/docs/release/0.3.3-GALLERY.md#silent-controls-walkthrough">
            Recording source and limits {"→"}
          </a>
        </details>
      </div>
    </details>
  );
}
