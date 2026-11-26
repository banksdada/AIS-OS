#!/usr/bin/env python3
"""Generate the Beauty Booked Up blog and microsite keyword banks."""

import csv
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "projects" / "beautybookedup"
BLOG_PATH = OUT_DIR / "keyword-bank.csv"
MICROSITE_PATH = OUT_DIR / "microsite-keyword-bank.csv"

START_DATE = date(2026, 11, 27)
SLOTS = ["07:00", "19:00"]

LOCATIONS = [
    "Wigan",
    "Manchester",
    "North West",
    "St Helens",
    "Bolton",
    "Warrington",
    "Leigh",
    "Chorley",
    "Salford",
    "Stockport",
]

BLOG_STEMS = [
    ("Websites and conversion", "Commercial", "website for beauticians in {location}"),
    ("Websites and conversion", "Commercial", "beauty business website in {location}"),
    ("Websites and conversion", "Commercial", "salon website that takes bookings in {location}"),
    ("Websites and conversion", "Commercial", "website for mobile beauty therapists in {location}"),
    ("Websites and conversion", "Informational", "beauty website checklist for {location} salons"),
    ("Websites and conversion", "Commercial", "beauty salon website design in {location}"),
    ("Websites and conversion", "Informational", "how to turn website visitors into beauty clients in {location}"),
    ("Websites and conversion", "Commercial", "one-page website for beauty businesses in {location}"),
    ("Websites and conversion", "Commercial", "website copy for beauticians in {location}"),
    ("Websites and conversion", "Commercial", "booking button for beauty website in {location}"),
    ("Websites and conversion", "Informational", "beauty website mistakes in {location}"),
    ("Websites and conversion", "Informational", "mobile-friendly beauty website in {location}"),
    ("Bookings and calendar", "Transactional", "booking system for beauty businesses in {location}"),
    ("Bookings and calendar", "Transactional", "online booking for lash techs in {location}"),
    ("Bookings and calendar", "Transactional", "booking link for nail techs in {location}"),
    ("Bookings and calendar", "Informational", "reduce no-shows for salons in {location}"),
    ("Bookings and calendar", "Transactional", "appointment reminders for beauticians in {location}"),
    ("Bookings and calendar", "Commercial", "salon calendar management in {location}"),
    ("Bookings and calendar", "Informational", "fill empty weekdays in {location} salons"),
    ("Bookings and calendar", "Informational", "deposit policy for beauty appointments in {location}"),
    ("Bookings and calendar", "Informational", "cancellation policy for salons in {location}"),
    ("Bookings and calendar", "Transactional", "same-day bookings for beauty salons in {location}"),
    ("Instagram and social", "Informational", "Instagram auto replies for salons in {location}"),
    ("Instagram and social", "Informational", "how to automate salon DMs in {location}"),
    ("Instagram and social", "Transactional", "Instagram bio link for beauty businesses in {location}"),
    ("Instagram and social", "Commercial", "social media management for beauty salons in {location}"),
    ("Instagram and social", "Informational", "Instagram story ideas for lash techs in {location}"),
    ("Instagram and social", "Informational", "content ideas for nail techs in {location}"),
    ("Instagram and social", "Informational", "how to turn Instagram DMs into bookings in {location}"),
    ("Instagram and social", "Informational", "saved replies for beauty businesses in {location}"),
    ("Instagram and social", "Informational", "Instagram highlight ideas for salons in {location}"),
    ("Instagram and social", "Informational", "weekly social plan for beauticians in {location}"),
    ("Google and reviews", "Informational", "Google Business Profile for beauticians in {location}"),
    ("Google and reviews", "Informational", "how to get more Google reviews in a beauty salon in {location}"),
    ("Google and reviews", "Commercial", "local SEO for beauty salons in {location}"),
    ("Google and reviews", "Commercial", "Google Maps visibility for beauty businesses in {location}"),
    ("Google and reviews", "Informational", "beauty salon SEO checklist for {location}"),
    ("Google and reviews", "Informational", "review request template for beauticians in {location}"),
    ("Google and reviews", "Informational", "respond to Google reviews for salons in {location}"),
    ("Google and reviews", "Informational", "Google posts for beauty businesses in {location}"),
    ("Google and reviews", "Informational", "local keywords for beauty salons in {location}"),
    ("Google and reviews", "Informational", "get found by clients searching near me in {location}"),
    ("AI and automation", "Commercial", "AI tools for beauty businesses in {location}"),
    ("AI and automation", "Commercial", "beauty business automation in {location}"),
    ("AI and automation", "Commercial", "AI for salon admin in {location}"),
    ("AI and automation", "Informational", "automate client follow-ups for beauticians in {location}"),
    ("AI and automation", "Informational", "AI content ideas for beauty salons in {location}"),
    ("AI and automation", "Commercial", "chatbot for beauty bookings in {location}"),
    ("AI and automation", "Informational", "automate review requests in {location} salons"),
    ("AI and automation", "Commercial", "AI inbox triage for beauty businesses in {location}"),
    ("AI and automation", "Informational", "simple AI workflows for lash techs in {location}"),
    ("Niche marketing", "Commercial", "marketing for African hair stylists in {location}"),
    ("Niche marketing", "Commercial", "marketing for braiders in {location}"),
    ("Niche marketing", "Commercial", "loc technician marketing in {location}"),
    ("Niche marketing", "Commercial", "wig maker marketing in {location}"),
    ("Niche marketing", "Commercial", "lash tech marketing in {location}"),
    ("Niche marketing", "Commercial", "nail tech marketing in {location}"),
    ("Niche marketing", "Commercial", "brow artist marketing in {location}"),
    ("Niche marketing", "Commercial", "aesthetician marketing in {location}"),
    ("Niche marketing", "Commercial", "mobile beauty marketing in {location}"),
    ("Niche marketing", "Commercial", "hair salon marketing in {location}"),
    ("Growth and retention", "Informational", "how to get more beauty clients in {location}"),
    ("Growth and retention", "Informational", "client retention for beauty salons in {location}"),
    ("Growth and retention", "Informational", "repeat bookings for lash techs in {location}"),
    ("Growth and retention", "Informational", "referral ideas for beauty businesses in {location}"),
    ("Growth and retention", "Commercial", "premium pricing for beauty services in {location}"),
    ("Growth and retention", "Informational", "client follow-up messages for beauticians in {location}"),
    ("Growth and retention", "Informational", "fill a beauty diary in {location}"),
    ("Operations and basics", "Informational", "CRM for beauty businesses in {location}"),
    ("Operations and basics", "Informational", "beauty business admin checklist in {location}"),
    ("Operations and basics", "Informational", "inbox management for salons in {location}"),
    ("Operations and basics", "Informational", "privacy and GDPR for beauty websites in {location}"),
    ("Operations and basics", "Informational", "booking terms for beauty salons in {location}"),
]

