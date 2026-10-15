# Voicy organic search and answer visibility

Owner authorization: 15 October 2026. Deadline: 31 December 2026, Europe/Prague.
Target: `Adobe podcast alternative`. Product: https://usevoicy.app/.
This is an execution plan and measurement protocol, not a promise of a Google position.

## Positioning and search intent

Voicy is a free local speech enhancer for Apple Silicon, not a replacement for every Adobe Podcast Studio feature. Lead with no audio uploads, offline processing, open application code and no account/daily quota. Preserve the product's limitations: large download, hardware requirements, slower-than-real-time processing, mono output, generative changes and separate model licenses.

Assume English-language US search is the primary market; report UK and all-country data separately. Desktop and mobile must be separated. This is a working market assumption, not a user-confirmed geo restriction. The homepage remains the brand/product experience; `/adobe-podcast-alternative` owns comparative intent. Do not create competing `/voicy-vs-adobe`, `/free-adobe-alternative` and year-suffixed copies.

Search observation on 15 October found a mix of comparison publishers, directories, and vendor landing pages: Denoisr, G2, Hilite and SureTake. This was web-search discovery, NOT an ordered or country-controlled Google rank audit. No search volume, domain authority or baseline rank is available yet. Inspect these pages for intent/coverage; do not treat their marketing claims as primary evidence about another product.

## Research findings and implications

