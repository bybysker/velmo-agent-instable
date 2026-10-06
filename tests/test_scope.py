from velmo.scope import is_follow_up, is_in_scope


def test_in_scope_for_order_question():
    assert is_in_scope("Où est ma commande 4521 ?") is True


def test_out_of_scope_for_unrelated_question():
    assert is_in_scope("Donne-moi une recette de cookies au chocolat") is False


SUPPORT_HISTORY = [
    ("user", "Bonjour, ma commande 4521 est en retard."),
    ("assistant", "Je regarde la commande 4521."),
]


def test_follow_up_with_order_number_is_accepted_in_context():
    assert is_follow_up("Et la précédente, la 4490, où en est-elle ?", SUPPORT_HISTORY) is True


def test_follow_up_without_history_is_rejected():
    assert is_follow_up("Et la précédente, la 4490, où en est-elle ?", []) is False


def test_off_topic_follow_up_is_rejected_even_in_context():
    assert is_follow_up("Et une bonne recette de cookies ?", SUPPORT_HISTORY) is False


def test_follow_up_does_not_modify_history():
    # L'agent transmet cette même liste au modèle juste après : elle doit rester intacte.
    history = list(SUPPORT_HISTORY)
    is_follow_up("Et la précédente, la 4490, où en est-elle ?", history)
    assert history == SUPPORT_HISTORY
