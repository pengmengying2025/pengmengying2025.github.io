# PROGRESS — Academic homepage (pengmengying2025.github.io)

al-folio (Jekyll) site. **Live:** https://pengmengying2025.github.io
_At session start, read this file + `git log` to get oriented._

_Last updated: 2026-11-05_

---

## ✅ Done

- **Five pages live** — About · Research · AI in Education · CV · 中文 (Chinese).
  Navbar order: **About · Research · AI in Education · CV · 中文 / Chinese**.
- **Removed all al-folio template leftovers** — demo posts/projects/books/pages/images, the blog & news features, and dark mode (site is now light-only).
- **Real headshot avatar** (`assets/img/mengyingprofile.png`) + **transparent favicon** (`assets/img/laifu_icon_t.png`).
- **Bug fix:** *Mobile dark mode hid CV institution names* — the theme-detecting JS added Bootstrap `table-dark` (white text) to every table on dark-preference devices. Fixed in `assets/js/no_defer.js` (stop adding `table-dark`) + safety net in `_sass/_cv.scss`.
- **Deployment migrated to GitHub Actions Pages** (`build_type: workflow`) — `.github/workflows/deploy.yml` now uses `upload-pages-artifact` + `deploy-pages` instead of the JamesIves push-to-`gh-pages` method. This root-cured the recurring "pages build and deployment" flakiness (previously needed manual re-runs on ~1 of every 2 pushes).
- **2026-11-05, round 1: Research and CV content** (`8e60f94`) — three papers retitled; "Cognitive Skills and Economic Growth" moved to first in Working Papers with "Under review" (bib `note` field); four new WIP entries (six in total); CV paper lists synced, heading now "Works in Progress"; Tsuda appointment, 2027 presentation group and 2026 grants updated.
- **2026-11-05, deploy fix** (`3973156`) — `ubuntu-latest` moved to ubuntu-26.04, which has no Ruby 3.3.5, so every deploy failed at Setup Ruby. Build job in `deploy.yml` pinned to `ubuntu-24.04`.
- **2026-11-05, round 2: page structure** — new AI in Education page (`_pages/ai-in-education.md`); About bio, name pronunciation and contact note (`contact_note` in `_config.yml`) rewritten; 中文 page reduced to the intro plus four articles (Yulai moved to AI in Education); Coffee Map page removed; `sort_by: none`, so Research groups follow `papers.bib` file order; CV Tsuda description line shortened; straight quotes in displayed text replaced with curly ones.

## ⏳ To do

- **Photographs page** (navbar position TBD) — *waiting on photos from MM.* Decisions to make first: group the photos or not? add captions/text or not?
- **Around 2026-08-01** (~2 weeks after migration): once the new Actions deployment is confirmed stable, the **`gh-pages` branch can be deleted** (currently kept as a rollback safety net).
- build job 临时固定在 ubuntu-24.04；长期方案是把 Ruby 从 3.3.5 升级到 ubuntu-latest 上可用的版本并完整测一次部署。
- **Undecided:** have the CV paper lists read from `papers.bib`. Assessed in round 1, not implemented: a build-time plugin fills the lists; `scripts/gen_cv.rb` must change with it or it crashes. In a scratch copy the plugin reproduced the CV page byte for byte.

## 🔧 Useful references

- **Deploy:** any push to `main` → `.github/workflows/deploy.yml` builds and publishes via Actions Pages. A successful push is not yet live: check that the Deploy site run finished. The Prettier workflow has failed on every push since at least July; it does not block deploys.
- **Rollback** (only if Actions deploy ever breaks): Settings → Pages → Source → "Deploy from a branch" → `gh-pages` → Save, then `git revert` the deploy.yml migration commit. The `gh-pages` branch still holds the last site.
- **CV content:** `_data/cv.yml`. Its paper lists are a separate copy, kept in sync with `papers.bib` by hand. Regenerate the (currently unused, download button removed) CV PDF with `ruby scripts/gen_cv.rb`.
- **Publications:** `_bibliography/papers.bib` (grouped Published / Working Papers / Works in Progress; each group displays in file order); coauthor homepage links in `_data/coauthors.yml`.
- **Do not link to `/publications/#<bib key>`:** `assets/js/bibsearch.js` treats the URL hash as filter text, so a key matches nothing and the page goes blank. Link to `/publications/` instead.
- **Curly quotes:** Markdown converts straight quotes on its own, but `_data/cv.yml` and raw HTML blocks do not, so type `“ ” ’` there directly.
- **Local preview:** `bundle exec ruby "$(bundle show jekyll)/exe/jekyll" serve` (the `jekyll` bin isn't on PATH; invoke via the gem's exe).
- `website-redesign-brief.md` (gitignored, local only) is the original spec.
