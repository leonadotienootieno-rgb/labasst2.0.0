"""
Lab Assistant Pro v2.1
A mobile-first laboratory calculation suite for researchers and educators.
Optimized for both desktop and phone/tablet use.
"""

import streamlit as st
import pandas as pd
import math
import time
from datetime import datetime
from pathlib import Path

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Lab Assistant Pro",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# ============================================
# LOAD CUSTOM CSS
# ============================================
def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Fallback inline CSS if file doesn't exist
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        .stApp { font-family: 'Inter', sans-serif; }
        
        .main-header {
            font-size: clamp(1.5rem, 5vw, 2.5rem);
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            border: none;
            border-radius: 12px;
            padding: 12px 20px;
            font-weight: 600;
            font-size: 16px;
            min-height: 48px;
            width: 100%;
            transition: transform 0.2s;
        }
        
        .stButton > button:active { transform: scale(0.98); }
        
        .stFormSubmitButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            font-weight: 600;
            font-size: 16px;
            min-height: 48px;
            width: 100%;
        }
        
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea {
            font-size: 16px !important;
            padding: 12px !important;
            border-radius: 10px !important;
            min-height: 48px;
        }
        
        div[data-testid="stMetric"] {
            background: #f8f9fa;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
        }
        
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 28px !important;
        }
        
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        }
        
        section[data-testid="stSidebar"] .stMarkdown {
            color: rgba(255,255,255,0.9) !important;
        }
        
        div[data-testid="stForm"] {
            border: 1px solid #e0e0e0;
            border-radius: 16px;
            padding: 20px;
            background: white;
        }
        
        div[data-testid="stExpander"] {
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            margin-bottom: 8px;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-weight: 500;
            padding: 10px 16px;
            font-size: 14px;
            white-space: nowrap;
        }
        
        div[data-testid="stProgress"] > div {
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 10px;
        }
        
        @media screen and (max-width: 768px) {
            .stApp { padding: 0.5rem !important; }
            
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
                font-size: 22px !important;
            }
            
            h2 { font-size: 1.3rem !important; }
            h3 { font-size: 1.1rem !important; }
            
            div[data-testid="stForm"] { padding: 12px; }
        }
        
        @media screen and (max-width: 480px) {
            .main-header { font-size: 1.3rem; }
            
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
                font-size: 18px !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)

load_css()

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'user': None,
        'user_email': None,
        'subscription_tier': 'free',
        'calculations_used': 0,
        'logbook': pd.DataFrame(columns=["Timestamp", "Module", "Result", "Note"]),
        'timer_running': False,
        'timer_end': None,
        'timer_task': '',
        'timer_duration': 0,
        'show_upgrade': False,
        'current_page': '🏠 Dashboard',
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================
# CONSTANTS
# ============================================
MAX_FREE_CALCULATIONS = st.secrets.get("MAX_FREE_CALCULATIONS", 10)
APP_NAME = st.secrets.get("APP_NAME", "Lab Assistant Pro")
APP_VERSION = "2.1"

