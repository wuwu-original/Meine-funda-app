import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# layout="centered" ist optimal für Smartphone-Displays
st.set_page_config(page_title="My Fundamental App", page_icon="📱", layout="centered")

# --- HINTERGRUND-DATEN FÜR DEN SCREENER ---
# Da yfinance nicht "alle Aktien der Welt" auf einmal abfragen kann, 
# definieren wir hier ein starkes globales Universum, das automatisch gescannt wird.
GLOBAL_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK-B", "JPM", "V", # USA
    "SAP", "SIE.DE", "ALV.DE", "BMW.DE", "MUV2.DE", "DTE.DE", # Deutschland
    "ASML.AS", "MC.PA", "OR.PA", "NESN.SW", "NOVN.SW", "NVO", # Europa Rest
    "TSM", "TM", "SONY", "BABA" # Asien
]

@st.cache_data(ttl=3600)
def get_stock_data_full(ticker_symbol):
    """
    Holt ALLE Daten für die Einzelanalyse: Finanzberichte, Info, Insider.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Basis-Info
        info = stock.info
        
        # Finanzberichte (Quartal)
        guv = stock.quarterly_financials
        bilanz = stock.quarterly_balance_sheet
        cashflow = stock.quarterly_cashflow
        
        # Insider
        insider = stock.major_holders
        
        return {
            "info": info,
            "guv": guv,
            "bilanz": bilanz,
            "cashflow": cashflow,
            "insider": insider
        }
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def run_screener_scan(tickers):
    """
    Scannt unsere hinterlegte Liste an Aktien für den Screener.
    """
    results = []
    
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            
            country = info.get('country', 'Unknown')
            market_cap = info.get('marketCap', 0) / 1_000_000_000 # in Milliarden
            kgv = info.get('trailingPE', 0)
            kbv = info.get('priceToBook', 0)
            
            # Für ROIC & ROC brauchen wir rudimentäre Bilanz/GuV Daten (Jahresbasis reicht hier für den Speed)
            bs = stock.balance_sheet
            fin = stock.financials
            
            roic = 0
            roc = 0
            
            if not bs.empty and not fin.empty:
                # Versuch der Berechnung, wenn Daten vorhanden
                op_inc = fin.loc['Operating Income'].iloc[0] if 'Operating Income' in fin.index else 0
                tot_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else 0
                curr_liab = bs.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in bs.index else 0
                curr_assets = bs.loc['Current Assets'].iloc[0] if 'Current Assets' in bs.index else 0
                net_ppe = bs.loc['Net PPE'].iloc[0] if 'Net PPE' in bs.index else 0
                
                inv_cap = tot_assets - curr_liab
                if inv_cap > 0:
                    roic = (op_inc / inv_cap) * 100
                    
                cap_emp = (curr_assets - curr_liab) + net_ppe
                if cap_emp > 0:
                    roc = (op_inc / cap_emp) * 100

            results.append({
                "Ticker": t,
                "Unternehmen": info.get('shortName', t),
                "Land": country,
                "Market Cap": market_cap,
                "KGV": kgv if kgv is not None else 0,
                "KBV": kbv if kbv is not None else 0,
                "ROIC %": roic,
                "ROC %": roc
            })
        except:
            continue # Bei Fehler mit einer Aktie einfach zur nächsten springen
            
    return pd.DataFrame(results)


st.title("📊 Funda-App")

# Zwei Haupt-Tabs
tab1, tab2 = st.tabs(["🔍 Einzel-Analyse", "🎯 Screener"])

with tab1:
    st.subheader("Aktie analysieren")
    ticker_input = st.text_input("Ticker-Symbol eingeben (z.B. AAPL, SIE.DE):", value="AAPL")
    
    if st.button("Analysieren", use_container_width=True):
        with st.spinner('Lade alle Berichte & Insider-Daten...'):
            data = get_stock_data_full(ticker_input.upper())
            
            if data is not None and data['info']:
                st.success(f"Daten für {data['info'].get('shortName', ticker_input.upper())} geladen!")
                
                # Top Kennzahlen (Statistiken als Quick-View)
                info = data['info']
                col1, col2, col3 = st.columns(3)
                col1.metric("KGV", f"{info.get('trailingPE', 0):.1f}" if info.get('trailingPE') else "-")
                col2.metric("KBV", f"{info.get('priceToBook', 0):.1f}" if info.get('priceToBook') else "-")
                mcap = info.get('marketCap', 0) / 1_000_000_000
                col3.metric("M.Cap", f"${mcap:.1f}B")
                
                st.markdown("---")
                
                # Navigation für die Finanzberichte (Sub-Tabs)
                st.markdown("### Finanzdaten & Details")
                sub1, sub2, sub3, sub4, sub5 = st.tabs(["GuV", "Bilanz", "Cashflow", "Statistiken", "Insider"])
                
                with sub1:
                    st.write("**Income Statement (Quartale)**")
                    if data['guv'] is not None and not data['guv'].empty:
                        st.dataframe(data['guv'].dropna(how='all'))
                    else:
                        st.write("Keine GuV Daten gefunden.")
                        
                with sub2:
                    st.write("**Balance Sheet (Quartale)**")
                    if data['bilanz'] is not None and not data['bilanz'].empty:
                        st.dataframe(data['bilanz'].dropna(how='all'))
                    else:
                        st.write("Keine Bilanz Daten gefunden.")
                        
                with sub3:
                    st.write("**Cashflow Statement (Quartale)**")
                    if data['cashflow'] is not None and not data['cashflow'].empty:
                        st.dataframe(data['cashflow'].dropna(how='all'))
                    else:
                        st.write("Keine Cashflow Daten gefunden.")
                        
                with sub4:
                    st.write("**Wichtige Verhältnisse & Margen**")
                    stats_dict = {
                        "Gross Margin": f"{info.get('grossMargins', 0)*100:.1f}%" if info.get('grossMargins') else "-",
                        "Operating Margin": f"{info.get('operatingMargins', 0)*100:.1f}%" if info.get('operatingMargins') else "-",
                        "Profit Margin": f"{info.get('profitMargins', 0)*100:.1f}%" if info.get('profitMargins') else "-",
                        "Return on Equity (ROE)": f"{info.get('returnOnEquity', 0)*100:.1f}%" if info.get('returnOnEquity') else "-",
                        "Return on Assets (ROA)": f"{info.get('returnOnAssets', 0)*100:.1f}%" if info.get('returnOnAssets') else "-",
                        "Debt to Equity": info.get('debtToEquity', '-'),
                        "Current Ratio": info.get('currentRatio', '-'),
                        "Dividenden Rendite": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "-"
                    }
                    st.table(pd.DataFrame(list(stats_dict.items()), columns=["Kennzahl", "Wert"]))
                    
                with sub5:
                    st.write("**Aktionärsstruktur / Insider**")
                    if data['insider'] is not None and not data['insider'].empty:
                        # yfinance liefert hier oft eine Tabelle ohne Spaltennamen, wir machen sie hübsch
                        insider_df = data['insider'].copy()
                        if len(insider_df.columns) == 2:
                            insider_df.columns = ["Anteil", "Kategorie"]
                        st.dataframe(insider_df, hide_index=True)
                    else:
                        st.write("Keine Insider-Daten gefunden.")
            else:
                st.error("Fehler beim Laden. Ticker existiert möglicherweise nicht.")

with tab2:
    st.subheader("Globaler Multi-Faktor Screener")
    st.write("Scannt automatisch eine vordefinierte Liste von globalen Top-Aktien.")
    
    # Lade Daten (wird gecached, dauert nur beim ersten Mal ein paar Sekunden)
    with st.spinner('Scanne den Markt...'):
        df_screener = run_screener_scan(GLOBAL_UNIVERSE)
    
    if not df_screener.empty:
        # Extrahiere alle verfügbaren Länder für den Filter
        available_countries = df_screener['Land'].unique().tolist()
        
        st.markdown("**Filter-Kriterien:**")
        selected_countries = st.multiselect("Länder auswählen:", available_countries, default=available_countries)
        
        colA, colB = st.columns(2)
        with colA:
            max_kgv = st.slider("Max. KGV:", min_value=1, max_value=150, value=40)
            max_kbv = st.slider("Max. KBV:", min_value=0.1, max_value=50.0, value=15.0)
            min_mcap = st.number_input("Min. Market Cap ($B):", min_value=0.0, value=10.0, step=10.0)
        with colB:
            min_roic = st.slider("Min. ROIC (%):", min_value=-10, max_value=50, value=5)
            min_roc = st.slider("Min. ROC (%):", min_value=-10, max_value=50, value=5)
        
        # Filtern
        filtered_df = df_screener[
            (df_screener['Land'].isin(selected_countries)) &
            (df_screener['Market Cap'] >= min_mcap) &
            (df_screener['KGV'] > 0) & (df_screener['KGV'] <= max_kgv) &
            (df_screener['KBV'] > 0) & (df_screener['KBV'] <= max_kbv) &
            (df_screener['ROIC %'] >= min_roic) &
            (df_screener['ROC %'] >= min_roc)
        ].sort_values(by="ROIC %", ascending=False)
        
        st.success(f"{len(filtered_df)} Aktien entsprechen deinen Kriterien!")
        
        # Schön formatierte Ausgabe
        st.dataframe(filtered_df.style.format({
            "Market Cap": "{:.1f}B",
            "KGV": "{:.1f}",
            "KBV": "{:.1f}",
            "ROIC %": "{:.1f}%",
            "ROC %": "{:.1f}%"
        }).background_gradient(subset=['ROIC %', 'ROC %'], cmap='Greens'), hide_index=True)
    else:
        st.warning("Fehler beim Scannen der Aktien.")
