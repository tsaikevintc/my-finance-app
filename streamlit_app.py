import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 終極對齊 CSS
st.markdown("""
<style>
    /* 禁止手機左右滑動 */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100vw !important;
    }
    .block-container { padding: 1rem 0.8rem !important; max-width: 100vw !important; overflow: hidden !important; }
    .stApp { background-color: #0B0E14; color: #FFFFFF; font-family: 'Inter', sans-serif; }

    /* 頂部區域容器 */
    .top-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin-top: 10px;
    }
    .total-title { font-size: 34px; font-weight: 700; color: #FFFFFF; }

    /* 針對 Streamlit Segmented Control 的膠囊風改造 */
    div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; }
    
    /* 強制膠囊縮小並並排在大數字右側 */
    div[data-testid="stSegmentedControl"] {
        position: absolute;
        right: 0px;
        top: 25px; /* 根據金額數字高度微調 */
        gap: 4px !important;
    }
    
    /* 膠囊按鈕樣式微縮 */
    div[data-testid="stSegmentedControl"] button {
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 2px 8px !important;
        min-height: 24px !important;
        height: 24px !important;
        font-size: 10px !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #00F2FE !important;
        color: #000 !important;
        font-weight: 700;
    }

    /* 時間軸 (底部 7D, 1M 等) 橫排補丁 */
    .time-wrap [data-testid="stSegmentedControl"] {
        position: relative !important;
        top: 0 !important;
        width: 100% !important;
        justify-content: space-between !important;
    }

    /* 盈虧樣式 */
    .profit-row { font-size: 13px; color: #9CA3AF; margin: -5px 0 15px 2px; }
    .pos { color: #00F2FE; font-weight: 600; }
    
    /* 卡片列表復原 */
    .section-header { font-size: 14px; color: #9CA3AF; margin: 20px 0 10px 5px; }
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
    # 模擬數據
    total_assets, total_cash, total_inv = 2329010, 2247500, 81510
    
    # 頂部佈局：數字渲染
    st.markdown('<div class="top-container">', unsafe_allow_html=True)
    # 我們需要偵測當前選中的值
    if 'view_opt' not in st.session_state: st.session_state.view_opt = '總覽'
    
    curr_val = {'總覽': total_assets, '現金': total_cash, '投資': total_inv}[st.session_state.view_opt]
    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)
    
    # 使用 st.segmented_control 代替按鈕，它在行動端渲染更穩定且不會換行
    st.session_state.view_opt = st.segmented_control(
        label="View Filter",
        options=["總覽", "現金", "投資"],
        default="總覽",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # 盈虧
    st.markdown(f'<div class="profit-row"><span class="pos">+2,314,010</span> 全部時間 ‧ 今日 <span class="pos">+2,247,500</span></div>', unsafe_allow_html=True)

    # 圖表
    fig = go.Figure(go.Scatter(y=[1.1, 1.4, 1.3, 1.6, 1.5, 1.9], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 時間軸 (同樣使用 segmented_control 確保手機橫排不跑位)
    st.markdown('<div class="time-wrap">', unsafe_allow_html=True)
    st.segmented_control(
        label="Time Filter",
        options=["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"],
        default="ALL",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # 資產列表
    st.markdown("<div class='section-header'>● 投資項目</div>", unsafe_allow_html=True)
    
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
    st.error(f"UI Error: {e}")