# ============================================
# UTILITY FUNCTIONS
# ============================================
def add_to_logbook(module: str, result: str, note: str = ""):
    """Add entry to session logbook"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([{
        "Timestamp": now,
        "Module": module,
        "Result": result,
        "Note": note
    }])
    st.session_state.logbook = pd.concat(
        [st.session_state.logbook, new_entry], 
        ignore_index=True
    )

def check_usage_allowed() -> bool:
    """Check if user is within free tier limits"""
    st.session_state.calculations_used += 1
    
    if st.session_state.subscription_tier == 'pro':
        return True
    
    if st.session_state.calculations_used > MAX_FREE_CALCULATIONS:
        st.session_state.show_upgrade = True
        return False
    
    return True

def show_upgrade_prompt():
    """Display upgrade prompt"""
    st.warning(f"⚠️ Free limit: {st.session_state.calculations_used}/{MAX_FREE_CALCULATIONS}")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2); 
                padding: 20px; border-radius: 16px; color: white; margin: 1rem 0;">
        <h3 style="color: white;">🔓 Go Pro</h3>
        <p>♾️ Unlimited calculations<br>
        📋 50+ protocols<br>
        📄 PDF reports<br>
        💾 Cloud storage</p>
        <h2 style="color: white;">$4.99/month</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Upgrade Now", use_container_width=True):
            st.balloons()
            st.success("🎉 Payment coming soon! Email pro@labassistant.com")
    with col2:
        if st.button("🔄 Reset Free Tier", use_container_width=True):
            st.session_state.calculations_used = 0
            st.session_state.show_upgrade = False
            st.rerun()

def format_number(value, decimals=4):
    """Format number to remove trailing zeros"""
    if value == int(value):
        return str(int(value))
    return f"{value:.{decimals}g}"

# ============================================
# PROTOCOL DATA
# ============================================
PROTOCOLS = {
    "PCR & Molecular Biology": {
        "Standard PCR (50µL)": {
            "components": {
                "Template DNA": "1-2 µL",
                "Forward Primer (10µM)": "1 µL",
                "Reverse Primer (10µM)": "1 µL",
                "dNTPs (10mM each)": "1 µL",
                "10X PCR Buffer": "5 µL",
                "Taq Polymerase (5U/µL)": "0.5 µL",
                "Nuclease-free Water": "to 50 µL"
            },
            "cycling": "95°C/3min → 35×(95°C/30s, 55°C/30s, 72°C/30s) → 72°C/5min",
            "tips": "Adjust annealing temp ±5°C based on primer Tm"
        },
        "qPCR Master Mix (20µL)": {
            "components": {
                "2X SYBR Green Mix": "10 µL",
                "Forward Primer (10µM)": "0.5 µL",
                "Reverse Primer (10µM)": "0.5 µL",
                "cDNA template": "2 µL",
                "Nuclease-free Water": "7 µL"
            },
            "cycling": "95°C/10min → 40×(95°C/15s, 60°C/1min)",
            "tips": "Run triplicates with NTC. Keep on ice."
        },
        "Colony PCR (25µL)": {
            "components": {
                "2X Master Mix": "12.5 µL",
                "Forward Primer (10µM)": "1 µL",
                "Reverse Primer (10µM)": "1 µL",
                "Nuclease-free Water": "10.5 µL",
                "Colony (template)": "touch with tip"
            },
            "cycling": "95°C/5min → 30×(95°C/30s, 55°C/30s, 72°C/1min/kb) → 72°C/5min",
            "tips": "Pick single colony. Streak plate first to save cells."
        }
    },
    "Protein Analysis": {
        "SDS-PAGE Running Buffer (10X)": {
            "components": {
                "Tris base": "30.3 g",
                "Glycine": "144.1 g",
                "SDS": "10 g",
                "dH₂O": "to 1 L"
            },
            "tips": "Do NOT adjust pH. Dilute to 1X. Store RT 6 months."
        },
        "Coomassie Staining": {
            "components": {
                "Coomassie R-250": "0.25 g",
                "Methanol": "45 mL",
                "Acetic acid": "10 mL",
                "dH₂O": "45 mL"
            },
            "tips": "Filter before use. Microwave 30s to speed staining."
        },
        "RIPA Lysis Buffer": {
            "components": {
                "Tris-HCl (pH 7.4)": "50 mM",
                "NaCl": "150 mM",
                "NP-40": "1%",
                "Sodium deoxycholate": "0.5%",
                "SDS": "0.1%",
                "Protease inhibitor": "add fresh"
            },
            "tips": "Keep on ice. Add PMSF fresh (1mM final)."
        }
    },
    "Cell Culture": {
        "Complete DMEM (500mL)": {
            "components": {
                "DMEM (high glucose)": "445 mL",
                "FBS (heat-inactivated)": "50 mL",
                "Pen/Strep (100X)": "5 mL"
            },
            "tips": "Store 4°C. Warm to 37°C before use. Use within 1 month."
        },
        "Cell Passaging": {
            "steps": [
                "Aspirate old media completely",
                "Wash with PBS (Ca²⁺/Mg²⁺ free) - 5mL for T75",
                "Add trypsin-EDTA: 2mL for T75 flask",
                "Incubate 2-5 min at 37°C, 5% CO₂",
                "Tap gently to detach (check under microscope)",
                "Add 4mL complete media to neutralize trypsin",
                "Transfer to 15mL tube",
                "Centrifuge 300g × 5 min",
                "Remove supernatant, resuspend in fresh media",
                "Count and seed at desired density"
            ],
            "tips": "Check confluence daily. Passage at 70-90%."
        },
        "Freezing Medium": {
            "components": {
                "Complete growth medium": "70%",
                "FBS": "20%",
                "DMSO": "10%"
            },
            "tips": "Make fresh. Cool cells slowly (Mr. Frosty or -80°C)."
        }
    }
}

# ============================================
# SIDEBAR NAVIGATION
# ============================================
def render_sidebar():
    """Mobile-friendly sidebar navigation"""
    
    with st.sidebar:
        st.markdown(f"# 🧪 {APP_NAME}")
        st.caption(f"v{APP_VERSION} | Mobile Ready")
        
        st.markdown("---")
        
        # User section
        if st.session_state.user_email:
            st.success(f"👤 {st.session_state.user_email}")
            st.caption(f"Tier: {st.session_state.subscription_tier.title()}")
            if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
                for key in ['user', 'user_email', 'subscription_tier', 'calculations_used']:
                    st.session_state[key] = None if key in ['user', 'user_email'] else 'free' if key == 'subscription_tier' else 0
                st.rerun()
        else:
            with st.expander("🔐 Sign In (Free)"):
                email = st.text_input("Email", placeholder="you@lab.com", key="login_email")
                if st.button("Continue with Email", use_container_width=True):
                    if "@" in email and "." in email:
                        st.session_state.user_email = email
                        st.session_state.calculations_used = 0
                        st.success("✅ Welcome!")
                        st.rerun()
                    else:
                        st.error("Enter a valid email")
        
        st.markdown("---")
        
        # Navigation - big touch-friendly buttons
        st.markdown("### 🧭 Navigation")
        
        menu_options = [
            ("🏠", "Dashboard"),
            ("🧬", "Dilution Calc"),
            ("🧫", "Microbiology"),
            ("🔬", "Cell Culture"),
            ("🧬", "DNA Normalization"),
            ("🧪", "Master Mix"),
            ("🔄", "Unit Converter"),
            ("🌀", "Centrifuge"),
            ("⏱️", "Lab Timer"),
            ("📋", "Protocols"),
            ("📊", "Logbook"),
            ("💰", "Budget"),
        ]
        
        for emoji, label in menu_options:
            if st.button(f"{emoji}  {label}", use_container_width=True, key=f"nav_{label}"):
                st.session_state.current_page = label
                st.rerun()
        
        st.markdown("---")
        
        # Usage meter
        st.caption(f"💎 {st.session_state.subscription_tier.title()} Tier")
        progress = min(st.session_state.calculations_used / MAX_FREE_CALCULATIONS, 1.0)
        st.progress(progress, text=f"📊 {st.session_state.calculations_used}/{MAX_FREE_CALCULATIONS}")
        
        if st.session_state.subscription_tier == 'free':
            if st.button("⭐ Upgrade to Pro", use_container_width=True, type="primary", key="upgrade_sidebar"):
                st.session_state.current_page = "Upgrade"
                st.rerun()
        
        st.markdown("---")
        st.caption(f"📝 {len(st.session_state.logbook)} logs | 🧮 {st.session_state.calculations_used} calcs")

# ============================================
# PAGE: DASHBOARD
# ============================================
def page_dashboard():
    st.markdown('<h1 class="main-header">🧪 Lab Assistant Pro</h1>', unsafe_allow_html=True)
    st.markdown("### Your Pocket Lab Assistant 📱")
    
    # Stats grid - 2x2 works great on mobile
    st.markdown("---")
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.metric("🧮 Calculations", len(st.session_state.logbook))
    with row1_col2:
        st.metric("📋 Protocols", "50+")
    
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.metric("⚡ Status", "Ready ✅")
    with row2_col2:
        st.metric("💎 Plan", st.session_state.subscription_tier.title())
    
    st.markdown("---")
    
    # Quick tools - big touch targets
    st.markdown("### ⚡ Quick Tools")
    
    tools = [
        ("🧬", "Dilution", "C1V1 calculator", "Dilution Calc"),
        ("🧫", "Growth", "Doubling time", "Microbiology"),
        ("🧪", "Master Mix", "PCR recipe", "Master Mix"),
        ("📋", "Protocols", "Templates", "Protocols"),
    ]
    
    for i in range(0, len(tools), 2):
        col1, col2 = st.columns(2)
        for col, tool in zip([col1, col2], tools[i:i+2]):
            if tool:
                emoji, title, desc, target = tool
                with col:
                    if st.button(f"{emoji} **{title}**\n\n_{desc}_", 
                               use_container_width=True, 
                               key=f"quick_{title}"):
                        st.session_state.current_page = target
                        st.rerun()
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("### 📊 Recent Activity")
    if not st.session_state.logbook.empty:
        recent = st.session_state.logbook.tail(5)[["Timestamp", "Module", "Result"]]
        st.dataframe(recent, use_container_width=True, hide_index=True, height=180)
    else:
        st.info("👆 Tap a tool to get started!")
        
    # Quick tip
    with st.expander("💡 Quick Tips"):
        st.markdown("""
        - 📱 **Mobile tip:** Swipe the sidebar from the left edge
        - 🔄 All calculations auto-save to your logbook
        - 📋 Protocols can be downloaded as text files
        - 💎 Upgrade to Pro for unlimited calculations
        """)

# ============================================
# PAGE: BIOCHEMISTRY DILUTION
# ============================================
def page_dilution():
    st.markdown('<h1 class="main-header">🧬 Solution Preparation</h1>', unsafe_allow_html=True)
    st.caption("C₁V₁ = C₂V₂ | Mobile-optimized")
    
    with st.form("dilution_form", clear_on_submit=False):
        c1 = st.number_input(
            "Stock Concentration (M)", 
            value=1.0, 
            format="%.4f",
            help="Your stock solution concentration"
        )
        c2 = st.number_input(
            "Target Concentration (M)", 
            value=0.1, 
            format="%.4f",
            help="Desired final concentration"
        )
        v2 = st.number_input(
            "Target Volume (mL)", 
            value=100.0, 
            min_value=0.01,
            help="How much solution you need"
        )
        note = st.text_input("🏷️ Label (optional)", placeholder="e.g., 0.1M NaCl for Buffer A")
        
        submitted = st.form_submit_button("🧮 Calculate Dilution", use_container_width=True)
        
        if submitted:
            if st.session_state.show_upgrade:
                show_upgrade_prompt()
                st.stop()
            
            if not check_usage_allowed():
                show_upgrade_prompt()
                st.stop()
            
            if c1 <= 0:
                st.error("❌ Stock concentration must be positive")
            elif c2 > c1:
                st.error("❌ Target can't exceed stock concentration")
            elif v2 <= 0:
                st.error("❌ Volume must be positive")
            else:
                v1 = (c2 * v2) / c1
                
                st.markdown("### 📊 Results")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🧪 Stock Needed", f"{v1:.4f} mL")
                with col2:
                    st.metric("💧 Diluent", f"{v2 - v1:.4f} mL")
                
                st.progress(v1/v2, text=f"Mix: {v1/v2:.0%} stock + {1-v1/v2:.0%} diluent")
                
                result = f"Add {format_number(v1)} mL stock to {format_number(v2-v1)} mL diluent"
                st.success(f"✅ {result}")
                st.code(result)
                
                add_to_logbook("Dilution", result, note)

# ============================================
# PAGE: MICROBIOLOGY
# ============================================
def page_microbiology():
    st.markdown('<h1 class="main-header">🧫 Microbiology</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📈 Doubling Time", "📊 Growth Curve"])
    
    with tab1:
        with st.form("growth_form", clear_on_submit=False):
            n0 = st.number_input("Initial Count (N₀)", value=1000, min_value=1, 
                               help="Starting number of bacteria")
            nt = st.number_input("Final Count (Nₜ)", value=100000, min_value=1,
                               help="Ending number of bacteria")
            t_elapsed = st.number_input("Time Elapsed (min)", value=120, min_value=1)
            note = st.text_input("🏷️ Notes", placeholder="e.g., E. coli at 37°C")
            
            if st.form_submit_button("🧮 Calculate", use_container_width=True):
                if not check_usage_allowed():
                    show_upgrade_prompt()
                    st.stop()
                
                if nt <= n0:
                    st.error("❌ Final count must be greater than initial")
                elif t_elapsed <= 0:
                    st.error("❌ Time must be positive")
                else:
                    n_gen = (math.log10(nt) - math.log10(n0)) / math.log10(2)
                    gen_time = t_elapsed / n_gen
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Generations", f"{n_gen:.1f}")
                    with col2:
                        st.metric("Doubling Time", f"{gen_time:.1f} min")
                    with col3:
                        rate = 1/gen_time if gen_time > 0 else 0
                        st.metric("Growth Rate", f"{rate:.4f} min⁻¹")
                    
                    st.info(f"📝 Population doubles every **{gen_time:.1f} minutes**")
                    add_to_logbook("Microbiology", f"g={gen_time:.1f} min", note)
    
    with tab2:
        st.markdown("### Interactive Growth Curve")
        st.caption("Enter comma-separated values")
        
        col1, col2 = st.columns(2)
        with col1:
            times = st.text_area("Time (min)", "0, 30, 60, 90, 120, 150, 180", 
                               height=100, key="times_input")
        with col2:
            readings = st.text_area("OD600", "0.05, 0.08, 0.15, 0.35, 0.65, 0.95, 1.10",
                                  height=100, key="readings_input")
        
        if st.button("📈 Plot Curve", use_container_width=True):
            try:
                t_list = [float(x.strip()) for x in times.replace('\n', ',').split(',') if x.strip()]
                r_list = [float(x.strip()) for x in readings.replace('\n', ',').split(',') if x.strip()]
                
                if len(t_list) != len(r_list):
                    st.error(f"❌ Mismatch: {len(t_list)} times vs {len(r_list)} readings")
                elif len(t_list) < 2:
                    st.error("❌ Need at least 2 points")
                else:
                    df = pd.DataFrame({"OD600": r_list}, index=t_list)
                    st.line_chart(df, use_container_width=True, height=300)
                    
                    if r_list:
                        st.success(f"✅ Plotted {len(t_list)} points | Max OD: {max(r_list):.3f}")
                        add_to_logbook("Growth Curve", f"{len(t_list)} points plotted")
                        
            except ValueError:
                st.error("❌ Enter numbers only")

# ============================================
# PAGE: TISSUE CULTURE
# ============================================
def page_cell_culture():
    st.markdown('<h1 class="main-header">🔬 Cell Culture Seeding</h1>', unsafe_allow_html=True)
    
    with st.form("seeding_form", clear_on_submit=False):
        density = st.number_input("Cell Density (cells/mL)", value=1_000_000, 
                                min_value=1, format="%d",
                                help="Concentration of your cell suspension")
        target = st.number_input("Cells Needed", value=500_000, 
                               min_value=1, format="%d",
                               help="Total cells to seed")
        final_vol = st.number_input("Final Volume (mL)", value=10.0, min_value=0.1,
                                  help="Total volume in culture vessel")
        
        vessel_sizes = {
            "T25 Flask (5mL)": 5, "T75 Flask (15mL)": 15,
            "6-well (2mL/well)": 2, "96-well (0.2mL)": 0.2, "Custom": 0
        }
        vessel = st.selectbox("Culture Vessel", list(vessel_sizes.keys()))
        
        if st.form_submit_button("🧮 Calculate", use_container_width=True):
            if not check_usage_allowed():
                show_upgrade_prompt()
                st.stop()
            
            if density <= 0:
                st.error("❌ Density must be positive")
            elif target <= 0:
                st.error("❌ Cell count must be positive")
            else:
                vol_cells = target / density
                vol_media = final_vol - vol_cells
                
                if vol_cells > final_vol:
                    st.error("❌ Suspension too dilute!")
                    st.info("💡 Centrifuge at 300g × 5 min and resuspend in smaller volume")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🧫 Cell Suspension", f"{vol_cells:.3f} mL")
                    with col2:
                        st.metric("💧 Fresh Media", f"{vol_media:.3f} mL")
                    
                    result = f"Mix {vol_cells:.3f} mL cells + {vol_media:.3f} mL media"
                    st.success(f"✅ {result}")
                    
                    if vessel in vessel_sizes and vessel_sizes[vessel] > 0:
                        st.caption(f"💡 {vessel} typical working volume: {vessel_sizes[vessel]} mL")
                    
                    add_to_logbook("Cell Culture", result, vessel)

# ============================================
# PAGE: DNA NORMALIZATION
# ============================================
def page_dna():
    st.markdown('<h1 class="main-header">🧬 DNA Normalization</h1>', unsafe_allow_html=True)
    st.caption("For PCR, sequencing, and cloning setup")
    
    with st.form("dna_form", clear_on_submit=False):
        conc = st.number_input("DNA Concentration (ng/µL)", value=15.0, min_value=0.1,
                             help="From NanoDrop/Qubit")
        target = st.number_input("Target DNA Mass (ng)", value=50.0, min_value=0.1,
                               help="How much DNA you need")
        total_v = st.number_input("Total Reaction Volume (µL)", value=25.0, min_value=1.0)
        note = st.text_input("🏷️ Sample ID", placeholder="e.g., gDNA-Sample-01")
        
        if st.form_submit_button("🧮 Calculate", use_container_width=True):
            if not check_usage_allowed():
                show_upgrade_prompt()
                st.stop()
            
            if conc <= 0:
                st.error("❌ Concentration must be positive")
            else:
                v_dna = target / conc
                
                if v_dna < 0.5:
                    st.warning("⚠️ Volume < 0.5µL - hard to pipette accurately")
                    st.info("💡 Pre-dilute DNA 1:10, then use 10× more volume")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🧬 DNA", f"{v_dna:.2f} µL")
                with col2:
                    st.metric("💧 Diluent", f"{total_v - v_dna:.2f} µL")
                with col3:
                    st.metric("📐 Total", f"{total_v:.1f} µL")
                
                result = f"DNA: {v_dna:.2f} µL + Diluent: {total_v - v_dna:.2f} µL"
                st.success(f"✅ {result}")
                st.code(result)
                
                add_to_logbook("DNA Norm", result, note)

# ============================================
# PAGE: MASTER MIX
# ============================================
def page_master_mix():
    st.markdown('<h1 class="main-header">🧪 Master Mix Generator</h1>', unsafe_allow_html=True)
    
    with st.form("master_mix_form", clear_on_submit=False):
        samples = st.number_input("Number of Samples", value=8, min_value=1, max_value=384)
        excess = st.slider("Extra (%)", 5, 25, 10, help="Extra for pipetting errors")
        
        total_rxns = math.ceil(samples * (1 + excess/100))
        
        st.info(f"📊 **{total_rxns}** reactions ({excess}% extra = {total_rxns - samples} extra)")
        
        st.markdown("**Per reaction (µL):**")
        col1, col2 = st.columns(2)
        with col1:
            water = st.number_input("Water", value=13.5, step=0.5)
            buffer = st.number_input("Buffer", value=2.5, step=0.5)
            dntps = st.number_input("dNTPs", value=0.5, step=0.5)
        with col2:
            fwd = st.number_input("Forward Primer", value=1.0, step=0.5)
            rev = st.number_input("Reverse Primer", value=1.0, step=0.5)
            enzyme = st.number_input("Polymerase", value=0.5, step=0.1)
        
        if st.form_submit_button("🧮 Generate Master Mix", use_container_width=True):
            if not check_usage_allowed():
                show_upgrade_prompt()
                st.stop()
            
            components = {
                "Water": water * total_rxns,
                "Buffer": buffer * total_rxns,
                "dNTPs": dntps * total_rxns,
                "Forward Primer": fwd * total_rxns,
                "Reverse Primer": rev * total_rxns,
                "Polymerase": enzyme * total_rxns,
            }
            
            total_vol = sum(components.values())
            
            st.markdown("### 📋 Master Mix Recipe")
            
            # Simple display
            for name, vol in components.items():
                st.metric(name, f"{vol:.1f} µL")
            
            st.markdown("---")
            st.metric("🧪 Total Mix", f"{total_vol:.1f} µL")
            aliquot = total_vol / samples
            st.success(f"✅ Add **{aliquot:.1f} µL** per tube")
            
            add_to_logbook("Master Mix", f"{total_rxns} rxns, {total_vol:.1f}µL total")

# ============================================
# PAGE: UNIT CONVERTER
# ============================================
def page_converter():
    st.markdown('<h1 class="main-header">🔄 Unit Converter</h1>', unsafe_allow_html=True)
    
    conv_type = st.radio("Type", ["Molarity → Mass", "% Solutions"], horizontal=True)
    
    if conv_type == "Molarity → Mass":
        with st.form("molarity_form", clear_on_submit=False):
            mw = st.number_input("Molecular Weight (g/mol)", value=58.44,
                               help="e.g., NaCl = 58.44")
            molarity = st.number_input("Molarity (M)", value=1.0, format="%.3f")
            volume = st.number_input("Volume (L)", value=1.0, format="%.3f")
            
            if st.form_submit_button("🔄 Convert", use_container_width=True):
                if mw <= 0:
                    st.error("❌ MW must be positive")
                else:
                    mass = molarity * mw * volume
                    st.metric("Mass to Weigh", f"{mass:.3f} g")
                    st.success(f"✅ Weigh **{mass:.3f} g** for {volume:.3f} L of {molarity} M")
                    add_to_logbook("Converter", f"{molarity}M, {volume}L = {mass:.3f}g")
    
    else:
        with st.form("percent_form", clear_on_submit=False):
            pct_type = st.radio("Type", ["% w/v", "% v/v"], horizontal=True)
            pct = st.number_input("Percentage", value=10.0, min_value=0.01, max_value=100.0)
            total = st.number_input("Total Volume (mL)", value=100.0, min_value=0.1)
            
            if st.form_submit_button("🔄 Calculate", use_container_width=True):
                amount = (pct / 100) * total
                unit = "g" if "w/v" in pct_type else "mL"
                st.success(f"✅ Use **{amount:.2f} {unit}** in {total:.1f} mL total")
                add_to_logbook("Converter", f"{pct}% = {amount:.2f}{unit}")

# ============================================
# PAGE: CENTRIFUGE
# ============================================
def page_centrifuge():
    st.markdown('<h1 class="main-header">🌀 Centrifuge Converter</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["RPM → RCF", "RCF → RPM"])
    
    with tab1:
        with st.form("rpm_form", clear_on_submit=False):
            radius = st.number_input("Rotor Radius (cm)", value=10.0, min_value=1.0,
                                   help="Distance from center to tube bottom")
            rpm = st.number_input("Speed (RPM)", value=5000, min_value=100)
            
            if st.form_submit_button("🌀 Convert to × g", use_container_width=True):
                rcf = 0.00001118 * radius * (rpm ** 2)
                st.metric("RCF", f"{rcf:.0f} × g")
                
                if rcf < 500:
                    st.info("💡 Cell pelleting range (300-500g)")
                elif rcf < 5000:
                    st.info("💡 Bacteria pelleting (3000-5000g)")
                else:
                    st.info("💡 Microsome/organelle pelleting")
                
                add_to_logbook("Centrifuge", f"{rpm} RPM = {rcf:.0f} × g")
    
    with tab2:
        with st.form("rcf_form", clear_on_submit=False):
            radius2 = st.number_input("Rotor Radius (cm)", value=10.0, min_value=1.0, key="r2")
            rcf_target = st.number_input("Desired RCF (× g)", value=5000, min_value=1)
            
            if st.form_submit_button("🌀 Convert to RPM", use_container_width=True):
                rpm_needed = math.sqrt(rcf_target / (0.00001118 * radius2))
                st.metric("Required RPM", f"{rpm_needed:.0f}")
                add_to_logbook("Centrifuge", f"{rcf_target}g = {rpm_needed:.0f} RPM")

# ============================================
# PAGE: LAB TIMER
# ============================================
def page_timer():
    st.markdown('<h1 class="main-header">⏱️ Lab Timer</h1>', unsafe_allow_html=True)
    
    presets = {
        "Custom": 0, "Quick Spin (30s)": 0.5, "Vortex (10s)": 0.17,
        "Incubation (5 min)": 5, "Heat Block (10 min)": 10,
        "Digestion (1 hr)": 60, "Overnight (16 hr)": 960
    }
    
    preset = st.selectbox("Preset", list(presets.keys()))
    mins = presets[preset] if preset != "Custom" else st.number_input("Minutes", 1, 1440, 5)
    
    task = st.text_input("Task Name", "Incubation", placeholder="What are you timing?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Start", use_container_width=True):
            if not st.session_state.timer_running:
                st.session_state.timer_running = True
                st.session_state.timer_end = time.time() + (mins * 60)
                st.session_state.timer_task = task
                st.session_state.timer_duration = mins
                st.rerun()
    with col2:
        if st.button("⏸️ Stop", use_container_width=True):
            st.session_state.timer_running = False
            st.rerun()
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.timer_running = False
            st.session_state.timer_end = None
            st.session_state.timer_task = ''
            st.rerun()
    
    # Timer display
    if st.session_state.timer_end is not None:
        remaining = max(0, st.session_state.timer_end - time.time())
        
        if st.session_state.timer_running and remaining > 0:
            mins_rem = int(remaining // 60)
            secs_rem = int(remaining % 60)
            
            progress = 1 - (remaining / (st.session_state.timer_duration * 60))
            st.progress(min(progress, 1.0))
            
            # Big timer display
            st.markdown(f"""
            <div style="text-align:center; padding:1.5rem; background:#f0f2f6; 
                        border-radius:16px; margin:1rem 0;">
                <h1 style="font-size:clamp(2rem, 15vw, 5rem); font-family:monospace; 
                          color:#667eea; margin:0;">
                    {mins_rem:02d}:{secs_rem:02d}
                </h1>
                <p style="color:#666; font-size:1.1rem; margin-top:0.5rem;">
                    {st.session_state.timer_task}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(1)
            st.rerun()
            
        elif remaining <= 0 and st.session_state.timer_end:
            st.balloons()
            st.success(f"🔔 **{st.session_state.timer_task} Complete!**")
            add_to_logbook("Timer", f"{st.session_state.timer_task} finished ({st.session_state.timer_duration} min)")
            st.session_state.timer_running = False
            st.session_state.timer_end = None

