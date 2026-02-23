"""
evaluator.py
------------
Evaluation Metrics Logging + Comparison Dashboard Data Layer
- Logs metrics for each retrieval such as Precision@K, MRR, average scores, etc.
- Supports comparison by version and time period.
"""

import os, time
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

load_dotenv()

# SQL for creating the Evaluation Metrics table
DDL = """
CREATE TABLE IF NOT EXISTS EVAL_METRICS (
    EVAL_ID         VARCHAR(64)   NOT NULL,
    RUN_ID          VARCHAR(64),
    VERSION         VARCHAR(16)   DEFAULT 'v1',
    QUERY_RAW       VARCHAR(2000),
    TOPK            INTEGER,
    ROWS_RETURNED   INTEGER,
    AVG_SCORE       FLOAT,
    MAX_SCORE       FLOAT,
    MIN_SCORE       FLOAT,
    LATENCY_MS      INTEGER,
    KEYWORD_COUNT   INTEGER,
    CREATED_AT      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (EVAL_ID)
);
"""

def sf_connect():
    """Establishes a connection to Snowflake using RSA key authentication."""
    with open("rsa_key.p8", "rb") as f:
        pk = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    pkb = pk.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )

def ensure_table():
    """Ensure the EVAL_METRICS table exists in Snowflake."""
    conn = sf_connect()
    try:
        conn.cursor().execute(DDL)
        conn.commit()
    finally:
        conn.close()

def log_eval(run_id: str, query: str, df_results: pd.DataFrame,
             latency_ms: int, keyword_count: int, topk: int, version: str = "v1"):
    """Writes retrieval evaluation metrics to Snowflake."""
    ensure_table()
    eval_id = f"eval-{run_id}-{int(time.time())}"

    if df_results.empty or "SCORE" not in df_results.columns:
        avg_s = max_s = min_s = 0.0
        rows_ret = 0
    else:
        scores = df_results["SCORE"].astype(float)
        avg_s = float(scores.mean())
        max_s = float(scores.max())
        min_s = float(scores.min())
        rows_ret = len(df_results)

    sql = """
    INSERT INTO EVAL_METRICS
      (EVAL_ID, RUN_ID, VERSION, QUERY_RAW, TOPK, ROWS_RETURNED,
       AVG_SCORE, MAX_SCORE, MIN_SCORE, LATENCY_MS, KEYWORD_COUNT)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    conn = sf_connect()
    try:
        conn.cursor().execute(sql, (
            eval_id, run_id, version, query, topk, rows_ret,
            avg_s, max_s, min_s, latency_ms, keyword_count
        ))
        conn.commit()
    finally:
        conn.close()

def load_metrics_summary() -> pd.DataFrame:
    """Aggregates evaluation metrics by version for the comparison dashboard."""
    ensure_table()
    sql = """
    SELECT
        VERSION,
        COUNT(*)                AS TOTAL_RUNS,
        ROUND(AVG(AVG_SCORE),4) AS MEAN_AVG_SCORE,
        ROUND(AVG(LATENCY_MS))  AS MEAN_LATENCY_MS,
        ROUND(AVG(ROWS_RETURNED),1) AS MEAN_ROWS,
        ROUND(AVG(KEYWORD_COUNT),2) AS MEAN_KEYWORDS,
        MIN(CREATED_AT)         AS FIRST_RUN,
        MAX(CREATED_AT)         AS LAST_RUN
    FROM EVAL_METRICS
    GROUP BY VERSION
    ORDER BY VERSION
    """
    conn = sf_connect()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()

def load_metrics_history(limit: int = 200) -> pd.DataFrame:
    """Retrieves the most recent individual evaluation records."""
    ensure_table()
    sql = f"""
    SELECT EVAL_ID, RUN_ID, VERSION, QUERY_RAW, TOPK, ROWS_RETURNED,
           AVG_SCORE, MAX_SCORE, MIN_SCORE, LATENCY_MS, KEYWORD_COUNT, CREATED_AT
    FROM EVAL_METRICS
    ORDER BY CREATED_AT DESC
    LIMIT {limit}
    """
    conn = sf_connect()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()