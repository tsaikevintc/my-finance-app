import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

# 1. 頁面設定
st.set_page_config(page_title="Asset Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 進階 CSS (優化圓餅圖標與佈局)
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* 圓餅百分比圖標：外圈由 conic-gradient 繪製進度 */
    .pie-icon-container {
        display: flex; align-items: center; justify-content: center;
        width: 42px; height: 42px; min-width: 42px;
        border-radius: 50%; position: relative;
        margin-right: 15px; font-size: 10px;
    }
    .pie-icon-inner {
        position: absolute; width: 34px; height: 34px;
        background-color: #161B22; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: #FFFFFF; font-weight: bold;
    }
    
    /* 卡片佈局 */
    .custom-card {
        background-color: #161B22; border-radius: 16px;
        padding: 12px 16px; margin-bottom: 10px;
        display: flex; align-items: center;
        border: 1px solid #1F2937;
    }
    .card-info { flex-grow: 1; overflow: hidden; }
    .card-title { font-size: 15px; font-weight: 600; color: #F3F4F6; }
    .card-sub { font-size: 11px; color: #9CA3AF; }
    .card-value { text-align: right; font-weight: 700; font-size: 16px; color: #F3F4F6; }

    /* 按鈕樣式 */
    .stButton > button {
        border-radius: 20px; border: 1px solid #374151;
        background-color: #1F2937; color: #9CA3AF;
        font-size: 13px; height: 35px;
    }
    .stButton > button:hover { border-color: #60A5FA; color: white; }
    
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 模擬歷史數據
@st.cache_data
def get_history():
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30)
    return pd.DataFrame({
        "date": dates,
        "Total": np.cumsum(np.random.randn(30) * 5000) + 1200000,
        "Cash": np.cumsum(np.random.randn(30) * 1000) + 400000,
        "Invest": np.cumsum(np.random.randn(30) * 4000) + 800000
    })

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
    # 預防性檢查：確保數值欄位正確
    c_df['金額'] = pd.to_numeric(c_df['金額'], errors='coerce').fillna(0)
    i_df['持有股數'] = pd.to_numeric(i_df['持有股數'], errors='coerce').fillna(0)
    
    rate = yf.Ticker("USDTWD=X").fast_info['last_price']
    
    # 計算資產
    c_df['TWD'] = c_df.apply(lambda r: r['金額'] * (rate if r.get('幣別')=='USD' else 1), axis=1)
    t_cash = c_df['TWD'].sum()
    
    tks = i_df['代號'].dropna().unique().tolist()
    prices = yf.download(tks, period="1d", progress=False)['Close'].iloc[-1].to_dict() if tks else {}
    i_df['市值TWD'] = i_df.apply(lambda r: (prices.get(r['代號'], r['買入成本'])*r['持有股數']) * (rate if r.get('幣別')=='USD' else 1), axis=1)
    t_inv = i_df['市值TWD'].sum()
    
    total = t_cash + t_inv

    # --- UI 頂部：切換視圖 ---
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    if b1.button("✨ 淨資產", use_container_width=True): st.session_state.view = 'Total'
    if b2.button("💵 流動資金", use_container_width=True): st.session_state.view = 'Cash'
    if b3.button("📈 投資組合", use_container_width=True): st.session_state.view = 'Invest'

    # --- 折線圖 ---
    h_df = get_history()
    v_conf = {
        'Total': ('Total', '#60A5FA', '總淨資產'),
        'Cash': ('Cash', '#34D399', '流動資金'),
        'Invest': ('Invest', '#F472B6', '投資組合')
    }
    key, color, label = v_conf[st.session_state.view]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h_df['date'], y=h_df[key], mode='lines', 
                             line=dict(color=color, width=3), fill='tozeroy',
                             fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)'))
    fig.update_layout(height=220, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', 
                      plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, color='#4B5563'), 
                      yaxis=dict(showgrid=False, visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    current_display_val = total if key=='Total' else (t_cash if key=='Cash' else t_inv)
    st.markdown(f"<h1 style='text-align:center; margin-top:-20px;'>$ {current_display_val:,.0f}</h1>", unsafe_allow_html=True)

    # --- 自定義卡片函數 ---
    def render_item(name, sub, val, pct, color):
        # 建立圓餅背景 CSS
        pie_bg = f"conic-gradient({color} {pct*3.6}deg, #374151 0deg)"
        st.markdown(f"""
        <div class="custom-card">
            <div class="pie-icon-container" style="background: {pie_bg};">
                <div class="pie-icon-inner">{int(pct)}%</div>
            </div>
            <div class="card-info">
                <div class="card-title">{name}</div>
                <div class="card-sub">{sub}</div>
            </div>
            <div class="card-value">$ {val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 列表區域 ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state.view in ['Total', 'Cash']:
        st.write("🏦 資金明細")
        for _, r in c_df.iterrows():
            # 安全讀取『附註』，若無則顯示幣別
            sub_text = r.get('附註', r.get('幣別', ''))
            render_item(r['大項目'], sub_text, r['TWD'], (r['TWD']/t_cash*100 if t_cash>0 else 0), "#34D399")

    if st.session_state.view in ['Total', 'Invest']:
        st.write("🚀 投資表現")
        i_sorted = i_df.sort_values('市值TWD', ascending=False)
        for _, r in i_sorted.iterrows():
            render_item(r['名稱'], r['代號'], r['市值TWD'], (r['市值TWD']/t_inv*100 if t_inv>0 else 0), "#60A5FA")

except Exception as e:
    st.error(f"系統運行錯誤: {e}")
    st.info("請檢查試算表欄位名稱是否包含：大項目、金額、幣別、名稱、代號、持有股數")
