from velmo.flow import Intent, classify, route


def test_classify_order_status():
    assert classify("Je veux le statut de ma commande 4521") is Intent.ORDER_STATUS


def test_classify_delivery():
    assert classify("Où est mon colis ?") is Intent.DELIVERY


def test_classify_after_sales_for_refund():
    assert classify("Je demande un remboursement pour la 4490") is Intent.AFTER_SALES


def test_route_after_sales_to_tool():
    assert route(Intent.AFTER_SALES) == "open_after_sales"


def test_classify_refund_wins_over_order_keyword():
    assert classify("Je veux un remboursement pour la commande 4490.") is Intent.AFTER_SALES


def test_classify_return_is_after_sales():
    assert classify("Je souhaite faire un retour") is Intent.AFTER_SALES


def test_classify_greeting_with_request_keeps_request():
    assert classify("Bonjour, ma commande 4521 est en retard.") is Intent.ORDER_STATUS
