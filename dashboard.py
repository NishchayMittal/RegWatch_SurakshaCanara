import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from sqlalchemy import create_engine
import os
import time
from datetime import datetime, timedelta

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RegWatch — Compliance Console",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="collapsed", # Sidebar hidden
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

# ─── Custom CSS for Brainfish Neo-Brutalist Light Theme ───────────────────────
st.markdown("""
<style>
/* ── Import Google Fonts (Satoshi substitute DM Sans, Inter, Monospace) ─── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap');

/* ── Global Styles & Force High Contrast Black Text ─── */
html, body, [class*="css"], p, span, label, div, select, input, textarea, h1, h2, h3, h4, h5, h6 {
    font-family: 'DM Sans', sans-serif !important;
    color: #000000 !important;
}

/* ── Set All Container Backgrounds to Transparent to Reveal Canvas ─── */
html, body, #root, div[data-testid="stAppViewContainer"],
div[data-testid="stHeader"],
section[data-testid="stMainBlockContainer"],
.stApp, .stMain, section.main {
    background-color: transparent !important;
}

/* ── Hide Streamlit Tab Border Line ─── */
.stTabs [data-testid="stTabBorder"] {
    display: none !important;
}

/* ── Hide Streamlit Sidebar Completely ─── */
section[data-testid="stSidebar"] {
    display: none !important;
}

/* ── Hide Streamlit branding ─── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Main container (Styled as a unified app window card) ─── */
.block-container {
    background-color: #ffffff !important;
    border: 3px solid #000000 !important;
    border-radius: 24px !important;
    box-shadow: 6px 6px 0px 0px #000000 !important;
    padding: 2.2rem !important;
    margin-top: 2.5rem !important;
    margin-bottom: 2rem !important;
    max-width: 1280px !important;
}

/* ── Neo-Brutalist Sticker Cards ─── */
.data-card, .map-item, .circular-card {
    background-color: #ffffff !important;
    border: 2px solid #000000 !important;
    border-radius: 16px !important;
    box-shadow: 3px 3px 0px 0px #000000 !important;
    padding: 1.2rem !important;
    margin-bottom: 1rem !important;
    color: #000000 !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}
.data-card:hover, .map-item:hover, .circular-card:hover {
    transform: translate(-1px, -1px) !important;
    box-shadow: 4px 4px 0px 0px #000000 !important;
    border-color: #000000 !important;
}
.map-item-selected {
    background-color: #fef3c8 !important; /* Buttercream highlight for selected items */
    border: 2.5px solid #000000 !important;
}

/* ── Hero header (Sky Wash) ─── */
.hero-container {
    background-color: #b7eaf6 !important; /* Sky Wash */
    border: 2px solid #000000 !important;
    border-radius: 20px !important;
    padding: 1.2rem 1.8rem !important;
    margin-bottom: 1.2rem !important;
    box-shadow: 4px 4px 0px 0px #000000 !important;
}
.hero-title {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
    color: #000000 !important;
    margin: 0;
    letter-spacing: -0.02em !important;
}
.hero-subtitle {
    font-size: 0.9rem !important;
    color: #333333 !important;
    margin-top: 0.3rem;
    font-weight: 500;
}

/* ── Typography & Headers ─── */
h1, h2, h3, .section-header {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #000000 !important;
}
.section-header {
    font-size: 1.3rem;
    margin: 0.8rem 0 0.6rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-header .accent {
    color: #3366e0 !important; /* Cobalt Field */
    text-decoration: underline;
    text-decoration-color: #a3e635; /* Lime underline */
    text-decoration-thickness: 3px;
}

/* ── Metric cards (Brainfish colors) ─── */
.metric-card {
    border: 2px solid #000000 !important;
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    text-align: center !important;
    box-shadow: 3px 3px 0px 0px #000000 !important;
    color: #000000 !important;
}
.metric-card.blue { background-color: #b7eaf6 !important; }
.metric-card.purple { background-color: #fae9ff !important; }
.metric-card.green { background-color: #d2fae5 !important; }
.metric-card.amber { background-color: #fef3c8 !important; }
.metric-card.red { background-color: #f5d1fe !important; }

.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0.2rem 0;
    font-family: 'DM Sans', sans-serif !important;
    letter-spacing: -0.03em !important;
    color: #000000 !important;
}
.metric-label {
    font-size: 0.68rem;
    color: #222222;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-icon {
    font-size: 1.2rem;
    margin-bottom: 0.1rem;
}

/* ── Neo-Brutalist Badges and Status Pills ─── */
.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: 2px solid #000000 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.status-done {
    background-color: #a3e635 !important;
    color: #000000 !important;
}
.status-pending {
    background-color: #fef3c8 !important;
    color: #000000 !important;
}
.status-processing {
    background-color: #b7eaf6 !important;
    color: #000000 !important;
}

.dept-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 100px;
    font-size: 0.72rem;
    font-weight: 700;
    border: 2px solid #000000 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.dept-kyc { background-color: #b7eaf6 !important; color: #000000 !important; }
.dept-legal { background-color: #fae9ff !important; color: #000000 !important; }
.dept-audit { background-color: #fef3c8 !important; color: #000000 !important; }
.dept-it { background-color: #d2fae5 !important; color: #000000 !important; }
.dept-default { background-color: #ffffff !important; color: #000000 !important; }

/* ── Confidence bar ─── */
.confidence-bar-bg {
    background: #000000;
    border-radius: 100px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    border: 1px solid #000000;
}
.confidence-bar-fill {
    height: 100%;
    border-radius: 100px;
}
.confidence-high { background-color: #a3e635; }
.confidence-mid { background-color: #fbbf25; }
.confidence-low { background-color: #f5d1fe; }

.map-action {
    font-size: 0.95rem;
    color: #000000;
    font-weight: 500;
    line-height: 1.5;
    margin-bottom: 0.6rem;
}
.map-meta {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    flex-wrap: wrap;
}
.map-meta-item {
    font-size: 0.75rem;
    color: #333333;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700;
}

.circular-title {
    font-size: 0.95rem;
    color: #000000;
    font-weight: 700;
}
.circular-source {
    font-size: 0.75rem;
    color: #333333;
    margin-top: 3px;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700;
}

/* ── Form Inputs (Fixed high-contrast white background & black text) ─── */
input, textarea, select, 
div[data-baseweb="input"] input, 
div[data-baseweb="select"] *, 
.stTextArea textarea, 
.stTextInput input, 
.stNumberInput input, 
.stSelectbox div,
.stSelectbox span,
.stSelectbox p,
[data-baseweb="popover"] * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Apply single neobrutalist border only to outer input & select box wrappers */
div[data-baseweb="input"],
div[data-baseweb="select"],
.stTextArea textarea,
.stTextInput input,
.stNumberInput input {
    border: 2px solid #000000 !important;
    border-radius: 4px !important;
}

/* Clear borders & backgrounds on nested inner wrapper elements to prevent double lines or black leak-through */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[role="combobox"] {
    border: none !important;
    background-color: transparent !important;
    background: transparent !important;
}

/* Force solid white backgrounds on outer inputs and select lists */
div[data-baseweb="input"],
div[data-baseweb="select"],
input,
textarea {
    background-color: #ffffff !important;
    background: #ffffff !important;
}

/* Ensure disabled inputs and textareas have high-contrast black text and light background */
textarea:disabled, input:disabled, [disabled], 
.stTextArea textarea:disabled, .stTextInput input:disabled,
div[data-baseweb="input"] input:disabled, textarea[disabled],
.stTextArea textarea[disabled], .stTextInput input[disabled] {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    background-color: #f1f1f1 !important;
    opacity: 1 !important;
    border-color: #000000 !important;
}

/* Style dropdown lists when open */
div[role="listbox"], li[role="option"], li[role="option"] * {
    background-color: #ffffff !important;
    color: #000000 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Ensure option values have black text and white backgrounds */
div[data-baseweb="popover"] * {
    background-color: #ffffff !important;
    color: #000000 !important;
}

/* Custom high-contrast placeholders */
::placeholder, textarea::placeholder, input::placeholder,
.stTextArea textarea::placeholder, .stTextInput input::placeholder {
    color: #555555 !important;
    -webkit-text-fill-color: #555555 !important;
    opacity: 1 !important;
}


/* ── Lime CTA Button & Universal Button Styling (Normal & Form Submit) ─── */
button, [data-testid*="baseButton"] {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #000000 !important;
    border-radius: 100px !important;
    font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 8px 24px !important;
    box-shadow: 2px 2px 0px 0px #000000 !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}
button:hover, [data-testid*="baseButton"]:hover {
    transform: translate(-1px, -1px) !important;
    box-shadow: 3px 3px 0px 0px #000000 !important;
    color: #000000 !important;
}

/* Primary / Active Buttons (Includes active navbar button and submit actions) */
button[kind="primary"], 
button[kind="primaryFormSubmit"], 
[data-testid="baseButton-primary"] {
    background-color: #a3e635 !important;
    box-shadow: 1.5px 1.5px 0px 0px #000000 !important;
}
button[kind="primary"]:hover, 
button[kind="primaryFormSubmit"]:hover, 
[data-testid="baseButton-primary"]:hover {
    box-shadow: 2.5px 2.5px 0px 0px #000000 !important;
}

/* Clickable RegWatch logo anchor link styles */
a[href*="page=home"] {
    color: #000000 !important;
    text-decoration: underline !important;
    text-decoration-color: #a3e635 !important;
    text-decoration-thickness: 3px !important;
    text-underline-offset: 4px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.3rem !important;
    letter-spacing: -0.02em !important;
    display: inline-block !important;
}
a[href*="page=home"]:hover, 
a[href*="page=home"]:visited, 
a[href*="page=home"]:active,
a[href*="page=home"]:focus {
    color: #000000 !important;
    text-decoration: underline !important;
    text-decoration-color: #a3e635 !important;
}


/* Page Border Container wrapping the active workspace container */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff !important;
    border: 3px solid #000000 !important;
    border-radius: 24px !important;
    box-shadow: 6px 6px 0px 0px #000000 !important;
    padding: 2rem !important;
    margin-top: 0.5rem !important;
    margin-bottom: 2.2rem !important;
}
</style>
""", unsafe_allow_html=True)


