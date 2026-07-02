---
layout: page
permalink: /publications/
title: Research
nav: true
nav_order: 1
---

<!-- _pages/publications.md -->

<!-- Bibsearch Feature -->

{% include bib_search.liquid %}

<div class="publications">

<h2 class="bibliography">Published</h2>
{% bibliography --query @*[category=published] %}

<h2 class="bibliography">Working Papers</h2>
{% bibliography --query @*[category=working] %}

<h2 class="bibliography">Works in Progress</h2>
{% bibliography --query @*[category=wip] %}

</div>
