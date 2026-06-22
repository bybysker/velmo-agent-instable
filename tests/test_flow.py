from velmo.flow import Intent, classify, route


def test_classify_order_status():
    assert classify("Je veux le statut de ma commande 4521") is Intent.ORDER_STATUS


def test_classify_delivery():
    assert classify("Où est mon colis ?") is Intent.DELIVERY


def test_classify_after_sales_for_refund():
    assert classify("Je demande un remboursement pour la 4490") is Intent.AFTER_SALES


def test_classify_after_sales_even_with_order_word():
    # Cas réel apres-vente-1 : "remboursement" doit primer sur "commande".
    assert classify("Je veux un remboursement pour la commande 4490.") is Intent.AFTER_SALES


def test_route_after_sales_to_tool():
    assert route(Intent.AFTER_SALES) == "open_after_sales"