# ============================================
# PAGE: PROTOCOLS
# ============================================
def page_protocols():
    st.markdown('<h1 class="main-header">📋 Protocol Library</h1>', unsafe_allow_html=True)
    
    if st.session_state.subscription_tier == 'free':
        st.info("💡 Free: 3 categories. Pro: 50+ protocols & PDF export")
    
    search = st.text_input("🔍 Search", placeholder="PCR, buffer, cell...")
    
    categories = list(PROTOCOLS.keys())
    
    for category in categories:
        protocols = PROTOCOLS[category]
        
        if search:
            protocols = {k: v for k, v in protocols.items() 
                        if search.lower() in k.lower() or search.lower() in category.lower()}
        
        if not protocols:
            continue
            
        st.markdown(f"### 📂 {category}")
        
        for name, details in protocols.items():
            with st.expander(f"📄 {name}"):
                if "components" in details:
                    st.markdown("**🧪 Components:**")
                    for comp, amount in details["components"].items():
                        st.markdown(f"- **{comp}**: `{amount}`")
                
                if "cycling" in details:
                    st.markdown("**🔄 Cycling:**")
                    st.code(details["cycling"])
                
                if "steps" in details:
                    st.markdown("**📝 Steps:**")
                    for i, step in enumerate(details["steps"], 1):
                        st.markdown(f"{i}. {step}")
                
                if "tips" in details:
                    st.info(f"💡 {details['tips']}")
                
                # Download
                text = f"{name}\n{'-'*40}\n"
                for key, val in details.items():
                    if key != "components":
                        text += f"\n{key.upper()}:\n{val}\n"
                    else:
                        text += "\nCOMPONENTS:\n"
                        for k, v in val.items():
                            text += f"  • {k}: {v}\n"
                
                st.download_button(
                    "📥 Download Protocol", text,
                    f"{name.lower().replace(' ', '_')}.txt",
                    use_container_width=True,
                    key=f"dl_{category}_{name}"
                )

