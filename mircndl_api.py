from fastapi import FastAPI
from mircndl_data import MircndlDataEngine
from mircndl_brain import MircndlBrain

app = FastAPI(title="mircndl API", version="1.0")

data_engine = MircndlDataEngine()
brain = MircndlBrain()

WATCHLIST = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "SISE.IS"]

@app.get("/")
def home():
    return {"durum": "aktif", "mesaj": "mircndl sunucusu çalışıyor 🚀"}

@app.get("/sinyaller")
def get_signals():
    sinyal_listesi = []
    
    for hisse in WATCHLIST:
        # Veri yeterli mi diye 6 aylık çekiyoruz (EMA200 için garanti olsun)
        raw = data_engine.get_data(hisse, period="6mo")
        df_4h = data_engine.convert_to_4h(raw)
        
        if df_4h is not None:
            df_analyzed = brain.add_indicators(df_4h)
            sonuc = brain.check_swing_signal(df_analyzed)
            
            # --- KRİTİK DÜZELTME BURADA ---
            # Gelen sonuç "VERİ YOK" yazısı değil, gerçek bir sinyal sözlüğü mü?
            if isinstance(sonuc, dict):
                sinyal_karti = {
                    "sembol": hisse,
                    "yon": sonuc['sinyal'],
                    "fiyat": sonuc['fiyat'],
                    "hedef": sonuc['hedef'],
                    "kalite": sonuc['kalite'],
                    "tarih": str(df_analyzed.index[-1])
                }
                sinyal_listesi.append(sinyal_karti)
    
    return {"bulunan_sinyaller": sinyal_listesi, "toplam": len(sinyal_listesi)}