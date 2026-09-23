export const site = {
  url: "https://usevoicy.app",
  github: "https://github.com/jindratilk/voicy",
  version: "0.3.2",
};
export const faqs = [
  [
    "Is Voicy really free?",
    "Yes. Voicy is a free, open-source speech enhancement app. No subscription, account, or credits. The application code is MIT licensed; bundled models and dependencies retain their own licenses.",
  ],
  [
    "Does my audio ever leave my Mac?",
    "No. The desktop app processes recordings locally using models included in the download. It works offline and does not upload your audio. The website demo uses a prerecorded sample.",
  ],
  [
    "Is this a free Adobe Podcast alternative?",
    "Voicy is an independent, local alternative for enhancing speech on Apple Silicon Macs. It reduces background noise and reverberation using AuK. It is not affiliated with Adobe, and results vary by recording. Try the demo and compare your own audio.",
  ],
  [
    "Which Macs can run Voicy?",
    "An Apple Silicon Mac with macOS 14 or newer. Intel Macs, Windows, and mobile devices are not supported in this release. The download is about 6.5 GB with models included. Allow about 8 GB for the installed app, plus space for recordings. 16 GB of memory or more is recommended; memory use adapts to available headroom.",
  ],
  [
    "What can I enhance?",
    "Import WAV, MP3, M4A, FLAC, AIFF, or OGG recordings without a fixed duration or file-size cap. Available memory and disk space still apply. Voicy exports mono, 48 kHz, 24-bit WAV. The enhancement model operates at 24 kHz.",
  ],
  [
    "How long does enhancement take?",
    "It depends on your Mac and the recording. This is not a real-time effect. Our 8.7-second demo took about 60 seconds of model processing on an M5 with 32 GB of memory. Longer recordings take longer.",
  ],
  [
    "Will every recording sound better?",
    "Not always. Generative enhancement can alter voice texture or words, especially in difficult audio. Your original is preserved. Compare both versions and listen carefully before publishing.",
  ],
];
