import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings

# Warnungen unterdrücken, damit die App nicht mit roten Texten vollgemüllt wird
warnings.filterwarnings('ignore')

# Seiten-Konfiguration
st.set_page_config(page_title="Funda-App", page_icon="📊", layout="wide")

st.title("📊 Funda-App")

# --- HILFSFUNKTIONEN FÜR DATENABRUF ---
@st.cache_data(ttl=3600)  # Speichert die Daten für 1 Stunde im Cache
def load_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Alle relevanten Berichte abrufen
        info = stock.info
        guv_a = stock.financials
        guv_q = stock.quarterly_financials
        bilanz_a = stock.balance_sheet
        bilanz_q = stock.quarterly_balance_sheet
        cf_a = stock.cashflow
        cf_q = stock.quarterly_cashflow
        insider = stock.major_holders
        
        # Eigene Berechnungen (ROIC & ROC) - stark vereinfacht basierend auf verfügbaren yfinance Daten
        try:
            ebit = info.get('ebitda', 0) # Fallback auf EBITDA, falls EBIT fehlt
            total_assets = info.get('totalAssets', bilanz_a.loc['Total Assets'].iloc[0] if 'Total Assets' in bilanz_a.index else 1)
            current_liabilities = bilanz_a.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in bilanz_a.index else 0
            net_working_capital = (bilanz_a.loc['Current Assets'].iloc[0] if 'Current Assets' in bilanz_a.index else 0) - current_liabilities
            fixed_assets = total_assets - (bilanz_a.loc['Current Assets'].iloc[0] if 'Current Assets' in bilanz_a.index else 0)
            
            # Greenblatt ROC = EBIT / (Net Working Capital + Net Fixed Assets)
            roc = ebit / (net_working_capital + fixed_assets) if (net_working_capital + fixed_assets) > 0 else np.nan
            
            # ROIC = NOPAT / Invested Capital (Hier vereinfacht als EBIT / (Total Assets - Current Liabilities))
            invested_capital = total_assets - current_liabilities
            roic = ebit / invested_capital if invested_capital > 0 else np.nan
            
        except:
            roc = np.nan
            roic = np.nan

        return {
            "info": info,
            "guv_q": guv_q,
            "guv_a": guv_a,
            "bilanz_q": bilanz_q,
            "bilanz_a": bilanz_a,
            "cashflow_q": cf_q,
            "cashflow_a": cf_a,
            "insider": insider,
            "calc_roc": roc,
            "calc_roic": roic
        }
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def load_screener_data():
    # Globale Watchlist (automatisch gescannt)
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
        "SAP", "SIE.DE", "ALV.DE", "VOW3.DE", "ASML", "LVMUY", 
        "TCEHY", "BABA", "TSM", "NVO", "JNJ", "JPM", "V"
    ]
    
    data_list = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            
            # Wenn MCap fehlt, überspringen
            if 'marketCap' not in info or info['marketCap'] is None:
                continue
                
            data_list.append({
                "Ticker": t,
                "Name": info.get("shortName", t),
                "Land": info.get("country", "Unbekannt"),
                "M.Cap (Mrd $)": info.get("marketCap", 0) / 1e9,
                "KGV": info.get("trailingPE", np.nan),
                "KBV": info.get("priceToBook", np.nan),
                "Marge (%)": info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else np.nan,
                "ROE (%)": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else np.nan,
                "Div. Rendite (%)": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
            })
        except:
            continue
            
    df = pd.DataFrame(data_list)
    # NaN Werte sicherheitshalber auffüllen oder belassen
    return df


# --- HAUPT-LAYOUT (TABS) ---
tab1, tab2 = st.tabs(["🔍 Einzel-Analyse", "🎯 Screener"])

