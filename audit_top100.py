import csv
import json
import re

SUBMISSION_FILE = "submission.csv"
CANDIDATES_FILE = "candidates.jsonl"

BAD_TITLES = [
    "marketing manager", "accountant", "hr manager", "customer support",
    "operations manager", "graphic designer", "sales executive",
    "content writer", "civil engineer", "mechanical engineer"
]

def low(x):
    return str(x or "").lower()

def has_exp_mismatch(candidate):
    profile = candidate.get("profile", {})
    years = float(profile.get("years_of_experience", 0) or 0)
    text = low(profile.get("summary", "")) + " " + low(profile.get("headline", ""))

    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)", text)

    for m in matches:
        mentioned = float(m)
        if abs(years - mentioned) >= 4:
            return True

    return False

top_rows = []

with open(SUBMISSION_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        top_rows.append(row)

ids = {row["candidate_id"] for row in top_rows}
candidate_map = {}

with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        c = json.loads(line)
        cid = c["candidate_id"]

        if cid in ids:
            candidate_map[cid] = c

problems = []

for row in top_rows:
    cid = row["candidate_id"]
    rank = int(row["rank"])
    score = float(row["score"])
    c = candidate_map[cid]

    p = c.get("profile", {})
    s = c.get("redrob_signals", {})

    title = low(p.get("current_title", ""))
    country = low(p.get("country", ""))
    years = float(p.get("years_of_experience", 0) or 0)
    open_to_work = s.get("open_to_work_flag")
    response = float(s.get("recruiter_response_rate", 0) or 0)
    willing = s.get("willing_to_relocate")
    notice = int(s.get("notice_period_days", 180) or 180)

    flags = []

    if any(bad in title for bad in BAD_TITLES):
        flags.append("BAD_TITLE")

    if has_exp_mismatch(c):
        flags.append("EXP_MISMATCH")

    if not open_to_work and response < 0.3:
        flags.append("NOT_OPEN_LOW_RESPONSE")

    if country != "india" and not willing:
        flags.append("NON_INDIA_NO_RELOCATE")

    if years > 14:
        flags.append("VERY_HIGH_EXPERIENCE")

    if notice >= 120:
        flags.append("LONG_NOTICE")

    if flags:
        problems.append((rank, cid, score, p.get("current_title"), years, p.get("location"), country, flags))

print("Total risky candidates in top 100:", len(problems))
print()

for item in problems:
    rank, cid, score, title, years, location, country, flags = item
    print(f"Rank {rank} | {cid} | score={score} | {title} | {years} yrs | {location}, {country} | {', '.join(flags)}")
