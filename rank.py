import csv
import json
import re
import sys

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


def has_exp_mismatch(candidate):
    profile = candidate.get("profile", {})
    years = float(profile.get("years_of_experience", 0) or 0)
    text = safe_lower(profile.get("summary", "")) + " " + safe_lower(profile.get("headline", ""))

    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)", text)

    for m in matches:
        mentioned = float(m)
        if abs(years - mentioned) >= 4:
            return True

    return False


def career_evidence_score(candidate):
    history = candidate.get("career_history", [])

    if not history:
        return -30, 0

    score = 0
    companies = [safe_lower(job.get("company", "")) for job in history if job.get("company")]

    if companies:
        service_count = 0

        for company in companies:
            if any(service in company for service in SERVICE_COMPANIES):
                service_count += 1

        if service_count == len(companies):
            score -= 20

    evidence_mentions = 0
    for job in history:
        title = safe_lower(job.get("title", ""))
        company = safe_lower(job.get("company", ""))
        description = safe_lower(job.get("description", ""))
        combined = title + " " + company + " " + description

        core_terms = [
            "ranking layer", "ranking pipeline", "learning-to-rank", "learning to rank", "re-ranking", "reranking",
            "hybrid retrieval", "semantic search", "vector search", "embedding-based search", "vector database",
            "candidate-jd matching", "candidate matching", "candidate-jd", "recommendation system", "recommendation systems", 
            "recommender system", "recommender systems", "recommendation pipeline", "search and discovery", "search & discovery",
            "built and shipped production recommendation system", "semantic search system", "bm25 + dense retrieval", "dense retrieval",
            "recruiter-facing search"
        ]
        for term in core_terms:
            if term in combined:
                score += 45
                evidence_mentions += 1

        eval_terms = [
            "ndcg", "mrr", "map", "offline evaluation", "online evaluation", "a/b test", "a/b testing", 
            "offline-online", "human relevance judgments", "evaluation framework", "relevance labeling",
            "recall@k", "offline/online evaluation", "relevance labels"
        ]
        for term in eval_terms:
            if term in combined:
                score += 35
                evidence_mentions += 1

        prod_terms = [
            "production", "deployed", "serving", "real users", "p95", "latency", "scale", "qps",
            "50m+", "30m+", "10m+", "35m+", "production deployment", "large-scale search",
            "p95 latency", "production deployment"
        ]
        for term in prod_terms:
            if term in combined:
                score += 25
                evidence_mentions += 1

        infra_terms = [
            "embedding drift", "index refresh", "index versioning", "rollback", "monitoring",
            "feature pipeline", "data pipeline", "retraining", "offline-online evaluation",
            "index refresh"
        ]
        for term in infra_terms:
            if term in combined:
                score += 15
                evidence_mentions += 1

        if any(x in combined for x in [
            "pure research",
            "academic lab",
            "research-only"
        ]):
            score -= 30

    return score, evidence_mentions


def career_evidence_count(candidate):
    count = 0
    for job in candidate.get("career_history", []):
        text = safe_lower(job.get("title", "")) + " " + safe_lower(job.get("description", ""))
        for term in GOOD_EVIDENCE_TERMS:
            if term in text:
                count += 1
    return count


def ai_skill_count(candidate):
    count = 0
    for skill in candidate.get("skills", []):
        name = safe_lower(skill.get("name", ""))
        if any(term in name for term in AI_SKILL_TERMS):
            count += 1
    return count


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

    notice_raw = signals.get("notice_period_days", 180)
    notice = 180 if notice_raw is None else int(notice_raw)

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

    notice_raw = signals.get("notice_period_days", 180)
    notice = 180 if notice_raw is None else int(notice_raw)

    # Long notice is a concern, but not an automatic reject.
    if notice >= 120:
        penalty -= 45
    elif notice >= 90:
        penalty -= 22

    return penalty

