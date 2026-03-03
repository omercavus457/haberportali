import streamlit as st
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util

# --- SAYFA AYARLARI ---
# Grid yapısının güzel durması için 'wide' (geniş ekran) moduna geçtik
st.set_page_config(page_title="AI Destekli Haber Portalı", layout="wide")

@st.cache_resource
def model_yukle():
    return SentenceTransformer('dbmdz/bert-base-turkish-cased')

model = model_yukle()

# 1. Aşama: Kategorili Veri Çekme
@st.cache_data(ttl=3600)
def haberleri_getir():
    # Kategorileri isimleriyle birlikte sözlük yapısında tutuyoruz
    kategoriler = {
        "Güncel": "https://www.trthaber.com/haber/guncel/",
        "Dünya / Savaş": "https://www.trthaber.com/haber/dunya/",
        "Ekonomi": "https://www.trthaber.com/haber/ekonomi/",
        "Spor": "https://www.trthaber.com/haber/spor/",
        "Sağlık": "https://www.trthaber.com/haber/saglik/"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    haberler = []
    sayac = 0
    
    for kat_isim, url in kategoriler.items():
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, "html.parser")
            kartlar = soup.find_all("div", class_="standard-card")
            
            for k in kartlar:
                a = k.find("a")
                if not a: continue
                
                baslik = a.get("title") or a.text.strip()
                link = a["href"]
                if not link.startswith("http"): link = "https://www.trthaber.com" + link
                
                if any(h['link'] == link for h in haberler):
                    continue
                    
                img = k.find("img")
                gorsel = img.get("data-src") or img.get("src") or "" if img else ""
                
                haberler.append({
                    "id": sayac, 
                    "baslik": baslik, 
                    "link": link, 
                    "gorsel": gorsel,
                    "kategori": kat_isim # Haberin hangi kategoriden geldiğini kaydediyoruz
                })
                sayac += 1
        except Exception:
            continue
            
    return haberler

data = haberleri_getir()

# 2. Aşama: Vektörleri Önceden Hesapla
@st.cache_data
def vektorleri_hesapla(_model, haberler_listesi):
    basliklar = [h['baslik'] for h in haberler_listesi]
    return _model.encode(basliklar, convert_to_tensor=True)

vektorler = vektorleri_hesapla(model, data)

# 3. Aşama: İçerik Detayını Çekme
@st.cache_data
def haber_detayi_getir(link):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(link, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, "html.parser")
        
        icerik_alani = soup.find("div", class_="editor-text") or soup.find("article")
        paragraflar = icerik_alani.find_all("p") if icerik_alani else soup.find_all("p")
            
        metinler = [p.text.strip() for p in paragraflar if len(p.text.strip()) > 30]
        return "\n\n".join(metinler) if metinler else "Bu haberin detaylı metni okunamadı."
    except Exception:
        return "İçerik yüklenirken bir sorun oluştu."

# --- NAVİGASYON VE ARAYÜZ ---
if 'secilen_haber' not in st.session_state:
    st.session_state.secilen_haber = None

# SAYFA 1: HABER DETAYI VE ÖNERİLER
if st.session_state.secilen_haber is not None:
    haber = st.session_state.secilen_haber
    
    if st.button("⬅️ Geri Dön"):
        st.session_state.secilen_haber = None
        st.rerun()
    
    # Haber Düzeni: Başlık -> Görsel -> Açıklama
    st.title(haber['baslik'])
    st.caption(f"Kategori: {haber['kategori']}")
    
    # Ortalanmış ve estetik görsel sunumu
    if haber['gorsel']:
        st.image(haber['gorsel'], use_container_width=True)
        
    with st.spinner("Haberin tam metni yükleniyor..."):
        tam_metin = haber_detayi_getir(haber['link'])
        
    st.write(tam_metin)
    st.markdown(f"**[Orijinal içerik]({haber['link']})**")
    
    st.divider()
    st.subheader("İlginizi Çekebilecek Diğer Haberler")
    
    # AI Algoritması (4 Benzer + 1 Farklı)
    secilen_vektor = vektorler[haber['id']]
    skorlar = []
    
    for i, diger in enumerate(data):
        if diger['id'] != haber['id']:
            skor = util.cos_sim(secilen_vektor, vektorler[i]).item()
            skorlar.append((skor, diger))
            
    skorlar.sort(key=lambda x: x[0], reverse=True)
    
    oneriler = [item[1] for item in skorlar[:4]]
    if len(skorlar) > 4:
        oneriler.append(skorlar[-1][1])
        
    # Önerileri yan yana şık kartlar şeklinde diz (5 sütun)
    oneri_sutunlari = st.columns(len(oneriler))
    for idx, o_haber in enumerate(oneriler):
        with oneri_sutunlari[idx]:
            with st.container(border=True): # Çerçeveli şık görünüm
                if o_haber['gorsel']:
                    st.image(o_haber['gorsel'], use_container_width=True)
                
                # Başlık çok uzunsa keselim ki tasarım bozulmasın
                gosterilecek_baslik = o_haber['baslik'][:60] + "..." if len(o_haber['baslik']) > 60 else o_haber['baslik']
                st.markdown(f"**{gosterilecek_baslik}**")
                
                # Dikdörtgen butonu en alta küçük olarak koyuyoruz
                if st.button("Oku", key=f"rec_{haber['id']}_{o_haber['id']}", use_container_width=True):
                    st.session_state.secilen_haber = o_haber
                    st.rerun()

# SAYFA 2: ANA LİSTE VE KATEGORİLER
else:
    st.title("📰 Gündem ve Haber Portalı")
    
    # Kategori Seçimi (Radyo Butonları / Hap Tasarım)
    kategori_secimi = st.radio(
        "Lütfen ilgilendiğiniz kategoriyi seçiniz:", 
        ["Tümü", "Güncel", "Dünya / Savaş", "Ekonomi", "Spor", "Sağlık"], 
        horizontal=True
    )
    
    st.divider()
    
    # Seçilen kategoriye göre veriyi filtrele
    if kategori_secimi == "Tümü":
        gosterilecek_haberler = data
    else:
        gosterilecek_haberler = [h for h in data if h['kategori'] == kategori_secimi]
        
    st.write(f"Seçili kategoride **{len(gosterilecek_haberler)}** haber listeleniyor.")
    
    # Şık Grid (Izgara) Tasarımı - Her satırda 4 haber
    sutun_sayisi = 4
    for i in range(0, len(gosterilecek_haberler), sutun_sayisi):
        cols = st.columns(sutun_sayisi)
        # O satırdaki haberleri sütunlara dağıt
        for j, h in enumerate(gosterilecek_haberler[i:i+sutun_sayisi]):
            with cols[j]:
                with st.container(border=True): # Kenarlıklı kart yapısı
                    if h['gorsel']:
                        st.image(h['gorsel'], use_container_width=True)
                    else:
                        st.info("Görsel Yok")
                        
                    # Yazıları kalın ve şık formatta yaz
                    st.markdown(f"**{h['baslik']}**")
                    
                    # Kartın içine tıklama butonu ekle
                    if st.button("Haberi Oku", key=f"main_{h['id']}", use_container_width=True):
                        st.session_state.secilen_haber = h
                        st.rerun()