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

def get_career_evidence_mentions(candidate):
    history = candidate.get("career_history", [])
    count = 0
    for job in history:
        title = low(job.get("title", ""))
        company = low(job.get("company", ""))
        desc = low(job.get("description", ""))
        combined = title + " " + company + " " + desc

        core_terms = [
            "ranking layer", "ranking pipeline", "learning-to-rank", "learning to rank", "re-ranking", "reranking",
            "hybrid retrieval", "semantic search", "vector search", "embedding-based search", "vector database",
            "candidate-jd matching", "candidate matching", "recommendation system", "recommendation systems", 
            "recommender system", "recommender systems", "recommendation pipeline", "search and discovery", "search & discovery"
        ]
        for term in core_terms:
            if term in combined:
                count += 1

        eval_terms = [
            "ndcg", "mrr", "map", "offline evaluation", "online evaluation", "a/b test", "a/b testing", 
            "offline-online", "human relevance judgments", "evaluation framework", "relevance labeling"
        ]
        for term in eval_terms:
            if term in combined:
                count += 1

        prod_terms = [
            "production", "deployed", "serving", "real users", "p95", "latency", "scale", "qps",
            "50m+", "30m+", "10m+", "35m+", "production deployment", "large-scale search"
        ]
        for term in prod_terms:
            if term in combined:
                count += 1

        infra_terms = [
            "embedding drift", "index refresh", "index versioning", "rollback", "monitoring",
            "feature pipeline", "data pipeline", "retraining", "offline-online evaluation"
        ]
        for term in infra_terms:
            if term in combined:
                count += 1
    return count

def get_ai_skills_count(candidate):
    count = 0
    core_skills = [
        "python", "information retrieval", "learning to rank",
        "learning-to-rank", "semantic search", "vector search",
        "recommendation systems", "recommendation", "embeddings",
        "embedding", "sentence transformers", "sentence-transformers",
        "bm25", "faiss", "milvus", "pinecone", "weaviate", "qdrant",
        "pgvector", "elasticsearch", "opensearch", "rag", "nlp", "llms",
        "llm"
    ]
    for skill in candidate.get("skills", []):
        name = low(skill.get("name", ""))
        if any(core in name for core in core_skills) or any(term in name for term in ["ai", "vector", "llm", "rag", "embeddings", "nlp", "semantic search", "vector search"]):
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

    evidence_count = get_career_evidence_mentions(c)
    skills_count = get_ai_skills_count(c)

    if evidence_count == 0:
        flags.append("LOW_CAREER_EVIDENCE")

    if skills_count >= 5 and evidence_count <= 1:
        flags.append("KEYWORD_SPAM_RISK")

    if flags:
        problems.append((rank, cid, score, p.get("current_title"), years, p.get("location"), country, flags))

print("Total risky candidates in top 100:", len(problems))
print()

for item in problems:
    rank, cid, score, title, years, location, country, flags = item
    print(f"Rank {rank} | {cid} | score={score} | {title} | {years} yrs | {location}, {country} | {', '.join(flags)}")
