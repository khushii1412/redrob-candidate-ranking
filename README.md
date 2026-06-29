# Redrob Candidate Ranking System

Deterministic candidate ranking solution for the Redrob India.Runs Intelligent Candidate Discovery challenge.

## Problem Statement

The task is to rank the top 100 candidates for a Senior AI Engineer role from a large candidate pool. The system goes beyond simple keyword matching and identifies candidates with real-world evidence in search, retrieval, ranking, recommendation systems, embeddings, LLMs, RAG, and production ML systems.

## Solution Overview

This project implements a deterministic, rule-based candidate intelligence ranker. It scores candidates using structured profile data, skills, career history, Redrob behavioral signals, location fit, availability, and suspicious-profile validation.

The final output is a valid submission CSV with the required columns:

candidate_id,rank,score,reasoning

## Key Signals Used

- Senior AI Engineer JD fit
- Search, retrieval, ranking, recommendation, and vector search experience
- Embeddings, FAISS, Pinecone, Qdrant, Weaviate, Elasticsearch, OpenSearch
- NLP, RAG, LLMs, fine-tuning, and candidate-JD matching
- Production career evidence
- Evaluation metrics such as NDCG, MRR, MAP, A/B testing, and offline-online evaluation
- Open-to-work status
- Recruiter response rate
- Notice period
- GitHub activity
- Location and relocation fit
- Suspicious profile and honeypot-style consistency checks

## Ranking Methodology

Each candidate receives a composite score from multiple components:

1. Experience fit  
Rewards candidates close to the 5-9 years target range.

2. Title fit  
Rewards relevant roles such as Senior AI Engineer, Lead AI Engineer, Senior ML Engineer, Search Engineer, Senior NLP Engineer, and Recommendation Systems Engineer.

3. Skill fit  
Scores relevant technical skills and skill depth.

4. Career evidence  
Strongly rewards actual production work in search, retrieval, ranking, recommendation systems, candidate-JD matching, hybrid retrieval, and evaluation pipelines.

5. Behavioral signals  
Uses open-to-work status, response rate, notice period, GitHub activity, profile completeness, and recruiter engagement signals.

6. Location fit  
Rewards India-based candidates, especially Pune, Noida, Delhi NCR, Mumbai, Hyderabad, and Bangalore, plus relocation willingness.

7. Validation penalties  
Penalizes unrelated roles, experience mismatch, suspicious expert-skill claims, very low response rate, non-India no-relocation profiles, and keyword-stuffed non-technical profiles.

## Explainability

The reasoning column is generated from candidate facts only. It summarizes title, experience, location, relevant skills, career evidence, availability, response rate, and notice period.

No hosted LLM or external API is used during ranking.

## Reproducibility

Run:

python3 rank.py
python3 validate_submission.py submission.csv
wc -l submission.csv

Expected output:

Wrote submission.csv
Submission is valid.
101 submission.csv

## Constraints

- No hosted LLM during ranking
- No network calls during ranking
- CPU-only
- No external Python dependencies
- Uses only Python standard libraries
- Fast deterministic execution
