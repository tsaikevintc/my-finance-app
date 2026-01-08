import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 核心 CSS：使用絕對定位鎖定按鈕，並徹底禁止換行與滾動
st.markdown("""
<style>
    /* 全域鎖定：禁止任何晃動 */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100vw !important;
    }
    .block-container { padding: 1rem 0.8rem !important; max-width: 100vw !important; overflow: hidden !important; }

    .stApp { background-color: #0B0E14; color: #FFFFFF; font-family: 'Inter', sans-serif; }

    /* 頂部 Header：金額位置固定 */
    .header-box {
        position: relative;
        height: 60px;
        width: 100%;
        display: flex;
        align-items: center;
    }
    .total-title { font-size: 34px; font-weight: 700; color: #FFFFFF; }

    /* 終極對齊：將按鈕群組絕對定位在右上方 */
    .floating-btns {
        position: absolute;
        top: 15px;
        right: 0px;
        z-index: 999;
    }

    /* 強制按鈕容器橫向排開 */
    div[data-testid="column"] {
        width: auto !important;
        flex: unset !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 4px !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        display: flex !important;
    }

    /* 膠囊按鈕微縮樣式 */
    div.stButton > button {
        border-radius: 20px !important;
        height: 22px !important;
        width: 48px !important;
        min-width: 48px !important;
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        font-size: 10px !important;
        padding: 0px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
    }
    div.stButton > button:focus, div.stButton > button:active { 
        background-color: #00F2FE !important; color: #000 !important; 
    }

    /* 時間軸強制橫排補丁 */
    .time-wrap [data-testid="stHorizontalBlock"] {
        margin-top: 10px !important;
        justify-content: space-between !important;
    }
    .time-wrap button { background: transparent !important; width: auto !important; min-width: 32px !important; font-size: 11px !important; border: none !important; }

    /* 盈虧與卡片 */
    .profit-row { font-size: 12px; color: #9CA3AF; margin-top: -10px; margin-bottom: 15px; }
    .pos { color: #00F2FE; font-weight: 600; }
    .custom-card {
        background: #161B22; border-radius: 12px; padding: 12px;
        margin-bottom: 10px; display: flex; align-items: center; border: 1px solid #1F2937;
    }
    .card-info { flex-grow: 1; margin-left: 12px; }
    .card-title { font-size: 14px; font-weight: 600; }
    .card-sub { font-size: 11px; color: #6B7280; }
    .card-value { text-align: right; font-weight: 700; font-size: 15px; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 邏輯與數據渲染
try:
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    total_assets, total_cash, total_inv = 2329010, 2247500, 81510
    curr_val = {'Total': total_assets, 'Cash': total_cash, 'Invest': total_inv}[st.session_state.view]

    # --- 頂部：數字與浮動按鈕 ---
    st.markdown('<div class="header-box">', unsafe_allow_html=True)
    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)
    
    # 使用絕對定位包裹按鈕
    st.markdown('<div class="floating-btns">', unsafe_allow_html=True)
    b_col1, b_col2, b_col3 = st.columns(3)
    if b_col1.button("總覽"): st.session_state.view = 'Total'
    if b_col2.button("現金"): st.session_state.view = 'Cash'
    if b_col3.button("投資"): st.session_state.view = 'Invest'
    st.markdown('</div></div>', unsafe_allow_html=True)

    # --- 盈虧 ---
    st.markdown(f'<div class="profit-row"><span class="pos">+2,035,360</span> 全部時間 ‧ 今日 <span class="pos">+1,112,247</span></div>', unsafe_allow_html=True)

    # --- 圖表 ---
    fig = go.Figure(go.Scatter(y=[1, 1.2, 1.1, 1.5, 1.4, 1.8], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- 時間橫軸 ---
    st.markdown('<div class="time-wrap">', unsafe_allow_html=True)
    t_cols = st.columns(7)
    for i, r in enumerate(['7D', '1M', '3M', '6M', 'YTD', '1Y', 'ALL']):
        t_cols[i].button(r)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 卡片列表 ---
    st.markdown("<div style='font-size:14px; color:#9CA3AF; margin:20px 0 10px 5px;'>● 投資</div>", unsafe_allow_html=True)
    
    def render_row(name, sub, val, pct, color):
        st.markdown(f"""
            <div class="custom-card">
                <div style="width: 32px; height: 32px; border-radius: 50%; border: 2px solid {color}; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold;">{pct}%</div>
                <div class="card-info">
                    <div class="card-title">{name}</div>
                    <div class="card-sub">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    render_row("特斯拉", "美股 ‧ NASDAQ:TSLA", 65000, 79, "#FFD700")
    render_row("蘋果", "美股 ‧ NASDAQ:AAPL", 8125, 9, "#FFD700")

except Exception as e:
    st.error(f"Error: {e}")
