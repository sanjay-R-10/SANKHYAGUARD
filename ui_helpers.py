from html import escape


def indian(n):
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


CSS = """<style>
.d{display:inline-block;min-width:1.5em;padding:.25em .1em;margin:2px;text-align:center;border-radius:6px;
   background:#1e293b;color:#e2e8f0;font-family:monospace;font-size:1.25em;}
.bad{background:#991b1b;color:#fee2e2;font-weight:700;}
.card{border-radius:12px;padding:12px 18px;margin:6px 0;}
.ok{background:#052e16;border:1px solid #166534;color:#dcfce7;}
.ask{background:#422006;border:1px solid #a16207;color:#fef3c7;}
.plain{background:#1e293b;border:1px solid #334155;color:#e2e8f0;}
.label{opacity:.75;font-size:.85em;}
</style>"""

REASONS = {
    "views_disagree": "The different readings of the audio do not agree.",
    "wrong_length": "The number has the wrong number of digits.",
}


def friendly_reasons(reasons):
    out = []
    for reason in reasons:
        if reason in REASONS:
            out.append(REASONS[reason])
        elif reason.endswith(":unparseable"):
            out.append(
                f"Could not read the number in view '{escape(reason.split(':')[0])}'."
            )
        elif reason.endswith(":unknown_words"):
            out.append(
                f"Unrecognised words in view '{escape(reason.split(':')[0])}'."
            )
        else:
            out.append(escape(reason))
    return out


def candidates_html(kind, candidates, positions):
    rows = []
    for candidate in candidates:
        if kind == "digits":
            boxes = "".join(
                f'<span class="d{" bad" if index in positions else ""}">'
                f"{escape(character)}</span>"
                for index, character in enumerate(candidate, 1)
            )
            rows.append(f"<div>{boxes}</div>")
        else:
            rows.append(
                f'<div><span class="d">₹{escape(indian(candidate))}</span></div>'
            )
    return "".join(rows)


def card(css_class, title, body):
    return (
        f'<div class="card {escape(css_class)}"><div class="label">'
        f"{escape(title)}</div><div>{body}</div></div>"
    )
