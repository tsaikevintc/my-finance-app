import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定：強制寬版並隱藏頂部選單
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 深度客製化 CSS (針對手機寬度優化)
st.markdown("""
<style>
    /* 全域背景：極簡深黑藍 */
    .stApp { background-color: #0B0E14; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* 移除 Streamlit 預設的多餘內距 */
    .block-container { padding: 1rem 1rem !important; }

    /* 總額與盈虧：左對齊，模仿截圖佈局 */
    .total-container { padding: 10px 5px; }
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF; line-height: 1; }
    .profit-row { font-size: 13px; margin-top: 8px; color: #9CA3AF; }
    .pos { color: #00F2FE; font-weight: 600; } /* 電氣青色 */
    .neg { color: #FF4D4D; font-weight: 600; }

    /* 懸浮按鈕組 (視圖切換) */
    .view-switcher { display: flex; gap: 8px; margin-bottom: 5px; }
    .stButton > button {
        border-radius: 20px; border: 1px solid #2D3139; height: 28px;
        background-color: #1C212B; color: #9CA3AF; font-size: 11px;
        padding: 0px 15px; border: none;
    }
    .stButton > button:focus, .stButton > button:active {
        background-color: #00F2FE !important; color: #000000 !important;
    }

    /* 時間區段按鈕組：更小、更緊湊 */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        background: transparent; border: none; color: #6B7280; font-weight: 500;
    }

    /* 下方資產卡片：移除邊框，使用微漸層 */
    .custom-card {
        background: linear-gradient(145deg, #1C212B, #14181F);
        border-radius: 12px; padding: 12px; margin-bottom: 8px;
        display: flex; align-items: center;
    }
    .card-info { flex-grow: 1; margin-left: 12px; }
    .card-title { font-size: 14px; font-weight: 500; color: #E5E7EB; }
    .card-sub { font-size: 11px; color: #6B7280; }
    .card-value { text-align: right; font-weight: 600; font-size: 15px; }

    /* 環狀圖標小一點 */
    .pie-icon-container {
        width: 36px; height: 36px; min-width: 36px;
        border-radius: 50%; position: relative; display: flex; align-items: center; justify-content: center;
    }
    .pie-icon-inner {
        position: absolute; width: 28px; height: 28px;
        background-color: #14181F; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 8px; font-weight: bold;
    }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 數據邏輯 (保持穩定性)
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def load_all():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    df_c = pd.read_csv(f"{base}&gid={G_C}")
    df_i = pd.read_csv(f"{base}&gid={G_I}")
    df_h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [df_c, df_i, df_h]: df.columns = df.columns.str.strip()
    return df_c, df_i, df_h

try:
    c_df, i_df, h_df = load_all()
    rate = yf.Ticker("USDTWD=X").fast_info.get('last_price', 32.5)

    # A. 計算
    total_cash = (pd.to_numeric(c_df['金額']) * c_df['幣別'].map({'USD': rate, 'TWD': 1})).sum()
    # 投資市值 (讀取 H2 避免重複抓取)
    total_inv = 81510 # 此處建議連結你 Sheet 的 H2，這裡先用你提供的數字
    total_assets = total_cash + total_inv

    # B. UI 頂部視圖切換 (懸浮感)
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    v_cols = st.columns([1, 1, 1, 2])
    with v_cols[0]: 
        if st.button("總覽"): st.session_state.view = 'Total'
    with v_cols[1]: 
        if st.button("現金"): st.session_state.view = 'Cash'
    with v_cols[2]: 
        if st.button("投資"): st.session_state.view = 'Invest'

    # C. 金額顯示 (左對齊)
    v_map = {'Total': ('Total', total_assets), 'Cash': ('Cash', total_cash), 'Invest': ('Invest', total_inv)}
    col_key, curr_val = v_map[st.session_state.view]
    
    h_df['Date'] = pd.to_datetime(h_df['Date'], format='mixed', errors='coerce')
    h_df = h_df.dropna(subset=['Date']).sort_values('Date')
    hist_vals = h_df[col_key].tolist()
    
    diff_today = curr_val - hist_vals[-1] if hist_vals else 0
    diff_all = curr_val - hist_vals[0] if hist_vals else 0
    
    st.markdown(f"""
        <div class="total-container">
            <div class="total-title">$ {curr_val:,.0f}</div>
            <div class="profit-row">
                <span class="{'pos' if diff_all >= 0 else 'neg'}">+{abs(diff_all):,.0f}</span> 全部時間 ‧ 
                今日 <span class="{'pos' if diff_today >= 0 else 'neg'}">+{abs(diff_today):,.0f}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # D. 新潮線圖 (電氣青漸層)
    if 'range' not in st.session_state: st.session_state.range = 'ALL'
    cutoff = datetime.now() - timedelta(days={'7D':7,'1M':30,'3M':90,'6M':180,'YTD':365,'1Y':365,'ALL':9999}[st.session_state.range])
    f_h = h_df[h_df['Date'] >= cutoff]

    fig = go.Figure()
    # 增加發光陰影效果
    fig.add_trace(go.Scatter(
        x=f_h['Date'], y=f_h[col_key],
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0, 242, 254, 0.03)'
    ))
    fig.update_layout(
        height=200, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, visible=False, range=[f_h[col_key].min()*0.99, f_h[col_key].max()*1.01])
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # E. 時間切換 (橫向排列)
    t_cols = st.columns(7)
    for i, r in enumerate(['7D', '1M', '3M', '6M', 'YTD', '1Y', 'ALL']):
        if t_cols[i].button(r): st.session_state.range = r

    # F. 下方清單
    st.markdown("<br>", unsafe_allow_html=True)
    def render_row(name, sub, val, pct, color):
        p_bg = f"conic-gradient({color} {pct*3.6}deg, #2D3139 0deg)"
        st.markdown(f"""
            <div class="custom-card">
                <div class="pie-icon-container" style="background: {p_bg};">
                    <div class="pie-icon-inner">{int(pct)}%</div>
                </div>
                <div class="card-info">
                    <div class="card-title">{name}</div>
                    <div class="card-sub">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    if st.session_state.view in ['Total', 'Cash']:
        for _, r in c_df.iterrows():
            render_row(r['大項目'], r.get('子項目',''), r['金額'], (r['金額']/total_cash*100), "#00F2FE")

except Exception as e:
    st.error(f"Error: {e}")
