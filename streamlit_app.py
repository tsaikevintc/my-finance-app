import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據讀取
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=60)
def fetch_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    i = pd.read_csv(f"{base}&gid={G_I}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

# 3. 終極 CSS：封殺白色、美化按鈕、亮白文字
st.markdown("""
<style>
    /* 背景鎖定 */
    [data-testid="stAppViewContainer"], .stApp { background-color: #0B0E14 !important; }
    .block-container { padding: 1rem !important; }

    /* 隱藏官方膠囊區 */
    div[data-testid="stSegmentedControl"] { display: none !important; }

    /* 頂部文字質感 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin: 0; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 15px; }
    .pos { color: #00F2FE !important; font-weight: 600; }
    .neg { color: #FF4D4D !important; font-weight: 600; }

    /* 下方膠囊按鈕美化 (橫向排列不換行) */
    .stHorizontalBlock { gap: 4px !important; }
    div.stButton > button {
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        border: 1px solid #30363D !important;
        border-radius: 10px !important;
        padding: 2px 5px !important;
        font-size: 11px !important;
        height: 28px !important;
        transition: 0.3s;
    }
    div.stButton > button:focus, div.stButton > button:active {
        background-color: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
    }

    /* 卡片樣式 */
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-value { font-size: 16px; font-weight: 700; color: #FFFFFF !important; text-align: right; }
    
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # 金額計算 (單一視圖)
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_cash = c_df['TWD'].sum()
    t_inv = 829010 
    t_total = t_cash + t_inv

    # 4. 盈虧計算 (即時總資產 vs 歷史數據)
    hist_vals = h_df['Total'].dropna().tolist()
    diff_all = t_total - hist_vals[0] if hist_vals else 0
    diff_today = t_total - hist_vals[-1] if hist_vals else 0

    # 5. 畫面渲染
    st.markdown(f"<div class='total-title'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)
    
    def fmt(v):
        cl = "pos" if v >= 0 else "neg"
        return f'<span class="{cl}">{" " if v < 0 else "+"}{v:,.0f}</span>'
    
    st.markdown(f'<div class="profit-row">{fmt(diff_all)} 全部時間 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 圖表 (微調高度)
    fig = go.Figure(go.Scatter(y=hist_vals, mode='lines', line=dict(color='#00F2FE', width=2.5), fill='tozeroy', fillcolor='rgba(0,242,254,0.02)'))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- 時間尺度膠囊 (修復點選與換行問題) ---
    # 使用 7 個等寬欄位，確保手機端不換行
    t_cols = st.columns(7)
    ranges = ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"]
    for i, r in enumerate(ranges):
        t_cols[i].button(r, key=f"range_{r}", use_container_width=True)

    # --- 卡片列表 ---
    st.markdown("<br>", unsafe_allow_html=True)
    def draw_card(title, sub, val):
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; border:1px solid #30363D; display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <div class="card-title">{title}</div>
                    <div style="color:#8B949E; font-size:11px; margin-top:2px;">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='color:#8B949E; font-size:14px; margin:10px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        draw_card(r['子項目'], r['大項目'], r['TWD'])

except Exception as e:
    st.error(f"系統錯誤: {e}")
