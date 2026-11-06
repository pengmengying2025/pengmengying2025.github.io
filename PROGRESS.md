# PROGRESS — Academic homepage (pengmengying2025.github.io)

al-folio (Jekyll) site. **Live:** https://pengmengying2025.github.io
_At session start, read this file + `git log` to get oriented._

_Last updated: 2026-11-06_

---

## ✅ Done

- **Six pages live** — About · Research · CV · AI in Education · 中文 (Chinese) · Elsewhere.
  Navbar order: **About · Research · CV · AI in Education · 中文 / Chinese · Elsewhere**.
- **Removed all al-folio template leftovers** — demo posts/projects/books/pages/images, the blog & news features, and dark mode (site is now light-only).
- **Real headshot avatar** (`assets/img/mengyingprofile.png`) + **transparent favicon** (`assets/img/laifu_icon_t.png`).
- **Bug fix:** *Mobile dark mode hid CV institution names* — the theme-detecting JS added Bootstrap `table-dark` (white text) to every table on dark-preference devices. Fixed in `assets/js/no_defer.js` (stop adding `table-dark`) + safety net in `_sass/_cv.scss`.
- **Deployment migrated to GitHub Actions Pages** (`build_type: workflow`) — `.github/workflows/deploy.yml` now uses `upload-pages-artifact` + `deploy-pages` instead of the JamesIves push-to-`gh-pages` method. This root-cured the recurring "pages build and deployment" flakiness (previously needed manual re-runs on ~1 of every 2 pushes).
- **2026-11-05, round 1: Research and CV content** (`8e60f94`) — three papers retitled; "Cognitive Skills and Economic Growth" moved to first in Working Papers with "Under review" (bib `note` field); four new WIP entries (six in total); CV paper lists synced, heading now "Works in Progress"; Tsuda appointment, 2027 presentation group and 2026 grants updated.
- **2026-11-05, deploy fix** (`3973156`) — `ubuntu-latest` moved to ubuntu-26.04, which has no Ruby 3.3.5, so every deploy failed at Setup Ruby. Build job in `deploy.yml` pinned to `ubuntu-24.04`.
- **2026-11-05, round 2: page structure** — new AI in Education page (`_pages/ai-in-education.md`); About bio, name pronunciation and contact note (`contact_note` in `_config.yml`) rewritten; 中文 page reduced to the intro plus four articles (Yulai moved to AI in Education); Coffee Map page removed; `sort_by: none`, so Research groups follow `papers.bib` file order; CV Tsuda description line shortened; straight quotes in displayed text replaced with curly ones.
- **2026-11-05, round 3** — About first paragraph rewritten; CV paper lists now built from papers.bib by _plugins/cv-papers.rb.
- **2026-11-05, round 4: redesign** — palette in `_sass/_themes.scss` (primary #233B40, accent #B7533B, background #FCFAF7); self-hosted fonts (headings Newsreader + Noto Serif SC, body Inter + Noto Sans SC), replacing Google Fonts; dark navbar, collapsing below 768px; non-fixed light footer; About opening (name, accent rule, subtitle) with the photo beside the bio and contact details under it; CV without cards, with coauthor links and bold paper titles; AI in Education products as cards, Yulai first; scroll progress bar and MathJax turned off. Page styles are in `_sass/_design.scss`. About text: subtitle added, first sentence of the second bio paragraph and the pronunciation line removed, photo alt text set, Graduate School of Economics linked.
- **2026-11-06, round 5: Elsewhere page** — new page, last in the navbar. Its first section, Fragments, shows ten photos: one full width, the rest in two staggered columns (one on phones), each opening larger on click. Order, captions and alt text are in `_data/fragments.yml`; the web images come from `scripts/build_photos.py` (WebP in two sizes, no metadata), and the originals stay out of the repo. With six links, the navbar now collapses below 992px instead of 768px. Coffee Atlas will be a second section.

## ⏳ To do

- **Around 2026-08-01** (~2 weeks after migration): once the new Actions deployment is confirmed stable, the **`gh-pages` branch can be deleted** (currently kept as a rollback safety net).
- build job 临时固定在 ubuntu-24.04；长期方案是把 Ruby 从 3.3.5 升级到 ubuntu-latest 上可用的版本并完整测一次部署。
  - Together with the Ruby upgrade: `scripts/gen_cv.rb` fails at its last step on a fresh clone, because git does not track the empty `assets/pdf/`. One line of `FileUtils.mkdir_p` fixes it.
  - `Check for broken links on site` 因为 ubuntu-26.04 上没有 Ruby 3.2.2 一直失败，线上链接检查实际上没在跑，升级 Ruby 时一起修。axe 只能手动触发，从没跑过，无障碍检查也没在跑；它的 Ruby 设置相同，升级时一起改，要自动跑还得另外打开触发条件。
  - 修好之前，不要以为死链有人在查。
- Coffee Atlas：作为 Elsewhere 页的第二个小节加入；用一张地图截图作预览，下面放打开完整地图的链接（不嵌入 iframe）；发布前由 MM 检查地图上有没有住处或办公室附近的店。
- **For reference:** the CV PDF's Email line prints raw HTML (`<a href=…>`), because `esc` in `scripts/gen_cv.rb` only handles `<em>`. The PDF is currently unused.

## 🔧 Useful references

- **Deploy:** any push to `main` → `.github/workflows/deploy.yml` builds and publishes via Actions Pages. A successful push is not yet live: check that the Deploy site run finished. The Prettier workflow has failed on every push since at least July; it does not block deploys.
- **Rollback** (only if Actions deploy ever breaks): Settings → Pages → Source → "Deploy from a branch" → `gh-pages` → Save, then `git revert` the deploy.yml migration commit. The `gh-pages` branch still holds the last site.
- **CV content:** `_data/cv.yml`. Regenerate the (currently unused, download button removed) CV PDF with `ruby scripts/gen_cv.rb`.
- **Rule: papers are edited only in `_bibliography/papers.bib`; `_data/cv.yml` no longer holds paper entries.** `_plugins/cv-papers.rb` fills the CV lists at build time.
- **Publications:** `_bibliography/papers.bib` (grouped Published / Working Papers / Works in Progress; each group displays in file order); coauthor homepage links in `_data/coauthors.yml`.
- **Do not link to `/publications/#<bib key>`:** `assets/js/bibsearch.js` treats the URL hash as filter text, so a key matches nothing and the page goes blank. Link to `/publications/` instead.
- **Fonts:** after adding Chinese text, run `python3 scripts/build_fonts.py` and commit `assets/fonts/`. It finds the characters by itself; until it runs, a new character shows in a system font.
- **Photos (Elsewhere, Fragments):** originals stay in `~/Dropbox/个人主页用/photo` and never enter the repo. Edit `_data/fragments.yml`, run `python3 scripts/build_photos.py`, then commit `assets/img/fragments/` and `_data/fragment_images.yml`. A committed image stays in git history for good, so settle the photo list before committing.
- **Curly quotes:** Markdown converts straight quotes on its own, but `_data/cv.yml` and raw HTML blocks do not, so type `“ ” ’` there directly.
- **Math:** `enable_math` in `_config.yml` is off, because no page has a formula. Turn it on when a page needs to display one.
- **Check style changes on a production build plus purgecss, as CI does:** the minifier can break colors that a dev build shows fine (translucent white became invalid CSS), and the local avatar can show as broken without ImageMagick.
- **Local preview:** `bundle exec ruby "$(bundle show jekyll)/exe/jekyll" serve` (the `jekyll` bin isn't on PATH; invoke via the gem's exe).
- `website-redesign-brief.md` (gitignored, local only) is the original spec.
