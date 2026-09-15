import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots # NEU: Für die Sub-Charts

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
        "TCEHY", "BABA", "TSM", "NVO", "JNJ", "JPM", "V",
        "ADBE", "CRM", "NFLX", "DIS", "MCD", "KO"
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
    return df


# --- HILFSFUNKTION FÜR INDIKATOREN ---
def calc_sma(series, period):
    return series.rolling(window=period).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_rp2_indicator(df_chart, ticker_symbol):
    """
    Übersetzung des Pine Scripts RP2.
    Verschmilzt wöchentliche Kursdaten mit vierteljährlichen Fundamentaldaten.
    """
    data = load_stock_data(ticker_symbol)
    if not data or data['guv_q'] is None or data['bilanz_q'] is None:
        return pd.Series(np.nan, index=df_chart.index)
        
    guv_q = data['guv_q'].T
    bilanz_q = data['bilanz_q'].T
    info = data['info']
    
    # Datum als Index sicherstellen
    guv_q.index = pd.to_datetime(guv_q.index)
    bilanz_q.index = pd.to_datetime(bilanz_q.index)
    
    fund = pd.DataFrame(index=guv_q.index)
    
    # Sicheres Auslesen der Metriken
    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)
        
    fund['Net Income'] = get_val(guv_q, ['Net Income', 'Net Income Common Stockholders'])
    fund['EBIT'] = get_val(guv_q, ['EBIT', 'Operating Income'])
    fund['Shares'] = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
    if fund['Shares'].isna().all():
        fund['Shares'] = info.get('sharesOutstanding', np.nan)
        
    fund['Equity'] = get_val(bilanz_q, ['Stockholders Equity', 'Total Equity Gross Minority Interest'])
    fund['Total Assets'] = get_val(bilanz_q, ['Total Assets'])
    fund['Current Liabilities'] = get_val(bilanz_q, ['Current Liabilities'])
    
    # Berechnung der fundamentalen Basiswerte (Quartalsweise)
    fund['EPS'] = fund['Net Income'] / fund['Shares']
    fund['BVPS'] = fund['Equity'] / fund['Shares']
    fund['Invested_Capital'] = fund['Total Assets'] - fund['Current Liabilities']
    fund['ROIC'] = fund['EBIT'] / fund['Invested_Capital']
    
    # Zusammenführen mit den wöchentlichen Kursdaten
    # Zeitzonen entfernen, um Konflikte beim Mergen zu verhindern
    try:
        chart_idx = df_chart.index.tz_localize(None)
        fund.index = fund.index.tz_localize(None)
    except:
        chart_idx = df_chart.index
        
    # Forward Fill: Füllt die Quartalswerte auf die wöchentlichen Tage auf (Treppenstufen-Effekt)
    fund_merged = fund.reindex(chart_idx.union(fund.index)).sort_index().ffill()
    fund_merged = fund_merged.reindex(chart_idx) 
    
    # Formel: (math.sqrt(targetValue * eps * bookValuePerShare) * (roic / price)*100)-20
    target_value = 22.5
    inner_sqrt = target_value * fund_merged['EPS'] * fund_merged['BVPS']
    
    # Vermeide Fehler durch negative Wurzeln
    sqrt_val = np.where(inner_sqrt >= 0, np.sqrt(np.maximum(inner_sqrt, 0)), np.nan)
    
    rp2 = (sqrt_val * (fund_merged['ROIC'] / df_chart['Close']) * 100) - 20
    return rp2


