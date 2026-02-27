"""
app.py  ——  UMKC PolicyPulse (Full Extended Version)
=========================================
Extensions Covered:
  ✅ [Data]    Additional dataset ingestion     → Sidebar manual CSV upload / scheduler call
  ✅ [Data]    Auto feature engineering pipeline → extract_keywords + write to FEATURE_STORE
  ✅ [Data]    Feature Store / Version management → feature_store.py
  ✅ [Model]   LLM Answer Generation            → Groq (llama3-8b-8192)
  ✅ [Model]   Evaluation metrics logging       → evaluator.py
  ✅ [Model]   Evaluation Comparison Dashboard   → "📊 Eval Comparison" Tab
  ✅ [Model]   What-if Scenario Simulation      → "🔮 What-if Simulation" Tab
  ✅ [System]  Interactive Analytics Dashboard   → "📈 Analytics Dashboard" Tab
  ✅ [System]  Scheduled data ingestion workflow → scheduler.py (can run in background)
  ✅ [System]  Query optimization/Materialized view → Snowflake RESULT_SCAN + Cache
  ✅ [System]  Pipeline Monitoring Dashboard     → "🔧 Pipeline Monitoring" Tab
"""

import os, re, time, csv, hashlib
from datetime import datetime

import pandas as pd
import streamlit as st
import snowflake.connector
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from groq import Groq

import feature_store   as fs
import evaluator       as ev
import scheduler       as sc

# ── Base Configuration ──────────────────────────────────────────
load_dotenv()
LOG_PATH    = "pipeline_logs.csv"
APP_VERSION = st.sidebar.selectbox("Model Version", ["v1", "v2", "v3"], index=0)

STOPWORDS = {
    "a","an","the","and","or","but","if","then","else","so",
    "is","are","was","were","be","been","being",
    "do","does","did","to","of","in","on","for","with","at","by","from","as",
    "how","much","many","what","when","where","who","whom","why",
    "i","me","my","you","your","we","our","they","their",
    "can","could","should","would","may","might","will","shall"
}

# ── Logging Utilities ──────────────────────────────────────────
def ensure_log_header():
    if os.path.exists(LOG_PATH):
        return
    with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "timestamp","run_id","stage","status",
            "rows_in","rows_out","latency_ms","error_message"
        ])

def log_event(run_id, stage, status, rows_out=None, latency_ms=None, error_message=""):
    ensure_log_header()
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.utcnow().isoformat(), run_id, stage, status,
            "", rows_out or "", latency_ms or "", error_message or ""
        ])

# ── Feature Engineering ─────────────────────────────────────────
def extract_keywords(query: str, max_terms: int = 6):
    tokens = re.findall(r"[a-zA-Z0-9]+", (query or "").lower())
    terms  = [t for t in tokens if t not in STOPWORDS and len(t) >= 3]
    seen, uniq = set(), []
    for t in terms:
        if t not in seen:
            uniq.append(t); seen.add(t)
    return uniq[:max_terms]

# ── Groq LLM Generation ─────────────────────────────────────────
@st.cache_resource
def get_groq_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        st.error("⚠️ GROQ_API_KEY is not set in your .env file. AI answers are disabled.")
        return None
    return Groq(api_key=key)