with tab1:
    st.header("Aktie analysieren")
    ticker_input = st.text_input("Ticker-Symbol eingeben (z.B. AAPL, MSFT, SAP):").upper()
    
    if ticker_input:
        data = load_stock_data(ticker_input)
        
        if data and data['info']:
            info = data['info']
            st.success(f"Daten für **{info.get('shortName', ticker_input)}** ({info.get('country', 'N/A')}) geladen!")
            
            # --- TOP METRIKEN ---
            mcap = info.get('marketCap', 0) / 1e9
            kgv = info.get('trailingPE', np.nan)
            kbv = info.get('priceToBook', np.nan)
            roic = data['calc_roic'] * 100 if not np.isnan(data['calc_roic']) else np.nan
            roc = data['calc_roc'] * 100 if not np.isnan(data['calc_roc']) else np.nan
            
            # Eigener "Power Score" (Beispiel: Marge + ROE)
            marge = info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0
            roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
            power_score = marge + roe
            
            col1, col2, col3 = st.columns(3)
            col1.metric("KGV", f"{kgv:.1f}" if pd.notna(kgv) else "N/A")
            col2.metric("KBV", f"{kbv:.1f}" if pd.notna(kbv) else "N/A")
            col3.metric("M.Cap", f"${mcap:.1f}B" if mcap > 0 else "N/A")
            
            col4, col5, col6 = st.columns(3)
            col4.metric("ROIC (ca.)", f"{roic:.1f}%" if pd.notna(roic) else "N/A")
            col5.metric("ROC Greenblatt (ca.)", f"{roc:.1f}%" if pd.notna(roc) else "N/A")
            col6.metric("Mein Power Score", f"{power_score:.1f}" if power_score != 0 else "N/A")
            
            st.markdown("---")
            
            # --- HILFSFUNKTION FÜR MATRIZEN & CHARTS ---
            def format_large_number(x):
                try:
                    val = float(x)
                    if pd.isna(val):
                        return "N/A"
                    if abs(val) >= 1e9:
                        return f"{val / 1e9:.2f} B"
                    elif abs(val) >= 1e6:
                        return f"{val / 1e6:.2f} M"
                    elif abs(val) >= 1e3:
                        return f"{val / 1e3:.2f} K"
                    else:
                        return f"{val:.2f}"
                except:
                    return x

            def render_statement(title, df_annual, df_quarterly, key_prefix):
                if df_annual is None or df_annual.empty or df_quarterly is None or df_quarterly.empty:
                    st.warning(f"Keine Daten für {title} gefunden.")
                    return
                
                # 1. Filter: Jährlich oder Quartal
                period = st.radio(f"Zeitraum für {title}:", ["Quartalsweise", "Jährlich"], horizontal=True, key=f"radio_{key_prefix}")
                df = df_quarterly if period == "Quartalsweise" else df_annual
                
                # Daten säubern (leere Zeilen weg, Spaltennamen als lesbares Datum formatieren)
                df = df.dropna(how='all')
                df.columns = [str(col).split(' ')[0] for col in df.columns]
                
                st.write("**Interaktive Grafik (Balkendiagramm)**")
                
                # Platzhalter für den Chart erstellen (damit der Chart OBEN bleibt, 
                # obwohl die Auswahl in der Tabelle UNTEN getroffen wird)
                chart_placeholder = st.empty()
                
                st.write("**Datenmatrix (Klicke links auf die Zeilennummer, um die Zeile im Chart anzuzeigen):**")
                
                # Tabelle formatieren (Zahlen in B, M, K umwandeln)
                display_df = df.copy()
                for col in display_df.columns:
                    display_df[col] = display_df[col].apply(format_large_number)
                    
                # 2. Interaktive Tabelle anzeigen (mit Auswahl-Funktion)
                selection_event = st.dataframe(
                    display_df, 
                    use_container_width=True,
                    on_select="rerun",           # Seite lädt bei Klick neu
                    selection_mode="multi-row",  # Mehrere Zeilen auswählbar
                    key=f"df_select_{key_prefix}"
                )
                
                # 3. Herausfinden, welche Zeilen der Nutzer angeklickt hat
                selected_rows = selection_event.selection.rows
                
                if selected_rows:
                    # Wandle die angeklickten Zeilen-Nummern in die echten Namen um (z.B. "Total Revenue")
                    selected_metrics = df.iloc[selected_rows].index.tolist()
                else:
                    # Wenn nichts ausgewählt ist, zeige standardmäßig die erste Zeile an
                    available_metrics = df.index.tolist()
                    selected_metrics = [available_metrics[0]] if available_metrics else []
                
                if selected_metrics:
                    # Für den Chart: Original-Daten nutzen (wegen korrekter Skalierung), Transponieren und sortieren
                    chart_data = df.loc[selected_metrics].T.sort_index()
                    
                    # Dynamische Skalierung für die Grafik
                    max_val = chart_data.abs().max().max()
                    
                    if pd.notna(max_val):
                        if max_val >= 1e9:
                            chart_data = chart_data / 1e9
                            suffix = " (in Mrd. / B)"
                        elif max_val >= 1e6:
                            chart_data = chart_data / 1e6
                            suffix = " (in Mio. / M)"
                        elif max_val >= 1e3:
                            chart_data = chart_data / 1e3
                            suffix = " (in Tsd. / K)"
                        else:
                            suffix = ""
                        
                        # Einheiten in die Legende der Grafik schreiben
                        if suffix:
                            chart_data.columns = [f"{col}{suffix}" for col in chart_data.columns]
                            
                    # Chart IN den vorbereiteten Platzhalter oben einfügen
                    with chart_placeholder:
                        st.bar_chart(chart_data)

            # --- SUB-TABS ---
            sub1, sub2, sub3, sub4, sub5 = st.tabs(["GuV", "Bilanz", "Cashflow", "Statistiken", "Insider"])
            
            with sub1:
                render_statement("GuV (Income Statement)", data['guv_a'], data['guv_q'], "guv")
                    
            with sub2:
                render_statement("Bilanz (Balance Sheet)", data['bilanz_a'], data['bilanz_q'], "bilanz")
                    
            with sub3:
                render_statement("Cashflow", data['cashflow_a'], data['cashflow_q'], "cf")
                    
            with sub4:
                st.write("**Wichtige Verhältnisse**")
                stats_dict = {
                    "Brutto-Marge": f"{info.get('grossMargins', 0)*100:.1f}%",
                    "Operative Marge": f"{info.get('operatingMargins', 0)*100:.1f}%",
                    "Netto-Marge": f"{info.get('profitMargins', 0)*100:.1f}%",
                    "Return on Equity (ROE)": f"{info.get('returnOnEquity', 0)*100:.1f}%",
                    "Return on Assets (ROA)": f"{info.get('returnOnAssets', 0)*100:.1f}%",
                    "Debt to Equity": info.get('debtToEquity', "N/A"),
                    "Current Ratio": info.get('currentRatio', "N/A")
                }
                st.table(pd.DataFrame(list(stats_dict.items()), columns=["Kennzahl", "Wert"]))
                
            with sub5:
                st.write("**Insider & Großaktionäre**")
                if data['insider'] is not None and not data['insider'].empty:
                    st.dataframe(data['insider'], use_container_width=True)
                else:
                    st.write("Keine Insider-Daten verfügbar.")
        else:
            st.error("Ticker nicht gefunden oder keine Daten verfügbar.")

