# E41 changed-runtime result

Audited on 25 October 2026. **The overall qualification failed:** macOS 14
completed the declared case and export; macOS 15 stopped on critical system
memory pressure. A passing matrix job does not replace the other result.

The [frozen protocol](E41-RUNTIME-QUALIFICATION.md) and
[sole run 40107471282](https://github.com/jindratilk/voicy/actions/runs/40107471282)
bind attempt 1 to source `ef73cf362437d52584a3f2519a34000e419ca1f9` and tag
`voicy-runtime-e41-20261024`. Both preceding E40 preparation failures remain
preserved. Neither experiment was rerun or retagged.

## Observed outcomes

| Check | macOS 14.8.9 arm64 | macOS 15.7.9 arm64 |
| --- | --- | --- |
| Job | 120912037936 | 120912038004 |
| Encrypted artifact | 12565856294 | 12565414586 |
| Inventory entries independently verified | 85 | 79 |
| Original input/reference file hashes verified | 10 | 10 |
| Model records checked in original and copied runtime | 18 + 18 | 18 + 18 |
| Approved package changes | Exactly the declared 10 | Exactly the declared 10 |
| Unrelated distributions | Unchanged | Unchanged |
| Existing real-MLX regression tests | 4 passed, none skipped | 4 passed, none skipped |
| Original case 1 model execution | Completed | Started, then stopped by guard |
| Actual PCM24 export | Passed | Not reached |
| Detach error recorded | No | No |

Both artifact ZIPs match GitHub's reported SHA256. Each encrypted payload,
recipient, decrypted archive, receipt, inventory and exact file set was checked.
Execution ledgers, predecessor identity and protocol hashes match. Raw logs,
audio and account evidence remain outside public Git.

Both cases used the original runner, model assets and input; Base32, q8,
group64, seed2026, guidance2 and the original automatic memory policy remain
unchanged. Both used the nonresident policy. These are not matched old/new
dependency performance comparisons.

## macOS 14 completed output

Independent FFprobe and FFmpeg decoding verified the actual files:

- Raw output: mono 24 kHz float32, 117,720 frames, all finite, nonzero,
  zero clipped samples. SHA256:
  `97ba8da28f0fe035883b053cf9cd6bb35ff9915e3d0e98d844233ea788dd6b1e`.
- Export: mono 48 kHz PCM24, 235,440 frames, all finite, nonzero,
  zero clipped samples. SHA256:
  `007d9ee8f04e7fb88e9d50af5be51e14ad2d02a3e7a35c1f252b157cd3eedafc`.

The source signed application remained unchanged. This qualifies one declared
case and export in an unsigned runtime copy on this host, not a new signed app.

## macOS 15 guarded stop

The controller recorded `memory_pressure=4` after the model started and
terminated the worker through its existing cleanup path. At the stop there
were 29,289,295,872 free bytes, above the unchanged 12 GiB disk guard: this was
a critical memory-pressure stop, not insufficient disk space. No completed
model output or export exists. Both hosted guests reported 7 GiB total memory;
the product recommends 16 GB or more.

Do not attribute the pressure event to a particular dependency, OS regression
or model operation from this single observation. The two host outcomes do not
establish such a cause, and the failed case must not be substituted with a
favourable host or replayed with weaker guards.

## Remaining release gate

Keep public 0.3.3 available. No new installer, signature, notarization, complete
five-case qualification, desktop GUI acceptance or audio publication follows
from E41. Human quality, consumer speed and ranking were not measured.

A future release qualification needs independently available adequate capacity
and a separately reviewed declaration for the actual changed app. Preserve
the existing disk, pressure, RSS and time limits, original failures and protected
signing process. Current local disk capacity remains below the existing guard;
no paid capacity, unrelated deletion or guard reduction was used.
