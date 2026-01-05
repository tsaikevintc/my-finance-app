import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# 1. 頁面基礎設定
st.set_page_config(page_title="Insights Asset", layout="wide", initial_sidebar_state="collapsed")

# 2. 核心 CSS：打造卡片感與進度條
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* 仿 APP 卡片容器 */
    .asset-card {
        background-color: #161B22;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #58A6FF; /* 側邊裝飾條 */
    }
    
    /* 進度條容器 */
    .progress-bg {
        background-color: #30363D;
        border-radius: 5px;
        width: 100%;
        height: 6px;
        margin-top: 8px;
    }
    .progress-fill {
        height: 6px;
        border-radius: 5px;
    }
    
    /* 文字排版 */
    .item-name { font-size: 16px; font-weight: 500; }
    .item-value { float: right; font-family: 'Courier New', monospace; }
    .item-percent { font-size: 12px; color: #8B949E; margin-left: 5px; }
    
    /* 隱藏預設元件 */
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 讀取資料
ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
G_C, G_I = "526580417", "1335772092"

@st.cache_data(ttl=60)
def load_all():
    url = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    df_c = pd.read_csv(f"{url}&gid={G_C}")
    df_i = pd.read_csv(f"{url}&gid={G_I}")
    df_c.columns = df_c.columns.str.strip()
    df_i.columns = df_i.columns.str.strip()
    return df_c, df_i

try:
    c_df, i_df = load_all()
    with st.spinner('Syncing...'):
        rate = yf.Ticker("USDTWD=X").fast_info['last_price']
        tks = i_df['代號'].dropna().unique().tolist()
        pxs = yf.download(tks, period="1d", progress=False)['Close']
        p_map = pxs.iloc[-1].to_dict() if len(tks)>1 else {tks[0]: pxs.iloc[-1]}

    # 數據處理
    c_df['台幣金額'] = c_df.apply(lambda r: r['金額'] * (rate if r['幣別']=='USD' else 1), axis=1)
    total_cash = c_df['台幣金額'].sum()
    
    i_df['現價'] = i_df['代號'].map(p_map).fillna(i_df['買入成本'])
    i_df['市值TWD'] = i_df.apply(lambda r: (r['現價']*r['持有股數']) * (rate if r['幣別']=='USD' else 1), axis=1)
    total_inv = i_df['市值TWD'].sum()
    
    total_assets = total_cash + total_inv

    # --- UI 呈現 ---
    st.markdown("<h2 style='text-align:center;'>我的淨資產</h2>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#58A6FF;'>$ {total_assets:,.0f}</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # A. 流動資金摺疊面板
    with st.expander(f"🏦 流動資金 (佔 {(total_cash/total_assets*100):.1f}%)", expanded=False):
        st.markdown(f"### 總額: $ {total_cash:,.0f}")
        for _, row in c_df.iterrows():
            pct = (row['台幣金額'] / total_cash) * 100
            st.markdown(f"""
                <div class="asset-card" style="border-left-color: #39FF14;">
                    <span class="item-name">{row['大項目']}</span>
                    <span class="item-value">$ {row['台幣金額']:,.0f}</span>
                    <div class="item-percent">{pct:.1f}%</div>
                    <div class="progress-bg"><div class="progress-fill" style="width: {pct}%; background-color: #39FF14;"></div></div>
                </div>
            """, unsafe_allow_html=True)

    # B. 投資部位摺疊面板
    with st.expander(f"📈 投資組合 (佔 {(total_inv/total_assets*100):.1f}%)", expanded=False):
        st.markdown(f"### 總額: $ {total_inv:,.0f}")
        # 依市值排序
        i_sorted = i_df.sort_values('市值TWD', ascending=False)
        for _, row in i_sorted.iterrows():
            pct = (row['市值TWD'] / total_inv) * 100
            # 根據損益決定顏色
            profit_color = "#00FF7F" if (row['現價'] - row['買入成本']) >= 0 else "#FF4B4B"
            st.markdown(f"""
                <div class="asset-card" style="border-left-color: {profit_color};">
                    <span class="item-name">{row['名稱']} ({row['代號']})</span>
                    <span class="item-value">$ {row['市值TWD']:,.0f}</span>
                    <div class="item-percent">{pct:.1f}% ‧ 股數: {row['持有股數']}</div>
                    <div class="progress-bg"><div class="progress-fill" style="width: {pct}%; background-color: {profit_color};"></div></div>
                </div>
            """, unsafe_allow_html=True)

    # C. 視覺化分析 (保留圓餅圖供快速參考)
    st.markdown("---")
    tabs = st.tabs(["資產分配", "持股比例"])
    with tabs[0]:
        fig = px.pie(values=[total_cash, total_inv], names=['現金', '投資'], hole=0.6, color_discrete_sequence=['#39FF14', '#58A6FF'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"資料讀取錯誤: {e}")
