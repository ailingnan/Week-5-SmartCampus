# Team Contributions: HappyGroup
### Project: Smart Campus Digital Twin (UMKC)

This document clearly outlines the individual responsibilities, technical ownership, and collaborative milestones achieved by the members of **HappyGroup**.

---

## 1. Team Roles & Technical Ownership

| Member | Primary Role | Technical Ownership | Extension Owned |
| :--- | :--- | :--- | :--- |
| **Ailing Nan** | Project Lead | Python ETL Pipeline, Feature Engineering, RSA Security, Database Governance | Extension 1 + 5 |
| **Lyza Iamrache** | Systems Lead | Snowflake Architecture, Automated Ingestion, Logging & Monitoring | Extension 2 + 6 |
| **Gia Huynh** | Evaluation & UI Lead | Streamlit Application, Query Optimization, Evaluation Dashboard | Extension 3 + 4 |

---

## 2. Detailed Member Contributions

### Ailing Nan — Project Lead

**Extension 1 (Owner): Automated Feature-Engineering Pipeline**
- Designed and implemented `feature_store.py`, which automatically extracts keyword features from every user query, filters stopwords, and writes versioned feature records to the Snowflake `FEATURE_STORE` table.
- Authored `04_feature_engineering.sql` to compute keyword density and text quality metadata at the SQL layer.
- Introduced version labeling (v1/v2/v3) to enable longitudinal comparison of feature distributions across system iterations.

**Extension 5 (Owner): What-if Scenario Simulation Module**
- Designed and implemented the `run_whatif()` function and Tab 4 in `app.py`.
- Enables users to test multiple query phrasings in parallel and compare chunks returned, average score, and latency side by side.
- Automatically surfaces the optimal query formulation based on retrieval score.

**Core Contributions:**
- Designed the core relational schema (`UMKC_RAG`) and established the staging-to-featured data flow.
- Implemented RSA Key Pair authentication (`rsa_key.p8`) used across all Python modules for secure, passwordless cloud communication.
- Authored foundational DDL scripts (`01_create_schema.sql`, `02_create_tables.sql`) and managed environment configuration (`.env`).
- Ensured all data chunks were traceable back to source documents via metadata linking.

---

### Lyza Iamrache — Systems Lead

**Extension 2 (Owner): System Performance & Evaluation Logging**
- Built the end-to-end logging layer in `evaluator.py` that records semantic score, latency, and row count for every retrieval and LLM generation run into Snowflake (`EVAL_METRICS`) and `pipeline_logs.csv`.
- Enabled real-time monitoring and post-hoc performance auditing across all pipeline stages.

**Extension 6 (Owner): Automated Scheduled Data Ingestion Workflow**
- Developed `scheduler.py`, a background polling worker that scans the `ingest_inbox/` directory, MD5-hashes each file to prevent duplicate ingestion, and appends new datasets to `DOC_CHUNKS_FEATURED`.
- Implemented the Inbox/Done file-movement pattern to ensure clean, auditable ingestion state.
- Exposed a configurable polling interval via `SCHEDULER_INTERVAL_SEC` environment variable.

**Core Contributions:**
- Developed the PDF extraction logic and the automated ingestion pipeline (`01_extract_chunk.py`).
- Optimized the chunking strategy (1,200-character windows with 200-character overlap) to balance context retention with retrieval speed.
- Designed the `INGEST_LOG` Snowflake table for file-level data lineage and deduplication tracking.

---

### Gia Huynh — Evaluation & UI Lead

**Extension 3 (Owner): Query Performance Optimization**
- Authored `05_retrieval_queries.sql` implementing ranked keyword-density scoring to prioritize high-relevance document sections and reduce AI hallucinations.
- Integrated `@st.cache_data` (120-second TTL) in `app.py` to eliminate redundant Snowflake round-trips for repeated queries.

**Extension 4 (Owner): Evaluation Metrics Comparison Dashboard**
- Built Tab 3 of `app.py`, an interactive dashboard that aggregates `EVAL_METRICS` by version and renders average score, mean latency, and total runs as bar charts.
- Implemented the best-version metric card that automatically highlights the top-performing pipeline version.

**Core Contributions:**
- Built the full **UMKC PolicyPulse** Streamlit dashboard (`app.py`) with six integrated tabs: Search + AI Answer, Analytics, Evaluation Comparison, What-if Simulation, Data Ingestion, and Pipeline Monitoring.
- Integrated Groq LLaMA API into the retrieval pipeline to generate grounded natural language answers from retrieved document chunks.
- Developed `feature_store.py` display components and version comparison visualizations in the Analytics Dashboard (Tab 2).

---

## 3. Collaborative Milestones

- **Architecture Design:** The team jointly designed the 4-tier system (Source → Processing → Storage → Application) to ensure seamless communication between the Streamlit UI and Snowflake.
- **RAG Pipeline Integration:** Collaborated on connecting the Snowflake retrieval layer to the Groq LLaMA generation layer, establishing the full Retrieval-Augmented Generation workflow.
- **Evaluation Strategy:** Collaboratively defined retrieval scoring criteria and "faithfulness" behaviors to ensure the system prioritizes grounded, document-backed responses over fluent but unverified answers.
- **Project Demo:** Jointly produced the final technical demo illustrating the full lifecycle — from raw PDF ingestion to a grounded LLM response.

---

*HappyGroup · UMKC Data Science · 2025*
