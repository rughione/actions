import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import os
import time

# 1. Configurazione Iniziale
st.set_page_config(page_title="Alpha Elite Terminal", layout="wide", initial_sidebar_state="expanded")
HISTORY_FILE = "alpha_tracker_final.csv"

if 'scan_results' not in st.session_state:
    st.session_state['scan_results'] = []

# 2. Liste Mercati
MARKETS = {
    "🇺🇸 USA (S&P 100)": {"tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "PG", "COST"], "index": "^GSPC"},
    "🇪🇺 Europa (Blue Chips)": {"tickers": ["ENI.MI", "UCG.MI", "ISP.MI", "MC.PA", "OR.PA", "ASML", "SAP", "SIE.DE", "TTE.PA"], "index": "^STOXX50E"}
}

# 3. CSS AVANZATO: "Zenith Ethereal Fintech"
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&family=Space+Grotesk:wght@500;700&display=swap');

    /* Sfondo, Font Generale e Colori Base Muted */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #1A1A1A;
        font-family: 'Inter', sans-serif;
        color: #A0A0A0; /* Muted light grey per descrizioni/testi secondari */
    }

    /* Nascondere Header/Footer Streamlit */
    header, footer {visibility: hidden;}

    /* FIX ETICHETTE INVISIBILI (Labels dei selettori) */
    label[data-testid="stWidgetLabel"] p {
        color: #E0E0E0 !important; /* Molto chiaro ma non bianco puro */
        font-weight: 700 !important;
        font-size: 14px !important;
        letter-spacing: 0.5px;
    }

    /* component Styling (Pill-like, large border-radius) */
    .stSelectbox div[data-baseweb="select"] { background-color: #2A2A2A !important; border-radius: 12px !important; border-color: #333 !important; }
    .stSelectbox div[data-baseweb="select"]:hover { border-color: #96A582 !important; }
    
    /* PROGRESS BAR OLIVE GREEN */
    .stProgress div[role="progressbar"] > div { background-color: #96A582 !important; }

    /* STYLING DELLE TAB */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: transparent; }
    .stTabs [aria-selected="true"] { color: #96A582 !important; border-bottom: 2px solid #96A582 !important; font-weight: 700 !important; }

    /* CARD DESIGN: Glassmorphism Interattivo con bordi ampi */
    .opportunity-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px;
        border-radius: 20px; /* Grandi angoli arrotondati come nel design system */
        margin-bottom: 20px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .opportunity-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(150, 165, 130, 0.4); /* Accento Olive */
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transform: translateY(-5px);
    }

    /* Ticker, Nomi e Status */
    .company-title { font-size: 26px; font-weight: 700; color: #FFFFFF; letter-spacing: -1px; }
    .ticker-badge {
        background: #2A2A2A; color: #E0E0E0; padding: 4px 10px; border-radius: 6px;
        font-family: 'Space Grotesk', sans-serif; font-size: 14px; border: 1px solid #333; margin-left: 10px;
    }
    .pills-container { display: flex; gap: 10px; align-items: center; justify-content: flex-end; }
    .status-pill {
        font-family: 'Space Grotesk', sans-serif; font-size: 14px; font-weight: 700;
        padding: 8px 16px; border-radius: 20px; text-transform: uppercase;
    }
    .status-neutral { background: #333; color: #A0A0A0; }
    .status-sell { background: #CB9999; color: black; } /* Accento Coral/Rose per Strong Sell */
    .status-buy { background: #96A582; color: black; } /* Accento Olive Green per Buy/Score */

    /* Metriche: Bold Numbers, Muted Labels */
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 25px; }
    .m-item { border-left: 1px solid #333; padding-left: 20px; }
    .m-label { color: #888888 !important; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .m-value { color: #FFFFFF !important; font-family: 'Space Grotesk', sans-serif; font-size: 20px; font-weight: 700; }
    .m-upside { font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-top: 5px; display: inline-block; }
    .m-plus { background: #96A582; color: black; }
    .m-minus { background: #CB9999; color: black; }

    /* Bottoni Custom */
    div.stButton > button {
        background: #111111; color: white; border: 1px solid #333; border-radius: 12px;
        padding: 10px 24px; transition: 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    div.stButton > button:hover { border-color: #96A582; color: #96A582; box-shadow: 0 0 15px rgba(150, 165, 130, 0.2); }
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

# --- UI PRINCIPALE ---
st.title("🏛️ Alpha Elite Terminal")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 SCREENER MERCATI", "📊 REGISTRO & STRESS TEST"])

with tab1:
    col_a, col_b = st.columns([2, 1])
    m_choice = col_a.selectbox("Seleziona Mercato", list(MARKETS.keys()))
    threshold = col_b.slider("Filtra per Score minimo", 1, 4, 3)

    if st.button("EXECUTE SYSTEM SCAN"):
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
        if not temp_res:
            st.warning(f"Nessun titolo trovato con Score >= {threshold}. Prova ad abbassare il filtro.")

    # Visualizzazione persistente dalla memoria di sessione
    for d in st.session_state['scan_results']:
        score_class = "status-buy" if d['Score'] >= 3 else "status-neutral"
        upside = ((d['Target'] / d['Price']) - 1) * 100
        up_class = "m-plus" if upside > 0 else "m-minus"
        with st.container():
            st.markdown(f"""
            <div class="opportunity-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div><span class="company-title">{d['Nome']}</span><span class="ticker-badge">{d['Ticker']}</span></div>
                    <div class="pills-container">
                        <span class="status-pill {score_class}">Score {d['Score']} / 4</span>
                    </div>
                </div>
                <div class="metric-grid">
                    <div class="m-item"><div class="m-label">Prezzo</div><div class="m-value">$ {d['Price']}</div></div>
                    <div class="m-item">
                        <div class="m-label">Target</div>
                        <div class="m-value" style="color:#FFFFFF;">$ {d['Target']}</div>
                        <span class="m-upside {up_class}">{round(upside,1)}% potenziale</span>
                    </div>
                    <div class="m-item"><div class="m-label">P/E Ratio</div><div class="m-value">{d['PE']}</div></div>
                    <div class="m-item"><div class="m-label">ROE</div><div class="m-value">{d['ROE']}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"TRACK {d['Ticker']}", key=f"save_{d['Ticker']}"):
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
            with st.spinner("Aggiornamento dati..."):
                for idx, row in df_h.iterrows():
                    stock_data = analyze_stock(row['Ticker'])
                    if stock_data:
                        s_perf = ((stock_data['Price'] / row['Prezzo_In']) - 1) * 100
                        b_perf = get_bench_perf(row['Index'], row['Data'])
                        alpha = s_perf - b_perf
                        # Logica colore per Alpha
                        status = "status-neutral"
                        if alpha > 5: status = "status-buy"
                        if alpha < -5: status = "status-sell"
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
