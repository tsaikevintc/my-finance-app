import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# 1. 頁面設定與配色
st.set_page_config(page_title="AssetPro | 個人資產管理", layout="wide")

# 注入自定義 CSS 提升美感
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { border: none !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 你的 Google Sheet 資訊
SHEET_ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
GID_CASH = "526580417"
GID_INVEST = "1335772092"

@st.cache_data(ttl=300)
def get_all_data():
    base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df_cash = pd.read_csv(f"{base}&gid={GID_CASH}")
    df_invest = pd.read_csv(f"{base}&gid={GID_INVEST}")
    df_cash.columns = [str(c).strip() for c in df_cash.columns]
    df_invest.columns = [str(c).strip() for c in df_invest.columns]
    return df_cash, df_invest

try:
    cash_df, invest_df = get_all_data()
    
    # --- 資料處理與市價抓取 ---
    with st.spinner('同步全球市價中...'):
        usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
        tickers = invest_df['代號'].dropna().unique().tolist()
        price_data = yf.download(tickers, period="1d", progress=False)['Close']
        prices = price_data.iloc[-1].to_dict() if len(tickers) > 1 else {tickers[0]: price_data.iloc[-1]}

    # 計算總額
    total_cash_twd = sum([row['金額'] * (usdtwd if row['幣別'] == 'USD' else 1) for _, row in cash_df.iterrows()])
    invest_df['現價'] = invest_df['代號'].map(prices).fillna(invest_df['買入成本'])
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    invest_df['損益'] = (invest_df['現價'] - invest_df['買入成本']) * invest_df['持有股數']
    total_invest_twd = sum([row['市值'] * (usdtwd if row['幣別'] == 'USD' else 1) for _, row in invest_df.iterrows()])
    total_assets = total_cash_twd + total_invest_twd

    # --- 介面開始 ---
    st.title("🛡️ AssetPro 資產管理系統")
    
    # 第一層：大指標 (Top Metrics)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總淨資產 (TWD)", f"${total_assets:,.0f}")
    col2.metric("現金資產", f"${total_cash_twd:,.0f}")
    col3.metric("投資市值", f"${total_invest_twd:,.0f}")
    col4.metric("即時美金匯率", f"{usdtwd:.2f}")

    st.divider()

    # 第二層：分頁階層式管理 (Tabs)
    tab1, tab2, tab3 = st.tabs(["📊 資產配置總覽", "💵 現金資產明細", "📈 投資組合分析"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("資產分佈比率")
            pie_data = pd.DataFrame({"類別": ["現金", "投資"], "金額": [total_cash_twd, total_invest_twd]})
            fig = px.pie(pie_data, values='金額', names='類別', hole=0.5, color_discrete_sequence=['#00CC96', '#636EFA'])
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("投資標的佔比")
            invest_pie = px.pie(invest_df, values='市值', names='名稱', hole=0.5)
            st.plotly_chart(invest_pie, use_container_width=True)

    with tab2:
        st.subheader("各帳戶餘
