# Project Plan — Document Explainer

Working development plan. Product: a web tool that explains official US letters in
plain language + translation + what to do. Audience: newcomers.

**Context:** proof-of-work for a Claude Corps application (deadline July 17, 2026).
Stage 1 + a screenshot is enough for the application; Stages 2-3 strengthen it but
aren't critical under the deadline.

---

## Stage 0 — MVP (done, July 14)

Text version: paste a letter → explanation (4 blocks) + translation.
- Flask + Claude (`claude-sonnet-5`), English UI, language dropdown + "other"
- Demo mode without a key, API error handling, 8000-char input limit + counter
- 18/18 tests, desktop + mobile checked, git (2 commits)

---

## Stage 1 — Bring it to life with a key (done, July 14)

Goal: demo answers replaced with real Claude calls.

1. Key at console.anthropic.com, ~$5 added → **verify:** key created
2. `cp .env.example .env`, set `ANTHROPIC_API_KEY=...` → **verify:** `.env` exists, git ignores it
3. `uv run python -m src.app` → localhost:5000 → **verify:** server up
4. Paste a real letter (or from `docs/example-letters.md`) → **verify:** response is NOT demo, all 4 blocks make sense, translation is correct
5. Check 2-3 letter types (DMV / IRS / lease) in different languages → **verify:** quality holds up
6. Screenshot of a live result → **verify:** have an image for the application

---

## Stage 2 — File upload (done)

Implemented: photo/PDF upload (drag&drop + button), Claude vision reads the image/PDF
directly (no separate OCR). Type and size validation (≤8 MB). 24/24 tests. Verified
live: a real photo of a letter → correct explanation + translation, honestly flagged
an unreadable fragment instead of hallucinating. Screenshot: `A:\Claude\letter-explainer-FILE.png`.

The key insight: **no separate OCR needed** — Claude reads images and PDFs natively.

**Backend:**
- Route by file type → the right Claude content block:
  - JPEG/PNG → image block (base64 + media_type)
  - PDF → document block (base64) — Claude reads it directly
  - (optional) text-based PDF → extract text via `pypdf` if we want it cheaper
- Validation: file type + size (image ≤ ~5 MB, PDF ≤ ~32 MB / page limit)
- Same system prompt, only the input changes
- Demo fallback for building without a key (like Stage 0)

**Frontend:**
- Upload button + drag&drop; on mobile, photo from camera (`accept="image/*" capture`)
- Filename preview, read as base64
- Toggle: "paste text" OR "upload a file"

**Tests + verify:**
- Upload a JPEG letter → meaningful explanation
- Upload a PDF → same
- Oversized/unsupported file → clear error
- Route tests (demo mode), full suite green

**Notes:** images/PDFs cost more in tokens (pennies for a demo); base64 inflates the
payload (multipart later for larger files); cap PDF page count.

---

## Stage 3 — Public link (done, July 14)

**URL: https://document-explainer-production.up.railway.app**

- Hosting: Railway (project `document-explainer`, CLI was already set up)
- Production server: gunicorn (1 worker, 4 threads) instead of the Flask dev server
- Rate limit: 10/min, 50/day per IP (Flask-Limiter) — protects against abuse
- $10/month spend limit on the key (set in the Anthropic console)
- Key rotated (the old one, exposed in chat, was revoked) and stored only as a
  Railway environment secret — not in code, not in git
- **Verify passed:** a real call through the public URL — correct explanation
  + Russian translation, no demo mode

---

## Stage 4 — Polish (optional, if time allows)

- "Copy" button for the result
- More languages / auto-detect the letter's language
- Light branding (name, logo)
- Privacy note (files aren't stored)

---

## Priorities under the July 17 deadline

1. **Required:** Stage 1 (live text version + screenshot) — enough for the application
2. **Strongly recommended:** Stage 2 (files) — a noticeably stronger demonstration
3. **Bonus:** Stage 3 (public link) — if time allows
4. Stage 4 — after submitting
