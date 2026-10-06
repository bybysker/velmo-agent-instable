import pytest
from pydantic import ValidationError

from velmo.guardrails import AgentReply, GuardrailError, validate_input


def test_validate_input_rejects_abusive_message():
    with pytest.raises(GuardrailError):
        validate_input("Mais tu es vraiment un imbécile, ce service !")


def test_validate_input_accepts_normal_message():
    validate_input("Bonjour, où en est ma commande 4521 ?")


def test_reply_accepts_known_category():
    reply = AgentReply(message="ok", category="order_status", within_scope=True)
    assert reply.category == "order_status"


def test_reply_rejects_unknown_category():
    with pytest.raises(ValidationError):
        AgentReply(message="ok", category="banane", within_scope=True)


@pytest.mark.parametrize("text", ["", "   "])
def test_validate_input_rejects_empty_message(text):
    with pytest.raises(GuardrailError):
        validate_input(text)


def test_validate_input_rejects_oversized_message():
    with pytest.raises(GuardrailError):
        validate_input("commande " * 200)
