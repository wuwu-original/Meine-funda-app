import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# layout="centered" ist optimal für Smartphone-Displays
st.set_page_config(page_title="My Fundamental App", page_icon="📱", layout="centered")

@st.cache_data(ttl=3600) # Caching, damit die App auf dem Handy schnell bleibt
def calculate_custom_indicators(ticker_symbol):
    """
    Holt Quartalszahlen und berechnet eigene fundamentale Indikatoren.
    Hier kannst du deine eigenen mathematischen Formeln einbauen!
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Quartalszahlen abrufen (Zeilen sind Metriken, Spalten sind Daten)
        q_financials = stock.quarterly_financials
        
        if q_financials.empty:
            return None
            
        # Transponieren, damit Datum als Zeile und Metriken als Spalten vorliegen
        df = q_financials.T
        
        # Daten bereinigen
        df = df.fillna(0)
        
        # Sicherstellen, dass die benötigten Spalten existieren
        # yfinance Spaltennamen variieren manchmal, wir nutzen Standardnamen
        if 'Total Revenue' in df.columns and 'Operating Income' in df.columns:
            
            # --- MEINE EIGENEN INDIKATOREN (HIER WIRD PROGRAMMIERT) ---
            
            # 1. Eigener Indikator: Operative Marge in %
            df['Custom_Op_Margin_%'] = (df['Operating Income'] / df['Total Revenue']) * 100
            
            # 2. Eigener Indikator: Quartals-Umsatzwachstum (QoQ)
            # Da die Daten absteigend sortiert sind, nutzen wir pct_change(-1)
            df['Custom_Rev_Growth_QoQ_%'] = df['Total Revenue'].pct_change(periods=-1) * 100
            
            # 3. Mein eigener "Score": Marge + Wachstum
            df['My_Power_Score'] = df['Custom_Op_Margin_%'] + df['Custom_Rev_Growth_QoQ_%']
            
            return df[['Total Revenue', 'Operating Income', 'Custom_Op_Margin_%', 'Custom_Rev_Growth_QoQ_%', 'My_Power_Score']]
        else:
            return None
            
    except Exception as e:
        return None

st.title("📊 Funda-App")

# Zwei Tabs: Einzelanalyse und Screener
tab1, tab2 = st.tabs(["🔍 Einzel-Analyse", "🎯 Screener"])

with tab1:
    st.subheader("Aktie analysieren")
    ticker_input = st.text_input("Ticker-Symbol eingeben (z.B. AAPL, MSFT):", value="AAPL")
    
    if st.button("Analysieren", use_container_width=True):
        with st.spinner('Lade Quartalszahlen...'):
            data = calculate_custom_indicators(ticker_input.upper())
            
            if data is not None and not data.empty:
                st.success(f"Daten für {ticker_input.upper()} geladen!")
                
                # Neuester Quartals-Score als großes Element (perfekt fürs Handy)
                latest_score = data['My_Power_Score'].iloc[0]
                latest_margin = data['Custom_Op_Margin_%'].iloc[0]
                
                col1, col2 = st.columns(2)
                col1.metric("Mein Power Score", f"{latest_score:.1f}")
                col2.metric("Op. Marge", f"{latest_margin:.1f}%")
                
                st.markdown("### Historische Quartale")
                # Zeige die Tabelle (auf dem Handy seitlich scrollbar)
                st.dataframe(data.style.format("{:.2f}").background_gradient(subset=['My_Power_Score'], cmap='RdYlGn'))
            else:
                st.error("Fehler beim Laden der Daten. Bitte Ticker prüfen.")

with tab2:
    st.subheader("Eigener Screener")
    st.write("Filtert Aktien basierend auf deinem Custom Score.")
    
    # Beispiel-Watchlist
    watchlist = st.text_input("Ticker (kommagetrennt):", "AAPL, MSFT, GOOGL, META, INTC")
    min_score = st.slider("Mindest Power-Score:", min_value=-50, max_value=100, value=20)
    
    if st.button("Screener starten", use_container_width=True):
        tickers = [t.strip().upper() for t in watchlist.split(",")]
        results = []
        
        progress_bar = st.progress(0)
        for i, t in enumerate(tickers):
            # Update Progress Bar für besseres Handy-Feedback
            progress_bar.progress((i + 1) / len(tickers))
            
            df = calculate_custom_indicators(t)
            if df is not None and not df.empty:
                latest = df.iloc[0]
                results.append({
                    "Ticker": t,
                    "Letztes Quartal": df.index[0].strftime("%Y-%m-%d"),
                    "Op Marge %": latest['Custom_Op_Margin_%'],
                    "Wachstum QoQ %": latest['Custom_Rev_Growth_QoQ_%'],
                    "My_Power_Score": latest['My_Power_Score']
                })
                
        # Resultate auswerten
        if results:
            res_df = pd.DataFrame(results)
            # Wende EIGENEN Filter an
            filtered_df = res_df[res_df['My_Power_Score'] >= min_score].sort_values(by="My_Power_Score", ascending=False)
            
            st.success(f"{len(filtered_df)} Aktien haben deinen Filter bestanden!")
            st.dataframe(filtered_df.style.format({
                "Op Marge %": "{:.1f}",
                "Wachstum QoQ %": "{:.1f}",
                "My_Power_Score": "{:.1f}"
            }))
        else:
            st.warning("Keine Daten gefunden.")
