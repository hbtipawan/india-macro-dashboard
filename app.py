# ─────────────────────────────────────────────────────────────────────────────
#  🇮🇳  India Macro Intelligence Dashboard  |  Streamlit Cloud Ready
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🇮🇳 India Macro Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "India Macro Intelligence Dashboard | Built with Streamlit + yfinance"
    }
)

# ── AUTO REFRESH every 5 minutes ─────────────────────────────────────────────
st_autorefresh(interval=300_000, limit=None, key="macro_auto_refresh")

# ── DARK THEME CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0d1117; }
[data-testid="stHeader"]           { background:transparent; }
.block-container                   { padding:1rem 2rem; }
div[data-testid="metric-container"] {
    background:#161b22; border-radius:10px;
    padding:14px 18px; border:1px solid #30363d;
}
div[data-testid="metric-container"] label {
    color:#8b949e !important; font-size:12px;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color:#e6edf3 !important; font-size:20px; font-weight:700;
}
h2,h3 { color:#e6edf3; }
.section-hdr {
    background:linear-gradient(90deg,#1f2937,#111827);
    border-left:4px solid #58a6ff;
    padding:8px 16px; border-radius:6px;
    color:#e6edf3; font-size:15px; font-weight:600; margin:12px 0 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  CONFIG TABLES
# ═════════════════════════════════════════════════════════════════════════════
MARKET_TICKERS = {
    "Nifty 50":     ("^NSEI",      "pts", False),
    "Sensex":       ("^BSESN",     "pts", False),
    "India VIX":    ("^INDIAVIX",  "",    True),
    "USD/INR":      ("INR=X",      "₹",   True),
    "Brent Crude":  ("BZ=F",       "$",   True),
    "Gold (USD)":   ("GC=F",       "$",   True),
    "Silver (USD)": ("SI=F",       "$",   True),
    "Copper (USD)": ("HG=F",       "$",   False), # Dr. Copper = growth indicator
    "US 10Y Yield": ("^TNX",       "%",   True),
    "DXY":          ("DX-Y.NYB",   "",    True),
    "S&P 500":      ("^GSPC",      "pts", False),
    "Nasdaq 100":   ("^NDX",       "pts", False), # Tech & Risk proxy
    "Russell 2000": ("^RUT",       "pts", False), # Global small-cap risk proxy
    "MSCI EM ETF":  ("EEM",        "$",   False),
    "Bitcoin":      ("BTC-USD",    "$",   False), # Pure liquidity indicator
}

SECTOR_TICKERS = {
    "Nifty Bank":   "^NSEBANK",
    "Nifty IT":     "^CNXIT",
    "Nifty Auto":   "^CNXAUTO",
    "Nifty FMCG":   "^CNXFMCG",
    "Nifty Metal":  "^CNXMETAL",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty Realty": "^CNXREALTY",
    "Nifty Energy": "^CNXENERGY",
    "Nifty Infra":  "^CNXINFRA",
    "Nifty Consum": "^CNXCONSUM",
    "Nifty Media":  "^CNXMEDIA",
    "Nifty PSE":    "^CNXPSE",
}

CHART_PAIRS = {
    "Nifty vs USD/INR":      ("^NSEI","INR=X",   "Inverse","#f78166"),
    "Nifty vs Crude Oil":    ("^NSEI","BZ=F",    "Inverse","#ffab40"),
    "Nifty vs Gold":         ("^NSEI","GC=F",    "Inverse","#ffd700"),
    "Nifty vs US 10Y Yield": ("^NSEI","^TNX",    "Inverse","#c084fc"),
    "Nifty vs DXY":          ("^NSEI","DX-Y.NYB","Inverse","#fb923c"),
    "Nifty vs Nasdaq 100":   ("^NSEI","^NDX",    "Direct", "#38bdf8"),
    "Nifty vs Copper":       ("^NSEI","HG=F",    "Direct", "#d97706"),
}

WB_INDICATORS = {
    "GDP Growth (%)":           ("NY.GDP.MKTP.KD.ZG",  "Direct"),
    "CPI Inflation (%)":        ("FP.CPI.TOTL.ZG",     "Inverse"),
    "Current Account (% GDP)":  ("BN.CAB.XOKA.GD.ZS",  "Inverse"),
    "Unemployment (%)":         ("SL.UEM.TOTL.ZS",      "Inverse"),
    "FDI Net Inflows (% GDP)":  ("BX.KLT.DINV.WD.GD.ZS","Direct"),
    "Gross Capital Formation (%)":("NE.GDI.TOTL.ZS",   "Direct"),
}

ALL_MACRO = [
    ("GDP Growth Rate",           "Direct",  "Strong",   "Higher GDP → corporate earnings → market up"),
    ("IIP (Industrial Output)",   "Direct",  "Moderate", "Manufacturing health; leads Nifty by 1-2 months"),
    ("RBI Repo Rate",             "Inverse", "Strong",   "Rate hike → cost of capital rises → P/E compression"),
    ("CPI Inflation",             "Inverse", "Moderate", "High CPI → RBI tightening → market corrects"),
    ("WPI Inflation",             "Inverse", "Moderate", "WPI rise → margin squeeze for corporates"),
    ("Fiscal Deficit (% GDP)",    "Inverse", "Moderate", "High deficit → bond yield spike + crowding out"),
    ("Govt Capital Expenditure",  "Direct",  "Strong",   "Capex drives infra & PSU sector earnings"),
    ("Money Supply (M3)",         "Direct",  "Strong",   "More liquidity → equities attract higher valuations"),
    ("10Y G-Sec Bond Yield",      "Inverse", "Strong",   "Rising yields make FDs attractive; reduces equity P/E"),
    ("USD/INR Exchange Rate",     "Inverse", "Strong",   "Rupee fall → FII outflows + import cost spike"),
    ("Brent Crude Oil Price",     "Inverse", "Strong",   "India imports 85% oil; $10 rise = $15B extra cost"),
    ("Forex Reserves",            "Direct",  "Moderate", "High reserves → macro stability → FII confidence"),
    ("Current Account Deficit",   "Inverse", "Moderate", "Wider CAD → rupee pressure → capital outflows"),
    ("FII / FPI Net Flows",       "Direct",  "Strong",   "Single most powerful short-term Nifty driver"),
    ("DII Net Flows",             "Direct",  "Moderate", "Counter-cyclical buffer via SIP inflows"),
    ("FDI Inflows",               "Direct",  "Moderate", "Long-term confidence; GDP and market expand together"),
    ("Gold Price (USD)",          "Inverse", "Moderate", "Safe-haven; risk-off = gold up, equities down"),
    ("Silver Price (USD)",        "Direct",  "Moderate", "Industrial demand proxy; follows risk-on capital flows"),
    ("Copper (Dr. Copper)",       "Direct",  "Moderate", "Leading indicator of global industrial/manufacturing health"),
    ("US Fed Funds Rate",         "Inverse", "Strong",   "Fed hike → EM outflows → Nifty sells off"),
    ("US Dollar Index (DXY)",     "Inverse", "Strong",   "Strong dollar → FII exits India → INR weakens"),
    ("Nasdaq 100",                "Direct",  "Strong",   "Global tech/growth proxy; highly correlated to Nifty IT"),
    ("Russell 2000",              "Direct",  "Moderate", "US Small-cap index; gauge of global speculative risk appetite"),
    ("Bitcoin",                   "Direct",  "Moderate", "Ultimate liquidity proxy; signals global risk-on/risk-off sentiment"),
    ("Global PMI / US GDP",       "Direct",  "Moderate", "IT & export sectors track global demand cycle"),
    ("India VIX",                 "Inverse", "Strong",   "Fear index; VIX > 20 = market stress zone"),
    ("GST Collections",           "Direct",  "Moderate", "Proxy for domestic consumption activity"),
    ("Corporate EPS Growth",      "Direct",  "Strong",   "Most direct driver: Nifty = EPS × P/E multiple"),
]

# ═════════════════════════════════════════════════════════════════════════════
#  DATA HELPERS
# ═════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_price(ticker: str):
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info
        return float(fi.last_price), float(fi.previous_close)
    except Exception:
        return None, None

@st.cache_data(ttl=300, show_spinner=False)
def get_history(ticker: str, period: str = "2y") -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[["Close"]].dropna()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=86400, show_spinner=False)
def world_bank(code: str, country: str = "IN") -> pd.DataFrame:
    url = (f"https://api.worldbank.org/v2/country/{country}/indicator/{code}"
           f"?format=json&per_page=50&mrv=35")
    try:
        r = requests.get(url, timeout=15)
        raw = r.json()
        if len(raw) > 1 and raw[1]:
            df = pd.DataFrame(raw[1])[["date", "value"]].dropna()
            df["date"] = pd.to_numeric(df["date"])
            return df.sort_values("date").reset_index(drop=True)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ─── Utility ─────────────────────────────────────────────────────────────────
def fmt_val(val, unit):
    if val is None:
        return "N/A"
    return f"{unit}{val:,.2f}" if unit in ["$","₹"] else f"{val:,.2f}{unit}"

def pct_chg(curr, prev):
    if None in (curr, prev) or prev == 0:
        return None
    return (curr - prev) / prev * 100

def signal_badge(pct, inverse=False):
    if pct is None:
        return "⚪ Neutral", "#6e7681"
    eff = -pct if inverse else pct
    if abs(eff) < 0.2:
        return "⚪ Neutral", "#6e7681"
    return ("🟢 Bullish", "#238636") if eff > 0 else ("🔴 Bearish", "#da3633")

def cell_color(val):
    if "Bullish" in str(val):
        return "background-color:#1a3a2e;color:#3fb950"
    if "Bearish" in str(val):
        return "background-color:#3a1a1a;color:#f85149"
    if val == "Direct":
        return "background-color:#1a3a2e;color:#3fb950"
    if val == "Inverse":
        return "background-color:#3a1a1a;color:#f85149"
    if val == "Strong":
        return "color:#e6edf3;font-weight:bold"
    return "background-color:#161b22;color:#8b949e"

def dual_axis_chart(t1, t2, l1, l2, period, color2):
    d1 = get_history(t1, period)
    d2 = get_history(t2, period)
    if d1.empty or d2.empty:
        return None, None
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=d1.index, y=d1["Close"], name=l1,
                             line=dict(color="#58a6ff", width=1.6)), secondary_y=False)
    fig.add_trace(go.Scatter(x=d2.index, y=d2["Close"], name=l2,
                             line=dict(color=color2, width=1.6)), secondary_y=True)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
        height=390, margin=dict(l=0, r=0, t=35, b=0),
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", bgcolor="rgba(0,0,0,0)"),
        font=dict(color="#8b949e", size=12),
        xaxis=dict(gridcolor="#21262d", showgrid=True),
        yaxis=dict(title=l1, gridcolor="#21262d"),
        yaxis2=dict(title=l2, gridcolor="#21262d"),
    )
    m1 = d1["Close"].resample("ME").last()
    m2 = d2["Close"].resample("ME").last()
    combined = pd.concat([m1, m2], axis=1).dropna()
    corr = float(combined.corr().iloc[0, 1]) if len(combined) > 5 else None
    return fig, corr

