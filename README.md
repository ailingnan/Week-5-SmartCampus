# Week-5-SmartCampus
# HappyGroup: Smart Campus Digital Twin
### Trust-Aware Multimodal GenAI for UMKC Information & Decision Support

## 1. System Workflow
The **HappyGroup** Smart Campus system is a production-grade data science pipeline designed to transform authoritative campus safety documents into a trust-aware digital twin.



* **Data Ingestion & Cleaning:** Raw PDFs (e.g., the UMKC Jeanne Clery Act Report) are processed via `01_extract_chunk.py`. The script cleans null bytes (`\x00`) and extracts text into 1200-character segments with 200-character overlaps to preserve semantic context.
* **Snowflake Cloud Warehouse:** Structured data, including metadata like `page_num` and `created_at`, is uploaded to Snowflake (Database: `TRAINING_DB`, Schema: `UMKC_RAG`).
* **Feature Engineering:** SQL-based transformations categorize text and calculate metadata (e.g., keyword density for specific sections like "Emergency Response").
* **Retrieval & Decision Support:** An optimized SQL layer acts as the system's "brain," allowing stakeholders to query the Digital Twin for specific campus information with grounding in the original documents.

---

## 2. Architecture Description
Our system is built on a 4-tier modular architecture to ensure scalability and reproducibility:

* **Source Layer:** Authoritative UMKC PDF documents (e.g., `2025ccfsrumkcpolice.pdf`) stored in the `/data` directory.
* **Processing Layer (Python):** Handles the ETL (Extract, Transform, Load) logic, chunking, and preparation of the structured `chunks.csv`.
* **Storage Layer (Snowflake):** * **Staging:** `DOC_CHUNKS_RAW` captures the initial data ingestion.
    * **Production:** `DOC_CHUNKS_FEATURED` stores high-quality, transformed data for retrieval.
* **Monitoring Layer:** A CSV-based logging system (`pipeline_logs.csv`) tracks the health, timestamps, and row counts of every ingestion run.

---

## 3. Implemented Extensions (Team of 3)
In accordance with the Capstone Sprint requirements for a 3-member team, we have implemented the following technical extensions:

### Extension 1: Automated Feature-Engineering Pipeline
* **Category:** Data / Feature Extension  
* **Implementation:** `04_feature_engineering.sql`. This script automatically processes raw text to generate metadata and categorization features. By filtering out "noise," it ensures high-density grounding data for decision support.

### Extension 2: Pipeline Monitoring & Performance Logs
* **Category:** System / Application Extension  
* **Implementation:** To ensure production reliability, we implemented a monitoring workflow via **`pipeline_logs.csv`**. This file records every script execution, tracking success/failure statuses and the volume of data ingested.



### Extension 3: Query Performance Optimization
* **Category:** System / Application Extension  
* **Implementation:** `05_retrieval_queries.sql`. We optimized retrieval using ranked search queries. This allows the system to prioritize the most relevant sections (such as "Evacuation Procedures") during a search, improving accuracy.

---

## 4. Setup & Reproducibility

### Prerequisites
* Python 3.8+
* Snowflake Account Access

### Installation
1. **Install Python Libraries:**
   ```bash
   pip install pypdf
