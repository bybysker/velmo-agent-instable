"""Rend les blocs Mermaid de docs/schemas_mermaid.md en PNG dans docs/img/.

Extrait les blocs ```mermaid dans l'ordre du document, puis appelle
mermaid-cli via npx. Sert à deux choses : produire les images du document
Word, et vérifier que les huit diagrammes compilent encore après une
retouche du Markdown.

Pré-requis : Node.js (npx). Le paquet @mermaid-js/mermaid-cli est téléchargé
à la volée, aucune installation préalable n'est nécessaire.

Usage :
    python tools/render_diagrams.py            # rend les PNG
    python tools/render_diagrams.py --check    # vérifie sans écrire dans docs/img
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "docs", "schemas_mermaid.md")
IMG = os.path.join(ROOT, "docs", "img")

# Un nom de fichier par bloc ```mermaid, dans l'ordre du document.
NAMES = [
    "01-architecture",
    "02-flux-cible",
    "03-classes",
    "04-sequence-nominale",
    "05-sequence-garde-fou",
    "06-sequence-perimetre",
    "07-sequence-memoire",
    "08-sequence-harnais",
]

SCALE = "3"          # facteur de résolution
BACKGROUND = "white"  # fond opaque : un PNG transparent devient illisible en mode sombre


def extract_blocks(path: str) -> list[str]:
    """Renvoie le contenu de chaque bloc ```mermaid, dans l'ordre."""
    blocks: list[str] = []
    buf: list[str] = []
    inside = False
    for line in io.open(path, encoding="utf-8").read().split("\n"):
        if line.strip() == "```mermaid":
            inside, buf = True, []
        elif inside and line.strip() == "```":
            blocks.append("\n".join(buf))
            inside = False
        elif inside:
            buf.append(line)
    return blocks


def render(src: str, dest: str) -> bool:
    cmd = ["npx", "-y", "-p", "@mermaid-js/mermaid-cli", "mmdc",
           "-i", src, "-o", dest, "-s", SCALE, "-b", BACKGROUND]
    done = subprocess.run(cmd, capture_output=True, text=True,
                          shell=os.name == "nt")
    return done.returncode == 0 and os.path.exists(dest)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="vérifie que les diagrammes compilent, sans écrire dans docs/img")
    args = ap.parse_args()

    if not shutil.which("npx"):
        print("npx introuvable — installer Node.js pour rendre les diagrammes.")
        return 1

    blocks = extract_blocks(SOURCE)
    if len(blocks) != len(NAMES):
        print(f"{len(blocks)} bloc(s) mermaid dans {os.path.basename(SOURCE)} "
              f"pour {len(NAMES)} nom(s) attendu(s).")
        print("Mettre à jour NAMES dans ce script si un diagramme a été ajouté ou retiré.")
        return 1

    out_dir = tempfile.mkdtemp(prefix="mermaid-check-") if args.check else IMG
    os.makedirs(out_dir, exist_ok=True)

    failures = 0
    with tempfile.TemporaryDirectory(prefix="mermaid-src-") as tmp:
        for name, block in zip(NAMES, blocks):
            src = os.path.join(tmp, name + ".mmd")
            io.open(src, "w", encoding="utf-8").write(block)
            dest = os.path.join(out_dir, name + ".png")
            if render(src, dest):
                print(f"  OK   {name}.png")
            else:
                print(f"  ECHEC {name}")
                failures += 1

    if args.check:
        shutil.rmtree(out_dir, ignore_errors=True)

    print(f"\n{len(NAMES) - failures}/{len(NAMES)} diagramme(s) rendu(s)"
          + (" (vérification seule)" if args.check else f" dans {IMG}"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
