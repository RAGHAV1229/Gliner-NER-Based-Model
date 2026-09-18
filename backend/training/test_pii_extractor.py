from app.services.pii_extractor import extract_pii_entities, luhn_check, validate_iban


def test_email_phone_and_pan():
    text = (
        "Contact Priya at priya.kapoor@infosys.com or +91 98765 43210. "
        "PAN ABCDE1234F and GST 27ABCDE1234F1Z5."
    )
    by_label = {item["label"]: item["text"] for item in extract_pii_entities(text)}
    assert by_label["EMAIL"] == "priya.kapoor@infosys.com"
    assert "98765" in by_label["PHONE"]
    assert by_label["PAN"] == "ABCDE1234F"


def test_luhn_and_iban():
    assert luhn_check("4532015112830366")
    assert not luhn_check("4532015112830367")
    assert validate_iban("GB82WEST12345698765432")
