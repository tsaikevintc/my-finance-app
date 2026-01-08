import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 質感 CSS
st.markdown("""
<style>
    [data-testid="stAppViewContainer"], .stApp { background-color: #0B0E14 !important; }
    .block-container { padding: 1.5rem 1.2rem !important; }

    .total-title { font-size: 42px; font-weight: 700; color: #FFFFFF !important; margin-bottom: 5px; letter-spacing: -1px; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 20px; }
    .pos { color: #00F2FE !important; font-weight: 600; }
    .neg { color: #FF4D4D !important; font-weight: 600; }

    /* 下方區間膠囊 (電氣青配色) */
    div[data-testid="stSegmentedControl"] { background-color: transparent !important; margin-top: 10px !important; }
    div[data-testid="stSegmentedControl"] button {
        background-color: #1C212B !important; color: #9CA3AF !important; 
        border: 1px solid #30363D !important; border-radius: 10px !important;
        min-height: 30px !important; font-size: 11px !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important; border: 1px solid #00F2FE !important; font-weight: 700 !important;
    }

    /* 卡片樣式 */
    .card-container { background: #161B22; border-radius: 14px; padding: 14px; margin-bottom: 12px; border: 1px solid #1F2937; display: flex; align-items: center; }
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-sub { font-size: 11px; color: #8B949E !important; }
    .card-value { font-size: 16px; font-weight: 700; color: #FFFFFF !important; text-align: right; flex-grow: 1; }
    
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 數據讀取與日期修復
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=60)
def fetch_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    i = pd.read_csv(f"{base}&gid={G_I}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    
    # --- 修正日期解析錯誤 ---
    # 使用 errors='coerce' 處理不一致的日期格式
    h['Date'] = pd.to_datetime(h['Date'], errors='coerce')
    h = h.dropna(subset=['Date']).sort_values('Date')
    return c, i, h

try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # 計算當前即時淨資產
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    current_cash = c_df['TWD'].sum()
    current_inv = 81510 # 假設的投資固定值，或從 i_df 計算
    latest_net_worth = current_cash + current_inv

    # --- 盈虧計算 (校對版) ---
    hist_list = h_df['Total'].tolist()
    
    if len(hist_list) >= 1:
        # 全部時間 = 最新 - 歷史第一筆 (2025/07/01)
        diff_all = latest_net_worth - hist_list[0]
        # 日盈虧 = 最新 - 歷史最後一筆 (昨日 2026/01/06)
        diff_today = latest_net_worth - hist_list[-1]
    else:
        diff_all = diff_today = 0

    # 4. 渲染介面
    st.markdown(f"<div class='total-title'>$ {latest_net_worth:,.0f}</div>", unsafe_allow_html=True)

    def fmt(v):
        color = "pos" if v >= 0 else "neg"
        prefix = "+" if v >= 0 else ""
        return f'<span class="{color}">{prefix}{v:,.0f}</span>'

    st.markdown(f'<div class="profit-row">{fmt(diff_all)} 全部時間 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 圖表
    fig = go.Figure(go.Scatter(
        x=h_df['Date'], y=h_df['Total'],
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'
    ))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 時間區間膠囊
    st.segmented_control("Range", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"], default="ALL", label_visibility="collapsed")

    # 資產列表
    st.markdown("<div style='color:#8B949E; font-size:14px; margin:20px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        st.markdown(f"""
            <div class="card-container">
                <div style="width:32px; height:32px; border-radius:50%; border:2px solid #00F2FE; display:flex; align-items:center; justify-content:center; font-size:8px; font-weight:bold; color:#00F2FE;">{int(r['TWD']/current_cash*100)}%</div>
                <div style="margin-left:12px;">
                    <div class="card-title">{r['子項目']}</div>
                    <div class="card-sub">{r['大項目']}</div>
                </div>
                <div class="card-value">$ {r['TWD']:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Render Error: {e}")
