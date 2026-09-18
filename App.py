import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import os

warnings.filterwarnings('ignore')

st.set_page_config(page_title="RP2 Analysis", page_icon="📈", layout="wide")

# ==========================================
# CUSTOM CSS & HINTERGRUND-ANIMATION
# ==========================================
custom_css = """
<style>
/* Der animierte Netzwerk-Hintergrund */
.stApp {
    background-color: #0b0f19 !important;
    background-image: 
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cg fill='%2326a69a' fill-opacity='0.4'%3E%3Ccircle cx='50' cy='50' r='2'/%3E%3Ccircle cx='200' cy='150' r='3'/%3E%3Ccircle cx='350' cy='50' r='1.5'/%3E%3Ccircle cx='100' cy='300' r='2.5'/%3E%3Ccircle cx='300' cy='350' r='2'/%3E%3Ccircle cx='400' cy='200' r='2'/%3E%3Ccircle cx='150' cy='400' r='1.5'/%3E%3Ccircle cx='0' cy='250' r='2'/%3E%3C/g%3E%3Cg stroke='%2326a69a' stroke-opacity='0.2' stroke-width='1'%3E%3Cline x1='50' y1='50' x2='200' y2='150'/%3E%3Cline x1='200' y1='150' x2='350' y2='50'/%3E%3Cline x1='50' y1='50' x2='100' y2='300'/%3E%3Cline x1='200' y1='150' x2='100' y2='300'/%3E%3Cline x1='200' y1='150' x2='300' y2='350'/%3E%3Cline x1='100' y1='300' x2='300' y2='350'/%3E%3Cline x1='350' y1='50' x2='300' y2='350'/%3E%3Cline x1='350' y1='50' x2='400' y2='200'/%3E%3Cline x1='300' y1='350' x2='400' y2='200'/%3E%3Cline x1='200' y1='150' x2='400' y2='200'/%3E%3Cline x1='100' y1='300' x2='150' y2='400'/%3E%3Cline x1='300' y1='350' x2='150' y2='400'/%3E%3Cline x1='50' y1='50' x2='0' y2='250'/%3E%3Cline x1='100' y1='300' x2='0' y2='250'/%3E%3Cline x1='200' y1='150' x2='0' y2='250'/%3E%3C/g%3E%3C/svg%3E"),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cg fill='%2342a5f5' fill-opacity='0.3'%3E%3Ccircle cx='30' cy='80' r='1.5'/%3E%3Ccircle cx='180' cy='40' r='2'/%3E%3Ccircle cx='250' cy='200' r='1'/%3E%3Ccircle cx='80' cy='250' r='2'/%3E%3Ccircle cx='300' cy='150' r='1.5'/%3E%3Ccircle cx='150' cy='300' r='1'/%3E%3C/g%3E%3Cg stroke='%2342a5f5' stroke-opacity='0.15' stroke-width='0.5'%3E%3Cline x1='30' y1='80' x2='180' y2='40'/%3E%3Cline x1='180' y1='40' x2='250' y2='200'/%3E%3Cline x1='250' y1='200' x2='80' y2='250'/%3E%3Cline x1='80' y1='250' x2='30' y2='80'/%3E%3Cline x1='180' y1='40' x2='300' y2='150'/%3E%3Cline x1='250' y1='200' x2='300' y2='150'/%3E%3Cline x1='80' y1='250' x2='150' y2='300'/%3E%3Cline x1='250' y1='200' x2='150' y2='300'/%3E%3C/g%3E%3C/svg%3E");
    background-size: 800px 800px, 500px 500px;
    background-position: 0 0, 0 0;
    animation: moveNets 120s linear infinite;
}

/* Parallax-Animation der zwei Netz-Ebenen */
@keyframes moveNets {
    0% { background-position: 0 0, 0 0; }
    100% { background-position: 800px 800px, -500px 500px; }
}

/* Macht den Haupt-Container leicht transparent mit Glassmorphism-Effekt */
.block-container {
    background-color: rgba(14, 17, 23, 0.88) !important;
    border-radius: 12px;
    padding: 2rem !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(5px);
    margin-top: 1.5rem;
}

/* Den oberen Balken (Header) von Streamlit ebenfalls anpassen */
[data-testid="stHeader"] {
    background-color: rgba(14, 17, 23, 0.7) !important;
    backdrop-filter: blur(10px);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# APP HEADER & LOGO
# ==========================================
# 1. Den absoluten Pfad des aktuellen Ordners ermitteln (sicher für Cloud)
base_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Automatisch nach der Logo-Datei suchen (egal ob jpg, jpeg oder png)
logo_path = None
for ext in ["jpg", "jpeg", "png"]:
    temp_path = os.path.join(base_dir, f"logo.{ext}")
    if os.path.exists(temp_path):
        logo_path = temp_path
        break

if logo_path:
    # Bild in Base64 umwandeln, damit es in HTML dargestellt werden kann
    with open(logo_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    
    # Korrekten MIME-Type für HTML setzen
    mime_type = "image/png" if logo_path.endswith("png") else "image/jpeg"
    
    # Bild rendern (mit object-fit für saubere Proportionen)
    logo_html = f"<img src='data:{mime_type};base64,{encoded_string}' style='width: 90px; height: 90px; object-fit: contain; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>"
else:
    # Fallback, falls das Bild immer noch nicht gefunden wird
    logo_html = "<div style='background: linear-gradient(135deg, #26a69a 0%, #00796b 100%); width: 90px; height: 90px; display: flex; align-items: center; justify-content: center; border-radius: 12px; color: white; font-size: 40px;'>📈</div>"

st.markdown(f"""
    <div style='display: flex; justify-content: center; align-items: center; gap: 20px; margin-bottom: 20px;'>
        {logo_html}
        <div>
            <h1 style='margin: 0; font-size: 32px;'>RP2 Analysis</h1>
            <p style='margin: 0; color: gray; font-size: 14px;'>Professional Fundamental & Valuation Suite</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# DATEN LADE FUNKTIONEN
# ==========================================
@st.cache_data(ttl=3600)  
def load_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        
        info = stock.info
        guv_a = stock.financials
        guv_q = stock.quarterly_financials
        bilanz_a = stock.balance_sheet
        bilanz_q = stock.quarterly_balance_sheet
        cf_a = stock.cashflow
        cf_q = stock.quarterly_cashflow
        insider = stock.major_holders
        
        try:
            insider_trans = stock.insider_transactions
        except:
            insider_trans = None
        
        try:
            ebit = info.get('ebitda', 0) 
            total_assets = info.get('totalAssets', bilanz_a.loc['Total Assets'].iloc[0] if 'Total Assets' in bilanz_a.index else 1)
            current_liabilities = bilanz_a.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in bilanz_a.index else 0
            net_working_capital = (bilanz_a.loc['Current Assets'].iloc[0] if 'Current Assets' in bilanz_a.index else 0) - current_liabilities
            fixed_assets = total_assets - (bilanz_a.loc['Current Assets'].iloc[0] if 'Current Assets' in bilanz_a.index else 0)
            
            roc = ebit / (net_working_capital + fixed_assets) if (net_working_capital + fixed_assets) > 0 else np.nan
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
            "insider_trans": insider_trans,
            "calc_roc": roc,
            "calc_roic": roic
        }
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def load_screener_data():
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
        "SAP", "SIE.DE", "ALV.DE", "VOW3.DE", "ASML", "LVMUY", 
        "TCEHY", "BABA", "TSM", "NVO", "JNJ", "JPM", "V",
        "ADBE", "CRM", "NFLX", "DIS", "MCD", "KO"
    ]
    
    data_list = []
    for t in tickers:
        try:
            data = load_stock_data(t)
            if not data or not data['info']:
                continue
            
            info = data['info']
            if 'marketCap' not in info or info['marketCap'] is None:
                continue
               
            roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else np.nan
            marge = info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else np.nan
            kgv = info.get("trailingPE", np.nan)
            
            # Echten RP2 Score berechnen anstatt Schätzung
            rp2_score = calc_latest_rp2(data)
                
            data_list.append({
                "Ticker": t,
                "Name": info.get("shortName", t),
                "Land": info.get("country", "Unbekannt"),
                "M.Cap (Mrd $)": info.get("marketCap", 0) / 1e9,
                "KGV": kgv,
                "KBV": info.get("priceToBook", np.nan),
                "Marge (%)": marge,
                "ROE (%)": roe,
                "RP2 Power (%)": rp2_score,
                "Div. Rendite (%)": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
            })
        except:
            continue
            
    df = pd.DataFrame(data_list)
    return df

