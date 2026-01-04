import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="個人資產管理", layout="wide")

# 你的 Google Sheet 資訊
SHEET_ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
GID_CASH = "526580417"
GID_INVEST = "1335772092"

# 建立 CSV 導出連結
def get_csv_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

@st.cache_data(ttl=300) # 每 5 分鐘快取一次
def get_all_data():
    # 讀取數據
    df_cash = pd.read_csv(get_csv_url(GID_CASH))
    df_invest = pd.read_csv(get_csv_url(GID_INVEST))
    
    # 欄位名稱極端清理
    df_cash.columns = [str(c).strip() for c in df_cash.columns]
    df_invest.columns = [str(c).strip() for c in df_invest.columns]
    
    # 確保數值欄位是浮點數
    for col in ['金額', '持有股數', '買入成本']:
        if col in df_cash.columns:
            df_cash[col] = pd.to_numeric(df_cash[col].astype(str).str.replace(',', ''), errors='coerce')
        if col in df_invest.columns:
            df_invest[col] = pd.to_numeric(df_invest[col].astype(str).str.replace(',', ''), errors='coerce')
            
    return df_cash, df_invest

st.title("💰 我的資產管理儀表板")

try:
    cash_df, invest_df = get_all_data()
    
    with st.spinner('連線 Google Sheets 並同步全球市價中...'):
        # 1. 抓取匯率
        try:
            usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
        except:
            usdtwd = 32.5 # 備用匯率
            
        # 2. 抓取股價
        tickers = invest_df['代號'].dropna().unique().tolist()
        if tickers:
            # 下載最新價格
            price_data = yf.download(tickers, period="1d", progress=False)['Close']
            if len(tickers) == 1:
                prices = {tickers[0]: price_data.iloc[-1]}
            else:
                prices = price_data.iloc[-1].to_dict()
        else:
            prices = {}

    # --- 計算現金 ---
    total_cash_twd = 0
    for _, row in cash_df.iterrows():
        amt = row.get('金額', 0)
        curr = str(row.get('幣別', 'TWD')).strip().upper()
        if curr == 'USD':
            total_cash_twd += amt * usdtwd
        else:
            total_cash_twd += amt

    # --- 計算投資 ---
    invest_df['現價'] = invest_df['代號'].map(prices).fillna(invest_df['買入成本'])
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    invest_df['損益'] = (invest_df['現價'] - invest_df['買入成本']) * invest_df['持有股數']
    
    total_invest_twd = 0
    for _, row in invest_df.iterrows():
        mv = row['市值'] if pd.notnull(row['市值']) else 0
        if str(row.get('幣別', 'TWD')).strip().upper() == 'USD':
            total_invest_twd += mv * usdtwd
        else:
            total_invest_twd += mv

    # --- 介面呈現 ---
    c1, c2, c
