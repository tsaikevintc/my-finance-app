import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 核心樣式：鎖定全黑，移除所有官方干擾
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }
    
    /* 這裡使用 Streamlit 官方新功能：自定義按鈕樣式覆蓋 */
    .stButton > button {
        background-color: #1C212B !important;
        border: 1px solid #30363D !important;
        color: #9CA3AF !important;
        border-radius: 20px !important;
        width: 100% !important;
        height: 32px !important;
    }
    .stButton > button:active, .stButton > button:focus {
        border-color: #00F2FE !important;
        color: #00F2FE !important;
        background-color: rgba(0, 242, 254, 0.1) !important;
    }
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def fetch_data():
    ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
    G_C, G_H = "526580417", "857913551"
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    h['Date'] = pd.to_datetime(h['Date'].str.replace('上午', 'AM').str.replace('下午', 'PM'), errors='coerce', format='mixed')
    h = h.dropna(subset=['Date']).sort_values('Date')
    return c, h

try:
    c_df, h_df = fetch_data()
    t_total = (c_df['金額'] * c_df['幣別'].apply(lambda x: 32.5 if x=='USD' else 1)).sum() + 829010

    # 使用 session_state 記憶狀態，這是反應速度最快的做法
    if "range" not in st.session_state:
        st.session_state.range = "ALL"

    # --- 頂部顯示區 ---
    st.markdown(f"<div style='font-size:38px; font-weight:700; color:white;'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)

    # --- 關鍵：橫向按鈕組 (棄用 Columns 以免手機排隊) ---
    # 利用 Markdown 寫入一個帶有滑動功能的 DIV，內嵌 Streamlit 原生 Button
    ranges = ["7D", "1M", "3M", "6M", "YTD", "ALL"]
    
    # 這裡使用 st.columns 的極簡化布局，並強制其不換行
    cols = st.columns(len(ranges))
    for i, r in enumerate(ranges):
        if cols[i].button(r, key=f"r_{r}"):
            st.session_state.range = r
            st.rerun() # 立即刷新 fragment

    # --- 數據運算與繪圖 ---
    now = h_df['Date'].max()
    f_map = {"7D": 7, "1M": 30, "3M": 90, "6M": 180, "YTD": (now - datetime(now.year, 1, 1)).days, "ALL": 9999}
    filtered_h = h_df[h_df['Date'] >= (now - timedelta(days=f_map[st.session_state.range]))]

    diff_p = t_total - filtered_h['Total'].iloc[0]
    diff_t = t_total - h_df['Total'].iloc[-1]

    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:700;">{"+" if v >= 0 else ""}{v:,.0f}</span>'

    st.markdown(f'<div style="color:#8B949E; font-size:13px;">{fmt(diff_p)} {st.session_state.range}區間總盈虧 ‧ 今日 {fmt(diff_t)}</div>', unsafe_allow_html=True)

    fig = go.Figure(go.Scatter(x=filtered_h['Date'], y=filtered_h['Total'], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 卡片區
    for _, r in c_df.iterrows():
        twd = r['金額'] * (32.5 if r['幣別']=='USD' else 1)
        st.markdown(f"""<div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; border:1px solid #30363D; display:flex; align-items:center;"><div style="flex-grow:1;"><div style="color:white; font-weight:600;">{r['子項目']}</div><div style="color:#8B949E; font-size:11px;">{r['大項目']}</div></div><div style="color:white; font-weight:700;">$ {twd:,.0f}</div></div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error: {e}")
