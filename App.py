import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

st.set_page_config(page_title="RP2 Analysis", page_icon="📈", layout="wide")

# App Header / Logo styling
st.markdown("""
    <div style='display: flex; align-items: center; gap: 15px; margin-bottom: 20px;'>
        <div style='background: linear-gradient(135deg, #26a69a 0%, #00796b 100%); padding: 12px; border-radius: 12px; color: white; font-size: 28px;'>📈</div>
        <div>
            <h1 style='margin: 0; font-size: 32px;'>RP2 Analysis</h1>
            <p style='margin: 0; color: gray; font-size: 14px;'>Professional Fundamental & Valuation Suite</p>
        </div>
    </div>
""", unsafe_allow_html=True)

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
            stock = yf.Ticker(t)
            info = stock.info
            if 'marketCap' not in info or info['marketCap'] is None:
                continue
               
            # Quick estimation or extraction for screener
            roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else np.nan
            marge = info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else np.nan
            kgv = info.get("trailingPE", np.nan)
            
            # Approximate RP2 for screening if possible, or fallback to ROE/Margin proxy
            approx_rp2 = (roe * 0.8) - 10 if pd.notna(roe) else np.nan
                
            data_list.append({
                "Ticker": t,
                "Name": info.get("shortName", t),
                "Land": info.get("country", "Unbekannt"),
                "M.Cap (Mrd $)": info.get("marketCap", 0) / 1e9,
                "KGV": kgv,
                "KBV": info.get("priceToBook", np.nan),
                "Marge (%)": marge,
                "ROE (%)": roe,
                "RP2 Power (%)": approx_rp2,
                "Div. Rendite (%)": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
            })
        except:
            continue
            
    df = pd.DataFrame(data_list)
    return df

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

    ev_sales_vals = np.where(revenue_merged > 0, ev / revenue