# ─── JS Interactive Bouncing Neo-Brutalist Sticker Background ─────────────────
# Injected via custom HTML component using window.parent.document to bypass sanitization
js_code = """
<script>
const parentDoc = window.parent.document;
if (!parentDoc.getElementById('particles-canvas')) {
    const canvas = parentDoc.createElement('canvas');
    canvas.id = 'particles-canvas';
    parentDoc.body.insertBefore(canvas, parentDoc.body.firstChild);
    
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
    canvas.style.zIndex = '-99';
    canvas.style.pointerEvents = 'none';
    
    const ctx = canvas.getContext('2d');
    let ripples = [];
    let gradientTime = 0;
    let mouseX = -1000;
    let mouseY = -1000;
    let nodes = [];
    
    const colors = [
        'rgba(183, 234, 246, 0.35)', 
        'rgba(250, 233, 255, 0.35)', 
        'rgba(254, 243, 200, 0.35)', 
        'rgba(210, 250, 229, 0.35)', 
        'rgba(245, 209, 254, 0.35)'
    ];
    const strokeColors = ['#b7eaf6', '#fae9ff', '#fef3c8', '#d2fae5', '#f5d1fe'];
    const labels = ['RBI', 'KYC', 'SLA', 'SEC', 'GO', 'MAP', 'DONE', '100%', '90d', 'AML'];
    
    window.parent.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });
    
    window.parent.addEventListener('mouseleave', () => {
        mouseX = -1000;
        mouseY = -1000;
    });
    
    window.parent.addEventListener('click', (e) => {
        ripples.push({
            x: e.clientX,
            y: e.clientY,
            r: 10,
            alpha: 1.0
        });
    });
    
    function initNodes() {
        nodes = [];
        const count = 34;
        const leftExcl = canvas.width * 0.28;
        const rightExcl = canvas.width * 0.72;
        
        for (let i = 0; i < count; i++) {
            // Generate node strictly outside the center columns
            let rx = Math.random() * canvas.width;
            if (rx > leftExcl && rx < rightExcl) {
                // Push it to left or right flank
                rx = Math.random() < 0.5 ? Math.random() * leftExcl : rightExcl + Math.random() * (canvas.width - rightExcl);
            }
            
            nodes.push({
                x: rx,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.9,
                vy: (Math.random() - 0.5) * 0.9,
                color: colors[i % colors.length],
                strokeColor: strokeColors[i % strokeColors.length],
                labelText: i < labels.length ? labels[i] : null
            });
        }
    }
    
    function resize() {
        canvas.width = window.parent.innerWidth;
        canvas.height = window.parent.innerHeight;
        initNodes();
    }
    window.parent.addEventListener('resize', resize);
    resize();

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const isLoading = parentDoc.querySelector('.loading-screen-container') !== null;
        canvas.style.backgroundColor = 'transparent';
        
        if (isLoading) {
            gradientTime += 0.0025;
            const grad = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
            const r1 = Math.floor(183 + Math.sin(gradientTime) * 15);
            const g1 = Math.floor(234 + Math.cos(gradientTime) * 15);
            const b1 = Math.floor(246 + Math.sin(gradientTime + 1) * 10);
            const r2 = Math.floor(250 + Math.sin(gradientTime * 1.5) * 5);
            const g2 = Math.floor(233 + Math.cos(gradientTime * 1.2) * 10);
            const b2 = Math.floor(255 + Math.sin(gradientTime * 0.8) * 5);
            grad.addColorStop(0, 'rgb(' + r1 + ',' + g1 + ',' + b1 + ')');
            grad.addColorStop(1, 'rgb(' + r2 + ',' + g2 + ',' + b2 + ')');
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            const leftExcl = canvas.width * 0.28;
            const rightExcl = canvas.width * 0.72;
            const topExcl = canvas.height * 0.16;
            const botExcl = canvas.height * 0.76;
            
            // 1. Process node updates and deflector shield bounces
            for (let i = 0; i < nodes.length; i++) {
                let n = nodes[i];
                n.x += n.vx;
                n.y += n.vy;
                
                // Cursor evasion force
                if (mouseX > 0 && mouseY > 0) {
                    const dx = n.x - mouseX;
                    const dy = n.y - mouseY;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist < 170 && dist > 0.1) {
                        const force = (1.0 - dist / 170) * 0.55;
                        n.vx += (dx / dist) * force;
                        n.vy += (dy / dist) * force;
                    }
                }
                
                n.vx *= 0.96;
                n.vy *= 0.96;
                
                const speed = Math.sqrt(n.vx*n.vx + n.vy*n.vy);
                if (speed < 0.25) {
                    n.vx += (Math.random() - 0.5) * 0.35;
                    n.vy += (Math.random() - 0.5) * 0.35;
                }
                if (speed > 1.8) {
                    n.vx = (n.vx / speed) * 1.5;
                    n.vy = (n.vy / speed) * 1.5;
                }
                
                // Outer boundaries
                if (n.x < 15) { n.x = 15; n.vx *= -1; }
                if (n.x > canvas.width - 15) { n.x = canvas.width - 15; n.vx *= -1; }
                if (n.y < 15) { n.y = 15; n.vy *= -1; }
                if (n.y > canvas.height - 15) { n.y = canvas.height - 15; n.vy *= -1; }
                
                // Center box boundaries (Deflector Shield)
                if (n.x > leftExcl && n.x < rightExcl && n.y > topExcl && n.y < botExcl) {
                    const dL = n.x - leftExcl;
                    const dR = rightExcl - n.x;
                    const dT = n.y - topExcl;
                    const dB = botExcl - n.y;
                    const minDist = Math.min(dL, dR, dT, dB);
                    
                    if (minDist === dL) {
                        n.x = leftExcl - 2;
                        n.vx = -Math.abs(n.vx) * 0.9;
                    } else if (minDist === dR) {
                        n.x = rightExcl + 2;
                        n.vx = Math.abs(n.vx) * 0.9;
                    } else if (minDist === dT) {
                        n.y = topExcl - 2;
                        n.vy = -Math.abs(n.vy) * 0.9;
                    } else {
                        n.y = botExcl + 2;
                        n.vy = Math.abs(n.vy) * 0.9;
                    }
                }
            }
            
            // Helper to block lines crossing through the center area
            const isCrossingCenter = (p1, p2) => {
                const midX = (p1.x + p2.x) / 2;
                const midY = (p1.y + p2.y) / 2;
                const q1x = p1.x * 0.75 + p2.x * 0.25;
                const q1y = p1.y * 0.75 + p2.y * 0.25;
                const q2x = p1.x * 0.25 + p2.x * 0.75;
                const q2y = p1.y * 0.25 + p2.y * 0.75;
                
                const checkPt = (x, y) => (x > leftExcl && x < rightExcl && y > topExcl && y < botExcl);
                return checkPt(midX, midY) || checkPt(q1x, q1y) || checkPt(q2x, q2y);
            };
            
            // 2. Draw crystal shard triangles
            const connectionLimit = 170;
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx1 = nodes[i].x - nodes[j].x;
                    const dy1 = nodes[i].y - nodes[j].y;
                    const dist1 = Math.sqrt(dx1*dx1 + dy1*dy1);
                    
                    if (dist1 < connectionLimit && !isCrossingCenter(nodes[i], nodes[j])) {
                        for (let k = j + 1; k < nodes.length; k++) {
                            const dx2 = nodes[j].x - nodes[k].x;
                            const dy2 = nodes[j].y - nodes[k].y;
                            const dist2 = Math.sqrt(dx2*dx2 + dy2*dy2);
                            
                            const dx3 = nodes[k].x - nodes[i].x;
                            const dy3 = nodes[k].y - nodes[i].y;
                            const dist3 = Math.sqrt(dx3*dx3 + dy3*dy3);
                            
                            if (dist2 < connectionLimit && dist3 < connectionLimit && 
                                !isCrossingCenter(nodes[j], nodes[k]) && 
                                !isCrossingCenter(nodes[k], nodes[i])) {
                                
                                ctx.fillStyle = nodes[i].color;
                                ctx.beginPath();
                                ctx.moveTo(nodes[i].x, nodes[i].y);
                                ctx.lineTo(nodes[j].x, nodes[j].y);
                                ctx.lineTo(nodes[k].x, nodes[k].y);
                                ctx.closePath();
                                ctx.fill();
                                
                                ctx.strokeStyle = 'rgba(0, 0, 0, 0.04)';
                                ctx.lineWidth = 1.0;
                                ctx.stroke();
                            }
                        }
                    }
                }
            }
            
            // 3. Draw connection lines
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.085)';
            ctx.lineWidth = 1.2;
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[i].x - nodes[j].x;
                    const dy = nodes[i].y - nodes[j].y;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist < connectionLimit && !isCrossingCenter(nodes[i], nodes[j])) {
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.stroke();
                    }
                }
            }
            
            // 4. Draw node dots and float labels
            nodes.forEach(n => {
                ctx.fillStyle = '#000000';
                ctx.beginPath();
                ctx.arc(n.x, n.y, 2.5, 0, Math.PI * 2);
                ctx.fill();
                
                if (n.labelText) {
                    ctx.save();
                    ctx.translate(n.x + 10, n.y - 12);
                    
                    const text = n.labelText;
                    ctx.font = '800 8.5px "JetBrains Mono", monospace';
                    const tw = ctx.measureText(text).width + 8;
                    const th = 13;
                    
                    ctx.fillStyle = '#000000';
                    ctx.fillRect(1.5, 1.5, tw, th);
                    
                    ctx.fillStyle = '#ffffff';
                    ctx.strokeStyle = '#000000';
                    ctx.lineWidth = 1.5;
                    ctx.fillRect(0, 0, tw, th);
                    ctx.strokeRect(0, 0, tw, th);
                    
                    ctx.fillStyle = '#000000';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(text, tw / 2, th / 2);
                    ctx.restore();
                }
            });
            
        } else {
            ctx.fillStyle = '#fafaf9';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.035)';
            ctx.lineWidth = 1.0;
            const gridSpacing = 35;
            
            for (let x = 0; x < canvas.width; x += gridSpacing) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }
            
            for (let y = 0; y < canvas.height; y += gridSpacing) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }
        }
        
        requestAnimationFrame(draw);
    }
    draw();
}
</script>
"""
components.html(js_code, height=0, width=0)
st.markdown("<br>", unsafe_allow_html=True)


