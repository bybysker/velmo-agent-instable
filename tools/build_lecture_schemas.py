"""Assemble le document Word « Lecture des schémas » à partir des PNG Mermaid.

Pré-requis : les PNG doivent exister dans docs/img/ — les produire d'abord avec
    python tools/render_diagrams.py

Usage :
    python tools/build_lecture_schemas.py
    DOCX_OUT=/tmp/essai.docx python tools/build_lecture_schemas.py

C'est ici que vit le texte des commentaires de chaque schéma : pour le
retoucher, modifier la table FIGURES ci-dessous puis relancer le script.
Éditer le .docx à la main serait perdu à la prochaine génération.
"""
from __future__ import annotations

import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
IMG = os.path.join(DOCS, "img")
OUT = os.environ.get("DOCX_OUT") or os.path.join(DOCS, "lecture_des_schemas.docx")

# page A4, marges 2,5 cm -> surface utile 16,0 x 24,7 cm
MAX_W = Cm(15.8)     # largeur max d'une figure
MAX_H = Cm(21.0)     # hauteur max pour qu'une figure tienne sous son titre

ACCENT = RGBColor(0x1F, 0x3D, 0x7A)
GREY = RGBColor(0x60, 0x60, 0x60)

# (fichier, titre, "ce qu'il montre", "comment le lire", "ce qu'il révèle")
FIGURES = [
    (
        "01-architecture.png",
        "Architecture — modules et dépendances",
        "La carte statique du code : les onze modules de src/velmo, regroupés en "
        "quatre zones (entrée/sortie, cœur d'orchestration, règles déterministes, "
        "adaptateurs externes), et les dépendances qui les relient.",
        "Partir de agent.py, au centre : c'est le seul point d'assemblage. Les "
        "flèches pleines sont des appels directs, les flèches pointillées des "
        "relations indirectes — le routage qui désigne un outil, le harnais de "
        "test qui rejoue une conversation.",
        "La frontière entre la zone « Règles déterministes » et la zone "
        "« Adaptateurs externes » est la ligne de partage du coût : à gauche, tout "
        "est gratuit, hors-réseau et testable ; à droite, chaque passage consomme "
        "un appel modèle. VelmoAgent ne connaît le modèle que par le protocole "
        "LLMClient, jamais Azure directement — c'est ce qui autorise un double de "
        "test. Enfin, tools.py n'est atteint que par des flèches pointillées : "
        "l'outil est désigné, pas encore appelé.",
    ),
    (
        "02-flux-cible.png",
        "Flux cible — le trajet d'un message",
        "Le parcours complet d'un message client, de la saisie à la réponse : "
        "sept étapes ordonnées et deux sorties anticipées.",
        "La lecture se fait de haut en bas. Les losanges sont des décisions ; "
        "les deux boîtes rouges sont des fins de parcours — on y répond au client "
        "sans aller plus loin. Tout le reste est un couloir à sens unique.",
        "Les deux refus sortent avant l'appel au modèle. Un message abusif ou "
        "hors-sujet ne coûte donc rien et ne peut pas faire déraper la réponse, "
        "puisqu'aucune réponse n'est générée. L'ordre des étapes n'est pas une "
        "préférence de style : c'est le principe « filtrer tôt, dépenser tard ». "
        "Déplacer le contrôle de périmètre après l'appel modèle rendrait le "
        "garde-fou inutile.",
    ),
    (
        "03-classes.png",
        "Diagramme de classes — les objets et leurs liens",
        "Ce qui est réellement un objet dans le code : VelmoAgent, "
        "ConversationMemory, AgentReply, AzureLLM, Settings, plus l'énumération "
        "Intent, l'exception GuardrailError et le protocole LLMClient. Les modules "
        "purement fonctionnels apparaissent en « module ».",
        "Les mentions entre guillemets doubles donnent la nature du type "
        "(Protocol, dataclass, BaseModel, enumeration). Le losange vide sur le "
        "lien vers LLMClient signale une agrégation — l'objet est fourni de "
        "l'extérieur ; le losange plein vers ConversationMemory signale une "
        "composition — l'agent la crée et la possède. Les flèches pointillées "
        "sont des dépendances d'usage.",
        "Trois décisions de conception se lisent directement sur le schéma. Le "
        "client de modèle est injecté, donc remplaçable par un double dans les "
        "tests. La mémoire appartient à l'agent, donc sa durée de vie est celle "
        "de la conversation. Enfin, le champ category d'AgentReply est typé par "
        "un Literal Pydantic : une catégorie inventée ne produit pas une réponse "
        "douteuse, elle empêche la construction de l'objet. La sortie est "
        "contrainte par le type, pas par une convention.",
    ),
    (
        "04-sequence-nominale.png",
        "Séquence — cas nominal « remboursement commande 4490 »",
        "Le dialogue complet entre les objets pour une demande légitime, tous "
        "les garde-fous franchis, jusqu'à l'appel au modèle et le retour au "
        "client.",
        "Le temps descend. Chaque flèche pleine est un appel, chaque flèche "
        "pointillée le retour de cet appel. La numérotation permet de citer une "
        "étape précise en réunion.",
        "Quatre vérifications déterministes s'enchaînent avant le premier appel "
        "réseau (étapes 3 à 10). La note sur flow explique le point le plus "
        "subtil du parcours après-vente : les mots-clés sont testés par priorité "
        "métier, donc « commande » ne masque plus « remboursement » dans une "
        "phrase qui contient les deux. On voit aussi que VelmoAgent ne parle "
        "jamais à Azure : il s'adresse à AzureLLM, qui traduit. C'est le même "
        "découplage que sur le diagramme de classes, vu cette fois en action.",
    ),
    (
        "05-sequence-garde-fou.png",
        "Séquence — court-circuit 1 : entrée abusive",
        "Ce qui se passe quand le client écrit « imbécile » : le garde-fou "
        "d'entrée se déclenche et le parcours s'arrête immédiatement.",
        "La flèche ouverte partant de guardrails n'est pas un retour de valeur : "
        "c'est une exception qui remonte. La note posée sur VelmoAgent indique où "
        "elle est rattrapée.",
        "C'est la différence entre détecter et gérer. Le garde-fou détectait déjà "
        "l'insulte avant correction — mais l'exception traversait toute la pile et "
        "faisait tomber l'application. Ici elle est convertie en réponse "
        "structurée : le refus devient une valeur de retour normale. La ligne de "
        "vie d'AzureLLM reste vide de bout en bout ; c'est la preuve visuelle "
        "qu'aucun jeton n'a été dépensé.",
    ),
    (
        "06-sequence-perimetre.png",
        "Séquence — court-circuit 2 : hors périmètre",
        "Le traitement d'une question hors sujet — une recette de cookies — par "
        "le contrôle de périmètre.",
        "Même lecture que la séquence précédente, mais le parcours va une étape "
        "plus loin : le garde-fou d'entrée laisse passer (le message n'est pas "
        "abusif), c'est le contrôle de périmètre qui tranche.",
        "Le refus vient d'un test de code sur une liste de sujets, pas d'une "
        "consigne donnée au modèle. La nuance est décisive : avant correction, "
        "l'agent refusait déjà les cookies, mais parce que le modèle obéissait au "
        "prompt système — un refus consenti, donc contournable par une "
        "reformulation. Ici le refus est déterministe : il ne dépend pas de "
        "l'humeur du modèle, et il est rejouable à l'identique dans un test. Le "
        "prompt système reste utile, mais comme seconde ceinture.",
    ),
    (
        "07-sequence-memoire.png",
        "Séquence — la mémoire sur trois tours",
        "Le cas ctx-oubli-1 : trois messages successifs, avec l'état de la "
        "mémoire à chaque tour.",
        "Suivre la ligne de vie de ConversationMemory. À chaque tour, l'agent "
        "commence par lire l'historique, puis appelle le modèle avec cet "
        "historique, et n'écrit qu'ensuite.",
        "L'ordre lire-puis-écrire n'est pas anodin : écrire d'abord ferait "
        "apparaître le message courant en double dans le contexte envoyé au "
        "modèle. On voit également l'historique grossir — vide au tour 1, deux "
        "entrées au tour 2, quatre au tour 3 — alors qu'avant correction il valait "
        "toujours la liste vide. La note sur la fenêtre glissante rappelle le "
        "second défaut, plus discret : la fenêtre retenait les tours les plus "
        "anciens au lieu des plus récents. Sur trois tours cela ne se voyait pas ; "
        "sur une conversation longue, l'agent aurait oublié ce qui venait d'être "
        "dit tout en se souvenant du début.",
    ),
    (
        "08-sequence-harnais.png",
        "Séquence — le harnais de non-régression",
        "Comment les cinq conversations problématiques fournies sont rejouées "
        "automatiquement pour vérifier que le comportement attendu tient.",
        "Le cadre « loop » se répète pour chaque cas ; le cadre « alt » présente "
        "deux chemins mutuellement exclusifs selon que l'entrée est refusée ou "
        "acceptée.",
        "Le modèle réel est remplacé par un double au comportement fixe : le test "
        "est donc déterministe et ne touche pas le réseau. Surtout, la branche "
        "haute de l'alternative ne descend jamais jusqu'au double — le test ne "
        "vérifie pas seulement que la réponse est un refus, il vérifie qu'aucun "
        "appel modèle n'a eu lieu. C'est ce qui distingue un vrai court-circuit "
        "d'un refus produit après coup.",
    ),
]


