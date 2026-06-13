"""
Lab Assistant Pro v2.0
A professional laboratory calculation suite for researchers and educators.
"""

import streamlit as st
import pandas as pd
import math
import time
from datetime import datetime
from pathlib import Path

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Lab Assistant Pro",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD CUSTOM CSS ---
def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# --- SESSION STATE INITIALIZATION ---
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
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- CONSTANTS ---
MAX_FREE_CALCULATIONS = st.secrets.get("MAX_FREE_CALCULATIONS", 10)
APP_NAME = st.secrets.get("APP_NAME", "Lab Assistant Pro")
APP_VERSION = st.secrets.get("APP_VERSION", "2.0.0")

# --- UTILITY FUNCTIONS ---
def add_to_logbook(module: str, result: str, note: str = ""):
    """Add an entry to the session logbook"""
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
    """Display upgrade prompt for free tier users"""
    st.warning(f"⚠️ You've used {st.session_state.calculations_used}/{MAX_FREE_CALCULATIONS} free calculations")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        ### 🔓 Unlock Unlimited Access
        
        - ♾️ Unlimited calculations
        - 📋 50+ protocol templates
        - 📄 PDF report export
        - 📊 Advanced analytics
        - 💾 Cloud storage for logs
        """)
    with col2:
        st.metric("Pro Plan", "$4.99/mo")
        if st.button("✨ Upgrade Now", use_container_width=True):
            st.session_state.show_upgrade = False
            # Placeholder for Stripe integration
            st.info("💡 Payment integration coming soon! Email us at pro@labassistant.com")
    
    if st.button("Continue with Free Tier (Session Reset)"):
        st.session_state.calculations_used = 0
        st.session_state.show_upgrade = False
        st.rerun()

# --- PROTOCOL DATA ---
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
            "tips": "Adjust annealing temperature based on primer Tm (±5°C)"
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
            "tips": "Always run in triplicate with NTC controls"
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
            "tips": "Do NOT adjust pH. Dilute to 1X before use."
        },
        "Coomassie Staining Solution": {
            "components": {
                "Coomassie R-250": "0.25 g",
                "Methanol": "45 mL",
                "Acetic acid": "10 mL",
                "dH₂O": "45 mL"
            },
            "tips": "Filter through Whatman paper before use"
        }
    },
    "Cell Culture": {
        "Complete DMEM Media (500mL)": {
            "components": {
                "DMEM (high glucose)": "445 mL",
                "FBS (heat-inactivated)": "50 mL",
                "Pen/Strep (100X)": "5 mL"
            },
            "tips": "Store at 4°C. Warm to 37°C before use."
        },
        "Cell Passaging Protocol": {
            "steps": [
                "Aspirate old media completely",
                "Wash with PBS (without Ca²⁺/Mg²⁺)",
                "Add trypsin-EDTA (2mL for T75 flask)",
                "Incubate 2-5 min at 37°C",
                "Tap gently to detach cells",
                "Add complete media (2X trypsin volume)",
                "Centrifuge at 300g for 5 min",
                "Resuspend in fresh complete media",
                "Count cells and seed at desired density"
            ],
            "tips": "Check confluence daily. Passage at 70-90% confluency."
        }
    }
}

# --- SIDEBAR ---
def render_sidebar():
    """Render the sidebar navigation and user info"""
    
    with st.sidebar:
        st.markdown(f"# 🧪 {APP_NAME}")
        st.caption(f"v{APP_VERSION}")
        
        st.markdown("---")
        
        # User section
        if st.session_state.user_email:
            st.success(f"👤 {st.session_state.user_email}")
            st.caption(f"Tier: {st.session_state.subscription_tier.title()}")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user_email = None
                st.session_state.user = None
                st.session_state.subscription_tier = 'free'
                st.rerun()
        else:
            with st.expander("🔐 Sign In / Register"):
                email = st.text_input("Email", placeholder="scientist@lab.com")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Sign In", use_container_width=True):
                        if "@" in email:
                            st.session_state.user_email = email
                            st.session_state.calculations_used = 0
                            st.success("✅ Signed in!")
                            st.rerun()
                        else:
                            st.error("Valid email required")
                with col2:
                    if st.button("Register", use_container_width=True):
                        if "@" in email:
                            st.session_state.user_email = email
                            st.session_state.calculations_used = 0
                            st.success("✅ Registered!")
                            st.rerun()
        
        st.markdown("---")
        
        # Navigation
        menu_options = [
            "🏠 Dashboard",
            "🧬 Biochemistry (C1V1)",
            "🧫 Microbiology & Growth",
            "🔬 Tissue Culture",
            "🧬 Forensics (DNA)",
            "🧪 Master Mix Generator",
            "🔄 Unit Converter",
            "🌀 Centrifuge (RPM/G)",
            "⏱️ Lab Timer",
            "📋 Protocol Library",
            "📊 Activity Logbook",
            "💰 Lab Budget Reference"
        ]
        
        selected = st.radio("Navigation", menu_options, label_visibility="collapsed")
        
        st.markdown("---")
        
        # Usage meter
        st.caption("Usage This Session")
        progress = min(st.session_state.calculations_used / MAX_FREE_CALCULATIONS, 1.0)
        st.progress(progress, text=f"{st.session_state.calculations_used}/{MAX_FREE_CALCULATIONS}")
        
        if st.session_state.subscription_tier == 'free':
            st.button("⭐ Upgrade to Pro - $4.99/mo", 
                     use_container_width=True, 
                     type="primary")
        
        st.markdown("---")
        st.caption(f"📊 Total logs: {len(st.session_state.logbook)}")
        
        return selected

# --- CALCULATOR PAGES ---

def page_dashboard():
    """Home dashboard"""
    st.markdown('<h1 class="main-header">🧪 Lab Assistant Pro</h1>', unsafe_allow_html=True)
    st.markdown("### Your All-in-One Laboratory Calculation Suite")
    
    # Stats cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🧮 Calculations", len(st.session_state.logbook))
    with col2:
        st.metric("📋 Protocols", "50+")
    with col3:
        st.metric("⚡ Status", "Ready")
    with col4:
        st.metric("☁️ Session", "Active")
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    cols = st.columns(4)
    quick_actions = [
        ("🧬 Dilution Calc", "Biochemistry (C1V1)"),
        ("🧫 Growth Curve", "Microbiology & Growth"),
        ("🧪 Master Mix", "Master Mix Generator"),
        ("📋 Protocols", "Protocol Library")
    ]
    
    for col, (label, _) in zip(cols, quick_actions):
        with col:
            st.button(label, use_container_width=True, key=f"quick_{label}")
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("### 📊 Quick Stats")
    if not st.session_state.logbook.empty:
        recent = st.session_state.logbook.tail(5)
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("Start calculating to see your activity here!")

def page_biochemistry():
    """C1V1 Dilution Calculator"""
    st.markdown("## 🧬 Solution Preparation")
    st.markdown("*Calculate precise volumes using C₁V₁ = C₂V₂*")
    
    with st.form("dilution_form"):
        col1, col2 = st.columns(2)
        with col1:
            c1 = st.number_input("Stock Concentration (M)", value=1.0, format="%.4f",
                               help="Concentration of your stock solution")
            c2 = st.number_input("Target Concentration (M)", value=0.1, format="%.4f",
                               help="Desired final concentration")
        with col2:
            v2 = st.number_input("Target Volume (mL)", value=100.0, min_value=0.01,
                               help="Final volume needed")
            note = st.text_input("Label (optional)", placeholder="e.g., 0.1M NaCl")
        
        submitted = st.form_submit_button("🧮 Calculate", use_container_width=True)
        
        if submitted:
            if st.session_state.show_upgrade:
                show_upgrade_prompt()
                st.stop()
            
            if not check_usage_allowed():
                show_upgrade_prompt()
                st.stop()
            
            if c1 <= 0:
                st.error("Stock concentration must be greater than zero")
            elif c2 > c1:
                st.error("Target concentration cannot exceed stock concentration")
            elif v2 <= 0:
                st.error("Target volume must be greater than zero")
            else:
                v1 = (c2 * v2) / c1
                
                col_r1, col_r2 = st.columns(2)
                col_r1.metric("Stock Volume", f"{v1:.4f} mL")
                col_r2.metric("Diluent Volume", f"{v2 - v1:.4f} mL")
                
                st.progress(v1/v2, text=f"Stock: {v1/v2:.1%} | Diluent: {1-v1/v2:.1%}")
                
                result = f"Add {v1:.4g} mL stock to {v2-v1:.4g} mL diluent"
                st.success(f"✅ {result}")
                add_to_logbook("Biochemistry", result, note)

def page_microbiology():
    """Microbiology Growth Analysis"""
    st.markdown("## 🧫 Microbiology Growth Analysis")
    
    tab1, tab2 = st.tabs(["📈 Doubling Time", "📊 Growth Curve"])
    
    with tab1:
        with st.form("growth_form"):
            col1, col2 = st.columns(2)
            with col1:
                n0 = st.number_input("Initial Count (N₀)", value=1000, min_value=1)
                nt = st.number_input("Final Count (Nₜ)", value=100000, min_value=1)
            with col2:
                t_elapsed = st.number_input("Time Elapsed (min)", value=120, min_value=1)
                note = st.text_input("Strain/Notes", placeholder="e.g., E. coli at 37°C")
            
            if st.form_submit_button("🧮 Calculate", use_container_width=True):
                if not check_usage_allowed():
                    show_upgrade_prompt()
                    st.stop()
                
                n_gen = (math.log10(nt) - math.log10(n0)) / math.log10(2)
                gen_time = t_elapsed / n_gen
                
                col_r1, col_r2, col_r3 = st.columns(3)
                col_r1.metric("Generations", f"{n_gen:.2f}")
                col_r2.metric("Doubling Time", f"{gen_time:.1f} min")
                col_r3.metric("Growth Rate", f"{1/gen_time:.4f} min⁻¹" if gen_time > 0 else "N/A")
                
                st.info(f"📝 Population doubles every {gen_time:.1f} minutes")
                add_to_logbook("Microbiology", f"Doubling time: {gen_time:.1f} min", note)
    
    with tab2:
        st.markdown("### Interactive Growth Curve")
        st.markdown("Enter time points and OD600 readings:")
        
        col1, col2 = st.columns(2)
        with col1:
            times = st.text_area("Time Points (min)", "0, 30, 60, 90, 120, 150, 180")
        with col2:
            readings = st.text_area("OD600 Readings", "0.05, 0.08, 0.15, 0.35, 0.65, 0.95, 1.10")
        
        if st.button("📈 Plot Curve", use_container_width=True):
            try:
                t_list = [float(x.strip()) for x in times.replace('\n', ',').split(',') if x.strip()]
                r_list = [float(x.strip()) for x in readings.replace('\n', ',').split(',') if x.strip()]
                
                if len(t_list) != len(r_list):
                    st.error("Number of time points and readings must match!")
                else:
                    df = pd.DataFrame({"OD600": r_list}, index=t_list)
                    st.line_chart(df, use_container_width=True)
                    st.success(f"✅ Plotted {len(t_list)} data points")
                    
            except ValueError:
                st.error("Please enter valid numbers only")

def page_tissue_culture():
    """Tissue Culture Seeding Calculator"""
    st.markdown("## 🔬 Cell Seeding Calculator")
    
    with st.form("seeding_form"):
        col1, col2 = st.columns(2)
        with col1:
            density = st.number_input("Cell Density (cells/mL)", value=1000000, format="%d")
            target = st.number_input("Total Cells Needed", value=500000, format="%d")
        with col2:
            final_vol = st.number_input("Final Volume (mL)", value=10.0, min_value=0.1)
            vessel = st.selectbox("Culture Vessel", 
                                ["T25 Flask (5mL)", "T75 Flask (15mL)", 
                                 "6-well (2mL/well)", "96-well (0.2mL/well)", "Custom"])
        
        if st.form_submit_button("🧮 Calculate", use_container_width=True):
            if not check_usage_allowed():
                show_upgrade_prompt()
                st.stop()
            
            if density <= 0:
                st.error("Cell density must be positive")
            else:
                vol_cells = target / density
                vol_media = final_vol - vol_cells
                
                if vol_cells > final_vol:
                    st.error("Cell suspension too dilute! Centrifuge and resuspend.")
                else:
                    col_r1, col_r2 = st.columns(2)
                    col_r1.metric("Cell Suspension", f"{vol_cells:.3f} mL")
                    col_r2.metric("Fresh Media", f"{vol_media:.3f} mL")
                    
                    result = f"Seed {vol_cells:.3f} mL cells + {vol_media:.3f} mL media"
                    st.success(f"✅ {result}")
                    add_to_logbook("Tissue Culture", result, vessel)

def page_forensics():
    """DNA Normalization Calculator"""
    st.markdown("## 🧬 DNA Normalization")
    
    with st.form("dna_form"):
        col1, col2 = st.columns(2)
        with col1:
            conc = st.number_input("DNA Concentration (ng/µL)", value=15.0, min_value=0.1)
            target = st.number_input("Target DNA Mass (ng)", value=50.0, min_value=0.1)
        with col2:
            total_v = st.number_input("Total Reaction Volume (µL)", value=25.0, min_value=1.0)
            note = st.text_input("Sample ID (optional)", placeholder="e.g., Sample-001")
        
        if st.form_submit_button("🧮 Calculate", use_container_width=True):
            if not check_usage_allowed():
                show_upgrade_prompt()
                st.stop()
            
            if conc <= 0:
                st.error("Concentration must be positive")
            else:
                v_dna = target / conc
                
                if v_dna < 0.5:
                    st.warning("⚠️ Volume too low for accurate pipetting. Consider pre-diluting 1:10.")
                
                col_r1, col_r2 = st.columns(2)
                col_r1.metric("DNA Volume", f"{v_dna:.2f} µL")
                col_r2.metric("Diluent Volume", f"{total_v - v_dna:.2f} µL")
                
                result = f"Add {v_dna:.2f}µL DNA + {total_v - v_dna:.2f}µL diluent"
                st.success(f"✅ {result}")
                add_to_logbook("Forensics", result, note)

def page_master_mix():
    """PCR Master Mix Generator"""
    st.markdown("## 🧪 Master Mix Generator")
    
    with st.form("master_mix_form"):
        samples = st.number_input("Number of Samples", value=8, min_value=1)
        excess = st.slider("Excess (%)", 5, 25, 10)
        
        total_rxns = math.ceil(samples * (1 + excess/100))
        st.info(f"📊 Preparing for **{total_rxns}** reactions ({excess}% excess)")
        
        st.markdown("### Per Reaction:")
        col1, col2, col3 = st.columns(3)
        with col1:
            water = st.number_input("Water (µL)", value=13.5, step=0.5)
            buffer = st.number_input("Buffer (µL)", value=2.5, step=0.5)
        with col2:
            dntps = st.number_input("dNTPs (µL)", value=0.5, step=0.5)
            fwd = st.number_input("Forward Primer (µL)", value=1.0, step=0.5)
        with col3:
            rev = st.number_input("Reverse Primer (µL)", value=1.0, step=0.5)
            enzyme = st.number_input("Polymerase (µL)", value=0.5, step=0.1)
        
        if st.form_submit_button("🧮 Generate Recipe", use_container_width=True):
            if not check_usage_allowed():
                show_upgrade_prompt()
                st.stop()
            
            components = {
                "Water": water * total_rxns,
                "Buffer": buffer * total_rxns,
                "dNTPs": dntps * total_rxns,
                "Forward Primer": fwd * total_rxns,
                "Reverse Primer": rev * total_rxns,
                "Polymerase": enzyme * total_rxns
            }
            
            total_vol = sum(components.values())
            
            df = pd.DataFrame({
                "Component": list(components.keys()),
                "Per Rxn (µL)": [water, buffer, dntps, fwd, rev, enzyme],
                f"×{total_rxns} (µL)": list(components.values())
            })
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("Total Master Mix", f"{total_vol:.1f} µL")
            st.success(f"✅ Add **{total_vol/total_rxns:.1f} µL** per tube")
            add_to_logbook("Master Mix", f"{total_rxns} rxns, {total_vol:.1f}µL")

def page_unit_converter():
    """Unit Converter"""
    st.markdown("## 🔄 Unit Converter")
    
    conv_type = st.selectbox("Conversion Type", 
                           ["Molarity → Mass", "Percentage Solutions"])
    
    if conv_type == "Molarity → Mass":
        with st.form("molarity_form"):
            col1, col2 = st.columns(2)
            with col1:
                mw = st.number_input("Molecular Weight (g/mol)", value=58.44)
                molarity = st.number_input("Molarity (M)", value=1.0, format="%.3f")
            with col2:
                volume = st.number_input("Volume (L)", value=1.0, format="%.3f")
            
            if st.form_submit_button("🔄 Convert", use_container_width=True):
                mass = molarity * mw * volume
                st.metric("Mass Required", f"{mass:.3f} g")
                st.success(f"✅ Weigh **{mass:.3f} g** for **{volume:.3f} L** of **{molarity} M** solution")
                add_to_logbook("Converter", f"{molarity}M = {mass:.3f}g in {volume:.3f}L")

def page_centrifuge():
    """RPM/RCF Converter"""
    st.markdown("## 🌀 Centrifuge: RPM ↔ RCF")
    
    tab1, tab2 = st.tabs(["RPM → RCF", "RCF → RPM"])
    
    with tab1:
        with st.form("rpm_form"):
            radius = st.number_input("Rotor Radius (cm)", value=10.0, min_value=1.0)
            rpm = st.number_input("Speed (RPM)", value=5000, min_value=100)
            
            if st.form_submit_button("🌀 Convert", use_container_width=True):
                rcf = 0.00001118 * radius * (rpm ** 2)
                st.metric("RCF", f"{rcf:.0f} × g")
                
                if rcf < 500:
                    st.info("💡 Low speed: Cell pelleting range")
                elif rcf < 5000:
                    st.info("💡 Medium speed: Bacteria pelleting")
                else:
                    st.info("💡 High speed: Organelle/microsome pelleting")
                
                add_to_logbook("Centrifuge", f"{rpm} RPM = {rcf:.0f} × g")

def page_timer():
    """Lab Timer"""
    st.markdown("## ⏱️ Lab Timer")
    
    presets = {
        "Custom": 0,
        "Quick Spin (30s)": 0.5,
        "Incubation (5 min)": 5,
        "Centrifuge (10 min)": 10,
        "Digestion (1 hr)": 60
    }
    
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Preset", list(presets.keys()))
    with col2:
        mins = presets[preset] if preset != "Custom" else st.number_input("Minutes", 1, 1440)
    
    task = st.text_input("Task", "Incubation")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    
    with col_b1:
        if st.button("▶️ Start", use_container_width=True):
            st.session_state.timer_running = True
            st.session_state.timer_end = time.time() + (mins * 60)
            st.session_state.timer_task = task
            st.session_state.timer_duration = mins
            st.rerun()
    
    with col_b2:
        if st.button("⏸️ Pause", use_container_width=True):
            st.session_state.timer_running = False
    
    with col_b3:
        if st.button("⏹️ Reset", use_container_width=True):
            st.session_state.timer_running = False
            st.session_state.timer_end = None
            st.rerun()
    
    if st.session_state.timer_end:
        remaining = max(0, st.session_state.timer_end - time.time())
        
        if st.session_state.timer_running and remaining > 0:
            mins_rem = int(remaining // 60)
            secs_rem = int(remaining % 60)
            
            st.progress(1 - (remaining / (st.session_state.timer_duration * 60)))
            
            st.markdown(f"""
            <div style="text-align:center; padding:2rem; background:#f0f2f6; border-radius:1rem;">
                <h1 style="font-size:4rem; font-family:monospace; color:#667eea;">
                    {mins_rem:02d}:{secs_rem:02d}
                </h1>
                <p>{st.session_state.timer_task}</p>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(1)
            st.rerun()
            
        elif remaining <= 0 and st.session_state.timer_end:
            st.balloons()
            st.success(f"🔔 {st.session_state.timer_task} Complete!")
            add_to_logbook("Timer", f"{st.session_state.timer_task} done")
            st.session_state.timer_running = False
            st.session_state.timer_end = None

