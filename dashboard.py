import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from datetime import datetime

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RegWatch — Compliance Dashboard",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# ─── Database Connection ──────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./regwatch.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

def fetch_data(query):
    try:
        return pd.read_sql(query, engine)
    except Exception:
        return pd.DataFrame()

# ─── Custom CSS for Premium Dark Theme ─────────────────────────────────────────
st.markdown("""
<style>
/* ── Import Google Font ─── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global ─── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Hide Streamlit branding ─── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Main container ─── */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* ── Hero header ─── */
.hero-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border: 1px solid rgba(56, 189, 248, 0.15);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero-container::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #06b6d4, #8b5cf6);
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    font-size: 1rem;
    color: #94a3b8;
    margin-top: 0.25rem;
    font-weight: 400;
}
.hero-badge {
    display: inline-block;
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 0.5rem;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

/* ── Metric cards ─── */
.metric-card {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.metric-card:hover {
    border-color: rgba(56, 189, 248, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(56, 189, 248, 0.08);
}
.metric-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
}
.metric-card.blue::after { background: linear-gradient(90deg, #3b82f6, #06b6d4); }
.metric-card.purple::after { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.metric-card.green::after { background: linear-gradient(90deg, #10b981, #34d399); }
.metric-card.amber::after { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.metric-card.red::after { background: linear-gradient(90deg, #ef4444, #f87171); }

.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0.3rem 0;
}
.metric-value.blue { color: #38bdf8; }
.metric-value.purple { color: #a78bfa; }
.metric-value.green { color: #34d399; }
.metric-value.amber { color: #fbbf24; }
.metric-value.red { color: #f87171; }

.metric-label {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.metric-icon {
    font-size: 1.6rem;
    margin-bottom: 0.2rem;
}

/* ── Section headers ─── */
.section-header {
    font-size: 1.3rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 1.5rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-header .accent {
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ── Status pills ─── */
.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.status-done {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.3);
}
.status-pending {
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.3);
}
.status-processing {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
}

/* ── Confidence bar ─── */
.confidence-bar-bg {
    background: rgba(148, 163, 184, 0.1);
    border-radius: 8px;
    height: 8px;
    width: 100%;
    overflow: hidden;
}
.confidence-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.5s ease;
}
.confidence-high { background: linear-gradient(90deg, #10b981, #34d399); }
.confidence-mid { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.confidence-low { background: linear-gradient(90deg, #ef4444, #f87171); }

/* ── Card containers ─── */
.data-card {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid rgba(148, 163, 184, 0.08);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* ── Department badge ─── */
.dept-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 600;
}
.dept-kyc { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25); }
.dept-legal { background: rgba(139, 92, 246, 0.15); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.25); }
.dept-audit { background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.25); }
.dept-it { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.25); }
.dept-default { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.25); }

/* ── MAP item card ─── */
.map-item {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.08);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: all 0.2s ease;
}
.map-item:hover {
    border-color: rgba(56, 189, 248, 0.2);
    background: rgba(30, 41, 59, 0.9);
}
.map-action {
    font-size: 0.88rem;
    color: #cbd5e1;
    line-height: 1.5;
    margin-bottom: 0.5rem;
}
.map-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}
.map-meta-item {
    font-size: 0.72rem;
    color: #64748b;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

/* ── Circular card ─── */
.circular-card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.08);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s ease;
}
.circular-card:hover {
    border-color: rgba(56, 189, 248, 0.2);
}
.circular-title {
    font-size: 0.88rem;
    color: #e2e8f0;
    font-weight: 500;
}
.circular-source {
    font-size: 0.7rem;
    color: #64748b;
    margin-top: 3px;
}

/* ── Pipeline step indicator ─── */
.pipeline-steps {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 1rem 0 1.5rem 0;
    flex-wrap: wrap;
}
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 10px;
    font-size: 0.78rem;
    color: #94a3b8;
    font-weight: 500;
}
.pipeline-step.active {
    border-color: rgba(56, 189, 248, 0.3);
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.08);
}
.pipeline-arrow {
    color: #334155;
    font-size: 1.2rem;
    margin: 0 0.3rem;
}

/* ── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.08);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #e2e8f0;
}

/* ── Audit log table ─── */
.audit-row {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.8rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.06);
    font-size: 0.78rem;
    color: #94a3b8;
}
.audit-event {
    font-weight: 600;
    color: #cbd5e1;
    min-width: 140px;
}

/* ── Fix Streamlit's default dataframe styling ─── */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}

/* ── Tabs styling ─── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ RegWatch")
    st.markdown("---")
    st.markdown("#### 🔍 Filters")

    # Department filter
    departments = fetch_data("SELECT DISTINCT assigned_department FROM maps")
    dept_list = ["All Departments"] + departments['assigned_department'].tolist() if not departments.empty else ["All Departments"]
    selected_dept = st.selectbox("Department", dept_list, index=0)

    # Status filter
    selected_status = st.selectbox("MAP Status", ["All", "pending", "complete"], index=0)

    # Confidence slider
    min_confidence = st.slider("Min Confidence Score", 0.0, 1.0, 0.0, 0.05)

    # Search box
    search_query = st.text_input("🔎 Search MAPs", placeholder="Type to search actions...")

    st.markdown("---")
    st.markdown("#### 📊 Quick Stats")
    
    total_c = fetch_data("SELECT COUNT(*) as c FROM circulars")
    total_m = fetch_data("SELECT COUNT(*) as c FROM maps")
    if not total_c.empty and not total_m.empty:
        st.markdown(f"**{int(total_c['c'][0])}** circulars ingested")
        st.markdown(f"**{int(total_m['c'][0])}** MAPs extracted")
        avg_conf = fetch_data("SELECT AVG(confidence) as avg FROM maps")
        if not avg_conf.empty and avg_conf['avg'][0]:
            st.markdown(f"**{avg_conf['avg'][0]:.0%}** avg confidence")

    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #475569; font-size: 0.7rem; margin-top: 1rem;'>"
        "RegWatch v1.0 — SurakshaCanara<br>"
        f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}"
        "</div>",
        unsafe_allow_html=True
    )


# ─── HERO HEADER ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🛡️ RegWatch Dashboard</div>
    <div class="hero-subtitle">Autonomous Regulatory Compliance Pipeline — Powered by Offline AI</div>
    <div class="hero-badge">● SYSTEM ONLINE — ALL AGENTS ACTIVE</div>
</div>
""", unsafe_allow_html=True)