# ─── SESSION STATE & LOADING PAGE ─────────────────────────────────────────────
if "entered_dashboard" not in st.session_state:
    st.session_state.entered_dashboard = True
if "active_page" not in st.session_state:
    st.session_state.active_page = "home"
if "page" in st.query_params:
    st.session_state.active_page = st.query_params["page"]
if "selected_map_id" not in st.session_state:
    st.session_state.selected_map_id = None
if "map_page" not in st.session_state:
    st.session_state.map_page = 1
if "circular_page" not in st.session_state:
    st.session_state.circular_page = 1
if "search_page" not in st.session_state:
    st.session_state.search_page = 1
if "prev_dept" not in st.session_state:
    st.session_state.prev_dept = ""
if "prev_status" not in st.session_state:
    st.session_state.prev_status = ""
if "prev_conf" not in st.session_state:
    st.session_state.prev_conf = 0.0
if "prev_search" not in st.session_state:
    st.session_state.prev_search = ""
if "prev_search_query" not in st.session_state:
    st.session_state.prev_search_query = ""
if "prev_search_dept" not in st.session_state:
    st.session_state.prev_search_dept = ""
if "prev_search_status" not in st.session_state:
    st.session_state.prev_search_status = ""
if "prev_search_sla" not in st.session_state:
    st.session_state.prev_search_sla = 0.0



