# Haber iç sayfa görsel düzeni — canlı sonuç
**31.10.2026 | 07:04 TSİ (UTC+3)**

## GERÇEKLEŞEN
Kurucunun içsayfalarda tutarsız sığma/kesilme bildirimi üzerine temaCSSve gerçekChrome ölçüleri okundu. Çakışan eski kurallar doğrulandı: single-news-feature için620→500/460maxwidth,100%width+520pxmaxheight; august-news-main-photo için7/4ve4/3 zorunluaspect+cover; aylıkaugx portreleri için240/230/220pxsabitheight+100%width. Bunlar aynı haber sisteminde farklı boşluk/kırpma davranışları yaratıyordu.

YeniHFCM3 HTML/header/sitewide/active CSS kaydı eklendi. CSS yalnız main.single-news-page içindeki haber makalesi anafigür/wp-block-image/editorial-figure/august-news-main-photo ve monthlyaugx görsellerini hedefler. Ana sayfa/mağaza/İtalya sanatçı kartlarına selector uygulanmaz; HFCM1/2 değişmedi.

Dosya: news-image-layout.css commit8b95d43d. Orijinalenboyoranı korunur,object-fitcontain,widthauto,heightauto,aspectauto; tamgenişlik ve580pxyükseklik tavanı,aylıkportrelerde320pxtavan. Kaynağın önceden kırpılmış kısmını geri getirmez; siteekstra kırpmaz. Anafigür820pxyazıalanına kadar genişleyebilir; portre doğal oranıyla ortalanır. MobilCSSmax680px için460pxtavan var.

GerçekChromeQA:
- MJTR doğal957×1405; yeni kutu395.05×580px,contain/aspectauto,oran hatası0.000018. Önce500×520kutuda letterboxidi.
- BeatlesTR doğal6128×3796; yeni819.99×507.95px,contain,oran hatası0.000023.
- Eylül aylıkdosyasında Oasis509.83×320,Céline217.32×320,Stevie513.59×287.70,U2486.06×320. Doğalboyutlar okunarak tamfotoğraf/contain/aspectauto doğrulandı.
- Mobiloverride denemesi ölçüm anında eski viewport değerini verdi; gerçekmobilQAbaşarısı iddia edilmiyor.

Dört yeniTR/ENhaber4872–75 ve EylülTR/EN4817/4818 aynıfeaturedID ile yenidenkaydedildi; metin/tarih/çeviri değişmedi; ziyaretçi cache yenilemesi amaçlandı. ÖncekiCDNoriginfallback korunur; sertifikaalt nedeni onarılmış denmez.

## Work2 — güncel ayrım
PR38taslak/açık/unmerged. Görev, TürkçeReels'in caption değişiminde fotoğrafı tekrar seçmesini düzeltmek, görseladayincelemesi,47testkanıtı veWindowsdevirpaketiydi. Adaykod+24yeni/23mevcut testteslimi tamamlandı. Ses/hizalama/FFmpeg ana testleri açıkfixture/stub;gerçekfilmdeğil. Son#32kontrolünde Windowsyeni alımı yok. Üçuygunfotoğraf/haklar,gerçekdoğalses+ölçülmüşhizalama vebağımsızfinalkabul açık. Work2hazırlığıbitti,tümTürkçeotomasyonbitmedi.

## Geri dönüş ve sınır
HFCM3Inactive ile yalnız buCSSgeri alınır. KonuHFCM2görselyüklemefallback'indena yrıdır. Herhaberin/tümcihazların kapsamlıdenetimi yapılmadı; canlı daronarımdır. Kaynakyazıyeniden yazılmadı. Somut ekran görüntüsü buWorkçıktısında saklandı.
