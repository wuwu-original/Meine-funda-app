import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# layout="centered" ist optimal für Smartphone-Displays
st.set_page_config(page_title="My Fundamental App", page_icon="📱", layout="centered")

@st.cache_data(ttl=3600) # Caching, damit die App auf dem Handy schnell bleibt
def calculate_custom_indicators(ticker_symbol):
    """
    Holt Quartalszahlen, Bilanzen und Marktdaten für eigene Indikatoren.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        market_cap = info.get('marketCap', 0)
        kgv = info.get('trailingPE', 0)
        kbv = info.get('priceToBook', 0)
        
        # Quartalszahlen & Bilanz abrufen
        q_financials = stock.quarterly_financials
        q_bs = stock.quarterly_balance_sheet
        
        if q_financials.empty:
            return None
            
        # Transponieren & leere Felder füllen
        df_fin = q_financials.T.fillna(0)
        df_bs = q_bs.T.fillna(0) if not q_bs.empty else pd.DataFrame(index=df_fin.index)
        
        # Zusammenführen von GuV und Bilanz anhand des Datums
        df = pd.concat([df_fin, df_bs], axis=1)
        
        op_income = df.get('Operating Income', pd.Series(0, index=df.index))
        revenue = df.get('Total Revenue', pd.Series(0, index=df.index))
        total_assets = df.get('Total Assets', pd.Series(0, index=df.index))
        current_liab = df.get('Current Liabilities', pd.Series(0, index=df.index))
        current_assets = df.get('Current Assets', pd.Series(0, index=df.index))
        net_ppe = df.get('Net PPE', pd.Series(0, index=df.index))
        
        # --- MEINE EIGENEN INDIKATOREN ---
        
        df['Market Cap (Brd)'] = market_cap / 1_000_000_000 if market_cap else 0
        df['KGV'] = kgv if kgv is not None else 0
        df['KBV'] = kbv if kbv is not None else 0
        
        df['Custom_Op_Margin_%'] = np.where(revenue != 0, (op_income / revenue) * 100, 0)
        df['Custom_Rev_Growth_QoQ_%'] = revenue.pct_change(periods=-1) * 100
        
        # Formel: Operating Income / (Total Assets - Current Liabilities)
        invested_capital = total_assets - current_liab
        df['ROIC_%'] = np.where(invested_capital > 0, (op_income / invested_capital) * 100 * 4, 0)
        
        # Formel: Operating Income / (Net Working Capital + Net Fixed Assets)
        nwc = current_assets - current_liab
        capital_employed = nwc + net_ppe
        df['Greenblatt_ROC_%'] = np.where(capital_employed > 0, (op_income / capital_employed) * 100 * 4, 0)
        
        # Eigener Gesamt-Score
        df['My_Power_Score'] = df['Custom_Op_Margin_%'] + df['Custom_Rev_Growth_QoQ_%']
        
        df = df.fillna(0)
        cols_to_keep = ['Market Cap (Brd)', 'KGV', 'KBV', 'Total Revenue', 'Operating Income', 
                        'Custom_Op_Margin_%', 'Custom_Rev_Growth_QoQ_%', 'ROIC_%', 'Greenblatt_ROC_%', 'My_Power_Score']
        
        # Gebe nur Spalten zurück, die sauber berechnet werden konnten
        existing_cols = [c for c in cols_to_keep if c in df.columns]
        return df[existing_cols]
            
    except Exception as e:
        return None

st.title("📊 Funda-App")

# Zwei Tabs: Einzelanalyse und Screener
tab1, tab2 = st.tabs(["🔍 Einzel-Analyse", "🎯 Screener"])

with tab1:
    st.subheader("Aktie analysieren")
    ticker_input = st.text_input("Ticker-Symbol eingeben (z.B. AAPL, ADBE):", value="AAPL")
    
    if st.button("Analysieren", use_container_width=True):
        with st.spinner('Lade Bilanzen und Marktdaten...'):
            data = calculate_custom_indicators(ticker_input.upper())
            
            if data is not None and not data.empty:
                st.success(f"Daten für {ticker_input.upper()} geladen!")
                
                latest = data.iloc[0]
                
                # Zwei Reihen mit je 3 Kennzahlen (perfekt fürs Handy)
                col1, col2, col3 = st.columns(3)
                col1.metric("Score", f"{latest['My_Power_Score']:.1f}")
                col2.metric("KGV", f"{latest['KGV']:.1f}" if latest['KGV'] > 0 else "-")
                col3.metric("ROIC", f"{latest['ROIC_%']:.1f}%")
                
                col4, col5, col6 = st.columns(3)
                col4.metric("ROC (Greenblatt)", f"{latest['Greenblatt_ROC_%']:.1f}%")
                col5.metric("KBV", f"{latest['KBV']:.1f}" if latest['KBV'] > 0 else "-")
                col6.metric("Market Cap", f"${latest['Market Cap (Brd)']:.1f}B")
                
                st.markdown("### Historische Quartale")
                st.dataframe(data.style.format("{:.2f}").background_gradient(subset=['My_Power_Score'], cmap='RdYlGn'))
            else:
                st.error("Fehler beim Laden der Daten oder keine passenden Kennzahlen gefunden.")

with tab2:
    st.subheader("Multi-Faktor Screener")
    st.write("Filtert Aktien basierend auf ALLEN Kriterien gleichzeitig.")
    
    watchlist = st.text_input("Ticker (kommagetrennt):", "AAPL, MSFT, GOOGL, META, INTC, ADBE, CRM, NFLX")
    
    st.markdown("**Filter-Kriterien:**")
    colA, colB = st.columns(2)
    with colA:
        min_score = st.slider("Min. Power-Score:", min_value=-50, max_value=100, value=20)
        max_kgv = st.slider("Max. KGV:", min_value=1, max_value=150, value=50)
        min_mcap = st.number_input("Min. Market Cap (Mrd $):", min_value=0.0, value=5.0, step=5.0)
    with colB:
        min_roic = st.slider("Min. ROIC (%):", min_value=-10, max_value=50, value=10)
        min_roc = st.slider("Min. ROC (Greenblatt) (%):", min_value=-10, max_value=50, value=10)
    
    if st.button("Screener starten", use_container_width=True):
        tickers = [t.strip().upper() for t in watchlist.split(",")]
        results = []
        
        progress_bar = st.progress(0)
        for i, t in enumerate(tickers):
            progress_bar.progress((i + 1) / len(tickers))
            
            df = calculate_custom_indicators(t)
            if df is not None and not df.empty:
                latest = df.iloc[0]
                results.append({
                    "Ticker": t,
                    "Market Cap": latest.get('Market Cap (Brd)', 0),
                    "KGV": latest.get('KGV', 0),
                    "ROIC %": latest.get('ROIC_%', 0),
                    "ROC %": latest.get('Greenblatt_ROC_%', 0),
                    "My_Power_Score": latest.get('My_Power_Score', 0)
                })
                
        if results:
            res_df = pd.DataFrame(results)
            
            # Bedingung: Aktie muss ALLE Bedingungen erfüllen. (KGV > 0 filtert unrentable Firmen aus)
            filtered_df = res_df[
                (res_df['My_Power_Score'] >= min_score) &
                (res_df['KGV'] > 0) & (res_df['KGV'] <= max_kgv) &
                (res_df['ROIC %'] >= min_roic) &
                (res_df['ROC %'] >= min_roc) &
                (res_df['Market Cap'] >= min_mcap)
            ].sort_values(by="My_Power_Score", ascending=False)
            
            st.success(f"{len(filtered_df)} Aktien haben alle Filter bestanden!")
            st.dataframe(filtered_df.style.format({
                "Market Cap": "{:.1f}B",
                "KGV": "{:.1f}",
                "ROIC %": "{:.1f}%",
                "ROC %": "{:.1f}%",
                "My_Power_Score": "{:.1f}"
            }))
        else:
            st.warning("Keine Daten gefunden.")
