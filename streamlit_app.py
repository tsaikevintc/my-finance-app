import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據讀取與日期解析
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

# 3. 終極 CSS (針對自定義 HTML 膠囊)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1rem !important; }

    /* 隱藏所有官方可能的干擾 */
    div[data-testid="stHorizontalBlock"] { gap: 0 !important; }

    /* 自定義 HTML 膠囊容器 */
    .capsule-wrapper {
        display: flex;
        overflow-x: auto;
        white-space: nowrap;
        gap: 6px; /* 按鈕之間的距離，您可以隨意調整 */
        padding: 5px 0 15px 0;
        scrollbar-width: none;
    }
    .capsule-wrapper::-webkit-scrollbar { display: none; }

    /* 模擬按鈕外觀 */
    .nav-btn {
        background: #1C212B;
        color: #9CA3AF;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 4px 12px;
        font-size: 12px;
        cursor: pointer;
        display: inline-block;
        text-decoration: none;
    }
    .nav-btn:active {
        background: rgba(0, 242, 254, 0.1);
        color: #00F2FE;
        border: 1px solid #00F2FE;
    }

    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin: 0; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 10px; }
    
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, h_df = fetch_data()
    
    # 使用 query_params 或 session_state 來處理篩選 (這版改用 query_params 更穩定)
    query_params = st.query_params
    current_range = query_params.get("range", "ALL")

    # 4. 計算金額
    rate = 32.5
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_total = c_df['TWD'].sum() + 829010 

    # 5. 渲染標題
    now = h_df['Date'].max()
    filter_map = {
        "7D": now - timedelta(days=7), "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90), "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365), "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    filtered_h = h_df[h_df['Date'] >= filter_map[current_range]]

    diff_period = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    diff_today = t_total - h_df['Total'].iloc[-1]

    st.markdown(f"<div class='total-title'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)
    
    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:600;">{"+" if v >= 0 else ""}{v:,.0f}</span>'
    
    st.markdown(f'<div class="profit-row">{fmt(diff_period)} {current_range}區間總盈虧 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 6. 【核心亮點】純 HTML 緊湊膠囊
    # 這裡我們用 HTML 生成連結，點擊後會觸發 URL 變更，Streamlit 會自動刷新畫面
    btns_html = "".join([
        f'<a href="?range={r}" target="_self" class="nav-btn" style="{"border:1px solid #00F2FE; color:#00F2FE; background:rgba(0,242,254,0.1);" if r == current_range else ""}">{r}</a>'
        for r in ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"]
    ])
    st.markdown(f'<div class="capsule-wrapper">{btns_html}</div>', unsafe_allow_html=True)

    # 7. 圖表
    fig = go.Figure(go.Scatter(x=filtered_h['Date'], y=filtered_h['Total'], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 8. 資產列表
    st.markdown("<div style='color:#8B949E; font-size:14px; margin:15px 5px 10px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:10px; border:1px solid #30363D; display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <div style="color:white !important; font-weight:600; font-size:15px;">{r['子項目']}</div>
                    <div style="color:#8B949E; font-size:11px;">{r['大項目']}</div>
                </div>
                <div style="color:white !important; font-weight:700; font-size:16px; text-align:right;">$ {r['TWD']:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"系統錯誤: {e}")
