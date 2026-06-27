import csv
import json
import re

CANDIDATES_FILE = "candidates.jsonl"
OUT_FILE = "submission.csv"

GOOD_TERMS = [
    "retrieval", "hybrid retrieval", "ranking", "learning to rank",
    "learning-to-rank", "search", "semantic search", "vector search",
    "search backend", "search infrastructure", "search & discovery",
    "recommendation", "recommendation systems", "recommender",
    "information retrieval", "embedding", "embeddings",
    "sentence transformers", "sentence-transformers", "bm25",
    "faiss", "milvus", "pinecone", "weaviate", "qdrant",
    "pgvector", "elasticsearch", "opensearch",
    "nlp", "llm", "llms", "rag", "fine-tuning", "finetuning",
    "lora", "qlora", "peft", "python", "machine learning", "ml",
    "mlops", "evaluation", "eval framework", "a/b testing",
    "offline metrics", "online metrics", "ndcg", "mrr", "map",
    "candidate-jd matching", "candidate matching"
]

CORE_SKILLS = [
    "python", "information retrieval", "learning to rank",
    "learning-to-rank", "semantic search", "vector search",
    "recommendation systems", "recommendation", "embeddings",
    "embedding", "sentence transformers", "sentence-transformers",
    "bm25", "faiss", "milvus", "pinecone", "weaviate", "qdrant",
    "pgvector", "elasticsearch", "opensearch", "rag", "nlp", "llms",
    "llm"
]

BAD_TERMS = [
    "marketing manager", "accountant", "hr manager", "customer support",
    "operations manager", "graphic designer", "sales executive",
    "content writer", "civil engineer", "mechanical engineer",
    "seo", "photoshop", "tally", "excel"
]

BAD_TITLES = [
    "marketing manager", "accountant", "hr manager", "customer support",
    "operations manager", "graphic designer", "sales executive",
    "content writer", "civil engineer", "mechanical engineer"
]

GOOD_LOCATIONS = [
    "pune", "noida", "delhi", "gurgaon", "gurugram",
    "mumbai", "hyderabad", "bangalore", "bengaluru"
]

SERVICE_COMPANIES = [
    "tcs", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "mindtree"
]


def safe_lower(value):
    return str(value or "").lower()