# --- HAUPT-LAYOUT (TABS) ---
tab1, tab2, tab3 = st.tabs(["🔍 Einzel-Analyse", "🎯 Screener", "📈 Kursverlauf"])

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
                
                period = st.radio(f"Zeitraum für {title}:", ["Quartalsweise", "Jährlich"], horizontal=True, key=f"radio_{key_prefix}")
                df = df_quarterly if period == "Quartalsweise" else df_annual
                
                df = df.dropna(how='all')
                df.columns = [str(col).split(' ')[0] for col in df.columns]
                
                st.write("**Interaktive Grafik (Balkendiagramm)**")
                chart_placeholder = st.empty()
                
                st.write("**Datenmatrix (Klicke links auf die Zeilennummer, um die Zeile im Chart anzuzeigen):**")
                
                display_df = df.copy()
                for col in display_df.columns:
                    display_df[col] = display_df[col].apply(format_large_number)
                    
                selection_event = st.dataframe(
                    display_df, 
                    use_container_width=True,
                    on_select="rerun",
                    selection_mode="multi-row",
                    key=f"df_select_{key_prefix}"
                )
                
                selected_rows = selection_event.selection.rows
                
                if selected_rows:
                    selected_metrics = df.iloc[selected_rows].index.tolist()
                else:
                    available_metrics = df.index.tolist()
                    selected_metrics = [available_metrics[0]] if available_metrics else []
                
                if selected_metrics:
                    chart_data = df.loc[selected_metrics].T.sort_index()
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
                        
                        if suffix:
                            chart_data.columns = [f"{col}{suffix}" for col in chart_data.columns]
                            
                    with chart_placeholder:
                        st.bar_chart(chart_data)

            def calculate_historical_stats(guv, bilanz):
                if guv is None or bilanz is None or guv.empty or bilanz.empty:
                    return pd.DataFrame()
                
                common_cols = guv.columns.intersection(bilanz.columns)
                if len(common_cols) == 0:
                    return pd.DataFrame()
                    
                g = guv[common_cols]
                b = bilanz[common_cols]
                
                stats = pd.DataFrame(index=[
                    "Brutto-Marge (%)", 
                    "Operative Marge (%)", 
                    "Netto-Marge (%)", 
                    "ROE (%)", 
                    "ROA (%)", 
                    "Debt to Equity", 
                    "Current Ratio"
                ], columns=common_cols)
                
                def get_val(df, keys):
                    for k in keys:
                        if k in df.index:
                            return df.loc[k]
                    return pd.Series(np.nan, index=df.columns)
                
                revenue = get_val(g, ['Total Revenue', 'Operating Revenue', 'Revenue'])
                gross_profit = get_val(g, ['Gross Profit'])
                op_income = get_val(g, ['Operating Income', 'EBIT'])
                net_income = get_val(g, ['Net Income', 'Net Income Common Stockholders'])
                
                equity = get_val(b, ['Stockholders Equity', 'Total Equity Gross Minority Interest', 'Common Stock Equity'])
                assets = get_val(b, ['Total Assets'])
                current_assets = get_val(b, ['Current Assets'])
                current_liabilities = get_val(b, ['Current Liabilities'])
                total_debt = get_val(b, ['Total Debt', 'Long Term Debt'])
                
                stats.loc["Brutto-Marge (%)"] = (gross_profit / revenue) * 100
                stats.loc["Operative Marge (%)"] = (op_income / revenue) * 100
                stats.loc["Netto-Marge (%)"] = (net_income / revenue) * 100
                stats.loc["ROE (%)"] = (net_income / equity) * 100
                stats.loc["ROA (%)"] = (net_income / assets) * 100
                stats.loc["Debt to Equity"] = total_debt / equity
                stats.loc["Current Ratio"] = current_assets / current_liabilities
                
                stats.replace([np.inf, -np.inf], np.nan, inplace=True)
                stats.columns = [str(col).split(' ')[0] for col in stats.columns]
                return stats.astype(float).round(2)

            sub1, sub2, sub3, sub4, sub5 = st.tabs(["GuV", "Bilanz", "Cashflow", "Statistiken", "Insider"])
            
            with sub1:
                render_statement("GuV (Income Statement)", data['guv_a'], data['guv_q'], "guv")
            with sub2:
                render_statement("Bilanz (Balance Sheet)", data['bilanz_a'], data['bilanz_q'], "bilanz")
            with sub3:
                render_statement("Cashflow", data['cashflow_a'], data['cashflow_q'], "cf")
            with sub4:
                st.write("**Historische Verhältnisse**")
                period_stats = st.radio("Zeitraum für Statistiken:", ["Quartalsweise", "Jährlich"], horizontal=True, key="radio_stats")
                
                if period_stats == "Quartalsweise":
                    hist_stats = calculate_historical_stats(data['guv_q'], data['bilanz_q'])
                else:
                    hist_stats = calculate_historical_stats(data['guv_a'], data['bilanz_a'])
                
                if hist_stats is not None and not hist_stats.empty:
                    chart_placeholder_stats = st.empty()
                    st.write("**Datenmatrix (Klicke links auf die Zeilennummer für Trend-Analyse):**")
                    
                    selection_event_stats = st.dataframe(
                        hist_stats, 
                        use_container_width=True,
                        on_select="rerun",
                        selection_mode="multi-row",
                        key="df_select_stats"
                    )
                    
                    selected_rows_stats = selection_event_stats.selection.rows
                    if selected_rows_stats:
                        selected_metrics_stats = hist_stats.iloc[selected_rows_stats].index.tolist()
                    else:
                        available_metrics_stats = hist_stats.index.tolist()
                        selected_metrics_stats = [available_metrics_stats[0]] if available_metrics_stats else []
                        
                    if selected_metrics_stats:
                        chart_data_stats = hist_stats.loc[selected_metrics_stats].T.sort_index()
                        with chart_placeholder_stats:
                            st.line_chart(chart_data_stats)
                else:
                    st.warning("Nicht genügend historische Daten vorhanden.")
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
    
    with st.spinner("Lade Screener-Daten..."):
        screener_df = load_screener_data()
        
    if not screener_df.empty:
        st.subheader("Filter")
        alle_laender = sorted(list(screener_df['Land'].unique()))
        gewaehlte_laender = st.multiselect("Nach Land filtern:", alle_laender, default=alle_laender)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            min_mcap = st.slider("Min. Marktkapitalisierung (Mrd $)", 0, 3000, 0)
            max_kgv = st.slider("Maximales KGV", 0, 150, 150)
        with col_f2:
            min_marge = st.slider("Min. Operative Marge (%)", -20, 60, -20)
            max_kbv = st.slider("Maximales KBV", 0, 100, 100)
            
        mask = (
            (screener_df['Land'].isin(gewaehlte_laender)) &
            (screener_df['M.Cap (Mrd $)'] >= min_mcap) &
            (screener_df['KGV'] <= max_kgv) &
            (screener_df['KBV'] <= max_kbv) &
            (screener_df['Marge (%)'] >= min_marge)
        )
        gefiltert = screener_df[mask].reset_index(drop=True)
        
        st.write(f"**Treffer: {len(gefiltert)} Unternehmen**")
        
        if len(gefiltert) > 0:
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

