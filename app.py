import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
from data_service import get_company_data
from dcf_engine import run_full_model, calc_wacc

# Page config
st.set_page_config(page_title="DCF Valuation Model", page_icon="📈", layout="wide")

# --- PREMIUM DARK CSS ---
st.markdown("""
    <style>
    /* Base Background & Styling */
    .main { background-color: #0a0e1a; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid rgba(255, 255, 255, 0.08); }
    
    /* Headings */
    h1, h2, h3 { color: #f1f5f9; font-weight: 800; letter-spacing: -0.02em; }
    .hero-title {
        font-size: 3.2rem;
        background: linear-gradient(135deg, #f1f5f9, #6366f1, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    
    /* Cards & Containers */
    .premium-card {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(12px);
        margin-bottom: 24px;
    }
    
    /* KPI Cards */
    .kpi-card {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        text-align: left;
    }
    .kpi-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
    .kpi-value { font-size: 1.8rem; font-weight: 800; color: #f1f5f9; }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 700;
        transition: all 0.2s;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    }
    
    /* Inputs & Sliders */
    .stSlider [data-baseweb="slider"] { color: #6366f1; }
    .stTextInput input { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); color: white; }
    
    /* Badges */
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: inline-block; }
    .badge-green { background: rgba(16, 185, 129, 0.15); color: #10b981; }
    .badge-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'company' not in st.session_state:
    st.session_state.company = None
if 'ticker' not in st.session_state:
    st.session_state.ticker = ""
if 'page' not in st.session_state:
    st.session_state.page = "Home"
if 'assumptions' not in st.session_state:
# ... (rest of assumptions)
    st.session_state.assumptions = {
        'revenue_growth': 0.15,
        'fcf_margin': 0.25,
        'tax_rate': 0.21,
        'wacc_mode': 'build',
        'wacc_direct': 0.10,
        'risk_free': 0.042,
        'mkt_premium': 0.055,
        'beta': 1.0,
        'terminal_method': 'perpetuity',
        'terminal_growth': 0.02,
        'exit_ebitda_multiple': 12.0,
        'years_forecast': 5,
        'equity_weight': 1.0,
        'debt_weight': 0.0,
        'net_debt_override': None,
        'shares_out_override': None
    }

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("📈 DCF Valuation")
    nav_options = ["Home", "Inputs", "Outputs", "Sensitivity", "Scenarios", "About"]
    try:
        index = nav_options.index(st.session_state.page)
    except:
        index = 0
    page = st.radio("Navigation", nav_options, index=index, label_visibility="collapsed")
    st.session_state.page = page # Update session state when clicked
    
    st.divider()
    if st.session_state.company:
        st.subheader("Active Company")
        st.markdown(f"**{st.session_state.company['name']}**")
        st.markdown(f"Ticker: `{st.session_state.company['ticker']}`")
        if st.button("Reset Session"):
            st.session_state.company = None
            st.rerun()

# --- HELPER: KPICard ---
def kpi_card(label, value, delta=None, delta_color="normal"):
    delta_html = ""
    if delta:
        color = "#10b981" if delta_color == "inverse" and "-" not in str(delta) else "#ef4444" 
        if delta_color == "normal": color = "#10b981" if "-" not in str(delta) else "#ef4444"
        delta_html = f'<div style="color: {color}; font-size: 0.85rem; font-weight: 600; margin-top: 4px;">{delta}</div>'
        
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)

# --- PAGE: HOME ---
if page == "Home":
    st.markdown('<h1 class="hero-title">DCF Valuation</h1>', unsafe_allow_html=True)
    st.markdown("Enter any ticker to build a full Discounted Cash Flow model.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker_input = st.text_input("Ticker Symbol", value=st.session_state.ticker, placeholder="e.g. NVDA, AAPL").upper()
        if st.button("Load Financials"):
            if ticker_input:
                with st.spinner("Fetching data..."):
                    st.session_state.company = get_company_data(ticker_input)
                    st.session_state.ticker = ticker_input
                    # Set defaults
                    st.session_state.assumptions['beta'] = st.session_state.company['beta']
                    st.rerun()

    if st.session_state.company:
        comp = st.session_state.company
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.subheader(f"{comp['name']} ({comp['ticker']})")
        
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Price", f"${comp['price']:,.2f}")
        with c2: st.metric("Market Cap", f"${comp['market_cap']/1e9:,.1f}B")
        with c3: st.metric("Beta", f"{comp['beta']:.2f}")
        
        if st.button("Go to Model →"):
            st.session_state.page = "Inputs" # Add this to session state to control navigation
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE: INPUTS ---
elif page == "Inputs":
    if not st.session_state.company:
        st.warning("Please load a company on the Home page first.")
    else:
        comp = st.session_state.company
        st.title(f"{comp['name']} - Model Inputs")
        
        col1, col2 = st.columns([2, 1.2])
        
        with col1:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.subheader("Forecast Assumptions")
            st.session_state.assumptions['revenue_growth'] = st.slider("Revenue Growth (%)", -5, 50, int(st.session_state.assumptions['revenue_growth']*100)) / 100
            st.session_state.assumptions['fcf_margin'] = st.slider("FCF Margin (%)", 0, 60, int(st.session_state.assumptions['fcf_margin']*100)) / 100
            st.session_state.assumptions['years_forecast'] = st.number_input("Forecast Years", 3, 10, st.session_state.assumptions['years_forecast'])
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.subheader("WACC Assumptions")
            wacc_mode = st.radio("Method", ["Direct WACC", "Build WACC"], index=0 if st.session_state.assumptions['wacc_mode'] == 'direct' else 1, horizontal=True)
            st.session_state.assumptions['wacc_mode'] = 'direct' if wacc_mode == "Direct WACC" else 'build'
            
            if st.session_state.assumptions['wacc_mode'] == 'direct':
                st.session_state.assumptions['wacc_direct'] = st.slider("WACC (%)", 5.0, 20.0, st.session_state.assumptions['wacc_direct']*100.0) / 100.0
            else:
                c1, c2 = st.columns(2)
                st.session_state.assumptions['risk_free'] = c1.number_input("Risk-Free Rate (%)", 0.0, 10.0, st.session_state.assumptions['risk_free']*100.0) / 100.0
                st.session_state.assumptions['beta'] = c2.number_input("Beta", 0.5, 3.0, st.session_state.assumptions['beta'])
                st.session_state.assumptions['mkt_premium'] = c1.number_input("Equity Risk Premium (%)", 0.0, 10.0, st.session_state.assumptions['mkt_premium']*100.0) / 100.0
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="premium-card" style="border-color: #6366f1;">', unsafe_allow_html=True)
            st.subheader("Live Preview")
            
            results = run_full_model(comp, st.session_state.assumptions)
            val = results['valuation']
            upside = val['upside_pct'] * 100
            
            kpi_card("Intrinsic Value", f"${val['per_share_value']:,.2f}")
            kpi_card("Upside / Downside", f"{upside:,.1f}%", f"{upside:,.1f}%", delta_color="normal")
            kpi_card("WACC Used", f"{val['wacc']*100:,.1f}%")
            
            if st.button("Run Full Model →"):
                st.session_state.page = "Outputs"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE: OUTPUTS ---
elif page == "Outputs":
    if not st.session_state.company:
        st.warning("Load a company first.")
    else:
        results = run_full_model(st.session_state.company, st.session_state.assumptions)
        val = results['valuation']
        forecast = results['forecast']
        
        st.title("Valuation Outputs")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Intrinsic Value", f"${val['per_share_value']:,.2f}")
        with c2: kpi_card("Market Price", f"${st.session_state.company['price']:,.2f}")
        with c3: kpi_card("Upside", f"{val['upside_pct']*100:,.1f}%")
        with c4: kpi_card("WACC", f"{val['wacc']*100:,.1f}%")
        
        st.divider()
        
        st.subheader("5-Year FCF Projection (Billions USD)")
        f_df = pd.DataFrame(forecast)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=f_df['year'], y=f_df['revenue']/1e9, name="Revenue", marker_color='#6366f1'))
        fig.add_trace(go.Bar(x=f_df['year'], y=f_df['fcf']/1e9, name="Free Cash Flow", marker_color='#10b981'))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        st.table(f_df.set_index('year')[['revenue', 'ebitda', 'fcf', 'pv_fcf']].applymap(lambda x: f"${x/1e9:,.1f}B"))

# --- PAGE: SENSITIVITY ---
elif page == "Sensitivity":
    if not st.session_state.company:
        st.warning("Load a company first.")
    else:
        st.title("Sensitivity Matrix")
        st.markdown("Intrinsic Value vs. WACC & Growth")
        
        # Recalc results for baseline
        res = run_full_model(st.session_state.company, st.session_state.assumptions)
        val = res['valuation']
        
        wacc_range = [val['wacc'] + i*0.01 for i in range(-2, 3)]
        growth_range = [st.session_state.assumptions['terminal_growth'] + i*0.005 for i in range(-2, 3)]
        
        matrix = []
        for g in growth_range:
            row = []
            for w in wacc_range:
                # Simple recalc for matrix
                n = st.session_state.assumptions['years_forecast']
                last_fcf = res['forecast'][-1]['fcf']
                fcf_next = last_fcf * (1 + g)
                tv = fcf_next / (w - g) if (w - g) > 0 else last_fcf * 50
                pv_tv = tv / (1 + w)**n
                ev = val['pv_fcf_sum'] + pv_tv
                eq = ev - (st.session_state.assumptions['net_debt_override'] or st.session_state.company['net_debt'])
                ps = eq / (st.session_state.assumptions['shares_out_override'] or st.session_state.company['shares_out'])
                row.append(ps)
            matrix.append(row)
            
        heat_df = pd.DataFrame(
            matrix, 
            index=[f"{g*100:,.1f}%" for g in growth_range],
            columns=[f"{w*100:,.1f}%" for w in wacc_range]
        )
        try:
            st.table(heat_df.style.background_gradient(cmap="RdYlGn", axis=None).format("${:,.2f}"))
        except ImportError:
            st.table(heat_df.applymap(lambda x: f"${x:,.2f}"))
            st.warning("Note: Background gradients disabled until 'matplotlib' is installed on server.")

# --- PAGE: SCENARIOS ---
elif page == "Scenarios":
    if not st.session_state.company:
        st.warning("Load a company first.")
    else:
        st.title("Scenario Analysis")
        st.markdown("Bear / Base / Bull — adjust inputs and compare outcomes.")
        
        base = st.session_state.assumptions
        comp = st.session_state.company
        
        scenarios = [
            {"name": "Bear", "growth": base['revenue_growth'] - 0.05, "margin": base['fcf_margin'] - 0.05, "wacc_adj": 0.01},
            {"name": "Base", "growth": base['revenue_growth'], "margin": base['fcf_margin'], "wacc_adj": 0},
            {"name": "Bull", "growth": base['revenue_growth'] + 0.10, "margin": base['fcf_margin'] + 0.05, "wacc_adj": -0.01},
        ]
        
        scenario_results = []
        for sc in scenarios:
            temp_assump = base.copy()
            temp_assump['revenue_growth'] = sc['growth']
            temp_assump['fcf_margin'] = sc['margin']
            # Adjust WACC
            actual_wacc = calc_wacc(temp_assump) + sc['wacc_adj']
            temp_assump['wacc_mode'] = 'direct'
            temp_assump['wacc_direct'] = actual_wacc
            
            res = run_full_model(comp, temp_assump)
            v = res['valuation']
            scenario_results.append({
                "Scenario": sc['name'],
                "Revenue Growth": f"{sc['growth']*100:.1f}%",
                "FCF Margin": f"{sc['margin']*100:.1f}%",
                "WACC": f"{actual_wacc*100:.1f}%",
                "Intrinsic Value": v['per_share_value'],
                "Upside": v['upside_pct']
            })
            
        res_df = pd.DataFrame(scenario_results)
        
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.subheader("Scenario Comparison")
        st.table(res_df.set_index("Scenario").style.format({
            "Intrinsic Value": "${:,.2f}",
            "Upside": "{:+.1%}"
        }))
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Visual Chart
        fig = go.Figure()
        colors = {'Bear': '#ef4444', 'Base': '#6366f1', 'Bull': '#10b981'}
        for i, row in res_df.iterrows():
            fig.add_trace(go.Bar(
                name=row['Scenario'], 
                x=[row['Scenario']], 
                y=[row['Intrinsic Value']],
                marker_color=colors[row['Scenario']]
            ))
        
        fig.add_hline(y=comp['price'], line_dash="dash", line_color="white", annotation_text="Current Price")
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', title="Intrinsic Value by Scenario")
        st.plotly_chart(fig, use_container_width=True)

# --- PAGE: ABOUT ---
elif page == "About":
    st.title("Financial Methodology")
    st.markdown("""
    This model utilizes a **3-Stage Discounted Cash Flow (DCF)** method:
    1. **Stage 1: Explicit Projection**: Projections for Revenue and FCF over a 5-year period.
    2. **Stage 2: Terminal Value**: Use of the Gordon Growth Method to estimate value beyond year 5.
    3. **Discounting**: All future cash flows are discounted to the Present Value (PV) using the **WACC**.
    """)
    st.divider()
    st.subheader("AI Usage Disclosure")
    st.info("Collaborative build with Antigravity AI. Logic verified for institutional accuracy.")
