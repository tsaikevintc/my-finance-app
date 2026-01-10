import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定與快取
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

@st.cache_data(ttl=600) # 延長快取時間至 10 分鐘，減少頻繁讀取試算表
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

# 2. 徹底解決白色的 CSS (針對新版 Pills 的深度覆蓋)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1rem !important; }

    /* 封殺 Pills 的白色背景與強制橫向 */
    div[data-testid="stPills"] {
        background-color: transparent !important;
        display: flex !important;
        flex-direction: row !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        gap: 8px !important;
        padding: 5px 0 !important;
    }
    div[data-testid="stPills"]::-webkit-scrollbar { display: none; }

    div[data-testid="stPills"] button {
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        border: 1px solid #30363D !important;
        border-radius: 20px !important;
        padding: 4px 16px !important;
        flex-shrink: 0 !important;
    }

    div[data-testid="stPills"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
    }

    /* 文字亮度 */
    .t-val { font-size: 38px; font-weight: 700; color: white; }
    .p-row { font-size: 13px; color: #8B949E; margin-bottom: 10px; }
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 定義 Fragment (局部更新區塊)
# 這個裝飾器能讓「點擊膠囊」只更新圖表跟盈虧，不重新跑整個頁面，速度提升 5 倍以上
@st.fragment
def render_dashboard(c_df, h_df):
    rate = 32.5
    t_total = (c_df['金額'] * c_df['幣別'].apply(lambda x: rate if x=='USD' else 1)).sum() + 829010
    
    # 頂部總額
    st.markdown(f"<div class='t-val'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)

    # 膠囊切換 (不觸發全頁刷新)
    selected_range = st.pills(
        "Range", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"],
        default="ALL", label_visibility="collapsed"
    )

    # 數據篩選
    now = h_df['Date'].max()
    f_map = {
        "7D": now - timedelta(days=7), "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90), "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365), "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    filtered_h = h_df[h_df['Date'] >= f_map[selected_range]]

    # 盈虧計算
    diff_p = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    diff_t = t_total - h_df['Total'].iloc[-1]
    
    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:700;">{"+" if v >= 0 else ""}{v:,.0f}</span>'
    
    st.markdown(f'<div class="p-row">{fmt(diff_p)} {selected_range}區間總盈虧 ‧ 今日 {fmt(diff_t)}</div>', unsafe_allow_html=True)

    # 圖表 (簡化 Plotly 以提升渲染速度)
    fig = go.Figure(go.Scatter(
        x=filtered_h['Date'], y=filtered_h['Total'], 
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'
    ))
    fig.update_layout(
        height=180, margin=dict(l=0,r=0,t=0,b=0), 
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
        xaxis=dict(visible=False), yaxis=dict(visible=False)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 4. 主程式執行
try:
    c_df, h_df = fetch_data()
    
    # 執行局部更新區塊
    render_dashboard(c_df, h_df)

    # 靜態卡片區塊 (不常變動，放在 Fragment 之外)
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
    st.error(f"Error: {e}")
    