# ==========================================
# INDIKATOREN & BERECHNUNGEN
# ==========================================
def calc_sma(series, period):
    return series.rolling(window=period).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_latest_rp2(data):
    try:
        guv_q = data['guv_q'].T
        bilanz_q = data['bilanz_q'].T
        info = data['info']
        price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose', 1)))
        
        # Sicherstellen, dass die Daten chronologisch aufsteigend sind (älteste zuerst, neueste zuletzt)
        guv_q.index = pd.to_datetime(guv_q.index)
        bilanz_q.index = pd.to_datetime(bilanz_q.index)
        guv_q = guv_q.sort_index()
        bilanz_q = bilanz_q.sort_index()
        
        net_income_q = guv_q['Net Income'].dropna() if 'Net Income' in guv_q.columns else guv_q['Net Income Common Stockholders'].dropna()
        ebit_q = guv_q['EBIT'].dropna() if 'EBIT' in guv_q.columns else guv_q['Operating Income'].dropna()
        shares = guv_q['Basic Average Shares'].iloc[-1] if 'Basic Average Shares' in guv_q.columns else info.get('sharesOutstanding', 1)
        
        net_income_ttm = net_income_q.iloc[-4:].sum() if len(net_income_q) >= 4 else net_income_q.sum() * (4 / max(len(net_income_q), 1))
        ebit_ttm = ebit_q.iloc[-4:].sum() if len(ebit_q) >= 4 else ebit_q.sum() * (4 / max(len(ebit_q), 1))
        
        eps_ttm = net_income_ttm / shares
        equity = bilanz_q['Stockholders Equity'].iloc[-1] if 'Stockholders Equity' in bilanz_q.columns else bilanz_q['Total Equity Gross Minority Interest'].iloc[-1]
        bvps = equity / shares
        
        total_assets = bilanz_q['Total Assets'].iloc[-1]
        current_liabilities = bilanz_q['Current Liabilities'].iloc[-1] if 'Current Liabilities' in bilanz_q.columns else 0
        invested_capital = total_assets - current_liabilities
        roic = ebit_ttm / invested_capital if invested_capital > 0 else 0
        
        target_value = 22.5
        inner_sqrt = target_value * eps_ttm * bvps
        sqrt_val = np.sqrt(max(inner_sqrt, 0)) if inner_sqrt >= 0 else 0
        rp2 = (sqrt_val * (roic / price) * 100) - 20
        return rp2
    except:
        return np.nan

def calc_rp2_indicator(df_chart, ticker_symbol):
    data = load_stock_data(ticker_symbol)
    if not data or data['guv_q'] is None or data['bilanz_q'] is None:
        return pd.Series(np.nan, index=df_chart.index)
        
    guv_q = data['guv_q'].T
    bilanz_q = data['bilanz_q'].T
    info = data['info']
    
    guv_q.index = pd.to_datetime(guv_q.index)
    bilanz_q.index = pd.to_datetime(bilanz_q.index)
    guv_q = guv_q.sort_index()
    bilanz_q = bilanz_q.sort_index()
    
    fund = pd.DataFrame(index=guv_q.index)
    
    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)
        
    net_income_q = get_val(guv_q, ['Net Income', 'Net Income Common Stockholders'])
    ebit_q = get_val(guv_q, ['EBIT', 'Operating Income'])
    shares = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
    
    if shares.isna().all():
        shares = info.get('sharesOutstanding', np.nan)
        
    net_income_ttm = net_income_q.rolling(window=4, min_periods=1).sum() 
    ebit_ttm = ebit_q.rolling(window=4, min_periods=1).sum() 
        
    fund['EPS_TTM'] = net_income_ttm / shares
    fund['Equity'] = get_val(bilanz_q, ['Stockholders Equity', 'Total Equity Gross Minority Interest'])
    fund['Total Assets'] = get_val(bilanz_q, ['Total Assets'])
    fund['Current Liabilities'] = get_val(bilanz_q, ['Current Liabilities'])
    
    fund['BVPS'] = fund['Equity'] / shares
    fund['Invested_Capital'] = fund['Total Assets'] - fund['Current Liabilities']
    fund['ROIC'] = ebit_ttm / fund['Invested_Capital']
    
    try:
        chart_idx = df_chart.index.tz_localize(None)
        fund.index = fund.index.tz_localize(None)
    except:
        chart_idx = df_chart.index
        
    fund_merged = fund.reindex(chart_idx.union(fund.index)).sort_index().ffill()
    fund_merged = fund_merged.reindex(chart_idx) 
    
    target_value = 22.5
    inner_sqrt = target_value * fund_merged['EPS_TTM'] * fund_merged['BVPS']
    sqrt_val = np.where(inner_sqrt >= 0, np.sqrt(np.maximum(inner_sqrt, 0)), np.nan)
    
    rp2 = (sqrt_val * (fund_merged['ROIC'] / df_chart['Close']) * 100) - 20
    return rp2

def calc_rp2_cf_indicator(df_chart, ticker_symbol):
    data = load_stock_data(ticker_symbol)
    if not data or data['cashflow_q'] is None or data['bilanz_q'] is None or data['guv_q'] is None:
        return pd.Series(np.nan, index=df_chart.index)
        
    cf_q = data['cashflow_q'].T
    bilanz_q = data['bilanz_q'].T
    guv_q = data['guv_q'].T
    info = data['info']
    
    cf_q.index = pd.to_datetime(cf_q.index)
    bilanz_q.index = pd.to_datetime(bilanz_q.index)
    guv_q.index = pd.to_datetime(guv_q.index)
    
    cf_q = cf_q.sort_index()
    bilanz_q = bilanz_q.sort_index()
    guv_q = guv_q.sort_index()
    
    fund = pd.DataFrame(index=cf_q.index)
    
    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)
        
    ocf_q = get_val(cf_q, ['Operating Cash Flow', 'Total Cash From Operating Activities', 'Cash Flow From Continuing Operating Activities'])
    ebit_q = get_val(guv_q, ['EBIT', 'Operating Income'])
    shares = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
    
    if shares.isna().all():
        shares = info.get('sharesOutstanding', np.nan)
        
    ocf_ttm = ocf_q.rolling(window=4, min_periods=1).sum() 
    ebit_ttm = ebit_q.rolling(window=4, min_periods=1).sum() 
        
    fund['CFPS_TTM'] = ocf_ttm / shares
    fund['Equity'] = get_val(bilanz_q, ['Stockholders Equity', 'Total Equity Gross Minority Interest'])
    fund['Total Assets'] = get_val(bilanz_q, ['Total Assets'])
    fund['Current Liabilities'] = get_val(bilanz_q, ['Current Liabilities'])
    
    fund['BVPS'] = fund['Equity'] / shares
    fund['Invested_Capital'] = fund['Total Assets'] - fund['Current Liabilities']
    fund['ROIC'] = ebit_ttm / fund['Invested_Capital']
    
    try:
        chart_idx = df_chart.index.tz_localize(None)
        fund.index = fund.index.tz_localize(None)
    except:
        chart_idx = df_chart.index
        
    fund_merged = fund.reindex(chart_idx.union(fund.index)).sort_index().ffill()
    fund_merged = fund_merged.reindex(chart_idx) 
    
    target_value = 22.5
    inner_sqrt = target_value * fund_merged['CFPS_TTM'] * fund_merged['BVPS']
    sqrt_val = np.where(inner_sqrt >= 0, np.sqrt(np.maximum(inner_sqrt, 0)), np.nan)
    
    rp2_cf = (sqrt_val * (fund_merged['ROIC'] / df_chart['Close']) * 100) - 20
    return rp2_cf

