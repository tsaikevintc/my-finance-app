import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="AssetPro", layout="wide")

# 樣式優化
st.markdown("""<style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
</style>""", unsafe_allow_html=True)

S_ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_CASH, G_INV = "526580417", "1335772092"

@st.cache_data(ttl=300)
def load_data():
    base = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv"
    df_c = pd.read_csv(f"{base}&gid={G_CASH}")
    df_i = pd.read_csv(f"{base}&gid={G_INV}")
    df_c.columns = df_c.columns.str.strip()
    df_i.columns = df_i.columns.str.strip()
    return df_c, df_i

try:
    c_df, i_df = load_data()
    with st.spinner('Updating...'):
        rate = yf.Ticker("USDTWD=X").fast_info['last_price']
        tkrs = i_df['代號'].dropna().unique().tolist()
        px_raw = yf.download(tkrs, period="1d", progress=False)['Close']
        prices = px_raw.iloc[-1].to_dict() if len(tkrs)>1 else {tkrs[0]: px_raw.iloc[-1]}

    # 計算
    c_twd = sum(r['金額'] * (rate if r['幣別']=='USD' else 1) for _, r in c_df.iterrows())
    i_df['現價'] = i_df['代號'].map(prices).fillna(i_df['買入成本'])
    i_df['市值'] = i_df['現價'] * i_df['持有股數']
    i_df['損益'] = (i_df['現價'] - i_df['買入成本']) * i_df['持有股數']
    i_twd = sum(r['市值'] * (rate if r['幣別']=='USD' else 1) for _, r in i_df.iterrows())

    # 介面
    st.title("🛡️ AssetPro 資產管理")
    m1, m2, m3 = st.columns(3)
    m1.metric("總淨資產", f"${c_twd+i_twd:,.0f}")
    m2.metric("投資市值", f"${i_twd:,.0f}")
    m3.metric("美金匯率", f"{rate:.2f}")

    t1, t2, t3 = st.tabs(["📊 總覽", "💵 現金", "📈 投資"])
    with t1:
        col_a, col_b = st.columns(2)
        fig1 = px.pie(values=[c_twd, i_twd], names=['現金', '投資'], hole=0.5, title="資產配置")
        col_a.plotly_chart(fig
