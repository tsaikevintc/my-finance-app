import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# 1. 頁面設定
st.set_page_config(page_title="Insights", layout="wide", initial_sidebar_state="collapsed")

# 2. 數據讀取
@st.cache_data(ttl=300)
def fetch_data():
    ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"
    G_C, G_H = "526580417", "857913551"
    base = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"
    c = pd.read_csv(f"{base}&gid={G_C}")
    h = pd.read_csv(f"{base}&gid={G_H}")
    for df in [c, h]: df.columns = df.columns.str.strip()
    h['Date'] = pd.to_datetime(h['Date'].str.replace('上午', 'AM').str.replace('下午', 'PM'), errors='coerce', format='mixed')
    h = h.dropna(subset=['Date']).sort_values('Date')
    return c, h

# 3. 基礎 CSS
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0B0E14 !important; }
    .block-container { padding: 1.2rem 1rem !important; }
    .t-val { font-size: 38px; font-weight: 700; color: white; margin-top: 5px; }
    .p-row { font-size: 13px; color: #8B949E; margin-bottom: 15px; }
    #MainMenu, header, footer { visibility: hidden; }
    
    /* 隱藏用於接收 JS 數值的輸入框 */
    div[data-testid="stTextInput"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

try:
    c_df, h_df = fetch_data()
    
    # 4. 總額計算
    t_total = (c_df['金額'] * c_df['幣別'].apply(lambda x: 32.5 if x=='USD' else 1)).sum() + 829010

    # 5. 頂部標題渲染
    st.markdown(f"<div class='t-val'>$ {t_total:,.0f}</div>", unsafe_allow_html=True)

    # 6. 核心：自定義橫向滑動膠囊 (純 HTML + JS)
    # 我們用一個隱藏的 text_input 來接收點擊的區間
    selected_range = st.text_input("hidden_range", value="ALL", key="range_state")

    # 手寫組件：絕對不會有白色底座
    capsule_html = f"""
    <div id="capsule-root" style="display: flex; overflow-x: auto; gap: 8px; white-space: nowrap; padding: 10px 0; scrollbar-width: none;">
        {" ".join([f'<div class="cap" onclick="selectRange(\'{r}\')" id="cap-{r}" style="padding: 6px 18px; border-radius: 20px; border: 1px solid {"#00F2FE" if selected_range==r else "#30363D"}; color: {"#00F2FE" if selected_range==r else "#9CA3AF"}; background: {"rgba(0,242,254,0.1)" if selected_range==r else "#1C212B"}; font-size: 13px; cursor: pointer; flex-shrink: 0; font-weight: {"700" if selected_range==r else "500"}; transition: 0.2s;">{r}</div>' for r in ["7D", "1M", "3M", "6M", "YTD", "1Y", "ALL"]])}
    </div>

    <script>
    function selectRange(val) {{
        // 找到 Streamlit 的隱藏輸入框並填值
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        for (let input of inputs) {{
            if (input.parentElement.parentElement.textContent.includes("hidden_range")) {{
                // 觸發原生事件讓 Streamlit 抓到變更
                let lastValue = input.value;
                input.value = val;
                let event = new Event('input', {{ bubbles: true }});
                event.simulated = true;
                let tracker = input._valueTracker;
                if (tracker) {{ tracker.setValue(lastValue); }}
                input.dispatchEvent(event);
                
                // 模擬按下 Enter 觸發更新
                input.dispatchEvent(new KeyboardEvent('keydown', {{ 'key': 'Enter', 'bubbles': true }}));
                break;
            }}
        }}
    }}
    </script>
    """
    components.html(capsule_html, height=55)

    # 7. 數據過濾邏輯
    now = h_df['Date'].max()
    f_map = {
        "7D": now - timedelta(days=7), "1M": now - timedelta(days=30),
        "3M": now - timedelta(days=90), "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365), "YTD": datetime(now.year, 1, 1),
        "ALL": h_df['Date'].min()
    }
    filtered_h = h_df[h_df['Date'] >= f_map.get(selected_range, h_df['Date'].min())]

    # 8. 盈虧與圖表渲染
    diff_p = t_total - filtered_h['Total'].iloc[0] if not filtered_h.empty else 0
    diff_t = t_total - h_df['Total'].iloc[-1]
    
    def fmt(v):
        cl = "#00F2FE" if v >= 0 else "#FF4D4D"
        return f'<span style="color:{cl}; font-weight:700;">{"+" if v >= 0 else ""}{v:,.0f}</span>'
    
    st.markdown(f'<div class="p-row">{fmt(diff_p)} {selected_range}區間總盈虧 ‧ 今日 {fmt(diff_t)}</div>', unsafe_allow_html=True)

    fig = go.Figure(go.Scatter(x=filtered_h['Date'], y=filtered_h['Total'], mode='lines', line=dict(color='#00F2FE', width=3), fill='tozeroy', fillcolor='rgba(0,242,254,0.05)'))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 9. 卡片區
    st.markdown("<div style='color:#8B949E; font-size:14px; margin:20px 5px 10px;'>● 現金資產</div>", unsafe_allow_html=True)
    for _, r in c_df.iterrows():
        twd = r['金額'] * (32.5 if r['幣別']=='USD' else 1)
        st.markdown(f"""
            <div style="background:#161B22; border-radius:12px; padding:14px; margin-bottom:12px; border:1px solid #30363D; display:flex; align-items:center;">
                <div style="flex-grow:1;"><div style="color:white; font-weight:600;">{r['子項目']}</div><div style="color:#8B949E; font-size:11px;">{r['大項目']}</div></div>
                <div style="color:white; font-weight:700;">$ {twd:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"系統錯誤: {e}")
