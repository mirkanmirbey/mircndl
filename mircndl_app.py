import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="mircndl Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS VE TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    
    /* Temel Analiz Kartları */
    .fundamental-card {
        background-color: #1E1E1E; padding: 15px; border-radius: 10px;
        border: 1px solid #333; margin-bottom: 10px;
    }
    .kirmizi { color: #FF5252; font-weight: bold; }
    .yesil { color: #00E676; font-weight: bold; }
    .baslik { font-size: 18px; font-weight: bold; color: #2196F3; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ SETİ (SEKTÖRLER VE HİSSELER) ---
SEKTORLER = {
    "🏦 Bankacılık": ["AKBNK.IS", "GARAN.IS", "ISCTR.IS", "YKBNK.IS", "VAKBN.IS", "HALKB.IS"],
    "✈️ Ulaştırma": ["THYAO.IS", "PGSUS.IS", "TAVHL.IS"],
    "🏭 Sanayi & Holding": ["KCHOL.IS", "SAHOL.IS", "SISE.IS", "TUPRS.IS", "EREGL.IS", "KRDMD.IS", "FROTO.IS", "TOASO.IS"],
    "⚡ Enerji & Teknoloji": ["ASELS.IS", "KONTR.IS", "SASA.IS", "HEKTS.IS", "ASTOR.IS", "EUPWR.IS", "MIATK.IS"],
    "🛒 Perakende & Gıda": ["BIMAS.IS", "MGROS.IS", "SOKM.IS", "ULKER.IS"]
}

# --- YAN MENÜ (KONTROL PANELİ) ---
st.sidebar.title("🔥 mircndl v5.0")

# 1. Mod Seçimi
mod = st.sidebar.selectbox("Analiz Modu", ["🛠️ Teknik Tarama", "🏢 Temel Analiz"])

st.sidebar.markdown("---")

secimler = {}

if mod == "🛠️ Teknik Tarama":
    # Zaman Dilimi
    zaman_etiket = st.sidebar.selectbox("Zaman Dilimi", ["4 Saatlik", "Günlük", "Haftalık"])
    # Arka planda yfinance formatına çevir
    zaman_map = {"4 Saatlik": "4h", "Günlük": "1d", "Haftalık": "1wk"}
    secimler['periyot'] = zaman_map[zaman_etiket]
    
    # Strateji
    secimler['strateji'] = st.sidebar.radio(
        "Strateji Seçin",
        ["RSI Diptekiler (<35)", "MACD Kesişimi (AL)", "Hareketli Ort. (SMA50>200)"]
    )
    
    # Kapsam (Hangi hisseler taransın?)
    kapsam = st.sidebar.selectbox("Tarama Kapsamı", ["BIST 30 (Hızlı)", "Tüm Sektörler (Yavaş)"])
    if kapsam == "BIST 30 (Hızlı)":
        secimler['liste'] = SEKTORLER["🏦 Bankacılık"] + SEKTORLER["🏭 Sanayi & Holding"]
    else:
        # Tüm listeleri birleştir
        tum_liste = []
        for v in SEKTORLER.values(): tum_liste += v
        secimler['liste'] = tum_liste

elif mod == "🏢 Temel Analiz":
    # Sektör Seçimi
    secilen_sektor_ismi = st.sidebar.selectbox("Sektör Seçin", list(SEKTORLER.keys()))
    secimler['liste'] = SEKTORLER[secilen_sektor_ismi]


# --- FONKSİYONLAR ---

def grafik_ciz(sembol, df):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#00E676', decreasing_line_color='#FF5252'
    )])
    fig.update_layout(
        title=f"{sembol}", template="plotly_dark", height=300,
        margin=dict(t=30, b=0, l=0, r=0), xaxis_rangeslider_visible=False
    )
    return fig

# Temel Analiz Verisi Çekme
def temel_bilgi_getir(sembol):
    try:
        hisse = yf.Ticker(sembol)
        info = hisse.info
        
        veriler = {
            "Fiyat": info.get('currentPrice', 0),
            "FK": info.get('trailingPE', 0), # Fiyat Kazanç
            "PD_DD": info.get('priceToBook', 0), # Piyasa/Defter Değeri
            "Temettu": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            "ROA": info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
            "Hedef": info.get('targetMeanPrice', 0),
            "Ozet": info.get('longBusinessSummary', 'Bilgi yok.')
        }
        return veriler
    except:
        return None