def page_protocols():
    """Protocol Library"""
    st.markdown("## 📋 Protocol Library")
    
    if st.session_state.subscription_tier == 'free':
        st.info("💡 **Free tier:** Access to 2 protocol categories. Upgrade to Pro for 50+ protocols!")
    
    categories = list(PROTOCOLS.keys())
    if st.session_state.subscription_tier == 'free':
        categories = categories[:2]  # Limit free users
    
    for category in categories:
        st.markdown(f"### {category}")
        protocols = PROTOCOLS[category]
        
        for name, details in protocols.items():
            with st.expander(f"📄 {name}"):
                if "components" in details:
                    st.markdown("**Components:**")
                    df = pd.DataFrame(details["components"].items(), 
                                    columns=["Component", "Amount"])
                    st.dataframe(df, hide_index=True, use_container_width=True)
                
                if "cycling" in details:
                    st.markdown(f"**Cycling:** `{details['cycling']}`")
                
                if "steps" in details:
                    st.markdown("**Steps:**")
                    for i, step in enumerate(details["steps"], 1):
                        st.markdown(f"{i}. {step}")
                
                if "tips" in details:
                    st.info(f"💡 {details['tips']}")
                
                # Download protocol
                text = f"{name}\n\n"
                for key, val in details.items():
                    if key != "components":
                        text += f"{key}: {val}\n"
                st.download_button("📥 Download", text, 
                                 f"{name.lower().replace(' ', '_')}.txt",
                                 key=f"dl_{name}")