# ─── PIPELINE FLOW INDICATOR ─────────────────────────────────────────────────
st.markdown("""
<div class="pipeline-steps">
    <div class="pipeline-step active">📡 Watcher</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-step active">🔍 Dedup</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-step active">📋 Extractor</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-step active">🧭 Router</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-step active">🔔 Notifier</div>
</div>
""", unsafe_allow_html=True)


# ─── METRIC CARDS ─────────────────────────────────────────────────────────────
circulars_count = fetch_data("SELECT COUNT(*) as c FROM circulars")
maps_count = fetch_data("SELECT COUNT(*) as c FROM maps")
pending_maps = fetch_data("SELECT COUNT(*) as c FROM maps WHERE status = 'pending'")
done_circulars = fetch_data("SELECT COUNT(*) as c FROM circulars WHERE status = 'done'")
review_count = fetch_data("SELECT COUNT(*) as c FROM human_review_maps WHERE status = 'pending'")

c_val = int(circulars_count['c'][0]) if not circulars_count.empty else 0
m_val = int(maps_count['c'][0]) if not maps_count.empty else 0
p_val = int(pending_maps['c'][0]) if not pending_maps.empty else 0
d_val = int(done_circulars['c'][0]) if not done_circulars.empty else 0
r_val = int(review_count['c'][0]) if not review_count.empty else 0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card blue">
        <div class="metric-icon">📄</div>
        <div class="metric-value blue">{c_val}</div>
        <div class="metric-label">Circulars Ingested</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card purple">
        <div class="metric-icon">📋</div>
        <div class="metric-value purple">{m_val}</div>
        <div class="metric-label">MAPs Extracted</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card green">
        <div class="metric-icon">✅</div>
        <div class="metric-value green">{d_val}</div>
        <div class="metric-label">Circulars Done</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card amber">
        <div class="metric-icon">⏳</div>
        <div class="metric-value amber">{p_val}</div>
        <div class="metric-label">MAPs Pending</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card red">
        <div class="metric-icon">👁️</div>
        <div class="metric-value red">{r_val}</div>
        <div class="metric-label">Needs Review</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋 Mandatory Action Points", "📄 Circulars", "📊 Department Analytics", "⚠️ Human Review Queue"])


