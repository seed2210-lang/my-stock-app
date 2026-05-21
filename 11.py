import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
import json
import os
import numpy as np

#1 --- 📱 모바일 최적화 및 스타일 ---
st.set_page_config(page_title="💰JJ-Money (슈퍼노바 풀버전)💰", layout="centered")
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3.5em; font-size: 16px; font-weight: bold; border-radius: 12px; margin-bottom: 8px; background-color: #2c2f33; color: white; border: 1px solid #d4af37; }
    .main-title { text-align: center; color: #d4af37; font-size: 24px; font-weight: bold; margin-bottom: 20px;}
    .stock-card { background: #1c2128; padding: 15px; border-radius: 12px; border-left: 5px solid #d4af37; margin-bottom: 12px; }
    .rank-badge { background: #d4af37; color: black; padding: 5px 12px; border-radius: 8px; font-size: 16px; font-weight: bold; }
    .price-curr { color: #ffffff; font-weight: bold; font-size: 18px; }
    .price-target { color: #ff4b4b; font-weight: bold; font-size: 18px; } 
    .price-stop { color: #4b8bff; font-weight: bold; font-size: 18px; }   
    .reason-box { background: #0d1117; padding: 10px; border-radius: 8px; border: 1px dashed #8b949e; margin-top: 10px; font-size: 13px; color: #e6edf3; }
    </style>
    """, unsafe_allow_html=True)

DATA_FILE = "jj_mobile_v6.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

#2 --- 🔐 보안 시스템 ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    st.markdown("<p class='main-title'>🌹오늘도짜쟌🌹</p>", unsafe_allow_html=True)
    pw = st.text_input("비밀번호(헤헿)", type="password")
    if st.button("입장하기 🚀"):
        if pw == "6006":
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("비밀번호가 틀렸어!")
    st.stop()

if 'my_stocks' not in st.session_state: st.session_state.my_stocks = load_data()

today_str = datetime.now().strftime('%Y-%m-%d')

#3 --- 🎯 슈퍼노바 엔진 ---
@st.cache_data(ttl=3600)
def get_all_stocks():
    try:
        df1 = fdr.StockListing('KOSPI')[['Code', 'Name']]
        df2 = fdr.StockListing('KOSDAQ')[['Code', 'Name']]
        return pd.concat([df1, df2]).dropna().sample(frac=1).reset_index(drop=True)
    except:
        return pd.DataFrame({'Code': ['005930', '000660', '042700'], 'Name': ['삼성전자', 'SK하이닉스', '한미반도체']})

def find_supernova(item):
    try:
        df = fdr.DataReader(item['Code'], (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
        if len(df) < 40: return None
        
        c = df['Close']; v = df['Volume']; h = df['High']; l = df['Low']
        curr_price = int(c.iloc[-1])
        prev_price = int(c.iloc[-2])
        
        if curr_price < 1000: return None
        
        vol_20ma = v.iloc[-21:-1].mean()
        curr_vol = v.iloc[-1]
        
        vol_burst = curr_vol > (vol_20ma * 2.5)
        strong_close = (curr_price - l.iloc[-1]) / (h.iloc[-1] - l.iloc[-1] + 0.001) > 0.75
        up_trend = curr_price > prev_price * 1.02
        
        if vol_burst and strong_close and up_trend:
            power_score = round((curr_vol / vol_20ma) + ((curr_price - l.iloc[-1]) / (h.iloc[-1] - l.iloc[-1] + 0.001) * 5), 2)
            target = int(curr_price * 1.12)
            stop = int(prev_price * 0.98)
            
            if power_score > 8:
                eta = "🔥 1~2일 내 즉각 폭발"
                reason = "평소보다 거래량이 엄청나게 터지면서 물량을 싹쓸이했어! 종가까지 밀리지 않고 꽉 찬 양봉을 만든 걸 보면 세력이 오늘 작정하고 들어온 거야. 내일 아침 갭상승 확률이 아주 높아!"
            else:
                eta = "📡 3~5일 스윙 매집"
                reason = "의미 있는 거래량이 들어오면서 추세를 살려놨어. 매물대를 한 번 소화했기 때문에 며칠 횡보하다가 위로 쏠 준비를 마친 차트야."

            return {"code": item['Code'], "name": item['Name'], "curr": curr_price, "target": target, "stop": stop, "score": power_score, "eta": eta, "reason": reason, "date": today_str}
        return None
    except: return None

#4 --- 📱 메인 UI (찾기, 급등, 보물함) ---
all_s = get_all_stocks()
tab1, tab2, tab3 = st.tabs(["🔍 종목찾기", "🚀 슈퍼노바(급등)", "💰 보물함"])

with tab1:
    s_word = st.text_input("종목명 검색", placeholder="예: 한미반도체, 삼성전자")
    if s_word and not all_s.empty:
        found = all_s[all_s['Name'].str.contains(s_word, case=False, na=False)]
        if not found.empty:
            for _, row in found.head(3).iterrows():
                res = find_supernova({'Code': row['Code'], 'Name': row['Name']})
                st.markdown(f"""
                <div class='stock-card'>
                    <h3>{row['Name']}</h3>
                    <p style='color:#8b949e;'>검색한 종목을 지갑에 바로 추가할 수 있어!</p>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                in_p = c1.number_input("매수가", key=f"p_{row['Code']}", value=int(fdr.DataReader(row['Code']).iloc[-1]['Close']))
                in_q = c2.number_input("수량(주)", key=f"q_{row['Code']}", value=1, min_value=1)
                
                if st.button("⭐ 지갑에 즉시 기록", key=f"btn_{row['Code']}"):
                    st.session_state.my_stocks.append({"name": row['Name'], "code": row['Code'], "curr": in_p, "target": int(in_p*1.1), "stop": int(in_p*0.95), "status": "BOUGHT", "buy_price": in_p, "qty": in_q, "sell_date": today_str})
                    save_data(st.session_state.my_stocks); st.toast("지갑 기록 완료! 🚀"); st.rerun()
        else: st.error("종목을 못 찾겠어!")

with tab2:
    st.write("🔥 **가장 강한 세력 매집주 찾기**")
    if st.button("🚀 슈퍼노바 스캔 시작"):
        results = []
        subset = all_s.head(400) 
        p_bar = st.progress(0, text="폭발 에너지 스캔 중... 위이잉")
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            futures = [ex.submit(find_supernova, {'Code': r.Code, 'Name': r.Name}) for r in subset.itertuples()]
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                r = f.result()
                if r: results.append(r)
                if i % 20 == 0: p_bar.progress((i+1)/len(subset))
        p_bar.empty()
        
        if results:
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            st.session_state.supernova_results = results
        else:
            st.session_state.supernova_results = []

    if 'supernova_results' in st.session_state:
        if st.session_state.supernova_results:
            for rank, r in enumerate(st.session_state.supernova_results[:10], 1):
                with st.expander(f"[{rank}위] {r['name']} (점수: {r['score']}) - {r['curr']:,}원"):
                    st.markdown(f"""
                    <div class='stock-card' style='border-left:none; padding:5px;'>
                        올라갈 시세(빨강): <span class='price-target'>{r['target']:,}원</span><br>
                        손절할 시세(파랑): <span class='price-stop'>{r['stop']:,}원</span><br>
                        예상 도달 시간: <b>{r['eta']}</b>
                        <div class='reason-box'><b>💡 왜 오를까?</b><br>{r['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    p_val = c1.number_input("매수가", key=f"p_sn_{rank}_{r['code']}", value=r['curr'])
                    q_val = c2.number_input("수량(주)", key=f"q_sn_{rank}_{r['code']}", value=1, min_value=1)
                    if st.button("⭐ 보물함에 기록", key=f"btn_sn_{rank}_{r['code']}"):
                        st.session_state.my_stocks.append({**r, "status": "BOUGHT", "buy_price": p_val, "qty": q_val, "sell_date": today_str})
                        save_data(st.session_state.my_stocks); st.rerun()
        else:
            st.info("오늘 장에서는 세력이 강력하게 개입한 완벽한 차트가 안 보여!")

with tab3:
    st.markdown("<h3 style='text-align:center;'>💖무조건잘된다니까💖</h3>", unsafe_allow_html=True)
    st.write("💰 **내 보물함 (수익률 실시간 관리)**")
    boughts = [s for s in st.session_state.my_stocks if s.get('status') == "BOUGHT"]
    if boughts:
        for i, s in enumerate(st.session_state.my_stocks):
            if s.get('status') == "BOUGHT":
                profit_rate = ((s['curr'] - s['buy_price']) / s['buy_price']) * 100
                total_profit = (s['curr'] - s['buy_price']) * s['qty']
                color = "#ff4b4b" if profit_rate > 0 else "#4b8bff"
                st.markdown(f"""
                    <div class='stock-card' style='border-left: 8px solid {color};'>
                        <span style='font-size:18px;'><b>{s['name']}</b></span> ({s['qty']}주)<br>
                        현재 수익률: <span style='color:{color}; font-weight:bold;'>{profit_rate:.2f}%</span><br>
                        실제 이익금: <b>{total_profit:,}원</b><br>
                        매수가: {s['buy_price']:,} ➔ 목표: <span class='price-target'>{s['target']:,}</span> | 탈출: <span class='price-stop'>{s['stop']:,}</span>
                    </div>
                    """, unsafe_allow_html=True)
                if st.button("청산 완료! (장부에서 삭제) 💸", key=f"sell_{i}_{s['code']}"):
                    st.session_state.my_stocks.pop(i); save_data(st.session_state.my_stocks); st.rerun()
    else: st.info("보물함이 비어있어! 급등 탭에서 스캔하고 마음에 드는 걸 담아봐!")
