# vehicle-and-personnel-tracking-system
This project is an LLM project developed to track when employees in the company do what work and which tools they use.








bu projenin en güncel sürümüdür veriler veri tabanına dinamik olarak işlnemektedir

---

### Proje Özeti
Bu proje, bir araç takip ve görev yönetim sistemidir. Aşağıdaki ana bileşenlerden oluşur:

1. **Görev Yönetimi:**
   - Görevlerin atanması, tamamlanması ve süre uzatma işlemleri yapılabilir.
   - Görevler dinamik olarak veritabanına kaydedilir.

2. **Araç ve Operatör Yönetimi:**
   - Araçların ve operatörlerin durumları (boşta/aktif) takip edilir.
   - Operatörlere araç atamaları yapılabilir.

3. **Veritabanı Entegrasyonu:**
   - SQL Server kullanılarak araçlar, operatörler ve görevler dinamik olarak yönetilir.

4. **Kullanıcı Arayüzü:**
   - Streamlit tabanlı bir arayüz ile kullanıcılar görev ve durum bilgilerini görüntüleyebilir.

5. **Doğal Dil İşleme:**
   - Kullanıcıdan alınan metinler analiz edilerek komut türü (yeni görev, süre uzatma, görev bitirme) belirlenir.

6. **API Entegrasyonu:**
   - Ollama API kullanılarak metin analizi yapılır.

### Kullanılan Teknolojiler
- **Python**: Projenin ana programlama dili.
- **Streamlit**: Kullanıcı arayüzü için.
- **SQLAlchemy ve pyodbc**: Veritabanı bağlantısı ve işlemleri için.
- **TheFuzz**: Yazım hatalarını tolere eden eşleştirme algoritmaları için.
- **Ollama API**: Doğal dil işleme için.

### Kurulum
1. Gerekli bağımlılıkları yüklemek için `requirements.txt` dosyasını kullanabilirsiniz.
2. Veritabanı bağlantı ayarlarını `DatabaseManager` sınıfında yapılandırın.
3. Streamlit uygulamasını başlatmak için aşağıdaki komutu çalıştırın:
   ```bash
   streamlit run app_gui.py
   ```
