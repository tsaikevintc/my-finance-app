import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="個人資產管理", layout="wide")

# 你的 Google Sheet 資訊
SHEET_ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
GID_CASH = "526580417"
GID_INVEST = "1335772092"

def get_csv_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

@st.cache_data(ttl=300)
def get_all_data():
    df_cash = pd.read_csv(get_csv_url(GID_CASH))
    df_invest = pd.read_csv(get_csv_url(GID_INVEST))
    df_cash.columns = [str(c).strip() for c in df_cash.columns]
    df_invest.columns = [str(c).strip() for c in df_invest.columns]
    
    for col in ['金額', '持有股數', '買入成本']:
        if col in df_cash.columns:
            df_cash[col] = pd.to_numeric(df_cash[col].astype(str).str.replace(',', ''), errors='coerce')
        if col in df_invest.columns:
            df_invest[col] = pd.to_numeric(df_invest[col].astype(str).str.replace(',', ''), errors='coerce')
    return df_cash, df_invest

st.title("💰 我的資產管理儀表板")

try:
    cash_df, invest_df = get_all_data()
    
    with st.spinner('同步全球市價中...'):
        try:
            usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
        except:
            usdtwd = 32.5
            
        tickers = invest_df['代號'].dropna().unique().tolist()
        prices = {}
        if tickers:
            price_data = yf.download(tickers, period="1d", progress=False)['Close']
            if len(tickers) == 1:
                prices = {tickers[0]: price_data.iloc[-1]}
            else:
                prices = price_data.iloc[-1].to_dict()

    # --- 計算邏輯 ---
    total_cash_twd = 0
    for _, row in cash_df.iterrows():
        amt = row.get('金額', 0)
        if row.get('幣別') == 'USD':
            total_cash_twd += amt * usdtwd
        else:
            total_cash_twd += amt

    invest_df['現價'] = invest_df['代號'].map(prices).fillna(invest_df['買入成本'])
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    invest_df['損益'] = (invest_df['現價'] - invest_df['買入成本']) * invest_df['持有股數']
    
    total_invest_twd = 0
    for _, row in invest_df.iterrows():
        mv = row['市值'] if pd.notnull(row['市值']) else 0
        if row.get('幣別') == 'USD':
            total_invest_twd += mv * usdtwd
        else:
            total_invest_twd += mv

    # --- 介面呈現 ---
    total_assets = total_cash_twd + total_invest_twd
    c1, c2, c3 = st.columns(3)
    c1.metric("總淨資產 (TWD)", f"${total_assets:,.0f}")
    c2.metric("現金資產", f"${total_cash_twd:,.0f}")
    c3.metric("美金匯率", f"{usdtwd:.2f}")

    st.divider()

    # --- 圓餅圖分析 ---
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.subheader("📊 資產配置比例")
        pie_data = pd.DataFrame({
            "類別": ["現金", "股票/投資"],
            "金額": [total_cash_twd, total_invest_twd]
        })
        fig = px.pie(pie_data, values='金額', names='類別', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("📈 投資明細")
        st.dataframe(invest_df[['代號', '持有股數', '現價', '損益']], use_container_width=True)

except Exception as e:
    st.error(f"發生錯誤：{e}")
