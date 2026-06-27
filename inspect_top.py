import csv
import json

SUBMISSION_FILE = "submission.csv"
CANDIDATES_FILE = "candidates.jsonl"

top_ids = []

with open(SUBMISSION_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if int(row["rank"]) <= 20:
            top_ids.append(row["candidate_id"])

candidate_map = {}

with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        candidate = json.loads(line)
        cid = candidate["candidate_id"]

        if cid in top_ids:
            candidate_map[cid] = candidate

for cid in top_ids:
    c = candidate_map[cid]
    p = c["profile"]
    s = c["redrob_signals"]

    print("=" * 100)
    print("ID:", cid)
    print("Name:", p.get("anonymized_name"))
    print("Title:", p.get("current_title"))
    print("Experience:", p.get("years_of_experience"))
    print("Location:", p.get("location"), p.get("country"))
    print("Headline:", p.get("headline"))
    print("Summary:", p.get("summary"))
    print("Open to work:", s.get("open_to_work_flag"))
    print("Response rate:", s.get("recruiter_response_rate"))
    print("Notice period:", s.get("notice_period_days"))
    print("GitHub score:", s.get("github_activity_score"))

    print("\nSkills:")
    for skill in c.get("skills", [])[:15]:
        print(
            "-",
            skill.get("name"),
            "|",
            skill.get("proficiency"),
            "|",
            skill.get("duration_months"),
            "months"
        )

    print("\nCareer:")
    for job in c.get("career_history", []):
        print("-", job.get("title"), "at", job.get("company"))
        print(" ", job.get("description"))
