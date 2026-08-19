"""Customer dataset generator."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from data_generation.config import GeneratorConfig
from data_generation.utils import seeded_rng, weighted_choice

CUSTOMER_COLUMNS = [
    "customer_id",
    "customer_name",
    "email",
    "country",
    "signup_date",
    "customer_segment",
    "lifetime_value",
]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Daniel", "Lisa", "Matthew", "Nancy",
    "Anthony", "Emily", "Mark", "Ashley", "Donald", "Amanda", "Steven", "Stephanie",
    "Paul", "Melissa", "Andrew", "Rebecca", "Joshua", "Laura", "Kenneth", "Sharon",
    "Priya", "Raj", "Ananya", "Arjun", "Sofia", "Lucas", "Emma", "Oliver", "Mia", "Noah",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Patel", "Singh", "Kumar", "Sharma", "Chen", "Wang", "Kim", "Nguyen", "Mueller",
]

EMAIL_DOMAINS = [
    ("gmail.com", 0.35),
    ("outlook.com", 0.15),
    ("yahoo.com", 0.10),
    ("hotmail.com", 0.08),
    ("icloud.com", 0.07),
    ("company.com", 0.10),
    ("corp.net", 0.05),
    ("mail.io", 0.10),
]


def generate_customers(config: GeneratorConfig) -> list[dict]:
    """Generate clean customer records with unique IDs and no anomalies."""
    rng = seeded_rng(config.reproducibility.random_seed, "customers")
    params = config.business_parameters
    count = config.dataset_sizes.customer_count

    countries = [c.name for c in params.countries]
    country_weights = [c.weight for c in params.countries]
    domain_names = [d[0] for d in EMAIL_DOMAINS]
    domain_weights = [d[1] for d in EMAIL_DOMAINS]

    used_emails: set[str] = set()
    date_range = params.date_range
    signup_end = date_range.end_date - timedelta(days=30)

    customers: list[dict] = []
    for customer_id in range(1, count + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        customer_name = f"{first} {last}"

        email = _unique_email(rng, first, last, domain_names, domain_weights, used_emails)
        country = rng.choices(countries, weights=country_weights, k=1)[0]
        segment = weighted_choice(rng, params.customer_segments)
        signup_date = _random_date(rng, date_range.start_date, signup_end)
        ltv_range = params.lifetime_value[segment]
        lifetime_value = _random_decimal(rng, ltv_range.min, ltv_range.max)

        customers.append({
            "customer_id": customer_id,
            "customer_name": customer_name,
            "email": email,
            "country": country,
            "signup_date": signup_date,
            "customer_segment": segment,
            "lifetime_value": lifetime_value,
        })

    return customers


def _unique_email(
    rng: random.Random,
    first: str,
    last: str,
    domains: list[str],
    domain_weights: list[float],
    used: set[str],
) -> str:
    """Generate a unique email address."""
    base = f"{first.lower()}.{last.lower()}"
    domain = rng.choices(domains, weights=domain_weights, k=1)[0]
    candidate = f"{base}@{domain}"
    suffix = 1
    while candidate in used:
        candidate = f"{base}{suffix}@{domain}"
        suffix += 1
    used.add(candidate)
    return candidate


def _random_date(rng: random.Random, start: date, end: date) -> date:
    """Generate a random date in [start, end] inclusive."""
    delta = (end - start).days
    offset = rng.randint(0, delta)
    return start + timedelta(days=offset)


def _random_decimal(rng: random.Random, low: Decimal, high: Decimal) -> Decimal:
    span = float(high - low)
    value = float(low) + rng.random() * span
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
