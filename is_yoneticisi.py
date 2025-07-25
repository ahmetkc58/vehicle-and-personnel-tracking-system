from database_manager import DatabaseManager

class IsYoneticisi:
    """Aktif görevleri veritabanında yönetir."""
    def __init__(self, db_manager: DatabaseManager):
        """DatabaseManager örneği ile başlatılır."""
        self.db_manager = db_manager

    def _arac_kontrol_et(self, arac_adi):
        """Veritabanında araç bulunup bulunmadığını kontrol eder."""
        if not arac_adi:
            return True  # Eğer araç adı boşsa kontrolü geç
            
        try:
            # Veritabanından tüm araçları al
            araclar = self.db_manager.arac_listesi_al()
            
            if not araclar:
                return True  # Araç listesi alınamazsa kontrolü geç, sistemi bozma
                
            # Basit kontrol - mevcut sistemin akıllı eşleştirmesini kullan
            eslesme = self.db_manager._smart_name_match(arac_adi, araclar)
            
            if eslesme:
                return True
            else:
                print(f"❌ Araç bulunamadı: '{arac_adi}' veritabanında mevcut değil!")
                return False
                
        except Exception as e:
            return True  # Hata durumunda sistemi bozma, kontrolü geç

    def is_ekle(self, gorevli, arac, gorev, bitis_tarihi):
        """Veritabanına yeni bir iş ekler."""
        if gorevli and gorev:
            # Araç kontrolü yap
            if arac and not self._arac_kontrol_et(arac):
                print(f"❌ HATA: '{arac}' araç veritabanında bulunamadı. Görev eklenmedi.")
                return False
                
            try:
                self.db_manager.aktif_gorev_ekle({
                    "Personel": gorevli,
                    "Arac": arac,
                    "Gorev": gorev,
                    "Tahmini_bitis": bitis_tarihi.strftime('%Y-%m-%d %H:%M:%S') if bitis_tarihi else None,
                    "Durum": "Aktif"
                })
                print(f"'{gorevli}' için görev başarıyla eklendi.")
                return True
            except Exception as e:
                print(f"Görev eklenirken hata oluştu: {e}")
                return False
        return False

    def is_bitir(self, gorevli):
        """Verilen görevliyi tamamlanmış olarak işaretler."""
        try:
            self.db_manager.operator_durum_guncelle(gorevli, "Boşta")
            print(f"'{gorevli}' için görev tamamlandı ve durum güncellendi.")
        except Exception as e:
            print(f"Görev tamamlanırken hata oluştu: {e}")

    def süre_uzat(self, gorevli, sure_bilgisi):
        """Verilen görevlinin işinin bitiş süresini uzatır."""
        try:
            # Süre uzatma işlemi için veritabanında ilgili kaydı güncelle
            mevcut_bitis = self.db_manager.get_bitis_tarihi(gorevli)  # Bu metodun DatabaseManager'da tanımlı olduğunu varsayıyoruz
            if not mevcut_bitis:
                return False, f"'{gorevli}' için aktif bir iş bulunamadı."

            from datetime import timedelta
            deger = int(sure_bilgisi['value'])
            birim = sure_bilgisi['unit'].lower()
            eklenecek_sure = timedelta()
            if 'saat' in birim:
                eklenecek_sure = timedelta(hours=deger)
            elif 'gün' in birim:
                eklenecek_sure = timedelta(days=deger)
            elif 'dakika' in birim:
                eklenecek_sure = timedelta(minutes=deger)

            yeni_bitis = mevcut_bitis + eklenecek_sure
            self.db_manager.update_bitis_tarihi(gorevli, yeni_bitis)  # Bu metodun DatabaseManager'da tanımlı olduğunu varsayıyoruz
            return True, f"'{gorevli}' görevinin süresi başarıyla uzatıldı."
        except Exception as e:
            return False, f"Hata: {e}"
