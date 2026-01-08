import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據讀取
@st.cache_data(ttl=60)
def fetch_data():
    ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
    G_C, G_I, G_H = "526580417", "1335772092", "857913551"
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    i = pd.read_csv(f"{base}&gid={G_I}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    h['Date'] = pd.to_datetime(h['Date'])
    return c, i, h

# 3. 質感 CSS (徹底封殺白色、強制橫向不換行)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }

    /* 讓 st.pills 在手機端橫向排列且可滑動 */
    div[data-testid="stPills"] {
        display: flex !important;
        flex-direction: row !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        gap: 8px !important;
        background-color: transparent !important;
        padding: 5px 0 !important;
    }
    div[data-testid="stPills"]::-webkit-scrollbar { display: none; } /* 隱藏捲軸 */

    /* 膠囊樣式修正 */
    div[data-testid="stPills"] button {
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        border: 1px solid #30363D !important;
        border-radius: 20px !important;
        padding: 4px 16px !important;
        flex-shrink: 0 !important; /* 防止被擠壓變形 */
    }
    div[data-testid="stPills"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
    }

    /* 文字亮度與佈局 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin: 0; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 12px; }
    .pos { color: #00F2FE !important; font-weight: 600; }
    .neg { color: #FF4D4D !important; font-weight: 600; }
    
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-value { font-size: 16px; font-weight: 700; color: #FFFFFF !important; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # 4. 基礎金額
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_total = c_df['TWD'].sum() + 829010 

    # --- 5. 時間篩選膠囊 ---
    # 放置在頂部，確保橫向滑動
    selected_range = st.pills(
        "Range", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"],
        default="ALL", label_visibility="collapsed"
    )

    # 6. 動態數據篩選邏輯
    now = h_df['Date'].max()
    filter_map = {
        "7D": now - timedelta(days=7),
        "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90),
        "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365),
        "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    
    # 篩選後的歷史數據
    filtered_h = h_df[h_df['Date'] >= filter_map[selected_range]]
    
    # 7. 區間盈虧計算
    # 區間總盈虧 = 當前總值 - 該區間第一筆紀錄
    # 今日盈虧 = 當前總值 - 歷史紀錄最後一筆
    diff_period = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    diff_today = t_total - h_df['Total'].iloc[-1]

    # 8. 渲染標題
    st.markdown(f"<div class='total-title'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)
    
    def fmt(v):
        cl = "pos" if v >= 0 else "neg"
        return f'<span class="{cl}">{" " if v < 0 else "+"}{v:,.0f}</span>'
    
    st.markdown(f"""
        <div class="profit-row">
            {fmt(diff_period)} {selected_range}區間總盈虧 ‧ 今日 {fmt(diff_today)}
        </div>
    """, unsafe_allow_html=True)

    # 渲染連動圖表
    fig = go.Figure(go.Scatter(
        x=filtered_h['Date'], y=filtered_h['Total'], 
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'
    ))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 9. 資產卡片
    def draw_card(title, sub, val):
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; border:1px solid #30363D; display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <div class="card-title">{title}</div>
                    <div style="color:#8B949E; font-size:11px; margin-top:2px;">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='color:#8B949E; font-size:14px; margin:10px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        draw_card(r['子項目'], r['大項目'], r['TWD'])

except Exception as e:
    st.error(f"系統錯誤: {e}")