# ═════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🇮🇳 India Macro Dashboard")
    st.caption(f"🕐 {datetime.now().strftime('%d %b %Y  %I:%M %p IST')}")
    st.caption("⏱ Auto-refreshes every 5 minutes")
    st.divider()

    chart_period = st.selectbox("📅 Chart Lookback Period",
                                ["6mo","1y","2y","5y","max"], index=2)
    st.divider()
    show_sectors = st.toggle("🏭 NSE Sector Heatmap", value=True)
    show_charts  = st.toggle("📈 Correlation Charts",  value=True)
    show_wb      = st.toggle("🌍 World Bank Data",     value=True)
    show_ref     = st.toggle("📋 Full Reference Table",value=True)
    st.divider()
    st.markdown("""
**📡 Data Sources**
- Yahoo Finance (`yfinance`)
- World Bank Open API
- Auto-refresh: every 5 min

**🔑 Legend**
| Color | Meaning |
|-------|---------|
| 🟢 | Bullish for Nifty |
| 🔴 | Bearish for Nifty |
| ⚪ | Neutral / No data |
""")

# ═════════════════════════════════════════════════════════════════════════════
#  HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,#0d1117,#161b22);
            border:1px solid #30363d;border-radius:12px;
            padding:20px 28px;margin-bottom:18px;">
  <h1 style="color:#e6edf3;margin:0;font-size:26px;">
    🇮🇳 India Macro Intelligence Dashboard
  </h1>
  <p style="color:#8b949e;margin:6px 0 0;font-size:13px;">
    Real-time tracker for macro & liquidity indicators that drive Indian equities
    &nbsp;|&nbsp; Nifty 50 / BSE Sensex &nbsp;|&nbsp; Auto-refresh every 5 min
  </p>
