import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 徹底封殺白色的 CSS
st.markdown("""
<style>
    /* 全域鎖定 */
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }

    /* 隱藏官方 Segmented Control 的所有預設邊框與底色 */
    div[data-testid="stSegmentedControl"] { background: transparent !important; }
    div[data-testid="stSegmentedControl"] button {
        background-color: #161B22 !important; /* 深灰色 */
        color: #8B949E !important; 
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.15) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
    }

    /* 字體色彩鎖定 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin-top: 5px; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 12px; }
    .pos { color: #00F2FE !important; font-weight: 600; }
    .neg { color: #FF4D4D !important; font-weight: 600; }

    /* 卡片字體修復 */
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-sub { font-size: 11px; color: #8B949E !important; }
    .card-value { font-size: 16px; font-weight: 700; color: #FFFFFF !important; text-align: right; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 盈虧計算邏輯 (邏輯重構)
# ------------------------------------------------------------------
# [今日盈虧] 公式修正：
# 許多人誤以為是「今天 - 昨天」，但如果數據還沒更新，會顯示為 0。
# 正確做法：當前資產 - (歷史表中最後一個交易日的數值)
# ------------------------------------------------------------------

def calculate_profits(current_val, history_list):
    if not history_list or len(history_list) == 0:
        return 0, 0
    # 全部時間 = 現在 - 歷史的第一筆
    all_time = current_val - history_list[0]
    # 今日 = 現在 - 歷史中「非今日」的最後一筆 (即昨日收盤)
    today = current_val - history_list[-1]
    return all_time, today

try:
    c_df, i_df, h_df = fetch_data() # 使用您原本的 fetch_data
    rate = 32.5

    # --- 頂部質感膠囊 ---
    nav_selection = st.segmented_control("V", ["總覽", "現金", "投資"], default="總覽", label_visibility="collapsed")
    
    # 計算各項數值
    t_cash = (c_df['金額'] * c_df['幣別'].map({'USD': rate, 'TWD': 1})).sum()
    t_inv = 829010 
    t_total = t_cash + t_inv

    vals = {"總覽": t_total, "現金": t_cash, "投資": t_inv}
    keys = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}
    current_val = vals[nav_selection]

    # 大數字
    st.markdown(f"<div class='total-title'>$ {current_val:,.0f}</div>", unsafe_allow_html=True)

    # 盈虧計算
    hist_vals = h_df[keys[nav_selection]].dropna().tolist()
    diff_all, diff_today = calculate_profits(current_val, hist_vals)

    def fmt(v):
        c = "pos" if v >= 0 else "neg"
        return f'<span class="{c}">{" " if v < 0 else "+"}{v:,.0f}</span>'

    st.markdown(f'<div class="profit-row">{fmt(diff_all)} 全部時間 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # --- 圖表與時間膠囊 ---
    fig = go.Figure(go.Scatter(y=hist_vals, mode='lines', line=dict(color='#00F2FE', width=2.5), fill='tozeroy', fillcolor='rgba(0,242,254,0.03)'))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.segmented_control("R", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"], default="ALL", label_visibility="collapsed")

    # --- 卡片渲染 (文字強制亮白) ---
    def draw_card(title, sub, val, pct, color):
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:12px; margin-bottom:10px; display:flex; align-items:center; border:1px solid #30363D;">
                <div style="width:32px; height:32px; border-radius:50%; border:2px solid {color}; display:flex; align-items:center; justify-content:center; font-size:8px; font-weight:bold; color:{color};">{int(pct)}%</div>
                <div style="flex-grow:1; margin-left:12px;">
                    <div class="card-title">{title}</div>
                    <div class="card-sub">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    # 內容連動
    if nav_selection in ["總覽", "現金"]:
        st.markdown("<div style='color:#8B949E; font-size:14px; margin:15px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            draw_card(r['子項目'], r['大項目'], r['TWD'], (r['TWD']/t_cash*100), "#00F2FE")

except Exception as e:
    st.error(f"Error: {e}")
