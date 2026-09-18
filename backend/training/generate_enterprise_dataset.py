from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config.entity_ontology import MODEL_LABEL_PROMPTS

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)

FIRST_NAMES = [
    "Aarav", "Aditi", "Aisha", "Akash", "Amina", "Ananya", "Arjun", "Ayesha",
    "Benjamin", "Chen", "Daniel", "Elena", "Fatima", "Grace", "Hassan",
    "Hiroshi", "Ibrahim", "Isabella", "James", "Jia", "Kabir", "Kavya",
    "Liam", "Maria", "Mei", "Mohammed", "Neha", "Noah", "Olivia", "Omar",
    "Priya", "Rahul", "Ravi", "Sana", "Sofia", "Suresh", "Thomas", "Uma",
    "Vikram", "Yara", "Zara", "Pranav", "Meera", "Nikhil", "Rohan", "Sara",
]
LAST_NAMES = [
    "Sharma", "Patel", "Khan", "Singh", "Mehta", "Iyer", "Nair", "Das",
    "Williams", "Johnson", "Brown", "Garcia", "Kim", "Chen", "Tanaka",
    "Muller", "Rossi", "Silva", "Hassan", "Ali", "Kapoor", "Verma",
    "Nama", "Reddy", "Banerjee", "Chopra", "Malik", "Fernandez",
]
ORGANIZATIONS = [
    "Microsoft", "Azure Cloud Services", "Infosys", "Tata Consultancy Services",
    "Amazon Web Services", "Google Cloud", "IBM", "Oracle", "SAP", "Accenture",
    "Deloitte", "PwC", "HDFC Bank", "State Bank of India", "Reserve Bank of India",
    "World Health Organization", "United Nations", "NATO", "ISRO", "DRDO",
    "All India Institute of Medical Sciences", "Stanford University",
    "Medi-Caps University", "BlueLine Logistics", "Data Dynamics",
    "Siemens", "Boeing", "Lockheed Martin", "Palantir", "CrowdStrike",
    "Ministry of Defence", "Ministry of Health", "European Central Bank",
    "Reliance Industries", "Adani Ports", "Tesla", "OpenAI", "NVIDIA",
]
CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Indore",
    "Kolkata", "Ahmedabad", "Jaipur", "London", "New York", "Singapore",
    "Dubai", "Tokyo", "Berlin", "Paris", "Riyadh", "Washington", "Sydney",
]
COUNTRIES = [
    "India", "United States", "United Kingdom", "Germany", "Japan",
    "Singapore", "United Arab Emirates", "France", "Canada", "Australia",
]
LOCATIONS = CITIES + COUNTRIES + [
    "Silicon Valley", "Gulf of Aden", "Red Sea", "Suez Canal",
    "Kashmir Valley", "Bay of Bengal", "Strait of Hormuz",
]
ADDRESSES = [
    "14 MG Road, Bengaluru", "221B Baker Street, London",
    "500 Oracle Parkway, Redwood City", "Plot 12, Vijay Nagar, Indore",
    "88 Marina Boulevard, Singapore", "1 Microsoft Way, Redmond",
]
DATES = [
    "12 March 2024", "2026-06-09", "01/11/2025", "15 August 2023",
    "3 July 2026", "November 2024", "Q3 2025", "21 June 2026",
]
TIMES = ["09:30 AM", "14:05", "18:45", "08:00", "23:10"]
DESIGNATIONS = [
    "Software Engineer", "Data Analyst", "Project Manager", "Chief Executive Officer",
    "Security Analyst", "Cloud Architect", "Physician", "Intelligence Officer",
    "Supply Chain Manager", "Machine Learning Engineer", "Legal Counsel",
    "Financial Controller", "DevOps Engineer", "Research Scientist",
]
DEPARTMENTS = [
    "Human Resources", "Finance", "Cybersecurity", "Research and Development",
    "Logistics", "Clinical Operations", "Legal", "Procurement",
]
PRODUCTS = [
    "Azure OpenAI", "Microsoft 365", "Windows 11", "Surface Laptop",
    "AWS Lambda", "Salesforce CRM", "SAP S/4HANA", "Tesla Model Y",
    "iPhone 16", "Cisco Catalyst", "CrowdStrike Falcon",
]
SKILLS = [
    "Python", "named entity recognition", "cloud architecture",
    "financial modeling", "incident response", "contract negotiation",
    "Kubernetes", "data governance", "clinical diagnosis",
]
TECHNOLOGIES = [
    "Azure Active Directory", "Kubernetes", "Apache Kafka", "PostgreSQL",
    "PyTorch", "GLiNER", "Terraform", "Docker", "Redis", "Elasticsearch",
]
LANGUAGES = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "C#", "SQL", "Rust",
]
MODELS = [
    "GPT-4o", "GLiNER", "BERT", "RoBERTa", "Llama 3", "Phi-3", "YOLOv8",
]
EVENTS = [
    "G20 Summit", "DefExpo 2026", "Olympic Games", "Black Hat Conference",
    "annual board meeting", "cybersecurity tabletop exercise",
    "monsoon relief operation",
]
PROJECTS = [
    "Project Falcon", "Operation Blue Shield", "Digital India Stack",
    "Project Nightingale", "Horizon Migration",
]
TEAMS = [
    "Mumbai Indians", "Manchester City", "Team Liquid", "India national cricket team",
]
COMPETITIONS = [
    "Indian Premier League", "UEFA Champions League", "World Cup",
    "The International",
]
AWARDS = [
    "Padma Shri", "Nobel Prize", "ACM Turing Award", "Employee of the Year",
]
NATIONALITIES = [
    "Indian", "American", "British", "Japanese", "German", "Emirati", "French",
]
DOCTORS = [
    "Dr. Rajesh Mehta", "Dr. Anjali Rao", "Dr. Sarah Collins", "Dr. Omar Farouk",
]
HOSPITALS = [
    "AIIMS Delhi", "Apollo Hospital", "Mayo Clinic", "Cleveland Clinic",
    "Fortis Hospital",
]
MEDICINES = [
    "Paracetamol", "Amoxicillin", "Metformin", "Atorvastatin", "Ibuprofen",
]
DISEASES = [
    "Type 2 diabetes", "hypertension", "malaria", "tuberculosis", "influenza",
]
BANKS = [
    "HDFC Bank", "State Bank of India", "JPMorgan Chase", "HSBC", "ICICI Bank",
]
WEAPONS = [
    "ballistic missile", "unmanned aerial vehicle", "assault rifle",
    "cruise missile", "surface-to-air missile", "explosives",
    "fighter aircraft", "artillery", "UAV", "ammunition",
]
THREAT_ACTORS = [
    "Lazarus Group", "APT29", "ISIS", "Anonymous", "Sandworm",
]
UNITS = [
    "Eastern Naval Command", "12th Infantry Division", "Rapid Action Force",
    "Special Protection Group", "Royal Saudi Air Force",
    "Logistics Coordination Office",
]
INFRA = [
    "Jawaharlal Nehru Port", "Tarapur Atomic Power Station",
    "Indira Gandhi International Airport", "Kaiga nuclear plant",
    "Mumbai suburban railway", "Facility Falcon", "Facility Oasis",
    "Facility Blue Port", "ammunition depot",
]
DOCUMENT_NUMBERS = [
    "FCT-2026-422B2D", "RSA-865", "DOC-2025-881A", "INV-77821", "NDA-2024-19",
]
DOCUMENT_TYPES = [
    "Restricted Defense Asset Inventory Brief",
    "Critical Infrastructure Resilience Bulletin",
    "Counter-Terrorism Threat Digest",
    "Export Continuity Advisory",
    "Cryptographic Key Custody Log",
]
AGREEMENTS = [
    "non-disclosure agreement", "master service agreement",
    "bilateral defence pact", "data processing addendum",
]
QUANTITIES = [
    "1,250 employees", "3.4 million", "450 MW", "12 missiles", "2,000 tons",
]

