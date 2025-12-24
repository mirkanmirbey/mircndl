import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="mircndl",
    page_icon="🕯️",
    layout="centered"
)

# --- TASARIM (DARK MODE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .stButton>button { 
        width: 100%; border-radius: 10px; background-color: #4CAF50; 
        color: white; font-weight: bold; padding: 10px; border: none;
    }
    .stButton>button:hover { background-color: #45a049; }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK ---
st.title("🕯️ mircndl")
st.caption("Mirkan & Candle • Gerçek Zamanlı Mum Analizi")
st.divider()

# --- GRAFİK ÇİZME FONKSİYONU ---
def grafik_ciz(sembol, df):
    # Son 40 mumu alalım ki grafik telefonda net görünsün
    df_son = df.tail(40)
    
    fig = go.Figure(data=[go.Candlestick(
        x=df_son.index,
        open=df_son['Open'],
        high=df_son['High'],
        low=df_son['Low'],
        close=df_son['Close'],
        increasing_line_color='#26A69A', # Borsa Yeşili
        decreasing_line_color='#EF5350'  # Borsa Kırmızısı
    )])

    # Grafik Ayarları (Karanlık Tema)
    fig.update_layout(
        title=f"{sembol} - 4 Saatlik Mumlar",
        title_font_size=14,
        dragmode='pan',
        template="plotly_dark", # Koyu Tema
        height=350, # Mobilde çok yer kaplamasın
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False # Alttaki kaydırma çubuğunu gizle
    )
    return fig

# --- ANALİZ MOTORU ---
@st.cache_data(ttl=900)
def verileri_analiz_et():
    hisseler = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "SISE.IS", 
                "AKBNK.IS", "TUPRS.IS", "EREGL.IS", "BIMAS.IS", "FROTO.IS", "SASA.IS", "HEKTS.IS"]
    sinyaller = []

    for sembol in hisseler:
        try:
            # Veri Çek
            df = yf.download(sembol, period="3mo", interval="1h", progress=False)
            
            # MultiIndex düzeltmesi
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            if len(df) < 50: continue

            # 4 Saatlik Dönüşüm
            ozet = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
            df_4h = df.resample('4h').agg(ozet).dropna()

            # İndikatörler (EMA & RSI)
            df_4h['EMA_200'] = df_4h['Close'].ewm(span=200).mean()
            
            delta = df_4h['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df_4h['RSI'] = 100 - (100 / (1 + rs))

            son = df_4h.iloc[-1]

            # Strateji
            trend = son['Close'] > son['EMA_200']
            rsi_uygun = son['RSI'] < 55 

            if trend and rsi_uygun:
                sinyaller.append({
                    "sembol": sembol.replace(".IS", ""),
                    "fiyat": son['Close'],
                    "rsi": son['RSI'],
                    "veri": df_4h # Grafiği çizmek için veriyi de saklıyoruz
                })

        except Exception:
            continue
            
    return sinyaller

# --- ARAYÜZ ---
if st.button("PİYASAYI TARA"):
    with st.spinner('Grafikler oluşturuluyor...'):
        firsatlar = verileri_analiz_et()
        
        if firsatlar:
            st.success(f"{len(firsatlar)} Mum Formasyonu Tespit Edildi")
            
            for s in firsatlar:
                # Kart Başlığı
                st.markdown(f"### 📈 {s['sembol']}")
                
                col1, col2 = st.columns(2)
                col1.metric("Fiyat", f"{s['fiyat']:.2f} ₺")
                col2.metric("RSI", f"{s['rsi']:.1f}")
                
                # --- İŞTE BURADA GRAFİĞİ ÇİZİYORUZ ---
                fig = grafik_ciz(s['sembol'], s['veri'])
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider() # Çizgi çek
        else:
            st.warning("Şu an stratejiye uygun grafik bulunamadı.")
