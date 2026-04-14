import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(page_title="Valutatore Azionario Pro", layout="wide")

st.title("📊 Stock Value Analyzer")
st.markdown("Analizza se un titolo è sottovalutato basandosi sui dati fondamentali di Yahoo Finance.")

# --- SIDEBAR: INPUT UTENTE ---
st.sidebar.header("Impostazioni Analisi")
tickers_input = st.sidebar.text_input("Inserisci i Ticker (separati da virgola)", "AAPL, MSFT, ENI.MI, TSLA, UCG.MI")
tickers = [t.strip().upper() for t in tickers_input.split(",")]

# --- LOGICA DI ANALISI ---
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        # Estrazione Dati
        price = info.get('currentPrice', 0)
        target = info.get('targetMeanPrice', 0)
        peg = info.get('pegRatio', 0)
        pb = info.get('priceToBook', 0)
        roe = info.get('returnOnEquity', 0)
        debt_equity = info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0
        pe = info.get('trailingPE', 0)
        fcf = info.get('freeCashflow', 0)
        cap = info.get('marketCap', 0)
        p_fcf = cap / fcf if fcf and fcf != 0 else 0

        # Calcolo Score (da 0 a 6)
        score = 0
        if 0 < peg < 1: score += 1          # Crescita a buon prezzo
        if 0 < pb < 1.5: score += 1         # Vicino al valore contabile
        if price < target: score += 1       # Sotto il target degli analisti
        if roe > 0.15: score += 1           # Alta efficienza (ROE > 15%)
        if 0 < debt_equity < 1: score += 1  # Debito sotto controllo
        if 0 < p_fcf < 20: score += 1       # Genera molta cassa rispetto al prezzo

        # Stato finale
        if score >= 4:
            status = "Sottovalutata 🟢"
        elif score >= 2:
            status = "Equa/Speculativa 🟡"
        else:
            status = "Sopravvalutata 🔴"

        return {
            "Ticker": ticker_symbol,
            "Prezzo": f"{price:.2f} €" if ".MI" in ticker_symbol else f"{price:.2f} $",
            "Stato": status,
            "Score": f"{score}/6",
            "P/E": round(pe, 2) if pe else "N/D",
            "PEG": round(peg, 2) if peg else "N/D",
            "ROE": f"{round(roe*100, 2)}%" if roe else "N/D",
            "P/FCF": round(p_fcf, 2) if p_fcf else "N/D",
            "D/E Ratio": round(debt_equity, 2) if debt_equity else "N/D"
        }
    except Exception as e:
        return None

# --- ESECUZIONE ANALISI ---
if st.sidebar.button("Avvia Analisi"):
    results = []
    with st.spinner('Recupero dati in corso...'):
        for t in tickers:
            data = get_stock_data(t)
            if data:
                results.append(data)
    
    if results:
        df = pd.DataFrame(results)
        st.subheader("Tabella Comparativa")
        st.table(df)
        
        # --- DETTAGLIO SINGOLO TITOLO CON GRAFICO ---
        st.divider()
        st.subheader("Focus Grafico")
        selected_ticker = st.selectbox("Seleziona un titolo per vedere l'andamento:", tickers)
        
        hist_data = yf.download(selected_ticker, period="6mo")
        if not hist_data.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist_data.index,
                            open=hist_data['Open'],
                            high=hist_data['High'],
                            low=hist_data['Low'],
                            close=hist_data['Close'])])
            fig.update_layout(title=f"Andamento 6 mesi: {selected_ticker}", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Non è stato possibile recuperare i dati. Controlla i Ticker inseriti.")

# --- FOOTER INFORMATIVO ---
st.info("""
**Parametri per il punteggio (Score):**
1. **PEG < 1**: L'azione costa poco rispetto alla crescita prevista.
2. **P/B < 1.5**: Il prezzo non è troppo distante dal valore reale dei beni aziendali.
3. **Prezzo < Target**: Il prezzo attuale è inferiore alla media stimata dagli analisti.
4. **ROE > 15%**: L'azienda è molto efficiente nel generare profitti dal capitale proprio.
5. **D/E < 1**: Il debito è inferiore al patrimonio netto (azienda solida).
6. **P/FCF < 20**: L'azienda produce cassa reale a un prezzo ragionevole.
""")