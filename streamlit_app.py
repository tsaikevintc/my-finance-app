import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 深度客製化 CSS：解決手機端對齊與滾動問題
st.markdown("""
<style>
    /* 核心：禁止任何左右晃動 */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100vw !important;
    }
    .block-container { padding: 1rem 0.8rem !important; max-width: 100vw !important; overflow: hidden !important; }

    /* 背景與字體 */
    .stApp { background-color: #0B0E14; color: #FFFFFF; font-family: 'Inter', sans-serif; }

    /* 頂部 Header：金額與按鈕平行容器 */
    .header-wrapper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        height: 50px;
        margin-bottom: 5px;
    }
    .total-title { font-size: 32px; font-weight: 700; color: #FFFFFF; }

    /* 強制橫向膠囊容器 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: flex-end !important;
        align-items: center !important;
        gap: 5px !important;
        margin-top: -52px !important; /* 關鍵：將按鈕向上拉至金額旁 */
    }

    /* 膠囊按鈕微調 */
    div.stButton > button {
        border-radius: 20px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        height: 22px !important;
        width: 48px !important;
        min-width: 48px !important;
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        font-size: 10px !important;
        padding: 0px !important;
    }
    div.stButton > button:focus { 
        background-color: #00F2FE !important; 
        color: #000 !important; 
        border: none !important;
    }

    /* 時間軸強制橫排 */
    .time-bar-wrap [data-testid="stHorizontalBlock"] {
        margin-top: 0px !important;
        justify-content: space-between !important;
    }
    .time-bar-wrap button { background: transparent !important; width: auto !important; min-width: 35px !important; border: none !important; font-size: 11px !important; }

    /* 盈虧樣式 */
    .profit-row { font-size: 13px; color: #9CA3AF; margin-top: 0px; margin-bottom: 10px; }
    .pos { color: #00F2FE; font-weight: 600; }

    /* 下方卡片復原 */
    .section-header { font-size: 14px; font-weight: 600; color: #9CA3AF; margin: 20px 0 10px 5px; }
    .custom-card {
        background: #161B22; border-radius: 12px; padding: 12px;
        margin-bottom: 10px; display: flex; align-items: center; border: 1px solid #1F2937;
    }
    .card-info { flex-grow: 1; margin-left: 12px; }
    .card-title { font-size: 14px; font-weight: 600; }
    .card-sub { font-size: 11px; color: #6B7280; }
    .card-value { text-align: right; font-weight: 700; font-size: 15px; }

    /* 隱藏 Streamlit 裝飾 */
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 資料與邏輯 (模擬你的資料來源)
try:
    # 模擬金額
    total_assets, total_cash, total_inv = 2329010, 2247500, 81510
    
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    curr_val = {'Total': total_assets, 'Cash': total_cash, 'Invest': total_inv}[st.session_state.view]

    # --- 渲染頂部：數字與按鈕並排 ---
    # 1. 顯示數字
    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)
    
    # 2. 顯示按鈕 (透過負 margin 強制拉回同一水平線)
    _, btn_col = st.columns([1, 1.3])
    with btn_col:
        b1, b2, b3 = st.columns(3)
        if b1.button("總覽"): st.session_state.view = 'Total'
        if b2.button("現金"): st.session_state.view = 'Cash'
        if b3.button("投資"): st.session_state.view = 'Invest'

    # --- 渲染盈虧 ---
    st.markdown(f"""
        <div class="profit-row">
            <span class="pos">+2,314,010</span> 全部時間 ‧ 
            今日 <span class="pos">+2,247,500</span>
        </div>
    """, unsafe_allow_html=True)

    # --- 渲染圖表 ---
    fig = go.Figure(go.Scatter(y=[10, 15, 13, 17, 22, 20, 25], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- 渲染時間軸 (強制橫排) ---
    st.markdown('<div class="time-bar-wrap">', unsafe_allow_html=True)
    t_cols = st.columns(7)
    ranges = ['7D', '1M', '3M', '6M', 'YTD', '1Y', 'ALL']
    for i, r in enumerate(ranges):
        t_cols[i].button(r)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 渲染卡片列表 (依照你的截圖風格復原) ---
    st.markdown("<div class='section-header'>● 投資</div>", unsafe_allow_html=True)
    
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

    render_row("台積電", "台股 ‧ TPE:2330", 1000, 1, "#FFD700")
    render_row("元大台灣50", "台股 ‧ TPE:0050", 300, 0, "#FFD700")
    render_row("特斯拉", "美股 ‧ NASDAQ:TSLA", 65000, 79, "#FFD700")

except Exception as e:
    st.error(f"Error: {e}")
