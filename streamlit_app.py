import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 終極質感 CSS：強制修正白色塊與卡片亮度
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0B0E14 !important;
        overflow-x: hidden !important;
    }
    .block-container { padding: 1.2rem 1rem !important; }

    /* --- 質感膠囊配色 (徹底解決白色塊) --- */
    div[data-testid="stSegmentedControl"] { background: transparent !important; }
    
    div[data-testid="stSegmentedControl"] button {
        background-color: #1C212B !important; 
        color: #9CA3AF !important; 
        border: 1px solid #2D333B !important;
        border-radius: 10px !important;
        height: 30px !important;
        font-size: 11px !important;
        box-shadow: none !important;
    }

    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.1) !important; 
        color: #00F2FE !important; 
        border: 1px solid #00F2FE !important;
        font-weight: 700 !important;
    }

    /* --- 字體顏色修正：確保卡片文字清晰 --- */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin-top: 5px; }
    .profit-row { font-size: 13px; color: #9CA3AF !important; margin-bottom: 12px; }
    .pos { color: #00F2FE !important; }
    .neg { color: #FF4D4D !important; }

    .section-header { font-size: 14px; color: #9CA3AF; margin: 25px 0 10px 5px; font-weight: 600; }
    
    .custom-card {
        background: #161B22; border-radius: 14px; padding: 14px;
        margin-bottom: 12px; display: flex; align-items: center; border: 1px solid #1F2937;
    }
    
    .card-info { flex-grow: 1; margin-left: 15px; }
    
    /* 核心文字強制純白 */
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-sub { font-size: 12px; color: #8B949E !important; }
    .card-value { text-align: right; font-weight: 700; font-size: 16px; color: #FFFFFF !important; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 資料讀取函式 (補回被漏掉的部分)
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def fetch_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    i = pd.read_csv(f"{base}&gid={G_I}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    # 去除欄位名稱空格
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

# 4. 主程式邏輯
try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # --- 頂部導覽 ---
    nav_selection = st.segmented_control("Nav", ["總覽", "現金", "投資"], default="總覽", label_visibility="collapsed")
    
    # 計算即時金額 (匯率轉換)
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_cash = c_df['TWD'].sum()
    t_inv = 829010 # 固定數值或根據 i_df 計算
    t_total = t_cash + t_inv

    vals = {"總覽": t_total, "現金": t_cash, "投資": t_inv}
    keys = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}
    current_val = vals[nav_selection]
    
    # 大金額
    st.markdown(f"<div class='total-title'>$ {current_val:,.0f}</div>", unsafe_allow_html=True)

    # --- 盈虧計算說明 ---
    h_df['Date'] = pd.to_datetime(h_df['Date'], errors='coerce')
    h_df = h_df.sort_values('Date')
    history = h_df[keys[nav_selection]].dropna().values
    
    if len(history) > 0:
        # 全部時間 = 當前總額 - 歷史紀錄第一天
        diff_all = current_val - history[0]
        # 今日盈虧 = 當前總額 - 歷史紀錄最後一天 (昨日收盤)
        diff_today = current_val - history[-1]
    else:
        diff_all = diff_today = 0

    def fmt(v):
        color = "pos" if v >= 0 else "neg"
        return f'<span class="{color}">{" " if v<0 else "+"}{v:,.0f}</span>'

    st.markdown(f'<div class="profit-row">{fmt(diff_all)} 全部時間 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # --- 圖表 ---
    fig = go.Figure(go.Scatter(
        y=h_df[keys[nav_selection]], mode='lines', 
        line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'
    ))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- 時間軸 ---
    st.segmented_control("Range", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"], default="ALL", label_visibility="collapsed")

    # --- 卡片渲染 ---
    def draw_card(title, sub, val, pct, color):
        st.markdown(f"""
            <div class="custom-card">
                <div style="width: 34px; height: 34px; border-radius: 50%; border: 2px solid {color}; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; color: {color};">{int(pct)}%</div>
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
    st.error(f"UI Error: {e}")
