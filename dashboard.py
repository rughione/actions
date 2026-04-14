import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import os
import time

# 1. Configurazione Iniziale
st.set_page_config(page_title="Alpha Intelligence Terminal", layout="wide")
HISTORY_FILE = "alpha_tracker_final.csv"

if 'scan_results' not in st.session_state:
    st.session_state['scan_results'] = []

# 2. Liste Mercati Ripristinate
MARKETS = {
    "🇺🇸 USA (S&P 100)": {"tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "PG", "COST"], "index": "^GSPC"},
    "🇪🇺 Europa (Blue Chips)": {"tickers": ["ENI.MI", "UCG.MI", "ISP.MI", "MC.PA", "OR.PA", "ASML", "SAP", "SIE.DE", "TTE.PA"], "index": "^STOXX50E"}
}

# 3. CSS per Massimo Contrasto (Ticker Bianchi)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; background-color: #050505; color: #ffffff; }
    .main { background-color: #050505; }
    .opportunity-card {
        background: linear-gradient(135deg, #111111 0%, #1a1a1a 100%);
        border: 1px solid #333; padding: 20px; border-radius: 12px; margin-bottom: 15px;
    }
    .metric-label { color: #aaaaaa; font-size: 11px; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 20px; font-weight: bold; }
    .badge-buy { background-color: #00c805; color: black; padding: 4px 10px; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI CORE ---
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
tab1, tab2 = st.tabs(["🔍 Screener Mercati", "📊 Registro & Stress Test"])

with tab1:
    col1, col2 = st.columns([2, 1])
    m_choice = col1.selectbox("Seleziona Mercato", list(MARKETS.keys()))
    threshold = col2.slider("Score minimo", 1, 4, 3)

    if st.button("AVVIA SCANSIONE"):
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
                        <span style="color: #ffffff; font-size: 22px; font-weight: bold;">{d['Nome']}</span> 
                        <span style="color: #ffffff; font-size: 18px; margin-left:10px; border: 1px solid #444; padding: 2px 6px; border-radius: 4px;">{d['Ticker']}</span>
                    </div>
                    <span class="badge-buy">SCORE: {d['Score']}/4</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 15px;">
                    <div class="metric-item"><p class="metric-label">Prezzo</p><p class="metric-value">{d['Price']} $</p></div>
                    <div class="metric-item"><p class="metric-label">Target</p><p class="metric-value" style="color:#00c805;">{d['Target']} $</p></div>
                    <div class="metric-item"><p class="metric-label">P/E Ratio</p><p class="metric-value">{d['PE']}</p></div>
                    <div class="metric-item"><p class="metric-label">ROE</p><p class="metric-value">{d['ROE']}</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Monitora {d['Ticker']}", key=f"save_{d['Ticker']}"):
                df = load_history()
                if d['Ticker'] not in df['Ticker'].values:
                    new_row = {"Data": datetime.date.today(), "Ticker": d['Ticker'], "Prezzo_In": d['Price'], "Prezzo_Attuale": d['Price'], 
                               "Perf_Stock": "0%", "Perf_Bench": "0%", "Alpha": "0%", "Score": d['Score'], "Status": "OK", "Index": MARKETS[m_choice]["index"]}
                    pd.concat([df, pd.DataFrame([new_row])]).to_csv(HISTORY_FILE, index=False)
                    st.toast(f"{d['Ticker']} Salvato!")

with tab2:
    st.subheader("Performance vs Mercato & Stress Test")
    df_h = load_history()
    if not df_h.empty:
        if st.button("🚀 ESEGUI ANALISI PERFORMANCE & STRESS TEST"):
            with st.spinner("Calcolo Alpha e verifica fondamentali..."):
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
        st.info("Esegui una scansione e salva i titoli per vederli qui.")