def load_candidates(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def collect_text(candidate):
    profile = candidate.get("profile", {})

    parts = [
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", ""),
        profile.get("current_company", ""),
        profile.get("current_industry", ""),
        profile.get("location", ""),
        profile.get("country", ""),
    ]

    for job in candidate.get("career_history", []):
        parts.extend([
            job.get("title", ""),
            job.get("company", ""),
            job.get("industry", ""),
            job.get("description", ""),
        ])

    for skill in candidate.get("skills", []):
        parts.append(skill.get("name", ""))

    return safe_lower(" ".join(parts))


def experience_score(years):
    years = float(years or 0)

    if 6 <= years <= 8:
        return 24
    if 5 <= years < 6 or 8 < years <= 9:
        return 18
    if 4 <= years < 5 or 9 < years <= 11:
        return 8
    if 3 <= years < 4:
        return 0
    if years < 3:
        return -18
    if years > 14:
        return -25
    if years > 11:
        return -10

    return 0


def title_score(candidate):
    profile = candidate.get("profile", {})
    title = safe_lower(profile.get("current_title", ""))

    excellent_titles = [
        "senior ai engineer",
        "lead ai engineer",
        "staff machine learning engineer",
        "senior machine learning engineer",
        "senior ml engineer",
        "senior nlp engineer",
        "recommendation systems engineer",
        "search engineer",
        "applied ml engineer",
        "senior applied scientist",
        "staff applied scientist"
    ]

    good_titles = [
        "ai engineer",
        "machine learning engineer",
        "ml engineer",
        "nlp engineer",
        "data scientist",
        "applied scientist"
    ]

    score = 0

    for item in excellent_titles:
        if item in title:
            score += 24
            break
    else:
        for item in good_titles:
            if item in title:
                score += 12
                break

    for item in BAD_TITLES:
        if item in title:
            score -= 45
            break

    return score


def text_score(text):
    score = 0

    for term in GOOD_TERMS:
        if term in text:
            score += 4

    for term in BAD_TERMS:
        if term in text:
            score -= 7

    strong_phrases = [
        "production recommendation system",
        "production ml systems",
        "hybrid retrieval system",
        "semantic search system",
        "learning-to-rank model",
        "learning to rank model",
        "ranking pipeline",
        "ranking layer",
        "retrieval architecture",
        "candidate-jd matching",
        "offline evaluation framework",
        "online a/b",
        "a/b testing infrastructure",
        "embedding drift",
        "index refresh",
        "relevance labeling",
        "recruiter-feedback loop",
        "behavioral-signal integration",
        "offline-online evaluation"
    ]

    for phrase in strong_phrases:
        if phrase in text:
            score += 13

    scale_phrases = [
        "real users", "deployed", "production", "serving",
        "50m+", "30m+", "10m+", "35m+", "8k",
        "p95", "latency", "qps"
    ]

    for phrase in scale_phrases:
        if phrase in text:
            score += 4

    return score


def skills_score(candidate):
    score = 0

    for skill in candidate.get("skills", []):
        name = safe_lower(skill.get("name", ""))
        proficiency = skill.get("proficiency", "")
        duration = int(skill.get("duration_months", 0) or 0)
        endorsements = int(skill.get("endorsements", 0) or 0)

        is_core = any(core in name for core in CORE_SKILLS)
        is_good = any(term in name for term in GOOD_TERMS)

        if is_core:
            score += 9
        elif is_good:
            score += 4

        if is_good:
            if proficiency == "expert":
                score += 5
            elif proficiency == "advanced":
                score += 3
            elif proficiency == "intermediate":
                score += 1

            if duration >= 48:
                score += 4
            elif duration >= 24:
                score += 2
            elif duration <= 3:
                score -= 4

            if endorsements >= 40:
                score += 2
            elif endorsements >= 20:
                score += 1

        if proficiency == "expert" and duration <= 2:
            score -= 30

    return score


def career_score(candidate):
    history = candidate.get("career_history", [])

    if not history:
        return -30

    score = 0
    companies = [safe_lower(job.get("company", "")) for job in history if job.get("company")]

    if companies:
        service_count = 0

        for company in companies:
            if any(service in company for service in SERVICE_COMPANIES):
                service_count += 1

        if service_count == len(companies):
            score -= 20

    for job in history:
        title = safe_lower(job.get("title", ""))
        company = safe_lower(job.get("company", ""))
        description = safe_lower(job.get("description", ""))
        combined = title + " " + company + " " + description

        if any(x in combined for x in [
            "ranking layer",
            "ranking pipeline",
            "learning-to-rank",
            "learning to rank",
            "semantic search",
            "hybrid retrieval",
            "recommendation system",
            "search and discovery",
            "search & discovery",
            "candidate-jd matching",
            "embedding-based search",
            "relevance labeling",
            "re-ranking",
            "reranking",
            "rag-based ranking"
        ]):
            score += 30

        if any(x in combined for x in [
            "ndcg",
            "mrr",
            "map",
            "offline evaluation",
            "online evaluation",
            "a/b test",
            "a/b testing",
            "offline-online",
            "human relevance judgments"
        ]):
            score += 20

        if any(x in combined for x in [
            "production",
            "deployed",
            "serving",
            "real users",
            "p95",
            "latency",
            "scale",
            "qps",
            "50m+",
            "30m+",
            "10m+",
            "35m+"
        ]):
            score += 13

        if any(x in combined for x in [
            "embedding drift",
            "index refresh",
            "index versioning",
            "rollback",
            "monitoring",
            "feature pipeline",
            "data pipeline",
            "retraining"
        ]):
            score += 10

        if any(x in combined for x in [
            "pure research",
            "academic lab",
            "research-only"
        ]):
            score -= 30

    return score


def behavior_score(candidate):
    signals = candidate.get("redrob_signals", {})
    score = 0

    open_to_work = signals.get("open_to_work_flag")
    response_rate = float(signals.get("recruiter_response_rate", 0) or 0)

    if open_to_work:
        score += 14
    else:
        score -= 25

    score += response_rate * 20

    avg_response = float(signals.get("avg_response_time_hours", 999) or 999)

    if avg_response <= 24:
        score += 8
    elif avg_response <= 72:
        score += 4
    elif avg_response > 150:
        score -= 8

    notice = int(signals.get("notice_period_days", 180) or 180)

    if notice <= 30:
        score += 14
    elif notice <= 60:
        score += 6
    elif notice <= 90:
        score -= 4
    elif notice >= 120:
        score -= 14

    github = float(signals.get("github_activity_score", -1) or -1)

    if github >= 75:
        score += 8
    elif github >= 40:
        score += 5
    elif github == -1:
        score -= 3

    interview_rate = float(signals.get("interview_completion_rate", 0) or 0)
    score += interview_rate * 6

    offer_rate = float(signals.get("offer_acceptance_rate", -1) or -1)

    if offer_rate >= 0:
        score += offer_rate * 4

    if signals.get("verified_email"):
        score += 1
    if signals.get("verified_phone"):
        score += 1
    if signals.get("linkedin_connected"):
        score += 1

    profile_complete = float(signals.get("profile_completeness_score", 0) or 0)

    if profile_complete >= 80:
        score += 3
    elif profile_complete < 40:
        score -= 5

    saves = int(signals.get("saved_by_recruiters_30d", 0) or 0)

    if saves >= 10:
        score += 3
    elif saves >= 5:
        score += 1

    return score


def location_score(candidate):
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    location = safe_lower(profile.get("location", ""))
    country = safe_lower(profile.get("country", ""))
    preferred_work_mode = signals.get("preferred_work_mode", "")

    score = 0

    if country == "india":
        score += 10
    else:
        score -= 15

    if any(city in location for city in GOOD_LOCATIONS):
        score += 14

    if signals.get("willing_to_relocate"):
        score += 10

    if preferred_work_mode in ["hybrid", "flexible", "onsite"]:
        score += 3

    return score


def consistency_penalty(candidate):
    profile = candidate.get("profile", {})
    summary = safe_lower(profile.get("summary", ""))
    headline = safe_lower(profile.get("headline", ""))
    profile_years = float(profile.get("years_of_experience", 0) or 0)

    penalty = 0

    year_text = summary + " " + headline
    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)", year_text)

    for match in matches:
        mentioned_years = float(match)

        if abs(profile_years - mentioned_years) >= 4:
            penalty -= 160
            break

    expert_tiny_count = 0
    expert_count = 0

    for skill in candidate.get("skills", []):
        proficiency = skill.get("proficiency", "")
        duration = int(skill.get("duration_months", 0) or 0)

        if proficiency == "expert":
            expert_count += 1

            if duration <= 3:
                expert_tiny_count += 1

    if expert_tiny_count >= 2:
        penalty -= 50

    if expert_count >= 10 and profile_years < 4:
        penalty -= 30

    history = candidate.get("career_history", [])
    total_months = sum(int(job.get("duration_months", 0) or 0) for job in history)
    profile_months = profile_years * 12

    if total_months > 0 and profile_months > 0:
        if abs(total_months - profile_months) > 72:
            penalty -= 30

    current_title = safe_lower(profile.get("current_title", ""))
    text = collect_text(candidate)

    if any(title in current_title for title in BAD_TITLES):
        ai_keyword_count = sum(1 for term in GOOD_TERMS if term in text)

        if ai_keyword_count >= 8:
            penalty -= 60

    return penalty


