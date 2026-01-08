import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 深度客製化 CSS (位置互換與縮小)
st.markdown("""
<style>
    /* 禁止手機左右滑動 */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100vw !important;
    }
    .block-container { padding: 1.2rem 1rem !important; max-width: 100vw !important; }
    .stApp { background-color: #0B0E14; color: #FFFFFF; font-family: 'Inter', sans-serif; }

    /* 頂部區域：膠囊在左上，數字在其下 */
    .header-box { display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 5px; }
    
    /* 膠囊按鈕縮小樣式 */
    div[data-testid="stSegmentedControl"] {
        gap: 4px !important;
        margin-bottom: 5px !important;
    }
    div[data-testid="stSegmentedControl"] button {
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 0px 8px !important;
        min-height: 20px !important;
        height: 20px !important;
        font-size: 9px !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #00F2FE !important;
        color: #000 !important;
        font-weight: 700;
    }

    /* 大數字樣式：縮小並靠左 */
    .total-title { font-size: 32px; font-weight: 700; color: #FFFFFF; margin-top: 5px; }

    /* 盈虧文字 */
    .profit-row { font-size: 12px; color: #9CA3AF; margin-bottom: 15px; }
    .pos { color: #00F2FE; font-weight: 600; }
    .neg { color: #FF4D4D; font-weight: 600; }

    /* 下方卡片列表 */
    .section-header { font-size: 14px; font-weight: 600; color: #9CA3AF; margin: 20px 0 10px 5px; }
    .custom-card {
        background: #161B22; border-radius: 12px; padding: 12px;
        margin-bottom: 10px; display: flex; align-items: center; border: 1px solid #1F2937;
    }
    .card-info { flex-grow: 1; margin-left: 12px; }
    .card-title { font-size: 14px; font-weight: 600; }
    .card-sub { font-size: 11px; color: #6B7280; }
    .card-value { text-align: right; font-weight: 700; font-size: 15px; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 資料來源與加載
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def load_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    i = pd.read_csv(f"{base}&gid={G_I}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    return c, i, h

try:
    c_df, i_df, h_df = load_data()
    rate = 32.5

    # --- 資料清洗與連動邏輯 ---
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    total_cash = c_df['TWD'].sum()
    total_inv = 81510 # 此處可根據 i_df 計算，暫用您的數值
    total_assets = total_cash + total_inv

    # 1. 頂部導覽膠囊 (左上角)
    view_map = {"總覽": "Total", "現金": "Cash", "投資": "Invest"}
    selected_label = st.segmented_control(
        label="Nav", options=["總覽", "現金", "投資"], default="總覽", label_visibility="collapsed"
    )
    view_key = view_map[selected_label]

    # 2. 動態大數字 (根據膠囊切換)
    curr_val = {"Total": total_assets, "Cash": total_cash, "Invest": total_inv}[view_key]
    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)

    # 3. 盈虧邏輯
    h_df['Date'] = pd.to_datetime(h_df['Date'], errors='coerce')
    hist_vals = h_df[view_key].dropna().tolist()
    diff_all = curr_val - hist_vals[0] if hist_vals else 0
    st.markdown(f'<div class="profit-row"><span class="pos">+{diff_all:,.0f}</span> 全部時間</div>', unsafe_allow_html=True)

    # 4. 圖表
    fig = go.Figure(go.Scatter(y=hist_vals, mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 5. 時間軸膠囊
    time_label = st.segmented_control(
        label="Time", options=["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"], default="ALL", label_visibility="collapsed"
    )

    # 6. 下方卡片：連動修復
    st.markdown("<br>", unsafe_allow_html=True)
    
    def render_row(name, sub, val, pct, color):
        st.markdown(f"""
            <div class="custom-card">
                <div style="width: 30px; height: 30px; border-radius: 50%; border: 2px solid {color}; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold;">{int(pct)}%</div>
                <div class="card-info">
                    <div class="card-title">{name}</div>
                    <div class="card-sub">{sub}</div>
                </div>
                <div class="card-value">$ {val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    # 根據選中的膠囊切換卡片內容
    if view_key in ["Total", "Cash"]:
        st.markdown("<div class='section-header'>● 現金資產</div>", unsafe_allow_html=True)
        for _, r in c_df.iterrows():
            render_row(r['子項目'], r['大項目'], r['TWD'], (r['TWD']/total_cash*100), "#00F2FE")

    if view_key in ["Total", "Invest"]:
        st.markdown("<div class='section-header'>● 投資項目</div>", unsafe_allow_html=True)
        for _, r in i_df.iterrows():
            # 這裡修正您的 i_df 欄位對應
            m_val = r['持有股數'] * r['買入成本'] * (rate if r['幣別']=='USD' else 1)
            render_row(r['名稱'], f"{r['類別']} ‧ {r['代號']}", m_val, (m_val/total_inv*100 if total_inv>0 else 0), "#FFD700")

except Exception as e:
    st.error(f"數據加載錯誤: {e}")
