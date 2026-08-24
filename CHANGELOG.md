# CHANGELOG — Signs-of-Life crawler fixes (net-knowledge fork)

Changes layered on top of `CENTRprojects/Signs-of-life`. Each entry says **what**, **which file(s)**, and **why**. Items marked ⚠️ are load-bearing — removing them silently reintroduces a real bug, so review carefully before dropping any during a merge.

> Config knob names below are indicative — confirm the exact identifiers against `app_domains/config.py` when merging.

## Data completeness
- **Persist all computed feature columns** — `formatting.py`, `output_processing.py`. The DB insert was built only from `TABLEAU_COLUMNS`, silently dropping ~10 columns the crawler already computed: `n_words, n_letter, links, headers, cookies, park_service, tag_quantity, url_history, flag_js_found, ind_non_schema`. Added to the write path. `headers`/`cookies` were being discarded in `to_csv()`; `links` was never surfaced — both wired through.
- ⚠️ **`date` column now populated** — `output_processing.py`. `date` was never in `TABLEAU_COLUMNS`, so it was omitted from every insert (NULL on the remote DB; insert-time `now()` locally). Now hardcoded into the insert, value from `RowDate()` which parses the `YYYY-MM-DD` filename prefix (falls back to `date.today()`). This also **restores the `ON CONFLICT (filename,date,input_url) DO NOTHING` dedup**, which was defeated while `date` was NULL.

## Stability
- **Entrypoint crash-loop fixed** — `.docker/bin/entrypoint.sh`. Self-recursion → `while` loop, plus an empty-`data/` glob guard. The old code blew the stack (~1000 cycles) and exited.
- **Browser watchdog** — `url_visitor.py`. An unbounded `webdriver.quit()` could hang the whole browser-fallback batch; added a hard-timeout watchdog.

## Anti-blocking (first pass)
- **Realistic request identity + retries** — `url_visitor.py`, `config.py`. Rotating browser User-Agents + browser-like headers; backoff/retry on 429 and 5xx; Selenium browser fallback on 403. Recovers real content from sites that reject a plain request.

## Classification accuracy (load-bearing gates)
- ⚠️ **Interstitial gate** — `classification_parked.py`, `formatting.py`. Challenge/error pages (Cloudflare "Just a moment"/"Attention Required", Vercel checkpoint, Incapsula, ISP placeholders, Cloudflare 5xx) are detected and routed to *blocked*, NOT counted as content/parked. Without it, block pages get misclassified as real content across the whole corpus (including major sites). Do not remove.
- ⚠️ **Empty-page gate** — `formatting.py`. A 200 response rendering ~0 visible words is no longer defaulted to "High content" (`EMPTY_WORD_THRESHOLD`). The original emptiness check was skipped whenever JS/iframe was present (i.e. almost always). **Ordering matters:** the word-count floor must NOT override a positive Parked-Notice-Registrar / Parked-Notice-Individual / ML-park detection — those exclusions are deliberate.
- **Reclassification on browser-fallback success** — `classification_parked.py`. Real content fetched via the browser fallback is promoted to Content instead of left stamped as an error.
- **Registrar validator fix** — `classification_parked.py`. Word/tag-count overrides were unreachable dead code after an `elif pred_ml_park`; reordered so they run.
- ⚠️ **Thin-block gate** — `formatting.py`, `config.py`. A page whose **terminal** status ∈ `BLOCKED_STATUS_CODES` and whose `n_words` ≤ threshold is classified blocked even when a retry cleared the error comment. Catches thin 403/interstitial pages that would otherwise read as High content.

## Blocked classification for the proxy second-pass (⚠️ the whole point of the pipeline)
All block-detection paths converge on machine-actionable `category_lv3` values that the proxy second-pass filters on:
- **`bot_blocked`** — a real site rejecting the crawler's bot/IP: terminal status in `BOT_BLOCKED_STATUS_CODES` (403/429/503), OR a detected bot-challenge/checkpoint (Cloudflare "Just a moment"/"Attention Required", Vercel, Incapsula), OR the thin-block gate. **The proxy pass re-crawls ONLY these** (`WHERE category_lv3 = 'bot_blocked'`).
- **`unreachable`** — Cloudflare origin errors in `ORIGIN_ERROR_STATUS_CODES` (520–527, 530): the origin server is down/misconfigured, so a proxy cannot help. **Not retried.**
- `lv4` carries the human-readable detail (`Blocked_Interstitial` / `Origin_Error`); `lv3` carries the actionable value.
- ⚠️ Do not rename these `lv3` strings without updating the proxy-pass filter. Connection/timeout/DNS errors are intentionally left in their existing categories (not `bot_blocked`).

## Config knobs added — `config.py`
Indicative: `ENABLE_UA_ROTATION`, `UA_POOL`, `MAX_RETRIES_429`, `MAX_RETRIES_5XX`, `ENABLE_BROWSER_ON_403`, `EMPTY_WORD_THRESHOLD`, `BLOCKED_STATUS_CODES`, `BOT_BLOCKED_STATUS_CODES`, `ORIGIN_ERROR_STATUS_CODES`, `RENDER_TIMEOUT_SECONDS`, `MAX_RETRIES_CONNECTION`.

## Pre-existing local tweaks (NOT part of this work — already in the deployed copy)
`output_processing.py`: the 5,000,000-char batch-flush threshold and the `$_$null$_$`→`null` replacement predate these changes. Preserve them on merge.

## Known limitations / deferred
- **Text-extraction under-count** on JS / block-editor pages (real content can read as too few words → misrouted). Highest-value next fix; measure scale before changing, since it touches every domain's features.
- **IPv6 fallback** for dual-stack domains (false connection errors where the host has no IPv6 egress and no IPv4 fallback).
- **`park_service`** computation populates on the wrong rows.
- **Proxy second pass** (Proxyseller): re-crawls `category_lv3 = 'bot_blocked'` only.
