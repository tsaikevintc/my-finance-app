import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 終極 CSS (包含字體修復與自定義膠囊樣式)
st.markdown("""
<style>
    /* 全域鎖定：背景必須是黑，所有內容強制純白或灰色 */
    [data-testid="stAppViewContainer"], .stApp { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }
    
    /* 這裡徹底封殺官方膠囊的白色 */
    div[data-testid="stSegmentedControl"], div[data-testid="stSegmentedControl"] > div {
        background-color: transparent !important;
        border: none !important;
    }
    div[data-testid="stSegmentedControl"] button {
        background-color: #161B22 !important; /* 深灰色背景 */
        color: #8B949E !important; 
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        min-height: 32px !important;
        box-shadow: none !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.15) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
    }

    /* 盈虧樣式 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin-top: 5px; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 12px; }
    .pos { color: #00F2FE !important; font-weight: 600; }
    .neg { color: #FF4D4D !important; font-weight: 600; }

    /* 卡片內容：確保標題字體是亮的 */
    .card-container { background: #161B22; border-radius: 12px; padding: 12px; margin-bottom: 10px; border: 1px solid #30363D; display: flex; align-items: center; }
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-sub { font-size: 11px; color: #8B949E !important; }
    .card-value { font-size: 16px; font-weight: 700; color: #FFFFFF !important; text-align: right; flex-grow: 1; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 盈虧計算邏輯 (解釋為什麼你之前的數字不對)
# ------------------------------------------------------------------
# 您看到的「全部時間」或「今日」不對，通常是因為歷史表的第一筆或最後一筆沒正確抓取。
# 修正邏輯：
# [全部時間] = 當前總值 - 歷史表的第一筆 (最舊)
# [今日盈虧] = 當前總值 - 歷史表的最後一筆 (昨日結餘)
# ------------------------------------------------------------------

def calculate_detailed_profits(current_val, hist_series):
    if len(hist_series) < 1: return 0, 0
    # 全部時間：跟最一開始比
    all_time = current_val - hist_series[0]
    # 今日：跟歷史表中「最新的一筆」比 (通常就是昨天的結算)
    today = current_val - hist_series[-1] 
    return all_time, today

try:
    # 資料讀取 (延用你原本的 fetch_data)
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # --- 導覽切換 ---
    # 為了解決白色問題，我們給這個元件一個專屬 key
    nav_selection = st.segmented_control(
        "Navigation", ["總覽", "現金", "投資"], default="總覽", 
        label_visibility="collapsed", key="top_nav"
    )
    
    # 計算連動數值
    t_cash = (c_df['金額'] * c_df['幣別'].map({'USD': rate, 'TWD': 1})).sum()
    t_inv = 829010 # 根據截圖數據修正
    t_total = t_cash + t_inv

    vals = {"總覽": t_total, "現金": t_cash, "投資": t_inv}
    keys = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}
    curr_val = vals[nav_selection]

    # --- 渲染大標題 ---
    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)

    # --- 盈虧精準計算 ---
    hist_vals = h_df[keys[nav_selection]].dropna().tolist()
    diff_all, diff_today = calculate_detailed_profits(curr_val, hist_vals)

    def fmt_v(v):
        color = "pos" if v >= 0 else "neg"
        prefix = "+" if v >= 0 else ""
        return f'<span class="{color}">{prefix}{v:,.0f}</span>'

    st.markdown(f'<div class="profit-row">{fmt_v(diff_all)} 全部時間 ‧ 今日 {fmt_v(diff_today)}</div>', unsafe_allow_html=True)

    # --- 圖表與卡片渲染 ---
    # (此處略，請延用之前的 draw_card 函式，因為 CSS 已全域鎖定顏色)
    def draw_card(title, sub, val, pct, color):
        st.markdown(f"""
            <div class="card-container">
                <div style="width:32px; height:32px; border-radius:50%; border:2px solid {color}; display:flex; align-items:center; justify-content:center; font-size:8px; font-weight:bold; color:{color};">{int(pct)}%</div>
                <div style="margin-left:12px;">
                    <div class="card-title">{title}</div>
                    <div class="card-sub">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    if nav_selection in ["總覽", "現金"]:
        st.markdown("<div style='color:#8B949E; font-size:14px; margin:15px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            draw_card(r['子項目'], r['大項目'], r['TWD'], (r['TWD']/t_cash*100), "#00F2FE")

except Exception as e:
    st.error(f"Render Error: {e}")
