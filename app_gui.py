import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from operator_manager import OperatorYoneticisi
from ollama import metin_analiz_et
from arac_yoneticisi import AracYoneticisi
from is_yoneticisi import IsYoneticisi
from database_manager import DatabaseManager
from sqlalchemy import create_engine

def main():
    st.set_page_config(page_title="Görev Yönetim Sistemi", layout="wide")
    st.title("Görev Yönetim Sistemi")

    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        st.session_state.db_manager.connect()

    db_manager = st.session_state.db_manager

    # SQLAlchemy engine oluştur
    engine = create_engine("mssql+pyodbc:///?odbc_connect=" + db_manager.connection_string)

    st.subheader("Metin Girişi")
    metin = st.text_input("Metni giriniz (ör: 'Ahmet Yılmaz işi bitti' veya yeni görev)", key="metin_giris")
    if st.button("İşle"):
        if metin:
            # Metni analiz et ve komut türünü belirle
            analiz_sonucu = metin_analiz_et(metin)
            
            if not analiz_sonucu:
                st.error("Metin analiz edilemedi. Lütfen tekrar deneyin.")
                return
                
            komut_turu = analiz_sonucu.get('komut_turu')
            
            if komut_turu == 'sure_uzatma':
                # Süre uzatma komutu
                gelen_kisi = analiz_sonucu.get('person')
                sure_bilgisi = analiz_sonucu.get('duration')
                
                if gelen_kisi and sure_bilgisi:
                    try:
                        db_manager.operator_durum_guncelle(gelen_kisi, "Aktif")
                        st.success(f"{gelen_kisi} için süre uzatıldı: {sure_bilgisi['value']} {sure_bilgisi['unit']}")
                    except Exception as e:
                        st.error(f"Hata: {e}")
                else:
                    st.warning("Süre uzatma bilgisi eksik.")
                    
            elif komut_turu == 'gorev_bitti':
                # Görev bitti komutu
                personel_adi = analiz_sonucu.get('person')
                
                if personel_adi:
                    try:
                        
                        # Önce aktif görev var mı kontrol et
                        tamamlanan_gorev = db_manager.get_aktif_gorev(personel_adi)
                        
                        if tamamlanan_gorev:
                            
                            # Bitiş tarihini ve durumu güncelle
                            tamamlanan_gorev['Bitis_tarihi'] = datetime.now()
                            tamamlanan_gorev['Durum'] = 'Tamamlandı'
                            
                            # Tamamlanan görevi ekle
                            db_manager.tamamlanan_gorev_ekle(tamamlanan_gorev)
                            
                            # Aktif görevden sil
                            db_manager.aktif_gorev_sil(personel_adi)
                            
                            # Operatörü boşa al ve aracını güncelle
                            db_manager.operatoru_bosa_al(personel_adi)
                            
                            st.success(f"{personel_adi} işi bitti olarak güncellendi ve tamamlanan görevlere eklendi.")
                        else:
                            
                            # Yine de operatör durumunu güncelle
                            db_manager.operator_durum_guncelle(personel_adi, "Boşta")
                            
                            st.warning(f"{personel_adi} için aktif görev bulunamadı, sadece durum 'Boşta' olarak güncellendi.")
                            
                    except Exception as e:
                        st.error(f"Hata: {e}")
                else:
                    st.warning("Personel adı bulunamadı.")
                    
            elif komut_turu == 'yeni_gorev':
                # Yeni görev komutu
                gelen_kisi = analiz_sonucu.get('person')
                gorev = analiz_sonucu.get('task')
                arac = analiz_sonucu.get('vehicle')
                sure_bilgisi = analiz_sonucu.get('duration')
                bitis_zamani = None
                
                if sure_bilgisi and 'value' in sure_bilgisi and 'unit' in sure_bilgisi:
                    try:
                        deger = int(sure_bilgisi['value'])
                        birim = sure_bilgisi['unit'].lower()
                        if 'saat' in birim:
                            bitis_zamani = datetime.now() + timedelta(hours=deger)
                        elif 'gün' in birim:
                            bitis_zamani = datetime.now() + timedelta(days=deger)
                        elif 'dakika' in birim:
                            bitis_zamani = datetime.now() + timedelta(minutes=deger)
                    except (ValueError, TypeError):
                        pass
                        
                if gelen_kisi and gorev:
                    # İş yöneticisi oluştur ve araç kontrolü yap
                    is_yoneticisi = IsYoneticisi(db_manager)
                    
                    try:
                        # is_ekle metodu artık araç kontrolü yapıyor
                        basarili = is_yoneticisi.is_ekle(
                            gorevli=gelen_kisi,
                            arac=arac,
                            gorev=gorev,
                            bitis_tarihi=bitis_zamani
                        )
                        
                        if basarili:
                            # Operatörü aktif yap
                            db_manager.operatoru_aktif_yap(gelen_kisi, arac)
                            print(f"DEBUG: operatör eklendi: {gelen_kisi}, Araç: {arac}")
                            st.success(f"{gelen_kisi} için yeni görev eklendi: {gorev}")
                           
                        else:
                            st.error("Görev eklenemedi. Araç kontrolü başarısız oldu.")
                            
                    except Exception as e:
                        st.error(f"Hata: {e}")
                else:
                    st.warning("Yeni görev bilgileri eksik.")
            else:
                st.warning("Komut türü anlaşılamadı. Lütfen daha açık bir ifade kullanın.")

    # Aktif İşler tablosunu göster
    st.subheader("Aktif İşler")
    try:
        aktif_isler = pd.read_sql_query("SELECT [Personel],[Arac],[Gorev],[Tahmini_bitis],[Durum] FROM Aktif_isler", engine)
        st.dataframe(aktif_isler, use_container_width=True)
    except Exception as e:
        st.error(f"Aktif işler yüklenirken hata oluştu: {e}")

    # Tamamlanan İşler tablosunu göster
    st.subheader("Tamamlanan İşler")
    try:
        tamamlanan_isler = pd.read_sql_query("SELECT [Personel],[Arac],[Gorev],[Tahmini_bitis],[Durum] FROM Tamamlanan_isler", engine)
        st.dataframe(tamamlanan_isler, use_container_width=True)
    except Exception as e:
        st.error(f"Tamamlanan işler yüklenirken hata oluştu: {e}")

    # Operatör ve Araç durumlarını göster
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Operatör Durumları")
        try:
            operator_durumlari = pd.read_sql_query("SELECT [Personel],[Durum],[Arac] FROM Personeller", engine)
            st.dataframe(operator_durumlari, use_container_width=True)
        except Exception as e:
            st.error(f"Operatör durumları yüklenirken hata oluştu: {e}")
    with col2:
        st.subheader("Araç Durumları")
        try:
            arac_durumlari = pd.read_sql_query("SELECT [Arac],[Durum] FROM Araclar", engine)
            st.dataframe(arac_durumlari, use_container_width=True)
        except Exception as e:
            st.error(f"Araç durumları yüklenirken hata oluştu: {e}")

if __name__ == "__main__":
    main()

