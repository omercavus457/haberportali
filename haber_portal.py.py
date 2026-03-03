import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util

# 1. Yapay Zeka Modelini Yükle (Türkçe destekli hafif bir model)
# Bu model cümleleri matematiksel vektörlere çevirir.
model = SentenceTransformer('dbmdz/bert-base-turkish-cased')

def haber_cek():
    url = "https://www.trthaber.com/haber/guncel/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")
    
    haber_listesi = []
    # TRT Haber'in güncel kart yapısı
    kartlar = soup.find_all("div", class_="standard-card")
    
    for k in kartlar:
        a_etiketi = k.find("a")
        if not a_etiketi: continue
        
        baslik = a_etiketi.get("title") or a_etiketi.text.strip()
        link = a_etiketi["href"]
        if not link.startswith("http"): link = "https://www.trthaber.com" + link
        
        # Duygu Analizi (Senin istediğin mantık)
        durum = "Nötr"
        iyi = ["kurtarıldı", "sağ salim", "müjde", "sevinç", "başarı"]
        kotu = ["saldırı", "patlama", "şehit", "vefat", "kayıp", "füze"]
        
        if any(w in baslik.lower() for w in iyi): durum = "İyi Haber 😊"
        elif any(w in baslik.lower() for w in kotu): durum = "Kötü Haber 😔"
        
        # Haberin "Anlam Vektörünü" oluştur (Öneri sistemi için)
        vektor = model.encode(baslik, convert_to_tensor=True)
        
        haber_listesi.append({
            "baslik": baslik,
            "link": link,
            "durum": durum,
            "vektor": vektor
        })
    return haber_listesi

# --- ÇALIŞTIRMA ---
haberler = haber_cek()

if not haberler:
    print("Haber bulunamadı, site yapısı değişmiş olabilir.")
else:
    # İlk haberi "okunan haber" varsayalım (Örn: Kedi kurtarma haberi olsun)
    okunan_haber = haberler[0]
    print(f"Şu an okuduğunuz: {okunan_haber['baslik']} ({okunan_haber['durum']})\n")
    print("--- Benzer Önerilen Haberler ---")

    # Diğer haberlerle benzerlik karşılaştırması yapalım
    for diger_haber in haberler[1:6]:
        # Cosine Similarity ile iki haberin birbirine ne kadar benzediğini buluyoruz
        benzerlik_skoru = util.cos_sim(okunan_haber['vektor'], diger_haber['vektor']).item()
        
        # Eğer benzerlik %40'tan fazlaysa listele
        if benzerlik_skoru > 0.40:
            print(f"[%{benzerlik_skoru*100:.1f} Benzer] - {diger_haber['baslik']}")