import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# --- MARKA AYARLARI ---
st.set_page_config(
    page_title="mircndl",
    page_icon="🕯️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- TASARIM VE GİZLEME ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    #MainMenu, footer, header {visibility: hidden;}
    
    .stButton>button { 
        width: 100%; border-radius: 12px; background-color: #2E7D32; 
        color: white; font-weight: bold; padding: 12px; border: none;
    }
    
    .hisse-karti {
        background-color: #1E1E1E; padding: 15px; border-radius: 10px;
        margin-bottom: 20px; border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK (VERSİYON KONTROLÜ İÇİN) ---
st.markdown("<h1 style='text-align: center;'>🕯️ mircndl</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4CAF50; font-weight:bold;'>v3.1 YENİ VERSİYON AKTİF</p>", unsafe_allow_html=True) 

# --- GRAFİK MOTORU (KOPUKLUK GİDERİCİ) ---
def grafik_ciz(sembol, df):
    df_son = df.tail(50).copy()
    
    # 1. Hile: Tarih indexini string (yazı) sütununa çeviriyoruz
    df_son['Tarih_Yazi'] = df_son.index.strftime('%d %b %H:%M')
    
    fig = go.Figure(data=[go.Candlestick(
        x=df_son['Tarih_Yazi'], # X eksenine artık tarih değil, yazı veriyoruz
        open=df_son['Open'],
        high=df_son['High'],
        low=df_son['Low'],
        close=df_son['Close'],
        increasing_line_color='#00C853',
        decreasing_line_color='#FF5252'
    )])

    fig.update_layout(
        title=dict(text=f"{sembol}", font=dict(color="white")),
        dragmode='pan',
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(t=40, b=0, l=0, r=0),
        xaxis_rangeslider_visible=False,
        # 2. Hile: Type category diyerek boşlukları siliyoruz
        xaxis=dict(type='category', showgrid=False, tickangle=-45), 
        yaxis=dict(showgrid=True, gridcolor='#333')
    )
    return fig

# --- VERİ MOTORU ---
@st.cache_data(ttl=0) # Önbelleği kapattık ki hemen güncellensin
def verileri_analiz_et():
    hisseler = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "SISE.IS", 
                "AKBNK.IS", "TUPRS.IS", "EREGL.IS", "BIMAS.IS"]
    sinyaller = []

    for sembol in hisseler:
        try:
            df = yf.download(sembol, period="3mo", interval="1h", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            if len(df) < 50: continue

            ozet = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
            df_4h = df.resample('4h').agg(ozet).dropna()

            df_4h['EMA'] = df_4h['Close'].ewm(span=200).mean()
            # Basit RSI
            delta = df_4h['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df_4h['RSI'] = 100 - (100 / (1 + rs))

            son = df_4h.iloc[-1]
            if son['Close'] > son['EMA'] and son['RSI'] < 65:
                sinyaller.append({
                    "sembol": sembol.replace(".IS", ""),
                    "fiyat": son['Close'],
                    "rsi": son['RSI'],
                    "veri": df_4h
                })
        except: continue
    return sinyaller

# --- ARAYÜZ ---
if st.button("PİYASAYI TARA (v3.1)"):
    with st.spinner('Analiz yapılıyor...'):
        firsatlar = verileri_analiz_et()
        if firsatlar:
            st.success(f"{len(firsatlar)} Grafik Bulundu")
            for s in firsatlar:
                st.markdown('<div class="hisse-karti">', unsafe_allow_html=True)
                c1, c2 = st.columns([2,1])
                c1.metric(s['sembol'], f"{s['fiyat']:.2f} ₺")
                c2.metric("RSI", f"{s['rsi']:.1f}")
                st.plotly_chart(grafik_ciz(s['sembol'], s['veri']), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("Şu an uygun sinyal yok.")
