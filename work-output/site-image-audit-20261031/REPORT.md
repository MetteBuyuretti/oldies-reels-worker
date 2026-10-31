# OLDIES RADYO — son girişlerin görsel arıza incelemesi
**31.10.2026 | 06:25 TSİ (UTC+3)**
**Sorumlu:** WORK1 / MASTER. Kapsam: salt okunur site, WordPress public REST ve gerçek Chrome görüntü kontrolü. Canlı içerik/ayar değişmedi.

## GERÇEKLEŞEN
Son 12 yayımlanmış TR/EN kayıt public WP REST ile incelendi. Ana sayfa, İtalya dosyası ve yeni Beatles/Michael Jackson yazılarının HTML/görsel alanları kontrol edildi. Altı özgün/CDN görsel URL'si HTTP ve içerik türüyle kontrol edildi.

### 1. Yeni haberlerde dosya var, Chrome CDN sertifikasını reddediyor
Beatles TR 4874 / EN 4875 featured_media=4442. Michael Jackson TR4872/EN4873 featured_media=4890. Bu haberlerde gövde img bulunmaması tek başına eksik değildir: tema featured görselini article/figure içine gerçekten ekliyor.

Gerçek Chrome'da Beatles yazısı kırık görsel/alt metin gösterdi; main kapak img complete=true, naturalWidth=0, naturalHeight=0. Aynı exact CDN görselini doğrudan açma girişimi **net::ERR_CERT_AUTHORITY_INVALID** verdi. Güvenlik uyarısı aşılmadı.

CDN adresi: https://i0.wp.com/oldiesradyo.com/wp-content/uploads/2026/10/The_Beatles_at_Wellington_Airport_21_June_1964.jpg?fit=1024%2C634&ssl=1

Aynı fotoğrafın site üzerindeki özgün adresi aynı Chrome'da başarıyla açıldı: **6128×3796, complete=true**.
https://oldiesradyo.com/wp-content/uploads/2026/10/The_Beatles_at_Wellington_Airport_21_June_1964.jpg

Bağımsız HTTP ortamında Beatles, Michael Jackson ve İtalya kapaklarının CDN ve origin sürümleri toplam altı istekte 200 image/jpeg veya image/png döndü. Bu nedenle dosya kaybı/başarısız upload iddiası yanlış olur. Sorun, gözlenen Chrome ortamındaki CDN TLS sertifika güvenidir; tüm ziyaretçilerde genel CDN kesintisi olduğu kanıtlanmadı. Sertifika issuer/chain, yerel proxy/antivirüs veya saat gibi alt nedenler bu incelemede teşhis edilmedi.

### 2. İtalya dosyası gerçekten eksik görselle yayında
TR4463/EN4464, featured_media4405. Gövdede yalnız kapak ve Gigliola Cinquetti fotoğrafı var. Diğer dokuz sanatçı kartında img yerine açıkça ♫ içeren oldies-artist-photo div bulunuyor. Dokuz fotoğraf ağda kaybolmuş değil; yayımlanan içerikte hiç eklenmemiş. Görsel kaynakları bölümünde yalnız Cinquetti kaydı ve uygun dönem portresi eklenmeyen isimler notu var. Sorun içerik tamamlama/kalite kontrolü; CDN onarımı bu dokuz eksik görseli doldurmaz. Yazı tarihi30Ekim, son modified2Ekim: önceden hazırlanmış zamanlanmış içeriğin eksik paketle açılmış olmasıyla uyumlu; zamanlama işlemini yapan süreç bu kanıtla kesinleşmez.

https://oldiesradyo.com/2026/10/30/1960larda-italya-10-unlu-sarkici/
https://oldiesradyo.com/en/2026/10/30/1960s-italian-singers/

### 3. Diğer kapsam
Fransa TR/EN gövdelerinde kapak+10 sanatçı img etiketi mevcut. Bunların hepsinin Chrome yükleme/kalite kabulü bu dar kontrolde yapılmadı. Eylül TR/EN dosyasında sekiz dış Wikimedia img URL'si mevcut; bu tek başına yükleme başarısı değildir, tümü test edilmedi. Başlangıç ana sayfa HTML yanıtında son haber kartları henüz yeni31Ekim haberleri yerine önceki haberleri taşıyordu; bunun cache veya kurgu kaynağı ayrıca incelenmedi.

## BEKLEYEN / PLANLANAN ÇÖZÜM
1. Haber görsellerinde gerçek origin URL sağlıklı. Site genelinde image CDN kapatmak yerine önce yetkili dar düzeltme hazırlanmalı: sorunlu kapaklarda origin adresi kullanılmasının wp_get_attachment_image/srcset/Jetpack tarafından tekrar CDN'e çevrilip çevrilmediği staging'de doğrulanmalı. Gerekirse WordPress.com/Jetpack tarafına CDN sertifika incelemesi açılır. Güvenlik doğrulamasını kapatmak çözüm değildir.
2. İtalya'nın dokuz eksik dönem portresi, kimlik/dönem/lisans kontrolü ve TR/EN eşleme ile tamamlanmalı. Fransa/Yunanistan kabul edilmiş düzeni korunmalı. Sırf kutu dolsun diye ilgisiz fotoğraf eklenmemeli.
3. Son kabul: Chrome'da kapak ve içerik görsellerinin naturalWidth>0 olması, mobil/masaüstü görüntü kontrolü, TR/EN ve ana sayfa kartlarının gerçek görsel yüklemesi. HTTP200 veya featured_media ID tek başına kabul değildir.

**Sonuç:** İki ayrı doğrulanmış kusur var: gözlenen Chrome'da i0.wp.com sertifika engeli ve İtalya içeriğinde dokuz eklenmemiş fotoğraf. Canlı düzeltme uygulanmadı; kurulu sistem onarıldı denmiyor.
