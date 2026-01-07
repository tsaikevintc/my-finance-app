import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="Insights Asset", layout="wide", initial_sidebar_state="collapsed")

# 2. 進階 CSS
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
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
    .custom-card {
        background-color: #161B22; border-radius: 16px;
        padding: 12px 16px; margin-bottom: 10px;
        display: flex; align-items: center; border: 1px solid #1F2937;
    }
    .card-info { flex-grow: 1; }
    .card-title { font-size: 15px; font-weight: 600; color: #F3F4F6; }
    .card-sub { font-size: 11px; color: #9CA3AF; }
    .card-value { text-align: right; font-weight: 700; font-size: 16px; color: #F3F4F6; }
    .stButton > button {
        border-radius: 20px; border: 1px solid #374151;
        background-color: #1F2937; color: #9CA3AF; font-size: 13px; height: 35px;
    }
    .stButton > button:hover { border-color: #60A5FA; color: white; }
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 輔助函式：轉換 yfinance 代號格式
def fix_ticker(t):
    t = str(t).strip()
    if 'TPE:' in t: return t.replace('TPE:', '') + '.TW'
    if 'NASDAQ:' in t: return t.replace('NASDAQ:', '')
    if 'NYSE:' in t: return t.replace('NYSE:', '')
    if 'BTCUSD' in t: return 'BTC-USD'
    return t

# 4. 資料讀取
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I, G_H = "526580417", "1335772092", "857913551"

@st.cache_data(ttl=300)
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
    
    # 取得匯率與股價 (增加安全檢查)
    try:
        rate = yf.Ticker("USDTWD=X").fast_info.get('last_price', 32.5)
    except:
        rate = 32.5
    
    # 計算現金 [cite: 3]
    c_df['TWD'] = c_df.apply(lambda r: float(r['金額']) * (rate if r.get('幣別')=='USD' else 1), axis=1)
    total_cash = c_df['TWD'].sum()
    
    # 計算投資 
    i_df['yf_ticker'] = i_df['代號'].apply(fix_ticker)
    tks = i_df['yf_ticker'].unique().tolist()
    
    prices = {}
    if tks:
        data = yf.download(tks, period="1d", progress=False)['Close']
        for t in tks:
            try:
                # 預防 index out of bounds
                val = data[t].iloc[-1] if isinstance(data, pd.DataFrame) else data.iloc[-1]
                if pd.isna(val): val = 0
                prices[t] = val
            except:
                prices[t] = 0

    i_df['市值TWD'] = i_df.apply(lambda r: (prices.get(r['yf_ticker'], r['買入成本']) * r['持有股數']) * (rate if r.get('幣別')=='USD' else 1), axis=1)
    total_inv = i_df['市值TWD'].sum()
    total_assets = total_cash + total_inv

    # --- UI 視圖切換 ---
    if 'view' not in st.session_state: st.session_state.view = 'Total'
    st.markdown("<h3 style='text-align: center; margin-bottom: 10px;'>Insights</h3>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    if b1.button("✨ 淨資產", use_container_width=True): st.session_state.view = 'Total'
    if b2.button("💵 流動資金", use_container_width=True): st.session_state.view = 'Cash'
    if b3.button("📈 投資組合", use_container_width=True): st.session_state.view = 'Invest'

    # --- 折線圖  ---
    v_conf = {'Total': ('Total', '#60A5FA'), 'Cash': ('Cash', '#34D399'), 'Invest': ('Invest', '#F472B6')}
    col_name, theme_color = v_conf[st.session_state.view]
    
    if not h_df.empty and col_name in h_df.columns:
        h_df['Date'] = pd.to_datetime(h_df['Date'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=h_df['Date'], y=h_df[col_name], mode='lines', line=dict(color=theme_color, width=3), fill='tozeroy', fillcolor=f'rgba({int(theme_color[1:3],16)},{int(theme_color[3:5],16)},{int(theme_color[5:7],16)},0.1)'))
        fig.update_layout(height=220, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False), yaxis=dict(visible=False))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    display_val = total_assets if col_name=='Total' else (total_cash if col_name=='Cash' else total_inv)
    st.markdown(f"<h1 style='text-align:center; margin-top:-25px;'>$ {display_val:,.0f}</h1>", unsafe_allow_html=True)

    def render_item(name, sub, val, pct, color):
        pie_bg = f"conic-gradient({color} {pct*3.6}deg, #374151 0deg)"
        st.markdown(f"""
        <div class="custom-card">
            <div class="pie-icon-container" style="background: {pie_bg};"><div class="pie-icon-inner">{int(pct)}%</div></div>
            <div class="card-info"><div class="card-title">{name}</div><div class="card-sub">{sub}</div></div>
            <div class="card-value">$ {val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.view in ['Total', 'Cash']:
        st.write("🏦 資金明細")
        for _, r in c_df.iterrows():
            render_item(r['大項目'], r.get('子項目', ''), r['TWD'], (r['TWD']/total_cash*100 if total_cash>0 else 0), "#34D399")

    if st.session_state.view in ['Total', 'Invest']:
        st.write("🚀 投資組合")
        for _, r in i_df.sort_values('市值TWD', ascending=False).iterrows():
            render_item(r['名稱'], r['代號'], r['市值TWD'], (r['市值TWD']/total_inv*100 if total_inv>0 else 0), "#60A5FA")

except Exception as e:
    st.error(f"系統運行錯誤: {e}")
