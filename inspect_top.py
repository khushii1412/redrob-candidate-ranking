import csv
import json

SUBMISSION_FILE = "submission.csv"
CANDIDATES_FILE = "candidates.jsonl"

top_candidates = []

with open(SUBMISSION_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rank = int(row["rank"])
        if rank <= 20:
            top_candidates.append({
                "candidate_id": row["candidate_id"],
                "rank": rank,
                "score": float(row["score"]),
                "reasoning": row["reasoning"]
            })

candidate_map = {}
ids = {c["candidate_id"] for c in top_candidates}

with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        c = json.loads(line)
        cid = c["candidate_id"]
        if cid in ids:
            candidate_map[cid] = c

for tc in top_candidates:
    cid = tc["candidate_id"]
    rank = tc["rank"]
    score = tc["score"]
    c = candidate_map[cid]
    p = c["profile"]
    s = c["redrob_signals"]

    print("=" * 100)
    print(f"Rank {rank} | ID: {cid} | Score: {score}")
    print(f"Name: {p.get('anonymized_name')}")
    print(f"Title: {p.get('current_title')}")
    print(f"Experience: {p.get('years_of_experience')} years")
    print(f"Location: {p.get('location')}, {p.get('country')}")
    print(f"Open to work: {s.get('open_to_work_flag')}")
    print(f"Response rate: {s.get('recruiter_response_rate')}")
    print(f"Notice period: {s.get('notice_period_days')} days")
    print(f"Reasoning in CSV: {tc['reasoning']}")

    print("\nTop Skills:")
    skills_list = []
    for skill in c.get("skills", [])[:15]:
        skills_list.append(f"{skill.get('name')} ({skill.get('proficiency')}, {skill.get('duration_months')}m)")
    print(", ".join(skills_list))

    print("\nCareer History Summary:")
    for job in c.get("career_history", []):
        print(f"- {job.get('title')} at {job.get('company')} ({job.get('duration_months')} months)")
        print(f"  Description: {job.get('description')}")
