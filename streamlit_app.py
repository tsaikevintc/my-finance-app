import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據解析修復
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

# 3. 核心 CSS：徹底封鎖官方樣式干擾
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1rem !important; }

    /* 隱藏所有官方可能產生白色的元件 */
    div[data-testid="stPills"], div[data-testid="stHorizontalBlock"], .stButton { display: none !important; }

    /* HTML 橫向捲動容器 */
    .capsule-wrapper {
        display: flex;
        overflow-x: auto;
        white-space: nowrap;
        gap: 8px;
        padding: 5px 0 20px 0;
        scrollbar-width: none;
    }
    .capsule-wrapper::-webkit-scrollbar { display: none; }

    /* 膠囊按鈕樣式 */
    .cap {
        display: inline-block;
        padding: 6px 18px;
        background: #1C212B;
        color: #9CA3AF;
        border: 1px solid #30363D;
        border-radius: 20px;
        font-size: 13px;
        text-decoration: none;
        transition: 0.2s;
    }
    .cap-active {
        background: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
        font-weight: 700;
    }

    /* 文字質感 */
    .t-val { font-size: 38px; font-weight: 700; color: white; margin-top: 5px; }
    .p-row { font-size: 13px; color: #8B949E; margin-bottom: 15px; }
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, h_df = fetch_data()
    
    # 透過 URL 參數記憶選擇的區間，避免點擊刷新後跑掉
    query_params = st.query_params
    current_r = query_params.get("range", "ALL")

    # 4. 金額計算
    t_total = (c_df['金額'] * c_df['幣別'].apply(lambda x: 32.5 if x=='USD' else 1)).sum() + 829010

    # 5. 手寫 HTML 膠囊 (解決排版跑掉與白色問題)
    ranges = ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"]
    cap_html = '<div class="capsule-wrapper">'
    for r in ranges:
        active_class = "cap-active" if current_r == r else ""
        # 這裡利用 href 直接改變 URL 參數，達成點擊切換
        cap_html += f'<a href="/?range={r}" target="_self" class="cap {active_class}">{r}</a>'
    cap_html += '</div>'
    st.markdown(cap_html, unsafe_allow_html=True)

    # 6. 動態篩選
    now = h_df['Date'].max()
    f_map = {
        "7D": now - timedelta(days=7), "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90), "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365), "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    filtered_h = h_df[h_df['Date'] >= f_map[current_r]]

    # 7. 渲染數據
    diff_p = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    diff_t = t_total - h_df['Total'].iloc[-1]
    
    st.markdown(f"<div class='t-val'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)
    
    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:700;">{"+" if v >= 0 else ""}{v:,.0f}</span>'
    
    st.markdown(f'<div class="p-row">{fmt(diff_p)} {current_r}區間總盈虧 ‧ 今日 {fmt(diff_t)}</div>', unsafe_allow_html=True)

    # 8. 圖表
    fig = go.Figure(go.Scatter(x=filtered_h['Date'], y=filtered_h['Total'], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 9. 資產卡片
    st.markdown("<div style='color:#8B949E; font-size:14px; margin:20px 5px 10px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        twd = r['金額'] * (32.5 if r['幣別']=='USD' else 1)
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; border:1px solid #30363D; display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <div style="color:white; font-weight:600;">{r['子項目']}</div>
                    <div style="color:#8B949E; font-size:11px;">{r['大項目']}</div>
                </div>
                <div style="color:white; font-weight:700;">$ {twd:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"系統錯誤: {e}")