def final_fit_penalty(candidate):
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    penalty = 0

    years = float(profile.get("years_of_experience", 0) or 0)
    summary = safe_lower(profile.get("summary", ""))
    headline = safe_lower(profile.get("headline", ""))
    country = safe_lower(profile.get("country", ""))

    open_to_work = signals.get("open_to_work_flag")
    response_rate = float(signals.get("recruiter_response_rate", 0) or 0)
    willing_to_relocate = signals.get("willing_to_relocate")

    year_text = summary + " " + headline
    mentioned_years = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)", year_text)

    for y in mentioned_years:
        y = float(y)

        if abs(years - y) >= 4:
            penalty -= 220
            break

    # JD is strongest for 5-9 years. Very senior candidates can still be valid,
    # but they should not dominate unless all other signals are excellent.
    if years > 14:
        penalty -= 130
    elif years > 11:
        penalty -= 45

    # Strong availability penalty.
    # A technically strong candidate who is not open and barely replies is risky.
    if not open_to_work and response_rate < 0.2:
        penalty -= 220
    elif not open_to_work and response_rate < 0.4:
        penalty -= 120
    elif not open_to_work:
        penalty -= 70

    if response_rate < 0.15:
        penalty -= 80
    elif response_rate < 0.3:
        penalty -= 40

    # Role is India hybrid, Pune/Noida preferred.
    # Non-India without relocation should not be top-ranked.
    if country != "india" and not willing_to_relocate:
        penalty -= 280
    elif country != "india":
        penalty -= 120

    notice = int(signals.get("notice_period_days", 180) or 180)

    # Long notice is a concern, but not an automatic reject.
    if notice >= 120:
        penalty -= 45
    elif notice >= 90:
        penalty -= 22

    return penalty

