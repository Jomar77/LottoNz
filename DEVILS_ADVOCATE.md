# Devil's Advocate Review — LottoNz GDPR & Backend Plan

> Reviewed: 2026-06-30. Authored by the devil's advocate agent.
> Purpose: stress-test assumptions before merge to main.

---

## 🚨 CRITICAL — Google AdSense contradicts the privacy policy

**This is not a minor concern. It is an active GDPR violation.**

`Frontend/index.html` loads AdSense unconditionally:

```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2415870612388253" crossorigin="anonymous"></script>
```

`PrivacyModal.tsx` simultaneously states:

> "None. We use no Google Analytics, no ad networks, and no tracking pixels."

This is factually false. AdSense:
- Is an **ad network** (explicitly denied)
- Sets **third-party cookies** on the user's device before any consent is given
- Sends user IP, browser fingerprint, and browsing context to Google servers
- Is subject to GDPR Article 6 (lawful basis) and Article 7 (consent) — **explicit opt-in is required before the script loads**

**Verdict: CRITICAL — merge-blocking**

**Mitigation:** Either remove AdSense entirely, or implement a proper two-tier consent gate (block the script until the user actively accepts advertising cookies). The current "Accept & Close" banner is a notice dismissal, not a GDPR-valid consent mechanism. A valid consent mechanism must be freely given, specific, informed, and unambiguous — the current banner fails all four tests because it loads AdSense regardless of whether the user clicks Accept or the X button.

Also: `index.html` has `<meta name="description" content="Jomar's Portfolio ...">` and `<link rel="canonical" href="https://www.jncrd.dev" />`. These are stale portfolio-site tags that will actively harm SEO and confuse crawlers. Fix alongside the AdSense work.

---

## 1. GDPR Necessity

**Concern:** The target audience is NZ residents. NZ has its own Privacy Act 2020, not GDPR. GDPR applies to EU/EEA residents — even if the site is hosted globally, it only applies when you specifically target or monitor EU individuals. Is there evidence of intentional EU targeting?

**Verdict: MINOR CONCERN**

GDPR technically applies if EU residents access the site and the operator "monitors" their behaviour (Recital 24). AdSense monitoring makes this moot — AdSense triggers GDPR obligations regardless of intended audience. Without AdSense, a purely local NZ site with no analytics would have a reasonable argument that GDPR doesn't apply.

With AdSense in place: GDPR definitely applies. The banner is not optional.

**Mitigation:** Decide: keep AdSense (require real consent) or drop AdSense (GDPR compliance becomes a nice-to-have, not a legal obligation).

---

## 2. The localStorage Claim

**Concern:** The banner says "localStorage only to remember this notice." The privacy policy says one key: `lotto_gdpr_dismissed`. Is this still true after the new engine/strategy UI?

**Verdict: VALID CONCERN (minor)**

User preferences (spread, leaning, consecutive, engine, strategies) are currently held only in React state — they reset on page reload. The design naturally invites persisting them. If any future PR adds `localStorage.setItem('lotto_prefs', ...)`, the privacy disclosure immediately becomes inaccurate without anyone noticing.

**Mitigation:** Add a comment in `App.tsx` near the preferences state explicitly noting "not persisted — update PrivacyModal if this changes." Alternatively, declare the full localStorage namespace in the policy now: "We may store user preferences locally in the future; all storage remains on-device and is never transmitted."

---

## 3. CORS Plan — Env-var Allowlist

**Concern:** Restricting CORS to `localhost:5173` and a production domain via env var is reasonable, but has two gaps:

1. **CI/preview environments:** If Vercel or Netlify spin up preview URLs (e.g. `lotto-pr-42.vercel.app`), the API will reject their requests with a CORS error. This silently breaks PR previews without explanation.
2. **Missing env var in production:** If the `ALLOWED_ORIGINS` env var is not set, what is the fallback? If it defaults to `localhost:5173`, the production API is effectively inaccessible from the production frontend. If it defaults to `*`, the restriction is meaningless.

