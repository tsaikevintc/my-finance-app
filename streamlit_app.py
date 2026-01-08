import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據讀取 (含日期格式修復)
@st.cache_data(ttl=60)
def fetch_data():
    ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
    G_C, G_I, G_H = "526580417", "1335772092", "857913551"
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, h]: df.columns = df.columns.str.strip()
    # 處理中文字眼日期
    h['Date'] = pd.to_datetime(h['Date'].str.replace('上午', 'AM').str.replace('下午', 'PM'), errors='coerce', format='mixed')
    h = h.dropna(subset=['Date']).sort_values('Date')
    return c, h

# 3. 終極 CSS (針對按鈕進行膠囊化改裝，徹底消滅白色)
st.markdown("""
<style>
    /* 全域背景 */
    [data-testid="stAppViewContainer"], .stApp { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }

    /* 關鍵：強制橫向佈局且不換行 */
    [data-testid="column"] { 
        min-width: fit-content !important; 
        flex: 1 1 auto !important;
    }
    div[data-testid="stHorizontalBlock"] {
        overflow-x: auto !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        padding-bottom: 10px;
    }
    div[data-testid="stHorizontalBlock"]::-webkit-scrollbar { display: none; }

    /* 按鈕膠囊化：取代 st.pills 以躲避白色背景 */
    div.stButton > button {
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        border: 1px solid #30363D !important;
        border-radius: 20px !important;
        padding: 4px 14px !important;
        font-size: 12px !important;
        height: auto !important;
        width: 100% !important;
        white-space: nowrap !important;
    }
    
    /* 模擬選中狀態 (利用按鈕 Focus 或手動邏輯) */
    div.stButton > button:focus {
        border: 1px solid #00F2FE !important;
        color: #00F2FE !important;
        background-color: rgba(0, 242, 254, 0.1) !important;
    }

    /* 隱藏官方標籤 */
    #MainMenu, header, footer { visibility: hidden; }
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, h_df = fetch_data()
    
    # 初始化 Session State
    if 'range' not in st.session_state:
        st.session_state.range = "ALL"

    # 4. 金額計算
    rate = 32.5
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_total = c_df['TWD'].sum() + 829010 

    # 5. 自定義橫向膠囊 (使用 columns + buttons)
    ranges = ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"]
    cols = st.columns(len(ranges))
    for i, r in enumerate(ranges):
        if cols[i].button(r, key=f"btn_{r}"):
            st.session_state.range = r

    # 6. 數據過濾
    now = h_df['Date'].max()
    filter_map = {
        "7D": now - timedelta(days=7), "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90), "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365), "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    filtered_h = h_df[h_df['Date'] >= filter_map[st.session_state.range]]

    # 7. 顯示區間總盈虧
    diff_period = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    diff_today = t_total - h_df['Total'].iloc[-1]

    st.markdown(f"<div class='total-title'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)
    
    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:600;">{"+" if v >= 0 else ""}{v:,.0f}</span>'
    
    st.markdown(f'<div class="profit-row">{fmt(diff_period)} {st.session_state.range}區間總盈虧 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 8. 圖表
    fig = go.Figure(go.Scatter(x=filtered_h['Date'], y=filtered_h['Total'], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 9. 資產卡片
    st.markdown("<div style='color:#8B949E; font-size:14px; margin:20px 5px 10px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; border:1px solid #30363D; display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <div style="color:white; font-weight:600;">{r['子項目']}</div>
                    <div style="color:#8B949E; font-size:11px;">{r['大項目']}</div>
                </div>
                <div style="color:white; font-weight:700;">$ {r['TWD']:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"系統錯誤: {e}")
