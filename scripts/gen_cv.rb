#!/usr/bin/env ruby
# Regenerate the CV PDF from _data/cv.yml (single source of truth).
#
# Usage (from the repo root; requires a TeX distro with `xelatex` on PATH):
#     ruby scripts/gen_cv.rb
#
# Output: assets/pdf/Mengying_Peng_CV.pdf
#
# Edit _data/cv.yml, re-run this script, and the web CV and the downloadable
# PDF stay in sync. (The download button itself is wired via `cv_pdf:` in
# _pages/cv.md — currently disabled.)

require 'yaml'
require 'tmpdir'
require 'fileutils'

ROOT = File.expand_path('..', __dir__)
CV = YAML.load_file(File.join(ROOT, '_data', 'cv.yml'))

def esc(s)
  s = s.to_s
  s = s.gsub('<em>', "\x01").gsub('</em>', "\x02")
  repl = { '\\' => '\textbackslash{}', '&' => '\&', '%' => '\%', '$' => '\$',
           '#' => '\#', '_' => '\_', '{' => '\{', '}' => '\}',
           '~' => '\textasciitilde{}', '^' => '\textasciicircum{}' }
  s = s.chars.map { |c| repl[c] || c }.join
  s.gsub("\x01", '\emph{').gsub("\x02", '}')
end

def render_time_table(sec)
  out = []
  sec['contents'].each do |e|
    if e.key?('items')
      out << "\\textbf{#{esc(e['year'])}}"
      out << '\begin{itemize}'
      e['items'].each { |it| out << "\\item #{esc(it)}" }
      out << '\end{itemize}'
    else
      title = esc(e['title'])
      yr = e['year']
      out << (yr ? "\\noindent\\textbf{#{title}}\\hfill #{esc(yr)}\\\\" : "\\noindent\\textbf{#{title}}\\\\")
      out << "\\textit{#{esc(e['institution'])}}" if e['institution']
      if e['description']
        out << '\begin{itemize}'
        e['description'].each do |d|
          if d.is_a?(Hash)
            out << "\\item #{esc(d['title'])}"
            if d['contents']
              out << '\begin{itemize}'
              d['contents'].each { |sub| out << "\\item #{esc(sub)}" }
              out << '\end{itemize}'
            end
          else
            out << "\\item #{esc(d)}"
          end
        end
        out << '\end{itemize}'
      end
      out << '\par\smallskip'
    end
  end
  out.join("\n")
end

def render_list(sec)
  (['\begin{itemize}'] + sec['contents'].map { |c| "\\item #{esc(c)}" } + ['\end{itemize}']).join("\n")
end

def render_map(sec)
  sec['contents'].reject { |c| c['name'] == 'Full Name' }
                 .map { |c| "\\textbf{#{esc(c['name'])}:} #{esc(c['value'])}\\par" }.join("\n")
end

full_name = CV.find { |s| s['type'] == 'map' }
              &.dig('contents')&.find { |c| c['name'] == 'Full Name' }&.dig('value') || 'Mengying Peng'

body = []
CV.each do |sec|
  body << "\\cvsection{#{esc(sec['title'])}}"
  case sec['type']
  when 'map'        then body << render_map(sec)
  when 'time_table' then body << render_time_table(sec)
  else                   body << render_list(sec)
  end
end

preamble = <<~'TEX'
  \documentclass[11pt]{article}
  \usepackage[margin=0.8in]{geometry}
  \usepackage{fontspec}
  \usepackage{enumitem}
  \setlist[itemize]{leftmargin=1.4em, itemsep=0.5pt, topsep=1.5pt, parsep=0pt}
  \usepackage[hidelinks]{hyperref}
  \setlength{\parindent}{0pt}
  \pagestyle{empty}
  \newcommand{\cvsection}[1]{\vspace{1.0ex}{\large\bfseries #1}\par\vspace{-0.5ex}\rule{\linewidth}{0.6pt}\vspace{0.7ex}\par}
  \begin{document}
TEX

title_block = "\\begin{center}\n{\\huge\\bfseries #{esc(full_name)}}\\\\[3pt]\n{\\large Curriculum Vitae}\n\\end{center}\n\\vspace{0.5ex}\n"

doc = preamble + title_block + body.join("\n") + "\n\\end{document}\n"

Dir.mktmpdir('cvbuild') do |dir|
  tex = File.join(dir, 'cv.tex')
  File.write(tex, doc)
  2.times { system('xelatex', '-interaction=nonstopmode', '-halt-on-error', '-output-directory', dir, tex, out: File::NULL) }
  pdf = File.join(dir, 'cv.pdf')
  abort 'xelatex failed — is it installed and on PATH?' unless File.exist?(pdf)
  out = File.join(ROOT, 'assets', 'pdf', 'Mengying_Peng_CV.pdf')
  FileUtils.cp(pdf, out)
  puts "Wrote #{out}"
end
