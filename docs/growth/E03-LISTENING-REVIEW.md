# E03 private listening review, version 1

Prepared 20 October 2026, after technical output generation on 15 October and before any human responses. This is a practical project audit with concealed variant labels. It is not a preregistered quality trial, independent panel, standardized MOS test or Adobe comparison.

## Fixed material and purpose

Use all five cases and all three existing listening copies per case from the [historical 0.3.2 results](E03-RESULTS.json). Keep the [original protocol](E03-PROTOCOL.md), source selection, degradations, model settings, mastering and hashes unchanged. The current download is 0.3.3; these historical outputs must retain their actual version. A new current-release run needs a separate pre-run addendum and the existing storage/memory guards.

The immediate task is qualitative: inspect word changes, missing speech and artifacts on every clip, including the clean control. Separately mastered copies have different achieved loudness values; do not interpret loudness preference as a quality result. This small English audiobook set is not representative of microphones, languages or real noisy environments. Training overlap is unknown.

## Preparation and blinding limits

`scripts/growth/serve_listening_review.py` uses the standard library, verifies the exact fifteen mono 48 kHz PCM24 files against the existing result/manifest hashes, and creates an exclusive private packet outside Git. It copies no audio and runs no inference. Preparing this read-only worksheet does not waive the 12 GiB headroom requirement for future model execution.

Each case has a separately shuffled A/B/C assignment. Opaque media URLs conceal file names and variant labels; the assignment seed, mapping, source paths and report digest stay in the private packet. Preserve its SHA-256 before any review. Restart with that same packet; do not regenerate assignments after seeing responses. The listener may infer a condition from its sound, and a technically informed person could identify public hashes. This is label concealment, not proof of complete blinding.

Example, using existing private files and a new destination:

```sh
python3 scripts/growth/serve_listening_review.py prepare \
  --results docs/growth/E03-RESULTS.json \
  --listening-root /path/to/e03-v1/listening-0.3.2 \
  --packet /path/outside/git/listening-packet.json
python3 scripts/growth/serve_listening_review.py serve \
  --packet /path/outside/git/listening-packet.json --port 54835
```

The server binds only to `127.0.0.1`. It serves the worksheet and the exact verified clips, rejects other paths/hosts and changed assets, and has no notes-submission API. Short WAVs are served in full; byte-range requests are not required or promised. Keep it private. Public audio publication still requires the original review gate and explicit Git asset allowlist.

## Reviewer workflow

1. Use headphones at a comfortable fixed volume. Keep playback equipment and volume stable. Avoid a noisy room. The interface plays one clip at a time, without autoplay.
2. Review every A/B/C clip in every case. Listen once before revealing the source script where possible; a revealed script can prime recognition. Script opening is recorded, not treated as an intelligibility measurement.
3. Select “No issue heard”, “Possible issue”, or “Cannot judge”; leave “Not reviewed” for unfinished work. Write exact words or time points for suspected problems. The source-script panel carries the exact corpus utterance ID for attribution and tracing. Do not assign a MOS or an overall winner.
4. Export JSON notes. They remain browser-local until download; the server receives no notes. Preserve the packet ID and original export. Drafts and ambiguous cases remain unverified.
5. Only attest to your own completed listening. Form completion, playback events and a self-attested file do not independently establish a human listener, an independent panel or a perceptual-quality result. Confirm actual review provenance before using notes in the evidence ledger.

The `?preview=1` view uses a separate browser-storage namespace and exports `qa_fixture` provenance/status. All automated UI checks must use that mode. Never mix its test notes with real assessments.

## Evidence gate

No human responses or judgments are created by preparation. After genuine notes are supplied, decode the sealed assignment and retain every case, negative observation and “cannot judge” response. Do not drop the clean control or select only flattering outputs. Preserve reviewer relationship, equipment, uncertainty and whether the transcript was viewed. Project-owner listening is not independent review.

Keep audio unpublished until the existing checks are satisfied, or present a documented failure explicitly without a quality endorsement. A historical review cannot establish current-release, long-form, population-wide or Adobe-superiority claims. External reviewer invitations still need named-destination message authorization; no invitations, public audio upload, account or purchase is part of this helper.

LibriSpeech © 2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The worksheet identifies resampling, degradation, enhancement and mastering. No reader endorsement is implied.
