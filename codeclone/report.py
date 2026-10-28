"""Report: report.html (ranked pairs, side-by-side code, clusters) and a console summary."""

import html

COLORS = ("#ffe08a", "#a8e6cf", "#ffb3c1", "#b5d0ff", "#e0c3fc", "#ffd3a5")


def _line_colors(clones, side):
    """line number -> color, one color per clone, for side 'a' or 'b'."""
    colors = {}
    for k, c in enumerate(clones):
        node = c.node_a if side == "a" else c.node_b
        for line in range(node.start_line, node.end_line + 1):
            colors.setdefault(line, COLORS[k % len(COLORS)])
    return colors


def _code_block(source, colors):
    rows = []
    for no, text in enumerate(source.split("\n"), start=1):
        style = ' style="background:%s"' % colors[no] if no in colors else ""
        rows.append('<span class="ln">%3d</span><span%s>%s</span>' % (no, style, html.escape(text) or " "))
    return "<pre>%s</pre>" % "\n".join(rows)


def write_html(path, files, pairs, flagged, groups, threshold):
    """pairs: all Pair objects ranked; flagged: those >= threshold; groups: lists of file ids."""
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
           "<p>%d files, %d pairs compared, threshold %.0f%%, %d pairs flagged.</p>"
           % (len(files), len(pairs), threshold * 100, len(flagged))]

    out.append("<h2>Plagiarism clusters</h2>")
    if groups:
        out.append("<ol>")
        for g in groups:
            out.append("<li>%s</li>" % ", ".join(html.escape(files[i].name) for i in g))
        out.append("</ol>")
    else:
        out.append("<p>None.</p>")

    out.append("<h2>Ranked pairs</h2><table><tr><th>#</th><th>File A</th><th>File B</th>"
               "<th>Similarity</th><th>Clones</th></tr>")
    for rank, p in enumerate(pairs, start=1):
        cls = ' class="hi"' if p.score >= threshold else ""
        out.append("<tr%s><td>%d</td><td>%s</td><td>%s</td><td>%.1f%%</td><td>%d</td></tr>"
                   % (cls, rank, html.escape(p.file_a.name), html.escape(p.file_b.name),
                      p.score * 100, len(p.clones)))
    out.append("</table>")

    out.append("<h2>Matched code (flagged pairs)</h2>")
    for p in flagged:
        ranges = "; ".join("A %d-%d = B %d-%d (%d nodes)" % (c.node_a.start_line, c.node_a.end_line,
                                                         c.node_b.start_line, c.node_b.end_line, c.node_a.size)
                           for c in p.clones)
        out.append("<details><summary>%s vs %s: %.1f%%</summary><p>%s</p><div class=\"side\">"
                   % (html.escape(p.file_a.name), html.escape(p.file_b.name), p.score * 100, html.escape(ranges)))
        out.append("<div><b>%s</b>%s</div>" % (html.escape(p.file_a.name),
                                                _code_block(p.file_a.source, _line_colors(p.clones, "a"))))
        out.append("<div><b>%s</b>%s</div>" % (html.escape(p.file_b.name),
                                                _code_block(p.file_b.source, _line_colors(p.clones, "b"))))
        out.append("</div></details>")
    out.append("</body></html>")

    with open(path, "w") as f:
        f.write("\n".join(out))


def print_summary(files, flagged, groups, threshold, top=10):
    print("Analysed %d files. %d pairs at or above %.0f%% similarity." % (len(files), len(flagged), threshold * 100))
    for p in flagged[:top]:
        print("  %5.1f%%  %s  <->  %s" % (p.score * 100, p.file_a.name, p.file_b.name))
    if len(flagged) > top:
        print("  ... and %d more (see report)" % (len(flagged) - top))
    print("Clusters:")
    for k, g in enumerate(groups, start=1):
        print("  %d. %s" % (k, ", ".join(files[i].name for i in g)))
    if not groups:
        print("  none")
