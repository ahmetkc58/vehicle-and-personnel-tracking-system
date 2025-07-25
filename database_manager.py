import pyodbc
import re

class DatabaseManager:
    def __init__(self, server="DESKTOP-R738L1R", database="arac_takip"):
        """
        Veritabanı bağlantı dizesini oluşturur.
        """
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
        )
        self.connection = None

    def _normalize_name(self, name):
        """İsmi normalize eder - Türkçe karakterleri düzeltir, fazla boşlukları temizler"""
        if not name:
            return ""
        
        # Türkçe karakter dönüşümleri (daha doğru mapping)
        turkce_map = {
            'ç': 'c', 'Ç': 'c',
            'ğ': 'g', 'Ğ': 'g', 
            'ı': 'i', 'I': 'i', 'İ': 'i', 'i̇': 'i',
            'ö': 'o', 'Ö': 'o',
            'ş': 's', 'Ş': 's',
            'ü': 'u', 'Ü': 'u'
        }
        
        # Fazla boşlukları temizle ve küçük harfe çevir
        normalized = ' '.join(name.split()).lower()
        
        # Türkçe karakterleri değiştir
        for tr_char, en_char in turkce_map.items():
            normalized = normalized.replace(tr_char, en_char)
            
        return normalized

    def _smart_name_match(self, aranan_isim, mevcut_isimler):
        """Akıllı isim eşleştirme yapar"""
        if not aranan_isim or not mevcut_isimler:
            return None
            
        aranan_norm = self._normalize_name(aranan_isim)
        aranan_kelimeler = aranan_norm.split()
        
        en_iyi_eslesme = None
        en_yuksek_skor = 0
        
        
        for mevcut_isim in mevcut_isimler:
            mevcut_norm = self._normalize_name(mevcut_isim)
            mevcut_kelimeler = mevcut_norm.split()
            
            skor = 0
            
            # 1. Tam eşleşme (en yüksek skor)
            if aranan_norm == mevcut_norm:
                return mevcut_isim
            
            # 2. Tüm kelimeler eşleşiyor mu kontrol et
            if len(aranan_kelimeler) <= len(mevcut_kelimeler):
                eslesme_sayisi = 0
                for aranan_kelime in aranan_kelimeler:
                    for mevcut_kelime in mevcut_kelimeler:
                        if aranan_kelime == mevcut_kelime:
                            eslesme_sayisi += 1
                            break
                        elif len(aranan_kelime) >= 3 and (aranan_kelime in mevcut_kelime or mevcut_kelime in aranan_kelime):
                            eslesme_sayisi += 0.7
                            break
                
                skor = (eslesme_sayisi / len(aranan_kelimeler)) * 100
            
            # 3. Kısmi eşleşme için ek puanlar
            if aranan_norm in mevcut_norm or mevcut_norm in aranan_norm:
                skor += 20
                
            
            # En yüksek skoru güncelle
            if skor > en_yuksek_skor and skor >= 60:  # En az %60 eşleşme gerekli
                en_yuksek_skor = skor
                en_iyi_eslesme = mevcut_isim
        
        if en_iyi_eslesme:
        
            return en_iyi_eslesme

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string)
            print("Veritabanına başarıyla bağlanıldı.")
        except pyodbc.Error as e:
            print("Veritabanına bağlanırken hata oluştu:", e)

    def arac_listesi_al(self):
        """Veritabanından araç listesini alır."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("SELECT Arac FROM Araclar WHERE Arac IS NOT NULL")
            araclar = [row[0].strip() if row[0] else '' for row in cursor.fetchall()]
            
            # Boş olanları filtrele
            araclar = [arac for arac in araclar if arac]
            
            return araclar
            
        except Exception as e:
            print(f"Araç listesi alınırken hata oluştu: {e}")
            return []

    def gorev_ekle(self, tablo_adi, gorev_verisi):
        """
        Veritabanına görev eklemek için bir fonksiyon.
        :param tablo_adi: Görevlerin ekleneceği tablo adı.
        :param gorev_verisi: Sözlük formatında görev verileri (ör. {"column1": "value1", "column2": "value2"}).
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return

        sutunlar = ', '.join(gorev_verisi.keys())
        yer_tutucular = ', '.join(['?'] * len(gorev_verisi))
        degerler = list(gorev_verisi.values())

        sorgu = f"INSERT INTO {tablo_adi} ({sutunlar}) VALUES ({yer_tutucular})"

        try:
            cursor = self.connection.cursor()
            cursor.execute(sorgu, degerler)
            self.connection.commit()
            print("Görev başarıyla eklendi.")
        except pyodbc.Error as e:
            print("Görev eklenirken hata oluştu:", e)

    def aktif_gorev_ekle(self, gorev_verisi):
        """
        'Aktif_isler' tablosuna yeni bir aktif görev ekler.
        :param gorev_verisi: Görev detaylarını içeren sözlük (ör. {"Personel": "Ahmet Yılmaz", "Arac": "Vinç 1", "Gorev": "Taşıma", "Tahmini_bitis": datetime, "Durum": "Aktif"}).
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return

        sutunlar = ', '.join(gorev_verisi.keys())
        yer_tutucular = ', '.join(['?'] * len(gorev_verisi))
        degerler = list(gorev_verisi.values())

        sorgu = f"INSERT INTO Aktif_isler ({sutunlar}) VALUES ({yer_tutucular})"

        try:
            cursor = self.connection.cursor()
            cursor.execute(sorgu, degerler)
            self.connection.commit()
            print("Aktif görev başarıyla eklendi.")
        except pyodbc.Error as e:
            print("Aktif görev eklenirken hata oluştu:", e)

    def tamamlanan_gorev_ekle(self, gorev_verisi):
        """
        'Tamamlanan_isler' tablosuna yeni bir tamamlanan görev ekler.
        :param gorev_verisi: Görev detaylarını içeren sözlük (ör. {"Personel": "Ahmet Yılmaz", "Arac": "Vinç 1", "Gorev": "Taşıma", "Bitis_tarihi": datetime.now(), "Durum": "Tamamlandı", "Tahmini_bitis": datetime}).
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return


        # ID sütununu çıkar (IDENTITY sütunu olduğu için)
        gorev_kopyasi = gorev_verisi.copy()
        if 'ID' in gorev_kopyasi:
            del gorev_kopyasi['ID']
        if 'Id' in gorev_kopyasi:
            del gorev_kopyasi['Id']
        if 'id' in gorev_kopyasi:
            del gorev_kopyasi['id']

        sutunlar = ', '.join(gorev_kopyasi.keys())
        yer_tutucular = ', '.join(['?'] * len(gorev_kopyasi))
        degerler = list(gorev_kopyasi.values())

        sorgu = f"INSERT INTO Tamamlanan_isler ({sutunlar}) VALUES ({yer_tutucular})"

        try:
            cursor = self.connection.cursor()
            
            # Önce tabloyu kontrol et
            cursor.execute("SELECT name FROM sys.tables WHERE name = 'Tamamlanan_isler'")
            tablo_var = cursor.fetchone()
            
            if not tablo_var:
                print("HATA: 'Tamamlanan_isler' tablosu bulunamadı!")
                # Mevcut tabloları listele
                cursor.execute("SELECT name FROM sys.tables WHERE type = 'U'")
                tablolar = [row[0] for row in cursor.fetchall()]
                print(f"Mevcut tablolar: {tablolar}")
                return
            
            # Tablo sütunlarını kontrol et
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Tamamlanan_isler'
                ORDER BY ORDINAL_POSITION
            """)
            sutun_bilgileri = cursor.fetchall()
            
            # Ekleme işlemi
            cursor.execute(sorgu, degerler)
            etkilenen_satir = cursor.rowcount
            self.connection.commit()
            
            if etkilenen_satir > 0:
                print(f"✅ Tamamlanan görev başarıyla eklendi. ({etkilenen_satir} satır eklendi)")
            else:
                print("⚠️ UYARI: Hiçbir satır eklenmedi!")
                
        except pyodbc.Error as e:
            print(f"❌ Tamamlanan görev eklenirken hata oluştu: {e}")
            print(f"   SQL: {sorgu}")
            print(f"   Değerler: {degerler}")

    def operator_durum_guncelle(self, operator_adi, durum):
        """
        'Personeller' tablosunda belirli bir operatörün 'Durum' sütununu günceller.
        :param operator_adi: Operatörün adı.
        :param durum: Yeni durum.
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return

        try:
            cursor = self.connection.cursor()
            
            # Önce tabloyu ve sütunları kontrol et
            cursor.execute("SELECT name FROM sys.tables WHERE name = 'Personeller'")
            tablo_var = cursor.fetchone()
            
            if not tablo_var:
                print("HATA: 'Personeller' tablosu bulunamadı!")
                cursor.execute("SELECT name FROM sys.tables WHERE type = 'U'")
                tablolar = [row[0] for row in cursor.fetchall()]
                print(f"Mevcut tablolar: {tablolar}")
                return
            
            # Personeller tablosunun sütunlarını kontrol et
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Personeller'
                ORDER BY ORDINAL_POSITION
            """)
            sutunlar = [row[0] for row in cursor.fetchall()]
            
            # Durum sütunu var mı kontrol et
            if 'Durum' not in sutunlar:
                print("HATA: 'Personeller' tablosunda 'Durum' sütunu bulunamadı!")
                print(f"Mevcut sütunlar: {sutunlar}")
                return
            
            # Önce tam eşleşme dene
            kontrol_sorgu = "SELECT COUNT(*) FROM Personeller WHERE Personel = ?"
            cursor.execute(kontrol_sorgu, (operator_adi,))
            kayit_sayisi = cursor.fetchone()[0]
            
            gercek_isim = operator_adi
            
            if kayit_sayisi == 0:
                # Tam eşleşme yoksa, akıllı eşleştirme yap
                print(f"'{operator_adi}' tam eşleşme bulunamadı, akıllı arama yapılıyor...")
                
                cursor.execute("SELECT Personel FROM Personeller")
                tum_personeller = [row[0] for row in cursor.fetchall()]
                
                # Akıllı eşleştirme kullan
                eslesme = self._smart_name_match(operator_adi, tum_personeller)
                
                if eslesme:
                    gercek_isim = eslesme
                    print(f"Akıllı eşleşme bulundu: '{operator_adi}' -> '{gercek_isim}'")
                else:
                    print(f"HATA: '{operator_adi}' adında personel bulunamadı!")
                    print(f"Mevcut personeller: {tum_personeller}")
                    return
            
            # Güncelleme yap
            sorgu = "UPDATE Personeller SET Durum = ? WHERE Personel = ?"
            cursor.execute(sorgu, (durum, gercek_isim))
            etkilenen_satir = cursor.rowcount
            self.connection.commit()
            
            if etkilenen_satir > 0:
                print(f"'{gercek_isim}' için durum başarıyla güncellendi. ({etkilenen_satir} satır etkilendi)")
            else:
                print(f"UYARI: '{gercek_isim}' için hiçbir satır güncellenmedi!")
                
        except pyodbc.Error as e:
            print("Durum güncellenirken hata oluştu:", e)

    def arac_durum_guncelle(self, arac_adi, durum):
        """
        'Araclar' tablosunda belirli bir aracın 'Durum' sütununu günceller.
        :param arac_adi: Aracın adı.
        :param durum: Yeni durum.
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return

        try:
            cursor = self.connection.cursor()
            
            # Önce tabloyu ve sütunları kontrol et
            cursor.execute("SELECT name FROM sys.tables WHERE name = 'Araclar'")
            tablo_var = cursor.fetchone()
            
            if not tablo_var:
                print("HATA: 'Araclar' tablosu bulunamadı!")
                cursor.execute("SELECT name FROM sys.tables WHERE type = 'U'")
                tablolar = [row[0] for row in cursor.fetchall()]
                print(f"Mevcut tablolar: {tablolar}")
                return
            
            # Araclar tablosunun sütunlarını kontrol et
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Araclar'
                ORDER BY ORDINAL_POSITION
            """)
            sutunlar = [row[0] for row in cursor.fetchall()]
            
            # Durum sütunu var mı kontrol et
            if 'Durum' not in sutunlar:
                print("HATA: 'Araclar' tablosunda 'Durum' sütunu bulunamadı!")
                print(f"Mevcut sütunlar: {sutunlar}")
                return
            
            # Önce tam eşleşme dene
            kontrol_sorgu = "SELECT COUNT(*) FROM Araclar WHERE Arac = ?"
            cursor.execute(kontrol_sorgu, (arac_adi,))
            kayit_sayisi = cursor.fetchone()[0]
            
            gercek_isim = arac_adi
            
            if kayit_sayisi == 0:
                # Tam eşleşme yoksa, akıllı eşleştirme yap
                print(f"'{arac_adi}' tam eşleşme bulunamadı, akıllı arama yapılıyor...")
                
                cursor.execute("SELECT Arac FROM Araclar")
                tum_araclar = [row[0] for row in cursor.fetchall()]
                
                # Akıllı eşleştirme kullan
                eslesme = self._smart_name_match(arac_adi, tum_araclar)
                
                if eslesme:
                    gercek_isim = eslesme
                    print(f"Akıllı eşleşme bulundu: '{arac_adi}' -> '{gercek_isim}'")
                else:
                    print(f"HATA: '{arac_adi}' adında araç bulunamadı!")
                    print(f"Mevcut araçlar: {tum_araclar}")
                    return
            
            # Güncelleme yap
            sorgu = "UPDATE Araclar SET Durum = ? WHERE Arac = ?"
            cursor.execute(sorgu, (durum, gercek_isim))
            etkilenen_satir = cursor.rowcount
            self.connection.commit()
            
            if etkilenen_satir > 0:
                print(f"'{gercek_isim}' için durum başarıyla güncellendi. ({etkilenen_satir} satır etkilendi)")
            else:
                print(f"UYARI: '{gercek_isim}' için hiçbir satır güncellenmedi!")
                
        except pyodbc.Error as e:
            print("Durum güncellenirken hata oluştu:", e)

    def get_aktif_gorev(self, personel_adi):
        """
        'Aktif_isler' tablosundan belirli bir personelin aktif görevini alır
        :param personel_adi: Görevli personelin adı.
        :return: Görev bilgilerini içeren bir sözlük veya None.
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return None


        try:
            cursor = self.connection.cursor()
            
            # Önce tabloda hiç kayıt var mı kontrol et
            cursor.execute("SELECT COUNT(*) FROM Aktif_isler")
            toplam_kayit = cursor.fetchone()[0]
            
            if toplam_kayit == 0:
                return None
            
            # Tüm aktif personelleri al
            cursor.execute("SELECT Personel FROM Aktif_isler")
            aktif_personeller = [row[0] for row in cursor.fetchall()]
            
            # Önce tam eşleşme dene
            sorgu = "SELECT * FROM Aktif_isler WHERE Personel = ?"
            cursor.execute(sorgu, (personel_adi,))
            sonuc = cursor.fetchone()
            
            gercek_personel = personel_adi
            
            if not sonuc:
                # Tam eşleşme yoksa, akıllı eşleştirme yap
                print(f"'{personel_adi}' tam eşleşme bulunamadı, akıllı arama yapılıyor...")
                
                # Akıllı eşleştirme kullan
                eslesme = self._smart_name_match(personel_adi, aktif_personeller)
                
                if eslesme:
                    gercek_personel = eslesme
                    print(f"Akıllı eşleşme bulundu: '{personel_adi}' -> '{gercek_personel}'")
                    # Eşleşen personel ile tekrar sorgula
                    cursor.execute(sorgu, (gercek_personel,))
                    sonuc = cursor.fetchone()
                else:
                    return None
            
            if sonuc:
                sutunlar = [column[0] for column in cursor.description]
                gorev_dict = dict(zip(sutunlar, sonuc))
                return gorev_dict
            else:
                return None
                
        except pyodbc.Error as e:
            return None

    def aktif_gorev_sil(self, personel_adi):
        """
        'Aktif_isler' tablosundan belirli bir personelin görevini siler.
        :param personel_adi: Görevli personelin adı.
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return

        try:
            cursor = self.connection.cursor()
            
            # Önce tam eşleşme dene
            kontrol_sorgu = "SELECT COUNT(*) FROM Aktif_isler WHERE Personel = ?"
            cursor.execute(kontrol_sorgu, (personel_adi,))
            kayit_sayisi = cursor.fetchone()[0]
            
            gercek_personel = personel_adi
            
            if kayit_sayisi == 0:
                # Tam eşleşme yoksa, akıllı eşleştirme yap
                print(f"'{personel_adi}' tam eşleşme bulunamadı, akıllı arama yapılıyor...")
                
                cursor.execute("SELECT Personel FROM Aktif_isler")
                aktif_personeller = [row[0] for row in cursor.fetchall()]
                
                # Akıllı eşleştirme kullan
                eslesme = self._smart_name_match(personel_adi, aktif_personeller)
                
                if eslesme:
                    gercek_personel = eslesme
                    print(f"Akıllı eşleşme bulundu: '{personel_adi}' -> '{gercek_personel}'")
                else:
                    print(f"HATA: '{personel_adi}' için aktif görev bulunamadı!")
                    print(f"Aktif görevli personeller: {aktif_personeller}")
                    return
            
            # Silme işlemi
            sorgu = "DELETE FROM Aktif_isler WHERE Personel = ?"
            cursor.execute(sorgu, (gercek_personel,))
            etkilenen_satir = cursor.rowcount
            self.connection.commit()
            
            if etkilenen_satir > 0:
                print(f"'{gercek_personel}' için aktif görev başarıyla silindi. ({etkilenen_satir} satır silindi)")
            else:
                print(f"UYARI: '{gercek_personel}' için hiçbir satır silinmedi!")
                
        except pyodbc.Error as e:
            print(f"Aktif görev silinirken hata oluştu: {e}")

    def operatoru_bosa_al(self, personel_adi):
        """
        Operatörü boşa alır - durumunu 'Boşta' yapar ve aracını boşaltır.
        :param personel_adi: Operatörün adı.
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return

        try:
            cursor = self.connection.cursor()
            
            # Önce personelin mevcut bilgilerini al
            cursor.execute("SELECT Personel, Arac FROM Personeller WHERE Personel = ?", (personel_adi,))
            personel_bilgisi = cursor.fetchone()
            
            gercek_personel = personel_adi
            
            if not personel_bilgisi:
                # Tam eşleşme yoksa, akıllı eşleştirme yap
                print(f"'{personel_adi}' tam eşleşme bulunamadı, akıllı arama yapılıyor...")
                
                cursor.execute("SELECT Personel FROM Personeller")
                tum_personeller = [row[0] for row in cursor.fetchall()]
                
                # Akıllı eşleştirme kullan
                eslesme = self._smart_name_match(personel_adi, tum_personeller)
                
                if eslesme:
                    gercek_personel = eslesme
                    print(f"Akıllı eşleşme bulundu: '{personel_adi}' -> '{gercek_personel}'")
                    # Eşleşen personel bilgilerini al
                    cursor.execute("SELECT Personel, Arac FROM Personeller WHERE Personel = ?", (gercek_personel,))
                    personel_bilgisi = cursor.fetchone()
                else:
                    print(f"HATA: '{personel_adi}' adında personel bulunamadı!")
                    return
            
            # Personelin kullandığı aracı al
            mevcut_arac = personel_bilgisi[1] if personel_bilgisi and len(personel_bilgisi) > 1 else None
            
            # Personelin durumunu 'Boşta' yap ve aracını boşalt
            cursor.execute("UPDATE Personeller SET Durum = ?, Arac = NULL WHERE Personel = ?", 
                          ("Boşta", gercek_personel))
            personel_etkilenen = cursor.rowcount
            
            # Eğer personelin aracı varsa, aracın durumunu da 'Boşta' yap
            arac_etkilenen = 0
            if mevcut_arac and mevcut_arac.strip():
                cursor.execute("UPDATE Araclar SET Durum = ? WHERE Arac = ?", 
                              ("Boşta", mevcut_arac))
                arac_etkilenen = cursor.rowcount
            
            self.connection.commit()
            
            if personel_etkilenen > 0:
                mesaj = f"'{gercek_personel}' başarıyla boşa alındı."
                if arac_etkilenen > 0:
                    mesaj += f" Aracı '{mevcut_arac}' da boşa alındı."
                print(mesaj)
            else:
                print(f"UYARI: '{gercek_personel}' için hiçbir değişiklik yapılmadı!")
                
        except pyodbc.Error as e:
            print(f"Operatör boşa alınırken hata oluştu: {e}")

    def operatoru_aktif_yap(self, personel_adi, arac_adi=None):
        """
        Operatörü aktif yapar ve belirtilen aracı ona atar.
        :param personel_adi: Operatörün adı.
        :param arac_adi: Atanacak aracın adı (opsiyonel).
        """
        if not self.connection:
            print("Veritabanına bağlantı kurulmamış. Önce connect() metodunu çağırın.")
            return

        try:
            cursor = self.connection.cursor()
            
            # Önce personeli bul
            cursor.execute("SELECT Personel FROM Personeller WHERE Personel = ?", (personel_adi,))
            personel_var = cursor.fetchone()
            
            gercek_personel = personel_adi
            
            if not personel_var:
                # Tam eşleşme yoksa, akıllı eşleştirme yap
                print(f"'{personel_adi}' tam eşleşme bulunamadı, akıllı arama yapılıyor...")
                
                cursor.execute("SELECT Personel FROM Personeller")
                tum_personeller = [row[0] for row in cursor.fetchall()]
                
                # Akıllı eşleştirme kullan
                eslesme = self._smart_name_match(personel_adi, tum_personeller)
                
                if eslesme:
                    gercek_personel = eslesme
                    print(f"Akıllı eşleşme bulundu: '{personel_adi}' -> '{gercek_personel}'")
                else:
                    print(f"HATA: '{personel_adi}' adında personel bulunamadı!")
                    return
            
            # Personelin durumunu 'Aktif' yap
            if arac_adi:
                cursor.execute("UPDATE Personeller SET Durum = ?, Arac = ? WHERE Personel = ?", 
                              ("Aktif", arac_adi, gercek_personel))
                # Aracın durumunu da 'Aktif' yap
                cursor.execute("UPDATE Araclar SET Durum = ? WHERE Arac = ?", 
                              ("Aktif", arac_adi))
            else:
                cursor.execute("UPDATE Personeller SET Durum = ? WHERE Personel = ?", 
                              ("Aktif", gercek_personel))
            
            etkilenen_satir = cursor.rowcount
            self.connection.commit()
            
            if etkilenen_satir > 0:
                mesaj = f"'{gercek_personel}' başarıyla aktif yapıldı."
                if arac_adi:
                    mesaj += f" Aracı: '{arac_adi}'"
                print(mesaj)
            else:
                print(f"UYARI: '{gercek_personel}' için hiçbir değişiklik yapılmadı!")
                
        except pyodbc.Error as e:
            print(f"Operatör aktif yapılırken hata oluştu: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            print("Veritabanı bağlantısı kapatıldı.")
