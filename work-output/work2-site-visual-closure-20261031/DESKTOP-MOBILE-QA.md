# D — haber masaüstü / mobil QA
31.10.2026 | 07:38 TSİ (UTC+3)

GERÇEKLEŞEN: Yeni ayrı Chrome sekmesinde BeatlesTR/EN4874/4875, MJTR/EN4872/4873, EylülTR/EN4817/4818 ve AğustosTR4300 ziyaretçi sayfaları gerçekgörünüm/screenshot ve DOMölçümüyle incelendi. Toplam27görselöğesi (dilçiftlerinde tekrarlar dahil) kaydırmayla yüklendi; naturalWidth/Height>0,complete,true,object-fitcontain,aspectauto; doğal oran farkları aşağıda. Başlıklar görünür tasarımda okunur; document.scrollWidth<=clientWidth, yataytaşma yok. Aylık sayfalardaki gizli0×0themefeatured asılgörsel sayılmadı. Oasis kaynakfotoğraflarından kolaj, Madonna kaynakta kırpılmışsürüm; contain kaynaktaki crop'u geri getirmez. SiteCSSekcrop/streç buölçümde görülmedi.

| PostID | Görünen imgöğesi | innerWidth/clientWidth | Enbüyük oran farkı | Masaüstü yükleme/geometri | İçerik/görsel ayrımı | 390pxmobil |
|---|---:|---|---:|---|---|---|
| 4874 | 1 | 1363/1348 | 0.0000177 | PASS | SCOPED_DESKTOP_REVIEW | NOT_VERIFIED |
| 4875 | 1 | 1363/1348 | 0.0000177 | PASS | SCOPED_DESKTOP_REVIEW | NOT_VERIFIED |
| 4872 | 1 | 1363/1348 | 0.0000255 | PASS | SCOPED_DESKTOP_REVIEW | NOT_VERIFIED |
| 4873 | 1 | 1363/1348 | 0.0000255 | PASS | SCOPED_DESKTOP_REVIEW | NOT_VERIFIED |
| 4817 | 8 | 1363/1348 | 0.0000453 | PASS | SCOPED_DESKTOP_REVIEW | NOT_VERIFIED |
| 4818 | 8 | 1363/1348 | 0.0000453 | PASS | SCOPED_DESKTOP_REVIEW | NOT_VERIFIED |
| 4300 | 7 | 1363/1348 | 0.0000469 | PASS | FAIL_ROD_DRAWING_LABELLED_PHOTO | NOT_VERIFIED |

Screenshotlar workspace kanıtı olarak tutuldu; QA.json dosya/hashlerini verir. Özellikle fullname+publiccontactfooter içeren görseller açıkrepoya/Library'ye yüklenmedi. Aylık fullpagecapture yeni navigasyonda offscreenlazyfotoğrafları bazen henüz çizmeden alabilir; tekfullpagecapture bütünfotoğraflar yüklendi kanıtı sayılmadı. Yükleme/ratio kayıtları gerçekkaydırma sonrasından; ayrıca görünürfotoğraflı viewport ve tam sayfa screenshotları incelendi.

## Somut hata: Rod çizimi fotoğraf diye etiketli
4300'de exactselector: `main.single-news-page article.augx-card figure.augx-portrait img[src*="/Rod_Stewart.jpg"]`.
Gerçekgörsel PascalKirchmair karikatürü; Commons kaydı https://commons.wikimedia.org/wiki/File:Rod_Stewart.jpg , ownwork/2014/CCBY-SA3.0 ve Drawings/RodStewartinart kategorileriyle uyumlu. Aynıdosyanın doğal787×900boyutu ve279.81×320contain kutusu doğru; bubirCSSkırpma sorunu değildir. Alt/kredi fotoğrafdiyor. **Görseli fotoğrafkabulü FAIL.**

`ROD-CONTENT-PROPOSAL.diff` exactWPrawfigure'den yalnız alt/kredi türünü düzeltir (önce archivephoto → sonra2014illüstrasyonu/fotoğrafdeğil); yeniURL/portreuydurmaz. Kaynakmodified 2026-10-25T02:05:21, figureSHA256 072358ac36a0fddf7e1b5f951adbc2fa9711f014c948b77e98882639a5e1716a. Bu öneri uygulanmadı: Dsaltokunur. MASTER gerçekfotoğraf şartını karşılayacaksa uygunfotoğrafı ayrıca seçipkaynak/lisans/backup/CASile değiştirmeli. Sırfcaptiondüzeltmekfotoğrafeksikliğini tamamlamaz. HFCM3veyaHFCM2yenidenyazılmadı; CSSfarkı üretilmedi, çünkü kanıtlanmışCSSkusuru yok.

İkincilbulgu: BeatlesEN4875credit/kaynak metni mevcut, Commonskaynak tıklanabiliranchor değil (creditLinks[]). Gerekirse yalnız mevcutkanonikURL'yi aynıcreditiçindelinkle; bu yükleme/CSSarızası değildir. Mevcutmetinveyayınstatüsü buDişinde değiştirilmedi.

## Mobil: NOT_VERIFIED
İstenen gerçek390CSSpx için buCUAtarayıcıyüzeyinde dokumenteviewportresize/emulation yeteneği yok. Gerçekbaşlangıç/son innerWidth1363,clientWidth1348,innerHeight936.390px isteme/ölçme yapılmış gibi yazılmadı; CSS/DOMenjeksiyonuyla sahteboyut oluşturulmadı. Viewport hiçdeğişmedi, başlangıç/son eşleşti; geçiciayar kalmadı. Yalnız bu7URL için gerçekviewport390ayarlayabilen mevcutMASTER/browseroperatörü birsonrakigerçekalımdan sonra10–20dkdarQA'yı tamamlamalı: actualinnerWidth/clientWidth+screenshot,27görselöğesinindoğaloran/yükleme/kredi/başlık/taşma kontrolü ve başlangıçviewport'ageridönüş. Genelkurulum/anahtar/yenikaynakbeklemiyor.

Buşekilde masaüstügeometriPASS ile genelgörsel/bağımsızkabul/mobilPASS ayrıdır.4300'deki haber/vefat/sağlık iddiaları bugörselQA ile doğrulanmışsayılmaz; içerikgerçekliği ayrıeditorialkontroldür. Yeniüretim/yayın/CSS/tema/HFCM/scheduler/Windows değişmedi.