</div>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  SECTION 1 ─ MARKET PULSE
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-hdr">📊 Section 1 — Market Pulse (Live)</div>',
            unsafe_allow_html=True)

t_items = list(MARKET_TICKERS.items())
cols = st.columns(5) # Dynamic scaling
for i, (name, (tick, unit, inv)) in enumerate(t_items):
    price, prev = get_price(tick)
    pct = pct_chg(price, prev)
    badge, _ = signal_badge(pct, inv)
    icon = badge[:2]
    delta = f"{pct:+.2f}%" if pct is not None else "N/A"
    
    with cols[i % 5]:
        st.metric(label=f"{icon} {name}", value=fmt_val(price, unit), delta=delta)

# ═════════════════════════════════════════════════════════════════════════════
#  SECTION 2 ─ MACRO SIGNAL SCORECARD
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-hdr">🎯 Section 2 — Daily Macro Signal Scorecard</div>',
            unsafe_allow_html=True)

rows = []
for name, (tick, unit, inv) in MARKET_TICKERS.items():
    price, prev = get_price(tick)
    pct = pct_chg(price, prev)
    badge, _ = signal_badge(pct, inv)
    rows.append({
        "Indicator":      name,
        "Current Value":  fmt_val(price, unit),
        "Daily Change":   f"{pct:+.2f}%" if pct else "N/A",
        "Market Relation":"Inverse" if inv else "Direct",
        "Market Signal":  badge,
    })

