import os
import sys
import json
import datetime
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Add current directory to path for direct backend imports fallback
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Page Configuration
st.set_page_config(
    page_title="Infosys AI Bug Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Glassmorphism CSS
CUSTOM_CSS = """
<style>
    /* Dark AI Futuristic Theme Palette */
    :root {
        --bg-dark: #090d16;
        --card-bg: rgba(18, 26, 42, 0.75);
        --card-border: rgba(0, 242, 254, 0.2);
        --accent-cyan: #00f2fe;
        --accent-blue: #4facfe;
        --accent-purple: #7f00ff;
        --text-primary: #f0f4f8;
        --text-muted: #94a3b8;
    }

    /* Global Body styling */
    .stApp {
        background: linear-gradient(135deg, #070a12 0%, #0d1322 50%, #080c18 100%);
        color: var(--text-primary);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Hide default Streamlit header/footer padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Glassmorphism Card Container */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(0, 242, 254, 0.45);
        box-shadow: 0 8px 32px 0 rgba(0, 242, 254, 0.15);
    }

    /* Custom Metric Styling */
    .metric-container {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 0.85rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* Severity Glowing Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-critical {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.5);
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
    }
    .badge-high {
        background: rgba(249, 115, 22, 0.2);
        color: #fb923c;
        border: 1px solid rgba(249, 115, 22, 0.5);
        box-shadow: 0 0 10px rgba(249, 115, 22, 0.3);
    }
    .badge-medium {
        background: rgba(234, 179, 8, 0.2);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.5);
    }
    .badge-low {
        background: rgba(56, 189, 248, 0.2);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.5);
    }
    .badge-resolved {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.5);
    }
    .badge-open {
        background: rgba(168, 85, 247, 0.2);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.5);
    }

    /* Custom Headers */
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Sidebar Logo Header */
    .sidebar-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
    }
    .sidebar-logo {
        font-size: 1.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sidebar-subtitle {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Backend Integration Layer with HTTP + Direct Engine Fallback
class BackendService:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.use_http = True
        self._check_connection()

    def _check_connection(self):
        try:
            r = requests.get(f"{self.base_url.rsplit('/api/v1', 1)[0]}/api/health", timeout=1.5)
            if r.status_code == 200:
                self.use_http = True
                return
        except Exception:
            pass
        self.use_http = False

    def get_bugs(self, q=None, category=None, severity=None, status=None):
        if self.use_http:
            try:
                params = {}
                if q: params["q"] = q
                if category and category != "All": params["category"] = category
                if severity and severity != "All": params["severity"] = severity
                if status and status != "All": params["status"] = status
                res = requests.get(f"{self.base_url}/bugs", params=params, timeout=5)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                st.error(f"HTTP fetch error: {e}")

        # Fallback to direct DB query
        return self._direct_db_get_bugs(q, category, severity, status)

    def _direct_db_get_bugs(self, q=None, category=None, severity=None, status=None):
        from backend.app.database import SessionLocal
        from backend.app.models.bug import Bug
        from backend.app.api.bugs import format_bug_dict
        from sqlalchemy import or_

        db = SessionLocal()
        try:
            query = db.query(Bug)
            if q and q.strip():
                sterm = f"%{q.strip()}%"
                query = query.filter(or_(
                    Bug.title.ilike(sterm),
                    Bug.description.ilike(sterm),
                    Bug.stack_trace.ilike(sterm),
                    Bug.root_cause.ilike(sterm),
                    Bug.category.ilike(sterm)
                ))
            if category and category != "All":
                query = query.filter(Bug.category == category)
            if severity and severity != "All":
                query = query.filter(Bug.severity == severity)
            if status and status != "All":
                query = query.filter(Bug.status == status)

            bugs = query.order_by(Bug.id.desc()).all()
            return [format_bug_dict(b) for b in bugs]
        finally:
            db.close()

    def get_stats(self):
        if self.use_http:
            try:
                res = requests.get(f"{self.base_url}/bugs/stats", timeout=5)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        
        from backend.app.database import SessionLocal
        from backend.app.api.bugs import get_bug_stats
        db = SessionLocal()
        try:
            return get_bug_stats(db)
        finally:
            db.close()

    def get_analytics(self):
        if self.use_http:
            try:
                res = requests.get(f"{self.base_url}/bugs/analytics", timeout=5)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        
        from backend.app.database import SessionLocal
        from backend.app.api.bugs import get_analytics
        db = SessionLocal()
        try:
            return get_analytics(db)
        finally:
            db.close()

    def get_categories(self):
        if self.use_http:
            try:
                res = requests.get(f"{self.base_url}/bugs/categories", timeout=5)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        
        from backend.app.database import SessionLocal
        from backend.app.api.bugs import get_categories
        db = SessionLocal()
        try:
            return get_categories(db)
        finally:
            db.close()

    def analyze_bug(self, title, description, stack_trace, category, log_file_name="", log_content=""):
        payload = {
            "title": title,
            "description": description,
            "stack_trace": stack_trace,
            "log_file_name": log_file_name,
            "log_content": log_content,
            "category": category
        }
        if self.use_http:
            try:
                res = requests.post(f"{self.base_url}/bugs/analyze", json=payload, timeout=10)
                if res.status_code in [200, 201]:
                    return res.json(), None
                return None, res.json().get("detail", "Analysis failed")
            except Exception as e:
                return None, str(e)
        
        # Direct execution fallback
        from backend.app.database import SessionLocal
        from backend.app.schemas.bug import BugCreate
        from backend.app.api.analyze import analyze_bug
        db = SessionLocal()
        try:
            b_in = BugCreate(
                title=title,
                description=description,
                stack_trace=stack_trace,
                log_file_name=log_file_name,
                log_content=log_content,
                category=category
            )
            res = analyze_bug(b_in, db)
            return res, None
        except Exception as e:
            return None, str(e)
        finally:
            db.close()

    def resolve_bug(self, bug_id, root_cause, resolution, resolution_notes=""):
        payload = {
            "root_cause": root_cause,
            "resolution": resolution,
            "resolution_notes": resolution_notes
        }
        if self.use_http:
            try:
                res = requests.post(f"{self.base_url}/bugs/{bug_id}/resolve", json=payload, timeout=5)
                if res.status_code == 200:
                    return res.json(), None
                return None, res.json().get("detail", "Resolve failed")
            except Exception as e:
                return None, str(e)

        from backend.app.database import SessionLocal
        from backend.app.schemas.bug import BugResolveRequest
        from backend.app.api.bugs import resolve_bug
        db = SessionLocal()
        try:
            req = BugResolveRequest(root_cause=root_cause, resolution=resolution, resolution_notes=resolution_notes)
            res = resolve_bug(bug_id, req, db)
            return res, None
        except Exception as e:
            return None, str(e)
        finally:
            db.close()

    def reset_db(self):
        if self.use_http:
            try:
                res = requests.post(f"{self.base_url}/bugs/reset", timeout=5)
                if res.status_code == 200:
                    return True, "Database reset to sample data successfully"
            except Exception as e:
                pass
        
        from backend.app.database import SessionLocal
        from backend.app.seed import seed_database
        db = SessionLocal()
        try:
            seed_database(db, force=True)
            return True, "Database reset to sample data successfully (Embedded DB)"
        except Exception as e:
            return False, str(e)
        finally:
            db.close()

    def get_chat_history(self, bug_id):
        if self.use_http:
            try:
                res = requests.get(f"{self.base_url}/bugs/{bug_id}/chat", timeout=5)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass

        from backend.app.database import SessionLocal
        from backend.app.api.chat import get_chat_history
        db = SessionLocal()
        try:
            msgs = get_chat_history(bug_id, db)
            return [{"sender": m.sender, "message": m.message} for m in msgs]
        except Exception:
            return []
        finally:
            db.close()

    def send_chat_message(self, bug_id, message):
        if self.use_http:
            try:
                res = requests.post(f"{self.base_url}/bugs/{bug_id}/chat", json={"message": message}, timeout=10)
                if res.status_code in [200, 201]:
                    return res.json(), None
            except Exception as e:
                return None, str(e)

        from backend.app.database import SessionLocal
        from backend.app.schemas.bug import ChatMessageCreate
        from backend.app.api.chat import send_chat_message
        db = SessionLocal()
        try:
            req = ChatMessageCreate(message=message)
            res = send_chat_message(bug_id, req, db)
            return {"sender": res.sender, "message": res.message}, None
        except Exception as e:
            return None, str(e)
        finally:
            db.close()

    def audit_code(self, code_text):
        if self.use_http:
            try:
                res = requests.post(f"{self.base_url}/code-review", json={"code": code_text}, timeout=5)
                if res.status_code == 200:
                    return res.json(), None
            except Exception as e:
                return None, str(e)

        from backend.app.schemas.bug import CodeReviewRequest
        from backend.app.api.code_review import audit_code
        try:
            req = CodeReviewRequest(code=code_text)
            res = audit_code(req)
            return res, None
        except Exception as e:
            return None, str(e)

# Instantiate Service Singleton
backend = BackendService(API_BASE_URL)

# Helper function for rendering glowing badges
def render_badge(text, badge_type):
    return f'<span class="badge badge-{badge_type.lower()}">{text}</span>'

# Sidebar Navigation Setup
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-logo">⚡ INFOSYS AI</div>
        <div class="sidebar-subtitle">Bug Diagnosis Platform</div>
    </div>
    """, unsafe_allow_html=True)

    status_color = "#4ade80" if backend.use_http else "#facc15"
    status_mode = "HTTP API (Port 8000)" if backend.use_http else "Direct Embedded Engine"
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.1); padding: 0.6rem; border-radius: 8px; font-size: 0.8rem; margin-bottom: 1rem;">
        <div>Backend Engine Status:</div>
        <div style="font-weight: 700; color: {status_color};">● {status_mode}</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        options=[
            "📊 Executive Dashboard",
            "⚡ AI Multi-Agent Analyzer",
            "🐛 Bug Knowledge Base",
            "💬 AI Mentor Chat",
            "🩺 Code Doctor",
            "⚙️ Platform Settings"
        ],
        index=0
    )

    st.markdown("---")
    st.caption("Infosys Multi-Agent AI Platform v2.0")
    st.caption("Powered by FastAPI & Streamlit")

