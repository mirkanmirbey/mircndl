import yfinance as yf
import pandas as pd

class MircndlDataEngine:
    def __init__(self):
        self.tickers = [
            "THYAO.IS", "GARAN.IS", "ASELS.IS", "SISE.IS", "KCHOL.IS"
        ]

    def get_data(self, symbol, interval="1h", period="1mo"):
        print(f"📡 Veri çekiliyor: {symbol}...")
        try:
            # multi_level_index=False diyerek tabloyu basitleştiriyoruz
            df = yf.download(tickers=symbol, period=period, interval=interval, progress=False, multi_level_index=False)
            
            if df.empty:
                print(f"⚠️ Hata: {symbol} için veri boş geldi.")
                return None
            
            # Garanti olsun diye sütun adlarını temizleyelim
            # Bazen 'Adj Close' gelir, onu 'Close' olarak kullanmak isteyebiliriz ama şimdilik standart duralım.
            return df
        except Exception as e:
            print(f"❌ Bağlantı Hatası: {e}")
            return None

    def convert_to_4h(self, df_1h):
        if df_1h is None: return None

        # Veri setinin kopyasını alalım ki orjinali bozulmasın
        df = df_1h.copy()

        # Eğer sütunlar 'MultiIndex' ise (örneğin ('Price', 'Open') gibi), onları düzeltelim
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)  # İkinci katmanı (Ticker ismini) siler

        # Resampling (Yeniden Örnekleme) Ayarları
        agg_dict = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }
        
        try:
            # 4 Saatlik (4h) dönüşüm
            df_4h = df.resample('4h').agg(agg_dict).dropna()
            return df_4h
        except Exception as e:
            print(f"⚠️ Dönüştürme Hatası: {e}")
            # Hata ayıklama için sütunları yazdıralım
            print(f"Mevcut Sütunlar: {df.columns.tolist()}")
            return None

# --- TEST ALANI ---
if __name__ == "__main__":
    motor = MircndlDataEngine()
    
    # Test
    sembol = "THYAO.IS"
    raw_data = motor.get_data(sembol)
    
    if raw_data is not None:
        print(f"Ham Veri Sütunları: {raw_data.columns.tolist()}") # Kontrol amaçlı
        swing_data = motor.convert_to_4h(raw_data)
        
        if swing_data is not None:
            print("\n--- ✅ BAŞARILI: 4 SAATLİK SWING VERİSİ ---")
            print(swing_data.tail())
        else:
            print("Dönüşüm başarısız oldu.")