PROMPT = MODEL_LABEL_PROMPTS
LEXICONS = {
    "PERSON": lambda rng: f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
    "ORGANIZATION": ORGANIZATIONS,
    "LOCATION": LOCATIONS,
    "CITY": CITIES,
    "COUNTRY": COUNTRIES,
    "ADDRESS": ADDRESSES,
    "DATE": DATES,
    "TIME": TIMES,
    "DESIGNATION": DESIGNATIONS,
    "DEPARTMENT": DEPARTMENTS,
    "PRODUCT": PRODUCTS,
    "SKILL": SKILLS,
    "TECHNOLOGY": TECHNOLOGIES,
    "PROGRAMMING_LANGUAGE": LANGUAGES,
    "MODEL_NAME": MODELS,
    "EVENT": EVENTS,
    "PROJECT": PROJECTS,
    "TEAM": TEAMS,
    "COMPETITION": COMPETITIONS,
    "AWARD": AWARDS,
    "NATIONALITY": NATIONALITIES,
    "DOCTOR": DOCTORS,
    "HOSPITAL": HOSPITALS,
    "MEDICINE": MEDICINES,
    "DISEASE": DISEASES,
    "BANK": BANKS,
    "WEAPON": WEAPONS,
    "THREAT_ACTOR": THREAT_ACTORS,
    "MILITARY_UNIT": UNITS,
    "INFRASTRUCTURE": INFRA,
    "AGREEMENT": AGREEMENTS,
    "QUANTITY": QUANTITIES,
    "DOCUMENT_NUMBER": DOCUMENT_NUMBERS,
    "DOCUMENT_TYPE": DOCUMENT_TYPES,
}


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def pick(label: str, rng: random.Random) -> str:
    values = LEXICONS[label]
    if callable(values):
        return values(rng)
    return rng.choice(values)


