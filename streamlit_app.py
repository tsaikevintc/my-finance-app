# --- 4. 頂部佈局：金額 + 膠囊按鈕 (強制橫排) ---
if 'view' not in st.session_state: st.session_state.view = 'Total'

v_map = {'Total': total_assets, 'Cash': total_cash, 'Invest': total_inv}
curr_val = v_map[st.session_state.view]

# 使用 HTML 建立一個 Flex 容器，讓左邊數字、右邊按鈕群組強制並排
st.markdown(f"""
    <div style="display: flex; align-items: baseline; justify-content: space-between; width: 100%;">
        <div class='total-title'>$ {curr_val:,.0f}</div>
        <div style="display: flex; gap: 4px;">
            <div id="btn-group"></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 為了讓 Streamlit 捕捉點擊，按鈕仍需用 st.button，但我們用 columns 緊湊排列並透過 CSS 抵銷縮放
btn_space1, btn_space2 = st.columns([1.5, 1]) # 創造出右側空間
with btn_space2:
    cols = st.columns(3)
    if cols[0].button("總覽"): st.session_state.view = 'Total'
    if cols[1].button("現金"): st.session_state.view = 'Cash'
    if cols[2].button("投資"): st.session_state.view = 'Invest'

# 強制修正 CSS 抵消 Streamlit 的手機端自動堆疊
st.markdown("""
<style>
    /* 強制 columns 在手機上不換行 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    
    /* 讓數字與按鈕群組靠得更近 */
    [data-testid="column"]:nth-child(1) { flex: 2 !important; }
    [data-testid="column"]:nth-child(2) { flex: 1.2 !important; }

    /* 進一步縮小膠囊按鈕 */
    div.stButton > button {
        width: 100% !important;
        min-width: 42px !important;
        height: 20px !important;
        padding: 0px 2px !important;
        font-size: 9px !important;
        margin-top: -50px; /* 向上移動對齊數字 */
    }
</style>
""", unsafe_allow_html=True)
