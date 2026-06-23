"""Rejeu des conversations problématiques fournies (non-régression de bout en bout).

Chaque cas de `data/conversations_problematiques.json` est rejoué dans l'agent
corrigé, puis on vérifie que son comportement correspond au champ `attendu`.
C'est le filet de sécurité : si une correction future re-casse un de ces cas,
un de ces tests passera au rouge.
"""

from velmo.agent import VelmoAgent
from velmo.regression import load_problem_conversations


def _case(case_id: str) -> dict:
    """Retrouve un cas par son identifiant dans le fichier fourni."""
    cases = load_problem_conversations()
    return next(c for c in cases if c["id"] == case_id)


def _user_messages(case: dict) -> list[str]:
    """Ne garde que les messages du client (les tours 'user')."""
    return [turn["content"] for turn in case["turns"] if turn["role"] == "user"]


def _replay(agent: VelmoAgent, case: dict) -> list:
    """Rejoue tous les messages du client et renvoie les réponses de l'agent."""
    return [agent.handle(message) for message in _user_messages(case)]


# --- Le harnais lui-même charge bien le jeu de données fourni ------------------


def test_problem_conversations_load():
    cases = load_problem_conversations()
    assert len(cases) >= 1
    assert all("turns" in case for case in cases)


# --- Rejeu cas par cas ---------------------------------------------------------


def test_replay_memoire_garde_la_commande_4521(make_scripted):
    """ctx-oubli-1 : l'agent doit encore connaître la 4521 du 1er tour."""
    agent = VelmoAgent(llm=make_scripted())

    _replay(agent, _case("ctx-oubli-1"))

    memoire = " ".join(contenu for _, contenu in agent.memory.history())
    assert "4521" in memoire


def test_replay_cookies_hors_perimetre_refuse(make_scripted):
    """perimetre-1 : une recette de cookies est hors support -> refus poli."""
    agent = VelmoAgent(llm=make_scripted())

    (reply,) = _replay(agent, _case("perimetre-1"))

    assert reply.within_scope is False
    assert reply.category == "refusal"


def test_replay_conseil_bourse_hors_perimetre_refuse(make_scripted):
    """perimetre-2 : un conseil boursier est hors rôle -> refus."""
    agent = VelmoAgent(llm=make_scripted())

    (reply,) = _replay(agent, _case("perimetre-2"))

    assert reply.within_scope is False
    assert reply.category == "refusal"


def test_replay_entree_abusive_rejetee_sans_crash(make_scripted):
    """entree-abusive-1 : une insulte est rejetée proprement (sans exception)."""
    agent = VelmoAgent(llm=make_scripted())

    (reply,) = _replay(agent, _case("entree-abusive-1"))

    assert reply.within_scope is False
    assert reply.category == "rejet"


def test_replay_remboursement_route_apres_vente(make_scripted):
    """apres-vente-1 : un remboursement part dans le parcours après-vente unifié."""
    agent = VelmoAgent(llm=make_scripted())

    (reply,) = _replay(agent, _case("apres-vente-1"))

    assert reply.category == "after_sales"
