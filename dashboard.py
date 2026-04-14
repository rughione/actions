import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import os
import time

# 1. Configurazione Iniziale
st.set_page_config(page_title="Alpha Intelligence Terminal", layout="wide", initial_sidebar_state="expanded")
HISTORY_FILE = "alpha_tracker_final.csv"

if 'scan_results' not in st.session_state:
    st.session_state['scan_results'] = []

# 2. Liste Mercati
MARKETS = {
    "🇺🇸 USA (S&P 100)": {"tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "PG", "COST"], "index": "^GSPC"},
    "🇪🇺 Europa (Blue Chips)": {"tickers": ["ENI.MI", "UCG.MI", "ISP.MI", "MC.PA", "OR.PA", "ASML", "SAP", "SIE.DE", "TTE.PA"], "index": "^STOXX50E"}
}

# 3. CSS AVANZATO: "Cyber-Finance Black"
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&family=Space+Grotesk:wght@500;700&display=swap');

    /* Sfondo e Font Generale */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050505;
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
    }

    /* Nascondere Header/Footer Streamlit per Look Pro */
    header, footer {visibility: hidden;}

    /* Styling delle Tab */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: transparent;
        border-radius: 4px 4px 0px 0px; border: none; color: #888; font-weight: 400;
    }
    .stTabs [aria-selected="true"] { color: #00FF88 !important; border-bottom: 2px solid #00FF88 !important; font-weight: 700 !important; }

    /* CARD DESIGN: Glassmorphism */
    .opportunity-card {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .opportunity-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 136, 0.3);
        box-shadow: 0 8px 32px rgba(0, 255, 136, 0.1);
        transform: translateY(-4px);
    }

    /* Tipografia e Badge */
    .company-title { font-size: 24px; font-weight: 700; color: #FFFFFF; letter-spacing: -0.5px; }
    .ticker-box {
        background: #1A1A1A; color: #00FF88; padding: 3px 10px; border-radius: 6px;
        font-family: 'Space Grotesk', sans-serif; font-size: 14px; border: 1px solid #333; margin-left: 10px;
    }
    .badge-buy {
        background: linear-gradient(135deg, #00FF88 0%, #00BD65 100%);
        color: #000; padding: 6px 14px; border-radius: 20px; font-weight: 800; font-family: 'Space Grotesk', sans-serif;
    }

    /* Metriche */
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }
    .m-item { border-left: 1px solid #333; padding-left: 15px; }
    .m-label { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
    .m-value { color: #FFF; font-family: 'Space Grotesk', sans-serif; font-size: 19px; font-weight: 700; }

    /* Bottoni Custom */
    div.stButton > button {
        background: #111; color: #EEE; border: 1px solid #333; border-radius: 8px;
        padding: 8px 20px; font-weight: 600; transition: 0.3s;
    }
    div.stButton > button:hover { border-color: #00FF88; color: #00FF88; background: #000; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI CORE (TUA LOGICA ORIGINALE) ---
def load_history():
    if os.path.exists(HISTORY_FILE): return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame(columns=["Data", "Ticker", "Prezzo_In", "Prezzo_Attuale", "Perf_Stock", "Perf_Bench", "Alpha", "Score", "Status", "Index"])

def get_bench_perf(index_ticker, start_date):
    try:
        data = yf.download(index_ticker, start=start_date, progress=False)['Close']
        perf = ((data.iloc[-1] / data.iloc[0]) - 1) * 100
        return float(perf)
    except: return 0.0

def analyze_stock(symbol):
    try:
        t = yf.Ticker(symbol); i = t.info
        p = i.get('currentPrice', 0); target = i.get('targetMeanPrice', 0)
        score = sum([p < target, i.get('trailingPE', 100) < 22, i.get('returnOnEquity', 0) > 0.15, i.get('recommendationKey') in ['buy', 'strong_buy']])
        return {"Ticker": symbol, "Nome": i.get('shortName', symbol), "Price": p, "Target": target, "Score": score, "PE": round(i.get('trailingPE', 0), 1), "ROE": f"{round(i.get('returnOnEquity', 0)*100, 1)}%"}
    except: return None

# --- INTERFACCIA ---
st.title("🏛️ Alpha Intelligence Terminal")

tab1, tab2 = st.tabs(["🔍 SCREENER MERCATI", "📊 REGISTRO & STRESS TEST"])

with tab1:
    col_a, col_b = st.columns([2, 1])
    m_choice = col_a.selectbox("Seleziona Mercato", list(MARKETS.keys()))
    threshold = col_b.slider("Filtra per Score minimo", 1, 4, 3)

    if st.button("AVVIA SCANSIONE SISTEMA"):
        st.session_state['scan_results'] = []
        progress = st.progress(0)
        temp_res = []
        tickers = MARKETS[m_choice]["tickers"]
        for i, t in enumerate(tickers):
            data = analyze_stock(t)
            if data and data['Score'] >= threshold:
                temp_res.append(data)
            progress.progress((i + 1) / len(tickers))
        st.session_state['scan_results'] = temp_res

    for d in st.session_state['scan_results']:
        with st.container():
            st.markdown(f"""
            <div class="opportunity-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="company-title">{d['Nome']}</span>
                        <span class="ticker-box">{d['Ticker']}</span>
                    </div>
                    <span class="badge-buy">SCORE {d['Score']} / 4</span>
                </div>
                <div class="metric-grid">
                    <div class="m-item"><div class="m-label">Prezzo</div><div class="m-value">$ {d['Price']}</div></div>
                    <div class="m-item"><div class="m-label">Target</div><div class="m-value" style="color:#00FF88;">$ {d['Target']}</div></div>
                    <div class="m-item"><div class="m-label">P/E Ratio</div><div class="m-value">{d['PE']}</div></div>
                    <div class="m-item"><div class="m-label">ROE</div><div class="m-value">{d['ROE']}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Monitora {d['Ticker']}", key=f"save_{d['Ticker']}"):
                df = load_history()
                if d['Ticker'] not in df['Ticker'].values:
                    new_row = {"Data": datetime.date.today(), "Ticker": d['Ticker'], "Prezzo_In": d['Price'], "Prezzo_Attuale": d['Price'], 
                               "Perf_Stock": "0%", "Perf_Bench": "0%", "Alpha": "0%", "Score": d['Score'], "Status": "OK", "Index": MARKETS[m_choice]["index"]}
                    pd.concat([df, pd.DataFrame([new_row])]).to_csv(HISTORY_FILE, index=False)
                    st.toast(f"System: {d['Ticker']} registrato.")

with tab2:
    st.subheader("Performance Intelligence")
    df_h = load_history()
    if not df_h.empty:
        if st.button("🚀 ESEGUI STRESS TEST & ANALISI ALPHA"):
            with st.spinner("Aggiornamento dati in corso..."):
                for idx, row in df_h.iterrows():
                    stock_data = analyze_stock(row['Ticker'])
                    if stock_data:
                        s_perf = ((stock_data['Price'] / row['Prezzo_In']) - 1) * 100
                        b_perf = get_bench_perf(row['Index'], row['Data'])
                        alpha = s_perf - b_perf
                        status = "MANTENERE" if stock_data['Score'] >= 2 else "PERICOLO"
                        df_h.at[idx, 'Prezzo_Attuale'] = stock_data['Price']
                        df_h.at[idx, 'Perf_Stock'] = f"{round(s_perf, 2)}%"
                        df_h.at[idx, 'Perf_Bench'] = f"{round(b_perf, 2)}%"
                        df_h.at[idx, 'Alpha'] = f"{round(alpha, 2)}%"
                        df_h.at[idx, 'Score'] = stock_data['Score']
                        df_h.at[idx, 'Status'] = status
                df_h.to_csv(HISTORY_FILE, index=False)
                st.rerun()

        st.data_editor(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Nessun titolo in monitoraggio attivo.")
