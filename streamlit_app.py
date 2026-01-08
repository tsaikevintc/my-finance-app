import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面基礎設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 全域質感 CSS (徹底封鎖任何官方元件產生的白色)
st.markdown("""
<style>
    /* 強制全域深色 */
    [data-testid="stAppViewContainer"], .stApp { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }

    /* 隱藏官方 Segmented Control (因為我們要用自定義的) */
    div[data-testid="stSegmentedControl"] { display: none !important; }

    /* 自定義 HTML 膠囊樣式 */
    .custom-nav { display: flex; gap: 8px; margin-bottom: 15px; }
    .nav-item {
        background: #1C212B; color: #8B949E; padding: 6px 16px; 
        border-radius: 20px; font-size: 13px; border: 1px solid #30363D;
        cursor: pointer; transition: 0.3s;
    }
    .nav-item.active {
        background: rgba(0, 242, 254, 0.1); color: #00F2FE; border: 1px solid #00F2FE; font-weight: bold;
    }

    /* 數值與卡片顏色鎖定 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin: 10px 0; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 15px; }
    .pos { color: #00F2FE !important; font-weight: 600; }
    .neg { color: #FF4D4D !important; font-weight: 600; }
    
    .card-title { color: #FFFFFF !important; font-weight: 600; font-size: 15px; }
    .card-value { color: #FFFFFF !important; font-weight: 700; font-size: 16px; text-align: right; }
    
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 數據與計算邏輯
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=60)
def fetch_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c, i, h = pd.read_csv(f"{base}&gid={G_C}"), pd.read_csv(f"{base}&gid={G_I}"), pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # --- 自定義膠囊導覽 (使用 st.radio 的隱藏技巧或 session_state) ---
    if 'nav' not in st.session_state: st.session_state.nav = "總覽"
    
    # 建立自定義 HTML 膠囊
    cols = st.columns([1, 1, 1, 3])
    with cols[0]: 
        if st.button("總覽", key="btn_all"): st.session_state.nav = "總覽"
    with cols[1]:
        if st.button("現金", key="btn_cash"): st.session_state.nav = "現金"
    with cols[2]:
        if st.button("投資", key="btn_inv"): st.session_state.nav = "投資"

    # 計算數值
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_cash = c_df['TWD'].sum()
    t_inv = 829010 
    t_total = t_cash + t_inv

    vals = {"總覽": t_total, "現金": t_cash, "投資": t_inv}
    keys = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}
    curr_val = vals[st.session_state.nav]

    # 4. 盈虧計算說明
    # [全部時間] = 目前金額 - 歷史表的第一筆 (最原始記錄)
    # [今日盈虧] = 目前金額 - 歷史表的最後一筆 (代表昨天結算的數字)
    hist_vals = h_df[keys[st.session_state.nav]].dropna().tolist()
    
    diff_all = curr_val - hist_vals[0] if hist_vals else 0
    diff_today = curr_val - hist_vals[-1] if hist_vals else 0

    # 5. 渲染畫面
    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)
    
    def fmt(v):
        cl = "pos" if v >= 0 else "neg"
        return f'<span class="{cl}">{" " if v < 0 else "+"}{v:,.0f}</span>'
    
    st.markdown(f'<div class="profit-row">{fmt(diff_all)} 全部時間 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 圖表
    fig = go.Figure(go.Scatter(y=hist_vals, mode='lines', line=dict(color='#00F2FE', width=2.5), fill='tozeroy', fillcolor='rgba(0,242,254,0.03)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 卡片 (強制使用亮白文字)
    def draw_card(title, sub, val, color):
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; display:flex; align-items:center; border:1px solid #30363D;">
                <div style="flex-grow:1;">
                    <div class="card-title">{title}</div>
                    <div style="color:#8B949E; font-size:11px; margin-top:2px;">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    if st.session_state.nav in ["總覽", "現金"]:
        st.markdown("<div style='color:#8B949E; font-size:14px; margin:10px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            draw_card(r['子項目'], r['大項目'], r['TWD'], "#00F2FE")

except Exception as e:
    st.error(f"Error: {e}")