# ============================================
# PAGE: LOGBOOK
# ============================================
def page_logbook():
    st.markdown('<h1 class="main-header">📊 Activity Logbook</h1>', unsafe_allow_html=True)
    
    if st.session_state.logbook.empty:
        st.info("📝 No calculations yet. Use the tools to build your log!")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entries", len(st.session_state.logbook))
    with col2:
        modules = st.session_state.logbook["Module"].nunique()
        st.metric("Tools Used", modules)
    with col3:
        last = st.session_state.logbook["Timestamp"].iloc[-1]
        st.metric("Last Activity", last.split(" ")[1][:5] if " " in last else last)
    
    st.markdown("---")
    
    # Filter
    all_modules = ["All"] + list(st.session_state.logbook["Module"].unique())
    filter_mod = st.selectbox("Filter by Tool", all_modules)
    
    df = st.session_state.logbook
    if filter_mod != "All":
        df = df[df["Module"] == filter_mod]
    
    st.dataframe(
        df[["Timestamp", "Module", "Result"]], 
        use_container_width=True, 
        hide_index=True,
        height=400
    )
    
    col1, col2 = st.columns(2)
    with col1:
        csv = st.session_state.logbook.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "lab_log.csv", "text/csv", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear Log", use_container_width=True):
            st.session_state.logbook = pd.DataFrame(columns=["Timestamp", "Module", "Result", "Note"])
            st.rerun()

