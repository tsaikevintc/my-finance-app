import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 頁面設定
st.set_page_config(page_title="Asset Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 專業金融 UI CSS (深色質感)
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* 金額與盈虧文字 */
    .total-title { font-size: 38px; font-weight: 800; margin-bottom: 2px; color: #F3F4F6; font-family: 'Inter', sans-serif; }
    .profit-row { font-size: 14px; margin-bottom: 20px; }
    .profit-positive { color: #4ADE80; font-weight: 600; }
    .profit-negative { color: #FB7185; font-weight: 600; }
    .label-text { color: #9CA3AF; margin: 0 5px; }

    /* 懸浮微型按鈕 */
    .stButton > button {
        border-radius: 8px; border: 1px solid #374151; height: 28px;
        background-color: #1F2937; color: #9CA3AF; font-size: 11px;
        padding: 0px 12px; transition: 0.2s;
    }
    .stButton > button:hover { border-color: #60A5FA; color: white; }

    /* 下方資產卡片 */
    .custom-card {
        background-color: #161B22; border-radius: 16px;
        padding: 12px 16px; margin-bottom: 10px;
        display: flex; align-items: center; border: 1px solid #1F2937;
    }
    .card-info { flex-grow: 1; }
    .card-title { font-size: 15px; font-weight: 600; color: #F3F4F6; }
    .card-sub { font-size: 11px; color: #9CA3AF; }
    .card-value { text-align: right; font-weight: 700; font-size: 16px; color: #F3F4F6; }

    .pie-icon-container {
        display: flex; align-items: center; justify-content: center;
        width: 40px; height: 40px; min-width: 40px;
        border-radius: 50%; position: relative; margin-right: 15px;
    }
    .pie-icon-inner {
        position: absolute; width: 32px; height: 32px;
        background-color: #161B22; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: #FFFFFF; font-size: 9px; font-weight: bold;
    }

    /* 隱藏預設元件 */
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 輔助函式
def fix_ticker(t):
    t = str(t).strip()
    if 'TPE:' in t: return t.replace('TPE:', '') + '.TW'
    if 'NASDAQ:' in t: return t.replace('NASDAQ:', '')
    if 'NYSE:' in t: return t.replace('NYSE:', '')
    return t

# 4. 資料來源
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
def load_all():
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    df_c = pd.read_csv(f"{base}&gid={G_C}")
    df_i = pd.read_csv(f"{base}&gid={G_I}")
    df_h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [df_c, df_i, df_h]: df.columns = df.columns.str.strip()
    return df_c, df_i, df_h

try:
    c_df, i_df, h_df = load_all()
    rate = yf.Ticker("USDTWD=X").fast_info.get('last_price', 32.5)
    
    # --- A. 核心計算 ---
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r.get('幣別')=='USD' else 1), axis=1)
    total_cash = c_df['TWD'].sum()
    
    # 投資市值計算
    i_df['yf_t'] = i_df['代號'].apply(fix_ticker)
    tk_list = i_df['yf_t'].unique().tolist()
    px_data = yf.download(tk_list, period="1d", progress=False)['Close']
    
    def get_market_val(row):
        try:
            curr_p = px_data[row['yf_t']].iloc[-1] if len(tk_list) > 1 else px_data.iloc[-1]
            if pd.isna(curr_p): curr_p = row['買入成本']
        except: curr_p = row['買入成本']
        return (curr_p * row['持有股數']) * (rate if row.get('幣別')=='USD' else 1)

    i_df['市值TWD'] = i_df.apply(get_market_val, axis=1)
    total_inv = i_df['市值TWD'].sum()
    total_assets = total_cash + total_inv

    # --- B. UI 頂部視圖切換 ---
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    btn_cols = st.columns([1, 1, 1, 5])
    with btn_cols[0]: 
        if st.button("✨ 總覽"): st.session_state.view = 'Total'
    with btn_cols[1]: 
        if st.button("🏦 現金"): st.session_state.view = 'Cash'
    with btn_cols[2]: 
        if st.button("📈 投資"): st.session_state.view = 'Invest'

    # --- C. 金額顯示與盈虧 ---
    v_map = {'Total': ('Total', total_assets), 'Cash': ('Cash', total_cash), 'Invest': ('Invest', total_inv)}
    col_key, curr_val = v_map[st.session_state.view]
    
    h_df['Date'] = pd.to_datetime(h_df['Date'], format='mixed', errors='coerce')
    h_df = h_df.dropna(subset=['Date']).sort_values('Date')
    
    hist_vals = h_df[col_key].tolist()
    diff_today = curr_val - hist_vals[-1] if hist_vals else 0
    diff_all = curr_val - hist_vals[0] if hist_vals else 0
    
    def get_cls(v): return "profit-positive" if v >= 0 else "profit-negative"
    def get_sign(v): return "+" if v >= 0 else ""

    st.markdown(f"<div class='total-title'>$ {curr_val:,.0f}</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='profit-row'>
            <span class='{get_cls(diff_all)}'>{get_sign(diff_all)}${abs(diff_all):,.0f}</span><span class='label-text'>全部時間</span>
            <span class='label-text'>‧</span>
            <span class='label-text'>今日</span><span class='{get_cls(diff_today)}'>{get_sign(diff_today)}${abs(diff_today):,.0f}</span>
        </div>
    """, unsafe_allow_html=True)

    # --- D. 折線圖與時間選擇器 ---
    if 'range' not in st.session_state: st.session_state.range = 'ALL'
    range_cols = st.columns(7)
    ranges = {'7D': 7, '1M': 30, '3M': 90, '6M': 180, 'YTD': 365, '1Y': 365, 'ALL': 9999}
    for i, r_name in enumerate(ranges.keys()):
        if range_cols[i].button(r_name): st.session_state.range = r_name

    cutoff = datetime.now() - timedelta(days=ranges[st.session_state.range])
    filtered_h = h_df[h_df['Date'] >= cutoff]
    if filtered_h.empty: filtered_h = h_df

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filtered_h['Date'], y=filtered_h[col_key],
        mode='lines', line=dict(color='#4ADE80', width=3),
        fill='tozeroy', fillcolor='rgba(74, 222, 128, 0.05)'
    ))
    fig.update_layout(
        height=240, margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, visible=False, range=[filtered_h[col_key].min()*0.98, filtered_h[col_key].max()*1.02])
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- E. 列表渲染函數 ---
    def render_card(name, sub, val, pct, color):
        pie_bg = f"conic-gradient({color} {pct*3.6}deg, #374151 0deg)"
        st.markdown(f"""
        <div class="custom-card">
            <div class="pie-icon-container" style="background: {pie_bg};"><div class="pie-icon-inner">{int(pct)}%</div></div>
            <div class="card-info"><div class="card-title">{name}</div><div class="card-sub">{sub}</div></div>
            <div class="card-value">$ {val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 根據視圖切換內容
    if st.session_state.view in ['Total', 'Cash']:
        st.write("🏦 資金明細")
        for _, r in c_df.iterrows():
            render_card(r['大項目'], r.get('子項目', ''), r['TWD'], (r['TWD']/total_cash*100 if total_cash>0 else 0), "#34D399")

    if st.session_state.view in ['Total', 'Invest']:
        st.write("🚀 投資表現")
        i_sorted = i_df.sort_values('市值TWD', ascending=False)
        for _, r in i_sorted.iterrows():
            render_card(r['名稱'], r['代號'], r['市值TWD'], (r['市值TWD']/total_inv*100 if total_inv>0 else 0), "#60A5FA")

except Exception as e:
    st.error(f"系統運行錯誤: {e}")
