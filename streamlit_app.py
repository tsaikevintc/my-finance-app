import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="個人資產管理", layout="wide")

# 你的試算表網址
BASE_URL = "https://docs.google.com/spreadsheets/d/1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4/export?format=csv"
GID_CASH = "526580417"
GID_INVEST = "1335772092"

@st.cache_data(ttl=600)
def get_data():
    # 讀取並強制跳過可能的空白列，清理所有隱藏字元
    df_cash = pd.read_csv(f"{BASE_URL}&gid={GID_CASH}")
    df_invest = pd.read_csv(f"{BASE_URL}&gid={GID_INVEST}")
    
    # 強力清理：移除欄位標題中的所有空白與換行符
    df_cash.columns = [str(c).strip() for c in df_cash.columns]
    df_invest.columns = [str(c).strip() for c in df_invest.columns]
    
    return df_cash, df_invest

st.title("💰 我的資產管理儀表板")

try:
    cash_df, invest_df = get_data()
    
    # 獲取匯率與股價
    with st.spinner('同步全球市價中...'):
        # 1. 獲取匯率 (如果 Yahoo 忙碌則預設 32.5)
        try:
            usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
        except:
            usdtwd = 32.5
            st.caption("無法取得即時匯率，暫以 32.5 計算")
        
        # 2. 處理投資清單 (確保有 '代號' 這一欄)
        # 如果欄位名稱不符，嘗試尋找最接近的名稱
        col_map = {c: c for c in invest_df.columns}
        target_col = '代號'
        
        if target_col in invest_df.columns:
            tickers = invest_df[target_col].dropna().unique().tolist()
            if tickers:
                try:
                    # 使用 yfinance 抓取，若失敗則回傳空字典
                    price_data = yf.download(tickers, period="1d", progress=False)['Close']
                    if len(tickers) == 1:
                        prices = {tickers[0]: price_data.iloc[-1]}
                    else:
                        prices = price_data.iloc[-1].to_dict()
                except:
                    prices = {}
            else:
                prices = {}
        else:
            st.error(f"在試算表中找不到『{target_col}』欄位，請檢查標題是否完全一致。")
            st.write("目前的欄位標題有：", list(invest_df.columns))
            st.stop()

    # --- 計算現金 ---
    total_cash_twd = 0
    # 尋找「金額」與「幣別」欄位
    for _, row in cash_df.iterrows():
        try:
            amt = float(row.get('金額', 0))
            curr = str(row.get('幣別', 'TWD')).strip().upper()
            if curr == 'USD':
                total_cash_twd += amt * usdtwd
            else:
                total_cash_twd += amt
        except:
            continue

    # --- 計算投資 ---
    invest_df['現價'] = invest_df['代號'].map(prices).fillna(invest_df['買入成本'])
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    invest_df['損益'] = (invest_df['現價'] - invest_df['買入成本']) * invest_df['持有股數']
    
    total_invest_twd = 0
    for _, row in invest_df.iterrows():
        val = row['市值'] if pd.notnull(row['市值']) else 0
        if str(row.get('幣別', 'TWD')).strip().upper() == 'USD':
            total_invest_twd += val * usdtwd
        else:
            total_invest_twd += val

    # --- 介面呈現 ---
    c1, c2, c3 = st.columns(3)
    c1.metric("總淨資產 (TWD)", f"${total_cash_twd + total_invest_twd:,.0f}")
    c2.metric("現金資產 (含YT)", f"${total_cash_twd:,.0f}")
    c3.metric("美金匯率", f"{usdtwd:.2f}")

    st.divider()
    st.subheader("📊 投資損益細節")
    st.dataframe(invest_df, use_container_width=True)

except Exception as e:
    st.error(f"發生非預期錯誤")
    st.info(f"技術細節: {e}")
