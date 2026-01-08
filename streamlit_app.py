import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據讀取補全
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=60)
def fetch_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c, i, h = pd.read_csv(f"{base}&gid={G_C}"), pd.read_csv(f"{base}&gid={G_I}"), pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

# 3. 終極 CSS：封殺官方元件，自定義捲動膠囊
st.markdown("""
<style>
    /* 核心背景鎖定 */
    [data-testid="stAppViewContainer"], .stApp { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }

    /* 隱藏引發白色塊與換行的官方元件 */
    div[data-testid="stSegmentedControl"] { display: none !important; }

    /* 橫向捲動膠囊容器 */
    .scroll-container {
        display: flex;
        overflow-x: auto;
        white-space: nowrap;
        gap: 8px;
        padding: 5px 0 15px 0;
        scrollbar-width: none; /* Firefox */
    }
    .scroll-container::-webkit-scrollbar { display: none; } /* Chrome/Safari */

    /* 膠囊按鈕樣式 */
    .capsule {
        display: inline-block;
        padding: 6px 20px;
        background: #1C212B;
        color: #9CA3AF;
        border: 1px solid #30363D;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
    }
    .capsule.active {
        background: rgba(0, 242, 254, 0.1);
        color: #00F2FE;
        border: 1px solid #00F2FE;
        font-weight: 700;
    }

    /* 文字樣式加強 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin: 5px 0; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 15px; }
    .pos { color: #00F2FE !important; }
    .neg { color: #FF4D4D !important; }
    
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # --- 頂部導覽切換 (邏輯與畫面分離) ---
    if 'nav' not in st.session_state: st.session_state.nav = "總覽"
    
    # 使用 st.columns 配合 st.button 達成無背景換行
    c1, c2, c3, _ = st.columns([1, 1, 1, 2])
    if c1.button("總覽", use_container_width=True): st.session_state.nav = "總覽"
    if c2.button("現金", use_container_width=True): st.session_state.nav = "現金"
    if c3.button("投資", use_container_width=True): st.session_state.nav = "投資"

    # 金額計算
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_cash = c_df['TWD'].sum()
    t_inv = 829010 
    t_total = t_cash + t_inv

    vals = {"總覽": t_total, "現金": t_cash, "投資": t_inv}
    keys = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}
    curr_val = vals[st.session_state.nav]

    # --- 盈虧計算邏輯解析 ---
    # 這裡抓取歷史表的數據來對比
    hist_vals = h_df[keys[st.session_state.nav]].dropna().tolist()
    
    # 全部時間 = 當前金額 - 歷史第一筆 (最初記錄)
    # 今日盈虧 = 當前金額 - 歷史最後一筆 (昨日收盤)
    diff_all = curr_val - hist_vals[0] if hist_vals else 0
    diff_today = curr_val - hist_vals[-1] if hist_vals else 0

    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)
    
    def fmt(v):
        cl = "pos" if v >= 0 else "neg"
        return f'<span class="{cl}">{" " if v < 0 else "+"}{v:,.0f}</span>'
    
    st.markdown(f'<div class="profit-row">{fmt(diff_all)} 全部時間 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 圖表
    fig = go.Figure(go.Scatter(y=hist_vals, mode='lines', line=dict(color='#00F2FE', width=2.5), fill='tozeroy', fillcolor='rgba(0,242,254,0.02)'))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- 時間尺度導覽 (橫向捲動不換行) ---
    st.markdown("""
        <div class="scroll-container">
            <div class="capsule">7D</div>
            <div class="capsule">1M</div>
            <div class="capsule">3M</div>
            <div class="capsule">6M</div>
            <div class="capsule">YTD</div>
            <div class="capsule">1Y</div>
            <div class="capsule active">ALL</div>
        </div>
    """, unsafe_allow_html=True)

    # 卡片渲染
    def draw_card(title, sub, val):
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; border:1px solid #30363D; display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <div style="color:#FFFFFF !important; font-weight:600; font-size:15px;">{title}</div>
                    <div style="color:#8B949E; font-size:11px; margin-top:2px;">{sub}</div>
                </div>
                <div style="color:#FFFFFF !important; font-weight:700; font-size:16px; text-align:right;">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    if st.session_state.nav in ["總覽", "現金"]:
        st.markdown("<div style='color:#8B949E; font-size:14px; margin:10px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            draw_card(r['子項目'], r['大項目'], r['TWD'])

except Exception as e:
    st.error(f"系統錯誤: {e}")
