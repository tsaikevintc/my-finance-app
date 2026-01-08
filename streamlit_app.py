import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 終極質感 CSS：強制移除白底，改為「深灰/電氣青」配色
st.markdown("""
<style>
    /* 1. 膠囊整體背景與邊框 */
    div[data-testid="stSegmentedControl"] { 
        background: transparent !important; 
    }
    
    /* 未選中狀態：深灰色、灰色字、無背景色塊 */
    div[data-testid="stSegmentedControl"] button {
        background-color: #1C212B !important; 
        color: #9CA3AF !important; 
        border: 1px solid #2D333B !important;
        border-radius: 10px !important;
        height: 30px !important;
        font-size: 11px !important;
        box-shadow: none !important;
        margin-right: 4px !important;
    }

    /* 選中狀態：電氣青邊框、青色字、微弱發光 */
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.1) !important; 
        color: #00F2FE !important; 
        border: 1px solid #00F2FE !important;
        font-weight: 700 !important;
    }

    /* 2. 字體顏色修復：確保標題與卡片數值為亮白色 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin-top: 5px; }
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-value { font-size: 16px; font-weight: 700; color: #FFFFFF !important; }
    .card-sub { font-size: 12px; color: #8B949E !important; }
    
    .profit-row { font-size: 13px; color: #9CA3AF !important; margin-bottom: 10px; }
    .pos { color: #00F2FE !important; }
    .neg { color: #FF4D4D !important; }

    /* 移除 Streamlit 預設裝飾 */
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 盈虧計算邏輯說明
# ---------------------------------------------------------
# [全部時間盈虧] = 當前資產總額 - 歷史紀錄中「第一筆」的資產總額
# [今日盈虧] = 當前資產總額 - 歷史紀錄中「最後一筆(昨日)」的資產總額
# ---------------------------------------------------------

try:
    # 假設從試算表讀取的數據
    c_df, i_df, h_df = fetch_data() # 請保留你之前的讀取函式
    rate = 32.5

    # 頂部導覽
    nav_selection = st.segmented_control("V", ["總覽", "現金", "投資"], default="總覽", label_visibility="collapsed")
    
    # 計算即時金額
    t_cash = (c_df['金額'] * c_df['幣別'].map({'USD': rate, 'TWD': 1})).sum()
    t_inv = 829010 
    t_total = t_cash + t_inv

    vals = {"總覽": t_total, "現金": t_cash, "投資": t_inv}
    keys = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}
    current_val = vals[nav_selection]
    
    # 渲染金額
    st.markdown(f"<div class='total-title'>$ {current_val:,.0f}</div>", unsafe_allow_html=True)

    # 盈虧核心計算
    history = h_df[keys[nav_selection]].dropna().values
    if len(history) > 0:
        # 1. 全部時間：當前減去歷史起點
        diff_all = current_val - history[0]
        # 2. 今日：當前減去最近一筆歷史紀錄（通常是昨日收盤）
        diff_today = current_val - history[-1]
    else:
        diff_all = diff_today = 0

    def fmt(v): return f'<span class="{"pos" if v>=0 else "neg"}">{" " if v<0 else "+"}{v:,.0f}</span>'
    st.markdown(f'<div class="profit-row">{fmt(diff_all)} 全部時間 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 圖表與卡片部分... (保持先前邏輯，但 CSS 會自動修正顏色)

except Exception as e:
    st.write(f"Error: {e}")
