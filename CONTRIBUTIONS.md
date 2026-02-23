# Team Contributions: HappyGroup
### Project: Smart Campus Digital Twin (UMKC)

This document outlines the specific responsibilities and technical contributions of each member of **HappyGroup** for the Smart Campus Capstone project.

---

## 1. Team Roles & Ownership Overview

| Member | Primary Role | Technical Ownership |
| :--- | :--- | :--- |
| **Ailing Nan** | Project Lead | Snowflake Architecture, Database Schema, RSA Authentication |
| **Lyza Iamrache** | Systems Lead | Python ETL Pipeline, PDF Extraction, Automated Logging |
| **Gia Huynh** | Evaluation Lead | Feature Engineering, Retrieval Optimization, Metrics Logic |

---

## 2. Detailed Member Contributions

### **Ailing Nan (Project Lead)**
* **Database Architecture:** Designed and implemented the Snowflake environment using a multi-schema approach.
* **Security & Auth:** Configured the RSA Key Pair authentication (using `key.sql`) to ensure secure programmatic access from Python to Snowflake.
* **Staging Logic:** Developed the staging workflow (`01_create_schema.sql` through `03_create_staging_tables.sql`) to manage the transition from raw CSV data to relational tables.
* **Project Governance:** Managed version control (GitHub) and coordinated the integration of SQL scripts with Python modules.



### **Lyza Iamrache (Systems Lead)**
* **Python ETL Pipeline:** Developed `01_extract_chunk.py` to handle complex PDF extraction, including cleaning null bytes and specialized character encoding.
* **Chunking Strategy:** Implemented the 1200-character chunking logic with a 200-character overlap to ensure semantic continuity for the RAG system.
* **Monitoring System:** Created the automated logging extension that generates `pipeline_logs.csv`, tracking every ingestion run's timestamp, record count, and success status.
* **Resource Management:** Managed the `requirements.txt` and environment configurations for the team.



### **Gia Huynh (Evaluation Lead)**
* **Feature Engineering:** Developed `04_feature_engineering.sql` to transform raw text chunks into high-quality features, including metadata generation and noise filtering.
* **Retrieval Optimization:** Designed `05_retrieval_queries.sql` using ranked keyword density (ILIKE) to improve the accuracy of the "Digital Twin" response grounding.
* **Performance Metrics:** Built the `evaluator.py` logic to calculate `AVG_SCORE` and `LATENCY_MS`, allowing the team to measure the reliability of the system.
* **Data Validation:** Conducted the final validation of retrieved chunks against the original UMKC Clery Act Report.

---

## 3. Collaborative Efforts
Beyond individual tasks, the team collaborated on the following:
* **Architecture Design:** Jointly developed the 4-tier system architecture to ensure the Python and Snowflake layers were perfectly synced.
* **Demo Production:** Collaboratively recorded and edited the 3-minute project demo video.
* **Troubleshooting:** Worked together to resolve pathing issues and Snowflake connector errors during the integration phase.

---