# ─── TOP NAVIGATION NAVBAR ────────────────────────────────────────────────────
if st.session_state.active_page != "home":
    nav_cols = st.columns([1.0, 1.0, 1.0, 1.0, 1.0])
    
    with nav_cols[0]:
        st.markdown("""
        <div style="height: 40px; display: flex; align-items: center; justify-content: flex-start; margin-top: 2px;">
            <a href="/?page=home" target="_self" style="font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 1.3rem; color: #000000 !important; text-decoration: underline !important; text-decoration-color: #a3e635 !important; text-decoration-thickness: 3px !important;">RegWatch</a>
        </div>
        """, unsafe_allow_html=True)
        
    with nav_cols[1]:
        btn_type = "primary" if st.session_state.active_page == "maps" else "secondary"
        if st.button("Action Points", type=btn_type, use_container_width=True, key="nav_btn_maps"):
            st.session_state.active_page = "maps"
            st.query_params.clear()
            st.rerun()
            
    with nav_cols[2]:
        btn_type = "primary" if st.session_state.active_page == "review" else "secondary"
        if st.button("Human Review", type=btn_type, use_container_width=True, key="nav_btn_review"):
            st.session_state.active_page = "review"
            st.query_params.clear()
            st.rerun()
            
    with nav_cols[3]:
        btn_type = "primary" if st.session_state.active_page == "circulars" else "secondary"
        if st.button("Circulars List", type=btn_type, use_container_width=True, key="nav_btn_circulars"):
            st.session_state.active_page = "circulars"
            st.query_params.clear()
            st.rerun()
            
    with nav_cols[4]:
        btn_type = "primary" if st.session_state.active_page == "search" else "secondary"
        if st.button("Search MAPs", type=btn_type, use_container_width=True, key="nav_btn_search"):
            st.session_state.active_page = "search"
            st.query_params.clear()
            st.rerun()
    
    # Divider line
    st.markdown("<hr style='border: 1px solid #000000; margin-top: 0.5rem; margin-bottom: 1.2rem;'/>", unsafe_allow_html=True)




# ─── SHARED METRIC CALCULATIONS ───────────────────────────────────────────────
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


# ─── HELPER BADGE FUNCTIONS ───────────────────────────────────────────────────
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


# ─── VIEW ROUTER ──────────────────────────────────────────────────────────────

