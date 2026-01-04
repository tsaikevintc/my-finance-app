import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="AssetPro", layout="wide")

# CSS 美化
st.markdown("""<style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
</style>""", unsafe_allow_html=True)

ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I = "526580417", "1335772092"

@st.cache_data(ttl=300)
def load():
    url = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    df_c = pd.read_csv(f"{url}&gid={G_C}")
    df_i = pd.read_csv(f"{url}&gid={G_I}")
    df_c.columns = df_c.columns.str.strip()
    df_i.columns = df_i.columns.str.strip()
    return df_c, df_i

try:
    c_df, i_df = load()
    with st.spinner('Updating...'):
        rate = yf.Ticker("USDTWD=X").fast_info['last_price']
        tks = i_df['代號'].dropna().unique().tolist()
        pxs = yf.download(tks, period="1d", progress=False)['Close']
        p_map = pxs.iloc[-1].to_dict() if len(tks)>1 else {tks[0]: pxs.iloc[-1]}

    # 計算
    cash_t = sum(r['金額'] * (rate if r['幣別']=='USD' else 1) for _, r in c_df.iterrows())
    i_df['現價'] = i_df['代號'].map(p_map).fillna(i_df['買入成本'])
    i_df['市值'] = i_df['現價'] * i_df['持有股數']
    i_df['損益'] = (i_df['現價'] - i_df['買入成本']) * i_df['持有股數']
    inv_t = sum(r['市值'] * (rate if r['幣別']=='USD' else 1) for _, r in i_df.iterrows())

    # 顯示
    st.title("🛡️ AssetPro 資產管理")
    m1, m2, m3 = st.columns(3)
    m1.metric("總淨資產", f"${cash_t+inv_t:,.0f}")
    m2.metric("投資市值", f"${inv_t:,.0f}")
    m3.metric("美金匯率", f"{rate:.2f}")

    t1, t2, t3 = st.tabs(["📊 總覽", "💵 現金", "📈 投資"])
    with t1:
        c_a, c_b = st.columns(2)
        f1 = px.pie(values=[cash_t, inv_t], names=['現金', '投資'], hole=0.5, title="資產配置")
        c_a.plotly_chart(f1, use_container_width=True)
        f2 = px.pie(i_df, values='市值', names='名稱', hole=0.5, title="投資分佈")
        c_b.plotly_chart(f2, use_container_width=True)
    with t2:
        st.dataframe(c_df, use_container_width=True, hide_index=True)
    with t3:
        st.dataframe(i_df.style.applymap(lambda v: 'color:red' if v<0 else 'color:green', subset=['損益']).format({'損益':'{:+,.0f}'}), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
