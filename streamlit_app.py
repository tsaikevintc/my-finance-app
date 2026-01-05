import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

# 1. 頁面設定
st.set_page_config(page_title="Asset Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 進階 CSS：環狀百分比圖標與浮動按鈕樣式
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    
    /* 圓餅百分比圖標樣式 */
    .pie-icon-container {
        display: flex; align-items: center; justify-content: center;
        width: 45px; height: 45px; min-width: 45px;
        border-radius: 50%; position: relative;
        margin-right: 15px; font-size: 10px; font-weight: bold;
    }
    .pie-icon-inner {
        position: absolute; width: 35px; height: 35px;
        background-color: #161B22; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
    }
    
    /* 卡片佈局優化 */
    .custom-card {
        background-color: #161B22; border-radius: 15px;
        padding: 15px; margin-bottom: 12px;
        display: flex; align-items: center; /* 垂直居中 */
        border: 1px solid #30363D;
    }
    .card-info { flex-grow: 1; }
    .card-title { font-size: 16px; font-weight: 500; }
    .card-sub { font-size: 12px; color: #8B949E; }
    .card-value { text-align: right; font-family: 'Inter', sans-serif; font-weight: bold; }

    /* 切換按鈕樣式 */
    .stButton > button {
        border-radius: 20px; border: 1px solid #30363D;
        background-color: #161B22; color: #8B949E;
        padding: 5px 20px; transition: 0.3s;
    }
    .stButton > button:hover { border-color: #58A6FF; color: white; }
</style>
""", unsafe_allow_html=True)

# 模擬歷史數據 (實際上應存於資料庫或試算表)
@st.cache_data
def get_history():
    dates = pd.date_range(start="2025-01-01", periods=30)
    return pd.DataFrame({
        "date": dates,
        "Total": np.cumsum(np.random.randn(30) * 10000) + 1000000,
        "Cash": np.cumsum(np.random.randn(30) * 2000) + 300000,
        "Invest": np.cumsum(np.random.randn(30) * 8000) + 700000
    })

# 初始化 Session State
if 'view' not in st.session_state: st.session_state.view = 'Total'

# 讀取試算表資料
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I = "526580417", "1335772092"

@st.cache_data(ttl=60)
def load_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    df_c = pd.read_csv(f"{base}&gid={G_C}")
    df_i = pd.read_csv(f"{base}&gid={G_I}")
    df_c.columns = df_c.columns.str.strip()
    df_i.columns = df_i.columns.str.strip()
    return df_c, df_i

try:
    c_df, i_df = load_data()
    rate = yf.Ticker("USDTWD=X").fast_info['last_price']
    
    # 數據計算
    c_df['TWD'] = c_df.apply(lambda r: r['金額'] * (rate if r['幣別']=='USD' else 1), axis=1)
    t_cash = c_df['TWD'].sum()
    
    # 抓取投資現價 (僅示範)
    tks = i_df['代號'].dropna().unique().tolist()
    prices = yf.download(tks, period="1d", progress=False)['Close'].iloc[-1].to_dict()
    i_df['市值TWD'] = i_df.apply(lambda r: (prices.get(r['代號'], r['買入成本'])*r['持有股數']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_inv = i_df['市值TWD'].sum()
    
    total = t_cash + t_inv

    # --- UI 頂部：切換按鈕 ---
    st.markdown("<h3 style='text-align: center;'>Insights</h3>", unsafe_allow_html=True)
    btn_col = st.columns([1,1,1])
    if btn_col[0].button("✨ 淨資產", use_container_width=True): st.session_state.view = 'Total'
    if btn_col[1].button("💵 流動資金", use_container_width=True): st.session_state.view = 'Cash'
    if btn_col[2].button("📈 投資組合", use_container_width=True): st.session_state.view = 'Invest'

    # --- 折線圖區域 ---
    hist_df = get_history()
    view_map = {'Total': ('Total', '#58A6FF', '總淨資產'), 'Cash': ('Cash', '#39FF14', '流動資金'), 'Invest': ('Invest', '#FF007A', '投資組合')}
    key, color, label = view_map[st.session_state.view]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df[key], mode='lines', 
                             line=dict(color=color, width=3), fill='tozeroy',
                             fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)'))
    fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', 
                      plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown(f"<h1 style='text-align: center;'>$ {total if key=='Total' else (t_cash if key=='Cash' else t_inv):,.0f}</h1>", unsafe_allow_html=True)

    # --- 下方卡片區域：帶圓餅百分比 ---
    def render_card(name, sub, val, pct, color):
        st.markdown(f"""
        <div class="custom-card">
            <div class="pie-icon-container" style="background: conic-gradient({color} {pct*3.6}deg, #30363D 0deg);">
                <div class="pie-icon-inner">{int(pct)}%</div>
            </div>
            <div class="card-info">
                <div class="card-title">{name}</div>
                <div class="card-sub">{sub}</div>
            </div>
            <div class="card-value">$ {val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state.view == 'Cash' or st.session_state.view == 'Total':
        st.subheader("🏦 資金明細")
        for _, r in c_df.iterrows():
            render_card(r['大項目'], r['附註'], r['TWD'], (r['TWD']/t_cash*100), "#39FF14")

    if st.session_state.view == 'Invest' or st.session_state.view == 'Total':
        st.subheader("🚀 投資表現")
        for _, r in i_df.iterrows():
            render_card(r['名稱'], r['代號'], r['市值TWD'], (r['市值TWD']/t_inv*100), "#58A6FF")

except Exception as e:
    st.error(f"Error: {e}")