NICHES = [
    "lash techs",
    "nail salons",
    "brow artists",
    "hair salons",
    "aesthetic clinics",
    "mobile beauty therapists",
    "African hair braiders",
    "loc technicians",
    "wig makers",
    "makeup artists",
    "beauty salons",
    "skin clinics",
    "hairdressers",
]

CONSUMER_KEYWORDS = {
    "lash techs": "lash artists in {location}",
    "nail salons": "nail salon in {location}",
    "brow artists": "brow artists in {location}",
    "hair salons": "hair salon in {location}",
    "aesthetic clinics": "aesthetics clinic in {location}",
    "mobile beauty therapists": "mobile beauty therapist in {location}",
    "African hair braiders": "African hair braiding in {location}",
    "loc technicians": "loc technician in {location}",
    "wig makers": "wig maker in {location}",
    "makeup artists": "makeup artist in {location}",
    "beauty salons": "beauty salon in {location}",
    "skin clinics": "skin clinic in {location}",
    "hairdressers": "hairdressers in {location}",
}

CHALLENGE_PHRASES = {
    "no-shows": "reduce no-shows for {niche} in {location}",
    "empty weekdays": "fill empty weekdays for {niche} in {location}",
    "poor Google visibility": "improve Google visibility for {niche} in {location}",
    "slow Instagram replies": "speed up Instagram replies for {niche} in {location}",
    "no online booking": "add online booking for {niche} in {location}",
    "weak website": "improve website for {niche} in {location}",
    "few Google reviews": "get more Google reviews for {niche} in {location}",
    "admin overload": "reduce admin for {niche} in {location}",
    "client drop-off": "improve repeat bookings for {niche} in {location}",
    "last-minute cancellations": "handle last-minute cancellations for {niche} in {location}",
}

