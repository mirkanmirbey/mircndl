import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# --- MARKA AYARLARI (RESİMLİ LOGO DENEMESİ) ---
# Buraya gerçek bir mum logosu linki koydum. Telefon bunu daha ciddiye alabilir.
MUM_LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2929/2929003.png"

st.set_page_config(
    page_title="MIRCNDL",
    page_icon=MUM_LOGO_URL, # Artık emoji değil, resim kullanıyoruz
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- GHOST MODE CSS (TÜM İZLERİ SİLME) ---
st.markdown("""
    <style>
    /* Ana Arka Planı Simsiyah Yap */
    .stApp { background-color: #000000; color: white; }
    
    /* Streamlit'in tüm menülerini, hamburger butonunu, footer'ını GİZLE */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    
    /* Buton Tasarımı */
    .stButton>button { 
        width: 100%; border-radius: 8px; background-color: #00C853; 
        color: white; font-weight: bold; padding: 14px; border: none;
        font-size: 16px; text-transform: uppercase; letter-spacing: 1px;
    }
    
    /* Kart Tasarımı */
    .hisse-karti {
        background-color: #111; padding: 15px; border-radius: 12px;
        margin-bottom: 20px; border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,255,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK ---
# Kendi logomuzu en tepeye, ortaya yerleştiriyoruz
st.markdown(f"""
    <div style='text-align: center; padding-bottom: 20px;'>
        <img src='{MUM_LOGO_URL}' width='60'>
        <h1 style='margin-top: -10px; font-family: sans-serif; letter-spacing: 2px;'>MIRCNDL</h1>
        <p style='color: gray; font-size: 12px;'>v3.2 GHOST EDITION</p>
    </div>
    """, unsafe_allow_html=True)

# --- GRAFİK MOTORU ---
def grafik_ciz(sembol, df):
    df_son = df.tail(50).copy()
    # Tarihleri yazıya çevirip boşlukları yok ediyoruz
    df_son['Tarih_Yazi'] = df_son.index.strftime('%H:%M')
    
    fig = go.Figure(data=[go.Candlestick(
        x=df_son['Tarih_Yazi'],
        open=df_son['Open'], high=df_son['High'],
        low=df_son['Low'], close=df_son['Close'],
        increasing_line_color='#00E676', # Neon Yeşil
        decreasing_line_color='#FF1744'  # Neon Kırmızı
    )])

    fig.update_layout(
        title=dict(text=f"{sembol}", font=dict(color="white", size=18)),
        dragmode='pan', template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=300, margin=dict(t=30, b=0, l=0, r=0),
        xaxis_rangeslider_visible=False,
        xaxis=dict(type='category', showgrid=False, tickangle=0), 
        yaxis=dict(showgrid=True, gridcolor='#222')
    )
    return fig

# --- VERİ MOTORU ---
@st.cache_data(ttl=0)
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
            
            delta = df_4h['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df_4h['RSI'] = 100 - (100 / (1 + rs))

            son = df_4h.iloc[-1]
            if son['Close'] > son['EMA'] and son['RSI'] < 65:
                sinyaller.append({
                    "sembol": sembol.replace(".IS", ""),
                    "fiyat": son['Close'], "rsi": son['RSI'], "veri": df_4h
                })
        except: continue
    return sinyaller

# --- ARAYÜZ ---
if st.button("PİYASAYI TARA"):
    with st.spinner('MIRCNDL sunucusu çalışıyor...'):
        firsatlar = verileri_analiz_et()
        if firsatlar:
            for s in firsatlar:
                st.markdown('<div class="hisse-karti">', unsafe_allow_html=True)
                c1, c2 = st.columns([2,1])
                c1.metric(s['sembol'], f"{s['fiyat']:.2f} ₺")
                c2.metric("RSI", f"{s['rsi']:.1f}")
                st.plotly_chart(grafik_ciz(s['sembol'], s['veri']), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("Şu an uygun grafik yok.")
