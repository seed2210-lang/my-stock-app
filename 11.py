import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 앱 설정
st.set_page_config(page_title="❤❤❤❤❤❤❤❤❤❤❤❤❤❤", layout="wide")
st.title("🌼쩡아🌼의 주식공부 v1.5")

# 세션 상태 초기화
if 'candidates' not in st.session_state:
    st.session_state.candidates = []
if 'rt_results' not in st.session_state:
    st.session_state.rt_results = []

# 2. 기능 함수들
def run_scan(market_type):
    with st.spinner("💎 2,500개 중 보석 후보 찾는 중..."):
        df_list = fdr.StockListing(market_type).head(1000)
        found = []
        for row in df_list.itertuples():
            try:
                vol = fdr.DataReader(row.Code, (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'))['Volume']
                if vol.iloc[-1] > vol.iloc[:-1].mean() * 1.5:
                    found.append({'코드': row.Code, '종목명': row.Name})
            except: continue
            if len(found) >= 50: break
        st.session_state.candidates = found
        update_realtime_data() # 찾자마자 시세 한번 가져오기

def update_realtime_data():
    if not st.session_state.candidates:
        st.warning("먼저 '광역 스캔'을 눌러줘!")
        return
    
    with st.spinner("🌸 최신 시세 반영 중..."):
        new_results = []
        for item in st.session_state.candidates:
            try:
                df = fdr.DataReader(item['코드'], (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
                curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
                is_agg = curr > df['High'].iloc[-6:-1].max()
                new_results.append({
                    "Agg": is_agg, "종목명": item['종목명'], "코드": item['코드'],
                    "현재가": int(curr), "변동": int(curr - prev), "점수": 70 + (20 if is_agg else 0)
                })
            except: continue
        st.session_state.rt_results = new_results

# 3. 사이드바 컨트롤러
st.sidebar.header("🌷 선택")
market = st.sidebar.selectbox("어디를검색하까", ["KOSPI", "KOSDAQ"])
if st.sidebar.button("🔍 전 종목 광역 스캔"):
    run_scan(market)

if st.sidebar.button("🔄 현재 시세로 새로고침"):
    update_realtime_data()

# 4. 메인 화면 표시
if st.session_state.rt_results:
    df_res = pd.DataFrame(st.session_state.rt_results).sort_values(by="점수", ascending=False)
    df_res['순위'] = [f"💙 {i+1}" if r.Agg else f"{i+1}" for i, r in enumerate(df_res.itertuples())]

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🌻 정예 50 실시간 추적")
        def style_row(row):
            color = '#FF4B4B' if row['변동'] > 0 else '#1C83E1' if row['변동'] < 0 else 'white'
            return [f'color: {color}; font-weight: bold;' if c in ['종목명', '변동'] else '' for c in row.index]

        st.dataframe(df_res[['순위', '종목명', '현재가', '변동']].style.apply(style_row, axis=1), 
                     use_container_width=True, hide_index=True)
        
        selected_name = st.selectbox("종목 선택:", df_res['종목명'].tolist())
        sel_row = df_res[df_res['종목명'] == selected_name].iloc[0]
        st.metric(f"💎 {selected_name}", f"{sel_row['현재가']:,}원", f"{sel_row['변동']:,}원")

    with col2:
        st.subheader("🍀 타이밍 분석 차트")
        df_chart = fdr.DataReader(sel_row['코드'], (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d'))
        df_chart['MA5'] = df_chart['Close'].rolling(5).mean()
        df_chart['MA20'] = df_chart['Close'].rolling(20).mean()
        
        # 하트 시그널 로직
        df_chart['Buy'] = (df_chart['Close'] > df_chart['High'].shift(1).rolling(5).max()) & (df_chart['Volume'] > df_chart['Volume'].rolling(20).mean() * 1.2)
        df_chart['Sell'] = (df_chart['Close'] < df_chart['MA5']) & (df_chart['Close'].shift(1) >= df_chart['MA5'].shift(1))
        
        fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name="캔들")])
        
        # 💙 매수/❤️ 매도 하트 추가
        buy_idx = df_chart[df_chart['Buy']].index
        sell_idx = df_chart[df_chart['Sell']].index
        
        fig.add_trace(go.Scatter(x=buy_idx, y=df_chart.loc[buy_idx, 'Low'] * 0.98, mode='markers', marker=dict(symbol='star', size=12, color='royalblue'), name="매수"))
        fig.add_trace(go.Scatter(x=sell_idx, y=df_chart.loc[sell_idx, 'High'] * 1.02, mode='markers', marker=dict(symbol='star', size=12, color='#FF4B4B'), name="매도"))

        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=5, r=5, t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)
        st.write(f"⏰ 데이터 기준: {datetime.now().strftime('%H:%M:%S')}")
else:
    st.info("사이드바에서 스캔을 시작해 봐!")
