import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="資產管理APP", layout="wide")

# 你的 Google Sheet 網址
SHEET_URL = "https://docs.google.com/spreadsheets/d/1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=600) # 每10分鐘快取一次，避免頻繁讀取
def get_data():
    cash_df = pd.read_csv(f"{SHEET_URL}&gid=0") # 現金資產分頁
    invest_df = pd.read_csv(f"{SHEET_URL}&gid=1263595166") # 投資清單分頁
    return cash_df, invest_df

st.title("💰 我的個人資產管理")

try:
    cash_df, invest_df = get_data()
    
    # 取得匯率
    usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
    
    # 計算現金部分
    cash_total_twd = 0
    for _, row in cash_df.iterrows():
        val = row['金額']
        if row['幣別'] == 'USD':
            cash_total_twd += val * usdtwd
        else:
            cash_total_twd += val

    # 取得股價並計算投資
    tickers = invest_df['代號'].tolist()
    prices = yf.download(tickers, period="1d")['Close'].iloc[-1].to_dict()
    
    invest_df['現價'] = invest_df['代號'].map(prices)
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    invest_df['損益'] = (invest_df['現價'] - invest_df['買入成本']) * invest_df['持有股數']
    
    # 總覽指標
    invest_total_twd = 0
    for _, row in invest_df.iterrows():
        if row['幣別'] == 'USD':
            invest_total_twd += row['市值'] * usdtwd
        else:
            invest_total_twd += row['市值']

    c1, c2, c3 = st.columns(3)
    c1.metric("總淨資產 (TWD)", f"{cash_total_twd + invest_total_twd:,.0f}")
    c2.metric("現金/YouTube收益", f"{cash_total_twd:,.0f}")
    c3.metric("美金匯率", f"{usdtwd:.2f}")

    st.subheader("📊 投資損益細節")
    st.dataframe(invest_df, use_container_width=True)

except Exception as e:
    st.error(f"連線失敗，請檢查試算表權限。錯誤: {e}")