def score_candidate_internal(candidate):
    profile = candidate.get("profile", {})
    text = collect_text(candidate)

    # 1. Experience score
    exp_s = experience_score(profile.get("years_of_experience"))
    if exp_s is None:
        exp_s = 0

    # 2. Title score
    tit_s = title_score(candidate)

    # 3. Skill score
    base_skill_s = skills_score(candidate)
    text_skill_contribution = 0
    for term in GOOD_TERMS:
        if term in text:
            text_skill_contribution += 4
    for term in BAD_TERMS:
        if term in text:
            text_skill_contribution -= 7
    skill_s = base_skill_s + text_skill_contribution

    # Count AI skills using standard aligned function
    ai_skills_count = ai_skill_count(candidate)
    evidence_count_val = career_evidence_count(candidate)

    # 4. Career evidence score
    base_career_s, evidence_mentions = career_evidence_score(candidate)
    text_career_contribution = 0
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
            text_career_contribution += 13
    scale_phrases = [
        "real users", "deployed", "production", "serving",
        "50m+", "30m+", "10m+", "35m+", "8k",
        "p95", "latency", "qps"
    ]
    for phrase in scale_phrases:
        if phrase in text:
            text_career_contribution += 4
    career_s = base_career_s + text_career_contribution

    # 5. Behavior score
    beh_s = behavior_score(candidate)

    # 6. Location score
    loc_s = location_score(candidate)

    # 7. Consistency penalty
    cons_p = consistency_penalty(candidate)

    # Keyword spam detection
    keyword_spam_penalty = 0
    if ai_skills_count >= 8 and evidence_count_val <= 2:
        keyword_spam_penalty = -200

    cons_p += keyword_spam_penalty

    # 8. Final fit penalty
    fit_p = final_fit_penalty(candidate)

    total = exp_s + tit_s + skill_s + career_s + beh_s + loc_s + cons_p + fit_p

    breakdown = {
        "experience_score": exp_s,
        "title_score": tit_s,
        "skill_score": skill_s,
        "career_evidence_score": career_s,
        "behavior_score": beh_s,
        "location_score": loc_s,
        "consistency_penalty": cons_p,
        "final_fit_penalty": fit_p,
        "ai_skills_count": ai_skills_count,
        "career_evidence_mentions": evidence_count_val,
        "keyword_spam_penalty": keyword_spam_penalty
    }

    return round(total, 4), breakdown


def score_candidate(candidate):
    score, _ = score_candidate_internal(candidate)
    return score


def determine_tier(candidate, evidence_count, skill_count):
    p = candidate.get("profile", {})
    s = candidate.get("redrob_signals", {})

    title = safe_lower(p.get("current_title", ""))
    country = safe_lower(p.get("country", ""))
    years = float(p.get("years_of_experience", 0) or 0)
    open_to_work = s.get("open_to_work_flag")
    response = float(s.get("recruiter_response_rate", 0) or 0)
    willing = s.get("willing_to_relocate")

    has_bad_title = any(bad in title for bad in BAD_TITLES)
    has_exp_m = has_exp_mismatch(candidate)
    is_not_open_low_res = (not open_to_work and response < 0.3)
    is_non_india_no_reloc = (country != "india" and not willing)
    is_keyword_spam = (skill_count >= 8 and evidence_count <= 2)
    is_low_career = (evidence_count <= 2)

    if (has_bad_title or has_exp_m or is_not_open_low_res or 
        is_non_india_no_reloc or is_keyword_spam or is_low_career):
        return "D"

    # Tier A: Excellent fit
    is_tier_a = (
        5.0 <= years <= 9.0 and
        (country == "india" or willing) and
        open_to_work and
        response >= 0.50 and
        evidence_count >= 5
    )
    if is_tier_a:
        return "A"

    # Tier B: Strong fit with minor concern
    is_relevant_title = any(t in title for t in ["engineer", "developer", "scientist", "analyst", "architect"]) or "ai" in title or "ml" in title or "nlp" in title or "search" in title or "recommendation" in title
    is_tier_b = (
        is_relevant_title and
        evidence_count >= 3
    )
    if is_tier_b:
        return "B"

    # Tier C: Acceptable backup
    return "C"


def rerank_stage(scored_candidates):
    adjusted = []
    for score, cid, candidate, breakdown in scored_candidates:
        s = candidate.get("redrob_signals", {})
        notice_raw = s.get("notice_period_days", 180)
        notice = 180 if notice_raw is None else int(notice_raw)

        evidence_count = career_evidence_count(candidate)
        skill_count = ai_skill_count(candidate)

        tier = determine_tier(candidate, evidence_count, skill_count)

        tier_boost = 0
        if tier == "A":
            tier_boost = 300000
        elif tier == "B":
            tier_boost = 200000
        elif tier == "C":
            tier_boost = 100000
        else:
            tier_boost = 0

        notice_penalty = 0
        if notice >= 120 and tier in ("A", "B"):
            notice_penalty = -2500

        final_score = score + tier_boost + notice_penalty

        breakdown["final_fit_penalty"] += (tier_boost + notice_penalty)
        breakdown["tier"] = tier

        adjusted.append((round(final_score, 4), cid, candidate, breakdown))

    adjusted.sort(key=lambda x: (-x[0], x[1]))
    return adjusted


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