# Teknik Analiz Motoru
@st.cache_data(ttl=600)
def teknik_tara(hisse_listesi, periyot, strateji):
    sonuclar = []
    # Periyoda göre veri çekme süresi ayarı
    sure = "2y" if periyot == "1wk" else "6mo"
    
    for sembol in hisse_listesi:
        try:
            df = yf.download(sembol, period=sure, interval=periyot, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            if len(df) < 20: continue
            
            # Boşlukları temizle
            df = df.dropna()

            # İndikatörler
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            
            son = df.iloc[-1]
            onceki = df.iloc[-2]
            
            uygun = False
            notlar = ""

            if strateji == "RSI Diptekiler (<35)":
                if son['RSI'] < 35:
                    uygun = True
                    notlar = f"RSI: {son['RSI']:.1f} (Aşırı Satım)"
            
            elif strateji == "MACD Kesişimi (AL)":
                if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] < signal.iloc[-2]:
                    uygun = True
                    notlar = "MACD AL Sinyali"
            
            elif strateji == "Hareketli Ort. (SMA50>200)":
                if son['SMA50'] > son['SMA200']:
                    uygun = True
                    notlar = "Golden Cross / Yükseliş Trendi"

            if uygun:
                sonuclar.append({
                    "sembol": sembol.replace(".IS", ""),
                    "fiyat": son['Close'],
                    "rsi": son['RSI'],
                    "not": notlar,
                    "veri": df
                })
        except: continue
    return sonuclar

# --- ANA EKRAN ---

if mod == "🛠️ Teknik Tarama":
    st.title(f"🔍 {secimler['periyot']} - {secimler['strateji']}")
    
    if st.button("TARAMAYI BAŞLAT", type="primary"):
        with st.spinner(f"{len(secimler['liste'])} hisse taranıyor..."):
            firsatlar = teknik_tara(secimler['liste'], secimler['periyot'], secimler['strateji'])
            
            if firsatlar:
                st.success(f"{len(firsatlar)} Hisse Bulundu!")
                for s in firsatlar:
                    with st.expander(f"📈 {s['sembol']} - {s['fiyat']:.2f} ₺ ({s['not']})", expanded=True):
                        st.plotly_chart(grafik_ciz(s['sembol'], s['veri']), use_container_width=True)
            else:
                st.warning("Bu kriterlere uyan hisse bulunamadı.")

elif mod == "🏢 Temel Analiz":
    st.title("📊 Temel Analiz Raporları")
    st.info("Hisseye tıklayarak detaylı mali raporu görebilirsin.")
    
    # Seçilen sektördeki hisseleri listele
    hisse_listesi = secimler['liste']
    
    for hisse_kodu in hisse_listesi:
        temiz_isim = hisse_kodu.replace(".IS", "")
        
        # Her hisse için bir genişletilebilir kutu (Expander)
        with st.expander(f"🏢 {temiz_isim} - Analiz Et"):
            # Kullanıcı açarsa veriyi çek (Hepsini başta çekersek sistem donar)
            with st.spinner(f"{temiz_isim} verileri Yahoo Finance'den alınıyor..."):
                veri = temel_bilgi_getir(hisse_kodu)
                
                if veri:
                    # Renklendirme Mantığı
                    fk_renk = "yesil" if 0 < veri['FK'] < 10 else "kirmizi"
                    pd_renk = "yesil" if 0 < veri['PD_DD'] < 2 else "kirmizi"
                    
                    st.markdown(f"""
                    <div class="fundamental-card">
                        <div style="display:flex; justify-content:space-between;">
                            <div>
                                <div class="baslik">FİYAT</div>
                                <h1>{veri['Fiyat']} ₺</h1>
                                <small>Hedef Fiyat: {veri['Hedef']} ₺</small>
                            </div>
                            <div style="text-align:right;">
                                <div>F/K Oranı: <span class="{fk_renk}">{veri['FK']:.2f}</span></div>
                                <div>PD/DD: <span class="{pd_renk}">{veri['PD_DD']:.2f}</span></div>
                                <div>Temettü: <b>%{veri['Temettu']:.2f}</b></div>
                            </div>
                        </div>
                        <hr style="border-color:#333;">
                        <p><i>{veri['Ozet'][:200]}...</i></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Veri alınamadı.")
