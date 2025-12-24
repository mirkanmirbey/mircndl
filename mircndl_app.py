import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="mircndl Pro",
    page_icon="📊",
    layout="wide", # Geniş ekran modu
    initial_sidebar_state="expanded" # Menü açık başlasın
)

# --- CSS TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    
    /* Kart Tasarımı */
    .metric-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MENÜ SİSTEMİ (SOL PANEL) ---
st.sidebar.title("🔥 mircndl Panel")
st.sidebar.write("Yapay Zeka Destekli Analiz")

# Ana Kategori Seçimi
ana_kategori = st.sidebar.selectbox(
    "Analiz Türü Seçin",
    ["🛠️ Teknik Analiz", "🏢 Temel & Sektör"]
)

st.sidebar.markdown("---") # Çizgi çek

# Alt Kategori Seçimi (Duruma göre değişir)
secilen_strateji = ""
secilen_sektor = ""

if ana_kategori == "🛠️ Teknik Analiz":
    secilen_strateji = st.sidebar.radio(
        "Teknik Stratejiler",
        ["RSI Diptekiler (<35)", "MACD Kesişimi (AL)", "Hareketli Ort. (SMA50>200)"]
    )
elif ana_kategori == "🏢 Temel & Sektör":
    secilen_sektor = st.sidebar.selectbox(
        "Sektör Seçin",
        ["Tümü", "Bankacılık", "Holdingler", "Sanayi & Enerji"]
    )

# --- FONKSİYONLAR ---

# 1. Grafik Çizme (Hafta sonlarını gizleyen profesyonel mod)
def grafik_ciz(sembol, df):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        increasing_line_color='#00E676',
        decreasing_line_color='#FF1744'
    )])

    fig.update_layout(
        title=f"{sembol} - 4 Saatlik",
        template="plotly_dark",
        height=350,
        margin=dict(t=30, b=0, l=0, r=0),
        xaxis_rangeslider_visible=False,
        # Hafta sonlarını gizleyen sihirli kod:
        xaxis=dict(
            rangebreaks=[
                dict(bounds=["sat", "mon"]), # Cumartesi-Pazartesi arasını gizle
            ]
        )
    )
    return fig

# 2. Veri Çekme ve Hesaplama Motoru
@st.cache_data(ttl=900)
def piyasayi_tara(kategori, strateji_veya_sektor):
    # Sektörlere göre hisse listeleri
    bankalar = ["AKBNK.IS", "GARAN.IS", "YKBNK.IS", "ISCTR.IS"]
    holdingler = ["KCHOL.IS", "SAHOL.IS", "SISE.IS", "TKFEN.IS"]
    sanayi = ["THYAO.IS", "ASELS.IS", "TUPRS.IS", "EREGL.IS", "FROTO.IS", "SASA.IS", "HEKTS.IS", "ASTOR.IS"]
    
    # Listeyi belirle
    if kategori == "🏢 Temel & Sektör":
        if strateji_veya_sektor == "Bankacılık": takip_listesi = bankalar
        elif strateji_veya_sektor == "Holdingler": takip_listesi = holdingler
        elif strateji_veya_sektor == "Sanayi & Enerji": takip_listesi = sanayi
        else: takip_listesi = bankalar + holdingler + sanayi
    else:
        takip_listesi = bankalar + holdingler + sanayi # Teknikte hepsine bak

    sonuclar = []

    for sembol in takip_listesi:
        try:
            df = yf.download(sembol, period="6mo", interval="1h", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            if len(df) < 50: continue

            # 4 Saatlik Dönüşüm
            ozet = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
            df_4h = df.resample('4h').agg(ozet).dropna()

            # --- İNDİKATÖRLER ---
            # RSI
            delta = df_4h['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df_4h['RSI'] = 100 - (100 / (1 + rs))

            # MACD (12, 26, 9)
            exp1 = df_4h['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df_4h['Close'].ewm(span=26, adjust=False).mean()
            df_4h['MACD'] = exp1 - exp2
            df_4h['Signal'] = df_4h['MACD'].ewm(span=9, adjust=False).mean()

            # SMA (Hareketli Ortalamalar)
            df_4h['SMA50'] = df_4h['Close'].rolling(window=50).mean()
            df_4h['SMA200'] = df_4h['Close'].rolling(window=200).mean()

            son = df_4h.iloc[-1]
            onceki = df_4h.iloc[-2]
            
            # --- FİLTRELEME MANTIĞI ---
            uygun = False
            notlar = ""

            if kategori == "🛠️ Teknik Analiz":
                if strateji_veya_sektor == "RSI Düşükler (<35)":
                    if son['RSI'] < 35:
                        uygun = True
                        notlar = f"RSI Aşırı Satımda: {son['RSI']:.1f}"
                
                elif strateji_veya_sektor == "MACD Kesişimi (AL)":
                    # Macd sinyali yukarı kesmişse
                    if son['MACD'] > son['Signal'] and onceki['MACD'] < onceki['Signal']:
                        uygun = True
                        notlar = "MACD Al Sinyali Üretti"
                
                elif strateji_veya_sektor == "Hareketli Ort. (SMA50>200)":
                    if son['SMA50'] > son['SMA200']:
                        uygun = True
                        notlar = "Trend Pozitif (Golden Cross Bölgesi)"
            
            else: # Temel & Sektör (Hepsini Getir)
                uygun = True # Filtre yok, hepsini listele
                notlar = f"Fiyat: {son['Close']:.2f} ₺"

            if uygun:
                sonuclar.append({
                    "sembol": sembol.replace(".IS", ""),
                    "fiyat": son['Close'],
                    "rsi": son['RSI'],
                    "not": notlar,
                    "veri": df_4h
                })

        except: continue
    
    return sonuclar

# --- ANA EKRAN GÖRÜNÜMÜ ---

if ana_kategori == "🛠️ Teknik Analiz":
    st.title(f"{secilen_strateji}")
    if st.button("🔍 Taramayı Başlat"):
        with st.spinner('Grafikler analiz ediliyor...'):
            firsatlar = piyasayi_tara(ana_kategori, secilen_strateji)
            if firsatlar:
                st.success(f"{len(firsatlar)} Hisse Bulundu")
                for s in firsatlar:
                    with st.expander(f"{s['sembol']} - {s['not']}", expanded=True):
                        c1, c2 = st.columns(2)
                        c1.metric("Fiyat", f"{s['fiyat']:.2f} ₺")
                        c2.metric("RSI", f"{s['rsi']:.1f}")
                        st.plotly_chart(grafik_ciz(s['sembol'], s['veri']), use_container_width=True)
            else:
                st.warning("Bu stratejiye uyan hisse bulunamadı.")

elif ana_kategori == "🏢 Temel & Sektör":
    st.title(f"{secilen_sektor} Sektörü")
    if st.button("📋 Listeyi Getir"):
         with st.spinner('Veriler çekiliyor...'):
            hisseler = piyasayi_tara(ana_kategori, secilen_sektor)
            if hisseler:
                # Sektör görünümü için yan yana kartlar
                cols = st.columns(2)
                for index, s in enumerate(hisseler):
                    with cols[index % 2]: # Çift sütun düzeni
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>{s['sembol']}</h3>
                            <h1>{s['fiyat']:.2f} ₺</h1>
                            <p>RSI: {s['rsi']:.1f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        with st.expander("Grafiği Aç"):
                             st.plotly_chart(grafik_ciz(s['sembol'], s['veri']), use_container_width=True)
