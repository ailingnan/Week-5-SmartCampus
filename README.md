# Week-5-SmartCampus
# HappyGroup: Smart Campus Digital Twin
### Trust-Aware Multimodal GenAI for UMKC Information & Decision Support

## 1. System Workflow
The **HappyGroup** Smart Campus system is a production-grade data science pipeline designed to transform authoritative campus documents into a trust-aware digital twin for decision support.



* **Data Ingestion & Cleaning:** Raw PDFs (e.g., UMKC Jeanne Clery Act Reports) are processed via `01_extract_chunk.py`. The script cleans null bytes (`\x00`) and generates 1200-character segments with 200-character overlaps to maintain semantic flow.
* **Cloud Warehousing:** Data is migrated to **Snowflake** using a staging-to-production pattern (Database: `TRAINING_DB`, Schema: `UMKC_RAG`).
* **Feature Engineering:** SQL-based transformations categorize text and calculate metadata, such as keyword density and chunk length, to prepare the grounding data.
* **Evaluation & Retrieval:** An optimized SQL layer performs ranked searches, while a dedicated Python evaluation module (`evaluator.py`) logs retrieval quality and latency back to Snowflake.

---

## 2. Architecture & Evaluation Layer
Our system follows a 4-tier modular architecture designed for high reliability and trust calibration.



* **Source Layer:** Local `/data` directory containing authoritative UMKC artifacts (PDFs).
* **Processing Layer (Python):** Handles ETL logic and creates the structured `chunks.csv`.
* **Storage Layer (Snowflake):** * `DOC_CHUNKS_RAW`: Initial staging of extracted text.
    * `DOC_CHUNKS_FEATURED`: Production table with engineered text features.
    * `EVAL_METRICS`: Automated logging of system performance metrics via RSA-key authentication.
* **Monitoring Layer (`pipeline_logs.csv`):** * Tracks every ingestion run with high-resolution timestamps.
    * Captures success/failure status and record counts to ensure data lineage.

---

## 3. Implemented Extensions (Team of 3)
As a three-member team, we implemented three technical extensions beyond the core requirements:

### Extension 1: Automated Feature-Engineering Pipeline
* **Category:** Data / Feature Extension  
* **Implementation:** `04_feature_engineering.sql`. This script automatically processes raw text to generate metadata and quality filters, ensuring only high-density information is used for grounding.

### Extension 2: System Performance & Evaluation Logging
* **Category:** System / Application Extension  
* **Implementation:** Integrated via `evaluator.py`. We developed a dedicated logging layer that records the semantic "score" and `LATENCY_MS` of every retrieval run into Snowflake for real-time monitoring.



### Extension 3: Query Performance Optimization
* **Category:** System / Application Extension  
* **Implementation:** `05_retrieval_queries.sql`. We optimized retrieval using ranked keyword density searches. This prioritizes relevant sections (like "Evacuation Procedures") to reduce AI hallucinations.

---

## 4. Setup & Reproducibility

### Prerequisites
* Python 
* Snowflake Account Access (RSA Key Authentication)
* Required Libraries: `pip install -r requirements.txt`

### Execution Steps
1.  **Prepare Data:** Create a `/data` folder and place your PDF reports (e.g., `2025ccfsrumkcpolice.pdf`) inside.
2.  **Run Ingestion:** ```bash
    python 01_extract_chunk.py
    ```
3.  **Deploy Snowflake Database:** Run SQL scripts `01_create_schema.sql` through `05_retrieval_queries.sql` in sequence.
4.  **Run Evaluation:** Execute `evaluator.py` to verify retrieval scores and log performance to the cloud.

---

---

## 6. Demo Video
https://drive.google.com/file/d/12sX22TeGd3j1BOOBwKp3kaGvAJtkJVeo/view?usp=sharing
***
