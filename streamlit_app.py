import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="個人資產管理", layout="wide")

# 基礎網址
BASE_URL = "https://docs.google.com/spreadsheets/d/1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4/export?format=csv"

# 填入你剛才提供的 gid
GID_CASH = "526580417"
GID_INVEST = "1335772092"

@st.cache_data(ttl=600)
def get_data():
    # 讀取兩個分頁
    df_cash = pd.read_csv(f"{BASE_URL}&gid={GID_CASH}")
    df_invest = pd.read_csv(f"{BASE_URL}&gid={GID_INVEST}")
    
    # 清理欄位名稱（去除空格）
    df_cash.columns = df_cash.columns.str.strip()
    df_invest.columns = df_invest.columns.str.strip()
    
    return df_cash, df_invest

st.title("💰 我的資產管理儀表板")

try:
    cash_df, invest_df = get_data()
    
    # 獲取匯率與股價
    with st.spinner('同步全球市價中...'):
        # 1. 匯率
        usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
        
        # 2. 投資現價
        tickers = invest_df['代號'].dropna().unique().tolist()
        if tickers:
            price_data = yf.download(tickers, period="1d", progress=False)['Close']
            # 處理多標的與單一標的回傳格式不同
            if len(tickers) == 1:
                prices = {tickers[0]: price_data.iloc[-1]}
            else:
                prices = price_data.iloc[-1].to_dict()
        else:
            prices = {}

    # --- 計算現金 ---
    total_cash_twd = 0
    for _, row in cash_df.iterrows():
        try:
            amt = float(row['金額'])
            if row['幣別'] == 'USD':
                total_cash_twd += amt * usdtwd
            else:
                total_cash_twd += amt
        except:
            continue

    # --- 計算投資 ---
    invest_df['現價'] = invest_df['代號'].map(prices)
    # 若抓不到現價（如加密貨幣代號不對），先用買入成本替代避免報錯
    invest_df['現價'] = invest_df['現價'].fillna(invest_df['買入成本'])
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    invest_df['損益'] = (invest_df['現價'] - invest_df['買入成本']) * invest_df['持有股數']
    
    total_invest_twd = 0
    for _, row in invest_df.iterrows():
        val = row['市值'] if pd.notnull(row['市值']) else 0
        if row['幣別'] == 'USD':
            total_invest_twd += val * usdtwd
        else:
            total_invest_twd += val

    # --- 介面呈現 ---
    col1, col2, col3 = st.columns(3)
    col1.metric("總淨資產 (TWD)", f"${total_cash_twd + total_invest_twd:,.0f}")
    col2.metric("現金資產", f"${total_cash_twd:,.0f}")
    col3.metric("目前美金匯率", f"{usdtwd:.2f}")

    st.divider()
    
    st.subheader("📊 投資清單詳細損益")
    # 美化表格顯示
    st.dataframe(invest_df.style.format({
        '持有股數': '{:,.2f}',
        '買入成本': '{:,.2f}',
        '現價': '{:,.2f}',
        '市值': '{:,.0f}',
        '損益': '{:+,.0f}'
    }), use_
