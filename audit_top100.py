import csv
import json
import re
import sys
import signal

try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except AttributeError:
    pass

SUBMISSION_FILE = "submission.csv"
CANDIDATES_FILE = "candidates.jsonl"

BAD_TITLES = [
    "marketing manager", "accountant", "hr manager", "customer support",
    "operations manager", "graphic designer", "sales executive",
    "content writer", "civil engineer", "mechanical engineer"
]

GOOD_EVIDENCE_TERMS = [
    "built and shipped production recommendation system",
    "production recommendation system",
    "recommender system",
    "recommendation system",
    "recommendation systems",
    "recommendation pipeline",
    "semantic search system",
    "semantic search",
    "hybrid retrieval",
    "bm25 + dense retrieval",
    "dense retrieval",
    "bm25",
    "vector search",
    "vector database",
    "embedding-based search",
    "learning-to-rank",
    "learning to rank",
    "ranking pipeline",
    "ranking layer",
    "re-ranking",
    "reranking",
    "rag-based ranking",
    "rag ranking",
    "candidate-jd matching",
    "candidate matching",
    "candidate-jd",
    "recruiter-facing search",
    "search & discovery",
    "search and discovery",
    "a/b testing",
    "a/b test",
    "ndcg",
    "mrr",
    "map",
    "recall@k",
    "p95 latency",
    "p95",
    "latency",
    "qps",
    "offline/online evaluation",
    "offline-online evaluation",
    "offline evaluation",
    "online evaluation",
    "relevance labels",
    "relevance labeling",
    "human relevance judgments",
    "embedding drift",
    "index refresh",
    "index versioning",
    "production deployment",
    "production ml",
    "deployed",
    "serving",
    "real users"
]

AI_SKILL_TERMS = [
    "llm", "rag", "embedding", "vector", "faiss", "pinecone", "qdrant",
    "weaviate", "milvus", "elasticsearch", "opensearch", "nlp",
    "recommendation", "ranking", "search", "fine-tuning", "lora", "qlora"
]


def low(x):
    return str(x or "").lower()


def get_notice(signals):
    notice_raw = signals.get("notice_period_days", 180)
    if notice_raw is None:
        return 180
    return int(notice_raw)


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


def career_evidence_count(candidate):
    count = 0

    for job in candidate.get("career_history", []):
        text = low(job.get("title", "")) + " " + low(job.get("description", ""))

        for term in GOOD_EVIDENCE_TERMS:
            if term in text:
                count += 1

    return count


def ai_skill_count(candidate):
    count = 0

    for skill in candidate.get("skills", []):
        name = low(skill.get("name", ""))

        if any(term in name for term in AI_SKILL_TERMS):
            count += 1

    return count


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

# To store summary counts by risk flag type
flag_counts_overall = {
    "BAD_TITLE": 0,
    "EXP_MISMATCH": 0,
    "NOT_OPEN_LOW_RESPONSE": 0,
    "NON_INDIA_NO_RELOCATE": 0,
    "VERY_HIGH_EXPERIENCE": 0,
    "LONG_NOTICE": 0,
    "LOW_CAREER_EVIDENCE": 0,
    "KEYWORD_SPAM_RISK": 0
}

top10_risky = 0
top20_risky = 0
top50_risky = 0

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
    notice = get_notice(s)

    evidence_count = career_evidence_count(c)
    skill_count = ai_skill_count(c)

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

    if evidence_count <= 2:
        flags.append("LOW_CAREER_EVIDENCE")

    if skill_count >= 8 and evidence_count <= 2:
        flags.append("KEYWORD_SPAM_RISK")

    if flags:
        # Increment flag counts
        for flag in flags:
            if flag in flag_counts_overall:
                flag_counts_overall[flag] += 1
                
        # Count risky per range
        if rank <= 10:
            top10_risky += 1
        if rank <= 20:
            top20_risky += 1
        if rank <= 50:
            top50_risky += 1

        problems.append((
            rank, cid, score, p.get("current_title"), years,
            p.get("location"), country, notice, flags
        ))

print("==================================================")
print("              RISK FLAG SUMMARY                  ")
print("==================================================")
print(f"Top 10 Risky Candidates Count: {top10_risky}")
print(f"Top 20 Risky Candidates Count: {top20_risky}")
print(f"Top 50 Risky Candidates Count: {top50_risky}")
print(f"Total Risky Candidates in Top 100: {len(problems)}")
print()
print("Risk Flag Counts Overall:")
for flag, count in flag_counts_overall.items():
    print(f"  - {flag}: {count}")
print()
print("==================================================")
print("             DETAILED RISKY LIST                 ")
print("==================================================")
for item in problems:
    rank, cid, score, title, years, location, country, notice, flags = item
    print(
        f"Rank {rank} | {cid} | score={score} | {title} | "
        f"{years} yrs | {location}, {country} | notice={notice} | {', '.join(flags)}"
    )
