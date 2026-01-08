import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Wealth Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據讀取
@st.cache_data(ttl=60)
def fetch_data():
    ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
    G_C, G_H = "526580417", "857913551"
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, h]: df.columns = df.columns.str.strip()
    h['Date'] = pd.to_datetime(h['Date'].str.replace('上午', 'AM').str.replace('下午', 'PM'), errors='coerce', format='mixed')
    h = h.dropna(subset=['Date']).sort_values('Date')
    return c, h

# 3. 終極 CSS (針對白色區塊的深度封鎖)
st.markdown("""
<style>
    /* 全域極致黑背景 */
    [data-testid="stAppViewContainer"], .stApp { background-color: #050505 !important; }
    .block-container { padding: 1.2rem 1.2rem !important; }

    /* --- 徹底封殺 st.pills 的白色區塊 (對抗行動端底座) --- */
    div[data-testid="stPills"], 
    div[data-testid="stPills"] > div,
    [data-testid="stPills"] fieldset {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        display: flex !important;
        flex-direction: row !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        gap: 6px !important;
        padding: 0 !important;
    }
    
    /* 隱藏捲軸 */
    div[data-testid="stPills"]::-webkit-scrollbar { display: none; }

    /* 膠囊按鈕：低調灰底 */
    div[data-testid="stPills"] button {
        background-color: #1A1A1A !important;
        color: #888888 !important;
        border: 1px solid #252525 !important;
        border-radius: 8px !important;
        padding: 4px 14px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        flex-shrink: 0 !important;
    }

    /* 選中狀態：電氣青與柔和光效 */
    div[data-testid="stPills"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
        font-weight: 600 !important;
    }

    /* 數值美化 */
    .total-title { font-size: 42px; font-weight: 800; color: #FFFFFF !important; letter-spacing: -1.5px; margin-bottom: -5px; }
    .profit-row { font-size: 13px; color: #555555 !important; margin-bottom: 20px; }
    
    /* 卡片與標題 */
    .asset-card {
        background: #111111;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #1A1A1A;
        display: flex;
        align-items: center;
    }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, h_df = fetch_data()
    rate = 32.5

    # 4. 計算金額
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_total = c_df['TWD'].sum() + 829010 

    # 5. 標題與金額
    st.markdown(f"<div class='total-title'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)

    # 6. 橫向膠囊 (確保快速反應)
    selected_range = st.pills(
        "Range", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"],
        default="ALL", label_visibility="collapsed"
    )

    # 7. 數據動態連動
    now = h_df['Date'].max()
    filter_map = {
        "7D": now - timedelta(days=7), "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90), "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365), "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    filtered_h = h_df[h_df['Date'] >= filter_map[selected_range]]
    
    diff_period = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    diff_today = t_total - h_df['Total'].iloc[-1]

    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:700;">{"+" if v >= 0 else ""}{v:,.0f}</span>'
    
    st.markdown(f'<div class="profit-row">{fmt(diff_period)} {selected_range}區間盈虧 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 8. 圖表
    fig = go.Figure(go.Scatter(
        x=filtered_h['Date'], y=filtered_h['Total'], 
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0,242,254,0.02)'
    ))
    fig.update_layout(height=170, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 9. 資產卡片
    st.markdown("<div style='color:#333333; font-size:11px; font-weight:800; margin:10px 5px; letter-spacing:1px;'>CASH ASSETS</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        st.markdown(f"""
            <div class="asset-card">
                <div style="flex-grow:1;">
                    <div style="color:#FFFFFF; font-weight:600; font-size:15px;">{r['子項目']}</div>
                    <div style="color:#555555; font-size:11px; margin-top:2px;">{r['大項目']}</div>
                </div>
                <div style="color:#FFFFFF; font-weight:700; font-size:17px;">$ {r['TWD']:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"系統錯誤: {e}")
