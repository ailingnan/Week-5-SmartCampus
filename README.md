# Week-5-SmartCampus
# HappyGroup: Smart Campus Digital Twin
### Trust-Aware Multimodal GenAI for UMKC Information & Decision Support

---

## 1. System Workflow

The **HappyGroup** Smart Campus system is a production-grade data science pipeline designed to transform authoritative campus documents into a trust-aware digital twin for decision support.

- **Data Ingestion & Cleaning:** Raw PDFs (e.g., UMKC Jeanne Clery Act Reports) are processed via `01_extract_chunk.py`. The script cleans null bytes (`\x00`) and generates 1,200-character segments with 200-character overlaps to maintain semantic flow.
- **Cloud Warehousing:** Data is migrated to **Snowflake** using a staging-to-production pattern (Database: `TRAINING_DB`, Schema: `UMKC_RAG`).
- **Feature Engineering:** SQL-based and Python-based transformations automatically categorize text and calculate metadata — including keyword density and chunk length — to prepare high-quality grounding data.
- **LLM Generation:** Retrieved document chunks are passed to **Groq LLaMA** as grounding context, enabling natural language answers rooted in official UMKC policy.
- **Evaluation & Retrieval:** An optimized SQL layer performs ranked searches, while a dedicated Python evaluation module (`evaluator.py`) logs retrieval quality and latency back to Snowflake.

---

## 2. Architecture & Evaluation Layer

Our system follows a 4-tier modular architecture designed for high reliability and trust calibration.

```
┌─────────────────────────────────────┐
│          SOURCE LAYER               │
│  Local /data — UMKC PDFs & CSVs    │
└────────────────┬────────────────────┘
                 │ ETL (Python)
┌────────────────▼────────────────────┐
│        PROCESSING LAYER             │
│  01_extract_chunk.py  →  chunks.csv │
│  scheduler.py  →  automated ingest  │
│  feature_store.py  →  keyword feats │
└────────────────┬────────────────────┘
                 │ RSA Auth
┌────────────────▼────────────────────┐
│         STORAGE LAYER (Snowflake)   │
│  DOC_CHUNKS_RAW      (staging)      │
│  DOC_CHUNKS_FEATURED (production)   │
│  FEATURE_STORE       (versioned)    │
│  EVAL_METRICS        (performance)  │
│  INGEST_LOG          (lineage)      │
└────────────────┬────────────────────┘
                 │ Streamlit
┌────────────────▼────────────────────┐
│       APPLICATION LAYER             │
│  app.py — PolicyPulse Dashboard     │
│  🔍 Search + AI Answer (Groq LLaMA) │
│  📈 Analytics Dashboard             │
│  📊 Evaluation Comparison           │
│  🔮 What-if Simulation              │
│  📥 Data Ingestion                  │
│  🔧 Pipeline Monitoring             │
└─────────────────────────────────────┘
```

**Key Snowflake Tables:**

| Table | Purpose |
|-------|---------|
| `DOC_CHUNKS_RAW` | Initial staging of extracted text |
| `DOC_CHUNKS_FEATURED` | Production table with engineered text features |
| `FEATURE_STORE` | Versioned keyword feature store per query run |
| `EVAL_METRICS` | Automated retrieval performance logging |
| `INGEST_LOG` | File-level ingestion lineage and deduplication |

**Monitoring:** `pipeline_logs.csv` tracks every ingestion and LLM generation run with high-resolution timestamps, success/failure status, row counts, and latency.

---

## 3. Implemented Extensions (Team of 3)

As a three-member team, we implemented **six technical extensions** beyond the core requirements, each owned by a team member.

### Extension 1 — Automated Feature-Engineering Pipeline *(Ailing Nan)*
- **Category:** Data / Feature Extension
- **Implementation:** `feature_store.py` + `04_feature_engineering.sql`
- **Description:** Automatically extracts keyword features from every user query, filters stopwords, and writes versioned feature records (keyword list, keyword count, TopK setting) to the Snowflake `FEATURE_STORE` table. Supports version labels (v1/v2/v3) for longitudinal comparison of feature distributions.

