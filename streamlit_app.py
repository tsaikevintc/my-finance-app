import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# 頁面設定
st.set_page_config(page_title="Insights Asset", layout="wide", initial_sidebar_state="collapsed")

# 注入深色主題 CSS
st.markdown("""
<style>
    /* 全域背景 */
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* 自定義卡片樣式 */
    .metric-card {
        background-color: #161B22;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #30363D;
        text-align: center;
        transition: transform 0.3s;
    }
    .metric-card:hover { transform: translateY(-5px); }
    
    /* 霓虹邊框設定 */
    .card-cyan { border-top: 4px solid #00F2FF; box-shadow: 0px 4px 15px rgba(0, 242, 255, 0.2); }
    .card-pink { border-top: 4px solid #FF007A; box-shadow: 0px 4px 15px rgba(255, 0, 122, 0.2); }
    .card-green { border-top: 4px solid #39FF14; box-shadow: 0px 4px 15px rgba(57, 255, 20, 0.2); }
    
    .metric-label { color: #8B949E; font-size: 14px; margin-bottom: 5px; }
    .metric-value { font-size: 24px; font-weight: bold; color: #FFFFFF; }
    .metric-sub { font-size: 12px; color: #58A6FF; margin-top: 5px; }

    /* Tab 樣式美化 */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: transparent !important;
        border-radius: 0px; border-bottom: 2px solid transparent;
        color: #8B949E;
    }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #FFFFFF !important; color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

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
    with st.spinner('Syncing...'):
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

    # 頂部導航
    st.markdown("<h2 style='text-align: center; color: white;'>Insights</h2>", unsafe_allow_html=True)
    
    # 自定義 Metric 卡片
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""<div class="metric-card card-cyan"><div class="metric-label">總資產 (TWD)</div><div class="metric-value">NT$ {cash_t+inv_t:,.0f}</div><div class="metric-sub">Bank Cash</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card card-pink"><div class="metric-label">投資市值</div><div class="metric-value">NT$ {inv_t:,.0f}</div><div class="metric-sub">Stock Portfolio</div></div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="metric-card card-green"><div class="metric-label">即時匯率</div><div class="metric-value">$ {rate:.2f}</div><div class="metric-sub">USD/TWD</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 階層分頁
    t1, t2, t3 = st.tabs(["資產總覽", "資產明細", "績效分析"])
    
    with t1:
        c_a, c_b = st.columns(2)
        # 圓餅圖顏色調整
        colors = ['#00F2FF', '#7000FF', '#FF007A', '#39FF14']
        f1 = px.pie(values=[cash_t, inv_t], names=['現金', '投資'], hole=0.7, 
                    color_discrete_sequence=colors)
        f1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                         font_color="white", showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        f1.update_traces(textposition='inside', textinfo='percent+label')
        
        c_a.markdown("<h4 style='text-align: center;'>資產分佈</h4>", unsafe_allow_html=True)
        c_a.plotly_chart(f1, use_container_width=True)
        
        f2 = px.pie(i_df, values='市值', names='名稱', hole=0.7, color_discrete_sequence=colors)
        f2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                         font_color="white", showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        c_b.markdown("<h4 style='text-align: center;'>投資組合</h4>", unsafe_allow_html=True)
        c_b.plotly_chart(f2, use_container_width=True)

    with t2:
        st.subheader("🏦 現金儲備")
        st.table(c_df)
        st.subheader("📊 持股清單")
        st.table(i_df[['名稱', '持有股數', '現價', '市值']])

    with t3:
        st.subheader("🚀 績效追蹤")
        # 損益顯示優化
        i_df['損益比'] = (i_df['損益'] / (i_df['買入成本'] * i_df['持有股數']) * 100).round(2)
        st.dataframe(i_df[['名稱', '代號', '買入成本', '現價', '損益', '損益比']].style.applymap(
            lambda v: 'color:#FF4B4B' if v < 0 else 'color:#00FF7F', subset=['損益', '損益比']
        ), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