| Evidence, checked 15 October 2026                                                                                                                                                                 | Implication                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Google says AI Overviews and AI Mode use the same core SEO eligibility; no special AI schema/text files required. [AI features](https://developers.google.com/search/docs/appearance/ai-features) | Prioritize indexability, internal links, textual answers, original useful media and accurate visible structured data. llms.txt is a convenience, not a ranking strategy. |
| Google recommends original, helpful, people-first content. [Guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)                                            | A practical choice guide with audible evidence beats generic lists. Do not claim author experience or independent testing that did not occur.                            |
| Google's scaled-content and link-spam rules. [Policies](https://developers.google.com/search/docs/essentials/spam-policies)                                                                       | No volume-for-volume publishing, doorway pages, paid ranking links, synthetic reviews, fabricated citations or automated community spam.                                 |
| [Adobe plan table](https://podcast.adobe.com/en/features): free 30 min/500 MB, 1 h/day; Premium 2 h/1 GB, 4 h/day                                                                                 | State plan-specific limits and date the source check. Re-check weekly; do not copy outdated third-party pricing.                                                         |
| Adobe [March 2026 update](https://podcast.adobe.com/en/guides/whats-new-in-adobe-podcast-march-2026): source separation, video/Studio improvements                                                | Position Voicy specifically against Enhance Speech. Acknowledge Adobe's broader workflow.                                                                                |
| [Adobe video guide](https://podcast.adobe.com/en/guides/enhance-speech-for-video): desktop/mobile browser workflow with file upload                                                               | Local privacy is a concrete architectural difference; it is not proof of better audio.                                                                                   |
| [Auphonic pricing](https://auphonic.com/pricing): 2 free hours/month with jingle; [Descript Studio Sound](https://www.descript.com/studio-sound): noise/echo reduction within editing             | Offer honest alternatives by workflow, with primary links and no unsupported quality ranking.                                                                            |
| Voicy [release validation](../release/VALIDATION.md), README, source and existing demo                                                                                                            | Existing reproducible product evidence can support a truthful comparison immediately. Single M5 processing example cannot support broad speed claims.                    |

Competitor discovery references: [Denoisr](https://denoisr.com/alternatives/adobe-podcast-alternative), [G2](https://www.g2.com/products/adobe-podcast/competitors/alternatives), [Hilite](https://www.hellohilite.com/learn/alternatives/adobe-podcast), [SureTake](https://www.suretake.io/blog/best-adobe-podcast-alternative). Full pages for Denoisr, Hilite and SureTake were inspected in this cycle; G2 was assessed from search discovery. Denoisr leads with quotas and a feature matrix plus an upload tool; Hilite emphasizes the broader record-to-publish workflow; SureTake uses a named author and workflow-specific alternatives. Their self-ranked lists do not establish independent superiority. The opportunity is a narrower local/offline comparison with reproducible audio and explicit hardware tradeoffs. Denoisr also makes broad no-transcription assertions that do not describe Adobe Studio accurately; do not repeat them.

## Measurement contract

1. GSC property: URL prefix `https://usevoicy.app/`, verified via domain-name provider. As observed in Chrome: home URL indexed; sitemap successful, 2 discovered pages; performance reports processing. These are independent signals. Unknown metrics remain null, not zero.
2. Export exact query `adobe podcast alternative` plus separate plural/free/Mac/offline variants. Store clicks, impressions, CTR, average position, page, country, device and date range for last 7 days versus prior 7, and last 28 versus prior 28. Do not silently aggregate the exact target with variants or branded queries. Note incomplete days and anonymized/omitted query limitations.
3. Primary outcome: owned usevoicy.app result first among organic web results for the exact query in US English desktop and mobile on three separate dated observations in the final week of December. Record engine, country, language, device, login state, top results and observed URL. GSC exact-query position trends support this; average position is not a universal literal rank. Report failure/partial success if this evidence is absent or mixed. UK and other markets separately.
4. Secondary: comparison-page indexing, nonbrand impressions/clicks, target-query coverage, relevant referring domains with real editorial links, and AI answer citations with model/provider/date/query and source URL. A prompt mentioning Voicy is not a citation. Google's AI traffic is included in GSC Web; do not fabricate a separate AI Overview report.
5. Product outcome: existing daily aggregate pageviews and download starts. They include bots/repeats, are not completed installs, and currently do not identify organic attribution. Do not calculate organic conversion rate from unmatched aggregate counters. Evaluate privacy-preserving route/referrer attribution separately before changing the data contract.
6. Capture private Google account screenshots/exports outside public Git: `/Users/giuseppe/Documents/voicy-growth-evidence/`. Public Git contains sanitized summaries and reproducible scripts only. No browser state, keys, raw account exports, credentials or customer audio.

## Delivery plan

### 15–22 October: foundations and first evidence

- Verify GSC account/property, existing indexing and sitemap; submit the changed sitemap after deployment.
- Ship one indexable comparison page with visible source/method disclosure, accessible original/processed audio, practical comparison, explicit limitations and internal links.
- Add a subtle atmospheric CSS background inspired by Fokly, preserving Voicy layout and readability. No large background movie or third-party tracking.
- Validate desktop/mobile, native audio, links, metadata/canonicals, sitemap, robots, admin exclusions, and download redirect. Test and review before production.
- Recover the performance baseline when GSC processing finishes. Request indexing for the new comparison page once, after live validation; do not repeatedly burn quota.
- Register native automation and verify its persisted active index and future next run. A TOML file alone is not scheduling proof.

### 23 October–5 November: original evidence and distribution readiness

- Reproduce at least 5 short, licensed/consented speech cases: steady fan, room echo, street noise, quiet consonants, and already-clean control. Include human speech/language diversity only with valid reuse rights.
- Preserve original inputs and checksums, exact app/model/settings, hardware, wall time, memory, output, failure cases and full transcripts. Normalize listening loudness without masking artifacts. Run Voicy on each. Adobe comparison only if access and audio upload rights permit; otherwise publish Voicy-only cases and say so.
- Predefine a blind listening protocol and invite independent feedback only after explicit authorization to message people. Do not invent listener panels/MOS/PESQ scores or imply synthetic samples establish real-world superiority.
- Publish a compact reproducible methodology/evidence page when material exists. Add a troubleshooting guide only for distinct demonstrated tasks. Each new URL must answer a real need and have internal links.
- Prepare factual directory submissions/editorial pitches for relevant macOS, open-source audio and privacy publications. No outreach sending is authorized by a generic project takeover. No purchases/subscriptions without a specified budget.
- Evaluate Bing Webmaster Tools import through existing Google authorization, and other search-provider indexability. Do not grant new broad OAuth scopes automatically.

### 6–26 November: learn from demand

- Use actual GSC query/page data to improve missing answers and snippets. Re-check SERP intent and current vendor facts.
- If not indexed after 7 days, inspect live URL/canonical/discovery/Google-selected canonical. Fix technical causes before adding content.
- If indexed without impressions after 14 days, examine intent, editorial differentiation, domain visibility and relevant discovery links. Do not label this a penalty without evidence.
- If position 4–20 with meaningful impressions, improve specific missing evidence and internal links. If top positions with poor CTR, test a truthful title/description once, allow at least 14 days, and record confounders.
- Inspect rich-result eligibility without expecting FAQ rich results for a software vendor; never add fake ratings.

### 27 November–31 December: consolidate and report

- Improve the winning canonical based on evidence; avoid migrations/URL changes without demonstrated need.
- Re-check vendor limits and accessibility; retain speed and platform caveats.
- Final controlled observations in the final week; report exact markets/devices, trends and missing data.
- On/after 31 December publish the owner outcome report and stop the scheduled campaign unless the user extends it. Do not mark goal achieved because the calendar expired.

## Operating loop

Intended cadence: daily 09:15 and 17:15 Europe/Prague, same chat heartbeat. Each cycle read STATE, verify current production/head, obtain fresh relevant data, select one highest-impact evidence-backed action, implement/review/test/ship when justified, verify production, and checkpoint. Avoid changing content twice a day just because the scheduler ran. One weekly owner report on Thursday; other unchanged checks quiet. Notify meaningful ship/regression/action needs with concrete evidence. Native local jobs require Mac and Codex availability.

The user authorizes normal implementation/deployment decisions for Voicy. Preserve dirty work, use isolated branches/worktrees, prefer connectors, and author commits `jindratilk <223098698+jindratilk@users.noreply.github.com>`. Verify repository/team/project each time. Vercel: skaluj / voicy / prj_Y6ykOgCVUFyqZvFMJoA9x0AjvqMF / root landing. Do not alter the desktop app or download worker to chase SEO without separately tested product need. No third-party messages, paid links, budget commitments or permission expansion from the broad mandate alone.

## Experiments

| ID  | Hypothesis                                                                           | Intervention                                                            | Evidence / evaluation                                                                                                             |
| --- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| E01 | A precise comparison satisfies alternative intent better than a brand homepage alone | `/adobe-podcast-alternative`, sources, audio, candid limits, home links | Indexed status first; 14/28-day exact-query impressions/position/clicks after deployment; no causal claim from before/after alone |
| E02 | Atmospheric background improves first impression without harming speed/readability   | Static CSS gradients and tiny data-URI texture                          | Desktop/mobile screenshots, layout/contrast, no new network image or JS dependency; no conversion lift claim without experiment   |
| E03 | Reproducible diverse samples provide value and a reason for editorial citations      | Pending licensed sample set and methodology                             | Artifacts/checksums, negative cases, external citations independently verified                                                    |

Keep STATE.json current with shipped head, deployment, GSC state, scheduler state, blockers and next concrete action. Keep metric exports immutable and dated. Do not overwrite missing outcomes with optimistic prose.
