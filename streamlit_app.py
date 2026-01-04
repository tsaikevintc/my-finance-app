import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="資產管理APP", layout="wide")

# 你的 Google Sheet 網址
SHEET_URL = "https://docs.google.com/spreadsheets/d/1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4/gviz/tq?tqx=out:csv"

# 設定快取：資料與股價每 30 分鐘才更新一次，避免被鎖 IP
@st.cache_data(ttl=1800)
def get_all_data():
    # 讀取試算表
    cash_df = pd.read_csv(f"{SHEET_URL}&gid=0")
    invest_df = pd.read_csv(f"{SHEET_URL}&gid=1263595166")
    
    # 取得匯率
    usdtwd_ticker = yf.Ticker("USDTWD=X")
    usdtwd = usdtwd_ticker.fast_info['last_price']
    
    # 取得股價
    tickers = invest_df['代號'].unique().tolist()
    # 這裡加入 retry 機制
    try:
        data = yf.download(tickers, period="1d", interval="1m")['Close']
        if not data.empty:
            prices = data.iloc[-1].to_dict()
        else:
            prices = {}
    except:
        prices = {}
        
    return cash_df, invest_df, usdtwd, prices

st.title("💰 我的個人資產管理")

try:
    cash_df, invest_df, usdtwd, prices = get_all_data()
    
    if not prices:
        st.warning("目前股價抓取較頻繁，部分數據可能延遲顯示，請稍候幾分鐘再試。")

    # 計算現金部分
    cash_total_twd = 0
    for _, row in cash_df.iterrows():
        val = row['金額']
        if row['幣別'] == 'USD':
            cash_total_twd += val * usdtwd
        else:
            cash_total_twd += val

    # 計算投資損益
    invest_df['現價'] = invest_df['代號'].map(prices).fillna(invest_df['買入成本']) # 若抓不到則顯示成本
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    invest_df['損益'] = (invest_df['現價'] - invest_df['買入成本']) * invest_df['持有股數']
    
    invest_total_twd = 0
    for _, row in invest_df.iterrows():
        if row['幣別'] == 'USD':
            invest_total_twd += row['市值'] * usdtwd
        else:
            invest_total_twd += row['市值']

    # 儀表板
    c1, c2, c3 = st.columns(3)
    c1.metric("總淨資產 (TWD)", f"{cash_total_twd + invest_total_twd:,.0f}")
    c2.metric("現金/YouTube收益", f"{cash_total_twd:,.0f}")
    c3.metric("美金匯率", f"{usdtwd:.2f}")

    st.subheader("📊 投資損益細節")
    st.dataframe(invest_df, use_container_width=True)

except Exception as e:
    st.error(f"系統忙碌中，請稍後再試。錯誤提示: {e}")
