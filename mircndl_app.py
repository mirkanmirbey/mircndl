import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# --- MARKA VE SAYFA AYARLARI ---
st.set_page_config(
    page_title="mircndl",        # Sekme İsmi
    page_icon="🕯️",              # Sekme İkonu
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS TASARIM (DARK MODE & LOGO GİZLEME) ---
st.markdown("""
    <style>
    /* Ana Arka Plan */
    .stApp { background-color: #0E1117; color: white; }
    
    /* Streamlit'in kendi kırmızı menüsünü ve footer'ını gizleyelim */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Buton Tasarımı */
    .stButton>button { 
        width: 100%; border-radius: 12px; background-color: #2E7D32; 
        color: white; font-weight: bold; padding: 12px; border: none;
        font-size: 16px; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #1B5E20; }
    
    /* Kart Tasarımı */
    .hisse-karti {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK ---
# Kendi logomuzu (ikonumuzu) başlığa elle koyuyoruz
st.markdown("<h1 style='text-align: center;'>🕯️ mircndl</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Algoritmik Mum Analizi v3.0</p>", unsafe_allow_html=True)
st.divider()

# --- GRAFİK ÇİZME (KOPUKLUK GİDERİLDİ) ---
def grafik_ciz(sembol, df):
    # Son 40 mumu al
    df_son = df.tail(40).copy()
    
    # Tarihleri basit okunur hale getir (Örn: "24 Ara 14:00")
    # Bu işlem grafikteki BOŞLUKLARI YOK EDER, mumları yan yana dizer.
    df_son.index = df_son.index.strftime('%d %b %H:%M')
    
    fig = go.Figure(data=[go.Candlestick(
        x=df_son.index, # Tarihleri metin olarak veriyoruz
        open=df_son['Open'],
        high=df_son['High'],
        low=df_son['Low'],
        close=df_son['Close'],
        increasing_line_color='#00C853', # Parlak Yeşil
        decreasing_line_color='#FF5252'  # Parlak Kırmızı
    )])

    # Grafik Ayarları
    fig.update_layout(
        title=dict(text=f"{sembol}", font=dict(color="white", size=20)),
        dragmode='pan',
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)', # Şeffaf arka plan
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_rangeslider_visible=False, # Alttaki slider'ı kapat
        xaxis=dict(type='category', showgrid=False), # MUM TİPİ: Boşlukları siler!
        yaxis=dict(showgrid=True, gridcolor='#333')
    )
    return fig

# --- ANALİZ MOTORU ---
@st.cache_data(ttl=900)
def verileri_analiz_et():
    # Hisseler (BIST 30 Karışık)
    hisseler = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "SISE.IS", 
                "AKBNK.IS", "TUPRS.IS", "EREGL.IS", "BIMAS.IS", "FROTO.IS", 
                "SASA.IS", "HEKTS.IS", "ASTOR.IS", "KONTR.IS"]
    sinyaller = []

    for sembol in hisseler:
        try:
            # Yahoo'dan veri çek
            df = yf.download(sembol, period="3mo", interval="1h", progress=False)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            if len(df) < 50: continue

            # 4 Saatlik Swing Mumlarına Çevir
            ozet = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
            df_4h = df.resample('4h').agg(ozet).dropna()

            # İndikatörler
            df_4h['EMA_200'] = df_4h['Close'].ewm(span=200).mean()
            
            # RSI Hesapla
            delta = df_4h['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df_4h['RSI'] = 100 - (100 / (1 + rs))

            son = df_4h.iloc[-1]

            # Basit Strateji: Trend yukarıysa ve RSI aşırı şişmemişse göster
            trend = son['Close'] > son['EMA_200']
            rsi_uygun = son['RSI'] < 60 

            if trend and rsi_uygun:
                sinyaller.append({
                    "sembol": sembol.replace(".IS", ""),
                    "fiyat": son['Close'],
                    "rsi": son['RSI'],
                    "veri": df_4h # Grafik verisi
                })

        except:
            continue
            
    return sinyaller

# --- ARAYÜZ ---
if st.button("PİYASAYI TARA"):
    with st.spinner('Yapay zeka grafikleri analiz ediyor...'):
        firsatlar = verileri_analiz_et()
        
        if firsatlar:
            st.success(f"Analiz Tamamlandı: {len(firsatlar)} Fırsat")
            
            for s in firsatlar:
                # Kapsayıcı kutu
                st.markdown('<div class="hisse-karti">', unsafe_allow_html=True)
                
                # Başlık ve Değerler
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.metric("Fiyat", f"{s['fiyat']:.2f} ₺")
                with col2:
                    st.metric("RSI", f"{s['rsi']:.1f}")
                
                # Grafik
                fig = grafik_ciz(s['sembol'], s['veri'])
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("Şu an kriterlere uyan grafik formasyonu yok.")
