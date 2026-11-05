# Fills the CV's paper lists from _bibliography/papers.bib, so papers are edited
# in one place only. A section in _data/cv.yml opts in with
# `bib_category: published | working | wip`; its `contents` is built here, in
# file order. scripts/gen_cv.rb also uses this module, without Jekyll.
require 'bibtex'

module CvPapers
  OWNER = { first: 'Mengying', last: 'Peng' }.freeze
  CATEGORIES = %w[published working wip].freeze

  module_function

  # `links` is _data/coauthors.yml on the web CV, where names link as on the
  # Research page. It is nil for the PDF, which takes plain text.
  def person(name, links)
    label = "#{name.first} #{name.last}"
    return label unless links

    candidates = Array(links[I18n.transliterate(name.last.to_s.downcase)])
    match = candidates.find { |c| Array(c['firstname']).include?(name.first.to_s) }
    match ? %(<a href="#{match['url']}">#{label}</a>) : label
  end

  def coauthors(entry, links)
    names = entry.author.to_a
                 .reject { |n| n.first.to_s == OWNER[:first] && n.last.to_s == OWNER[:last] }
                 .map { |n| person(n, links) }
    return names.join(' and ') if names.size <= 2

    "#{names[0..-2].join(', ')}, and #{names[-1]}"
  end

  # Published: "Title, with A, <em>Journal</em>, 2025."
  # Otherwise: "Title — with A and B" plus ". <em>Under review</em>" if there is a note.
  # On the web CV the title is bold and the note carries a class for its color.
  def line(entry, links)
    title = entry[:title].to_s
    title = "<strong>#{title}</strong>" if links
    with = coauthors(entry, links)
    if entry.field?(:journal)
      parts = [title]
      parts << "with #{with}" unless with.empty?
      parts << "<em>#{entry[:journal]}</em>" << entry[:year].to_s
      "#{parts.join(', ')}."
    else
      text = with.empty? ? title : "#{title} — with #{with}"
      return text unless entry.field?(:note)

      links ? %(#{text}. <em class="paper-note">#{entry[:note]}</em>) : "#{text}. <em>#{entry[:note]}</em>"
    end
  end

  # A paper with any other category would silently vanish from Research and the CV.
  def validate!(entries, bib_path)
    bad = entries.reject { |e| CATEGORIES.include?(e[:category].to_s) }
    return if bad.empty?

    details = bad.map { |e| "#{e.key} (#{e[:category] ? "category=#{e[:category]}" : 'no category'})" }
    raise "cv-papers: #{bib_path}: category must be #{CATEGORIES.join(' / ')}; bad entries: #{details.join(', ')}"
  end

  # The latex filter matches jekyll-scholar's, so both pages read the same text.
  def fill!(sections, bib_path, links: nil)
    entries = BibTeX.open(bib_path, filter: :latex).select { |e| e.is_a?(BibTeX::Entry) }
    validate!(entries, bib_path)
    sections.each do |section|
      category = section['bib_category']
      next unless category

      matching = entries.select { |e| e[:category].to_s == category }
      raise "cv-papers: no entries in #{bib_path} with category=#{category}" if matching.empty?

      section['contents'] = matching.map { |e| line(e, links) }
    end
  end
end

if defined?(Jekyll)
  class CvPapersGenerator < Jekyll::Generator
    priority :highest

    def generate(site)
      sections = site.data['cv']
      CvPapers.fill!(sections, site.in_source_dir('_bibliography', 'papers.bib'), links: site.data['coauthors'] || {})
      filled = sections.select { |s| s['bib_category'] }
                       .map { |s| "#{s['title']}=#{s['contents'].size}" }
      Jekyll.logger.info 'CV papers:', filled.join(', ')
    end
  end
end