# ============================================
# PAGE: BUDGET
# ============================================
def page_budget():
    st.markdown('<h1 class="main-header">💰 Budget Reference</h1>', unsafe_allow_html=True)
    st.caption("Approximate prices in USD. Actual costs vary by region and supplier.")
    
    budget_data = {
        "PCR & Molecular Biology": [
            ("Taq Polymerase", "$0.50/rxn", "NEB"),
            ("dNTPs Mix", "$0.30/rxn", "Thermo"),
            ("SYBR Green qPCR Mix", "$1.00/rxn", "Bio-Rad"),
            ("DNA Ladder (100bp)", "$2.00/lane", "Invitrogen"),
            ("Restriction Enzyme", "$0.80/rxn", "NEB"),
        ],
        "Cell Culture": [
            ("DMEM (500mL)", "$25/bottle", "Gibco"),
            ("FBS (500mL)", "$250/bottle", "Sigma"),
            ("Trypsin-EDTA (100mL)", "$35/bottle", "Gibco"),
            ("Pen/Strep (100mL)", "$15/bottle", "Gibco"),
            ("DMSO (50mL)", "$40/bottle", "Sigma"),
        ],
        "General Lab": [
            ("Ethanol 100% (1L)", "$30", "Fisher"),
            ("Isopropanol (1L)", "$25", "Fisher"),
            ("Agarose (100g)", "$80", "Bio-Rad"),
            ("Tris Base (500g)", "$45", "Sigma"),
            ("Glycine (1kg)", "$60", "Sigma"),
        ]
    }
    
    tabs = st.tabs(list(budget_data.keys()))
    for tab, (category, items) in zip(tabs, budget_data.items()):
        with tab:
            for item, price, supplier in items:
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;
                           padding:12px; background:#f8f9fa; border-radius:8px; margin-bottom:6px;">
                    <div>
                        <strong>{item}</strong><br>
                        <small style="color:#666;">{supplier}</small>
                    </div>
                    <div style="font-weight:600; color:#667eea;">{price}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("💡 Monthly budget estimate for small lab: $200-500 (basic consumables)")

