import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS：固定顏色與版面
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] { overflow-x: hidden !important; width: 100vw !important; }
    .block-container { padding: 1rem 1rem !important; max-width: 100vw !important; }
    .stApp { background-color: #0B0E14; color: #FFFFFF; }

    /* 修復膠囊顏色，防止白色塊 */
    div[data-testid="stSegmentedControl"] button {
        background-color: #1C212B !important;
        color: #9CA3AF !important;
        border-radius: 20px !important;
        height: 24px !important;
        font-size: 11px !important;
        border: none !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #00F2FE !important;
        color: #000000 !important;
    }

    .total-title { font-size: 36px; font-weight: 700; margin: 5px 0 0 0; }
    .profit-row { font-size: 13px; margin-bottom: 15px; }
    
    /* 盈虧顏色動態類別 */
    .text-pos { color: #00F2FE; font-weight: 600; }
    .text-neg { color: #FF4D4D; font-weight: 600; }

    .custom-card {
        background: #161B22; border-radius: 12px; padding: 12px;
        margin-bottom: 10px; display: flex; align-items: center; border: 1px solid #1F2937;
    }
    .card-info { flex-grow: 1; margin-left: 12px; }
    .card-value { text-align: right; font-weight: 700; font-size: 15px; }

    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. 資料與邏輯
try:
    # 這裡建議保留您原本讀取 Google Sheet 的函數 (load_data)
    # 為了演示連動效果，我簡化了計算邏輯
    rate = 32.5
    
    # 頂部導覽切換
    nav_selection = st.segmented_control(
        "View", ["總覽", "現金", "投資"], default="總覽", label_visibility="collapsed"
    )

    # 模擬數據：實際使用時請替換為 c_df, i_df, h_df 的計算值
    data_map = {
        "總覽": {"val": 2329010, "diff": 2035360, "key": "Total"},
        "現金": {"val": 1500000, "diff": 500000, "key": "Cash"},
        "投資": {"val": 829010, "diff": -12500, "key": "Invest"}  # 假設投資目前是虧損
    }
    
    selected = data_map[nav_selection]
    
    # 顯示大數字
    st.markdown(f"<div class='total-title'>$ {selected['val']:,.0f}</div>", unsafe_allow_html=True)

    # 盈虧數字變色邏輯
    p_color_class = "text-pos" if selected['diff'] >= 0 else "text-neg"
    p_symbol = "+" if selected['diff'] >= 0 else ""
    
    st.markdown(f"""
        <div class="profit-row">
            <span class="{p_color_class}">{p_symbol}{selected['diff']:,.0f}</span> 全部時間
        </div>
    """, unsafe_allow_html=True)

    # 圖表 (簡化演示)
    fig = go.Figure(go.Scatter(y=[1, 1.2, 0.9, 1.5], mode='lines', line=dict(color='#00F2FE', width=3)))
    fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 時間切換
    st.segmented_control("Range", ["7D", "1M", "3M", "ALL"], default="ALL", label_visibility="collapsed")

    # 下方卡片：條件式渲染
    st.markdown("<br>", unsafe_allow_html=True)
    
    if nav_selection in ["總覽", "現金"]:
        st.markdown("<div style='font-size:14px; color:#9CA3AF; margin-bottom:10px;'>● 現金資產</div>", unsafe_allow_html=True)
        # 這裡放入您 c_df 的迴圈
        st.markdown('<div class="custom-card"><div class="card-info"><b>國泰世華</b><br><small>活期存款</small></div><div class="card-value">$ 1,200,000</div></div>', unsafe_allow_html=True)

    if nav_selection in ["總覽", "投資"]:
        st.markdown("<div style='font-size:14px; color:#9CA3AF; margin-bottom:10px;'>● 投資項目</div>", unsafe_allow_html=True)
        # 這裡放入您 i_df 的迴圈
        st.markdown('<div class="custom-card"><div class="card-info"><b>台積電</b><br><small>TPE: 2330</small></div><div class="card-value">$ 829,010</div></div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error: {e}")
