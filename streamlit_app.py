import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# 1. 頁面設定
st.set_page_config(page_title="Asset Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 全域鎖定深色與文字亮度
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1rem !important; }
    .t-val { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin: 0; }
    .p-row { font-size: 13px; color: #8B949E !important; margin-bottom: 15px; }
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
    for df in [c, h]: df.columns = df.columns.str.strip()
    h['Date'] = pd.to_datetime(h['Date'].str.replace('上午', 'AM').str.replace('下午', 'PM'), errors='coerce', format='mixed')
    h = h.dropna(subset=['Date']).sort_values('Date')
    return c, h

try:
    c_df, h_df = fetch_data()
    t_total = (c_df['金額'] * c_df['幣別'].apply(lambda x: 32.5 if x=='USD' else 1)).sum() + 829010

    # 3. 核心：處理膠囊選擇 (使用 URL 參數以換取最穩定的狀態保存)
    selected_range = st.query_params.get("range", "ALL")

    # 4. 手寫 HTML/CSS 膠囊：這是唯一能保證「橫向不換行」且「無白色」的方法
    # 我們完全跳過 st.pills 和 st.columns
    capsule_items = ["7D", "1M", "3M", "6M", "YTD", "ALL"]
    capsule_html = f"""
    <div style="display: flex; overflow-x: auto; gap: 8px; white-space: nowrap; padding: 5px 0 15px 0; -webkit-overflow-scrolling: touch; scrollbar-width: none;">
        {" ".join([f'''
            <a href="/?range={r}" target="_self" style="
                text-decoration: none;
                display: inline-block;
                padding: 6px 16px;
                background: {"rgba(0, 242, 254, 0.15)" if selected_range == r else "#1C212B"};
                color: {"#00F2FE" if selected_range == r else "#9CA3AF"};
                border: 1px solid {"#00F2FE" if selected_range == r else "#30363D"};
                border-radius: 20px;
                font-size: 13px;
                font-family: sans-serif;
                font-weight: {"700" if selected_range == r else "500"};
            ">{r}</a>
        ''' for r in capsule_items])}
    </div>
    <style> div::-webkit-scrollbar {{ display: none; }} </style>
    """
    
    # 5. 渲染標題
    st.markdown(f"<div class='t-val'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)
    
    # 6. 計算與顯示盈虧
    now = h_df['Date'].max()
    f_map = {"7D": 7, "1M": 30, "3M": 90, "6M": 180, "YTD": (now - datetime(now.year, 1, 1)).days, "ALL": 9999}
    filtered_h = h_df[h_df['Date'] >= (now - timedelta(days=f_map.get(selected_range, 9999)))]
    
    diff_p = t_total - filtered_h['Total'].iloc[0]
    diff_t = t_total - h_df['Total'].iloc[-1]
    
    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:700;">{"+" if v >= 0 else ""}{v:,.0f}</span>'
    
    st.markdown(f'<div class="p-row">{fmt(diff_p)} {selected_range}區間總盈虧 ‧ 今日 {fmt(diff_t)}</div>', unsafe_allow_html=True)

    # 7. 嵌入膠囊 (放置在盈虧下方，圖表上方)
    components.html(capsule_html, height=50)

    # 8. 圖表
    fig = go.Figure(go.Scatter(x=filtered_h['Date'], y=filtered_h['Total'], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 9. 卡片區 (維持亮白文字)
    st.markdown("<div style='color:#8B949E; font-size:14px; margin:10px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        twd = r['金額'] * (32.5 if r['幣別']=='USD' else 1)
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; border:1px solid #30363D; display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <div style="color:#FFFFFF !important; font-weight:600; font-size:15px;">{r['子項目']}</div>
                    <div style="color:#8B949E; font-size:11px; margin-top:2px;">{r['大項目']}</div>
                </div>
                <div style="color:#FFFFFF !important; font-weight:700; font-size:16px;">$ {twd:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error: {e}")