with tab3:
    st.header("Historischer Kursverlauf & Indikatoren")
    
    col_c1, col_c2, col_c3 = st.columns([1, 1.5, 1.5])
    with col_c1:
        ticker_input_chart = st.text_input("Ticker-Symbol:", key="chart_ticker").upper()
    with col_c2:
        overlay_ind = st.multiselect("Overlays (im Chart):", ["SMA 50", "SMA 200"])
    with col_c3:
        sub_ind = st.multiselect("Sub-Charts (max. 5):", ["RP2 Indikator (SinepTrader)", "RSI 14"], max_selections=5)
    
    if ticker_input_chart:
        with st.spinner(f"Lade Kurs- und Fundamentaldaten für {ticker_input_chart}..."):
            try:
                df_chart = yf.download(ticker_input_chart, period="4y", interval="1wk")
                
                if not df_chart.empty:
                    if isinstance(df_chart.columns, pd.MultiIndex):
                        df_chart.columns = df_chart.columns.droplevel(1)
                        
                    # Dynamische Anzahl an Reihen berechnen
                    num_subcharts = len(sub_ind)
                    row_heights = [0.6] + [0.4 / num_subcharts] * num_subcharts if num_subcharts > 0 else [1.0]
                    
                    fig = make_subplots(
                        rows=num_subcharts + 1, 
                        cols=1, 
                        shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=row_heights
                    )
                    
                    # 1. Haupt-Candlestick Chart hinzufügen
                    fig.add_trace(go.Candlestick(
                        x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                        low=df_chart['Low'], close=df_chart['Close'], name="Kurs"
                    ), row=1, col=1)
                    
                    # 2. Overlays hinzufügen
                    if "SMA 50" in overlay_ind:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=calc_sma(df_chart['Close'], 50), line=dict(color='blue', width=1), name="SMA 50"), row=1, col=1)
                    if "SMA 200" in overlay_ind:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=calc_sma(df_chart['Close'], 200), line=dict(color='orange', width=2), name="SMA 200"), row=1, col=1)
                        
                    # 3. Sub-Charts iterativ hinzufügen
                    current_row = 2
                    
                    for ind in sub_ind:
                        if ind == "RSI 14":
                            rsi_vals = calc_rsi(df_chart['Close'], 14)
                            fig.add_trace(go.Scatter(x=df_chart.index, y=rsi_vals, line=dict(color='purple', width=1.5), name="RSI 14"), row=current_row, col=1)
                            # RSI Zonen
                            fig.add_hline(y=70, line_dash="dot", line_color="red", row=current_row, col=1)
                            fig.add_hline(y=30, line_dash="dot", line_color="green", row=current_row, col=1)
                            
                        elif ind == "RP2 Indikator (SinepTrader)":
                            rp2_vals = calc_rp2_indicator(df_chart, ticker_input_chart)
                            
                            # Farbe dynamisch: Grün wenn >= 0, sonst Rot (Als Bar-Chart besonders übersichtlich)
                            colors = ['#26a69a' if val >= 0 else '#ef5350' for val in rp2_vals]
                            
                            fig.add_trace(go.Bar(
                                x=rp2_vals.index, 
                                y=rp2_vals, 
                                marker_color=colors, 
                                name="RP2"
                            ), row=current_row, col=1)
                            
                            # Nulllinie wie im Pine Script
                            fig.add_hline(y=0, line_dash="dot", line_color="gray", row=current_row, col=1)
                            
                        current_row += 1

                    # Layout optimieren
                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        margin=dict(l=10, r=10, t=30, b=10),
                        height=500 + (num_subcharts * 150), # Chart wächst mit Subcharts
                        template="plotly_white",
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Keine historischen Kursdaten gefunden.")
            except Exception as e:
                st.error(f"Fehler beim Abrufen der Kursdaten: {e}")