df_score = pd.DataFrame(rows)
styled_score = (
    df_score.style
    .map(cell_color, subset=["Market Signal", "Market Relation"])
    .set_properties(**{"background-color": "#161b22", "color": "#e6edf3",
                       "border": "1px solid #30363d"})
)
st.dataframe(styled_score, use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
#  SECTION 3 ─ NSE SECTOR HEATMAP
# ═════════════════════════════════════════════════════════════════════════════
if show_sectors:
    st.markdown('<div class="section-hdr">🏭 Section 3 — NSE Sector Heatmap (Live)</div>',
                unsafe_allow_html=True)
    sec_items = list(SECTOR_TICKERS.items())
    s_cols = st.columns(4) # Dynamic scaling
    for i, (sname, stick) in enumerate(sec_items):
        sp, sprev = get_price(stick)
        spct = pct_chg(sp, sprev)
        sbadge, _ = signal_badge(spct, inverse=False)
        icon = sbadge[:2]
        with s_cols[i % 4]:
            st.metric(
                label=f"{icon} {sname}",
                value=fmt_val(sp, ""),
                delta=f"{spct:+.2f}%" if spct else "N/A"
            )

# ═════════════════════════════════════════════════════════════════════════════
#  SECTION 4 ─ HISTORICAL CORRELATION CHARTS
# ═════════════════════════════════════════════════════════════════════════════
if show_charts:
    st.markdown('<div class="section-hdr">📈 Section 4 — Historical Correlation Charts</div>',
                unsafe_allow_html=True)
    tabs = st.tabs(list(CHART_PAIRS.keys()))
    for tab, (tab_name, (t1, t2, expected, color)) in zip(tabs, CHART_PAIRS.items()):
        with tab:
            parts = tab_name.split(" vs ")
            fig, corr = dual_axis_chart(t1, t2, parts[0], parts[1], chart_period, color)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                if corr is not None:
                    observed = ("Inverse" if corr < -0.1 else
                                ("Direct" if corr > 0.1 else "No clear relation"))
                    match = ("✅ Matches expectation"
                             if (expected == "Inverse" and corr < -0.1) or
                                (expected == "Direct"  and corr > 0.1)
                             else "⚠️ Diverging — context needed")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Pearson Correlation (r)", f"{corr:.3f}")
                    c2.metric("Observed Relationship", f"{'📉' if observed=='Inverse' else '📈'} {observed}")
                    c3.metric("Expected vs Actual", match)
            else:
                st.warning(f"⚠️ Could not load chart data for {tab_name}.")

# ═════════════════════════════════════════════════════════════════════════════
#  SECTION 5 ─ WORLD BANK MACRO DATA
# ═════════════════════════════════════════════════════════════════════════════
if show_wb:
    st.markdown('<div class="section-hdr">🌍 Section 5 — World Bank Macro Indicators (India, Annual)</div>',
                unsafe_allow_html=True)
    wb_rows = []
    for label, (code, relation) in WB_INDICATORS.items():
        df_wb = world_bank(code)
        if not df_wb.empty and len(df_wb) >= 2:
            latest  = df_wb.iloc[-1]
            prev_r  = df_wb.iloc[-2]
            chg     = latest["value"] - prev_r["value"]
            bull    = (chg > 0 and relation == "Direct") or (chg < 0 and relation == "Inverse")
            signal  = "🟢 Bullish" if bull else "🔴 Bearish"
        else:
            latest  = type("obj", (object,), {"value": None, "date": "-"})()
            chg     = None
            signal  = "⚪ Loading…"
        wb_rows.append({
            "Indicator":      label,
            "Latest Value":   f"{latest.value:.2f}%" if latest.value else "Fetching…",
            "Year":           int(latest.date) if str(latest.date).isdigit() else "-",
            "YoY Change":     f"{chg:+.2f}%" if chg is not None else "-",
            "Market Relation":relation,
            "Market Signal":  signal,
        })

    df_wb_disp = pd.DataFrame(wb_rows)
    st.dataframe(
        df_wb_disp.style
        .map(cell_color, subset=["Market Signal","Market Relation"])
        .set_properties(**{"background-color":"#161b22","color":"#e6edf3",
                           "border":"1px solid #30363d"}),
        use_container_width=True, hide_index=True
    )

    # ── GDP 30-year bar chart ──────────────────────────────────────────────
    df_gdp = world_bank("NY.GDP.MKTP.KD.ZG")
    if not df_gdp.empty:
        st.markdown("###### 🇮🇳 India GDP Growth Rate — 30-Year Trend")
        fig_gdp = go.Figure(go.Bar(
            x=df_gdp["date"], y=df_gdp["value"],
            marker_color=["#238636" if v >= 0 else "#da3633" for v in df_gdp["value"]],
            text=[f"{v:.1f}%" for v in df_gdp["value"]],
            textposition="outside",
        ))
        fig_gdp.update_layout(
            template="plotly_dark",
            paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
            height=320, margin=dict(l=0,r=0,t=30,b=0),
            yaxis_title="GDP Growth (%)",
            font=dict(color="#8b949e"),
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(gridcolor="#21262d"),
        )
        st.plotly_chart(fig_gdp, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
#  SECTION 6 ─ COMPLETE MACRO REFERENCE TABLE
# ═════════════════════════════════════════════════════════════════════════════
if show_ref:
    st.markdown('<div class="section-hdr">📋 Section 6 — Complete Macro Reference</div>',
                unsafe_allow_html=True)
    df_ref = pd.DataFrame(ALL_MACRO,
                          columns=["Macro Indicator","Relation","Strength","Rationale"])
    st.dataframe(
        df_ref.style
        .map(cell_color, subset=["Relation","Strength"])
        .set_properties(**{"background-color":"#161b22","color":"#e6edf3",
                           "border":"1px solid #30363d","font-size":"13px"}),
        use_container_width=True, hide_index=True
    )

# ═════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown(f"""
<div style="background:#161b22;border-radius:10px;padding:16px;border:1px solid #30363d;">
  <p style="color:#8b949e;font-size:12px;margin:0;line-height:1.8;">
    <b style="color:#e6edf3;">📡 Data:</b> Yahoo Finance (yfinance) &nbsp;|&nbsp;
    World Bank Open API &nbsp;|&nbsp; All free, no API keys required<br>
    <b style="color:#e6edf3;">⏱ Market data</b> refreshes every 5 min &nbsp;|&nbsp;
    <b style="color:#e6edf3;">World Bank data</b> refreshes daily<br>
    <b style="color:#e6edf3;">⚡ Last refreshed:</b>
    {datetime.now().strftime("%d %b %Y, %I:%M:%S %p IST")}
  </p>
</div>
""", unsafe_allow_html=True)
