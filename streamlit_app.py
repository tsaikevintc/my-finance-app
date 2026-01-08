import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據讀取與日期解析修復
@st.cache_data(ttl=60)
def fetch_data():
    ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
    G_C, G_I, G_H = "526580417", "1335772092", "857913551"
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    i = pd.read_csv(f"{base}&gid={G_I}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    
    for df in [c, i, h]: df.columns = df.columns.str.strip()
    
    # --- 關鍵修復：處理包含「上午/下午」的日期格式 ---
    h['Date'] = pd.to_datetime(h['Date'].str.replace('上午', 'AM').str.replace('下午', 'PM'), errors='coerce', format='mixed')
    h = h.dropna(subset=['Date']).sort_values('Date')
    return c, i, h

# 3. 終極 CSS (強制橫向、封殺白色)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }

    /* 強制 st.pills 橫向排列且不換行 */
    [data-testid="stPills"] {
        display: flex !important;
        flex-direction: row !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        gap: 8px !important;
        padding: 5px 0 15px 0 !important;
    }
    [data-testid="stPills"]::-webkit-scrollbar { display: none; } 

    [data-testid="stPills"] button {
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        border: 1px solid #30363D !important;
        border-radius: 20px !important;
        flex-shrink: 0 !important;
    }

    [data-testid="stPills"] button[aria-checked="true"] {
        background-color: rgba(0, 242, 254, 0.1) !important;
        color: #00F2FE !important;
        border: 1px solid #00F2FE !important;
    }

    /* 文字亮度 */
    .total-title { font-size: 38px; font-weight: 700; color: #FFFFFF !important; margin: 0; }
    .profit-row { font-size: 13px; color: #8B949E !important; margin-bottom: 12px; }
    .pos { color: #00F2FE !important; font-weight: 600; }
    .neg { color: #FF4D4D !important; font-weight: 600; }
    .card-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; }
    .card-value { font-size: 16px; font-weight: 700; color: #FFFFFF !important; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, i_df, h_df = fetch_data()
    rate = 32.5

    # 4. 金額計算
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r['幣別']=='USD' else 1), axis=1)
    t_total = c_df['TWD'].sum() + 829010 

    # 5. 時間篩選膠囊 (橫向滑動)
    selected_range = st.pills(
        "Range", ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"],
        default="ALL", label_visibility="collapsed"
    )

    # 6. 動態篩選與盈虧連動
    now = h_df['Date'].max()
    filter_map = {
        "7D": now - timedelta(days=7),
        "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90),
        "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365),
        "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    
    filtered_h = h_df[h_df['Date'] >= filter_map[selected_range]]
    
    # 區間盈虧：當前總額 - 篩選後的第一筆
    diff_period = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    # 今日盈虧：當前總額 - 歷史表最後一筆
    diff_today = t_total - h_df['Total'].iloc[-1]

    # 7. 渲染介面
    st.markdown(f"<div class='total-title'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)
    
    def fmt(v):
        cl = "pos" if v >= 0 else "neg"
        prefix = "+" if v >= 0 else ""
        return f'<span class="{cl}">{prefix}{v:,.0f}</span>'
    
    st.markdown(f'<div class="profit-row">{fmt(diff_period)} {selected_range}區間總盈虧 ‧ 今日 {fmt(diff_today)}</div>', unsafe_allow_html=True)

    # 圖表
    fig = go.Figure(go.Scatter(
        x=filtered_h['Date'], y=filtered_h['Total'], 
        mode='lines', line=dict(color='#00F2FE', width=3),
        fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'
    ))
    fig.update_layout(height=170, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 8. 資產卡片
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

    st.markdown("<div style='color:#8B949E; font-size:14px; margin:15px 5px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        draw_card(r['子項目'], r['大項目'], r['TWD'])

except Exception as e:
    st.error(f"解析錯誤: {e}")
