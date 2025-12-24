import pandas as pd
import numpy as np

class MircndlBrain:
    def __init__(self):
        pass

    def add_indicators(self, df):
        """
        Veriye Swing Trade için gerekli indikatörleri ekler.
        Kütüphane bağımlılığı olmaması için hesaplamaları manuel yapıyoruz.
        """
        if df is None or len(df) < 200:
            return None
        
        # Veriyi bozmamak için kopyalıyoruz
        data = df.copy()

        # 1. EMA (Üssel Hareketli Ortalama) - Trend Takibi için
        # EMA 50 ve EMA 200
        data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
        data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()

        # 2. RSI (Göreceli Güç Endeksi) - 14 Periyot
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # 3. Hacim Ortalaması (Son 20 mum)
        data['Vol_Avg'] = data['Volume'].rolling(window=20).mean()

        return data

    def check_swing_signal(self, df):
        """
        Son muma bakarak AL/SAT kararı verir.
        """
        if df is None: return "VERİ YOK"

        last_row = df.iloc[-1]       # En son kapanan mum
        prev_row = df.iloc[-2]       # Bir önceki mum

        # --- STRATEJİ MANTIĞI ---
        
        # KURAL 1: Trend Yukarı mı? (Fiyat > EMA 200)
        trend_is_up = last_row['Close'] > last_row['EMA_200']

        # KURAL 2: RSI "Ucuz" bölgede mi? (Swing için < 45 iyidir, <30 çok nadir gelir)
        rsi_is_cheap = last_row['RSI'] < 45

        # KURAL 3: RSI Dönüş Yapıyor mu? (RSI düşüşten yukarı kafa kaldırdı mı?)
        rsi_turning_up = last_row['RSI'] > prev_row['RSI']

        # KURAL 4: Hacim Artışı Var mı?
        volume_is_high = last_row['Volume'] > last_row['Vol_Avg']

        # SİNYAL OLUŞTURMA
        if trend_is_up and rsi_is_cheap and rsi_turning_up:
            signal_quality = "ORTA"
            if volume_is_high:
                signal_quality = "YÜKSEK 🔥"
            
            return {
                "sinyal": "AL (LONG)",
                "fiyat": last_row['Close'],
                "stop_loss": last_row['Close'] * 0.95, # %5 Stop
                "hedef": last_row['Close'] * 1.10,     # %10 Kar Hedefi
                "kalite": signal_quality,
                "sebep": f"Trend Pozitif, RSI: {last_row['RSI']:.2f}"
            }
        
        return None

# --- TEST ALANI (Entegrasyon) ---
if __name__ == "__main__":
    # Önceki yazdığımız 'mircndl_data' modülünü çağırıyoruz
    from mircndl_data import MircndlDataEngine
    
    data_engine = MircndlDataEngine()
    brain = MircndlBrain()

    print("🧠 mircndl Beyni Çalışıyor...")
    
    # Test edilecek hisseler
    test_hisseleri = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS"]

    for hisse in test_hisseleri:
        # 1. Veriyi Çek (1 Saatlik -> 4 Saatliğe Çevir)
        raw = data_engine.get_data(hisse, period="6mo") # EMA200 için en az 6 ay veri lazım
        df_4h = data_engine.convert_to_4h(raw)

        if df_4h is not None:
            # 2. İndikatörleri Ekle
            df_analyzed = brain.add_indicators(df_4h)
            
            # 3. Sinyal Kontrol Et
            sinyal = brain.check_swing_signal(df_analyzed)

            if sinyal:
                print(f"\n🚨 TESPİT EDİLDİ: {hisse}")
                print(f"   Detay: {sinyal}")
            else:
                # Sinyal yoksa bile son durumu görelim
                last_rsi = df_analyzed.iloc[-1]['RSI']
                print(f"   {hisse}: Sinyal Yok (RSI: {last_rsi:.2f})")