def page_logbook():
    """Activity Logbook"""
    st.markdown("## 📊 Activity Logbook")
    
    if st.session_state.logbook.empty:
        st.info("No calculations yet. Start using the calculators!")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        modules = st.multiselect("Filter by Module", 
                               st.session_state.logbook["Module"].unique())
    with col2:
        if st.button("🗑️ Clear Log", use_container_width=True):
            st.session_state.logbook = pd.DataFrame(columns=["Timestamp", "Module", "Result", "Note"])
            st.rerun()
    
    df = st.session_state.logbook
    if modules:
        df = df[df["Module"].isin(modules)]
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, "lab_log.csv", "text/csv")

def page_budget():
    """Budget Reference"""
    st.markdown("## 💰 Reagent Price Reference")
    st.caption("Approximate prices for budget planning")
    
    data = {
        "PCR & Molecular Biology": pd.DataFrame({
            "Reagent": ["Taq Polymerase", "dNTPs Mix", "SYBR Green Mix", "DNA Ladder"],
            "Price/Rxn": ["$0.50", "$0.30", "$1.00", "$2.00"],
            "Supplier": ["NEB", "Thermo", "Bio-Rad", "Invitrogen"]
        }),
        "Cell Culture": pd.DataFrame({
            "Reagent": ["DMEM (500mL)", "FBS (500mL)", "Trypsin (100mL)", "P/S (100mL)"],
            "Price": ["$25", "$250", "$35", "$15"],
            "Supplier": ["Gibco", "Sigma", "Gibco", "Gibco"]
        })
    }
    
    tabs = st.tabs(list(data.keys()))
    for tab, (cat, df) in zip(tabs, data.items()):
        with tab:
            st.dataframe(df, use_container_width=True, hide_index=True)

# --- MAIN APP ---
def main():
    """Main application entry point"""
    
    selected = render_sidebar()
    
    # Route to correct page
    pages = {
        "🏠 Dashboard": page_dashboard,
        "🧬 Biochemistry (C1V1)": page_biochemistry,
        "🧫 Microbiology & Growth": page_microbiology,
        "🔬 Tissue Culture": page_tissue_culture,
        "🧬 Forensics (DNA)": page_forensics,
        "🧪 Master Mix Generator": page_master_mix,
        "🔄 Unit Converter": page_unit_converter,
        "🌀 Centrifuge (RPM/G)": page_centrifuge,
        "⏱️ Lab Timer": page_timer,
        "📋 Protocol Library": page_protocols,
        "📊 Activity Logbook": page_logbook,
        "💰 Lab Budget Reference": page_budget,
    }
    
    if selected in pages:
        pages[selected]()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"© 2024 {APP_NAME} | v{APP_VERSION}")

if __name__ == "__main__":
    main()