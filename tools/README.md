# tools — outillage de la documentation

Scripts qui produisent les documents de `docs/`. Ils ne font pas partie de
l'application : rien dans `src/velmo/` n'en dépend.

## Chaîne de production

```text
docs/schemas_mermaid.md          (source : 8 blocs ```mermaid)
        |
        |  render_diagrams.py    (Node.js / npx + mermaid-cli)
        v
docs/img/*.png                   (8 images, facteur 3, fond blanc)
        |
        |  build_lecture_schemas.py   (python-docx)
        v
docs/lecture_des_schemas.docx    (A4, une figure par page + commentaires)
```

Le Markdown est la **source de vérité** : les PNG et le `.docx` en sont des
produits dérivés, régénérables à tout moment.

## Scripts

### `render_diagrams.py`

Extrait les blocs ```mermaid de `docs/schemas_mermaid.md` et les rend en PNG
dans `docs/img/`. L'ordre des blocs dans le document détermine le nom des
fichiers, via la liste `NAMES` en tête du script — ajouter ou retirer un
diagramme impose de la mettre à jour, sans quoi le script s'arrête avec un
message explicite.

```bash
python tools/render_diagrams.py            # écrit dans docs/img/
python tools/render_diagrams.py --check    # vérifie que les 8 diagrammes compilent
```

Le mode `--check` rend les diagrammes dans un dossier temporaire puis
l'efface. Il sert à valider une retouche du Markdown sans toucher aux images
commitées.

Pré-requis : Node.js. Le paquet `@mermaid-js/mermaid-cli` est téléchargé à la
volée par `npx`, aucune installation préalable.

### `build_lecture_schemas.py`

Assemble `docs/lecture_des_schemas.docx` à partir des PNG.

```bash
python tools/build_lecture_schemas.py
DOCX_OUT=/tmp/essai.docx python tools/build_lecture_schemas.py   # sortie ailleurs
```

**Le texte des commentaires de chaque schéma vit dans ce script**, dans la
table `FIGURES` : un tuple par figure, avec le nom du fichier, le titre, puis
les trois commentaires « ce qu'il montre / comment le lire / ce qu'il révèle ».
Pour retoucher un commentaire, modifier ce tuple et relancer le script —
éditer le `.docx` à la main serait perdu à la génération suivante.

Pré-requis : `pip install python-docx`. Volontairement hors des dépendances de
`pyproject.toml`, qui ne décrit que l'application.

### `md2ascii.py`

Convertit les tableaux Markdown d'un fichier en tableaux ASCII, et remplace le
tracé Unicode des schémas (`│ ├ └ ─ ► ▼`, `✅ ❌ ⛔`) par des caractères ASCII.
C'est ce qui rend les notes de `docs/` lisibles en terminal et dans un diff.

```bash
python tools/md2ascii.py docs/*.md
```

Le script est **idempotent** : relancé sur un fichier déjà converti, il ne
trouve plus de tableau Markdown et ne change rien. Il ignore le contenu des
blocs de code, et laisse les blocs ```mermaid intacts.

Deux réglages en tête du fichier : `BUDGET` (largeur totale maximale d'un
tableau, 126 caractères) et `MIN_COL`. Les colonnes sont rétrécies en
commençant par la plus large, jamais en dessous de la longueur de leur plus
long mot.

## Régénérer toute la documentation

```bash
python tools/render_diagrams.py
python tools/build_lecture_schemas.py
```
