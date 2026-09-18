from __future__ import annotations

import re

# Identifier extractors modeled on Azure Language PII / Microsoft Presidio.
# These are deterministic and must win over GLiNER on overlapping spans.

REGEX_PATTERNS: dict[str, str] = {
    "CREDIT_CARD": r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)",
    "EMAIL": (
        r"(?<![\w.])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        r"(?![\w.])"
    ),
    "PHONE": (
        r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?"
        r"\d{3,5}[\s.-]?\d{4}(?!\w)"
    ),
    "WEBSITE": r"(?<!\w)(?:https?://|www\.)[^\s<>\"]+",
    "PERCENTAGE": (
        r"(?<![\w.])\d+(?:\.\d+)?\s*(?:%|percent|percentage)(?!\w)"
    ),
    "MONEY": (
        r"(?<!\w)(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)"
        r"\s?\d[\d,]*(?:\.\d+)?"
        r"(?:\s?(?:crore|lakh|million|billion|thousand|k))?(?!\w)"
    ),
    "DATE": (
        r"\b(?:0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?[\s./-]+"
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
        r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"[\s,./-]+\d{4}\b"
        r"|"
        r"\b\d{4}[-/](?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])\b"
        r"|"
        r"\b(?:0?[1-9]|[12]\d|3[01])[-/](?:0?[1-9]|1[0-2])[-/]\d{4}\b"
        r"|"
        r"\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/]\d{2,4}\b"
    ),
    "TIME": (
        r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?"
        r"(?:\s?(?:AM|PM|am|pm))?\b"
    ),
    "QUANTITY": (
        r"(?<!\w)\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\w)"
        r"|"
        r"(?<!\w)\d+(?:\.\d+)?\s?"
        r"(?:kg|km|mw|gw|tons?|units?|employees|people|patients|"
        r"missiles|vehicles|servers)(?!\w)"
    ),
    "DOCTOR": (
        r"\bDr\.?\s+[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,3}\b"
    ),
    "HOSPITAL": (
        r"\b(?:[A-Z][A-Za-z&.'-]*\s+){0,5}"
        r"(?:Hospital|Clinic|Medical Centre|Medical Center|"
        r"Nursing Home|Health Centre|Health Center)\b"
    ),
    "FILE_NAME": (
        r"(?<![\w.-])[A-Za-z0-9][A-Za-z0-9_. -]*"
        r"\.(?:pdf|docx?|xlsx?|pptx?|csv|tsv|txt|md|html?|rtf|"
        r"eml|json|xml|zip)(?![\w.-])"
    ),
    "AADHAR": r"(?<!\d)[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}(?!\d)",
    "PAN": r"(?<![A-Za-z0-9])[A-Za-z]{5}\d{4}[A-Za-z](?![A-Za-z0-9])",
    "GST": (
        r"(?<![A-Za-z0-9])\d{2}[A-Za-z]{5}\d{4}[A-Za-z]"
        r"[1-9A-Za-z]Z[0-9A-Za-z](?![A-Za-z0-9])"
    ),
    "IFSC": r"(?<![A-Za-z0-9])[A-Za-z]{4}0[A-Za-z0-9]{6}(?![A-Za-z0-9])",
    "PASSPORT": r"(?<![A-Za-z0-9])[A-PR-WYa-pr-wy][1-9]\d{6}(?![A-Za-z0-9])",
    "ZIP_CODE": r"(?<!\d)[1-9]\d{5}(?!\d)",
    "IP_ADDRESS": (
        r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?!\d)"
    ),
    "IP_ADDRESS_V6": (
        r"(?<![A-Fa-f0-9:])(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}"
        r"(?![A-Fa-f0-9:])"
    ),
    "MAC_ADDRESS": (
        r"(?<![A-Fa-f0-9])(?:[A-Fa-f0-9]{2}[:-]){5}[A-Fa-f0-9]{2}"
        r"(?![A-Fa-f0-9])"
    ),
    "HASH": (
        r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{64}(?![A-Fa-f0-9])"
        r"|(?<![A-Fa-f0-9])[A-Fa-f0-9]{40}(?![A-Fa-f0-9])"
        r"|(?<![A-Fa-f0-9])[A-Fa-f0-9]{32}(?![A-Fa-f0-9])"
    ),
    "BANK_ACCOUNT": (
        r"(?:account|a/c|acc(?:ount)?\.?\s*no\.?|bank\s*a/?c)"
        r"[^\d]{0,15}(\d{9,18})"
    ),
    "US_SSN": r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)",
    "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b",
    "SWIFT_CODE": r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b",
    "UUID": (
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
        r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
    ),
    "CVE": r"\bCVE-\d{4}-\d{4,7}\b",
    "CWE": r"\bCWE-\d{1,4}\b",
    "VIN": r"\b[A-HJ-NPR-Z0-9]{17}\b",
}


