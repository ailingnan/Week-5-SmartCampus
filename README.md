# Week-5-SmartCampus
# HappyGroup: Smart Campus Digital Twin
### Trust-Aware Multimodal GenAI for UMKC Information & Decision Support

## 1. System Workflow
The **HappyGroup** Smart Campus system is a production-grade data science pipeline designed to transform authoritative campus documents into a trust-aware digital twin for decision support.



* **Data Ingestion & Cleaning:** Raw PDFs (e.g., UMKC Jeanne Clery Act Reports) are processed via `01_extract_chunk.py`. The script handles text extraction, cleans null bytes (`\x00`), and generates 1200-character segments with 200-character overlaps.
* **Cloud Warehousing:** Data is migrated to **Snowflake** using a staging-to-production pattern (Database: `TRAINING_DB`, Schema: `UMKC_RAG`).
* **Feature Engineering:** SQL-based transformations categorize text and calculate metadata, such as keyword density and chunk length, to prepare the grounding data.
* **Evaluation & Retrieval:** An optimized SQL layer performs ranked searches, while a dedicated Python evaluation module (`evaluator.py`) logs retrieval quality and latency back to Snowflake.

---

## 2. Architecture & Evaluation Layer
Our system follows a 4-tier modular architecture designed for high reliability and trust calibration.



* **Source Layer:** Local `/data` directory containing authoritative UMKC artifacts.
* **Processing Layer (Python):** Handles ETL logic and creates the structured `chunks.csv`.
* **Storage Layer (Snowflake):** * `DOC_CHUNKS_RAW`: Initial staging of extracted text.
    * `DOC_CHUNKS_FEATURED`: Production table with engineered text features.
    * `EVAL_METRICS`: Automated logging of system performance.
* **Evaluation Layer (`evaluator.py`):** * Tracks `AVG_SCORE`, `MAX_SCORE`, and `MIN_SCORE` for retrieval relevance.
    * Monitors `LATENCY_MS` to ensure production-level responsiveness.
    * Supports `VERSION` tracking to compare pipeline iterations (e.g., v1 vs v2).

---

## 3. Implemented Extensions (Team of 3)
As a three-member team, we implemented three technical extensions beyond the core requirements:

### Extension 1: Automated Feature-Engineering Pipeline
* **Category:** Data / Feature Extension  
* **Implementation:** Found in `04_feature_engineering.sql`. This script automatically processes raw text to generate metadata and quality filters, ensuring only high-density information is used for grounding.

### Extension 2: System Performance & Evaluation Logging
* **Category:** System / Application Extension  
* **Implementation:** Integrated via `evaluator.py`. We developed a dedicated logging layer that records the semantic "score" of every retrieval run into Snowflake, allowing for real-time monitoring of the AI's accuracy.



### Extension 3: Query Performance Optimization
* **Category:** System / Application Extension  
* **Implementation:** Found in `05_retrieval_queries.sql`. We optimized retrieval using ranked keyword density searches. This prioritizes the most relevant sections (like "Evacuation Procedures") to reduce "hallucinations" and improve response speed.

---

## 4. Setup & Reproducibility

### Prerequisites
* Python 3.8+
* Snowflake Account Access (with RSA Key Authentication)
* Required Libraries: `pip install pypdf snowflake-connector-python pandas`

### Execution Steps
1.  **Prepare Data:** Place PDF reports in the `/data` folder.
2.  **Run Ingestion:** ```bash
    python 01_extract_chunk.py
    ```
3.  **Deploy Snowflake:** Run SQL scripts `01_create_schema.sql` through `05_retrieval_queries.sql` in sequence.
4.  **Run Evaluation:** Use `evaluator.py` to test retrieval logic and log metrics:
    ```python
    from evaluator import log_metrics
    # Example: log_metrics(run_id="v1", avg_score=0.85, latency=120)
    ```

---

## 5. Team Contributions (HappyGroup)
| Member | Primary Ownership | Responsibilities |
| :--- | :--- | :--- |
| **Ailing Nan** | Project Lead | Snowflake Architect, Schema Design, Staging Logic. |
| **Lyza Iamrache** | Systems Lead | Python Ingestion Pipeline, Logging Extension, PDF ETL. |
| **Gia Huynh** | Evaluation Lead | Feature Engineering SQL, Retrieval Optimization, Evaluator Logic. |

---

## 6. Demo Video