### Extension 2 — System Performance & Evaluation Logging *(Lyza Iamrache)*
- **Category:** System / Application Extension
- **Implementation:** `evaluator.py` + `pipeline_logs.csv`
- **Description:** A dedicated logging layer records the semantic score, latency, and row count of every retrieval and LLM generation run into Snowflake (`EVAL_METRICS`) and local CSV. Enables real-time monitoring and post-hoc performance auditing.

### Extension 3 — Query Performance Optimization *(Gia Huynh)*
- **Category:** System / Application Extension
- **Implementation:** `05_retrieval_queries.sql` + `@st.cache_data` in `app.py`
- **Description:** Retrieval is optimized through ranked keyword-density scoring in SQL, combined with a 120-second Streamlit result cache that eliminates redundant Snowflake round-trips. Prioritizes high-density sections to reduce AI hallucinations.

### Extension 4 — Evaluation Metrics Comparison Dashboard *(Gia Huynh)*
- **Category:** Model / Decision Extension
- **Implementation:** Tab 3 in `app.py` + `evaluator.py`
- **Description:** An interactive dashboard aggregates `EVAL_METRICS` by version, surfacing average score, mean latency, and total runs as bar charts. Automatically highlights the best-performing version.

### Extension 5 — What-if Scenario Simulation Module *(Ailing Nan)*
- **Category:** Model / Decision Extension
- **Implementation:** Tab 4 in `app.py` (`run_whatif()`)
- **Description:** Users enter multiple query phrasings and the system runs all scenarios in parallel, returning a side-by-side comparison of chunks returned, average score, and latency. Automatically identifies the optimal query formulation.

### Extension 6 — Automated Scheduled Data Ingestion Workflow *(Lyza Iamrache)*
- **Category:** System / Application Extension
- **Implementation:** `scheduler.py`
- **Description:** A background polling worker scans the `ingest_inbox/` directory, hashes each file to prevent duplicate ingestion, and appends new CSV datasets to `DOC_CHUNKS_FEATURED`. Can be run continuously with a configurable interval (`SCHEDULER_INTERVAL_SEC`).

---

## 4. Repository Structure

```
Week-5-SmartCampus/
├── README.md
├── CONTRIBUTIONS.md
├── pipeline_logs.csv
├── requirements.txt
├── .env.example
│
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_create_tables.sql
│   ├── 03_create_staging_tables.sql
│   ├── 04_feature_engineering.sql
│   └── 05_retrieval_queries.sql
│
├── ingestion/
│   └── scheduler.py
│
├── feature_engineering/
│   └── feature_store.py
│
├── modeling/
│   └── evaluator.py
│
├── app/
│   └── app.py
│
└── architecture/
    └── architecture_diagram.png
```

---

## 5. Setup & Reproducibility

### Prerequisites
- Python 3.10+
- Snowflake Account with RSA Key Authentication configured
- Groq API Key (free at [console.groq.com](https://console.groq.com))

```bash
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=TRAINING_DB
SNOWFLAKE_SCHEMA=UMKC_RAG
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
SCHEDULER_INTERVAL_SEC=60
```

### Execution Steps

1. **Prepare Data:** Place PDF reports into the `/data` folder.

2. **Run Ingestion:**
```bash
python ingestion/01_extract_chunk.py
```

3. **Deploy Snowflake Schema:** Run SQL scripts in order:
```
sql/01_create_schema.sql
sql/02_create_tables.sql
sql/03_create_staging_tables.sql
sql/04_feature_engineering.sql
sql/05_retrieval_queries.sql
```

4. **Launch Application:**
```bash
streamlit run app/app.py
```

5. **Run Evaluation Module:**
```bash
python modeling/evaluator.py
```

6. **(Optional) Start Scheduled Ingestion:**
```bash
python ingestion/scheduler.py
```

---

## 6. Demo Video

[▶ Watch Demo on Google Drive](https://drive.google.com/file/d/12sX22TeGd3j1BOOBwKp3kaGvAJtkJVeo/view?usp=sharing)

---

*HappyGroup · UMKC Data Science · 2025*
