# PROGRESS — Academic homepage (pengmengying2025.github.io)

al-folio (Jekyll) site. **Live:** https://pengmengying2025.github.io
_At session start, read this file + `git log` to get oriented._

_Last updated: 2026-07-18_

---

## ✅ Done

- **Five pages rebuilt and live** — About · Research · CV · 中文 (Chinese) · Coffee Map.
  Navbar order: **About · Research · CV · 中文 / Chinese · Coffee Map**.
- **Removed all al-folio template leftovers** — demo posts/projects/books/pages/images, the blog & news features, and dark mode (site is now light-only).
- **Real headshot avatar** (`assets/img/mengyingprofile.png`) + **transparent favicon** (`assets/img/laifu_icon_t.png`).
- **Bug fixes:**
  - *Mobile dark mode hid CV institution names* — the theme-detecting JS added Bootstrap `table-dark` (white text) to every table on dark-preference devices. Fixed in `assets/js/no_defer.js` (stop adding `table-dark`) + safety net in `_sass/_cv.scss`.
  - *Coffee Map blank on mobile* — Google My Maps iframe. Fixed in `_pages/coffee-map.md`: dropped `loading="lazy"` and the account-scoped `/u/0/` URL, added `referrerpolicy` + explicit size.
- **Deployment migrated to GitHub Actions Pages** (`build_type: workflow`) — `.github/workflows/deploy.yml` now uses `upload-pages-artifact` + `deploy-pages` instead of the JamesIves push-to-`gh-pages` method. This root-cured the recurring "pages build and deployment" flakiness (previously needed manual re-runs on ~1 of every 2 pushes).

## ⏳ To do

- **Photographs page** (nav_order **4**, slots between 中文 and Coffee Map) — *waiting on photos from MM.* Decisions to make first: group the photos or not? add captions/text or not?
- **Around 2026-08-01** (~2 weeks after migration): once the new Actions deployment is confirmed stable, the **`gh-pages` branch can be deleted** (currently kept as a rollback safety net).

## 🔧 Useful references

- **Deploy:** any push to `main` → `.github/workflows/deploy.yml` builds and publishes via Actions Pages. No manual steps; no more re-runs needed.
- **Rollback** (only if Actions deploy ever breaks): Settings → Pages → Source → "Deploy from a branch" → `gh-pages` → Save, then `git revert` the deploy.yml migration commit. The `gh-pages` branch still holds the last site.
- **CV content:** `_data/cv.yml`. Regenerate the (currently unused, download button removed) CV PDF with `ruby scripts/gen_cv.rb`.
- **Publications:** `_bibliography/papers.bib` (grouped Published / Working Papers / Works in Progress); coauthor homepage links in `_data/coauthors.yml`.
- **Local preview:** `bundle exec ruby "$(bundle show jekyll)/exe/jekyll" serve` (the `jekyll` bin isn't on PATH; invoke via the gem's exe).
- `website-redesign-brief.md` (gitignored, local only) is the original spec.