# ─── TAB 1: MAPs ─────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">📋 <span class="accent">Mandatory Action Points</span></div>', unsafe_allow_html=True)

    maps_df = fetch_data("""
        SELECT m.id, m.action, m.assigned_department, m.sla_days, m.status, m.confidence, c.title as circular_title
        FROM maps m 
        JOIN circulars c ON m.circular_id = c.id 
        ORDER BY m.id DESC
    """)

    if not maps_df.empty:
        # Apply sidebar filters
        filtered = maps_df.copy()
        if selected_dept != "All Departments":
            filtered = filtered[filtered['assigned_department'] == selected_dept]
        if selected_status != "All":
            filtered = filtered[filtered['status'] == selected_status]
        filtered = filtered[filtered['confidence'] >= min_confidence]
        if search_query:
            filtered = filtered[filtered['action'].str.contains(search_query, case=False, na=False)]

        st.markdown(f"<p style='color: #64748b; font-size: 0.85rem;'>Showing <b style='color: #38bdf8;'>{len(filtered)}</b> of {len(maps_df)} action points</p>", unsafe_allow_html=True)

        def get_dept_class(dept):
            if 'KYC' in str(dept) or 'AML' in str(dept): return 'dept-kyc'
            if 'Legal' in str(dept): return 'dept-legal'
            if 'Audit' in str(dept): return 'dept-audit'
            if 'IT' in str(dept) or 'Tech' in str(dept): return 'dept-it'
            return 'dept-default'

        def get_conf_class(conf):
            if conf >= 0.85: return 'confidence-high'
            if conf >= 0.7: return 'confidence-mid'
            return 'confidence-low'

        for _, row in filtered.iterrows():
            dept_cls = get_dept_class(row['assigned_department'])
            conf_cls = get_conf_class(row['confidence'])
            conf_pct = int(row['confidence'] * 100)
            status_cls = 'status-done' if row['status'] == 'complete' else 'status-pending'

            st.markdown(f"""
            <div class="map-item">
                <div class="map-action">"{row['action']}"</div>
                <div class="map-meta">
                    <span class="dept-badge {dept_cls}">{row['assigned_department']}</span>
                    <span class="status-pill {status_cls}">{row['status']}</span>
                    <span class="map-meta-item">⏱️ SLA: {row['sla_days']} days</span>
                    <span class="map-meta-item">📎 {row['circular_title'][:50]}...</span>
                    <span class="map-meta-item" style="margin-left: auto;">
                        Confidence: {conf_pct}%
                        <div class="confidence-bar-bg" style="width: 60px; display: inline-block; margin-left: 4px; vertical-align: middle;">
                            <div class="confidence-bar-fill {conf_cls}" style="width: {conf_pct}%;"></div>
                        </div>
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No MAPs found. Run `python run_demo.py` first.")


# ─── TAB 2: CIRCULARS ────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">📄 <span class="accent">Ingested Circulars</span></div>', unsafe_allow_html=True)

    circulars_df = fetch_data("SELECT id, title, status, source, created_at FROM circulars ORDER BY created_at DESC")

    if not circulars_df.empty:
        for _, row in circulars_df.iterrows():
            status_cls = 'status-done' if row['status'] == 'done' else ('status-processing' if row['status'] == 'processing' else 'status-pending')
            # Count MAPs for this circular
            map_count_df = fetch_data(f"SELECT COUNT(*) as c FROM maps WHERE circular_id = {row['id']}")
            map_c = int(map_count_df['c'][0]) if not map_count_df.empty else 0

            st.markdown(f"""
            <div class="circular-card">
                <div>
                    <div class="circular-title">{row['title']}</div>
                    <div class="circular-source">Source: {row['source']} &nbsp;|&nbsp; {map_c} MAPs extracted</div>
                </div>
                <div>
                    <span class="status-pill {status_cls}">{row['status']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No circulars found. Run `python run_demo.py` first.")


# ─── TAB 3: DEPARTMENT ANALYTICS ─────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">📊 <span class="accent">Department Analytics</span></div>', unsafe_allow_html=True)

    dept_df = fetch_data("""
        SELECT assigned_department as Department, 
               COUNT(*) as total_maps,
               ROUND(AVG(confidence), 2) as avg_confidence,
               ROUND(AVG(sla_days), 1) as avg_sla
        FROM maps 
        GROUP BY assigned_department
    """)

    if not dept_df.empty:
        # Department distribution chart
        col_chart, col_table = st.columns([3, 2])
        
        with col_chart:
            st.markdown("##### MAPs Distribution by Department")
            st.bar_chart(dept_df.set_index('Department')['total_maps'], color="#38bdf8")

        with col_table:
            st.markdown("##### Department Summary")
            for _, row in dept_df.iterrows():
                dept_cls = get_dept_class(row['Department'])
                st.markdown(f"""
                <div class="map-item" style="margin-bottom: 0.8rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="dept-badge {dept_cls}">{row['Department']}</span>
                        <span style="color: #38bdf8; font-weight: 700; font-size: 1.3rem;">{int(row['total_maps'])}</span>
                    </div>
                    <div class="map-meta" style="margin-top: 0.5rem;">
                        <span class="map-meta-item">📈 Avg Confidence: {row['avg_confidence']:.0%}</span>
                        <span class="map-meta-item">⏱️ Avg SLA: {row['avg_sla']:.0f} days</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Confidence distribution
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Confidence Score Distribution")
        if not maps_df.empty:
            confidence_bins = pd.cut(maps_df['confidence'], bins=[0, 0.7, 0.8, 0.9, 1.0], labels=['< 70%', '70-80%', '80-90%', '90-100%'])
            conf_dist = confidence_bins.value_counts().sort_index()
            st.bar_chart(conf_dist, color="#818cf8")
    else:
        st.info("No department data available.")


# ─── TAB 4: HUMAN REVIEW QUEUE ───────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">⚠️ <span class="accent">Human Review Queue</span></div>', unsafe_allow_html=True)

    review_df = fetch_data("""
        SELECT r.id, c.title, r.confidence, r.status 
        FROM human_review_maps r 
        JOIN circulars c ON r.circular_id = c.id 
        ORDER BY r.confidence ASC
    """)

    if not review_df.empty and len(review_df) > 0:
        for _, row in review_df.iterrows():
            conf_pct = int(row['confidence'] * 100)
            conf_cls = get_conf_class(row['confidence'])
            st.markdown(f"""
            <div class="map-item">
                <div class="map-action" style="font-weight: 500;">📎 {row['title']}</div>
                <div class="map-meta">
                    <span class="status-pill status-pending">{row['status']}</span>
                    <span class="map-meta-item">
                        Confidence: {conf_pct}%
                        <div class="confidence-bar-bg" style="width: 80px; display: inline-block; margin-left: 4px; vertical-align: middle;">
                            <div class="confidence-bar-fill {conf_cls}" style="width: {conf_pct}%;"></div>
                        </div>
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="data-card" style="text-align: center; padding: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✅</div>
            <div style="color: #4ade80; font-weight: 600; font-size: 1.1rem;">All Clear!</div>
            <div style="color: #64748b; font-size: 0.85rem; margin-top: 0.3rem;">
                No items currently require human review. All extractions passed the confidence threshold.
            </div>
        </div>
        """, unsafe_allow_html=True)
