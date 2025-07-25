import pandas as pd
from thefuzz import process

class OperatorYoneticisi:
    """Operatörlerin listesini ve durumlarını (aktif/boşta) yönetir."""
    def __init__(self, operator_adlari, db_manager=None):
        """Başlangıç operatör listesi ile DataFrame'i oluşturur."""
        self.operatorler = operator_adlari
        self.db_manager = db_manager
        self.df_kisiler = pd.DataFrame({
            'Operatör': self.operatorler,
            'Durum': ['boşta'] * len(self.operatorler),
            'Kullandığı Araç': [None] * len(self.operatorler)
        })

    def durum_df_al(self):
        """Operatör durumlarını içeren DataFrame'i döndürür."""
        return self.df_kisiler

    def operator_bul(self, isim):
        """Verilen isme en çok benzeyen operatörü bulur (yazım hatalarını tolere eder)."""
        if not isim:
            return None
        # thefuzz kütüphanesi ile %80 ve üzeri benzerlikte olan en iyi eşleşmeyi bulur.
        eslesme = process.extractOne(isim, self.operatorler, score_cutoff=70)
        return eslesme[0] if eslesme else None

    def arac_kontrol_et(self, arac_adi):
        """Veritabanında araç bulunup bulunmadığını kontrol eder."""
        if not self.db_manager or not arac_adi:
            return True  # Eğer db_manager yoksa ya da araç adı boşsa kontrolü geç
            
        try:
            # Veritabanından tüm araçları al
            araclar = self.db_manager.arac_listesi_al()
            
            # Mevcut sistemin akıllı eşleştirmesini kullan
            eslesme = self.db_manager._smart_name_match(arac_adi, araclar)
            
            if eslesme:
                return True
            else:
                print(f"❌ Araç bulunamadı: '{arac_adi}' veritabanında mevcut değil!")
                return False
                
        except Exception as e:
            return True  # Hata durumunda sistemi bozma, kontrolü geç

    def operatoru_aktif_yap(self, kisi_adi, arac_adi=None):
        """Bir operatörün durumunu 'aktif' olarak günceller ve kullandığı aracı kaydeder."""
        # Önce araç kontrolü yap
        if arac_adi and not self.arac_kontrol_et(arac_adi):
            print(f"❌ HATA: '{arac_adi}' araç veritabanında bulunamadı. Görev ataması iptal edildi.")
            return False
        print(f"DEBUG:{self.arac_kontrol_et(arac_adi)}araçlar ")
        eslesen_kisi = self.operator_bul(kisi_adi)
        if eslesen_kisi:
            print(f"\nDEBUG: Operatör bulunuyor: {eslesen_kisi}...")
            self.df_kisiler.loc[self.df_kisiler['Operatör'] == eslesen_kisi, 'Durum'] = 'aktif'
            self.df_kisiler.loc[self.df_kisiler['Operatör'] == eslesen_kisi, 'Kullandığı Araç'] = arac_adi
            print(f"\n'{eslesen_kisi}' adlı operatöre görev atandı.")
            return True
        else:
            print(f"\nUyarı: '{kisi_adi}' operatör listesiyle eşleşmedi.")
            return False

    def operatoru_bosa_al(self, isim_iceren_metin):
        """Bir operatörün durumunu 'boşta' olarak günceller ve kullandığı aracın adını ve kendi adını döndürür."""
        # Metinden "işi bitti" ifadesini çıkararak sadece isim kısmını bırakır.
        olasi_isim = isim_iceren_metin.lower().replace("işi bitti", "").strip()
        print(f"olasi isim: {olasi_isim}")
        eslesen_kisi = self.operator_bul(olasi_isim)
        print(f"eslesen kisi: {eslesen_kisi}")
        if eslesen_kisi:
            # Operatörün kullandığı aracı al
            kullanilan_arac_sorgu = self.df_kisiler['Operatör'] == eslesen_kisi
            kullanilan_arac = self.df_kisiler.loc[kullanilan_arac_sorgu, 'Kullandığı Araç'].iloc[0]
            
            # Operatörün durumunu ve araç bilgisini sıfırla
            self.df_kisiler.loc[kullanilan_arac_sorgu, ['Durum', 'Kullandığı Araç']] = ['boşta', None]
            
            print(f"\n'{eslesen_kisi}' adlı operatörün durumu 'boşta' olarak güncellendi.")
            return kullanilan_arac, eslesen_kisi # Kullandığı aracın ve operatörün adını döndür
        else:
            print("\n'işi bitti' komutu için geçerli bir operatör bulunamadı.")
            return None, None

    def is_musait(self, kisi_adi=None, arac_yoneticisi=None, arac_adi=None):
        """Hem operatörün hem de aracın müsait olup olmadığını kontrol eder."""
        if kisi_adi:
            eslesen_kisi = self.operator_bul(kisi_adi)
            if eslesen_kisi:
                durum = self.df_kisiler.loc[self.df_kisiler['Operatör'] == eslesen_kisi, 'Durum'].iloc[0]
                if durum != 'boşta':
                    return False, f"'{kisi_adi}' şu anda meşgul."
        if arac_adi and arac_yoneticisi:
            if not arac_yoneticisi.is_arac_musait(arac_adi):
                return False, f"'{arac_adi}' şu anda kullanımda."
        return True, "Müsait."

    def is_operator_musait(self, kisi_adi):
        """Belirtilen operatörün boşta olup olmadığını kontrol eder."""
        return self.is_musait(kisi_adi=kisi_adi)[0]

    def is_arac_musait(self, arac_adi):
        """Belirtilen aracın boşta olup olmadığını kontrol eder."""
        return self.is_musait(arac_adi=arac_adi)[0]
