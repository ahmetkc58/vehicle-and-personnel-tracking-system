from pdb import main
import requests
import json

# Ollama sunucu URL'si (varsayılan olarak localhost:11434)
OLLAMA_BASE_URL = "http://localhost:11434"

def ollama_yapilandir(base_url=None):
    """Ollama sunucu URL'sini yapılandırır."""
    global OLLAMA_BASE_URL
    if base_url:
        OLLAMA_BASE_URL = base_url

def ollama_istek_gonder(prompt, model="qwen2.5vl:3b"):
    """Ollama API'sine istek gönderir ve yanıtı döndürür."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        print(f"Ollama API hatası: {e}")
        return None

def metin_analiz_et(metin, model="qwen2.5vl:3b"):
    """Verilen metni Ollama API kullanarak analiz eder ve görev türünü belirler."""
    
    print(f"DEBUG: Analiz edilen metin: '{metin}'")
    
    # Önce basit kelime kontrolü yapalım
    metin_lower = metin.lower()
    
    # Görev bitti kontrolü
    bitti_kelimeleri = ['bitti', 'tamamlandı', 'bitirdi', 'tamamladı', 'bitmiş', 'tamamlanmış']
    if any(kelime in metin_lower for kelime in bitti_kelimeleri):
        # İsim çıkarma için gelişmiş yaklaşım
        kelimeler = metin.split()
        if kelimeler:
            # Bitti kelimesinin konumunu bul
            bitti_index = -1
            for i, kelime in enumerate(kelimeler):
                if any(bitti_kelime in kelime.lower() for bitti_kelime in bitti_kelimeleri):
                    bitti_index = i  # i-1 değil, i olmalı
                    break
            
            # İsmi topla (bitti kelimesinden önceki kelimeler)
            if bitti_index > 0:
                isim = ' '.join(kelimeler[:bitti_index])
            elif bitti_index == 0:
                # Eğer cümle "bitti" ile başlıyorsa, sonraki kelimelere bak
                # Örnek: "bitti Ali Baydemi"
                if len(kelimeler) > 1:
                    isim = ' '.join(kelimeler[1:])
                else:
                    isim = kelimeler[0]
            else:
                # Bitti kelimesi bulunamadıysa (bu durumda olmamalı ama güvenlik için)
                isim = kelimeler[0]
            
            # "işi", "görevi" gibi kelimeleri temizle
            temizlenecek_kelimeler = ['işi', 'görevi', 'is', 'gorev']
            isim_kelimeler = isim.split()
            temiz_kelimeler = [k for k in isim_kelimeler if k.lower() not in temizlenecek_kelimeler]
            
            if temiz_kelimeler:
                isim = ' '.join(temiz_kelimeler)
            
            # Noktalama işaretlerini temizle
            isim = isim.strip('.,!?;:"()[]{}')
            
            
            return {
                "komut_turu": "gorev_bitti",
                "person": isim
            }
    
    # Süre uzatma kontrolü
    uzatma_kelimeleri = ['uzat', 'ekle', 'daha', 'artır', 'uzatma']
    if any(kelime in metin_lower for kelime in uzatma_kelimeleri):
        # Süre uzatma için Ollama'ya sor
        prompt = f"""Bu metin bir süre uzatma komutu. Kişi adını ve süreyi çıkar:
        
            Metin: "{metin}"

            JSON formatında yanıt ver:
            {{
            "person": "kişi adı ve soyadı (örneğin: Ahmet Yılmaz)",
            "duration": {{
                "value": sayısal_değer,
                "unit": "saat/gün/dakika"
            }}
            }}"""
        
        try:
            yanit = ollama_istek_gonder(prompt, model)
            if yanit:
                cleaned_response = yanit.strip().replace("```json", "").replace("```", "").strip()
                parsed_data = json.loads(cleaned_response)
                parsed_data["komut_turu"] = "sure_uzatma"
                return parsed_data
        except Exception as e:
            print(f"Süre uzatma analizi hatası: {e}")
            return None
    
    # Yeni görev için Ollama'ya sor
    prompt = f"""Bu metin yeni bir görev ataması. Bilgileri dikkatli şekilde çıkar:

                Metin: "{metin}"

                KURALLAR:
                - Kişi adını tam olarak çıkar (ad + soyad)
                - Eğer metinde araç belirtilmişse (vinç, kamyon, forklift vb.) SADECE BİR ARAÇ adını çıkar
                - Birden fazla araç varsa ana kullanılacak aracı seç 
                - Araç numarası varsa dahil et (örnek: vinç 1, kamyon 3)
                - "ile" kelimesinden sonra gelen araç genellikle kullanılacak araçtır
                - Eğer hiç araç yok ise null döndür
                - Vehicle alanına SADECE TEK ARAÇ ADI yaz, virgül kullanma
                - Görev açıklamasını net şekilde çıkar
                - Süre bilgisini dikkatli çıkar

                ÖRNEKLEr:
                "Ali tankı vinç 1 ile taşıyacak" -> vehicle: "vinç 1" (tank değil!)
                "Mehmet vinç 2 ve kamyon 3 kullanacak" -> vehicle: "vinç 2" (ilkini seç)

                JSON formatında yanıt ver:
                {{
                "person": "kişi adı ve soy adı (örneğin: Ahmet Yılmaz)",
                "task": "görev açıklaması",
                "duration": {{
                    "value": sayısal_değer,
                    "unit": "saat/gün/dakika"
                }},
                "vehicle": "TEK araç adı (örnek: vinç 1) veya null"
                }}"""
    
    try:
        yanit = ollama_istek_gonder(prompt, model)
        print("yanıt:",yanit)
        if not yanit:
            return None
            
        # JSON yanıtını temizle
        cleaned_response = yanit.strip().replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(cleaned_response)
        parsed_data["komut_turu"] = "yeni_gorev"
        return parsed_data
        
    except Exception as hata:
        print(f"API Hatası veya JSON ayrıştırma hatası: {hata}")
        return None

# Geriye dönük uyumluluk için eski isimleri koruyalım
configure_ollama = ollama_yapilandir
send_ollama_request = ollama_istek_gonder

def parse_task_info(metin, model="qwen2.5vl:3b"):
    """Eski API uyumluluğu için - yeni görev bilgilerini döndürür"""
    result = metin_analiz_et(metin, model)
    if result and result.get('komut_turu') == 'yeni_gorev':
        return {
            'person': result.get('person'),
            'task': result.get('task'),
            'duration': result.get('duration'),
            'vehicle': result.get('vehicle')
        }
    return None

def parse_update_info(text, model="qwen2.5vl:3b"):
    """Eski API uyumluluğu için - süre uzatma bilgilerini döndürür"""
    result = metin_analiz_et(text, model)
    if result and result.get('komut_turu') == 'sure_uzatma':
        return {
            'person': result.get('person'),
            'duration': result.get('duration')
        }
    return None

# Türkçe isimler
gorev_bilgisi_ayristir = parse_task_info
guncelleme_bilgisi_ayristir = parse_update_info

# Test fonksiyonu
def test_metin_analiz():
    """Metin analiz fonksiyonunu test eder"""
    test_metinleri = [
        "Ali Baydemi bitti",
        "Ali Baydemi işi bitti", 
        "Ahmet Yılmaz tamamlandı",
        "bitti Ali Baydemi",
        "Murat Aslantaş bitirdi",
        "İş bitti Ali Baydemi"
    ]
    
    print("=== METİN ANALİZ TEST ===")
    for metin in test_metinleri:
        sonuc = metin_analiz_et(metin)
        if sonuc:
            print(f"'{metin}' -> Kişi: '{sonuc.get('person')}', Komut: {sonuc.get('komut_turu')}")
        else:
            print(f"'{metin}' -> Analiz edilemedi")

if __name__ == "__main__":
    test_metin_analiz()