def calc_rp2_peg_indicator(df_chart, ticker_symbol):
    data = load_stock_data(ticker_symbol)
    if not data or data['guv_q'] is None or data['bilanz_q'] is None:
        return pd.Series(np.nan, index=df_chart.index)
        
    guv_q = data['guv_q'].T
    bilanz_q = data['bilanz_q'].T
    info = data['info']
    
    guv_q.index = pd.to_datetime(guv_q.index)
    bilanz_q.index = pd.to_datetime(bilanz_q.index)
    guv_q = guv_q.sort_index()
    bilanz_q = bilanz_q.sort_index()
    
    fund = pd.DataFrame(index=guv_q.index)
    
    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)
        
    net_income_q = get_val(guv_q, ['Net Income', 'Net Income Common Stockholders'])
    ebit_q = get_val(guv_q, ['EBIT', 'Operating Income'])
    shares = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
    
    if shares.isna().all():
        shares = info.get('sharesOutstanding', np.nan)
        
    net_income_ttm = net_income_q.rolling(window=4, min_periods=1).sum() 
    ebit_ttm = ebit_q.rolling(window=4, min_periods=1).sum() 
    eps_ttm = net_income_ttm / shares
    
    eps_ttm_prev = eps_ttm.shift(4)
    eps_growth = ((eps_ttm - eps_ttm_prev) / eps_ttm_prev.abs()) * 100
    eps_growth = eps_growth.replace([np.inf, -np.inf], np.nan)
    
    fund['EPS_Adj'] = eps_ttm * eps_growth
    fund['Equity'] = get_val(bilanz_q, ['Stockholders Equity', 'Total Equity Gross Minority Interest'])
    fund['Total Assets'] = get_val(bilanz_q, ['Total Assets'])
    fund['Current Liabilities'] = get_val(bilanz_q, ['Current Liabilities'])
    
    fund['BVPS'] = fund['Equity'] / shares
    fund['Invested_Capital'] = fund['Total Assets'] - fund['Current Liabilities']
    fund['ROIC'] = (ebit_ttm / fund['Invested_Capital']) * 100
    
    try:
        chart_idx = df_chart.index.tz_localize(None)
        fund.index = fund.index.tz_localize(None)
    except:
        chart_idx = df_chart.index
        
    fund_merged = fund.reindex(chart_idx.union(fund.index)).sort_index().ffill()
    fund_merged = fund_merged.reindex(chart_idx) 
    
    target_value = 2.0  
    inner_sqrt = target_value * fund_merged['EPS_Adj'] * fund_merged['BVPS']
    sqrt_val = np.where(inner_sqrt >= 0, np.sqrt(np.maximum(inner_sqrt, 0)), np.nan)
    
    rp2_peg = ((sqrt_val / df_chart['Close']) * (fund_merged['ROIC'] / 15.0) - 1) * 10 - 10
    return rp2_peg

def calc_rp2_pe_indicator(df_chart, ticker_symbol):
    data = load_stock_data(ticker_symbol)
    if not data or data['guv_q'] is None:
        return pd.DataFrame()

    guv_q = data['guv_q'].T
    guv_q.index = pd.to_datetime(guv_q.index)
    guv_q = guv_q.sort_index()
    info = data['info']

    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)

    net_income_q = get_val(guv_q, ['Net Income', 'Net Income Common Stockholders'])
    shares = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])

    if shares.isna().all():
        shares = info.get('sharesOutstanding', np.nan)

    net_income_ttm = net_income_q.rolling(window=4, min_periods=1).sum() 
    eps_ttm = net_income_ttm / shares

    try:
        chart_idx = df_chart.index.tz_localize(None)
        eps_ttm.index = eps_ttm.index.tz_localize(None)
    except:
        chart_idx = df_chart.index

    eps_merged = eps_ttm.reindex(chart_idx.union(eps_ttm.index)).sort_index().ffill()
    eps_merged = eps_merged.reindex(chart_idx)

    pe_vals = np.where(eps_merged > 0, df_chart['Close'] / eps_merged, np.nan)
    pe_series = pd.Series(pe_vals, index=df_chart.index)

    pe_sma = pe_series.rolling(window=300, min_periods=1).mean()
    buy_line = pe_series.expanding(min_periods=10).quantile(0.1)
    sell_line = pe_series.expanding(min_periods=10).quantile(0.9)

    return pd.DataFrame({
        'PE': pe_series,
        'Average': pe_sma,
        'Buy': buy_line,
        'Sell': sell_line
    })

