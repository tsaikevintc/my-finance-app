import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="資產管理APP", layout="wide")

# 你的原始網址
BASE_URL = "https://docs.google.com/spreadsheets/d/1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4/export?format=csv"

@st.cache_data(ttl=600)
def get_data():
    # 使用 gid 來區分分頁：0 是第一個分頁，1263595166 是投資清單
    cash_df = pd.read_csv(f"{BASE_URL}&gid=0")
    invest_df = pd.read_csv(f"{BASE_URL}&gid=1263595166")
    
    # 移除欄位名稱前後的空白（防止因為空格導致找不到欄位）
    cash_df.columns = cash_df.columns.str.strip()
    invest_df.columns = invest_df.columns.str.strip()
    
    return cash_df, invest_df

st.title("💰 我的個人資產管理")

try:
    cash_df, invest_df = get_data()
    
    # 取得匯率
    with st.spinner('正在獲取最新匯率與股價...'):
        usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
        
        # 取得投資現價
        ticker_list = invest_df['代號'].unique().tolist()
        # 為了避免 Rate Limit，改用單個下載或簡化請求
        price_data = yf.download(ticker_list, period="1d")['Close']
        
        # 處理單一標的與多個標的返回格式不同的問題
        if len(ticker_list) == 1:
            prices = {ticker_list[0]: price_data.iloc[-1]}
        else:
            prices = price_data.iloc[-1].to_dict()

    # --- 計算現金 ---
    cash_total_twd = 0
    # 假設欄位順序：大項目, 子項目, 幣別, 金額
    for _, row in cash_df.iterrows():
        try:
            val = float(row['金額'])
            if row['幣別'] == 'USD':
                cash_total_twd += val * usdtwd
            else:
                cash_total_twd += val
        except:
            continue

    # --- 計算投資 ---
    invest_df['現價'] = invest_df['代號'].map(prices)
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    invest_df['損益'] = (invest_df['現價'] - invest_df['買入成本']) * invest_df['持有股數']
    
    invest_total_twd = 0
    for _, row in invest_df.iterrows():
        # 如果是美股或加密貨幣(USD)，換算回台幣
        market_val = row['市值'] if pd.notnull(row['市值']) else 0
        if row['幣別'] == 'USD':
            invest_total_twd += market_val * usdtwd
        else:
            invest_total_twd += market_val

    # --- 顯示介面 ---
    c1, c2, c3 = st.columns(3)
    c1.metric("總淨資產 (TWD)", f"{cash_total_twd + invest_total_twd:,.0f}")
    c2.metric("現金資產 (折合TWD)", f"{cash_total_twd:,.0f}")
    c3.metric("美金匯率", f"{usdtwd:.2f}")

    st.subheader("📊 投資清單明細")
    st.dataframe(invest_df, use_container_width=True)

except Exception as e:
    st.error(f"資料處理發生錯誤。")
    st.info(f"技術細節: {e}")
    st.warning("請檢查 Google 試算表的分頁名稱與欄位名稱（代號、金額、幣別）是否與程式碼一致。")
