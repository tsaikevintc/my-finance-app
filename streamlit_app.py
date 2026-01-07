import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 精準排版 CSS (針對 1000019740.png 風格優化)
st.markdown("""
<style>
    .stApp { background-color: #0B0E14; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .block-container { padding: 1rem 1rem !important; }

    /* 大金額與右側小按鈕 */
    .header-box { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: -5px; }
    .total-title { font-size: 34px; font-weight: 700; color: #FFFFFF; }
    
    /* 盈虧文字 */
    .profit-row { font-size: 12px; margin-top: 5px; color: #9CA3AF; margin-bottom: 10px; }
    .pos { color: #00F2FE; font-weight: 600; }
    .neg { color: #FF4D4D; font-weight: 600; }

    /* 頂部切換按鈕 (縮小並橫排) */
    .view-btn-container { display: flex; gap: 5px; }
    div.stButton > button {
        border-radius: 15px; border: none; height: 24px;
        background-color: #1C212B; color: #9CA3AF; font-size: 10px;
        padding: 0px 10px; min-width: 50px;
    }
    div.stButton > button:focus { background-color: #00F2FE !important; color: #000000 !important; }

    /* 時間區段 (強制橫排與縮小) */
    .time-container { display: flex; justify-content: space-between; margin-top: -20px; padding: 0 5px; }
    .time-btn-col { padding: 0 !important; }

    /* 下方卡片復原與分組 */
    .section-header { font-size: 14px; font-weight: 600; color: #9CA3AF; margin: 15px 0 10px 5px; display: flex; align-items: center; }
    .dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .custom-card {
        background: #161B22; border-radius: 12px; padding: 12px;
        margin-bottom: 8px; display: flex; align-items: center;
    }
    .card-info { flex-grow: 1; margin-left: 12px; }
    .card-title { font-size: 14px; font-weight: 500; }
    .card-sub { font-size: 11px; color: #6B7280; }
    .card-value { text-align: right; font-weight: 600; font-size: 14px; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 數據載入 (Source 1, 2, 3)
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def load_all():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    i = pd.read_csv(f"{base}&gid={G_I}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

try:
    c_df, i_df, h_df = load_all()
    rate = 32.5  # 預設匯率

    # --- A. 核心計算 ---
    # 現金明細與總額 (Source 3)
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    total_cash = c_df['TWD'].sum()
    
    # 投資明細與總額 (Source 2)
    # 使用快取或預設市值 81510 
    total_inv = 81510 
    total_assets = total_cash + total_inv

    # --- B. 頂部佈局 (金額 + 右側縮小按鈕) ---
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    
    header_col1, header_col2 = st.columns([2, 1])
    
    with header_col1:
        v_map = {'Total': total_assets, 'Cash': total_cash, 'Invest': total_inv}
        curr_val = v_map[st.session_state.view]
        st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)
    
    with header_col2:
        st.markdown("<div class='view-btn-container'>", unsafe_allow_html=True)
        btn_c1, btn_c2, btn_c3 = st.columns(3)
        if btn_c1.button("總覽"): st.session_state.view = 'Total'
        if btn_c2.button("現金"): st.session_state.view = 'Cash'
        if btn_c3.button("投資"): st.session_state.view = 'Invest'
        st.markdown("</div>", unsafe_allow_html=True)

    # --- C. 盈虧計算 ---
    h_df['Date'] = pd.to_datetime(h_df['Date'], format='mixed', errors='coerce')
    h_df = h_df.dropna(subset=['Date']).sort_values('Date')
    col_key = st.session_state.view
    hist_vals = h_df[col_key].tolist()
    
    diff_today = curr_val - hist_vals[-1] if hist_vals else 0
    diff_all = curr_val - hist_vals[0] if hist_vals else 0
    
    st.markdown(f"""
        <div class="profit-row">
            <span class="{'pos' if diff_all >= 0 else 'neg'}">+{abs(diff_all):,.0f}</span> 全部時間 ‧ 
            今日 <span class="{'pos' if diff_today >= 0 else 'neg'}">+{abs(diff_today):,.0f}</span>
        </div>
    """, unsafe_allow_html=True)

    # --- D. 電氣青線圖 ---
    if 'range' not in st.session_state: st.session_state.range = 'ALL'
    ranges = {'7D':7, '1M':30, '3M':90, '6M':180, 'YTD':365, '1Y':365, 'ALL':9999}
    cutoff = datetime.now() - timedelta(days=ranges[st.session_state.range])
    f_h = h_df[h_df['Date'] >= cutoff]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=f_h['Date'], y=f_h[col_key],
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0, 242, 254, 0.05)'
    ))
    fig.update_layout(
        height=180, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, visible=False, range=[f_h[col_key].min()*0.99, f_h[col_key].max()*1.01])
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- E. 時間區段橫排按鈕 ---
    t_cols = st.columns(7)
    for i, r in enumerate(ranges.keys()):
        if t_cols[i].button(r): st.session_state.range = r

    # --- F. 下方清單 (復原版本與分組) ---
    def render_row(name, sub, val, pct, color):
        p_bg = f"conic-gradient({color} {pct*3.6}deg, #2D3139 0deg)"
        st.markdown(f"""
            <div class="custom-card">
                <div class="pie-icon-container" style="background: {p_bg}; width:30px; height:30px; min-width:30px; display:flex; align-items:center; justify-content:center; border-radius:50%;">
                    <div style="background:#161B22; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:7px;">{int(pct)}%</div>
                </div>
                <div class="card-info">
                    <div class="card-title">{name}</div>
                    <div class="card-sub">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 顯示現金資產 (Source 3)
    if st.session_state.view in ['Total', 'Cash']:
        st.markdown("<div class='section-header'><span class='dot' style='background:#00F2FE'></span>資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            render_row(r['子項目'], r['大項目'], r['TWD'], (r['TWD']/total_cash*100), "#00F2FE")

    # 顯示投資組合 (Source 2)
    if st.session_state.view in ['Total', 'Invest']:
        st.markdown("<div class='section-header'><span class='dot' style='background:#FFD700'></span>投資</div>", unsafe_allow_html=True)
        for _, r in i_df.iterrows():
            # 計算該項投資的台幣市值
            m_val = r['持有股數'] * r['買入成本'] * (rate if r['幣別']=='USD' else 1)
            render_row(r['名稱'], f"{r['類別']} ‧ {r['代號']}", m_val, (m_val/total_inv*100 if total_inv>0 else 0), "#FFD700")

except Exception as e:
    st.error(f"Layout Error: {e}")
