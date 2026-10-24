# Fransa 1960’lar yazısı — görsel onarım sonucu
**25.10.2026 | 02:26 TSİ (UTC+3)** — WORK MASTER

## Kısa özet — 25.10.2026 | 02:26 TSİ
- GERÇEKLEŞEN / CANLIDA: Fransa TR4461 ve EN4462 yazılarında üç nota yer tutucusu gerçek fotoğraflarla değiştirildi. İki yazıda da kapak + 10 sanatçı görseli mevcut.
- GERÇEKLEŞEN: Sorunlu CDN yoluna bağımlı iç görseller için doğrulanmış site dosyalarını kullanan picture/source teslimi uygulandı. TR sayfasında 10/10 sanatçı fotoğrafının tarayıcıda yüklendiği görüldü.
- GERÇEKLEŞEN: Ana sayfada Fransa kapağı Almanya kartıyla aynı yerleşimde görünüyor. Yalnız Fransa TR/EN araştırma kartlarını hedefleyen CSS eklenerek kapak doğrudan site dosyasından gösterildi.
- SINIR: Sheila fotoğrafı 2012 tarihlidir; kart ve kaynaklarda açıkça işaretlendi. Diğer dokuz sanatçı görseli 1960’lara aittir. CDN sertifika sorununun altyapısal kökü çözülmüş sayılmıyor.
- DOĞRULAMA: Masaüstü gerçek görünüm + anonim HTTP200 + WordPress geri okuması. Mobil viewport isteği ölçülen genişliği değiştirmedi; mobil görsel kabulü verilmedi.

## Ayrıntılı kayıt — 25.10.2026 | 02:26 TSİ

### Mevcut durum ve neden
Kurucunun verdiği Fransa URL’si TR4461’e ait; Polylang EN4462 ile eşleşiyor. Referanslar Almanya4459 ve Yunanistan4308 doğrudan okundu. Fransa’da Johnny Hallyday, Sheila ve Serge Gainsbourg kartları fotoğraf yerine ♫ içeriyordu. Diğer yedi kartın fotoğraf kaydı vardı.

Eski öne çıkarılmış görsel4404 zaten atanmıştı; sorun “hiç atanmamış” değildi. Chrome’da Fransa kapak/portre CDN istekleri yüklenemedi; kapak adresi doğrudan açıldığında ERR_CERT_AUTHORITY_INVALID görüldü. Aynı dosyalar ve örnek CDN uçları bağımsız HTTP kontrolünde200 döndü. Bu yüzden dosyaların silindiği veya bütün ziyaretçilerin aynı sertifika sorununu yaşadığı iddia edilmedi.

### Uygulanan değişiklik
- Orijinal TR/EN metinleri ve4404 görsel bilgisi değişiklikten önce before.json olarak korundu.
- Mevcut kapak tasarımı korundu; yeniden tasarlanmadı. WebP kopyası4849,1672×941,488074bayt. Eski PNG2914959bayttı.
- Yeni gerçek fotoğraflar: Johnny Hallyday4850 (31Mart1963, Noord-Hollands Archief/Fotoburo de Boer,CC0); Serge Gainsbourg4851 (20Mart1965Eurovision,RAI,CommonsPD-Italy; fotoğrafta solda); Sheila4852 (23Haziran2012,ErioTACFrance–Perpignan,CCBY-SA3.0).
- Yedi mevcut arşiv fotoğrafının kaynakları yeniden doğrulandı. İki yazıda kapak ve10fotoğraf picture/source ile doğrudan oldiesradyo.com dosyalarından yüklenir. Fotoğraflar mevcut gri tonlu kart çerçevesinde gösterilir.
- Her yazının yalnız ikinci core/html içerik bloğu, değişiklik/hash kilitleriyle değiştirildi. İlk CSS bloğu ve ana biyografi/dinleme metinleri korundu. Kaynak/künye notları tamamlandı.
- Ana sayfa CSS’sine yalnız `a.research-card[data-post-id="4461"] > img` ve4462 eşini hedefleyen `content:url(...)` kuralı eklendi. Var olan CSS aynen korundu; custom-css-before.css yedeği mevcut. Bu kural gerçek img src/srcset üretimini değiştirmez; tarayıcıdaki görüntüyü doğrulanmış yerel kapaktan sağlar. Genel CDN ayarı veya PHP/eklenti kodu değiştirilmedi.
- İlk yeni PNG kopyası4846 ve denenmiş global-styles CSS yolu görünüm sorununu çözmedi. Global-styles576 içindeki deneme CSS’si hemen kaldırılarak önceki boş styles durumu geri yüklendi.4846 kullanılmayan medya olarak kaldı; kalıcı silme yapılmadı.

### Kontrol sonuçları
| Kontrol | Sonuç |
|---|---|
| TR sanatçı kartları |10/10fotoğraf; tümünde naturalWidth>0 ve complete=true |
| TR kapak | Doğrudan origin dosyasından1672piksel yüklendi |
| EN içerik |10fotoğraf+kapak,11picture/source; doğru İngilizce başlık/alternatif metin |
| Ana sayfa | Fransa veAlmanya kartları aynı satır/ölçüde; Fransa kapağı gerçek ekran görüntüsünde görünür |
| WordPress geri okuma | İki aday içerik byte düzeyinde kaydedilenle eşleşti; content_warnings boş |
| Yayın kimliği | TR tarih/başlık/kategori/etiket/yayın durumu korundu; EN başlık/yayın durumu korundu;featured_media4849 |
| Anonim sayfalar | TR,EN veana sayfa HTTP200; TR/EN’de11origin source |
| Mobil |390×844talebine rağmen gerçek ölçüm1536kaldı; dar ekran kabulü verilmedi |

Bu, MASTER’ın gerçek çıktı/görünüm kontrolüdür; yeni bağımsız WATCHDOG PASS’i olarak sunulmaz. Önceki site geneli üretim kararları değiştirilmedi.

### Geri dönüş ve kapsam
İlgili içerik için before.json’daki ikinci HTML bloğu ve eski featured_media4404 geri uygulanabilir. Ana sayfa kuralı custom-css-before.css ile geri alınabilir. Diğer ülke yazıları yalnız referans olarak okundu; onların eksikleri bu işte düzeltilmiş sayılmaz. CDN’nin sertifika/önbellek altyapısı ayrıca incelenmedikçe onarılmış değildir. Kullanıcıya görünen Fransa iç görselleri ve ana sayfa kapağı için kapsamlı yeniden kurulum yerine sınırlı origin teslimi uygulanmıştır.

### Bağlantılar
- [Türkçe yazı](https://oldiesradyo.com/2026/10/23/1960larda-fransa-10-unlu-sarkici/)
- [İngilizce yazı](https://oldiesradyo.com/en/2026/10/23/1960s-french-singers/)
- [Düzenle](https://oldiesradyo.com/wp-admin/post.php?post=4461&action=edit)
- [Ana sayfa](https://oldiesradyo.com/)
- [Değişiklik öncesi yedek](before.json)
- [CSS yedeği](custom-css-before.css)
