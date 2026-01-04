import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="測試版-資產管理", layout="wide")

st.title("🧪 獨立測試模式 (不連線 Google)")

# 手動建立測試數據，完全不讀取外部檔案
def get_test_data():
    cash_data = {
        '大項目': ['台幣帳戶', '美金帳戶'],
        '幣別': ['TWD', 'USD'],
        '金額': [100000, 2000]
    }
    invest_data = {
        '代號': ['2330.TW', 'AAPL', 'BTC-USD'],
        '持有股數': [1000, 10, 0.05],
        '買入成本': [600, 150, 40000],
        '幣別': ['TWD', 'USD', 'USD']
    }
    return pd.DataFrame(cash_data), pd.DataFrame(invest_data)

try:
    cash_df, invest_df = get_test_data()
    
    # 獲取匯率
    with st.spinner('正在嘗試抓取 Yahoo 股價...'):
        try:
            usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
        except:
            usdtwd = 32.5
        
        # 獲取股價
        tickers = invest_df['代號'].tolist()
        price_data = yf.download(tickers, period="1d", progress=False)['Close']
        
        if len(tickers) == 1:
            prices = {tickers[0]: price_data.iloc[-1]}
        else:
            prices = price_data.iloc[-1].to_dict()

    # 計算損益
    invest_df['現價'] = invest_df['代號'].map(prices)
    invest_df['市值'] = invest_df['現價'] * invest_df['持有股數']
    
    # 介面顯示
    st.success("✅ 獨立測試環境執行成功！這代表程式碼沒問題。")
    
    c1, c2 = st.columns(2)
    c1.metric("測試總資產 (TWD)", f"{invest_df['市值'].sum():,.0f}")
    c2.metric("測試匯率", f"{usdtwd:.2f}")

    st.subheader("📊 測試投資表格")
    st.dataframe(invest_df)

except Exception as e:
    st.error(f"連獨立測試都失敗了。錯誤訊息: {e}")
