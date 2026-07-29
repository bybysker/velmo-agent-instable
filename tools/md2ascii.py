"""Convertit tous les tableaux Markdown d'un fichier en tableaux ASCII.

- ignore ce qui est dans un bloc de code (```...```)
- nettoie le balisage inline : **gras** -> MAJUSCULES (si court), *ital* -> texte,
  puces unicode -> equivalent ASCII, <br> -> espace
- calcule les largeurs de colonnes pour tenir dans un budget de caracteres
- enveloppe le resultat dans un bloc ```text
"""
from __future__ import annotations

import io
import re
import sys
import textwrap

BUDGET = 126          # largeur totale max du tableau rendu
MIN_COL = 6           # largeur mini d'une colonne

SUBS = [
    ("✅", "[OK]"), ("❌", "[KO]"), ("⛔", "[!]"), ("⚠️", "[!]"), ("⚠", "[!]"),
    ("→", "->"), ("←", "<-"), ("↔", "<->"), ("⟶", "->"),
    ("≠", "!="), ("≥", ">="), ("≤", "<="),
    ("«", '"'), ("»", '"'), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
    ("–", "-"), ("—", "-"), ("…", "..."),
]


# tracé unicode -> tracé ASCII, pour les blocs de schéma
DIAGRAM_SUBS = [
    ("──", "--"), ("─", "-"), ("│", "|"), ("├", "+"), ("└", "+"), ("┌", "+"),
    ("┘", "+"), ("┐", "+"), ("┤", "+"), ("┬", "+"), ("┴", "+"), ("┼", "+"),
    ("═", "="), ("║", "|"), ("►", ">"), ("▶", ">"), ("◄", "<"),
    ("▼", "v"), ("▲", "^"), ("•", "-"),
] + SUBS


def clean(cell: str) -> str:
    s = cell.strip()
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"«[\s  ]*", '"', s)
    s = re.sub(r"[\s  ]*»", '"', s)
    # **gras** -> MAJUSCULES si court, sinon on retire juste les marqueurs
    def bold(m):
        inner = m.group(1)
        return inner.upper() if len(inner) <= 24 else inner
    s = re.sub(r"\*\*(.+?)\*\*", bold, s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", s)  # *italique*
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)          # [texte](lien)
    for a, b in SUBS:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c for c in s.split("|")]


def is_delim(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\|?[\s:|-]*-[\s:|-]*\|?\s*", line)) and "-" in line


def longest_word(text: str) -> int:
    return max((len(w) for w in text.split()), default=1)


def compute_widths(rows: list[list[str]]) -> list[int]:
    n = len(rows[0])
    natural = [max(len(r[i]) for r in rows) for i in range(n)]
    floor = [max(MIN_COL, min(natural[i], max(longest_word(r[i]) for r in rows)))
             for i in range(n)]
    w = natural[:]
    while sum(w) + 3 * n + 1 > BUDGET:
        # rogne la colonne la plus large qui peut encore l'etre
        cand = [i for i in range(n) if w[i] > floor[i]]
        if not cand:
            break
        i = max(cand, key=lambda k: w[k])
        w[i] -= 1
    return w


def render(header: list[str], body: list[list[str]], widths: list[int]) -> str:
    def rule(ch="-"):
        return "+" + "+".join(ch * (x + 2) for x in widths) + "+"

    def block(cells):
        cols = [textwrap.wrap(c, w) or [""] for c, w in zip(cells, widths)]
        h = max(len(c) for c in cols)
        out = []
        for i in range(h):
            out.append("|" + "|".join(
                " " + (col[i] if i < len(col) else "").ljust(w) + " "
                for col, w in zip(cols, widths)))
            out[-1] += "|"
        return out

    res = [rule()] + block(header) + [rule("=")]
    for r in body:
        res += block(r) + [rule()]
    return "\n".join(res)


def convert(path: str) -> int:
    lines = io.open(path, encoding="utf-8").read().split("\n")
    out: list[str] = []
    i, inside_fence, count = 0, False, 0

    fence_lang = ""
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            if not inside_fence:
                fence_lang = line.strip()[3:].strip()
                # un bloc sans langage qui contient du schéma devient ```text
                out.append(line if fence_lang else "```text")
            else:
                out.append(line)
                fence_lang = ""
            inside_fence = not inside_fence
            i += 1
            continue

        if inside_fence and fence_lang != "mermaid":
            for a, b in DIAGRAM_SUBS:
                line = line.replace(a, b)
            out.append(line)
            i += 1
            continue

        if (not inside_fence and line.lstrip().startswith("|")
                and i + 1 < len(lines) and is_delim(lines[i + 1])):
            header = [clean(c) for c in split_row(line)]
            j = i + 2
            body = []
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                cells = [clean(c) for c in split_row(lines[j])]
                cells = (cells + [""] * len(header))[:len(header)]
                body.append(cells)
                j += 1
            widths = compute_widths([header] + body)
            out.append("```text")
            out.append(render(header, body, widths))
            out.append("```")
            count += 1
            i = j
            continue

        out.append(line)
        i += 1

    io.open(path, "w", encoding="utf-8").write("\n".join(out))
    return count


if __name__ == "__main__":
    for p in sys.argv[1:]:
        n = convert(p)
        print(f"{n} tableau(x) converti(s) : {p.split('/')[-1]}")