def append_text(tokens: list[str], text: str) -> None:
    tokens.extend(tokenize(text))


def append_entity(
    tokens: list[str],
    ner: list[list],
    label: str,
    rng: random.Random,
) -> str:
    value = pick(label, rng)
    value_tokens = tokenize(value)
    start = len(tokens)
    tokens.extend(value_tokens)
    ner.append([start, len(tokens) - 1, PROMPT[label]])
    return value


def sample_from_parts(parts: list, rng: random.Random) -> dict:
    tokens: list[str] = []
    ner: list[list] = []
    for part in parts:
        if isinstance(part, tuple):
            append_entity(tokens, ner, part[0], rng)
        else:
            append_text(tokens, part)
    return {"tokenized_text": tokens, "ner": ner}


def business_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_entity(tokens, ner, "PERSON", rng)
    append_text(tokens, ", a ")
    append_entity(tokens, ner, "DESIGNATION", rng)
    append_text(tokens, " at ")
    append_entity(tokens, ner, "ORGANIZATION", rng)
    append_text(tokens, " in ")
    append_entity(tokens, ner, "LOCATION", rng)
    append_text(tokens, ", led ")
    append_entity(tokens, ner, "PROJECT", rng)
    append_text(tokens, " under a ")
    append_entity(tokens, ner, "AGREEMENT", rng)
    append_text(tokens, " signed on ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def hr_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_text(tokens, "Candidate ")
    append_entity(tokens, ner, "PERSON", rng)
    append_text(tokens, " applied for ")
    append_entity(tokens, ner, "DESIGNATION", rng)
    append_text(tokens, " in the ")
    append_entity(tokens, ner, "DEPARTMENT", rng)
    append_text(tokens, " team, listing ")
    append_entity(tokens, ner, "SKILL", rng)
    append_text(tokens, " and ")
    append_entity(tokens, ner, "TECHNOLOGY", rng)
    append_text(tokens, " among core strengths.")
    return {"tokenized_text": tokens, "ner": ner}


def medical_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_entity(tokens, ner, "DOCTOR", rng)
    append_text(tokens, " at ")
    append_entity(tokens, ner, "HOSPITAL", rng)
    append_text(tokens, " diagnosed ")
    append_entity(tokens, ner, "PERSON", rng)
    append_text(tokens, " with ")
    append_entity(tokens, ner, "DISEASE", rng)
    append_text(tokens, " and prescribed ")
    append_entity(tokens, ner, "MEDICINE", rng)
    append_text(tokens, " on ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def tech_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_entity(tokens, ner, "ORGANIZATION", rng)
    append_text(tokens, " deployed ")
    append_entity(tokens, ner, "PRODUCT", rng)
    append_text(tokens, " using ")
    append_entity(tokens, ner, "PROGRAMMING_LANGUAGE", rng)
    append_text(tokens, " and ")
    append_entity(tokens, ner, "TECHNOLOGY", rng)
    append_text(tokens, ", with inference served by ")
    append_entity(tokens, ner, "MODEL_NAME", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def finance_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_entity(tokens, ner, "PERSON", rng)
    append_text(tokens, " transferred funds through ")
    append_entity(tokens, ner, "BANK", rng)
    append_text(tokens, " after the ")
    append_entity(tokens, ner, "AGREEMENT", rng)
    append_text(tokens, " took effect on ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, " at ")
    append_entity(tokens, ner, "TIME", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def security_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_text(tokens, "Intelligence linked ")
    append_entity(tokens, ner, "THREAT_ACTOR", rng)
    append_text(tokens, " to a plot involving a ")
    append_entity(tokens, ner, "WEAPON", rng)
    append_text(tokens, " near ")
    append_entity(tokens, ner, "INFRASTRUCTURE", rng)
    append_text(tokens, ". ")
    append_entity(tokens, ner, "MILITARY_UNIT", rng)
    append_text(tokens, " raised readiness to ")
    append_entity(tokens, ner, "QUANTITY", rng)
    append_text(tokens, " before ")
    append_entity(tokens, ner, "EVENT", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def sports_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_entity(tokens, ner, "PERSON", rng)
    append_text(tokens, ", a ")
    append_entity(tokens, ner, "NATIONALITY", rng)
    append_text(tokens, " athlete, represented ")
    append_entity(tokens, ner, "TEAM", rng)
    append_text(tokens, " at the ")
    append_entity(tokens, ner, "COMPETITION", rng)
    append_text(tokens, " in ")
    append_entity(tokens, ner, "LOCATION", rng)
    append_text(tokens, " and later received the ")
    append_entity(tokens, ner, "AWARD", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def address_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_entity(tokens, ner, "ORGANIZATION", rng)
    append_text(tokens, " registered its office at ")
    append_entity(tokens, ner, "ADDRESS", rng)
    append_text(tokens, " and notified partners in ")
    append_entity(tokens, ner, "LOCATION", rng)
    append_text(tokens, " on ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def mixed_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_text(tokens, "On ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, ", ")
    append_entity(tokens, ner, "PERSON", rng)
    append_text(tokens, " of ")
    append_entity(tokens, ner, "ORGANIZATION", rng)
    append_text(tokens, " presented ")
    append_entity(tokens, ner, "PRODUCT", rng)
    append_text(tokens, " during the ")
    append_entity(tokens, ner, "EVENT", rng)
    append_text(tokens, " in ")
    append_entity(tokens, ner, "LOCATION", rng)
    append_text(tokens, ", citing ")
    append_entity(tokens, ner, "QUANTITY", rng)
    append_text(tokens, " in production capacity.")
    return {"tokenized_text": tokens, "ner": ner}


def hard_negative_sample(rng: random.Random) -> dict:
    """Picnic/admin text that must NOT teach SECURITY_THREAT on generic words."""
    tokens, ner = [], []
    append_entity(tokens, ner, "ORGANIZATION", rng)
    append_text(
        tokens,
        " issued a routine picnic weather note. Staff stored blankets and "
        "catering supplies. The document contains no defence, military, or "
        "classified operational plan. Logistics completed ordinary tasks in ",
    )
    append_entity(tokens, ner, "LOCATION", rng)
    append_text(tokens, " between ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, " and ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def defense_inventory_sample(rng: random.Random) -> dict:
    """Mirrors uploaded classification JSON: weapons, units, facilities, refs."""
    tokens, ner = [], []
    append_text(tokens, "Title: ")
    append_entity(tokens, ner, "DOCUMENT_TYPE", rng)
    append_text(tokens, ". Document ")
    append_entity(tokens, ner, "DOCUMENT_NUMBER", rng)
    append_text(tokens, " prepared by ")
    append_entity(tokens, ner, "MILITARY_UNIT", rng)
    append_text(tokens, " on ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, ". Inventory references ")
    append_entity(tokens, ner, "WEAPON", rng)
    append_text(tokens, " and ")
    append_entity(tokens, ner, "WEAPON", rng)
    append_text(tokens, " staged near ")
    append_entity(tokens, ner, "INFRASTRUCTURE", rng)
    append_text(tokens, ". Movement from ")
    append_entity(tokens, ner, "INFRASTRUCTURE", rng)
    append_text(tokens, " to ")
    append_entity(tokens, ner, "INFRASTRUCTURE", rng)
    append_text(tokens, " was coordinated by ")
    append_entity(tokens, ner, "ORGANIZATION", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def threat_digest_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_entity(tokens, ner, "DOCUMENT_TYPE", rng)
    append_text(tokens, " ")
    append_entity(tokens, ner, "DOCUMENT_NUMBER", rng)
    append_text(tokens, " warns that ")
    append_entity(tokens, ner, "THREAT_ACTOR", rng)
    append_text(tokens, " may target ")
    append_entity(tokens, ner, "INFRASTRUCTURE", rng)
    append_text(tokens, " using a ")
    append_entity(tokens, ner, "WEAPON", rng)
    append_text(tokens, ". ")
    append_entity(tokens, ner, "MILITARY_UNIT", rng)
    append_text(tokens, " remains on alert in ")
    append_entity(tokens, ner, "LOCATION", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


def custody_log_sample(rng: random.Random) -> dict:
    tokens, ner = [], []
    append_text(tokens, "Custody log ")
    append_entity(tokens, ner, "DOCUMENT_NUMBER", rng)
    append_text(tokens, " lists cryptographic material held by ")
    append_entity(tokens, ner, "PERSON", rng)
    append_text(tokens, " at ")
    append_entity(tokens, ner, "ORGANIZATION", rng)
    append_text(tokens, " in ")
    append_entity(tokens, ner, "LOCATION", rng)
    append_text(tokens, " effective ")
    append_entity(tokens, ner, "DATE", rng)
    append_text(tokens, ".")
    return {"tokenized_text": tokens, "ner": ner}


GENERATORS = [
    business_sample,
    hr_sample,
    medical_sample,
    tech_sample,
    finance_sample,
    security_sample,
    sports_sample,
    address_sample,
    mixed_sample,
    hard_negative_sample,
    defense_inventory_sample,
    threat_digest_sample,
    custody_log_sample,
]


def generate_dataset(total_samples: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    data = []
    seen = set()
    attempts = 0
    while len(data) < total_samples and attempts < total_samples * 30:
        attempts += 1
        sample = rng.choice(GENERATORS)(rng)
        key = " ".join(sample["tokenized_text"])
        if key in seen or not sample["ner"]:
            continue
        seen.add(key)
        data.append(sample)
    return data


def write_lexicon_files(entities_dir: Path) -> None:
    entities_dir.mkdir(parents=True, exist_ok=True)
    static_maps = {
        "PERSON.txt": [f"{first} {last}" for first in FIRST_NAMES for last in LAST_NAMES[:12]],
        "ORGANIZATION.txt": ORGANIZATIONS,
        "CITY.txt": CITIES,
        "LOCATION.txt": LOCATIONS,
        "ADDRESS.txt": ADDRESSES,
        "DATE.txt": DATES,
        "DESIGNATION.txt": DESIGNATIONS,
        "PRODUCT.txt": PRODUCTS,
        "SKILL.txt": SKILLS,
        "TECHNOLOGY.txt": TECHNOLOGIES,
        "PROGRAMMING_LANGUAGE.txt": LANGUAGES,
        "MODEL_NAME.txt": MODELS,
        "NATIONALITY.txt": NATIONALITIES,
        "MEDICINE.txt": MEDICINES,
        "DISEASE.txt": DISEASES,
        "TEAM.txt": TEAMS,
        "COMPETITION.txt": COMPETITIONS,
        "AWARD.txt": AWARDS,
    }
    for filename, values in static_maps.items():
        path = entities_dir / filename
        unique = list(dict.fromkeys(values))
        path.write_text("\n".join(unique) + "\n", encoding="utf-8")


def label_counts(samples: list[dict]) -> dict:
    counter: Counter[str] = Counter()
    for sample in samples:
        for _, _, label in sample.get("ner", []):
            counter[label] += 1
    return dict(counter)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Azure-class GLiNER training data."
    )
    parser.add_argument("--samples", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        default=str(BACKEND_DIR / "training" / "enterprise_gliner.json"),
    )
    args = parser.parse_args()

    write_lexicon_files(BACKEND_DIR / "entities")
    dataset = generate_dataset(args.samples, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(dataset)} samples to {output}")
    print(json.dumps(label_counts(dataset), indent=2))


if __name__ == "__main__":
    main()
