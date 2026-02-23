# Team Contributions: HappyGroup
### Project: Smart Campus Digital Twin (UMKC)

This document clearly outlines the individual responsibilities, technical ownership, and collaborative milestones achieved by the members of **HappyGroup**.

---

## 1. Team Roles & Technical Ownership

| Member | Primary Role | Technical Ownership |
| :--- | :--- | :--- |
| **Ailing Nan** | Project Lead | Snowflake Architecture, RSA Security, Database Governance |
| **Lyza Iamrache** | Systems Lead | Python ETL Pipeline, Scheduled Ingestion, Logging & Monitoring |
| **Gia Huynh** | Evaluation & UI Lead | Streamlit Application, Feature Store, RAG Evaluation Metrics |

---

## 2. Detailed Member Contributions

### **Ailing Nan (Project Lead)**
* **Snowflake Infrastructure:** Designed the core relational schema (`UMKC_RAG`) and established the staging-to-featured data flow.
* **Security & Authentication:** Implemented the RSA Key Pair authentication mechanism (`rsa_key.p8`) used across all Python modules to ensure secure, passwordless cloud communication.
* **Database Logic:** Authored the fundamental DDL scripts (`01_create_schema.sql`, `02_create_tables.sql`) and managed the environment configuration (`.env`).
* **Governance:** Ensured all data chunks were traceable back to their source documents via metadata linking.



### **Lyza Iamrache (Systems Lead)**
* **Inference & Ingestion Pipeline:** Developed the PDF extraction logic and the automated ingestion worker (`scheduler.py`).
* **Scheduled Workflows:** Designed the "Inbox/Done" polling system that automatically detects, hashes, and uploads new CSV datasets to Snowflake.
* **Pipeline Monitoring:** Created the comprehensive logging extension (`pipeline_logs.csv`) which tracks success rates, row counts, and latency across the ETL and LLM generation stages.
* **System Reliability:** Optimized the chunking strategy (1200-character windows) to balance context retention with retrieval speed.



### **Gia Huynh (Evaluation & UI Lead)**
* **Interface Development:** Built the **UMKC PolicyPulse** dashboard (`app.py`), integrating real-time chat with complex analytics and monitoring tabs.
* **Feature Store & Versioning:** Developed `feature_store.py` to log and version-control keyword distributions, enabling side-by-side comparison of different system iterations.
* **Evaluation Framework:** Implemented the `evaluator.py` module to capture retrieval metrics (AVG/MAX/MIN scores) and grounding faithfulness.
* **Simulation Logic:** Designed the "What-if Simulation" tab to allow users to test the digital twin's reasoning across hypothetical campus scenarios.



---

## 3. Collaborative Milestones
* **Architecture Integration:** The team jointly designed the 4-tier system (Source, Processing, Storage, Application) to ensure seamless communication between the Streamlit UI and Snowflake.
* **Evaluation Strategy:** Collaborative definition of "Faithfulness" and "Refusal" behaviors to ensure the system prioritizes trust over fluency.
* **Project Demo:** Jointly produced the final technical demo illustrating the full lifecycle from raw PDF ingestion to a grounded LLM response.

---

