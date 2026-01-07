import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# 1. 頁面設定與 APP 質感優化
st.set_page_config(page_title="Insights Asset", layout="wide", initial_sidebar_state="collapsed")

# 2. 進階 CSS：打造仿 APP 的深色 UI
st.markdown("""
<style>
    /* 全域背景 */
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* 圓餅百分比圖標：左側圓環效果 */
    .pie-icon-container {
        display: flex; align-items: center; justify-content: center;
        width: 42px; height: 42px; min-width: 42px;
        border-radius: 50%; position: relative; margin-right: 15px;
    }
    .pie-icon-inner {
        position: absolute; width: 34px; height: 34px;
        background-color: #161B22; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: #FFFFFF; font-size: 10px; font-weight: bold;
    }
    
    /* 卡片設計 */
    .custom-card {
        background-color: #161B22; border-radius: 16px;
        padding: 12px 16px; margin-bottom: 10px;
        display: flex; align-items: center; border: 1px solid #1F2937;
    }
    .card-info { flex-grow: 1; }
    .card-title { font-size: 15px; font-weight: 600; color: #F3F4F6; }
    .card-sub { font-size: 11px; color: #9CA3AF; }
    .card-value { text-align: right; font-weight: 700; font-size: 16px; color: #F3F4F6; }

    /* 切換按鈕 (選取狀態由 Session State 控制) */
    .stButton > button {
        border-radius: 20px; border: 1px solid #374151;
        background-color: #1F2937; color: #9CA3AF; font-size: 13px; height: 35px;
    }
    .stButton > button:hover { border-color: #60A5FA; color: white; }
    
    /* 隱藏不必要元件 */
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 資料來源設定 (請確保 GID 正確)
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C = "526580417"   # 現金資產分頁
G_I = "1335772092"  # 投資清單分頁
G_H = "857913551"   # History 歷史紀錄分頁

@st.cache_data(ttl=60)
def load_all_data():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    df_c = pd.read_csv(f"{base}&gid={G_C}")
    df_i = pd.read_csv(f"{base}&gid={G_I}")
    df_h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [df_c, df_i, df_h]:
        df.columns = df.columns.str.strip()
    return df_c, df_i, df_h

try:
    c_df, i_df, h_df = load_all_data()
    rate = yf.Ticker("USDTWD=X").fast_info['last_price']
    
    # 即時計算現金與投資
    c_df['TWD'] = c_df.apply(lambda r: r['金額'] * (rate if r.get('幣別')=='USD' else 1), axis=1)
    total_cash = c_df['TWD'].sum()
    
    tks = i_df['代號'].dropna().unique().tolist()
    px_raw = yf.download(tks, period="1d", progress=False)['Close']
    prices = px_raw.iloc[-1].to_dict() if len(tks)>1 else ({tks[0]: px_raw.iloc[-1]} if tks else {})
    i_df['市值TWD'] = i_df.apply(lambda r: (prices.get(r['代號'], r['買入成本'])*r['持有股數']) * (rate if r.get('幣別')=='USD' else 1), axis=1)
    total_inv = i_df['市值TWD'].sum()
    total_assets = total_cash + total_inv

    # --- UI: 頂部視圖切換 ---
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    
    st.markdown("<h3 style='text-align: center; margin-bottom: 10px;'>Insights</h3>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    if b1.button("✨ 淨資產", use_container_width=True): st.session_state.view = 'Total'
    if b2.button("💵 流動資金", use_container_width=True): st.session_state.view = 'Cash'
    if b3.button("📈 投資組合", use_container_width=True): st.session_state.view = 'Invest'

    # --- UI: 折線圖 (讀取 History 分頁) ---
    v_conf = {
        'Total': ('Total', '#60A5FA'), 
        'Cash': ('Cash', '#34D399'), 
        'Invest': ('Invest', '#F472B6')
    }
    col_name, theme_color = v_conf[st.session_state.view]
    
    if not h_df.empty and col_name in h_df.columns:
        h_df['Date'] = pd.to_datetime(h_df['Date'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=h_df['Date'], y=h_df[col_name], mode='lines', 
            line=dict(color=theme_color, width=3),
            fill='tozeroy',
            fillcolor=f'rgba({int(theme_color[1:3],16)},{int(theme_color[3:5],16)},{int(theme_color[5:7],16)},0.1)'
        ))
        fig.update_layout(
            height=220, margin=dict(l=10,r=10,t=10,b=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#4B5563'),
            yaxis=dict(showgrid=False, visible=False)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("尚未發現歷史數據，請確認 History 分頁內容。")

    # 顯示目前選取的總金額
    display_val = total_assets if col_name=='Total' else (total_cash if col_name=='Cash' else total_inv)
    st.markdown(f"<h1 style='text-align:center; margin-top:-25px;'>$ {display_val:,.0f}</h1>", unsafe_allow_html=True)

    # --- 渲染函數: 環狀百分比卡片 ---
    def render_item(name, sub, val, pct, color):
        pie_bg = f"conic-gradient({color} {pct*3.6}deg, #374151 0deg)"
        st.markdown(f"""
        <div class="custom-card">
            <div class="pie-icon-container" style="background: {pie_bg};">
                <div class="pie-icon-inner">{int(pct)}%</div>
            </div>
            <div class="card-info">
                <div class="card-title">{name}</div>
                <div class="card-sub">{sub}</div>
            </div>
            <div class="card-value">$ {val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 列表顯示 ---
    if st.session_state.view in ['Total', 'Cash']:
        st.write("🏦 資金明細")
        for _, r in c_df.iterrows():
            sub = r.get('附註', r.get('幣別', 'Cash'))
            render_item(r['大項目'], sub, r['TWD'], (r['TWD']/total_cash*100 if total_cash>0 else 0), "#34D399")

    if st.session_state.view in ['Total', 'Invest']:
        st.write("🚀 投資組合")
        i_sorted = i_df.sort_values('市值TWD', ascending=False)
        for _, r in i_sorted.iterrows():
            render_item(r['名稱'], r['代號'], r['市值TWD'], (r['市值TWD']/total_inv*100 if total_inv>0 else 0), "#60A5FA")

except Exception as e:
    st.error(f"系統運行錯誤: {e}")
