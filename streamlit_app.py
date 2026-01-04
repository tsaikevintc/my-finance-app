import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="診斷模式-資產管理", layout="wide")

# 你的 GID
GID_CASH = "526580417"
GID_INVEST = "1335772092"
SHEET_ID = "1DLRxWZmQhSzmjCOOvv-cCN3BeChb94sD6rFHimuXjs4"

# 換一種更直接的 CSV 匯出網址格式
def get_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

@st.cache_data(ttl=60)
def fetch_raw_data(gid):
    url = get_url(gid)
    df = pd.read_csv(url)
    return df

st.title("🔍 系統診斷與資產管理")

try:
    # 嘗試讀取資料
    cash_raw = fetch_raw_data(GID_CASH)
    invest_raw = fetch_raw_data(GID_INVEST)

    # --- 診斷面板 ---
    with st.expander("🛠️ 點擊展開系統診斷資訊"):
        st.write("現金分頁讀取到的欄位：", list(cash_raw.columns))
        st.write("投資分頁讀取到的欄位：", list(invest_raw.columns))
        st.write("現金分頁前兩行數據：", cash_raw.head(2))
        st.write("投資分頁前兩行數據：", invest_raw.head(2))

    # --- 強制欄位名稱對齊 ---
    # 如果標題有空格或格式問題，我們強制重新命名
    def clean_df(df):
        df.columns = [str(c).strip() for c in df.columns]
        return df

    cash_df = clean_df(cash_raw)
    invest_df = clean_df(invest_raw)

    # --- 核心邏輯 (簡單化) ---
    usdtwd = 32.5 # 先給預設值，避免 yfinance 報錯卡住
    try:
        usdtwd = yf.Ticker("USDTWD=X").fast_info['last_price']
    except:
        pass

    # 檢查是否有『代號』欄位
    if '代號' in invest_df.columns:
        st.success("✅ 成功找到『代號』欄位！")
        
        # 顯示簡單數據
        st.subheader("💰 現金資產概況")
        st.table(cash_df)
        
        st.subheader("📈 投資清單概況")
        st.table(invest_df)
        
        st.metric("美金匯率參考", f"{usdtwd:.2f}")
    else:
        st.error("❌ 依然找不到『代號』欄位")
        st.write("目前的標題清單為：", list(invest_df.columns))

except Exception as e:
    st.error("🚨 讀取失敗：Google 試算表連線中斷")
    st.info(f"技術錯誤：{e}")
    st.markdown("""
    ### 解決建議：
    1. **檢查試算表權限**：請再次確認試算表的 **「共用」** 是否設定為 **「知道連結的任何人」** 且為 **「檢視者」**。
    2. **重新發佈**：在試算表中，點擊 **檔案 > 共用 > 發佈到網路**，選擇 **整個文件** 並格式選 **CSV**。這有助於外部連結讀取。
    """)