def luhn_check(card_number: str) -> bool:
    digits = re.sub(r"\D", "", card_number)
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    for index, digit in enumerate(digits[::-1]):
        number = int(digit)
        if index % 2 == 1:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0


def validate_phone(phone_number: str) -> bool:
    digits = re.sub(r"\D", "", phone_number)
    return 10 <= len(digits) <= 15


def validate_aadhar(aadhar_number: str) -> bool:
    digits = re.sub(r"\D", "", aadhar_number)
    return len(digits) == 12 and digits[0] not in ("0", "1")


def validate_pan(pan_number: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{5}\d{4}[A-Za-z]", pan_number))


def validate_gst(gst_number: str) -> bool:
    return bool(
        re.fullmatch(
            r"\d{2}[A-Za-z]{5}\d{4}[A-Za-z][1-9A-Za-z]Z[0-9A-Za-z]",
            gst_number,
        )
    )


def validate_ifsc(ifsc_code: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{4}0[A-Za-z0-9]{6}", ifsc_code))


def validate_passport(passport_number: str) -> bool:
    return bool(re.fullmatch(r"[A-PR-WYa-pr-wy][1-9]\d{6}", passport_number))


def validate_zip_code(zip_code: str) -> bool:
    digits = re.sub(r"\D", "", zip_code)
    return len(digits) == 6 and digits[0] != "0"


def validate_ip_address(ip_address: str) -> bool:
    parts = ip_address.split(".")
    if len(parts) != 4:
        return False
    return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


def validate_iban(iban: str) -> bool:
    compact = re.sub(r"\s+", "", iban).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", compact):
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in rearranged)
    return int(numeric) % 97 == 1


def validate_swift(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?", code))


def validate_vin(vin: str) -> bool:
    return bool(re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin.upper())) and not vin.isdigit()


def validate_money(amount: str) -> bool:
    """Reject tiny `$0`/`$6` noise common in binary/image decode artifacts."""
    compact = amount.strip()
    digits = re.sub(r"\D", "", compact)
    if re.search(r"(USD|INR|EUR|GBP|Rs\.?|₹|€|£)", compact, re.I):
        return bool(digits)
    # Bare `$` amounts need 2+ digits, a decimal, or a magnitude word
    if re.search(r"(crore|lakh|million|billion|thousand|\bk\b)", compact, re.I):
        return bool(digits)
    if "." in compact or "," in compact:
        return bool(digits)
    return len(digits) >= 2


def validate_percentage(value: str) -> bool:
    """Reject lone `0%`/`5%` hits from binary noise when possible."""
    if re.search(r"percent", value, re.I):
        return True
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    if not match:
        return False
    number = match.group(1)
    if "." in number:
        return True
    # Keep multi-digit percentages; drop single-digit noise from images
    return len(number) >= 2


VALIDATORS = {
    "CREDIT_CARD": luhn_check,
    "PHONE": validate_phone,
    "AADHAR": validate_aadhar,
    "PAN": validate_pan,
    "GST": validate_gst,
    "IFSC": validate_ifsc,
    "PASSPORT": validate_passport,
    "ZIP_CODE": validate_zip_code,
    "IP_ADDRESS": validate_ip_address,
    "IBAN": validate_iban,
    "SWIFT_CODE": validate_swift,
    "VIN": validate_vin,
    "MONEY": validate_money,
    "PERCENTAGE": validate_percentage,
}


def extract_pii_entities(text: str) -> list[dict]:
    entities: list[dict] = []

    for label, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            if label == "BANK_ACCOUNT":
                if not match.group(1):
                    continue
                entity_text = match.group(1)
                start_index = match.start(1)
                end_index = match.end(1)
            else:
                entity_text = match.group().strip()
                start_index = match.start()
                end_index = match.end()

            if label == "WEBSITE":
                cleaned = entity_text.rstrip(".,);]}")
                end_index -= len(entity_text) - len(cleaned)
                entity_text = cleaned

            if label == "SWIFT_CODE" and entity_text.upper() in {
                "HTTP",
                "HTTPS",
                "JSON",
                "HTML",
                "UTF8",
            }:
                continue

            validator = VALIDATORS.get(label)
            if validator and not validator(entity_text):
                continue

            if len(entity_text) < 2:
                continue

            entities.append(
                {
                    "text": entity_text,
                    "label": label,
                    "score": 0.99,
                    "start": start_index,
                    "end": end_index,
                    "source": "regex",
                }
            )

    return entities
