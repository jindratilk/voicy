# Download measurement contract, version 1

Adopted 20 October 2026. This contract observes existing public GitHub metadata. It adds no website events, cookies, identifiers, referrer collection or application telemetry.

## What can be measured

GitHub's [release-asset REST API](https://docs.github.com/en/rest/releases/assets) exposes an asset ID, name, size, digest and `download_count`. Public metadata can be read without new account permissions. Use the connector to fetch `https://api.github.com/repos/jindratilk/voicy/releases/tags/v0.3.3`; do not download binaries to read counters.

| Signal | Permitted interpretation | Unavailable interpretation |
| --- | --- | --- |
| Primary assistant `download_count` | GitHub-reported cumulative counter for that exact asset | Unique people, installs, completed setup, organic conversions |
| Each offline-image part's counter | Separate GitHub-reported counter for that part | Four summed users, full-image completion, successful assembly |
| Existing Worker download counter | Legacy Cloudflare route activity only | Current GitHub distribution or all downloads |
| Existing homepage pageviews | Aggregate homepage events including bots, repeats and our checks | Unique visitors, comparison-page visits, organic sessions |
| GSC clicks | Google-reported clicks within the recorded search filters/date range | Linked download or completed-install events |

Do not label the GitHub counter “download starts” or “completed downloads”: the cited API does not establish the event, retry, caching, byte-range or completion semantics needed for those stronger labels. Our release validation and browser checks contribute to counters. Historical QA totals are incomplete; do not guess a subtraction or call the remainder customers. Do not divide these counters by pageviews or GSC clicks to produce a conversion rate. Do not sum assistant, payload-part, manifest and qualification-file counters into an acquisition total.

## Qualified identity and baseline

The current stable release is `v0.3.3`, release ID `416695244`. Its primary assistant is asset ID `654436308`, `Voicy-0.3.3-arm64.dmg`, 146704 bytes, SHA-256 `61b69b2a812daa837240ab70057c74e0cf62ba02ba090757f38663e9489c4b45`. Bind each observation to that full identity and the [qualified public artifact](https://github.com/jindratilk/voicy/releases/download/v0.3.3/QUALIFICATION.json), rather than choosing whichever release or similarly named file is newest. Metadata identity is not a fresh signature or native-runtime test.

The first snapshot under this contract is retained privately in the 20 October download-measurement checkpoint. It records nine separate assets; the assistant counter is 42 and the four payload-part counters are 7, 4, 4 and 4. These are cumulative mixed-traffic observations, not acquisitions. There is no interval delta for this baseline. Retain the raw response and its SHA-256; keep later snapshots append-only. A receipt timestamp describes collection, not a provider-guaranteed counter-update time.

## Collection and comparison

1. At most once per scheduled growth cycle, fetch release metadata only when it advances measurement or checks a demonstrated distribution issue. A weekly report can reuse the most recent dated receipt; never imply a new measurement occurred. Do not poll to manufacture activity.
2. Preserve the exact source URL, receipt time in UTC, repository, release ID/tag, draft/prerelease flags, and all asset IDs, names, sizes, digests, creation/update times, URLs and counters. Keep raw JSON and collection errors outside public Git. No browser account export or credential belongs in the public summary.
3. Verify the selected release is stable and its primary asset matches the qualified identity. Do not silently cross a replaced asset, changed digest/size or release boundary. A replacement/new version starts a distinct series and baseline. Missing, malformed or failed observations remain unavailable.
4. Compare the same asset identities at two dated receipts. Report a nonnegative difference as a “GitHub-reported counter increase between receipts”, with the elapsed interval and mixed-traffic caveat. A decrease or identity mismatch makes the delta unavailable and triggers investigation; do not clamp it to zero. No daily backfill, interpolation or assumed data freshness.
5. Keep individual payload counters separate and preserve divergent counts. Neither their minimum nor their sum proves completed downloads or installs. Do not infer a funnel or abandonment rate from unmatched counters.
6. Record our own binary-download checks separately with date, artifact and reason when known. Avoid unnecessary full downloads. Unknown QA contribution remains unknown; metadata-only collection is not a binary-download check.

## Decisions this supports

Use missing assets, an incorrect identity or failed public redirects to investigate delivery health. Use later counter changes only as a coarse distribution signal alongside independently collected search data. A zero change does not prove no demand, and a positive change does not prove an SEO improvement.

Organic conversion measurement remains unimplemented. Before collecting anything new, define the exact event, aggregate attribution categories, retention, access controls, bot/QA handling, consent/privacy implications and acceptance checks. Prefer the smallest useful aggregate; no fingerprint, persistent visitor identifier, full referrer URL, search-query logging or customer-audio collection is authorized by this measurement contract. Do not add telemetry merely to fill an unavailable KPI.

## Offline receipt validation

`scripts/growth/download_counters.py` validates saved JSON without networking,
browser access, tokens or binary downloads. Save the complete connector release
response outside Git, record the actual UTC receipt time, then run:

```sh
python3 scripts/growth/download_counters.py snapshot \
  --release-json "$VOICY_EVIDENCE/RELEASE-RAW.json" \
  --observed-utc "$VOICY_RECEIPT_UTC" \
  --output "$VOICY_EVIDENCE/SNAPSHOT.json"
python3 scripts/growth/download_counters.py compare \
  --previous "$VOICY_PREVIOUS/SNAPSHOT.json" \
  --current "$VOICY_EVIDENCE/SNAPSHOT.json" \
  --output "$VOICY_EVIDENCE/COUNTER-COMPARISON.json"
```

Set these directory variables to existing private locations outside the public
checkout. Each output must be new; the helper refuses overwrite and checkout
destinations, including symlinks into the checkout, and creates files with mode
0600. A replacement release needs a separately reviewed identity and baseline.

The helper binds the stable release and exact qualified assistant ID, name, size
and digest, hashes the saved response bytes, retains each asset separately, and
requires timezone-aware increasing receipt times. Missing or malformed metadata
rejects the snapshot. Changed/missing secondary assets and decreasing counters
have null deltas with an explicit reason; they are never clamped to zero. The
original 20 October baseline format is supported. A compact historical summary
without the required identity fields is insufficient input; do not invent its
missing fields or overwrite it. A receipt hash protects provenance only when the
original raw file is retained and independently matched; it does not authenticate
arbitrary input or prove provider freshness. Reports preserve acquisition metrics
as null and have no summed acquisition total.
