import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 終極 CSS (徹底封殺白色區塊，確保文字亮白)
st.markdown("""
<style>
    /* 核心背景 */
    [data-testid="stAppViewContainer"], .stApp { 
        background-color: #0B0E14 !important; 
    }
    .block-container { padding: 1.2rem 1rem !important; }
    
    /* 徹底封殺 Segmented Control 的白色底座 */
    div[data-testid="stSegmentedControl"], 
    div[data-testid="stSegmentedControl"] > div,
    div[role="radiogroup"] {
        background-color: transparent !important;
        border: none !important;
    }
    
    div[data-testid="stSegmentedControl"] button {
        background-color: #1C212B !important; /* 質感深灰 */
        color: #9CA3AF !important; 
        border: 1px solid #30363D !important;
        border-radius: 10px !important;
        min-height: 32px !important;
        box-shadow: none !important;
    }

    /* 選中狀態：電氣青邊框與文字 */
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
        font-weight: 700 !important;
    }

    /* 文字顏色修復 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin-top: 5px; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 12px; }
    .pos { color: #00F2FE !important; font-weight: 600; }
    .neg { color: #FF4D4D !important; font-weight: 600; }

    /* 卡片字體修復 */
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-sub { font-size: 11px; color: #8B949E !important; }
    .card-value { font-size: 16px; font-weight: 700; color: #FFFFFF !important; text-align: right; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 補回數據讀取函數 (fetch_data)
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def fetch_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    i = pd.read_csv(f"{base}&gid={G_I}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    # 清洗欄位空格
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

# 4. 盈虧計算邏輯
# 全部時間 = 當前總值 - 歷史表第一筆
# 今日盈虧 = 當前總值 - 歷史表最後一筆 (代表昨日結算)
def get_profits(curr, hist_list):
    if not hist_list: return 0, 0
    all_time = curr - hist_list[0]
    today = curr - hist_list[-1]
    return all_time, today

try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # --- 頂部導覽 ---
    nav_selection = st.segmented_control(
        "Nav", ["總覽", "現金", "投資"], default="總覽", label_visibility="collapsed"
    )
    
    # 金額計算
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_cash = c_df['TWD'].sum()
    t_inv = 829010 
    t_total = t_cash + t_inv

    vals = {"總覽": t_total, "現金": t_cash, "投資": t_inv}
    keys = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}
    curr_val = vals[nav_selection]

    # 顯示金額
    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)

    # 盈虧計算
    hist_vals = h_df[keys[nav_selection]].dropna().tolist()
    diff_all, diff_today = get_profits(curr_val, hist_vals)

    def fmt(v):
        cl = "pos" if v >= 0 else "neg"
        return f'<span class="{cl}">{" " if v < 0 else "+"}{v:,.0f}</span>'

    st.markdown(f'<div class="profit-row">{fmt(diff_all)} 全部時間 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # --- 圖表 ---
    fig = go.Figure(go.Scatter(y=hist_vals, mode='lines', line=dict(color='#00F2FE', width=2.5), fill='tozeroy', fillcolor='rgba(0,242,254,0.03)'))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- 時間軸 ---
    st.segmented_control("Range", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"], default="ALL", label_visibility="collapsed")

    # --- 卡片渲染 ---
    def draw_card(title, sub, val, pct, color):
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:12px; margin-bottom:10px; display:flex; align-items:center; border:1px solid #30363D;">
                <div style="width:32px; height:32px; border-radius:50%; border:2px solid {color}; display:flex; align-items:center; justify-content:center; font-size:8px; font-weight:bold; color:{color};">{int(pct)}%</div>
                <div style="flex-grow:1; margin-left:12px;">
                    <div class="card-title">{title}</div>
                    <div class="card-sub">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    if nav_selection in ["總覽", "現金"]:
        st.markdown("<div style='color:#8B949E; font-size:14px; margin:20px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            draw_card(r['子項目'], r['大項目'], r['TWD'], (r['TWD']/t_cash*100), "#00F2FE")

except Exception as e:
    st.error(f"系統錯誤: {e}")