OUTCOME_PHRASES = {
    "more bookings": "get more bookings for {niche} in {location}",
    "fewer gaps": "fewer diary gaps for {niche} in {location}",
    "faster replies": "faster client replies for {niche} in {location}",
    "better local visibility": "better local visibility for {niche} in {location}",
    "fuller diary": "fuller diary for {niche} in {location}",
    "more reviews": "more Google reviews for {niche} in {location}",
    "repeat clients": "more repeat clients for {niche} in {location}",
    "less admin": "less admin for {niche} in {location}",
    "higher-value clients": "attract higher-value clients for {niche} in {location}",
    "calmer inbox": "calmer inbox for {niche} in {location}",
}

BLOG_FIELDS = [
    "keyword",
    "use_for",
    "location",
    "status",
    "draft_file",
    "approved",
    "last_used",
    "notes",
    "pillar",
    "intent",
    "scheduled_date",
    "slot",
]

MICROSITE_FIELDS = [
    "id",
    "status",
    "location",
    "niche",
    "challenge",
    "outcome",
    "consumer_keyword",
    "primary_keyword",
    "secondary_keyword",
    "site_folder",
    "notes",
    "use_for",
]


def write_csv(path, fields, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def slugify(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def blog_rows():
    rows = []
    for index in range(730):
        pillar, intent, stem = BLOG_STEMS[index % len(BLOG_STEMS)]
        location = LOCATIONS[(index // len(BLOG_STEMS)) % len(LOCATIONS)]
        day_offset = index // len(SLOTS)
        rows.append(
            {
                "keyword": stem.format(location=location),
                "use_for": "Beauty Booked Up",
                "location": location,
                "status": "new",
                "draft_file": "",
                "approved": "",
                "last_used": "",
                "notes": "",
                "pillar": pillar,
                "intent": intent,
                "scheduled_date": (START_DATE + timedelta(days=day_offset)).isoformat(),
                "slot": SLOTS[index % len(SLOTS)],
            }
        )
    return rows


def microsite_rows():
    rows = []
    challenges = list(CHALLENGE_PHRASES)
    outcomes = list(OUTCOME_PHRASES)
    for index in range(500):
        location = LOCATIONS[index % len(LOCATIONS)]
        niche = NICHES[(index // len(LOCATIONS)) % len(NICHES)]
        challenge = challenges[(index // (len(LOCATIONS) * len(NICHES))) % len(challenges)]
        outcome = outcomes[(index // 7) % len(outcomes)]
        primary = CHALLENGE_PHRASES[challenge].format(niche=niche, location=location)
        secondary = OUTCOME_PHRASES[outcome].format(niche=niche, location=location)
        rows.append(
            {
                "id": f"MS-{index + 1:03d}",
                "status": "planned",
                "location": location,
                "niche": niche,
                "challenge": challenge,
                "outcome": outcome,
                "consumer_keyword": CONSUMER_KEYWORDS[niche].format(location=location),
                "primary_keyword": primary,
                "secondary_keyword": secondary,
                "site_folder": slugify(f"{location}-{niche}-{challenge}"),
                "notes": "Planned only. Do not create a project or repo without explicit approval.",
                "use_for": "Microsite",
            }
        )
    return rows


def main():
    blog = blog_rows()
    microsites = microsite_rows()
    assert len(blog) == 730
    assert len(microsites) == 500
    assert len({row["keyword"] for row in blog}) == 730
    assert len({row["primary_keyword"] for row in microsites}) == 500
    write_csv(BLOG_PATH, BLOG_FIELDS, blog)
    write_csv(MICROSITE_PATH, MICROSITE_FIELDS, microsites)
    print(f"Wrote {len(blog)} blog keywords to {BLOG_PATH.relative_to(ROOT)}")
    print(f"Wrote {len(microsites)} microsite keywords to {MICROSITE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