# PAGE 1: EXECUTIVE DASHBOARD
if page == "📊 Executive Dashboard":
    st.markdown('<div class="section-title">📊 Executive Defect Intelligence Dashboard</div>', unsafe_allow_html=True)
    
    stats = backend.get_stats()
    analytics = backend.get_analytics()

    # Top Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{stats.get('total', 0)}</div>
            <div class="metric-label">Total Tracked</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value" style="background: linear-gradient(135deg, #f87171 0%, #ef4444 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{stats.get('open', 0)}</div>
            <div class="metric-label">Open Bugs</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value" style="background: linear-gradient(135deg, #fb923c 0%, #f97316 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{stats.get('inProgress', 0)}</div>
            <div class="metric-label">In-Progress</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value" style="background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{stats.get('resolved', 0)}</div>
            <div class="metric-label">Resolved</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value" style="background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{stats.get('resolutionRate', 0)}%</div>
            <div class="metric-label">Resolution Rate</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row
    ch_col1, ch_col2 = st.columns(2)
    with ch_col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Severity Distribution")
        sev_counts = stats.get("severityCounts", {})
        sev_df = pd.DataFrame([{"Severity": k, "Count": v} for k, v in sev_counts.items()])
        color_map = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#38bdf8"}
        fig_sev = px.pie(sev_df, names="Severity", values="Count", color="Severity", color_discrete_map=color_map, hole=0.4)
        fig_sev.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f0f4f8", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_sev, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Bugs by Category")
        cat_counts = stats.get("categoryCounts", {})
        cat_df = pd.DataFrame([{"Category": k, "Count": v} for k, v in cat_counts.items()]).sort_values("Count", ascending=True)
        fig_cat = px.bar(cat_df, x="Count", y="Category", orientation='h', color_discrete_sequence=["#00f2fe"])
        fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f0f4f8", xaxis_title="Bug Count", yaxis_title="", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_cat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Analytics Component Risk Heatmap & Anti-Patterns
    an_col1, an_col2 = st.columns(2)
    with an_col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🔥 Component Risk Matrix")
        for cr in analytics.get("categoryRisks", []):
            risk_clr = "#ef4444" if cr["riskScore"] >= 60 else ("#f97316" if cr["riskScore"] >= 30 else "#38bdf8")
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div>
                    <strong style="color: #f0f4f8;">{cr['category']}</strong>
                    <div style="font-size: 0.75rem; color: #94a3b8;">Total: {cr['totalBugs']} | Open: {cr['openBugs']} | Critical/High: {cr['criticalHighCount']}</div>
                </div>
                <div style="text-align: right;">
                    <span style="font-weight: 800; font-size: 1.1rem; color: {risk_clr};">{cr['riskScore']}</span>
                    <div style="font-size: 0.7rem; color: {risk_clr};">{cr['riskLevel']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with an_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("⚠️ Recurring Anti-Pattern Alerts")
        for ap in analytics.get("antiPatterns", []):
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; padding: 0.75rem; border-radius: 4px; margin-bottom: 0.75rem;">
                <div style="font-weight: 700; color: #f87171;">{ap['pattern']}</div>
                <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 0.2rem;">Impact: {ap['impact']} | Categories: {', '.join(ap['affectedCategories'])}</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.4rem;">💡 <i>{ap['recommendation']}</i></div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<h4 style='font-size: 1.1rem; margin-top: 1rem;'>🎯 Team Productivity Focus</h4>", unsafe_allow_html=True)
        for rec in analytics.get("teamRecommendations", []):
            st.markdown(f"• {rec}")
        st.markdown('</div>', unsafe_allow_html=True)

# PAGE 2: MULTI-AGENT BUG ANALYZER
elif page == "⚡ AI Multi-Agent Analyzer":
    st.markdown('<div class="section-title">⚡ Multi-Agent AI Bug Diagnosis Pipeline</div>', unsafe_allow_html=True)
    st.caption("Submit a bug report or stack trace to run the 5-Agent pipeline (Triage, Log Analysis, Root Cause RAG, Duplicate Detection, and Remediation Strategy).")

    # Sample Presets Selector
    samples = {
        "Custom Bug Input": {"title": "", "desc": "", "stack": "", "cat": "Auto-detect"},
        "Order Service - Null Pointer Exception": {
            "title": "NullPointerException in Order Processing Service during checkout",
            "desc": "Users experience unexpected error 500 when attempting to complete payment with missing user profile details.",
            "stack": "java.lang.NullPointerException: Cannot invoke 'UserProfile.getBillingAddress()' because 'user' is null\n\tat com.infosys.checkout.OrderService.processOrder(OrderService.java:142)\n\tat com.infosys.checkout.OrderController.checkout(OrderController.java:58)",
            "cat": "Backend"
        },
        "Database Connection Leak in HikariCP": {
            "title": "HikariCP connection pool exhaustion after 30 minutes under load",
            "desc": "API endpoints start timing out with ConnectionTimeoutException under high concurrent traffic.",
            "stack": "com.zaxxer.hikari.pool.HikariPool$PoolInitializationException: Exception during pool initialization\n\tcaused by java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available, request timed out after 30000ms.",
            "cat": "Database"
        },
        "SQL Injection Vulnerability in User Search": {
            "title": "Unsanitized user search input allows raw SQL string concatenation",
            "desc": "Security audit detected raw query concatenation in user filter API endpoint.",
            "stack": "org.sqlite.SQLiteException: [SQLITE_ERROR] SQL error or missing database (near \"OR\": syntax error)\n\tat com.infosys.repository.UserRepository.findByName(UserRepository.java:89)",
            "cat": "Security"
        }
    }

    selected_sample = st.selectbox("⚡ Quick Load Sample Scenario", options=list(samples.keys()))
    sample_data = samples[selected_sample]

    uploaded_file = st.file_uploader("📁 Attach Log File (.log, .txt, .json)", type=["log", "txt", "json"])
    log_file_content = ""
    log_file_name = ""
    if uploaded_file is not None:
        log_file_name = uploaded_file.name
        try:
            log_file_content = uploaded_file.getvalue().decode("utf-8")
            st.success(f"Attached file: `{log_file_name}` ({len(log_file_content)} bytes)")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    with st.form("analyze_form"):
        title_in = st.text_input("Bug Title *", value=sample_data["title"], placeholder="e.g. NullPointerException in Payment Gateway")
        desc_in = st.text_area("Bug Description", value=sample_data["desc"], placeholder="Explain expected vs actual behavior...")
        stack_in = st.text_area("Stack Trace / Log Error Output", value=sample_data["stack"], placeholder="Paste exception stack trace or server log...", height=120)
        
        cats = backend.get_categories()
        if "Auto-detect" not in cats:
            cats = ["Auto-detect"] + cats
        cat_in = st.selectbox("Category Preference", options=cats, index=0)

        submit_btn = st.form_submit_button("🚀 Run AI Diagnosis Pipeline")

    if submit_btn:
        if not title_in.strip():
            st.error("Please enter a bug title.")
        elif not desc_in.strip() and not stack_in.strip() and not log_file_content.strip():
            st.error("Please provide either a description, stack trace, or attached log file.")
        else:
            with st.spinner("Executing Multi-Agent AI Pipeline (Log Parsing -> AI Triage -> Root Cause -> TF-IDF Duplicates -> FAISS RAG -> Remediation)..."):
                result, err = backend.analyze_bug(title_in, desc_in, stack_in, cat_in, log_file_name, log_file_content)
                if err:
                    st.error(f"Analysis failed: {err}")
                else:
                    st.success(f"Analysis Complete! Logged as bug code **{result.get('id')}**")
                    st.session_state["last_analysis"] = result

    # Render Analysis Results
    if "last_analysis" in st.session_state:
        res = st.session_state["last_analysis"]
        analysis = res.get("analysisResults") or {}

        st.markdown("---")
        st.markdown(f"### 📋 Analysis Report for Bug `{res.get('id')}`: {res.get('title')}")
        
        # Summary Header Tags
        b_sev = render_badge(res.get('severity', 'Medium'), res.get('severity', 'Medium'))
        b_cat = render_badge(res.get('category', 'General'), 'low')
        b_prio = render_badge(f"Priority: {res.get('priority', 'P3')}", 'open')
        st.markdown(f"Status: {b_sev} {b_cat} {b_prio}", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        t1, t2, t3, t_fix, t_test, t_ver, t_sec, t4, t5, t6 = st.tabs([
            "🎯 1. AI Triage & Priority",
            "🔍 2. Log Parsing",
            "🧠 3. Root Cause Analysis",
            "🪄 4. AI Auto-Fix",
            "🧪 5. Auto Tests",
            "✅ 6. Verification",
            "🛡️ 7. Security Scan",
            "👯 8. Duplicate Check",
            "📚 9. RAG Retrieval",
            "🛠️ 10. Fix Recommendation"
        ])

        with t1:
            triage = analysis.get("triage", {})
            ps = triage.get("priorityScore", {})
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            col_a, col_b, col_c, col_d, col_e = st.columns(5)
            col_a.metric("Severity", triage.get("severity", "Medium"))
            col_b.metric("Priority", triage.get("priority", "P3"))
            col_c.metric("Category", triage.get("category", "General"))
            col_d.metric("Confidence Score", f"{triage.get('confidence', 85)}%")
            col_e.metric("Priority Score", f"{ps.get('score', 75)}/100 ({ps.get('level', 'Medium')})")

            st.markdown(f"**Classification Summary:** {triage.get('summary', 'Classified automatically by TriageAgent.')}")
            
            if triage.get("reasoning"):
                st.markdown(f"**🧠 Classification Reasoning:** {triage.get('reasoning')}")
            
            if triage.get("tags"):
                st.markdown(f"**🏷️ Tags:** {', '.join(triage.get('tags', []))}")
                
            rec = triage.get("details", {}).get("recommendation")
            if rec:
                st.info(rec)

            clarifications = triage.get("clarificationQuestions") or triage.get("clarificationsNeeded")
            if clarifications:
                st.warning("⚠️ Clarifications Requested to Boost Diagnostic Accuracy:")
                for q in clarifications:
                    if isinstance(q, dict):
                        st.write(f"- **{q.get('question')}** (Options: {', '.join(q.get('options', []))})")
                    else:
                        st.write(f"- {q}")
            st.markdown('</div>', unsafe_allow_html=True)

        with t2:
            log_an = analysis.get("logAnalysis", {})
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("⚡ Automatic Log Parsing Extracted Parameters")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Exception Type", log_an.get("exceptionType") or log_an.get("errorType") or "Unknown")
            col2.metric("Programming Language", (log_an.get("programmingLanguage") or log_an.get("language") or "generic").capitalize())
            col3.metric("Failure Line", f"Line {log_an.get('lineNumber', 'N/A')}")

            col4, col5 = st.columns(2)
            col4.metric("Failing Method", f"{log_an.get('methodName', 'N/A')}()")
            col5.metric("Failure Point Location", log_an.get("failurePoint") or "N/A")

            st.markdown(f"**Error Message:** `{log_an.get('errorMessage') or 'N/A'}`")
            
            code_path = log_an.get("codePath") or log_an.get("details", {}).get("frames", [])
            if code_path:
                with st.expander("📚 Execution Call Stack / Parsed Code Path", expanded=True):
                    for idx, frame in enumerate(code_path, 1):
                        st.markdown(f"`{idx}.` `{frame}`")
            
            st.markdown("**Parsed Log/Stack Output:**")
            st.code(log_an.get("parsedSnippet") or res.get("stackTrace") or "No stack trace provided.", language="java")
            
            insights = log_an.get("logInsights", [])
            if insights:
                st.markdown("**🔍 Log Pattern Insights:**")
                for ins in insights:
                    st.markdown(f"- {ins}")
            st.markdown('</div>', unsafe_allow_html=True)

        with t3:
            rc = analysis.get("rootCause", {})
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f"**Diagnosed Root Cause Category:** `{rc.get('category', 'General Failure')}`")
            st.markdown(f"**Technical Diagnosis:** {rc.get('technicalExplanation', rc.get('summary', 'No technical explanation generated.'))}")
            
            # Ranked Probable Causes
            probable = rc.get("probableCauses", [])
            if probable:
                with st.expander("📊 Probable Root Cause Ranking Breakdown", expanded=True):
                    for p in probable:
                        st.markdown(f"- **[{p.get('confidence')}% Confidence]** {p.get('cause')} *(Source: {p.get('source')})*")

            beginner_sum = rc.get("beginnerSummary") or rc.get("beginnerExplanation", {}).get("simplifiedSummary")
            analogy = rc.get("analogy") or rc.get("beginnerExplanation", {}).get("analogy")
            if beginner_sum or analogy:
                st.info(f"💡 **Beginner-Friendly Explanation:** {beginner_sum or ''}")
                if analogy:
                    st.caption(f"Real-world Analogy: {analogy}")

            prev_tips = rc.get("preventionTips", [])
            if prev_tips:
                st.markdown("**🛡️ Prevention Best Practices:**")
                for tip in prev_tips:
                    st.markdown(f"- {tip}")
            st.markdown('</div>', unsafe_allow_html=True)

        with t_fix:
            auto_fix = analysis.get("autoFix") or {}
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("🪄 AI Auto-Fix Corrected Code Suggestion")
            st.markdown(f"**Explanation:** {auto_fix.get('explanation', 'Corrected code generated by AI Auto-Fix Agent.')}")
            if auto_fix.get("diff"):
                st.markdown("**Unified Code Fix Diff:**")
                st.code(auto_fix.get("diff"), language="diff")
            if auto_fix.get("fixedCode"):
                st.markdown("**Corrected Code Snippet:**")
                st.code(auto_fix.get("fixedCode"), language=auto_fix.get("language", "python"))
            st.markdown('</div>', unsafe_allow_html=True)

        with t_test:
            test_gen = analysis.get("testGenerator") or {}
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader(f"🧪 Auto-Generated Unit & Regression Tests ({test_gen.get('testFramework', 'Pytest')})")
            if test_gen.get("testCode"):
                st.code(test_gen.get("testCode"), language="python")
            st.markdown('</div>', unsafe_allow_html=True)

        with t_ver:
            fix_ver = analysis.get("fixVerification") or {}
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("✅ Fix Verification & Quality Assurance Report")
            is_p = fix_ver.get("status") == "PASS"
            st.markdown(f"**Status:** {'🟢 PASS' if is_p else '🔴 FAIL'} | **Score:** `{fix_ver.get('score', 100)}/100` | **Execution:** `{fix_ver.get('executionTimeMs', 12)}ms`")
            st.info(fix_ver.get("summary", "All verification checks passed."))
            for c in fix_ver.get("checks", []):
                st.markdown(f"- **[{c.get('status')}] {c.get('name')}:** {c.get('details')}")
            st.markdown('</div>', unsafe_allow_html=True)

        with t_sec:
            sec_scan = analysis.get("securityScan") or {}
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader(f"🛡️ Security Vulnerability Scanner (Risk: {sec_scan.get('riskLevel', 'Clean')})")
            st.markdown(f"**Score:** `{sec_scan.get('score', 100)}/100` | **Total Findings:** `{sec_scan.get('totalVulnerabilities', 0)}`")
            st.info(sec_scan.get("summary", "No security vulnerabilities detected."))
            for f in sec_scan.get("findings", []):
                st.warning(f"**[{f.get('severity')}] {f.get('category')} ({f.get('cwe')}):** Line {f.get('line')} - {f.get('message')}")
            st.markdown('</div>', unsafe_allow_html=True)

        with t4:
            dup = analysis.get("duplicate", {})
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            is_dup = dup.get("isDuplicate", dup.get("hasDuplicates", False))
            sim_score = dup.get("similarityScore", 0)
            if not sim_score and dup.get("duplicates"):
                sim_score = dup["duplicates"][0].get("similarity", 0)

            dup_clr = "#ef4444" if is_dup else "#4ade80"
            st.markdown(f"Duplicate Status: <strong style='color:{dup_clr};'>{'DUPLICATE DETECTED' if is_dup else 'UNIQUE DEFECT'}</strong> (Max Similarity: {sim_score}%)", unsafe_allow_html=True)
            
            if dup.get("matchedBugId"):
                st.markdown(f"**Top Matched Defect:** `{dup.get('matchedBugId')}` — *{dup.get('matchedBugTitle')}*")
                if dup.get("historicalResolution"):
                    st.success(f"**Resolved Solution:** {dup.get('historicalResolution')}")
            
            duplicates_list = dup.get("duplicates", [])
            if duplicates_list:
                st.markdown("#### 👯 Similar Past Defects in Knowledge Base")
                for d in duplicates_list:
                    with st.expander(f"📌 {d.get('id')}: {d.get('title')} ({d.get('similarity')}% match)", expanded=False):
                        st.markdown(f"- **Title Similarity:** {d.get('titleSimilarity', 0)}% | **Content:** {d.get('contentSimilarity', 0)}% | **Error:** {d.get('errorSimilarity', 0)}%")
                        st.markdown(f"- **Root Cause:** {d.get('rootCause')}")
                        st.markdown(f"- **Resolution:** {d.get('resolution')}")
            else:
                st.caption("No similar historical defects found above threshold.")

            rec = dup.get("details", {}).get("recommendation")
            if rec:
                st.caption(f"Recommendation: {rec}")
            st.markdown('</div>', unsafe_allow_html=True)

        with t5:
            rag = analysis.get("ragRetrieval") or {}
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📚 RAG Knowledge Retrieval (Sentence Transformers + FAISS)")
            st.markdown(f"**Retrieval Engine:** `{rag.get('details', {}).get('vectorEngine', 'SentenceTransformers + FAISS IndexFlatIP')}`")
            st.markdown(f"**Summary:** {rag.get('summary', 'Retrieved relevant historical resolutions.')}")

            items = rag.get("items", [])
            if items:
                st.markdown("#### 🎯 Top Retrieved Historical Bugs & Confirmed Resolutions")
                for item in items:
                    with st.expander(f"📌 {item.get('id')}: {item.get('title')} ({item.get('similarityScore')}% Similarity Match)", expanded=True):
                        st.markdown(f"- **Category:** `{item.get('category')}`")
                        st.markdown(f"- **Diagnosed Root Cause:** {item.get('rootCause')}")
                        st.success(f"**Confirmed Resolution:** {item.get('confirmedResolution')}")
            else:
                st.info("No matching historical resolutions retrieved from Knowledge Base.")
            st.markdown('</div>', unsafe_allow_html=True)

        with t6:
            rem = analysis.get("remediation", {})
            strat_map = rem.get("strategyMap") or {}
            strat_list = rem.get("strategies", [])
            
            if not strat_map and isinstance(strat_list, list) and len(strat_list) >= 3:
                strat_map = {
                    "hotfix": strat_list[0],
                    "refactor": strat_list[1],
                    "architecture": strat_list[2]
                }
            
            st.markdown("Select a recommended fix strategy tier below:")
            f1, f2, f3 = st.tabs(["⚡ Hotfix (Quick)", "🧹 Refactor (Standard)", "🏛️ Architecture (Long-term)"])
            
            def render_fix_card(fix_data):
                if not fix_data:
                    st.write("No strategy data available.")
                    return
                desc = fix_data.get("description") or fix_data.get("approach", "")
                st.markdown(f"**Approach:** {desc}")
                col_x, col_y = st.columns(2)
                col_x.markdown(f"**Effort:** `{fix_data.get('effort', 'Low')}` | **Risk:** `{fix_data.get('risk', 'Low')}`")
                
                steps = fix_data.get("steps", [])
                if steps:
                    st.markdown("**Action Steps:**")
                    for s in steps:
                        st.markdown(f"1. {s}" if not s.startswith("1.") else s)
                
                code_snip = fix_data.get("codeSnippet") or fix_data.get("codeExample")
                if code_snip:
                    st.markdown("**Code Fix Example:**")
                    st.code(code_snip, language="java")
                
                if fix_data.get("pros"):
                    st.caption("Pros: " + ", ".join(fix_data.get("pros", [])))
                if fix_data.get("cons"):
                    st.caption("Cons: " + ", ".join(fix_data.get("cons", [])))

            with f1:
                render_fix_card(strat_map.get("hotfix"))
            with f2:
                render_fix_card(strat_map.get("refactor"))
            with f3:
                render_fix_card(strat_map.get("architecture"))

            hist_fixes = rem.get("historicalFixes", [])
            if hist_fixes:
                st.markdown("---")
                st.markdown("#### 📚 Resolutions from Similar Past Defects")
                for hf in hist_fixes:
                    st.markdown(f"• **{hf.get('bugId')}**: {hf.get('resolution')}")


# PAGE 3: BUG KNOWLEDGE BASE
elif page == "🐛 Bug Knowledge Base":
    st.markdown('<div class="section-title">🐛 Bug Knowledge Base & Defect Explorer</div>', unsafe_allow_html=True)

    # Search and Filter Toolbar
    f_col1, f_col2, f_col3, f_col4 = st.columns([3, 1.5, 1.5, 1.5])
    with f_col1:
        q_search = st.text_input("🔍 Search bugs...", placeholder="Search title, stack trace, root cause...")
    with f_col2:
        categories = backend.get_categories()
        sel_cat = st.selectbox("Category", options=categories)
    with f_col3:
        sel_sev = st.selectbox("Severity", options=["All", "Critical", "High", "Medium", "Low"])
    with f_col4:
        sel_stat = st.selectbox("Status", options=["All", "Open", "In-Progress", "Resolved"])

    bugs = backend.get_bugs(q=q_search, category=sel_cat, severity=sel_sev, status=sel_stat)

    st.caption(f"Showing {len(bugs)} bug records matching filters.")
    st.markdown("<br>", unsafe_allow_html=True)

    if not bugs:
        st.info("No bugs found matching the specified criteria.")
    else:
        for b in bugs:
            b_sev = render_badge(b.get("severity", "Medium"), b.get("severity", "Medium"))
            b_stat = render_badge(b.get("status", "Open"), "resolved" if b.get("status") == "Resolved" else ("open" if b.get("status") == "Open" else "high"))
            b_cat = render_badge(b.get("category", "General"), "low")

            header_html = f"**{b.get('id')}**: {b.get('title')} &nbsp; {b_sev} {b_cat} {b_stat}"
            
            with st.expander(f"{b.get('id')} — {b.get('title')} ({b.get('severity')}) — [{b.get('status')}]"):
                st.markdown(f"**Date Logged:** {b.get('dateSubmitted')} | **Category:** {b.get('category')} | **Status:** {b.get('status')}")
                st.markdown(f"**Description:** {b.get('description')}")

                if b.get("logFileName"):
                    st.caption(f"📁 Log File: `{b.get('logFileName')}`")

                if b.get("stackTrace"):
                    st.markdown("**Stack Trace / Log Output:**")
                    st.code(b.get("stackTrace"), language="java")

                if b.get("status") == "Resolved":
                    st.success(f"**Diagnosed Root Cause:** {b.get('rootCause')}\n\n**Applied Fix:** {b.get('resolution')}\n\n**Resolution Notes:** {b.get('resolutionNotes') or 'N/A'}")
                else:
                    with st.form(f"resolve_form_{b.get('id')}"):
                        st.subheader("Mark Bug as Resolved")
                        rc_in = st.text_input("Diagnosed Root Cause *", value=b.get("rootCause") or "Unchecked null reference / Database connection leak")
                        res_in = st.text_area("Applied Fix *", value="Added null validation checks and defensive error handling.")
                        notes_in = st.text_area("Resolution Notes", value="Verified via unit test execution and verified fix in staging environment.")
                        res_btn = st.form_submit_button("✅ Mark as Resolved")

                        if res_btn:
                            res_obj, err = backend.resolve_bug(b.get("id"), rc_in, res_in, notes_in)
                            if err:
                                st.error(f"Resolution failed: {err}")
                            else:
                                st.success(f"Bug {b.get('id')} marked as Resolved!")
                                st.rerun()

# PAGE 4: AI MENTOR CHAT
elif page == "💬 AI Mentor Chat":
    st.markdown('<div class="section-title">💬 Interactive AI Mentor Conversational Chat</div>', unsafe_allow_html=True)
    st.caption("Ask questions about bug fixes, stack trace interpretation, SQL queries, Git workflows, or software architecture.")

    bugs = backend.get_bugs()
    bug_options = ["General Engineering Advice"] + [f"{b.get('id')}: {b.get('title')}" for b in bugs]
    
    selected_bug_option = st.selectbox("Select Contextual Bug", options=bug_options)
    selected_bug_id = selected_bug_option.split(":")[0] if ":" in selected_bug_option else "BUG-001"

    # Chat history load
    history = backend.get_chat_history(selected_bug_id)

    # Render History
    for msg in history:
        role = "user" if msg.get("sender") == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg.get("message"))

    # Quick prompt shortcuts
    st.markdown("**Quick Prompts:**")
    prompt_cols = st.columns(4)
    quick_prompt = None
    if prompt_cols[0].button("🧪 How to test this?"):
        quick_prompt = "How do I write unit and integration tests to prevent this bug?"
    if prompt_cols[1].button("💡 Simple Explanation"):
        quick_prompt = "Explain the root cause and fix in simple beginner terms with an analogy."
    if prompt_cols[2].button("🔒 Security Audit"):
        quick_prompt = "Are there any security vulnerabilities associated with this stack trace?"
    if prompt_cols[3].button("⚡ Performance Fix"):
        quick_prompt = "How can we optimize performance and prevent memory/connection leaks here?"

    user_input = st.chat_input("Type your debugging question...")
    final_prompt = quick_prompt or user_input

    if final_prompt:
        with st.chat_message("user"):
            st.markdown(final_prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("AI Mentor is analyzing query..."):
                res, err = backend.send_chat_message(selected_bug_id, final_prompt)
                if err:
                    st.error(f"Error getting reply: {err}")
                else:
                    st.markdown(res.get("message"))
                    st.rerun()

# PAGE 5: CODE DOCTOR
elif page == "🩺 Code Doctor":
    st.markdown('<div class="section-title">🩺 Code Doctor Static Analysis Tool</div>', unsafe_allow_html=True)
    st.caption("Perform automated static analysis with 17 anti-pattern rules, health score calculation, and refactoring advice.")

    code_samples = {
        "Custom Code": "",
        "Java - Null Pointer & Resource Leak": """public class OrderProcessor {
    public void process(Order order) {
        // Anti-pattern: Missing null check
        String email = order.getUser().getEmail();
        
        try {
            Connection conn = DriverManager.getConnection("jdbc:sqlite:app.db");
            Statement stmt = conn.createStatement();
            // Anti-pattern: Unparameterized query
            stmt.executeQuery("SELECT * FROM users WHERE email = '" + email + "'");
        } catch(Exception e) {
            // Anti-pattern: Generic catch & swallowed exception
        }
    }
}""",
        "Python - Broad Exception & Hardcoded Secrets": """def query_database(user_input):
    api_key = "secret_12345_hardcoded"  # Security risk
    try:
        sql = "SELECT * FROM items WHERE name = '%s'" % user_input
        execute(sql)
    except Exception:
        pass  # Bare exception pass
"""
    }

    sel_code_sample = st.selectbox("Load Sample Code Snippet", options=list(code_samples.keys()))
    
    code_input = st.text_area(
        "Paste Code Snippet for Audit",
        value=code_samples[sel_code_sample],
        height=220,
        placeholder="Paste Java, Python, or SQL snippet here..."
    )

    if st.button("🩺 Run Code Doctor Audit"):
        if not code_input.strip():
            st.error("Please enter code to audit.")
        else:
            with st.spinner("Running 17 static analysis rules..."):
                audit_res, err = backend.audit_code(code_input)
                if err:
                    st.error(f"Audit failed: {err}")
                else:
                    st.markdown("---")
                    score = audit_res.get("healthScore", 100)
                    score_clr = "#4ade80" if score >= 80 else ("#facc15" if score >= 50 else "#ef4444")
                    
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.8); border: 2px solid {score_clr}; border-radius: 12px; padding: 1.5rem; text-align: center; margin-bottom: 1.5rem;">
                        <div style="font-size: 0.9rem; color: #94a3b8; text-transform: uppercase;">Overall Code Health Score</div>
                        <div style="font-size: 3.5rem; font-weight: 900; color: {score_clr};">{score} / 100</div>
                        <div style="font-size: 1rem; color: #f0f4f8;">{audit_res.get('summary', 'Code audit completed.')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    violations = audit_res.get("violations", [])
                    if not violations:
                        st.success("🎉 Outstanding! No static analysis violations detected.")
                    else:
                        st.subheader(f"⚠️ Detected Rule Violations ({len(violations)})")
                        for v in violations:
                            v_sev = v.get("severity", "Medium")
                            v_badge = render_badge(v_sev, v_sev)
                            
                            st.markdown(f"""
                            <div class="glass-card">
                                <div><strong>Rule [{v.get('ruleId')}]: {v.get('ruleName')}</strong> &nbsp; {v_badge}</div>
                                <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 0.4rem;">{v.get('description')}</div>
                                <div style="font-size: 0.85rem; color: #38bdf8; margin-top: 0.4rem;">💡 <strong>Fix Recommendation:</strong> {v.get('suggestedFix')}</div>
                            </div>
                            """, unsafe_allow_html=True)

# PAGE 6: PLATFORM SETTINGS
elif page == "⚙️ Platform Settings":
    st.markdown('<div class="section-title">⚙️ Platform Settings & Operations</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Database Operations")
    st.caption("Reset the platform database back to initial sample bugs and admin account seed state.")

    if st.button("🔄 Reset Database to Sample Data"):
        success, msg = backend.reset_db()
        if success:
            st.success(msg)
            st.rerun()
        else:
            st.error(f"Reset failed: {msg}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("System Architecture & Status")
    st.markdown(f"- **FastAPI Backend URL:** `{API_BASE_URL}`")
    st.markdown(f"- **Engine Mode:** `{'REST HTTP Client' if backend.use_http else 'Direct Embedded Engine'}`")
    st.markdown("- **Multi-Agent Pipeline Agents:** TriageAgent, LogAnalysisAgent, RootCauseAgent, DuplicateDetectionAgent, RemediationAgent, ChatAgent, CodeReviewAgent")
    st.markdown('</div>', unsafe_allow_html=True)
