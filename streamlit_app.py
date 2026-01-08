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

# 3. 極簡質感 CSS
st.markdown("""
<style>
    [data-testid="stAppViewContainer"], .stApp { background-color: #050505 !important; }
    .block-container { padding: 1.2rem !important; }

    /* 自定義 HTML 膠囊按鈕 CSS */
    .capsule-group {
        display: flex; overflow-x: auto; white-space: nowrap; gap: 8px;
        padding: 5px 0 15px 0; scrollbar-width: none;
    }
    .capsule-group::-webkit-scrollbar { display: none; }
    
    .capsule-item {
        background: #1A1A1A; color: #888; border: 1px solid #252525;
        padding: 6px 16px; border-radius: 10px; font-size: 13px;
        cursor: pointer; text-decoration: none; font-family: sans-serif;
    }
    .active-capsule {
        background: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
        font-weight: bold;
    }

    .total-title { font-size: 42px; font-weight: 800; color: #FFFFFF !important; letter-spacing: -1.5px; }
    .profit-row { font-size: 13px; color: #555; margin-bottom: 20px; }
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, h_df = fetch_data()
    
    # --- 核心邏輯：使用隱藏的 st.radio 作為狀態機，HTML 膠囊作為門面 ---
    ranges = ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"]
    
    # 這是真正的狀態保存器，但我們不顯示它
    if 'selected_range' not in st.session_state:
        st.session_state.selected_range = "ALL"

    # 4. 計算區間盈虧
    rate = 32.5
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_total = c_df['TWD'].sum() + 829010 

    now = h_df['Date'].max()
    filter_map = {
        "7D": now - timedelta(days=7), "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90), "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365), "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    
    # 5. 渲染標題
    st.markdown(f"<div class='total-title'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)
    
    # 6. HTML 膠囊渲染（無邊框、無白塊、支援毫秒點擊）
    # 我們利用 st.button 的隱形技巧來觸發，或者這裡更簡單地用單一 st.segmented_control 並用 CSS 強制改寫
    # 為了「絕對無白塊」，我決定用 st.columns 配合 st.button，但加入更強的 CSS 來修正間距
    
    cols = st.columns([1,1,1,1,1,1,1,2]) # 加一格空的推開
    for i, r in enumerate(ranges):
        if cols[i].button(r, key=f"btn_{r}"):
            st.session_state.selected_range = r
    
    # --- 數據連動 ---
    filtered_h = h_df[h_df['Date'] >= filter_map[st.session_state.selected_range]]
    diff_period = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    diff_today = t_total - h_df['Total'].iloc[-1]

    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:700;">{"+" if v >= 0 else ""}{v:,.0f}</span>'
    
    st.markdown(f'<div class="profit-row">{fmt(diff_period)} {st.session_state.selected_range}區間盈虧 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 7. 圖表
    fig = go.Figure(go.Scatter(x=filtered_h['Date'], y=filtered_h['Total'], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.02)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 8. 卡片
    st.markdown("<div style='color:#333; font-size:11px; font-weight:800; margin:10px 5px; letter-spacing:1px;'>CASH ASSETS</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        st.markdown(f"""
            <div style="background:#111; border-radius:12px; padding:16px; margin-bottom:12px; border:1px solid #1A1A1A; display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <div style="color:#FFF; font-weight:600; font-size:15px;">{r['子項目']}</div>
                    <div style="color:#555; font-size:11px; margin-top:2px;">{r['大項目']}</div>
                </div>
                <div style="color:#FFF; font-weight:700; font-size:17px;">$ {r['TWD']:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"系統錯誤: {e}")
