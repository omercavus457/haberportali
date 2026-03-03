# haberportali
# 🤖 Yapay Zeka Destekli Haber Portalı

Bu proje, TRT Haber üzerinden güncel haberleri çeken ve **BERT (NLP)** modeli kullanarak kullanıcıya akıllı öneriler sunan bir web portalıdır.

## ✨ Özellikler
* **Web Scraping:** BeautifulSoup ile 5 farklı kategoriden canlı haber çekimi.
* **AI Öneri Sistemi:** Okuduğunuz habere en benzer 4 haber ve ufuk açıcı 1 farklı haber önerisi.
* **Duygu Analizi:** Haberlerin içeriklerine göre kategorizasyon.
* **Modern Arayüz:** Streamlit ile hazırlanmış kart tasarımlı Dashboard.

## 🚀 Nasıl Çalıştırılır?
1. Bu depoyu indirin.
2. Terminale şu komutu yazarak kütüphaneleri kurun:
   `pip install -r requirements.txt`
3. Projeyi başlatın:
   `python -m streamlit run haber_portal.py`
