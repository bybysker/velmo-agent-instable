import pytest

from velmo.agent import VelmoAgent
from velmo.guardrails import AgentReply, GuardrailError
from velmo.regression import load_problem_conversations, replay

CASES = {case["id"]: case for case in load_problem_conversations()}


def test_problem_conversations_load():
    cases = load_problem_conversations()
    assert len(cases) >= 1
    assert all("turns" in case for case in cases)


def test_every_provided_case_has_a_replay_check():
    # Un nouveau cas ajouté au jeu de données doit recevoir son contrôle ci-dessous.
    assert set(CASES) == {
        "ctx-oubli-1",
        "perimetre-1",
        "perimetre-2",
        "entree-abusive-1",
        "apres-vente-1",
    }


def _replay(case_id, make_scripted):
    llm = make_scripted()
    outcomes = replay(CASES[case_id], VelmoAgent(llm=llm))
    return llm, outcomes


def test_replay_ctx_oubli_1_keeps_context(make_scripted):
    llm, outcomes = _replay("ctx-oubli-1", make_scripted)

    # Aucun des trois messages client n'est refusé, relance comprise.
    assert all(isinstance(o, AgentReply) and o.within_scope for o in outcomes)
    # Au dernier tour, le modèle voit encore les deux commandes citées avant.
    _, history_seen, _ = llm.calls[-1]
    flat = " ".join(content for _, content in history_seen)
    assert "4521" in flat
    assert "4490" in flat


@pytest.mark.parametrize("case_id", ["perimetre-1", "perimetre-2"])
def test_replay_out_of_scope_is_refused(case_id, make_scripted):
    llm, outcomes = _replay(case_id, make_scripted)

    [reply] = outcomes
    assert isinstance(reply, AgentReply)
    assert reply.within_scope is False
    assert reply.category == "refusal"
    assert llm.calls == []  # le modèle n'est jamais sollicité


def test_replay_abusive_input_is_rejected(make_scripted):
    llm, outcomes = _replay("entree-abusive-1", make_scripted)

    [outcome] = outcomes
    assert isinstance(outcome, GuardrailError)
    assert llm.calls == []


def test_replay_refund_goes_to_unified_after_sales(make_scripted):
    _, outcomes = _replay("apres-vente-1", make_scripted)

    [reply] = outcomes
    assert isinstance(reply, AgentReply)
    assert reply.category == "after_sales"
