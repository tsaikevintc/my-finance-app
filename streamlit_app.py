import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="資產管理APP", layout="wide")

# 你的試算表網址與 GID
BASE_URL = "https://docs.google.com/spreadsheets/d/1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4/export?format=csv"
GID_CASH = "526580417"
GID_INVEST = "1335772092"

def safe_float(val):
    try:
        return float(str(val).replace(',', '').strip())
    except:
        return 0.0

@st.cache_data(ttl=300)
def get_data():
    # 讀取資料
    df_c = pd.read_csv(f"{BASE_URL}&gid={GID_CASH}")
    df_i = pd.read_csv(f"{BASE_URL}&gid={GID_INVEST}")
    return df_c, df_i

st.title("💰 我的個人資產管理")

try:
    cash_raw, invest_raw = get_data()

    # --- 強力偵錯區：如果還是出錯，這一段會幫我們抓出原因 ---
    if st.checkbox("顯示原始資料(除錯用)"):
        st.write("現金分頁前兩列：", cash_raw.head(2))
        st.write("投資分頁前兩列：", invest_raw.head(2))

    # --- 取得匯率 ---
    try:
        usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
    except:
        usdtwd = 32.5

    # --- 處理現金 (根據你的表格順序：第3欄是幣別, 第4欄是金額) ---
    # 我們不靠名稱，靠「位置」 (iloc)
    total_cash_twd = 0
    for i in range(len(cash_raw)):
        row = cash_raw.iloc[i]
        curr = str(row.iloc[2]).strip().upper() # 幣別
        amt = safe_float(row.iloc[3])           # 金額
        if curr == 'USD':
            total_cash_twd += amt * usdtwd
        else:
            total_cash_twd += amt

    # --- 處理投資 (根據你的表格順序：第2欄是代號, 第4欄是股數, 第5欄是成本, 第6欄是幣別) ---
    invest_list = []
    tickers = []
    
    for i in range(len(invest_raw)):
        row = invest_raw.iloc[i]
        symbol = str(row.iloc[1]).strip() # 代號
        if symbol and symbol != 'nan':
            tickers.append(symbol)
            invest_list.append({
                "代號": symbol,
                "名稱": row.iloc[2],
                "持有股數": safe_float(row.iloc[3]),
                "買入成本": safe_float(row.iloc[4]),
                "幣別": str(row.iloc[5]).strip().upper()
            })
    
    # 批次抓取股價
    prices = {}
    if tickers:
        try:
            p_data = yf.download(tickers, period="1d", progress=False)['Close']
            if len(tickers) == 1:
                prices = {tickers[0]: p_data.iloc[-1]}
            else:
                prices = p_data.iloc[-1].to_dict()
        except:
            pass

    # 計算損益
    final_invest_df = pd.DataFrame(invest_list)
    final_invest_df['現價'] = final_invest_df['代號'].map(prices).fillna(final_invest_df['買入成本'])
    final_invest_df['市值'] = final_invest_df['現價'] * final_invest_df['持有股數']
    final_invest_df['損益'] = (final_invest_df['現價'] - final_invest_df['買入成本']) * final_invest_df['持有股數']

    total_invest_twd = 0
    for _, r in final_invest_df.iterrows():
        m_val = r['市值']
        if r['幣別'] == 'USD':
            total_invest_twd += m_val * usdtwd
        else:
            total_invest_twd += m_val

    # --- 介面 ---
    col1, col2, col3 = st.columns(3)
    col1.metric("總淨資產 (TWD)", f"{total_cash_twd + total_invest_twd:,.0f}")
    col2.metric("現金資產", f"{total_cash_twd:,.0f}")
    col3.metric("美金匯率", f"{usdtwd:.2f}")

    st.subheader("📊 投資清單")
    st.dataframe(final_invest_df, use_container_width=True)

except Exception as e:
    st.error(f"偵測到異常，請勾選下方的『顯示原始資料』並截圖給我，這能幫助我修好它。")
    st.info(f"錯誤代碼: {e}")