with tab2:
    st.header("Globaler Screener")
    st.write("Scannt automatisch eine globale Watchlist (Big Tech, DAX, Asien).")
    
    with st.spinner("Lade Screener-Daten..."):
        screener_df = load_screener_data()
        
    if not screener_df.empty:
        # --- FILTER-BEREICH ---
        st.subheader("Filter")
        
        # Länder-Filter (Multi-Select)
        alle_laender = sorted(list(screener_df['Land'].unique()))
        gewaehlte_laender = st.multiselect("Nach Land filtern:", alle_laender, default=alle_laender)
        
        # Schieberegler für Metriken
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            min_mcap = st.slider("Min. Marktkapitalisierung (Mrd $)", 0, 3000, 50)
            max_kgv = st.slider("Maximales KGV", 0, 100, 50)
        with col_f2:
            min_marge = st.slider("Min. Operative Marge (%)", -20, 60, 10)
            max_kbv = st.slider("Maximales KBV", 0, 50, 20)
            
        # Filter anwenden
        mask = (
            (screener_df['Land'].isin(gewaehlte_laender)) &
            (screener_df['M.Cap (Mrd $)'] >= min_mcap) &
            (screener_df['KGV'] <= max_kgv) &
            (screener_df['KBV'] <= max_kbv) &
            (screener_df['Marge (%)'] >= min_marge)
        )
        gefiltert = screener_df[mask].reset_index(drop=True)
        
        # --- ERGEBNIS-TABELLE ---
        st.write(f"**Treffer: {len(gefiltert)} Unternehmen**")
        
        if len(gefiltert) > 0:
            # Schöne farbige Tabelle
            st.dataframe(
                gefiltert.style.format({
                    "M.Cap (Mrd $)": "{:.1f}",
                    "KGV": "{:.1f}",
                    "KBV": "{:.1f}",
                    "Marge (%)": "{:.1f}%",
                    "ROE (%)": "{:.1f}%",
                    "Div. Rendite (%)": "{:.1f}%"
                }).background_gradient(subset=['Marge (%)', 'ROE (%)'], cmap='Greens')
            )
        else:
            st.warning("Keine Unternehmen entsprechen deinen Filterkriterien.")