# ─── VIEW 0: HOME LANDING VIEW ────────────────────────────────────────────────
if st.session_state.active_page == "home":
    
    # Frameless overlay style override for home page only
    st.markdown("""
    <style>
    .block-container {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Centered welcome loading container
    st.markdown("""
    <div class="loading-screen-container" style="margin-top: 8vh; display: flex; flex-direction: column; align-items: center; text-align: center;">
        <!-- Eyebrow Tag -->
        <div style="background-color: #ffffff; border: 2px solid #000000; border-radius: 100px; padding: 6px 16px; font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 0.8rem; color: #000000; display: inline-block; margin-bottom: 2rem; box-shadow: 2px 2px 0px 0px #000000;">
            THE COMPLIANCE LAYER FOR BANCO
        </div>
        <!-- Display Headline -->
        <div style="font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 4rem; color: #000000; line-height: 1.15; letter-spacing: -0.04em; max-width: 800px; margin-bottom: 1.5rem; text-align: center;">
            Your compliance isn't up to date. <span style="background-color: #a3e635; padding: 0px 14px; border: 2px solid #000000; border-radius: 12px; display: inline-block; box-shadow: 2px 2px 0px 0px #000000;">RegWatch</span> fixes that.
        </div>
        <!-- Subtitle Description -->
        <div style="font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #222222; line-height: 1.5; max-width: 620px; margin-bottom: 3rem; text-align: center; font-weight: 500;">
            RegWatch builds living regulatory knowledge, routed and validated personally across bank departments. No missed deadlines, 100% offline security.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Launch CTA Button centered
    l_col1, l_col2, l_col3 = st.columns([1.5, 1, 1.5])
    with l_col2:
        if st.button("Launch Compliance Console", use_container_width=True, key="home_launch_btn"):
            st.session_state.active_page = "maps"
            st.query_params.clear()
            st.rerun()



# ─── VIEW 1: MANDATORY ACTION POINTS DIRECTORY (With Split Details Panel) ──────
elif st.session_state.active_page == "maps":
    
    # Hero Info Header
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">Mandatory Action Points Console</div>
        <div class="hero-subtitle">Operational compliance items extracted from circulars, routed to departments.</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1.5, 2.5])
    
    # Left column: Filters, Metrics & Logs
    with col_left:
        st.markdown('<div class="section-header">Filter and <span class="accent">Configure</span></div>', unsafe_allow_html=True)
        
        # Filters inside left column
        departments = fetch_data("SELECT DISTINCT assigned_department FROM maps")
        dept_list = ["All Departments"] + departments['assigned_department'].tolist() if not departments.empty else ["All Departments"]
        selected_dept = st.selectbox("Department", dept_list, index=0)
        selected_status = st.selectbox("MAP Status", ["All", "pending", "complete"], index=0)
        min_confidence = st.slider("Min Confidence Score", 0.0, 1.0, 0.0, 0.05)
        search_query = st.text_input("Quick Filter", placeholder="Type to narrow down list...")
        
        # Metrics Grid
        st.markdown('<div class="section-header">Compliance <span class="accent">Metrics</span></div>', unsafe_allow_html=True)
        st.markdown(f"""
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 1rem;">
<div class="metric-card blue">
<div class="metric-value">{c_val}</div>
<div class="metric-label">Circulars</div>
</div>
<div class="metric-card purple">
<div class="metric-value">{m_val}</div>
<div class="metric-label">MAPs</div>
</div>
<div class="metric-card green">
<div class="metric-value">{d_val}</div>
<div class="metric-label">Done</div>
</div>
<div class="metric-card red">
<div class="metric-value">{r_val}</div>
<div class="metric-label">Needs Review</div>
</div>
</div>
""", unsafe_allow_html=True)

        # Audit Logs
        st.markdown('<div class="section-header">Compliance <span class="accent">Logs</span></div>', unsafe_allow_html=True)
        audit_df = fetch_data("SELECT event as event_type, details as description, created_at FROM audit_log ORDER BY created_at DESC LIMIT 4")
        if not audit_df.empty:
            for _, log in audit_df.iterrows():
                st.markdown(f"""
                <div style="padding: 0.5rem 0.8rem; background-color: #ffffff; border: 2px solid #000000; border-radius: 8px; margin-bottom: 0.4rem; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; box-shadow: 2px 2px 0px 0px #000000; color: #000000;">
                    <div style="font-weight: 700; color: #3366e0;">[{log['event_type'].upper()}]</div>
                    <div style="color: #222222; margin-top: 0.2rem; font-weight: 500;">{log['description']}</div>
                </div>
                """, unsafe_allow_html=True)

    # Right column: Split Details Panel & Scrollable List
    with col_right:
        inner_list, inner_details = st.columns([1.1, 0.9])
        
        # Load maps data
        maps_df = fetch_data("""
            SELECT m.id, m.action, m.assigned_department, m.sla_days, m.status, m.confidence, c.title as circular_title
            FROM maps m 
            JOIN circulars c ON m.circular_id = c.id 
            ORDER BY m.id DESC
        """)
        
        filtered = maps_df.copy()
        if not maps_df.empty:
            if selected_dept != "All Departments":
                filtered = filtered[filtered['assigned_department'] == selected_dept]
            if selected_status != "All":
                filtered = filtered[filtered['status'] == selected_status]
            filtered = filtered[filtered['confidence'] >= min_confidence]
            if search_query:
                filtered = filtered[filtered['action'].str.contains(search_query, case=False, na=False, regex=False)]
                
        # Reset to page 1 if any filter changed
        if (st.session_state.prev_dept != selected_dept or
            st.session_state.prev_status != selected_status or
            st.session_state.prev_conf != min_confidence or
            st.session_state.prev_search != search_query):
            st.session_state.map_page = 1
            st.session_state.prev_dept = selected_dept
            st.session_state.prev_status = selected_status
            st.session_state.prev_conf = min_confidence
            st.session_state.prev_search = search_query

        # Pagination calculations
        items_per_page = 3
        total_items = len(filtered)
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        
        if st.session_state.map_page > total_pages:
            st.session_state.map_page = total_pages
        if st.session_state.map_page < 1:
            st.session_state.map_page = 1
            
        start_idx = (st.session_state.map_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = filtered.iloc[start_idx:end_idx] if not filtered.empty else filtered

        # Inner Left: List of MAP cards
        with inner_list:
            st.markdown('<div class="section-header">Obligations List</div>', unsafe_allow_html=True)
            if not filtered.empty:
                st.markdown(f"<p style='color: #333333; font-size: 0.75rem; font-weight: 700; font-family: \"JetBrains Mono\", monospace; margin-bottom: 0.5rem;'>Filtered: {total_items} items (Page {st.session_state.map_page}/{total_pages})</p>", unsafe_allow_html=True)
                for _, row in page_items.iterrows():
                    dept_cls = get_dept_class(row['assigned_department'])
                    status_cls = 'status-done' if row['status'] == 'complete' else 'status-pending'
                    status_text = 'COMPLETE' if row['status'] == 'complete' else 'PENDING'
                    
                    is_selected = int(row['id']) == st.session_state.selected_map_id
                    card_cls = "map-item-selected" if is_selected else ""
                    
                    st.markdown(f"""
                    <div class="map-item {card_cls}" style="margin-bottom: 0.4rem; padding: 1rem !important;">
                        <div class="map-action" style="font-size: 0.88rem; font-weight: 700;">"{row['action'][:100]}..."</div>
                        <div class="map-meta">
                            <span class="dept-badge {dept_cls}">{row['assigned_department']}</span>
                            <span class="status-pill {status_cls}">{status_text}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Details and Evidence", key=f"sel_{row['id']}", use_container_width=True):
                        st.session_state.selected_map_id = int(row['id'])
                        st.rerun()
                
                # Pagination controls row
                st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)
                if st.button("Prev", disabled=(st.session_state.map_page <= 1), use_container_width=True, key="prev_page_btn"):
                    st.session_state.map_page -= 1
                    st.rerun()
                st.markdown(f"<div style='text-align: center; font-weight: 700; font-family: \"JetBrains Mono\", monospace; font-size: 0.72rem; padding: 5px 0;'>Page {st.session_state.map_page} of {total_pages}</div>", unsafe_allow_html=True)
                if st.button("Next", disabled=(st.session_state.map_page >= total_pages), use_container_width=True, key="next_page_btn"):
                    st.session_state.map_page += 1
                    st.rerun()
            else:
                st.info("No matching action points found.")
                
        # Inner Right: Details Card & Submission form (Fixed, no visual layout glitches!)
        with inner_details:
            st.markdown('<div class="section-header">Compliance Review</div>', unsafe_allow_html=True)
            if st.session_state.selected_map_id:
                # Fetch details for the selected MAP
                selected_row = maps_df[maps_df['id'] == st.session_state.selected_map_id]
                if not selected_row.empty:
                    row = selected_row.iloc[0]
                    dept_cls = get_dept_class(row['assigned_department'])
                    conf_pct = int(row['confidence'] * 100)
                    conf_cls = get_conf_class(row['confidence'])
                    status_cls = 'status-done' if row['status'] == 'complete' else 'status-pending'
                    status_text = 'COMPLETE' if row['status'] == 'complete' else 'PENDING'
                    
                    # Details Header Card
                    st.markdown(f"""
                    <div class="data-card" style="margin-bottom: 1rem; border-color: #000000; box-shadow: 2px 2px 0px #000000;">
                        <div style="font-weight: 700; font-size: 0.95rem; line-height: 1.4; color: #000000; margin-bottom: 0.8rem;">"{row['action']}"</div>
                        <div class="map-meta" style="margin-bottom: 0.6rem;">
                            <span class="dept-badge {dept_cls}">{row['assigned_department']}</span>
                            <span class="status-pill {status_cls}">{status_text}</span>
                        </div>
                        <div class="map-meta-item">SLA Deadline: <b>{row['sla_days']} days</b></div>
                        <div class="map-meta-item">Ingested Title: <b>{row['circular_title']}</b></div>
                        <div class="map-meta-item" style="margin-top: 0.4rem;">
                            Extraction Confidence: <b>{conf_pct}%</b>
                            <div class="confidence-bar-bg" style="width: 100%; height: 6px; margin-top: 3px;">
                                <div class="confidence-bar-fill {conf_cls}" style="width: {conf_pct}%;"></div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Submission History logs
                    ev_df = fetch_data(f"SELECT * FROM evidence WHERE map_id = {row['id']} ORDER BY submitted_at DESC")
                    if not ev_df.empty:
                        st.markdown("##### Upload History")
                        for _, ev in ev_df.iterrows():
                            ev_status_cls = 'status-done' if ev['status'] == 'accepted' else 'status-pending'
                            st.markdown(f"""
                            <div style="padding: 0.6rem 0.8rem; background-color: #f9f9f9; border: 2px solid #000000; border-radius: 8px; margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; box-shadow: 2px 2px 0px #000000; color: #000000;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="font-weight: 700;">Dept: {ev['submitted_by']}</span>
                                    <span class="status-pill {ev_status_cls}">{ev['status']}</span>
                                </div>
                                <div style="color: #222222; margin-top: 0.3rem;">{ev['description']}</div>
                                <div style="color: #3366e0; margin-top: 0.3rem; text-decoration: underline;">
                                    <a href="{ev['file_url']}" target="_blank">{ev['file_url'][:30]}...</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Submit Form
                    if row['status'] != 'complete':
                        st.markdown("##### Upload Evidence")
                        with st.form(key=f"evidence_form_col_{row['id']}"):
                            desc = st.text_area("Compliance Description", placeholder="Minimum 50 characters detailing compliance steps taken...", key=f"desc_{row['id']}")
                            file_url = st.text_input("Supporting Document URL", placeholder="https://internal.bank/policy.pdf", key=f"file_{row['id']}")
                            submitted_by = st.text_input("Approving Department", value=row['assigned_department'], key=f"by_{row['id']}")
                            
                            submit_btn = st.form_submit_button(label="Submit Evidence", use_container_width=True)
                            
                            if submit_btn:
                                if not desc or len(desc.strip()) < 10:
                                    st.error("Please enter a valid description (at least 10 characters).")
                                else:
                                    from app.agents.validator import ValidatorAgent, ValidatorConfig
                                    from app.db.models import MAPItem, Evidence, AuditLog
                                    from sqlalchemy.orm import sessionmaker
                                    
                                    validator = ValidatorAgent(ValidatorConfig(min_description_len=50))
                                    Session = sessionmaker(bind=engine)
                                    session = Session()
                                    try:
                                        map_item = session.query(MAPItem).filter(MAPItem.id == int(row['id'])).first()
                                        val_res = validator.validate(desc, file_url)
                                        
                                        evidence = Evidence(
                                            map_id=map_item.id,
                                            description=desc,
                                            file_url=file_url,
                                            submitted_by=submitted_by,
                                            status="accepted" if val_res.is_valid else "rejected",
                                            missing_items=None if val_res.is_valid else val_res.feedback,
                                            created_at=datetime.utcnow()
                                        )
                                        session.add(evidence)
                                        
                                        if val_res.is_valid:
                                            map_item.status = "complete"
                                            log_event = "evidence_accepted"
                                            log_msg = f"Evidence accepted for MAP {map_item.id}."
                                            st.success("Evidence accepted! Status updated to COMPLETE.")
                                        else:
                                            map_item.status = "evidence_incomplete"
                                            log_event = "evidence_rejected"
                                            log_msg = f"Evidence rejected for MAP {map_item.id}."
                                            old_sla = map_item.sla_days
                                            map_item.sla_days = max(1, old_sla // 2)
                                            st.error("Evidence rejected. SLA reduced.")
                                            
                                        audit = AuditLog(
                                            event=log_event,
                                            details=log_msg,
                                            created_at=datetime.utcnow()
                                        )
                                        session.add(audit)
                                        session.commit()
                                        
                                        time.sleep(0.5)
                                        st.rerun()
                                    except Exception as ex:
                                        session.rollback()
                                        st.error(f"Database error: {ex}")
                                    finally:
                                        session.close()
            else:
                st.markdown("""
                <div class="data-card" style="text-align: center; padding: 2rem; border-style: dashed;">
                    <div style="font-weight: 700; color: #222222; font-size: 0.9rem;">No Selection</div>
                    <div style="font-size: 0.78rem; color: #555555; margin-top: 0.2rem;">
                        Select a Mandatory Action Point card from the left list to view compliance metrics, history records, and submit evidence.
                    </div>
                </div>
                """, unsafe_allow_html=True)



# ─── VIEW 2: HUMAN REVIEW WORKSPACE ──────────────────────────────────────────
elif st.session_state.active_page == "review":
    
    st.markdown("""
    <div class="hero-container" style="background-color: #f5d1fe !important;">
        <div class="hero-title">Human Review Queue</div>
        <div class="hero-subtitle">Adjust obligation details, select departments, and route low-confidence extractions.</div>
    </div>
    """, unsafe_allow_html=True)
    
    review_df = fetch_data("""
        SELECT r.id, c.id as circular_id, c.title, c.raw_text, r.confidence, r.status 
        FROM human_review_maps r 
        JOIN circulars c ON r.circular_id = c.id 
        WHERE r.status = 'pending'
        ORDER BY r.confidence ASC
    """)
    
    if not review_df.empty:
        options = {f"ID {row['id']}: {row['title']} (Confidence: {int(row['confidence']*100)}%)": row for _, row in review_df.iterrows()}
        selected_option = st.selectbox("Select Circular for Review", list(options.keys()))
        selected_row = options[selected_option]
        
        col_left_text, col_right_form = st.columns([1, 1])
        
        with col_left_text:
            st.markdown("##### Source Circular Text")
            st.text_area("Raw Text View", value=selected_row['raw_text'], height=420, disabled=True, key=f"raw_view_{selected_row['id']}")
            
        with col_right_form:
            st.markdown("##### AI Extraction Routing Form")
            
            default_action = ""
            if "verify credit history" in selected_row['raw_text'].lower():
                default_action = "Banks are advised to verify credit history of borrowers before extending large commercial loans."
            else:
                default_action = "Describe the compliance mandate details here..."
                
            with st.form(key=f"review_form_{selected_row['id']}"):
                action_text = st.text_area("Compliance Obligation Action", value=default_action, height=150)
                
                departments_list = ["Credit Risk", "KYC / AML", "IT & Cybersecurity", "Treasury & Investments", "Retail Banking Compliance", "HR & Conduct", "Legal & Regulatory Affairs", "Audit & Inspection"]
                assigned_dept = st.selectbox("Assigned Department", departments_list, index=0)
                sla_days = st.number_input("SLA Days (Deadline)", min_value=1, max_value=360, value=7)
                
                approve_btn = st.form_submit_button("Approve and Route Task", use_container_width=True)
                
                if approve_btn:
                    if not action_text or len(action_text.strip()) < 10:
                        st.error("Please enter a valid compliance obligation description.")
                    else:
                        from app.db.models import MAPItem, Task, AuditLog, Circular, HumanReviewMap
                        from sqlalchemy.orm import sessionmaker
                        from datetime import datetime, timedelta
                        
                        Session = sessionmaker(bind=engine)
                        session = Session()
                        try:
                            map_item = MAPItem(
                                circular_id=int(selected_row['circular_id']),
                                action=action_text,
                                assigned_department=assigned_dept,
                                sla_days=int(sla_days),
                                status="pending",
                                confidence=0.95,
                                created_at=datetime.utcnow()
                            )
                            session.add(map_item)
                            session.flush()
                            
                            due_date = datetime.utcnow() + timedelta(days=int(sla_days))
                            from app.db.models import Department
                            dept_rec = session.query(Department).filter(Department.name == assigned_dept).first()
                            dept_id = dept_rec.id if dept_rec else None

                            task_item = Task(
                                map_id=map_item.id,
                                department_id=dept_id,
                                status="pending",
                                due_at=due_date,
                                assigned_at=datetime.utcnow()
                            )
                            session.add(task_item)
                            
                            hr_map = session.query(HumanReviewMap).filter(HumanReviewMap.id == int(selected_row['id'])).first()
                            hr_map.status = "approved"
                            
                            circular = session.query(Circular).filter(Circular.id == int(selected_row['circular_id'])).first()
                            circular.status = "done"
                            
                            audit = AuditLog(
                                event="human_review_approved",
                                details=f"Human approved MAP {map_item.id} for Circular {circular.id}.",
                                created_at=datetime.utcnow()
                            )
                            session.add(audit)
                            session.commit()
                            
                            st.success("Compliance task approved and routed successfully!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as ex:
                            session.rollback()
                            st.error(f"Database error: {ex}")
                        finally:
                            session.close()
    else:
        st.markdown("""
        <div class="data-card" style="text-align: center; padding: 3rem; background-color: #ffffff !important; border: 2px solid #000000 !important; box-shadow: 3px 3px 0px 0px #000000 !important;">
            <div style="color: #a3e635; font-weight: 700; font-size: 1.3rem; font-family: 'DM Sans', sans-serif;">All Clear!</div>
            <div style="color: #222222; font-size: 0.88rem; margin-top: 0.3rem; font-weight: 700;">
                No items currently require human review. All extractions passed the confidence threshold.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─── VIEW 3: INGESTED CIRCULARS DIRECTORY ──────────────────────────────────────
elif st.session_state.active_page == "circulars":
    
    st.markdown("""
    <div class="hero-container" style="background-color: #fae9ff !important;">
        <div class="hero-title">Ingested Circulars List</div>
        <div class="hero-subtitle">List of raw files and regulatory documents parsed into the compliance system.</div>
    </div>
    """, unsafe_allow_html=True)
    
    circulars_df = fetch_data("SELECT id, title, status, source, created_at FROM circulars ORDER BY created_at DESC")
    
    if not circulars_df.empty:
        # Pagination calculations for circulars
        c_items_per_page = 3
        c_total_items = len(circulars_df)
        c_total_pages = max(1, (c_total_items + c_items_per_page - 1) // c_items_per_page)
        
        if st.session_state.circular_page > c_total_pages:
            st.session_state.circular_page = c_total_pages
        if st.session_state.circular_page < 1:
            st.session_state.circular_page = 1
            
        c_start_idx = (st.session_state.circular_page - 1) * c_items_per_page
        c_end_idx = c_start_idx + c_items_per_page
        c_page_items = circulars_df.iloc[c_start_idx:c_end_idx]
        
        st.markdown(f"<p style='color: #333333; font-size: 0.75rem; font-weight: 700; font-family: \"JetBrains Mono\", monospace; margin-bottom: 0.5rem;'>Showing {len(c_page_items)} of {c_total_items} items (Page {st.session_state.circular_page}/{c_total_pages})</p>", unsafe_allow_html=True)
        
        for _, row in c_page_items.iterrows():
            status_cls = 'status-done' if row['status'] == 'done' else ('status-processing' if row['status'] == 'processing' else 'status-pending')
            map_count_df = fetch_data(f"SELECT COUNT(*) as c FROM maps WHERE circular_id = {row['id']}")
            map_c = int(map_count_df['c'][0]) if not map_count_df.empty else 0
            
            st.markdown(f"""
            <div class="circular-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="circular-title">{row['title']}</div>
                        <div class="circular-source">Source: {row['source']} &nbsp;|&nbsp; {map_c} MAPs extracted</div>
                    </div>
                    <div>
                        <span class="status-pill {status_cls}">{row['status']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Pagination buttons
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        c_col1, c_col2, c_col3 = st.columns([1, 2, 1])
        with c_col1:
            if st.button("Prev", disabled=(st.session_state.circular_page <= 1), use_container_width=True, key="c_prev_page"):
                st.session_state.circular_page -= 1
                st.rerun()
        with c_col2:
            st.markdown(f"<div style='text-align: center; font-weight: 700; font-family: \"JetBrains Mono\", monospace; font-size: 0.75rem; height: 35px; display: flex; align-items: center; justify-content: center;'>Page {st.session_state.circular_page} of {c_total_pages}</div>", unsafe_allow_html=True)
        with c_col3:
            if st.button("Next", disabled=(st.session_state.circular_page >= c_total_pages), use_container_width=True, key="c_next_page"):
                st.session_state.circular_page += 1
                st.rerun()
# ─── VIEW 4: SEPARATE MAP SEARCH DIRECTORY ────────────────────────────────────
elif st.session_state.active_page == "search":
    
    st.markdown("""
    <div class="hero-container" style="background-color: #fef3c8 !important;">
        <div class="hero-title">Global Map Search</div>
        <div class="hero-subtitle">Full-text query index matching circular actions, timelines, and departments.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Wide Search Box
    q_search = st.text_input("Search compliance obligations database...", placeholder="Type keywords e.g. 'audits', 'KYC', 'interest rates'...", key="g_search_input")
    
    # Render departments list for search page
    departments = fetch_data("SELECT DISTINCT assigned_department FROM maps")
    dept_list = ["All Departments"] + departments['assigned_department'].tolist() if not departments.empty else ["All Departments"]

    col_sf1, col_sf2, col_sf3 = st.columns(3)
    with col_sf1:
        s_dept = st.selectbox("Department Filter", dept_list, key="s_dept")
    with col_sf2:
        s_stat = st.selectbox("Obligation Status", ["All", "pending", "complete"], key="s_stat")
    with col_sf3:
        s_sla = st.number_input("Max SLA Timeline (Days)", min_value=1, max_value=360, value=360, key="s_sla")
        
    st.markdown("---")
    
    # Reset to page 1 if any filter changed
    if (st.session_state.prev_search_query != q_search or
        st.session_state.prev_search_dept != s_dept or
        st.session_state.prev_search_status != s_stat or
        st.session_state.prev_search_sla != float(s_sla)):
        st.session_state.search_page = 1
        st.session_state.prev_search_query = q_search
        st.session_state.prev_search_dept = s_dept
        st.session_state.prev_search_status = s_stat
        st.session_state.prev_search_sla = float(s_sla)
    
    # Query database based on search criteria
    query_str = """
        SELECT m.id, m.action, m.assigned_department, m.sla_days, m.status, m.confidence, c.title as circular_title
        FROM maps m 
        JOIN circulars c ON m.circular_id = c.id 
        WHERE m.sla_days <= %d
    """ % s_sla
    
    if s_dept != "All Departments":
        query_str += " AND m.assigned_department = '%s'" % s_dept
    if s_stat != "All":
        query_str += " AND m.status = '%s'" % s_stat
    if q_search:
        escaped_q = q_search.replace("'", "''")
        query_str += " AND LOWER(m.action) LIKE LOWER('%%%s%%')" % escaped_q
        
    query_str += " ORDER BY m.id DESC"
    
    results = fetch_data(query_str)
    
    # Pagination calculations for search
    s_items_per_page = 3
    s_total_items = len(results)
    s_total_pages = max(1, (s_total_items + s_items_per_page - 1) // s_items_per_page)
    
    if st.session_state.search_page > s_total_pages:
        st.session_state.search_page = s_total_pages
    if st.session_state.search_page < 1:
        st.session_state.search_page = 1
        
    s_start_idx = (st.session_state.search_page - 1) * s_items_per_page
    s_end_idx = s_start_idx + s_items_per_page
    s_page_items = results.iloc[s_start_idx:s_end_idx] if not results.empty else results
    
    st.markdown(f"#### Search Results ({s_total_items} matches, Page {st.session_state.search_page}/{s_total_pages})")
    
    if not results.empty:
        for _, row in s_page_items.iterrows():
            dept_cls = get_dept_class(row['assigned_department'])
            status_cls = 'status-done' if row['status'] == 'complete' else 'status-pending'
            status_text = 'COMPLETE' if row['status'] == 'complete' else 'PENDING'
            conf_pct = int(row['confidence'] * 100)
            
            st.markdown(f"""
            <div class="data-card" style="border-color: #000000; box-shadow: 3px 3px 0px #000000;">
                <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 0.8rem;">"{row['action']}"</div>
                <div class="map-meta">
                    <span class="dept-badge {dept_cls}">{row['assigned_department']}</span>
                    <span class="status-pill {status_cls}">{status_text}</span>
                    <span class="map-meta-item">SLA Timeline: {row['sla_days']} days</span>
                    <span class="map-meta-item">Accuracy: {conf_pct}%</span>
                    <span class="map-meta-item" style="margin-left: auto;">{row['circular_title'][:40]}...</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Pagination buttons
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        s_col1, s_col2, s_col3 = st.columns([1, 2, 1])
        with s_col1:
            if st.button("Prev", disabled=(st.session_state.search_page <= 1), use_container_width=True, key="s_prev_page"):
                st.session_state.search_page -= 1
                st.rerun()
        with s_col2:
            st.markdown(f"<div style='text-align: center; font-weight: 700; font-family: \"JetBrains Mono\", monospace; font-size: 0.75rem; height: 35px; display: flex; align-items: center; justify-content: center;'>Page {st.session_state.search_page} of {s_total_pages}</div>", unsafe_allow_html=True)
        with s_col3:
            if st.button("Next", disabled=(st.session_state.search_page >= s_total_pages), use_container_width=True, key="s_next_page"):
                st.session_state.search_page += 1
                st.rerun()
    else:
        st.info("No compliance items matched your search query criteria.")