def score_candidate(candidate):
    profile = candidate.get("profile", {})
    text = collect_text(candidate)

    score = 0
    score += experience_score(profile.get("years_of_experience"))
    score += title_score(candidate)
    score += text_score(text)
    score += skills_score(candidate)
    score += career_score(candidate)
    score += behavior_score(candidate)
    score += location_score(candidate)
    score += consistency_penalty(candidate)
    score += final_fit_penalty(candidate)

    return round(score, 4)


def get_relevant_skills(candidate):
    skills = []

    for skill in candidate.get("skills", []):
        name = skill.get("name", "")
        low = safe_lower(name)

        if any(core in low for core in CORE_SKILLS):
            skills.append(name)

    return skills[:4]


def get_best_career_evidence(candidate):
    best = []

    for job in candidate.get("career_history", []):
        title = job.get("title", "")
        company = job.get("company", "")
        desc = safe_lower(job.get("description", ""))

        if any(x in desc for x in [
            "ranking",
            "retrieval",
            "semantic search",
            "recommendation",
            "learning-to-rank",
            "learning to rank",
            "candidate-jd",
            "rag-based ranking"
        ]):
            best.append(f"{title} at {company}")

    return best[:2]


def make_reason(candidate):
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    title = profile.get("current_title", "Candidate")
    years = profile.get("years_of_experience", "unknown")
    location = profile.get("location", "unknown location")
    response = float(signals.get("recruiter_response_rate", 0) or 0)
    notice = signals.get("notice_period_days", "unknown")
    open_to_work = signals.get("open_to_work_flag")

    skills = get_relevant_skills(candidate)
    career_evidence = get_best_career_evidence(candidate)

    if skills:
        skill_text = ", ".join(skills)
    else:
        skill_text = "limited direct retrieval/ranking skills"

    if career_evidence:
        career_text = "Career evidence includes " + " and ".join(career_evidence)
    else:
        career_text = "Career evidence is more adjacent than directly search/ranking focused"

    availability = "open to work" if open_to_work else "not marked open to work"

    return (
        f"{title} with {years} years in {location}; key relevant skills include {skill_text}. "
        f"{career_text}; {availability}, response rate {response:.2f}, notice period {notice} days."
    )


def main():
    scored = []

    for candidate in load_candidates(CANDIDATES_FILE):
        score = score_candidate(candidate)
        scored.append((score, candidate["candidate_id"], candidate))

    scored.sort(key=lambda x: (-x[0], x[1]))
    top_100 = scored[:100]

    with open(OUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank, (score, candidate_id, candidate) in enumerate(top_100, start=1):
            writer.writerow([
                candidate_id,
                rank,
                score,
                make_reason(candidate)
            ])

    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
