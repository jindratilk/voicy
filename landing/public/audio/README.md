# Website demonstration: transcript and method

## Spoken text

The text alternative used beside both players is:

> Enhance your speech with Voicy. For free. Fully on your Mac. Turn noisy recordings into clear speech, without sending your audio to the cloud.

The original combines this synthetic voice with simulated fan noise and light room reflections. The second file is the Voicy-processed version of that recording. Both are loudness-normalized. These are the existing demo assets, created before release 0.3.3; they were not regenerated for that release.

## Recorded generation settings

Clean voice: ElevenLabs, George, eleven_multilingual_v2; not a recording of the developer or a user. The before sample adds deterministic simulated fan noise (overall SNR 9 dB), mild band limiting and two room reflections. The after sample is actual Voicy AuK32 output: q8/group64, 32 steps, seed 2026, CFG 2. Both use the app's two-pass loudness normalization. The clean reference is not substituted for the enhanced sample.

## Public file identity, checked 18 October 2026

Both are mono, 48 kHz, 24-bit PCM WAV. One exported sample frame accounts for the duration difference.

| File | Bytes | Sample frames | Duration | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| [Original](https://usevoicy.app/audio/before.wav) | 1,250,638 | 416,845 | 8.684271 s | `aa68cb0a47f75e8eab4b8ab9e1aa9aac284a787b2639c651cd2c7e15f787f8d2` |
| [Voicy output](https://usevoicy.app/audio/after.wav) | 1,250,640 | 416,846 | 8.684292 s | `625cce0e527c018d42db4f2122c88aa5d7dd26c7a8aa97538d526cd36772d98e` |

The live downloads matched the repository files byte for byte. A fixed local Whisper base.en transcription pass on each public file corroborated the surrounding wording, recognizing the brand as "voice" in the original and "Voicey" in the output. The displayed text uses the generation script's brand spelling, "Voicy". No repeated decodes were selected to hide this difference.

This automated check is not a human listening assessment, an audio-quality score or an Adobe comparison. Listen to both samples and check your own recordings for changed consonants, voice texture or missing words. The files demonstrate one synthetic example; they do not establish general improvement or current-release performance.

These demonstration recordings are distributed with the project. ElevenLabs-generated audio is not model code or a human endorsement.
