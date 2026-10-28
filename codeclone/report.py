"""Report: report.html (ranked pairs, side-by-side code, clusters) and a console summary."""

import html

COLORS = ("#ffe08a", "#a8e6cf", "#ffb3c1", "#b5d0ff", "#e0c3fc", "#ffd3a5")


def _line_colors(matches, side):
    """line number -> color, one color per match, for side 'a' or 'b'."""
    colors = {}
    for k, m in enumerate(matches):
        lo, hi = (m.a_start, m.a_end) if side == "a" else (m.b_start, m.b_end)
        for line in range(lo, hi + 1):
            colors.setdefault(line, COLORS[k % len(COLORS)])
    return colors


def _code_block(source, colors):
    rows = []
    for no, text in enumerate(source.split("\n"), start=1):
        style = ' style="background:%s"' % colors[no] if no in colors else ""
        rows.append('<span class="ln">%3d</span><span%s>%s</span>' % (no, style, html.escape(text) or " "))
    return "<pre>%s</pre>" % "\n".join(rows)


def write_html(path, result, sources):
    """result: AnalysisResult; sources: file name -> source text."""
    threshold = result.threshold
    flagged = result.flagged_pairs()
    out = ["""<!doctype html><html><head><meta charset="utf-8"><title>CodeClone Report</title>
<style>
body{font-family:system-ui,sans-serif;margin:24px;background:#fafafa;color:#222}
table{border-collapse:collapse;margin-bottom:24px}td,th{border:1px solid #ccc;padding:4px 10px}
th{background:#eee}.hi{color:#b00020;font-weight:bold}
.side{display:flex;gap:12px}.side>div{flex:1;min-width:0}
pre{background:#fff;border:1px solid #ddd;padding:8px;overflow-x:auto;font-size:13px}
.ln{color:#999;margin-right:10px;user-select:none}details{margin-bottom:12px}
summary{cursor:pointer;font-weight:bold}
</style></head><body>""",
           "<h1>CodeClone Detector report</h1>",
           "<p>%d files, %d pairs scored (%d skipped by the index), threshold %.0f%%, %d pairs flagged.</p>"
           % (len(result.files), len(result.pairs), result.stats["pairs_skipped"], threshold * 100, len(flagged))]

    if result.errors:
        out.append("<h2>Files that could not be parsed</h2><ul>")
        for name, err in result.errors.items():
            out.append("<li>%s: %s</li>" % (html.escape(name), html.escape(err)))
        out.append("</ul>")

    out.append("<h2>Plagiarism clusters</h2>")
    if result.clusters:
        out.append("<ol>")
        for g in result.clusters:
            out.append("<li>%s</li>" % ", ".join(html.escape(name) for name in g))
        out.append("</ol>")
    else:
        out.append("<p>None.</p>")

    out.append("<h2>Ranked pairs</h2><table><tr><th>#</th><th>File A</th><th>File B</th>"
               "<th>Score</th><th>Dice</th><th>Containment</th><th>LCS</th><th>Winnow</th><th>Clones</th></tr>")
    for rank, p in enumerate(result.pairs, start=1):
        cls = ' class="hi"' if p.score >= threshold else ""
        sig = "".join("<td>%.0f%%</td>" % (p.signals[k] * 100) for k in ("dice", "containment", "lcs", "winnow"))
        out.append("<tr%s><td>%d</td><td>%s</td><td>%s</td><td>%.1f%%</td>%s<td>%d</td></tr>"
                   % (cls, rank, html.escape(p.a), html.escape(p.b), p.score * 100, sig, len(p.matches)))
    out.append("</table>")

    out.append("<h2>Matched code (flagged pairs)</h2>")
    for p in flagged:
        ranges = "; ".join("A %d-%d = B %d-%d (%d nodes)" % (m.a_start, m.a_end, m.b_start, m.b_end, m.size)
                           for m in p.matches)
        out.append("<details><summary>%s vs %s: %.1f%%</summary><p>%s</p><div class=\"side\">"
                   % (html.escape(p.a), html.escape(p.b), p.score * 100, html.escape(ranges)))
        out.append("<div><b>%s</b>%s</div>" % (html.escape(p.a), _code_block(sources[p.a], _line_colors(p.matches, "a"))))
        out.append("<div><b>%s</b>%s</div>" % (html.escape(p.b), _code_block(sources[p.b], _line_colors(p.matches, "b"))))
        out.append("</div></details>")
    out.append("</body></html>")

    with open(path, "w") as f:
        f.write("\n".join(out))


def print_summary(result, top=10):
    flagged = result.flagged_pairs()
    s = result.stats
    print("Analysed %d files: %d pairs scored, %d skipped by the index (%.3fs)."
          % (s["files"], s["pairs_scored"], s["pairs_skipped"], result.timing["total"]))
    print("%d pairs at or above %.0f%% similarity." % (len(flagged), result.threshold * 100))
    for p in flagged[:top]:
        print("  %5.1f%%  %s  <->  %s" % (p.score * 100, p.a, p.b))
    if len(flagged) > top:
        print("  ... and %d more (see report)" % (len(flagged) - top))
    print("Clusters:")
    for k, g in enumerate(result.clusters, start=1):
        print("  %d. %s" % (k, ", ".join(g)))
    if not result.clusters:
        print("  none")
