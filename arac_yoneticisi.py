import pandas as pd
from thefuzz import process

class AracYoneticisi:
    """Araçların listesini ve durumlarını (çalışıyor/boşta) yönetir."""
    def __init__(self, arac_adlari):
        """Başlangıç araç listesi ile DataFrame'i oluşturur."""
        self.araclar = arac_adlari
        self.df_araclar = pd.DataFrame({
            'Araç': self.araclar,
            'Durum': ['boşta'] * len(self.araclar)
        })

    def durum_df_al(self):
        """Araç durumlarını içeren DataFrame'i döndürür."""
        return self.df_araclar

    def _arac_bul(self, isim):
        """Verilen isme en çok benzeyen aracı bulur (yazım hatalarını tolere eder)."""
        if not isim:
            return None
        # thefuzz kütüphanesi ile %80 ve üzeri benzerlikte olan en iyi eşleşmeyi bulur.
        eslesme = process.extractOne(isim, self.araclar, score_cutoff=80)
        return eslesme[0] if eslesme else None

    def araci_calisiyor_yap(self, arac_adi):
        """Bir aracın durumunu 'çalışıyor' olarak günceller."""
        eslesen_arac = self._arac_bul(arac_adi)
        if eslesen_arac:
            self.df_araclar.loc[self.df_araclar['Araç'] == eslesen_arac, 'Durum'] = 'çalışıyor'
            print(f"\n'{eslesen_arac}' adlı aracın durumu 'çalışıyor' olarak güncellendi.")
        else:
            print(f"\nUyarı: '{arac_adi}' araç listesiyle eşleşmedi.")

    def araci_bosa_al(self, arac_adi):
        """Bir aracın durumunu 'boşta' olarak günceller."""
        eslesen_arac = self._arac_bul(arac_adi)
        if eslesen_arac:
            self.df_araclar.loc[self.df_araclar['Araç'] == eslesen_arac, 'Durum'] = 'boşta'
            print(f"\n'{eslesen_arac}' adlı aracın durumu 'boşta' olarak güncellendi.")
        else:
            print(f"\nUyarı: '{arac_adi}' araç listesiyle eşleşmedi.")

    def is_arac_musait(self, arac_adi):
        """Belirtilen aracın boşta olup olmadığını kontrol eder."""
        eslesen_arac = self._arac_bul(arac_adi)
        if eslesen_arac:
            durum = self.df_araclar.loc[self.df_araclar['Araç'] == eslesen_arac, 'Durum'].iloc[0]
            return durum == 'boşta'
        return False
