import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Asset Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 精緻化 CSS - 模擬截圖中的懸浮感與文字排列
st.markdown("""
<style>
    .stApp { background-color: #F8F9FB; color: #1A1C1E; }
    
    /* 總額與盈虧文字排列 */
    .total-title { font-size: 32px; font-weight: 800; margin-bottom: 2px; color: #1A1C1E; }
    .profit-all { color: #E57373; font-size: 14px; font-weight: 600; }
    .profit-today { color: #4CAF50; font-size: 14px; font-weight: 600; margin-top: 2px; }

    /* 懸浮按鈕樣式 */
    .stButton > button {
        border-radius: 12px; border: none; height: 28px;
        background-color: #E9ECEF; color: #495057; font-size: 11px;
        padding: 0px 10px; transition: 0.3s;
    }
    .stButton > button:hover { background-color: #DEE2E6; }
    div[data-testid="stHorizontalBlock"] button { box-shadow: 0px 2px 5px rgba(0,0,0,0.05); }

    /* 隱藏預設元件 */
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 資料載入
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def load_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    df_c = pd.read_csv(f"{base}&gid={G_C}")
    df_i = pd.read_csv(f"{base}&gid={G_I}")
    df_h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [df_c, df_i, df_h]: df.columns = df.columns.str.strip()
    return df_c, df_i, df_h

try:
    c_df, i_df, h_df = load_data()
    # 匯率解析與計算 (簡化邏輯以聚焦於 UI)
    rate = yf.Ticker("USDTWD=X").fast_info.get('last_price', 32.5)
    total_cash = (c_df['金額'] * c_df['幣別'].map({'USD': rate, 'TWD': 1})).sum() [cite: 3]
    total_inv = 81510  # 這裡建議使用你 Sheet 中 H2 的即時值 [cite: 2]
    total_assets = total_cash + total_inv

    # --- UI Layout ---
    
    # A. 頂部狀態欄
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    
    # B. 懸浮按鈕區 (模擬懸浮在圖表上方)
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    float_cols = st.columns([1, 1, 1, 4]) # 靠左排列
    with float_cols[0]: 
        if st.button("✨ 淨資產"): st.session_state.view = 'Total'
    with float_cols[1]: 
        if st.button("🏦 流動"): st.session_state.view = 'Cash'
    with float_cols[2]: 
        if st.button("📈 投資"): st.session_state.view = 'Invest'

    # C. 金額顯示與盈虧
    v_map = {'Total': ('Total', total_assets), 'Cash': ('Cash', total_cash), 'Invest': ('Invest', total_inv)}
    col_key, current_val = v_map[st.session_state.view]
    
    # 計算盈虧 (從 History 數據比對)
    h_df['Date'] = pd.to_datetime(h_df['Date'], format='mixed', errors='coerce').dropna() [cite: 1]
    h_df = h_df.sort_values('Date')
    
    last_val = h_df[col_key].iloc[-1] if len(h_df) > 0 else current_val
    prev_val = h_df[col_key].iloc[-2] if len(h_df) > 1 else last_val
    first_val = h_df[col_key].iloc[0] if len(h_df) > 0 else last_val
    
    diff_today = last_val - prev_val
    diff_all = last_val - first_val
    pct_today = (diff_today / prev_val * 100) if prev_val != 0 else 0

    st.markdown(f"""
        <div class='total-title'>$ {current_val:,.2f}</div>
        <div class='profit-all'>+ $ {diff_all:,.2f} ({ (diff_all/first_val*100):.2f}%) 全部時間</div>
        <div class='profit-today'>+ $ {diff_today:,.2f} (+{pct_today:.2f}%) 今日</div>
    """, unsafe_allow_html=True)

    # D. 折線圖 (自定義時間範圍過濾)
    if 'range' not in st.session_state: st.session_state.range = 'ALL'
    
    # 時間過濾邏輯
    now = h_df['Date'].max()
    ranges = {'7D': 7, '1M': 30, '6M': 180, 'YTD': (now - datetime(now.year, 1, 1)).days, '1Y': 365, 'ALL': 9999}
    filtered_h = h_df[h_df['Date'] >= (now - timedelta(days=ranges[st.session_state.range]))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filtered_h['Date'], y=filtered_h[col_key],
        mode='lines', line=dict(color='#4ECDC4', width=2.5),
        fill='tozeroy', fillcolor='rgba(78, 205, 196, 0.05)'
    ))
    fig.update_layout(
        height=250, margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, visible=False, range=[filtered_h[col_key].min()*0.98, filtered_h[col_key].max()*1.02])
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # E. 時間切換按鈕 (簡潔橫列)
    t_cols = st.columns(len(ranges))
    for i, r_name in enumerate(ranges.keys()):
        if t_cols[i].button(r_name): st.session_state.range = r_name

    # F. 下方資產明細 (仿截圖卡片)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    # ... (此處可沿用之前的 render_item 函數，建議將背景改為白色以符合新風格)

except Exception as e:
    st.error(f"佈局載入錯誤: {e}")
