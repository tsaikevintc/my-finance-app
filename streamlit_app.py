import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 電氣青 UI CSS
st.markdown("""
<style>
    .stApp { background-color: #0B0E14; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .block-container { padding: 1.5rem 1rem !important; }

    /* 頂部佈局：金額與右側膠囊按鈕並排 */
    .header-box { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 2px; }
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF; }
    
    /* 微型膠囊按鈕 */
    div.stButton > button {
        border-radius: 20px; border: none; height: 20px; width: 45px;
        background-color: #1C212B; color: #9CA3AF; font-size: 9px;
        padding: 0px 5px; min-width: 45px; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #2D3139; color: white; }
    div.stButton > button:focus { background-color: #00F2FE !important; color: #000 !important; }

    /* 盈虧文字 */
    .profit-row { font-size: 13px; color: #9CA3AF; margin-bottom: 10px; }
    .pos { color: #00F2FE; font-weight: 600; }
    .neg { color: #FF4D4D; font-weight: 600; }

    /* 時間區段 (橫排緊湊) */
    .time-container { display: flex; justify-content: space-between; margin-top: -20px; }
    div[data-testid="stHorizontalBlock"] .stButton > button {
        background: transparent; width: auto; font-size: 11px;
    }

    /* 下方資產卡片 (復原舊版分組佈局) */
    .section-header { font-size: 14px; font-weight: 600; color: #9CA3AF; margin: 20px 0 10px 5px; display: flex; align-items: center; }
    .dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    
    .custom-card {
        background: #161B22; border-radius: 12px; padding: 12px;
        margin-bottom: 10px; display: flex; align-items: center;
    }
    .card-info { flex-grow: 1; margin-left: 12px; }
    .card-title { font-size: 14px; font-weight: 500; color: #E5E7EB; }
    .card-sub { font-size: 11px; color: #6B7280; }
    .card-value { text-align: right; font-weight: 600; font-size: 15px; }

    /* 圓環佔比圖標 */
    .pie-icon-container {
        width: 36px; height: 36px; min-width: 36px;
        border-radius: 50%; position: relative; display: flex; align-items: center; justify-content: center;
    }
    .pie-icon-inner {
        position: absolute; width: 28px; height: 28px;
        background-color: #161B22; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 8px; font-weight: bold;
    }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 資料來源與讀取
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def load_all():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c, i, h = pd.read_csv(f"{base}&gid={G_C}"), pd.read_csv(f"{base}&gid={G_I}"), pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

try:
    c_df, i_df, h_df = load_all()
    rate = 32.5 # 匯率預設

    # 計算資產
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    total_cash = c_df['TWD'].sum()
    total_inv = 81510 # 固定市值或計算值
    total_assets = total_cash + total_inv

    # 4. 頂部佈局：金額 + 膠囊按鈕
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    
    col_amt, col_btns = st.columns([1.8, 1])
    with col_amt:
        v_map = {'Total': total_assets, 'Cash': total_cash, 'Invest': total_inv}
        curr_val = v_map[st.session_state.view]
        st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)
    
    with col_btns:
        st.markdown("<div style='display:flex; gap:4px; margin-top:20px;'>", unsafe_allow_html=True)
        bc1, bc2, bc3 = st.columns(3)
        if bc1.button("總覽"): st.session_state.view = 'Total'
        if bc2.button("現金"): st.session_state.view = 'Cash'
        if bc3.button("投資"): st.session_state.view = 'Invest'
        st.markdown("</div>", unsafe_allow_html=True)

    # 5. 盈虧計算
    h_df['Date'] = pd.to_datetime(h_df['Date'], format='mixed', errors='coerce').dropna()
    h_df = h_df.sort_values('Date')
    hist_vals = h_df[st.session_state.view].tolist()
    
    diff_today = curr_val - hist_vals[-1] if hist_vals else 0
    diff_all = curr_val - hist_vals[0] if hist_vals else 0

    st.markdown(f"""
        <div class="profit-row">
            <span class="{'pos' if diff_all >= 0 else 'neg'}">+{abs(diff_all):,.0f}</span> 全部時間 ‧ 
            今日 <span class="{'pos' if diff_today >= 0 else 'neg'}">+{abs(diff_today):,.0f}</span>
        </div>
    """, unsafe_allow_html=True)

    # 6. 電氣青發光線圖
    if 'range' not in st.session_state: st.session_state.range = 'ALL'
    ranges = {'7D':7, '1M':30, '3M':90, '6M':180, 'YTD':365, '1Y':365, 'ALL':9999}
    cutoff = datetime.now() - timedelta(days=ranges[st.session_state.range])
    f_h = h_df[h_df['Date'] >= cutoff]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=f_h['Date'], y=f_h[st.session_state.view],
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0, 242, 254, 0.05)'
    ))
    fig.update_layout(
        height=200, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, visible=False, range=[f_h[st.session_state.view].min()*0.98, f_h[st.session_state.view].max()*1.02])
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 7. 時間選擇橫排
    t_cols = st.columns(7)
    for i, r in enumerate(ranges.keys()):
        if t_cols[i].button(r): st.session_state.range = r

    # 8. 卡片渲染函數
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

    # 9. 資產明細 (按視圖顯示)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.view in ['Total', 'Cash']:
        st.markdown("<div class='section-header'><span class='dot' style='background:#00F2FE'></span>資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            render_row(r['子項目'], r['大項目'], r['TWD'], (r['TWD']/total_cash*100), "#00F2FE")

    if st.session_state.view in ['Total', 'Invest']:
        st.markdown("<div class='section-header'><span class='dot' style='background:#FFD700'></span>投資</div>", unsafe_allow_html=True)
        for _, r in i_df.iterrows():
            m_val = r['持有股數'] * r['買入成本'] * (rate if r['幣別']=='USD' else 1)
            render_row(r['名稱'], f"{r['類別']} ‧ {r['代號']}", m_val, (m_val/total_inv*100), "#FFD700")

except Exception as e:
    st.error(f"UI Loading Error: {e}")