**Verdict: VALID CONCERN**

**Mitigation:**
- Document the required env var in `.env.example` with a clear comment.
- On startup, log the active CORS origins so operators can verify.
- For preview URLs, support a `ALLOWED_ORIGINS_PATTERN` regex alternative, or accept a comma-separated list that can include wildcards.
- Fail loudly (startup warning, not a silent `*` fallback) when the env var is absent in non-development mode.

---

## 4. Rate Limiting — Multi-Worker Gap

**Concern:** slowapi's default `InMemoryRateLimiter` is per-process. With `uvicorn --workers 4`, each worker runs independently. A user can make 4× the configured rate against the same server by distributing requests across workers (which the OS load-balancer does automatically).

**Verdict: VALID CONCERN**

30 req/min per worker × 4 workers = 120 effective requests/min per IP before any worker refuses. A determined scraper doesn't even need to try.

**On the threshold itself:** 30 req/min is the right order of magnitude for normal use (20 tickets = 1 request, so 30 allows 600 tickets/min, which is absurd for any real user). The problem is multi-worker bypass, not the threshold.

**Mitigation:**
- Use Redis as the slowapi storage backend (`slowapi.util.get_remote_address` + `limits.storage.RedisStorage`). This shares counters across workers.
- If Redis is out of scope, document the multi-worker limitation explicitly in the plan and pin the production deployment to a single worker until Redis is added.

---

## 5. Sitemap for a SPA with One Route

**Concern:** A `sitemap.xml` with one URL (`/`) provides almost no SEO value. Googlebot discovers single-page apps through JavaScript rendering, not XML sitemaps. The maintenance overhead (keeping `lastmod` current, adding new routes if they're added) is disproportionate to the benefit.

**Verdict: MINOR CONCERN**

A sitemap costs almost nothing to add and does no harm. It signals to crawlers that the page exists and when it was last modified, which can marginally help indexing speed. However:
- The canonical URL in `index.html` currently points to `jncrd.dev` (wrong site). Fix that first — a sitemap pointing to the correct domain while the canonical points elsewhere creates a contradictory signal.
- A `robots.txt` alongside the sitemap is more immediately useful.

**Mitigation:** Fix the canonical tag and meta description first. Then add the sitemap. Keep `lastmod` tied to the data refresh date (updated by the scraper cron), not hardcoded.

---

## 6. Merge with No Backend Integration Tests

**Concern:** Merging to main with the API non-functional is explicitly accepted. The risk depends entirely on what the CI pipeline runs.

**Verdict: VALID CONCERN IF CI runs `python -m pytest api/tests/ -q`**

If the GitHub Actions workflow (or equivalent) runs the API tests and the API tests require the API to be up, every merge to main will produce a failing CI badge. This trains the team to ignore red CI, which is a dangerous habit.

**Mitigation:**
- Check `.github/workflows/` for any API test steps. If they exist, either skip them with a condition or mock the dependency.
- Add a `[skip ci]` note to the merge commit if CI is known to fail, and create a tracking issue to restore it.
- The frontend tests (Vitest) and type checks pass cleanly and should be the merge gate for this PR.

---

## Summary Table

| # | Issue | Verdict | Blocking? |
|---|-------|---------|-----------|
| 0 | AdSense loads before consent + privacy policy lies about it | 🚨 CRITICAL | **Yes** |
| 1 | GDPR necessity for NZ-targeted site | MINOR | No |
| 2 | localStorage disclosure accuracy | MINOR | No |
| 3 | CORS env-var missing = silent prod failure | VALID | Plan only |
| 4 | slowapi multi-worker bypass | VALID | Plan only |
| 5 | Sitemap SEO value for SPA | MINOR | No |
| 6 | CI red if API tests run on merge | VALID | Check CI |

**Before merging:** Resolve item 0. Everything else is forward-looking (plan doc) or minor.