def calc_rp2_ev_ebitda_indicator(df_chart, ticker_symbol):
    data = load_stock_data(ticker_symbol)
    if not data or data['guv_q'] is None or data['bilanz_q'] is None:
        return pd.DataFrame()

    guv_q = data['guv_q'].T
    guv_q.index = pd.to_datetime(guv_q.index)
    guv_q = guv_q.sort_index()
    
    bilanz_q = data['bilanz_q'].T
    bilanz_q.index = pd.to_datetime(bilanz_q.index)
    bilanz_q = bilanz_q.sort_index()
    
    info = data['info']

    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)

    ebitda_q = get_val(guv_q, ['EBITDA', 'Normalized EBITDA'])
    if ebitda_q.isna().all():
        ebitda_q = get_val(guv_q, ['EBIT', 'Operating Income'])
        
    shares_q = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
    if shares_q.isna().all():
        shares_q = pd.Series(info.get('sharesOutstanding', np.nan), index=guv_q.index)

    total_debt_q = get_val(bilanz_q, ['Total Debt']).fillna(0)
    cash_q = get_val(bilanz_q, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments', 'Total Cash']).fillna(0)

    ebitda_ttm = ebitda_q.rolling(window=4, min_periods=1).sum() 

    try:
        chart_idx = df_chart.index.tz_localize(None)
        ebitda_ttm.index = ebitda_ttm.index.tz_localize(None)
        shares_q.index = shares_q.index.tz_localize(None)
        total_debt_q.index = total_debt_q.index.tz_localize(None)
        cash_q.index = cash_q.index.tz_localize(None)
    except:
        chart_idx = df_chart.index

    ebitda_merged = ebitda_ttm.reindex(chart_idx.union(ebitda_ttm.index)).sort_index().ffill().reindex(chart_idx)
    shares_merged = shares_q.reindex(chart_idx.union(shares_q.index)).sort_index().ffill().reindex(chart_idx)
    debt_merged = total_debt_q.reindex(chart_idx.union(total_debt_q.index)).sort_index().ffill().reindex(chart_idx)
    cash_merged = cash_q.reindex(chart_idx.union(cash_q.index)).sort_index().ffill().reindex(chart_idx)

    mc = df_chart['Close'] * shares_merged
    ev = mc + debt_merged - cash_merged

    ev_ebitda_vals = np.where(ebitda_merged > 0, ev / ebitda_merged, np.nan)
    ev_ebitda_series = pd.Series(ev_ebitda_vals, index=df_chart.index)

    ev_sma = ev_ebitda_series.rolling(window=300, min_periods=1).mean()
    buy_line = ev_ebitda_series.expanding(min_periods=10).quantile(0.1)
    sell_line = ev_ebitda_series.expanding(min_periods=10).quantile(0.9)

    return pd.DataFrame({
        'EV_EBITDA': ev_ebitda_series,
        'Average': ev_sma,
        'Buy': buy_line,
        'Sell': sell_line
    })

def calc_rp2_ev_sales_indicator(df_chart, ticker_symbol):
    data = load_stock_data(ticker_symbol)
    if not data or data['guv_q'] is None or data['bilanz_q'] is None:
        return pd.DataFrame()

    guv_q = data['guv_q'].T
    guv_q.index = pd.to_datetime(guv_q.index)
    guv_q = guv_q.sort_index()
    
    bilanz_q = data['bilanz_q'].T
    bilanz_q.index = pd.to_datetime(bilanz_q.index)
    bilanz_q = bilanz_q.sort_index()
    
    info = data['info']

    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)

    revenue_q = get_val(guv_q, ['Total Revenue', 'Operating Revenue', 'Revenue'])
    shares_q = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
    if shares_q.isna().all():
        shares_q = pd.Series(info.get('sharesOutstanding', np.nan), index=guv_q.index)

    total_debt_q = get_val(bilanz_q, ['Total Debt']).fillna(0)
    cash_q = get_val(bilanz_q, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments', 'Total Cash']).fillna(0)

    revenue_ttm = revenue_q.rolling(window=4, min_periods=1).sum() 

    try:
        chart_idx = df_chart.index.tz_localize(None)
        revenue_ttm.index = revenue_ttm.index.tz_localize(None)
        shares_q.index = shares_q.index.tz_localize(None)
        total_debt_q.index = total_debt_q.index.tz_localize(None)
        cash_q.index = cash_q.index.tz_localize(None)
    except:
        chart_idx = df_chart.index

    revenue_merged = revenue_ttm.reindex(chart_idx.union(revenue_ttm.index)).sort_index().ffill().reindex(chart_idx)
    shares_merged = shares_q.reindex(chart_idx.union(shares_q.index)).sort_index().ffill().reindex(chart_idx)
    debt_merged = total_debt_q.reindex(chart_idx.union(total_debt_q.index)).sort_index().ffill().reindex(chart_idx)
    cash_merged = cash_q.reindex(chart_idx.union(cash_q.index)).sort_index().ffill().reindex(chart_idx)

    mc = df_chart['Close'] * shares_merged
    ev = mc + debt_merged - cash_merged

    ev_sales_vals = np.where(revenue_merged > 0, ev / revenue_merged, np.nan)
    ev_sales_series = pd.Series(ev_sales_vals, index=df_chart.index)

    ev_sma = ev_sales_series.rolling(window=300, min_periods=1).mean()
    buy_line = ev_sales_series.expanding(min_periods=10).quantile(0.1)
    sell_line = ev_sales_series.expanding(min_periods=10).quantile(0.9)

    return pd.DataFrame({
        'EV_Sales': ev_sales_series,
        'Average': ev_sma,
        'Buy': buy_line,
        'Sell': sell_line
    })

def calc_rp2_p_fcf_indicator(df_chart, ticker_symbol):
    data = load_stock_data(ticker_symbol)
    if not data or data['cashflow_q'] is None or data['guv_q'] is None:
        return pd.DataFrame()

    cf_q = data['cashflow_q'].T
    cf_q.index = pd.to_datetime(cf_q.index)
    cf_q = cf_q.sort_index()
    
    guv_q = data['guv_q'].T
    guv_q.index = pd.to_datetime(guv_q.index)
    guv_q = guv_q.sort_index()
    
    info = data['info']

    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)

    fcf_q = get_val(cf_q, ['Free Cash Flow'])
    if fcf_q.isna().all():
        ocf = get_val(cf_q, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
        capex = get_val(cf_q, ['Capital Expenditure'])
        fcf_q = ocf - capex.abs()
        
    shares_q = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
    if shares_q.isna().all():
        shares_q = pd.Series(info.get('sharesOutstanding', np.nan), index=cf_q.index)

    fcf_ttm = fcf_q.rolling(window=4, min_periods=1).sum() 

    try:
        chart_idx = df_chart.index.tz_localize(None)
        fcf_ttm.index = fcf_ttm.index.tz_localize(None)
        shares_q.index = shares_q.index.tz_localize(None)
    except:
        chart_idx = df_chart.index

    fcf_merged = fcf_ttm.reindex(chart_idx.union(fcf_ttm.index)).sort_index().ffill().reindex(chart_idx)
    shares_merged = shares_q.reindex(chart_idx.union(shares_q.index)).sort_index().ffill().reindex(chart_idx)

    fcf_per_share = fcf_merged / shares_merged
    p_fcf_vals = np.where(fcf_per_share > 0, df_chart['Close'] / fcf_per_share, np.nan)
    p_fcf_series = pd.Series(p_fcf_vals, index=df_chart.index)

    p_fcf_sma = p_fcf_series.rolling(window=300, min_periods=1).mean()
    buy_line = p_fcf_series.expanding(min_periods=10).quantile(0.1)
    sell_line = p_fcf_series.expanding(min_periods=10).quantile(0.9)

    return pd.DataFrame({
        'P_FCF': p_fcf_series,
        'Average': p_fcf_sma,
        'Buy': buy_line,
        'Sell': sell_line
    })

def calc_rp2_intrinsic(df_chart, ticker_symbol, params):
    data = load_stock_data(ticker_symbol)
    if not data or data['guv_q'] is None or data['bilanz_q'] is None:
        return pd.DataFrame()
        
    guv_q = data['guv_q'].T
    bilanz_q = data['bilanz_q'].T
    info = data['info']
    
    guv_q.index = pd.to_datetime(guv_q.index)
    bilanz_q.index = pd.to_datetime(bilanz_q.index)
    guv_q = guv_q.sort_index()
    bilanz_q = bilanz_q.sort_index()
    
    fund = pd.DataFrame(index=bilanz_q.index.union(guv_q.index)).sort_index()
    
    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)
        
    net_income_q = get_val(guv_q, ['Net Income', 'Net Income Common Stockholders'])
    shares_q = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
    if shares_q.isna().all():
        shares_q = info.get('sharesOutstanding', np.nan)
    net_income_ttm = net_income_q.rolling(window=4, min_periods=1).sum()
    eps = net_income_ttm / shares_q
    
    equity = get_val(bilanz_q, ['Stockholders Equity', 'Total Equity Gross Minority Interest'])
    bvps = equity / shares_q
    
    goodwill = get_val(bilanz_q, ['Goodwill', 'Goodwill And Other Intangible Assets']).fillna(0)
    intangibles = get_val(bilanz_q, ['Other Intangible Assets']).fillna(0)
    
    tangible_eq = equity - goodwill - intangibles
    tbvps = tangible_eq / shares_q
    final_bvps = tbvps.where(tbvps.notna(), bvps)
    
    ebit_q = get_val(guv_q, ['EBIT', 'Operating Income'])
    ebit_ttm = ebit_q.rolling(window=4, min_periods=1).sum()
    total_assets = get_val(bilanz_q, ['Total Assets'])
    current_liabilities = get_val(bilanz_q, ['Current Liabilities'])
    invested_capital = total_assets - current_liabilities
    roic = ebit_ttm / invested_capital
    
    cash_sti = get_val(bilanz_q, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments', 'Total Cash']).fillna(0)
    recv_net = get_val(bilanz_q, ['Net Receivables', 'Accounts Receivable']).fillna(0)
    inv_val = get_val(bilanz_q, ['Inventory']).fillna(0)
    ppe_net = get_val(bilanz_q, ['Net PPE', 'Properties']).fillna(0)
    short_term_debt = get_val(bilanz_q, ['Current Debt', 'Short Long Term Debt']).fillna(0)
    total_debt = get_val(bilanz_q, ['Total Debt']).fillna(0)
    
    weighted_sum = (params['w_cash'] * cash_sti) + (params['w_recv'] * recv_net) + (params['w_inv'] * inv_val) + (params['w_ppe'] * ppe_net) - short_term_debt
    weighted_sumh = (params['w_cash'] * cash_sti) + (params['w_recvh'] * recv_net) + (params['w_invh'] * inv_val) + (params['w_ppeh'] * ppe_net) - short_term_debt
    weighted_sumtot = (params['w_cash'] * cash_sti) + (params['w_recv'] * recv_net) + (params['w_inv'] * inv_val) + (params['w_ppe'] * ppe_net) - total_debt
    
    fund['EPS'] = eps
    fund['Final_BVPS'] = final_bvps
    fund['ROIC'] = roic
    fund['Shares'] = shares_q
    fund['Sum'] = weighted_sum
    fund['Sum_H'] = weighted_sumh
    fund['Sum_Tot'] = weighted_sumtot
    
    try:
        chart_idx = df_chart.index.tz_localize(None)
        fund.index = fund.index.tz_localize(None)
    except:
        chart_idx = df_chart.index
        
    fund_merged = fund.reindex(chart_idx.union(fund.index)).sort_index().ffill()
    fund_merged = fund_merged.reindex(chart_idx) 
    
    valid_eps = fund_merged['EPS'].where(fund_merged['EPS'] > 0, np.nan)
    valid_bvps = fund_merged['Final_BVPS'].where(fund_merged['Final_BVPS'] > 0, np.nan)
    valid_roic = fund_merged['ROIC'].where(fund_merged['ROIC'] > 0, np.nan)
    
    current_pe = df_chart['Close'] / valid_eps
    inner_val = params['targetMultiplier'] * valid_eps * valid_bvps * valid_roic
    current_intrinsic = np.where(inner_val >= 0, np.sqrt(np.maximum(inner_val, 0)), np.nan)
    intrinsic_value = current_intrinsic * (1.0 + params['expectedGrowth']) * (params['normalizedPE'] / current_pe)
    
    shares_arr = fund_merged['Shares']
    if params['normalizePS']:
        val_ps = np.where(shares_arr > 0, fund_merged['Sum'] / shares_arr, fund_merged['Sum'])
        val_psh = np.where(shares_arr > 0, fund_merged['Sum_H'] / shares_arr, fund_merged['Sum_H'])
        val_pstot = np.where(shares_arr > 0, fund_merged['Sum_Tot'] / shares_arr, fund_merged['Sum_Tot'])
    else:
        val_ps = fund_merged['Sum']
        val_psh = fund_merged['Sum_H']
        val_pstot = fund_merged['Sum_Tot']
    
    return pd.DataFrame({
        'IntrinsicValue': intrinsic_value,
        'CurrentIntrinsic': current_intrinsic,
        'Val_PS': val_ps,
        'Val_PSH': val_psh,
        'Val_PSTOT': val_pstot
    }, index=df_chart.index)

def calc_greenwald_valuation(df_chart, ticker_symbol, params):
    data = load_stock_data(ticker_symbol)
    if not data or data['guv_q'] is None or data['bilanz_q'] is None:
        return pd.DataFrame()
        
    guv_q = data['guv_q'].T
    bilanz_q = data['bilanz_q'].T
    info = data['info']
    
    guv_q.index = pd.to_datetime(guv_q.index)
    bilanz_q.index = pd.to_datetime(bilanz_q.index)
    guv_q = guv_q.sort_index()
    bilanz_q = bilanz_q.sort_index()
    
    common_index = bilanz_q.index.union(guv_q.index).sort_values()
    fund = pd.DataFrame(index=common_index)
    
    def get_val(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(np.nan, index=df.index)
        
    cash = get_val(bilanz_q, ['Cash And Cash Equivalents', 'Total Cash']).fillna(0)
    receivables = get_val(bilanz_q, ['Net Receivables', 'Accounts Receivable']).fillna(0)
    inventory = get_val(bilanz_q, ['Inventory']).fillna(0)
    ppe_net = get_val(bilanz_q, ['Net PPE', 'Properties']).fillna(0)
    total_liabilities = get_val(bilanz_q, ['Total Liabilities']).fillna(0)
    
    shares_q = get_val(guv_q, ['Basic Average Shares', 'Ordinary Shares Number'])
        
    rnd_q = get_val(guv_q, ['Research And Development']).fillna(0)
    sga_q = get_val(guv_q, ['Selling General And Administration', 'Operating Expense']).fillna(0)
    ebit_q = get_val(guv_q, ['EBIT', 'Operating Income']).fillna(0)
    tax_q = get_val(guv_q, ['Tax Provision', 'Income Tax Expense']).fillna(0)
    pretax_q = get_val(guv_q, ['Pretax Income']).fillna(0)
    
    rnd_ttm = rnd_q.rolling(window=4, min_periods=1).sum().abs()
    sga_ttm = sga_q.rolling(window=4, min_periods=1).sum().abs()
    ebit_ttm = ebit_q.rolling(window=4, min_periods=1).sum()
    tax_ttm = tax_q.rolling(window=4, min_periods=1).sum().abs()
    pretax_ttm = pretax_q.rolling(window=4, min_periods=1).sum()
    
    cash = cash.reindex(fund.index).ffill()
    receivables = receivables.reindex(fund.index).ffill()
    inventory = inventory.reindex(fund.index).ffill()
    ppe_net = ppe_net.reindex(fund.index).ffill()
    total_liabilities = total_liabilities.reindex(fund.index).ffill()
    
    rnd_ttm = rnd_ttm.reindex(fund.index).ffill()
    sga_ttm = sga_ttm.reindex(fund.index).ffill()
    ebit_ttm = ebit_ttm.reindex(fund.index).ffill()
    tax_ttm = tax_ttm.reindex(fund.index).ffill()
    pretax_ttm = pretax_ttm.reindex(fund.index).ffill()
    
    if shares_q.isna().all():
        shares_aligned = pd.Series(info.get('sharesOutstanding', np.nan), index=fund.index)
    else:
        shares_aligned = shares_q.reindex(fund.index).ffill()
    
    adj_cash = cash * params['cash_factor']
    adj_recv = receivables * params['recv_factor']
    adj_inv = inventory * params['inv_factor']
    adj_ppe = ppe_net * params['ppe_factor']
    
    add_rnd = (rnd_ttm * params['rnd_years']) if params['use_intangibles'] else pd.Series(0, index=fund.index)
    add_sga = (sga_ttm * params['sga_years']) if params['use_intangibles'] else pd.Series(0, index=fund.index)
    
    total_reproduction_assets = adj_cash + adj_recv + adj_inv + adj_ppe + add_rnd + add_sga
    av_total = total_reproduction_assets - total_liabilities
    
    av_per_share = np.where(shares_aligned > 0, av_total / shares_aligned, np.nan)
    
    eff_tax_rate = np.where(pretax_ttm != 0, tax_ttm / pretax_ttm, 0.25)
    final_tax_rate = np.clip(eff_tax_rate, 0.0, 0.40) 
    
    nopat = ebit_ttm * (1 - final_tax_rate)
    epv_total = nopat / params['wacc']
    epv_per_share = np.where(shares_aligned > 0, epv_total / shares_aligned, np.nan)
    
    fund['AV_PS'] = av_per_share
    fund['EPV_PS'] = epv_per_share
    
    try:
        chart_idx = df_chart.index.tz_localize(None)
        fund.index = fund.index.tz_localize(None)
    except:
        chart_idx = df_chart.index
        
    fund_merged = fund.reindex(chart_idx.union(fund.index)).sort_index().ffill()
    fund_merged = fund_merged.reindex(chart_idx) 
    
    buy_price = fund_merged['EPV_PS'] * (1 - params['margin_safety'])
    franchise_value = (fund_merged['EPV_PS'] / fund_merged['AV_PS']) - 1
    
    return pd.DataFrame({
        'AV_PS': fund_merged['AV_PS'],
        'EPV_PS': fund_merged['EPV_PS'],
        'Buy_Price': buy_price,
        'Franchise_Value': franchise_value
    }, index=df_chart.index)

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

def calculate_historical_stats(guv, bilanz):
    if guv is None or bilanz is None or guv.empty or bilanz.empty:
        return pd.DataFrame()
    
    common_cols = guv.columns.intersection(bilanz.columns)
    if len(common_cols) == 0:
        return pd.DataFrame()
        
    g = guv[common_cols]
    b = bilanz[common_cols]
    
    stats = pd.DataFrame(index=[
        "Brutto-Marge (%)", "Operative Marge (%)", "Netto-Marge (%)", 
        "ROE (%)", "ROA (%)", "Debt to Equity", "Current Ratio"
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

def render_statement(title, df_annual, df_quarterly, key_prefix):
    if df_annual is None or df_annual.empty or df_quarterly is None or df_quarterly.empty:
        st.warning(f"Keine Daten für {title} gefunden.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        period = st.radio(f"Zeitraum für {title}:", ["Quartalsweise", "Jährlich"], horizontal=True, key=f"radio_{key_prefix}")
    with col2:
        detail = st.radio("Detailgrad:", ["Kompakt", "Alle Zeilen"], horizontal=True, key=f"detail_{key_prefix}")
        
    df = df_quarterly if period == "Quartalsweise" else df_annual
    
    df = df.dropna(how='all')
    df.columns = [str(col).split(' ')[0] for col in df.columns]
    
    main_metrics = [
        'Total Revenue', 'Gross Profit', 'Operating Income', 'EBIT', 'Net Income', 'Net Income Common Stockholders',
        'Total Assets', 'Current Assets', 'Total Liabilities', 'Total Liabilities Net Minority Interest', 'Current Liabilities',
        'Stockholders Equity', 'Total Equity Gross Minority Interest', 'Total Debt', 'Net Debt', 
        'Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow', 'Free Cash Flow', 'End Cash Position'
    ]

    display_df = df.copy()

    if detail == "Kompakt":
        filtered_idx = []
        for idx in display_df.index:
            if any(m.lower() == str(idx).lower() for m in main_metrics):
                filtered_idx.append(idx)
        if filtered_idx:
            display_df = display_df.loc[filtered_idx]
    
    st.write("**Interaktive Grafik**")
    chart_placeholder = st.empty()
    
    st.write("**Datenmatrix (Klicke links auf die Zeile für den Chart):**")
    
    view_df = display_df.copy()
    for col in view_df.columns:
        view_df[col] = view_df[col].apply(format_large_number)
        
    selection_event = st.dataframe(
        view_df, 
        use_container_width=True,
        on_select="rerun",
        selection_mode="multi-row",
        key=f"df_select_{key_prefix}_{detail}_{period}"
    )
    
    selected_rows = selection_event.selection.rows
    if selected_rows:
        selected_metrics = display_df.iloc[selected_rows].index.tolist()
    else:
        available_metrics = display_df.index.tolist()
        selected_metrics = [available_metrics[0]] if available_metrics else []
    
    if selected_metrics:
        chart_data = display_df.loc[selected_metrics].T.sort_index()
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
            fig = go.Figure()
            for col in chart_data.columns:
                fig.add_trace(go.Bar(x=chart_data.index, y=chart_data[col], name=col))
            
            fig.update_layout(
                barmode='group',
                margin=dict(l=10, r=10, t=10, b=10),
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# UI TABS & LAYOUT
# ==========================================
tab1, tab2, tab3 = st.tabs(["🔍 Einzel-Analyse", "🎯 Screener", "📈 Kursverlauf"])

with tab1:
    st.header("Aktie analysieren")
    ticker_input = st.text_input("Ticker-Symbol eingeben (z.B. AAPL, MSFT, SAP):").upper()
    
    if ticker_input:
        data = load_stock_data(ticker_input)
        
        if data and data['info']:
            info = data['info']
            st.success(f"Daten für **{info.get('shortName', ticker_input)}** ({info.get('country', 'N/A')}) geladen!")
            
            mcap = info.get('marketCap', 0) / 1e9
            kgv = info.get('trailingPE', np.nan)
            kbv = info.get('priceToBook', np.nan)
            roic = data['calc_roic'] * 100 if not np.isnan(data['calc_roic']) else np.nan
            roc = data['calc_roc'] * 100 if not np.isnan(data['calc_roc']) else np.nan
            
            latest_rp2_score = calc_latest_rp2(data)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("KGV", f"{kgv:.1f}" if pd.notna(kgv) else "N/A")
            col2.metric("KBV", f"{kbv:.1f}" if pd.notna(kbv) else "N/A")
            col3.metric("M.Cap", f"${mcap:.1f}B" if mcap > 0 else "N/A")
            
            col4, col5, col6 = st.columns(3)
            col4.metric("ROIC (ca.)", f"{roic:.1f}%" if pd.notna(roic) else "N/A")
            col5.metric("ROC Greenblatt (ca.)", f"{roc:.1f}%" if pd.notna(roc) else "N/A")
            col6.metric("RP2 Power Score", f"{latest_rp2_score:.1f}%" if pd.notna(latest_rp2_score) else "N/A")
            
            st.markdown("---")
            
            sub1, sub2, sub3, sub4, sub5, sub6 = st.tabs(["GuV", "Bilanz", "Cashflow", "Statistiken", "Insider Anteile", "Insider Trades"])
            
            with sub1: render_statement("GuV (Income Statement)", data['guv_a'], data['guv_q'], "guv")
            with sub2: render_statement("Bilanz (Balance Sheet)", data['bilanz_a'], data['bilanz_q'], "bilanz")
            with sub3: render_statement("Cashflow", data['cashflow_a'], data['cashflow_q'], "cf")
            with sub4:
                st.write("**Historische Verhältnisse**")
                period_stats = st.radio("Zeitraum für Statistiken:", ["Quartalsweise", "Jährlich"], horizontal=True, key="radio_stats")
                
                hist_stats = calculate_historical_stats(data['guv_q'], data['bilanz_q']) if period_stats == "Quartalsweise" else calculate_historical_stats(data['guv_a'], data['bilanz_a'])
                
                if hist_stats is not None and not hist_stats.empty:
                    chart_placeholder_stats = st.empty()
                    st.write("**Datenmatrix (Klicke links auf die Zeile für Trend-Analyse):**")
                    
                    selection_event_stats = st.dataframe(
                        hist_stats, use_container_width=True, on_select="rerun", selection_mode="multi-row", key="df_select_stats"
                    )
                    
                    selected_rows_stats = selection_event_stats.selection.rows
                    selected_metrics_stats = hist_stats.iloc[selected_rows_stats].index.tolist() if selected_rows_stats else (hist_stats.index.tolist()[:1] if not hist_stats.empty else [])
                        
                    if selected_metrics_stats:
                        chart_data_stats = hist_stats.loc[selected_metrics_stats].T.sort_index()
                        with chart_placeholder_stats:
                            st.line_chart(chart_data_stats)
                else:
                    st.warning("Nicht genügend historische Daten vorhanden.")
            with sub5:
                if data['insider'] is not None and not data['insider'].empty:
                    df_insider = data['insider'].copy()
                    for col in df_insider.columns:
                        if pd.api.types.is_numeric_dtype(df_insider[col]):
                            df_insider[col] = df_insider[col].apply(lambda x: f"{x * 100:.2f}%" if pd.notna(x) else x)
                    st.dataframe(df_insider, use_container_width=True)
                else:
                    st.write("Keine Insider-Daten verfügbar.")
            with sub6:
                if data['insider_trans'] is not None and not data['insider_trans'].empty:
                    df_trans = data['insider_trans'].copy()
                    st.dataframe(df_trans, use_container_width=True)
                else:
                    st.write("Keine aktuellen Insider-Transaktionen gefunden.")
        else:
            st.error("Ticker nicht gefunden oder keine Daten verfügbar.")

with tab2:
    st.header("Globaler Screener")
    with st.spinner("Lade Screener-Daten..."):
        screener_df = load_screener_data()
        
    if not screener_df.empty:
        alle_laender = sorted(list(screener_df['Land'].unique()))
        gewaehlte_laender = st.multiselect("Nach Land filtern:", alle_laender, default=alle_laender)
        
        st.markdown("### 🎛️ Filterkriterien")
        st.caption("Lasse ein Feld leer (keine Eingabe), wenn das Kriterium nicht gefiltert werden soll.")
        
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            st.markdown("**M.Cap (Mrd $)**")
            min_mcap = st.number_input("Min M.Cap", value=None, placeholder="Kein Limit", key="mcap_min")
            max_mcap = st.number_input("Max M.Cap", value=None, placeholder="Kein Limit", key="mcap_max")
            
        with col_f2:
            st.markdown("**KGV**")
            min_kgv = st.number_input("Min KGV", value=None, placeholder="Kein Limit", key="kgv_min")
            max_kgv = st.number_input("Max KGV", value=None, placeholder="Kein Limit", key="kgv_max")
            
        with col_f3:
            st.markdown("**KBV**")
            min_kbv = st.number_input("Min KBV", value=None, placeholder="Kein Limit", key="kbv_min")
            max_kbv = st.number_input("Max KBV", value=None, placeholder="Kein Limit", key="kbv_max")
            
        with col_f4:
            st.markdown("**RP2 Power Score (%)**")
            min_rp2 = st.number_input("Min RP2", value=None, placeholder="Kein Limit", key="rp2_min")
            max_rp2 = st.number_input("Max RP2", value=None, placeholder="Kein Limit", key="rp2_max")
            
        # Basis-Maske: Land muss passen
        mask = screener_df['Land'].isin(gewaehlte_laender)
        
        # Dynamische Filterung anwenden, wenn Felder nicht leer (None) sind
        if min_mcap is not None:
            mask &= (screener_df['M.Cap (Mrd $)'].fillna(-9999) >= min_mcap)
        if max_mcap is not None:
            mask &= (screener_df['M.Cap (Mrd $)'].fillna(999999) <= max_mcap)
            
        if min_kgv is not None:
            mask &= (screener_df['KGV'].fillna(-9999) >= min_kgv)
        if max_kgv is not None:
            mask &= (screener_df['KGV'].fillna(999999) <= max_kgv)
            
        if min_kbv is not None:
            mask &= (screener_df['KBV'].fillna(-9999) >= min_kbv)
        if max_kbv is not None:
            mask &= (screener_df['KBV'].fillna(999999) <= max_kbv)
            
        if min_rp2 is not None:
            mask &= (screener_df['RP2 Power (%)'].fillna(-9999) >= min_rp2)
        if max_rp2 is not None:
            mask &= (screener_df['RP2 Power (%)'].fillna(999999) <= max_rp2)
            
        gefiltert = screener_df[mask].reset_index(drop=True)
        
        st.write(f"**Treffer: {len(gefiltert)} Unternehmen**")
        if len(gefiltert) > 0:
            st.dataframe(gefiltert.style.format({
                "M.Cap (Mrd $)": "{:.1f}", 
                "KGV": "{:.1f}", 
                "KBV": "{:.1f}", 
                "Marge (%)": "{:.1f}%", 
                "ROE (%)": "{:.1f}%", 
                "RP2 Power (%)": "{:.1f}%",
                "Div. Rendite (%)": "{:.1f}%"
            }).background_gradient(subset=['RP2 Power (%)', 'ROE (%)'], cmap='Greens'))
        else:
            st.warning("Keine Unternehmen entsprechen deinen Filterkriterien.")

with tab3:
    st.header("Historischer Kursverlauf & Indikatoren")
    
    col_c1, col_c2, col_c3 = st.columns([1, 1.5, 1.5])
    with col_c1:
        ticker_input_chart = st.text_input("Ticker-Symbol:", key="chart_ticker").upper()
    with col_c2:
        overlay_ind = st.multiselect("Overlays (im Chart):", ["SMA 50", "SMA 200", "RP2 Intrinsic Value", "Liquiditätswert pro Aktie", "Greenwald Valuation"])
    with col_c3:
        sub_ind = st.multiselect("Sub-Charts (max. 5):", ["RP2 Indikator (SinepTrader)", "RP2 CF Indikator (SinepTrader)", "RP2 PEG Indikator (SinepTrader)", "RP2 P E (SinepTrader)", "RP2 EV EBITDA (SinepTrader)", "RP2 EV Sales (SinepTrader)", "RP2 P FCF (SinepTrader)", "RSI 14"], max_selections=5)
    
    rp2iv_params = {
        'targetMultiplier': 112.5, 'expectedGrowth': 0.0, 'normalizedPE': 15.0,
        'w_cash': 1.0, 'w_recv': 0.75, 'w_inv': 0.50, 'w_ppe': 0.01,
        'w_recvh': 0.90, 'w_invh': 0.75, 'w_ppeh': 0.50, 'normalizePS': True
    }
    
    greenwald_params = {}
    
    needs_params = "RP2 Intrinsic Value" in overlay_ind or "Liquiditätswert pro Aktie" in overlay_ind or "Greenwald Valuation" in overlay_ind
    
    if needs_params:
        st.markdown("### ⚙️ Parameter-Einstellungen")
        with st.container():
            if "RP2 Intrinsic Value" in overlay_ind:
                st.markdown("**RP2 Intrinsic Value:**")
                col_p1, col_p2, col_p3 = st.columns(3)
                rp2iv_params['targetMultiplier'] = col_p1.number_input("Bewertungs-Multiplikator", value=112.5, step=1.0)
                rp2iv_params['expectedGrowth'] = col_p2.number_input("Erw. Gewinnwachstum (nächste 12M)", value=0.0, step=0.01)
                rp2iv_params['normalizedPE'] = col_p3.number_input("Ziel KGV", value=15.0, step=1.0)
                st.write("") 
                
            if "Liquiditätswert pro Aktie" in overlay_ind:
                st.markdown("**Gewichtung der Vermögenswerte (Liquiditätswert):**")
                col_w1, col_w2, col_w3, col_w4 = st.columns(4)
                rp2iv_params['w_cash'] = col_w1.number_input("Cash & STI", value=1.00, step=0.05)
                rp2iv_params['w_recv'] = col_w2.number_input("Forderungen (netto)", value=0.75, step=0.05)
                rp2iv_params['w_inv'] = col_w3.number_input("Vorräte", value=0.50, step=0.05)
                rp2iv_params['w_ppe'] = col_w4.number_input("Sachanlagen", value=0.01, step=0.05)
                
                st.markdown("**Alternative obere Gewichte:**")
                col_w1h, col_w2h, col_w3h = st.columns(3)
                rp2iv_params['w_recvh'] = col_w1h.number_input("Forderungen (H)", value=0.90, step=0.05)
                rp2iv_params['w_invh'] = col_w2h.number_input("Vorräte (H)", value=0.75, step=0.05)
                rp2iv_params['w_ppeh'] = col_w3h.number_input("Sachanlagen (H)", value=0.50, step=0.05)
                
                rp2iv_params['normalizePS'] = st.checkbox("Pro Aktie anzeigen (÷ Shares)", value=True)
                st.write("")
                
            if "Greenwald Valuation" in overlay_ind:
                st.markdown("**Greenwald Valuation: Deep Dive Analysis:**")
                st.caption("1. Materielle Assets anpassen")
                g1, g2, g3, g4 = st.columns(4)
                greenwald_params['cash_factor'] = g1.number_input("Cash Faktor", value=1.0, min_value=0.9, max_value=1.0, step=0.01)
                greenwald_params['recv_factor'] = g2.number_input("Forderungen Faktor", value=0.98, min_value=0.5, step=0.01)
                greenwald_params['inv_factor'] = g3.number_input("Vorräte Faktor", value=1.0, min_value=0.5, max_value=2.0, step=0.05)
                greenwald_params['ppe_factor'] = g4.number_input("PP&E Faktor", value=1.2, min_value=0.5, max_value=5.0, step=0.1)
                
                st.caption("2. Immaterielle Reproduktionskosten")
                g5, g6, g7 = st.columns(3)
                greenwald_params['use_intangibles'] = g5.checkbox("R&D und SG&A addieren?", value=True)
                greenwald_params['rnd_years'] = g6.number_input("Jahre an R&D addieren", value=2.0, min_value=0.0, step=0.5)
                greenwald_params['sga_years'] = g7.number_input("Jahre an SG&A addieren", value=1.0, min_value=0.0, step=0.5)
                
                st.caption("3. Bewertung & WACC")
                g8, g9 = st.columns(2)
                greenwald_params['wacc'] = g8.number_input("WACC (Kapitalkosten)", value=0.10, step=0.005)
                greenwald_params['margin_safety'] = g9.number_input("Sicherheitsmarge (MoS)", value=0.33, step=0.05)
                
        st.markdown("---")
        
    if ticker_input_chart:
        with st.spinner(f"Lade Kurs- und Fundamentaldaten für {ticker_input_chart}..."):
            try:
                df_chart = yf.download(ticker_input_chart, period="10y", interval="1wk")
                
                if not df_chart.empty:
                    if isinstance(df_chart.columns, pd.MultiIndex):
                        df_chart.columns = df_chart.columns.droplevel(1)
                        
                    num_subcharts = len(sub_ind)
                    row_heights = [0.6] + [0.4 / num_subcharts] * num_subcharts if num_subcharts > 0 else [1.0]
                    
                    fig = make_subplots(rows=num_subcharts + 1, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=row_heights)
                    
                    fig.add_trace(go.Candlestick(
                        x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                        low=df_chart['Low'], close=df_chart['Close'], name="Kurs"
                    ), row=1, col=1)
                    
                    if "SMA 50" in overlay_ind:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=calc_sma(df_chart['Close'], 50), line=dict(color='blue', width=1), name="SMA 50"), row=1, col=1)
                    if "SMA 200" in overlay_ind:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=calc_sma(df_chart['Close'], 200), line=dict(color='orange', width=2), name="SMA 200"), row=1, col=1)
                        
                    if "RP2 Intrinsic Value" in overlay_ind:
                        df_iv = calc_rp2_intrinsic(df_chart, ticker_input_chart, rp2iv_params)
                        if not df_iv.empty:
                            fig.add_trace(go.Scatter(x=df_iv.index, y=df_iv['IntrinsicValue'], line=dict(color='blue', width=2), name="Intrinsischer Wert"), row=1, col=1)
                            fig.add_trace(go.Scatter(x=df_iv.index, y=df_iv['CurrentIntrinsic'], line=dict(color='gold', width=2), name="Intrinsisch (ohne Wachstum)"), row=1, col=1)
                                
                    if "Liquiditätswert pro Aktie" in overlay_ind:
                        df_iv = calc_rp2_intrinsic(df_chart, ticker_input_chart, rp2iv_params)
                        if not df_iv.empty:
                            fig.add_trace(go.Scatter(x=df_iv.index, y=df_iv['Val_PS'], line=dict(color='gray', width=2), name="Konservative Vermögenssumme"), row=1, col=1)
                            fig.add_trace(go.Scatter(x=df_iv.index, y=df_iv['Val_PSH'], line=dict(color='darkgray', width=2), name="Obere Vermögenssumme"), row=1, col=1)
                            fig.add_trace(go.Scatter(x=df_iv.index, y=df_iv['Val_PSTOT'], line=dict(color='lightblue', width=2), name="Summe mit allen Verb."), row=1, col=1)
                    
                    if "Greenwald Valuation" in overlay_ind:
                        df_gw = calc_greenwald_valuation(df_chart, ticker_input_chart, greenwald_params)
                        if not df_gw.empty:
                            fig.add_trace(go.Scatter(x=df_gw.index, y=df_gw['EPV_PS'], line=dict(color='green', width=2), name="EPV (Ertragskraft)"), row=1, col=1)
                            fig.add_trace(go.Scatter(x=df_gw.index, y=df_gw['AV_PS'], line=dict(color='orange', width=2), name="AV (Reproduktion)"), row=1, col=1)
                            fig.add_trace(go.Scatter(x=df_gw.index, y=df_gw['Buy_Price'], mode='markers', marker=dict(color='blue', size=4), name="Kaufpreis (MoS)"), row=1, col=1)
                            
                            latest_av = df_gw['AV_PS'].dropna().iloc[-1] if not df_gw['AV_PS'].dropna().empty else 0
                            latest_epv = df_gw['EPV_PS'].dropna().iloc[-1] if not df_gw['EPV_PS'].dropna().empty else 0
                            latest_franchise = df_gw['Franchise_Value'].dropna().iloc[-1] if not df_gw['Franchise_Value'].dropna().empty else 0
                            
                            st.markdown("**Greenwald Live-Bewertung (Aktuellstes Quartal):**")
                            mc1, mc2, mc3 = st.columns(3)
                            mc1.metric("AV (Reproduktion) / Aktie", f"${latest_av:.2f}")
                            mc2.metric("EPV (Ertragskraft) / Aktie", f"${latest_epv:.2f}")
                            mc3.metric("Franchise Value (Moat)", f"{latest_franchise * 100:.1f}%", 
                                       delta="Moat Vorhanden" if latest_franchise > 0 else "Kein Moat",
                                       delta_color="normal" if latest_franchise > 0 else "inverse")

                    current_row = 2
                    for ind in sub_ind:
                        if ind == "RSI 14":
                            rsi_vals = calc_rsi(df_chart['Close'], 14)
                            fig.add_trace(go.Scatter(x=df_chart.index, y=rsi_vals, line=dict(color='purple', width=1.5), name="RSI 14"), row=current_row, col=1)
                            fig.add_hline(y=70, line_dash="dot", line_color="red", row=current_row, col=1)
                            fig.add_hline(y=30, line_dash="dot", line_color="green", row=current_row, col=1)
                            
                        elif ind == "RP2 Indikator (SinepTrader)":
                            rp2_vals = calc_rp2_indicator(df_chart, ticker_input_chart)
                            colors = ['#26a69a' if val >= 0 else '#ef5350' for val in rp2_vals]
                            fig.add_trace(go.Bar(x=rp2_vals.index, y=rp2_vals, marker_color=colors, name="RP2"), row=current_row, col=1)
                            fig.add_hline(y=0, line_dash="dot", line_color="gray", row=current_row, col=1)
                            
                        elif ind == "RP2 CF Indikator (SinepTrader)":
                            rp2_cf_vals = calc_rp2_cf_indicator(df_chart, ticker_input_chart)
                            colors = ['#26a69a' if pd.notna(val) and val >= 0 else '#ef5350' for val in rp2_cf_vals]
                            fig.add_trace(go.Bar(x=rp2_cf_vals.index, y=rp2_cf_vals, marker_color=colors, name="RP2 CF"), row=current_row, col=1)
                            fig.add_hline(y=0, line_dash="dot", line_color="gray", row=current_row, col=1)
                            
                        elif ind == "RP2 PEG Indikator (SinepTrader)":
                            rp2_peg_vals = calc_rp2_peg_indicator(df_chart, ticker_input_chart)
                            colors = ['#26a69a' if pd.notna(val) and val >= 0 else '#ef5350' for val in rp2_peg_vals]
                            fig.add_trace(go.Bar(x=rp2_peg_vals.index, y=rp2_peg_vals, marker_color=colors, name="RP2 PEG"), row=current_row, col=1)
                            fig.add_hline(y=0, line_dash="dot", line_color="gray", row=current_row, col=1)
                            
                        elif ind == "RP2 P E (SinepTrader)":
                            df_pe = calc_rp2_pe_indicator(df_chart, ticker_input_chart)
                            if not df_pe.empty:
                                fig.add_trace(go.Scatter(x=df_pe.index, y=df_pe['PE'], line=dict(color='blue', width=2), name="P/E"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_pe.index, y=df_pe['Average'], line=dict(color='gray', width=1.5), name="SMA 300"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_pe.index, y=df_pe['Buy'], line=dict(color='red', width=1, dash='dash'), name="Buy Zone"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_pe.index, y=df_pe['Sell'], line=dict(color='red', width=1, dash='dash'), name="Sell Zone"), row=current_row, col=1)
                                
                        elif ind == "RP2 EV EBITDA (SinepTrader)":
                            df_ev = calc_rp2_ev_ebitda_indicator(df_chart, ticker_input_chart)
                            if not df_ev.empty:
                                fig.add_trace(go.Scatter(x=df_ev.index, y=df_ev['EV_EBITDA'], line=dict(color='blue', width=2), name="EV/EBITDA"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_ev.index, y=df_ev['Average'], line=dict(color='gray', width=1.5), name="SMA 300"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_ev.index, y=df_ev['Buy'], line=dict(color='red', width=1, dash='dash'), name="Buy Zone"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_ev.index, y=df_ev['Sell'], line=dict(color='red', width=1, dash='dash'), name="Sell Zone"), row=current_row, col=1)
                                
                        elif ind == "RP2 EV Sales (SinepTrader)":
                            df_sales = calc_rp2_ev_sales_indicator(df_chart, ticker_input_chart)
                            if not df_sales.empty:
                                fig.add_trace(go.Scatter(x=df_sales.index, y=df_sales['EV_Sales'], line=dict(color='blue', width=2), name="EV/Sales"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_sales.index, y=df_sales['Average'], line=dict(color='gray', width=1.5), name="SMA 300"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_sales.index, y=df_sales['Buy'], line=dict(color='red', width=1, dash='dash'), name="Buy Zone"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_sales.index, y=df_sales['Sell'], line=dict(color='red', width=1, dash='dash'), name="Sell Zone"), row=current_row, col=1)
                                
                        elif ind == "RP2 P FCF (SinepTrader)":
                            df_p_fcf = calc_rp2_p_fcf_indicator(df_chart, ticker_input_chart)
                            if not df_p_fcf.empty:
                                fig.add_trace(go.Scatter(x=df_p_fcf.index, y=df_p_fcf['P_FCF'], line=dict(color='blue', width=2), name="P/FCF"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_p_fcf.index, y=df_p_fcf['Average'], line=dict(color='gray', width=1.5), name="SMA 300"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_p_fcf.index, y=df_p_fcf['Buy'], line=dict(color='red', width=1, dash='dash'), name="Buy Zone"), row=current_row, col=1)
                                fig.add_trace(go.Scatter(x=df_p_fcf.index, y=df_p_fcf['Sell'], line=dict(color='red', width=1, dash='dash'), name="Sell Zone"), row=current_row, col=1)
                        current_row += 1

                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        margin=dict(l=10, r=10, t=30, b=10),
                        height=500 + (num_subcharts * 150),
                        template="plotly_white",
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Keine historischen Kursdaten gefunden.")
            except Exception as e:
                st.error(f"Fehler beim Abrufen der Kursdaten: {e}")
