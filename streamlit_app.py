import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 終極 CSS 修復：解決白色色塊問題
st.markdown("""
<style>
    /* 移除滾動條與限制寬度 */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100vw !important;
        background-color: #0B0E14;
    }
    .block-container { padding: 1rem 1rem !important; }

    /* 修復 Segmented Control 白色色塊：強制背景與文字 */
    div[data-testid="stSegmentedControl"] { background-color: transparent !important; }
    
    div[data-testid="stSegmentedControl"] button {
        background-color: #1C212B !important; /* 強制深色背景 */
        color: #FFFFFF !important; /* 強制白色文字 */
        border: none !important;
        border-radius: 20px !important;
        min-height: 24px !important;
        height: 24px !important;
        font-size: 11px !important;
        opacity: 1 !important;
    }
    
    /* 選中狀態：電氣青背景 + 黑色文字 */
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #00F2FE !important;
        color: #000000 !important;
        box-shadow: none !important;
    }

    /* 佈局樣式 */
    .total-title { font-size: 36px; font-weight: 700; color: #FFFFFF; margin: 5px 0 0 2px; }
    .profit-row { font-size: 12px; color: #9CA3AF; margin-left: 2px; margin-bottom: 12px; line-height: 1.5; }
    .pos { color: #00F2FE; font-weight: 600; }
    .neg { color: #FF4D4D; font-weight: 600; }

    /* 卡片設計 */
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

# 3. 資料加載
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def fetch_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c, i, h = pd.read_csv(f"{base}&gid={G_C}"), pd.read_csv(f"{base}&gid={G_I}"), pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # --- 頂部導覽 ---
    nav_selection = st.segmented_control(
        "Nav", ["總覽", "現金", "投資"], default="總覽", label_visibility="collapsed"
    )
    
    # 計算即時金額
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_cash = c_df['TWD'].sum()
    t_inv = 829010 # 依截圖更新
    t_total = t_cash + t_inv

    view_data = {"總覽": t_total, "現金": t_cash, "投資": t_inv}
    view_key = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}[nav_selection]
    
    # 顯示金額
    st.markdown(f"<div class='total-title'>$ {view_data[nav_selection]:,.0f}</div>", unsafe_allow_html=True)

    # --- 盈虧計算：全部時間 & 今日 ---
    h_df['Date'] = pd.to_datetime(h_df['Date'], errors='coerce')
    h_df = h_df.sort_values('Date')
    current_val = view_data[nav_selection]
    
    hist_series = h_df[view_key].dropna().values
    diff_all = current_val - hist_series[0] if len(hist_series) > 0 else 0
    diff_today = current_val - hist_series[-1] if len(hist_series) > 0 else 0

    def format_diff(val):
        color = "pos" if val >= 0 else "neg"
        prefix = "+" if val >= 0 else ""
        return f'<span class="{color}">{prefix}{val:,.0f}</span>'

    st.markdown(f"""
        <div class="profit-row">
            {format_diff(diff_all)} 全部時間 ‧ 今日 {format_diff(diff_today)}
        </div>
    """, unsafe_allow_html=True)

    # --- 圖表 ---
    fig = go.Figure(go.Scatter(
        x=h_df['Date'], y=h_df[view_key], 
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'
    ))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- 時間軸 ---
    st.segmented_control(
        "Range", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"], default="ALL", label_visibility="collapsed"
    )

    # --- 卡片列表 ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    def draw_card(title, sub, val, pct, color):
        st.markdown(f"""
            <div class="custom-card">
                <div style="width: 32px; height: 32px; border-radius: 50%; border: 2px solid {color}; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold;">{int(pct)}%</div>
                <div class="card-info">
                    <div class="card-title">{title}</div>
                    <div class="card-sub">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    if nav_selection in ["總覽", "現金"]:
        st.markdown("<div class='section-header'>● 現金資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            draw_card(r['子項目'], r['大項目'], r['TWD'], (r['TWD']/t_cash*100), "#00F2FE")

    if nav_selection in ["總覽", "投資"]:
        st.markdown("<div class='section-header'>● 投資項目</div>", unsafe_allow_html=True)
        for _, r in i_df.iterrows():
            m_val = r['持有股數'] * r['買入成本'] * (rate if r['幣別']=='USD' else 1)
            draw_card(r['名稱'], f"{r['類別']} ‧ {r['代號']}", m_val, (m_val/t_inv*100 if t_inv>0 else 0), "#FFD700")

except Exception as e:
    st.error(f"Error: {e}")