def get_detailed_career_evidence(candidate):
    evidence_points = []
    for job in candidate.get("career_history", []):
        desc = safe_lower(job.get("description", ""))
        title = safe_lower(job.get("title", ""))
        combined = title + " " + desc

        if "ranking pipeline" in combined or "ranking layer" in combined:
            evidence_points.append("production ranking pipeline")
        if "semantic search" in combined:
            evidence_points.append("semantic search system")
        if "hybrid retrieval" in combined:
            evidence_points.append("hybrid retrieval")
        if "recommendation system" in combined or "recommender system" in combined:
            evidence_points.append("recommendation system")
        if "rag-based ranking" in combined or "rag ranking" in combined or ("rag" in combined and "ranking" in combined):
            evidence_points.append("RAG-based ranking")
        if "ndcg" in combined or "a/b test" in combined or "evaluation" in combined:
            evidence_points.append("NDCG/A-B testing/evaluation")
        if "vector search" in combined or "bm25" in combined or "dense retrieval" in combined:
            evidence_points.append("vector search/BM25/dense retrieval")

    seen = set()
    unique_evidence = []
    for pt in evidence_points:
        if pt not in seen:
            seen.add(pt)
            unique_evidence.append(pt)

    return unique_evidence


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
    evidence_pts = get_detailed_career_evidence(candidate)

    if skills:
        skill_text = f"skills in {', '.join(skills)}"
    else:
        skill_text = "limited direct retrieval/ranking skills"

    if evidence_pts:
        evidence_text = f"Demonstrated experience with {', '.join(evidence_pts)}"
    else:
        fallback_ev = get_best_career_evidence(candidate)
        if fallback_ev:
            evidence_text = f"Adjacent search/ranking experience at {', '.join(fallback_ev)}"
        else:
            evidence_text = "Adjacent ML/software experience"

    availability = "open to work" if open_to_work else "not open to work"

    reason = f"{title} ({years} yrs, {location}) with {skill_text}. {evidence_text}. Status: {availability}, response rate {response:.0%}, notice: {notice}d."
    return reason


def main():
    debug_mode = "--debug" in sys.argv
    scored = []

    for candidate in load_candidates(CANDIDATES_FILE):
        score, breakdown = score_candidate_internal(candidate)
        scored.append((score, candidate["candidate_id"], candidate, breakdown))

    scored = rerank_stage(scored)
    top_100 = scored[:100]

    # Calculate min and max of top 100 original scores for normalization
    orig_scores = [x[0] for x in top_100]
    max_orig = orig_scores[0] if orig_scores else 1.0
    min_orig = orig_scores[-1] if orig_scores else 0.0
    range_orig = max_orig - min_orig
    target_max = 1000.0
    target_min = 850.0
    range_target = target_max - target_min

    # 1. Initial linear scaling
    norm_scores = []
    for score in orig_scores:
        if range_orig > 0:
            ns = target_min + (score - min_orig) / range_orig * range_target
        else:
            ns = target_max
        norm_scores.append(round(ns, 2))

    # 2. Adjust top-to-bottom to guarantee monotonicity and tie-break rules
    for i in range(1, len(norm_scores)):
        # Ensure it is non-increasing
        if norm_scores[i] > norm_scores[i-1]:
            norm_scores[i] = norm_scores[i-1]
        
        # If equal, check candidate_id ascending tie-break requirement
        # If candidate_id is descending (top_100[i-1][1] > top_100[i][1]), we must decrease norm_scores[i]
        if norm_scores[i] == norm_scores[i-1] and top_100[i-1][1] > top_100[i][1]:
            norm_scores[i] = round(norm_scores[i-1] - 0.01, 2)

    normalized_top_100 = []
    for rank, (score, candidate_id, candidate, breakdown) in enumerate(top_100, start=1):
        normalized_top_100.append((norm_scores[rank-1], score, candidate_id, candidate, breakdown))

    with open(OUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank, (norm_score, score, candidate_id, candidate, breakdown) in enumerate(normalized_top_100, start=1):
            writer.writerow([
                candidate_id,
                rank,
                norm_score,
                make_reason(candidate)
            ])

    print(f"Wrote {OUT_FILE}")

    if debug_mode:
        print("\n--- DEBUG BREAKDOWN (TOP 10) ---")
        for rank, (norm_score, score, candidate_id, candidate, breakdown) in enumerate(normalized_top_100[:10], start=1):
            p = candidate.get("profile", {})
            print(f"Rank {rank} | ID: {candidate_id} | Name: {p.get('anonymized_name')} | Title: {p.get('current_title')} | Tier: {breakdown['tier']} | Exported Score: {norm_score} | Raw Score: {score}")
            print(f"  exp: {breakdown['experience_score']} | title: {breakdown['title_score']} | skill: {breakdown['skill_score']} | career: {breakdown['career_evidence_score']} | behavior: {breakdown['behavior_score']} | location: {breakdown['location_score']} | consistency: {breakdown['consistency_penalty']} | fit: {breakdown['final_fit_penalty']}")
            print(f"  AI skills: {breakdown['ai_skills_count']} | career mentions: {breakdown['career_evidence_mentions']} | spam penalty: {breakdown['keyword_spam_penalty']}")
            print(f"  Reason: {make_reason(candidate)}")
            print("-" * 80)


if __name__ == "__main__":
    main()