def generate_answer(question: str, chunks_df: pd.DataFrame, model: str = "llama3-8b-8192") -> str:
    """Concatenates retrieved Chunks into Context and calls Groq to generate a natural language response"""
    if chunks_df.empty:
        return "⚠️ No relevant documents found. Unable to generate an answer.", 0

    # Take top 5 chunks to build context (preventing token limit overflow)
    context_parts = []
    for i, row in chunks_df.head(5).iterrows():
        context_parts.append(
            f"[Source: {row['DOC_NAME']} Page {row['PAGE_NUM']}]\n{row['CHUNK_TEXT']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a helpful assistant for UMKC (University of Missouri-Kansas City) students and staff.
Answer the question based ONLY on the provided context from official UMKC documents.
If the context doesn't contain enough information, say so clearly.
Answer in the same language as the question.

Context:
{context}

Question: {question}

Answer:"""

    client = get_groq_client()
    t0 = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.2,
    )
    ms = int((time.time() - t0) * 1000)
    answer = response.choices[0].message.content.strip()
    return answer, ms

# ── Snowflake Connection ────────────────────────────────────────
@st.cache_resource(ttl=600)
def get_sf_engine():
    with open("rsa_key.p8", "rb") as f:
        pk = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )
    pkb = pk.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return dict(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )

def sf_connect():
    return snowflake.connector.connect(**get_sf_engine())

# ── Core Retrieval (With Caching) ───────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def cached_retrieval(query: str, topk: int):
    return _run_retrieval(query, topk)

def _run_retrieval(user_query: str, topk: int):
    terms = extract_keywords(user_query)
    if not terms:
        return pd.DataFrame(), terms

    where_parts = ["CHUNK_TEXT ILIKE %s" for _ in terms]
    score_parts = ["IFF(CHUNK_TEXT ILIKE %s, 1, 0)" for _ in terms]
    sql = f"""
    SELECT DOC_NAME, PAGE_NUM, CHUNK_ID, CHUNK_TEXT, TEXT_LENGTH,
           ({" + ".join(score_parts)}) AS SCORE
    FROM DOC_CHUNKS_FEATURED
    WHERE {" OR ".join(where_parts)}
    ORDER BY SCORE DESC, TEXT_LENGTH DESC
    LIMIT {int(topk)};
    """
    score_params = [f"%{t}%" for t in terms]  # for IFF() expressions in SELECT
    where_params  = [f"%{t}%" for t in terms]  # for ILIKE clauses in WHERE
    params = score_params + where_params

    conn = sf_connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return pd.DataFrame(rows, columns=cols), terms
    finally:
        try: cur.close()
        except Exception: pass
        conn.close()

# ── What-if Scenario Simulation ─────────────────────────────────
def run_whatif(base_query: str, scenarios: list[str], topk: int):
    """Retrieves multiple scenarios in parallel and returns a comparison DataFrame"""
    records = []
    for s in scenarios:
        t0 = time.time()
        df, terms = cached_retrieval(s, topk)
        ms = int((time.time() - t0) * 1000)
        avg_score = float(df["SCORE"].mean()) if not df.empty and "SCORE" in df.columns else 0
        records.append({
            "Scenario Query": s,
            "Keyword Count":  len(terms),
            "Returned Chunks": len(df),
            "Average Score":  round(avg_score, 3),
            "Latency (ms)":   ms,
            "Keywords":       ", ".join(terms),
        })
    return pd.DataFrame(records)

# ════════════════════════════════════════════════════════════════
#  UI LAYOUT
# ════════════════════════════════════════════════════════════════
st.set_page_config(page_title="UMKC PolicyPulse", layout="wide", page_icon="🎓")
st.title("🎓 UMKC PolicyPulse — Snowflake RAG (Full Extended Version)")



tabs = st.tabs([
    "🔍 Retrieval",
    "📈 Analytics Dashboard",
    "📊 Eval Comparison",
    "🔮 What-if Simulation",
    "📥 Data Ingestion",
    "🔧 Pipeline Monitoring",
])

# ─────────────────────────────────────────────────────────────
# TAB 1 · Retrieval
# ─────────────────────────────────────────────────────────────
with tabs[0]:
    st.header("🔍 Document Retrieval + AI Answer")

    q    = st.text_input("Enter your question", value="How much is a parking permit?")
    topk = st.slider("Top-K", 3, 20, 8)

    # LLM Settings
    with st.expander("⚙️ LLM Settings", expanded=False):
        llm_model = st.selectbox(
            "Groq Model",
            ["llama-3.1-8b-instant", "llama3-8b-8192", "llama-3.3-70b-versatile", "llama3-70b-8192"],
            index=0
        )
        use_llm = st.toggle("Enable AI Generated Answer", value=True)

    if st.button("🔎 Search", type="primary"):
        run_id = f"search-{int(time.time())}"
        t0 = time.time()
        try:
            # ── Step 1: Retrieval ─────────────────────────────
            with st.spinner("🔍 Retrieving documents..."):
                df, terms = cached_retrieval(q, topk)
            retrieval_ms = int((time.time() - t0) * 1000)

            # ── Step 2: LLM Generation ────────────────────────
            if use_llm and not df.empty:
                with st.spinner("🤖 AI generating answer..."):
                    answer, llm_ms = generate_answer(q, df, model=llm_model)
                log_event(run_id, "llm_generate", "success", latency_ms=llm_ms)
            else:
                answer = None
                llm_ms = 0

            total_ms = int((time.time() - t0) * 1000)

            # ── Logs & Metrics ────────────────────────────────
            log_event(run_id, "search", "success", rows_out=len(df), latency_ms=retrieval_ms)
            fs.save_features(run_id, q, terms, topk, version=APP_VERSION)
            ev.log_eval(run_id, q, df, retrieval_ms, len(terms), topk, version=APP_VERSION)

            # ── Display AI Answer ─────────────────────────────
            if answer:
                st.markdown("### 🤖 AI Answer")
                st.info(answer)
                st.caption(f"Retrieval: {retrieval_ms} ms · LLM Gen: {llm_ms} ms · Total: {total_ms} ms · Model: {llm_model}")
            else:
                st.success(f"✅ Returned {len(df)} results in {retrieval_ms} ms (AI Answer Disabled)")

            # ── Display Raw Chunks ────────────────────────────
            st.markdown("### 📄 Retrieved Raw Document Fragments")
            st.write("Extracted Keywords:", terms)
            st.dataframe(
                df[["DOC_NAME","PAGE_NUM","CHUNK_ID","SCORE","TEXT_LENGTH"]],
                use_container_width=True
            )
            for i, r in df.iterrows():
                with st.expander(
                    f"{i+1}. {r['DOC_NAME']}  p{r['PAGE_NUM']}  "
                    f"chunk={r['CHUNK_ID']}  score={r['SCORE']}"
                ):
                    st.write(r["CHUNK_TEXT"])

        except Exception as e:
            ms = int((time.time() - t0) * 1000)
            log_event(run_id, "search", "fail", rows_out=0, latency_ms=ms, error_message=str(e))
            st.error(f"Query Failed: {e}")

# ─────────────────────────────────────────────────────────────
# TAB 2 · Analytics Dashboard
# ─────────────────────────────────────────────────────────────
with tabs[1]:
    st.header("📈 Interactive Analytics Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Feature Version Distribution")
        try:
            fv = fs.load_feature_versions()
            if fv.empty:
                st.info("No feature data. Please perform a retrieval first.")
            else:
                st.dataframe(fv, use_container_width=True)
                st.bar_chart(fv.set_index("VERSION")["TOTAL_QUERIES"])
        except Exception as e:
            st.warning(f"Failed to load feature versions: {e}")

    with col2:
        st.subheader("Evaluation Metric Trends")
        try:
            hist = ev.load_metrics_history(200)
            if hist.empty:
                st.info("No evaluation data. Please perform a retrieval first.")
            else:
                hist["CREATED_AT"] = pd.to_datetime(hist["CREATED_AT"])
                st.line_chart(
                    hist.sort_values("CREATED_AT").set_index("CREATED_AT")[["AVG_SCORE","LATENCY_MS"]]
                )
        except Exception as e:
            st.warning(f"Failed to load evaluation history: {e}")

    st.subheader("Recent Feature Logs")
    try:
        fh = fs.load_feature_history(50)
        st.dataframe(fh, use_container_width=True)
    except Exception as e:
        st.warning(f"Failed to load feature history: {e}")

# ─────────────────────────────────────────────────────────────
# TAB 3 · Eval Comparison Dashboard
# ─────────────────────────────────────────────────────────────
with tabs[2]:
    st.header("📊 Evaluation Comparison Dashboard")

    try:
        summary = ev.load_metrics_summary()
        if summary.empty:
            st.info("No evaluation data yet. Please perform a few searches in the Retrieval tab.")
        else:
            st.subheader("Summary by Version")
            st.dataframe(summary, use_container_width=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Versions",  len(summary))
            with c2:
                st.metric("Total Runs", int(summary["TOTAL_RUNS"].sum()))
            with c3:
                best = summary.loc[summary["MEAN_AVG_SCORE"].idxmax(), "VERSION"]
                st.metric("Highest Avg Score Version", best)

            st.subheader("Average Score Comparison")
            st.bar_chart(summary.set_index("VERSION")["MEAN_AVG_SCORE"])

            st.subheader("Average Latency Comparison (ms)")
            st.bar_chart(summary.set_index("VERSION")["MEAN_LATENCY_MS"])

            st.subheader("Individual Eval Records (Recent 200)")
            detail = ev.load_metrics_history(200)
            st.dataframe(detail, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load evaluation data: {e}")

# ─────────────────────────────────────────────────────────────
# TAB 4 · What-if Simulation
# ─────────────────────────────────────────────────────────────
with tabs[3]:
    st.header("🔮 What-if Scenario Simulation")
    st.markdown(
        "Enter multiple query variations. The system retrieves them in parallel and compares results—"
        "helping you find the optimal phrasing or evaluate the impact of keyword changes."
    )

    default_scenarios = (
        "How much is a parking permit?\n"
        "What is the cost of student parking?\n"
        "Parking fees for faculty\n"
        "Campus parking regulations"
    )
    raw = st.text_area("Scenario List (One query per line)", value=default_scenarios, height=140)
    wi_topk = st.slider("Top-K per Scenario", 3, 15, 5, key="wi_topk")

    if st.button("▶ Run Simulation", type="primary"):
        scenarios = [s.strip() for s in raw.splitlines() if s.strip()]
        if not scenarios:
            st.warning("Please enter at least one scenario")
        else:
            with st.spinner(f"Simulating {len(scenarios)} scenarios..."):
                cmp = run_whatif("", scenarios, wi_topk)

            st.success("Simulation Complete!")
            st.dataframe(cmp, use_container_width=True)

            st.subheader("Returned Chunks Count Comparison")
            st.bar_chart(cmp.set_index("Scenario Query")["Returned Chunks"])

            st.subheader("Average Score Comparison")
            st.bar_chart(cmp.set_index("Scenario Query")["Average Score"])

            st.subheader("Latency Comparison (ms)")
            st.bar_chart(cmp.set_index("Scenario Query")["Latency (ms)"])

            best_row = cmp.loc[cmp["Average Score"].idxmax()]
            st.info(f"🏆 Best Scenario: **{best_row['Scenario Query']}** "
                    f"Avg Score={best_row['Average Score']}  "
                    f"Keywords: {best_row['Keywords']}")

# ─────────────────────────────────────────────────────────────
# TAB 5 · Data Ingestion
# ─────────────────────────────────────────────────────────────
with tabs[4]:
    st.header("📥 Additional Dataset Ingestion")

    st.markdown("""
    Upload CSV files. The system will parse and append them to the Snowflake `DOC_CHUNKS_FEATURED` table.
    
    **CSV must contain these columns:**
    `DOC_NAME`, `PAGE_NUM`, `CHUNK_ID`, `CHUNK_TEXT`, `TEXT_LENGTH`
    """)

    uploaded = st.file_uploader("Select CSV files (supports multiple)", type="csv", accept_multiple_files=True)

    if uploaded and st.button("⬆ Start Ingestion", type="primary"):
        sc.ensure_dirs()
        for uf in uploaded:
            save_path = os.path.join(sc.INBOX_DIR, uf.name)
            with open(save_path, "wb") as f:
                f.write(uf.getbuffer())

        results = sc.run_once()
        for r in results:
            if r["status"] == "success":
                st.success(f"✅ {r['file']} — Ingested {r['rows']} rows")
            elif r["status"] == "skipped":
                st.info(f"⏭ {r['file']} — Already ingested, skipped")
            else:
                st.error(f"❌ {r['file']} — Failed: {r.get('error')}")

    st.subheader("Ingestion Logs")
    try:
        ilog = sc.load_ingest_log(50)
        st.dataframe(ilog, use_container_width=True)
    except Exception as e:
        st.warning(f"Ingestion log failed to load (Upload a file first): {e}")

    st.divider()
    st.subheader("⏰ Scheduled Auto-Ingestion Instructions")
    st.code(
        "# Run the scheduler independently in the background (scans ingest_inbox/ every 60s)\n"
        "python scheduler.py\n\n"
        "# Custom interval (seconds)\n"
        "SCHEDULER_INTERVAL_SEC=30 python scheduler.py",
        language="bash"
    )

# ─────────────────────────────────────────────────────────────
# TAB 6 · Pipeline Monitoring
# ─────────────────────────────────────────────────────────────
with tabs[5]:
    st.header("🔧 Pipeline Monitoring Dashboard")

    if os.path.exists(LOG_PATH):
        log_df = pd.read_csv(LOG_PATH)

        total  = len(log_df)
        ok     = (log_df["status"] == "success").sum()
        fail   = (log_df["status"] == "fail").sum()
        avg_ms = log_df["latency_ms"].dropna().astype(float).mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Runs",  total)
        c2.metric("Success",     int(ok))
        c3.metric("Failure",     int(fail))
        c4.metric("Avg Latency (ms)", f"{avg_ms:.0f}" if not pd.isna(avg_ms) else "—")

        st.subheader("Success / Failure Distribution")
        status_counts = log_df["status"].value_counts()
        st.bar_chart(status_counts)

        st.subheader("Latency Trend")
        lat = log_df[["timestamp","latency_ms"]].dropna()
        lat["latency_ms"] = lat["latency_ms"].astype(float)
        lat = lat.set_index("timestamp")
        st.line_chart(lat)

        st.subheader("Recent 50 Logs")
        st.dataframe(log_df.tail(50), use_container_width=True)
    else:
        st.info("No logs found. Perform a search in the Retrieval tab first.")