# ============================================
# PAGE: UPGRADE
# ============================================
def page_upgrade():
    st.markdown('<h1 class="main-header">⭐ Upgrade to Pro</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="border:2px solid #e0e0e0; border-radius:16px; padding:24px; text-align:center;">
            <h3>🆓 Free</h3>
            <h1 style="color:#666;">$0</h1>
            <p>Forever</p>
            <hr>
            <p>✅ 10 calculations/session</p>
            <p>✅ 3 protocol categories</p>
            <p>✅ CSV export</p>
            <p>✅ All calculators</p>
            <p>❌ Cloud storage</p>
            <p>❌ PDF reports</p>
            <p>❌ Priority support</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="border:2px solid #667eea; border-radius:16px; padding:24px; text-align:center;
                   background:linear-gradient(135deg, #667eea11, #764ba211);">
            <h3>💎 Pro</h3>
            <h1 style="color:#667eea;">$4.99</h1>
            <p>per month</p>
            <hr>
            <p>✅ ♾️ Unlimited calculations</p>
            <p>✅ 📋 50+ protocols</p>
            <p>✅ 📄 PDF reports</p>
            <p>✅ 💾 Cloud storage</p>
            <p>✅ 📊 Analytics</p>
            <p>✅ ⭐ Priority support</p>
            <p>✅ 🔄 Auto-save logs</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Continue Free", use_container_width=True, key="stay_free_btn")
    with col2:
        if st.button("✨ Upgrade Now", use_container_width=True, type="primary"):
            st.balloons()
            st.success("🎉 Payment system coming soon!")
            st.info("📧 Email pro@labassistant.com to get early access")
    
    st.markdown("---")
    st.markdown("""
    ### Why Go Pro?
    
    - **Unlimited calculations** - No more session limits
    - **Cloud storage** - Your logs saved permanently
    - **PDF reports** - Professional documentation for lab meetings
    - **Priority support** - Get help within 24 hours
    - **Advanced features** - Be first to access new tools
    
    Perfect for grad students, postdocs, and research scientists who spend hours on calculations daily.
    """)

# ============================================
# MAIN APP ROUTER
# ============================================
def main():
    """Main app with mobile-friendly routing"""
    
    render_sidebar()
    
    # Page router
    pages = {
        "Dashboard": page_dashboard,
        "Dilution Calc": page_dilution,
        "Microbiology": page_microbiology,
        "Cell Culture": page_cell_culture,
        "DNA Normalization": page_dna,
        "Master Mix": page_master_mix,
        "Unit Converter": page_converter,
        "Centrifuge": page_centrifuge,
        "Lab Timer": page_timer,
        "Protocols": page_protocols,
        "Logbook": page_logbook,
        "Budget": page_budget,
        "Upgrade": page_upgrade,
    }
    
    current = st.session_state.get('current_page', 'Dashboard')
    if current in pages:
        pages[current]()
    else:
        page_dashboard()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"© 2024 {APP_NAME} | v{APP_VERSION}")
    st.sidebar.caption("Made for Scientists 🔬")

if __name__ == "__main__":
    main()