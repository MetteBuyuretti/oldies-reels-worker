# Canlı görsel onarımı — sonuç
**31.10.2026 | 06:40 TSİ (UTC+3)**
**Yetki:** Kurucunun güncel açık talebi: siteyi düzelt veya yaptır; sorumluluk MASTER'da.

## GERÇEKLEŞEN — Work1
HFCM yeni snippet2 (HTML/header/sitewide/active) kuruldu. Var olan snippet1 ve tema/Jetpack ayarları değiştirilmedi. Kaynak: image-origin-fallback.js, commit61e59a8e. Bu küçük script yalnız i0–i3.wp.com üzerinden kendi oldiesradyo.com/wp-content/uploads görselinin yüklenmesi başarısız olduğunda aynı dosyayı HTTPS site origininden bir kere açar; srcset/sizes ve picture source override temizlenir. Sağlıklı görsele ve başka site/host görsellerine dokunmaz; TLS güvenlik kontrolünü kapatmaz. Yedi davranış kontrolü ve node syntax geçti.

Gerçek Chrome doğrulaması: Beatles TR/EN6128×3796, Michael Jackson TR957×1405 fotoğrafları origin fallback ile yüklendi. Önceden aynı Chrome'da Beatles complete=true/naturalWidth0 ve doğrudan CDN net::ERR_CERT_AUTHORITY_INVALID idi. Yeni sonuç naturalWidth>0. Michael JacksonEN aynı mevcut görseli/same featuredID4890 ve snippet içeren public HTML kullanıyor; ayrı Chrome ekran kontrolü yapılmadı. Ana sayfada kontrol anında main içinde complete=true/naturalWidth0 olan görsel yoktu.

Dört yeni haber4872/4873/4874/4875 aynı mevcut featured_media değerleriyle yeniden kaydedildi; başlık/metin/tarih değişmedi, post cache yenilendi. Anonim HTTP ile normal sorgusuz dört haber+ana sayfada yeni scriptin bulunduğu doğrulandı. Eski cachedHTML'de script yoktu; bu ayrım giderildi.

## GERÇEKLEŞEN — görevlendirilen İtalya uygulayıcısı
TR4463/EN4464 dokuz gerçek1960lar fotoğrafı, dönem/kişi/kaynak/hak kayıtlarıyla eklendi. Mevcut metin/CSS/tarih/çeviri ilişkileri korundu. Raw önce/sonra ve publicHTML kanıtı:
https://github.com/MetteBuyuretti/oldies-reels-worker/blob/2d42d61050b3ff7471ef96bd262ca6c0aa04d938/work-output/italy-image-repair-20261031/RESULT.md

Work1 ayrıca gerçek Chrome'da her iki dili kaydırarak10sanatçı kartının10unda img bulunduğunu ve10unun naturalWidth>0 olduğunu doğruladı. Nota placeholder0. Önce1/10du. Büyük orijinal dosyalar hata durumunda daha fazla trafik yaratabilir; fallback yalnız başarısız yüklemeye uygulanır.

## BEKLEYEN
CDN sertifika zincirinin alt nedeninin çözülmesi bu onarım değildir. Site orijinal dosyaya güvenli geri dönüşle görünürlük sağlıyor. Tüm1185sayfanın/mobilboyutların bağımsız tam denetimi yapılmadı; tüm siteye operasyonel/süreklilikPASS verilmiyor. İtalya lisans/kimlik incelemesi uygulayıcı kanıtıdır; bağımsız WATCHDOG kararı iddia edilmez.

## Geri dönüş
Yeni snippet2 HFCMden Inactive yapılarak yalnız fallback geri alınabilir; var olan snippet1 korunur. İtalya önceki raw içerik yedekleri yukarıdaki rapordadır; geri dönüş iki içerik bölümüne sınırlıdır. Kullanıcının şu an istediği onarım tamamlandı, ek genel onay beklenmiyor.