def add_figure(doc: Document, path: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    pic = run.add_picture(path, width=MAX_W)
    if pic.height > MAX_H:
        ratio = MAX_H / pic.height
        pic.height = MAX_H
        pic.width = int(pic.width * ratio)


def add_block(doc: Document, label: str, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(label + " — ")
    r.bold = True
    r.font.color.rgb = ACCENT
    p.add_run(text)


def main() -> None:
    manquants = [f for f, *_ in FIGURES if not os.path.exists(os.path.join(IMG, f))]
    if manquants:
        raise SystemExit(
            "PNG absents de docs/img/ : " + ", ".join(manquants)
            + "\nLancer d'abord : python tools/render_diagrams.py"
        )

    doc = Document()

    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = section.right_margin = Cm(2.5)
    section.top_margin = section.bottom_margin = Cm(2.5)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)

    for name, size, color in (("Title", 26, ACCENT), ("Heading 1", 16, ACCENT),
                              ("Heading 2", 13, ACCENT)):
        st = doc.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.color.rgb = color
        st.font.bold = True

    doc.add_heading("Velmo — lecture des schémas", level=0)

    sub = doc.add_paragraph()
    r = sub.add_run("Assistant de support Velmo : architecture, flux cible et "
                    "interactions entre objets")
    r.italic = True
    r.font.size = Pt(12)
    r.font.color.rgb = GREY

    doc.add_paragraph(
        "Ce document reprend les huit schémas produits pour l'agent Velmo et les "
        "commente un par un. Chaque figure est suivie de trois lectures : ce "
        "qu'elle montre, comment la parcourir, et ce qu'elle révèle du "
        "fonctionnement — ou des défauts — de l'agent."
    )
    doc.add_paragraph(
        "Les schémas décrivent le flux cible, c'est-à-dire le comportement visé "
        "une fois les défauts corrigés. La dernière section signale les points "
        "sur lesquels le code n'a pas encore rejoint ces schémas."
    )

    p = doc.add_paragraph()
    r = p.add_run("Source : diagrammes Mermaid de docs/schemas_mermaid.md, "
                  "rendus en PNG dans docs/img/.")
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = GREY

    for n, (img, title, shows, howto, reveals) in enumerate(FIGURES, start=1):
        doc.add_page_break()
        doc.add_heading(f"{n}. {title}", level=1)
        add_figure(doc, os.path.join(IMG, img))

        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(f"Figure {n} — {title}")
        r.italic = True
        r.font.size = Pt(9)
        r.font.color.rgb = GREY

        add_block(doc, "Ce qu'il montre", shows)
        add_block(doc, "Comment le lire", howto)
        add_block(doc, "Ce qu'il révèle", reveals)

    # --- section finale ---------------------------------------------------
    doc.add_page_break()
    doc.add_heading("9. Ce que les schémas ne disent pas encore", level=1)
    doc.add_paragraph(
        "Les huit figures décrivent la cible. Trois écarts subsistent entre "
        "cette cible et le code effectivement en place ; ils sont listés ici pour "
        "qu'ils soient visibles plutôt que sous-entendus."
    )

    for title, body in [
        ("Le routage n'est pas câblé",
         "Sur la séquence nominale, l'agent appelle route() puis l'outil "
         "open_after_sales. Dans le code, handle() classe l'intention mais "
         "n'appelle ni route() ni les outils : la réponse vient du modèle seul. "
         "C'est le dernier défaut fonctionnel ouvert."),
        ("L'ordre du contrôle de périmètre diffère",
         "Le flux cible place le contrôle de périmètre avant la classification. "
         "Le code fait l'inverse : il classe d'abord, et ne vérifie le périmètre "
         "que si aucune intention n'a été reconnue. Le résultat est identique sur "
         "les cinq cas fournis, mais le schéma et le code divergent — il faut "
         "trancher lequel des deux fait foi."),
        ("Le nom de la catégorie de refus n'est pas fixé",
         "Les schémas emploient hors_perimetre ; le code renvoie refusal, seule "
         "valeur admise par le type Category. Tant que ce point n'est pas tranché, "
         "le test de non-régression du cas hors-périmètre échouera quelle que "
         "soit la qualité du garde-fou."),
    ]:
        doc.add_heading(title, level=2)
        doc.add_paragraph(body)

    doc.save(OUT)
    print("écrit :", OUT)


if __name__ == "__main__":
    main()
