import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# 1. 앱 설정
st.set_page_config(page_title="❤❤❤❤❤❤❤❤❤❤❤❤❤", layout="wide")
st.title(" 🌼쩡아🌼의 주식공부 v1.4.3")

# 세션 상태 초기화 (데이터 보존)
if 'candidates' not in st.session_state:
    st.session_state.candidates = []
if 'hunting' not in st.session_state:
    st.session_state.hunting = False

# 2. 광역 스캔 (버튼 누를 때만 실행)
def run_scan(market_type):
    with st.spinner("💎 2,500개 종목 중 보석을 찾는 중..."):
        df_list = fdr.StockListing(market_type).head(1000) # 렉 방지 상위 1000개
        found = []
        for row in df_list.itertuples():
            try:
                # 최근 거래량 터진 후보군만 1차 선발
                vol_check = fdr.DataReader(row.Code, (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'))['Volume']
                if vol_check.iloc[-1] > vol_check.iloc[:-1].mean() * 1.5:
                    found.append({'코드': row.Code, '종목명': row.Name})
            except: continue
            if len(found) >= 50: break # 정예 50개만
        st.session_state.candidates = found
        st.session_state.hunting = True

# 3. 사이드바 (컨트롤러)
market = st.sidebar.selectbox("사냥터 선택", ["KOSPI", "KOSDAQ"])
if st.sidebar.button("🔍 전 종목 광역 스캔 시작"):
    run_scan(market)

# 4. 메인 화면 (마법의 지우개 컨테이너)
main_container = st.empty()

with main_container.container():
    if st.session_state.candidates:
        # 실시간 데이터 가져오기
        rt_results = []
        for item in st.session_state.candidates:
            try:
                df = fdr.DataReader(item['코드'], (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
                curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
                is_agg = curr > df['High'].iloc[-6:-1].max() # 공격적 타점
                rt_results.append({
                    "Agg": is_agg, "종목명": item['종목명'], "코드": item['코드'],
                    "현재가": int(curr), "변동": int(curr - prev), "점수": 70 + (20 if is_agg else 0)
                })
            except: continue
        
        df_res = pd.DataFrame(rt_results).sort_values(by="점수", ascending=False)
        df_res['순위'] = [f"💙 {i+1}" if r.Agg else f"{i+1}" for i, r in enumerate(df_res.itertuples())]

        # 화면 분할
        col1, col2 = st.columns([1, 1.2])

        with col1:
            st.subheader("🌸실시간 정예 50종목")
            
            def style_row(row):
                color = '#FF4B4B' if row['변동'] > 0 else '#1C83E1' if row['변동'] < 0 else 'white'
                return [f'color: {color}; font-weight: bold;' if c in ['종목명', '변동'] else '' for c in row.index]

            st.dataframe(df_res[['순위', '종목명', '현재가', '변동']].style.apply(style_row, axis=1), 
                         use_container_width=True, hide_index=True)
            
            # 선택 박스 (데이터 변화를 즉각 반영하기 위해 key 설정)
            selected_name = st.selectbox("집중 분석 종목:", df_res['종목명'].tolist(), key="stock_selector")
            sel_row = df_res[df_res['종목명'] == selected_name].iloc[0]
            
            st.metric(f"💎 {selected_name}", f"{sel_row['현재가']:,}원", f"{sel_row['변동']:,}원")

        with col2:
            st.subheader("🍀타이밍 분석 차트")
            df_chart = fdr.DataReader(sel_row['코드'], (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d'))
            
            # 이동평균선 계산
            df_chart['MA5'] = df_chart['Close'].rolling(5).mean()
            df_chart['MA20'] = df_chart['Close'].rolling(20).mean()
            
            # 💙 블루 하트 (매수) 타점 계산: 공격적 돌파 시
            df_chart['Buy_Signal'] = (df_chart['Close'] > df_chart['High'].shift(1).rolling(5).max()) & (df_chart['Volume'] > df_chart['Volume'].rolling(20).mean() * 1.2)
            buy_pts = df_chart[df_chart['Buy_Signal']]

            # ❤️ 레드 하트 (매도) 타점 계산: 5일 이평선 이탈 시 (가장 안전한 로직)
            df_chart['Sell_Signal'] = (df_chart['Close'] < df_chart['MA5']) & (df_chart['Close'].shift(1) >= df_chart['MA5'].shift(1))
            sell_pts = df_chart[df_chart['Sell_Signal']]

            fig = go.Figure()
            
            # 캔들 차트
            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name="캔들"))
            
            # 이동평균선
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='orange', width=1), name="5일선"))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='red', width=1), name="20일선"))
            
            # 💙 블루 하트 (매수 표시) - 적당한 금액으로 표시
            fig.add_trace(go.Scatter(x=buy_pts.index, y=buy_pts['Low'] * 0.98, mode='markers+text', 
                                     marker=dict(symbol='star', size=12, color='royalblue'),
                                     text=[f"💙\n{int(p):,}원" for p in buy_pts['Close']], textposition="bottom center", name="매수타점"))

            # ❤️ 레드 하트 (매도 표시)
            fig.add_trace(go.Scatter(x=sell_pts.index, y=sell_pts['High'] * 1.02, mode='markers+text', 
                                     marker=dict(symbol='star', size=12, color='#FF4B4B'),
                                     text="❤️", textposition="top center", name="매도타점"))

            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.bar_chart(df_chart['Volume'], height=150)
            
        st.write(f"⏰ 마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.info("먼저 사이드바에서 '광역 스캔'을 눌러서 보석 후보를 뽑아줘!")

# 10초 대기 후 새로고침
if st.session_state.hunting:
    time.sleep(10)
    st.rerun()