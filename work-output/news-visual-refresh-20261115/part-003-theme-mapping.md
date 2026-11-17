# Master Kumanda WORK — devam ve kaynak haritası
17 Kasım 2026, 10:03 TSİ. Sorumlu: mevcut WORK MASTER/root oturumu.
Kapsam: mevcut görevleri kaldığı yerden devralma; Antigravity ve Etsy ilan sistemi hariç.

## Güncel durum
| İş | Son somut kanıt | Açık kalan |
|---|---|---|
| İngilizce Facebook | 17 Kasım VERIFIED.md: 26.1667 sn Beatles videosu 1515026953796803; authenticated public playback doğrulaması; günlük 14:23 TSİ english-review.yml | Çok günlük doğal süreklilik; stok ve farklı sanatçı rotasyonu |
| Jingle | 16 Kasım 21:29 TSİ checkpoint: mevcut beş denemeli runner finalizer'a bağlı; gerçek kurulu giriş eski doğrulanmış MP3'ü tekrar render etmeden kullandı | Gerçek yeni sağlayıcı çifti indirme→final sürekliliği; dinleme ve bağımsız kabul. Üç üretim görevi Disabled |
| Instagram→YouTube | Son üç kesin Instagram kimliği için düzeltilmiş API media_url vermiyor | Final MP4/export veya sağlayıcının indirilebilir final URL'si. Aynı başarısız sorguları yineleme |
| Web SEO #41 | 12 Kasım: 17 exact 301 + 9 RSS; tek description/canonical, Lionel taslak link düzeltmesi | Google crawl/indeks, Guard1.0.4 kaynak/log idempotency, JSON-LD ve bağımsız kabul |
| Görsel yenileme #43 | Önce yalnız talimat vardı; bu oturum gerçek canlı markup/CSS ve tarihsel uygulanmış şablonu eşleştirdi | Aşağıdaki ilk eksik uygulama adımı |

EN Facebook'un 14 Kasım'daki disabled/PR44'e bağlı eski durumu, 17 Kasım çalışır durumunun açıklaması olarak kullanılmamalı. PR44'ün bütün kapsamı veya TR yayın kapısı bu sonuçla kapanmış sayılmaz.

## #43 ALINDI ve somut kaynak haritası
Aktif tema canlı WordPress okuması: oldies-radyo-1950s-theme, Oldies Radyo v7.3.7.1.
- TR sayfa630: template boş; kayıtlı eski Gutenberg içeriği 28 Ağustos tarihli.
- EN sayfa1714: seçili template page-muzik-haberleri.php.
- 17 Kasım anonim GET: TR ve EN HTTP200; ikisinde news-archive-page, news-card-grid ve monthly-news mevcut; oldies-news-hub yok.
- Dolayısıyla önceki part-001/002'deki #630 Query Loop CSS'sini canlı görünümün kesin kaynağı saymak yanlış. Gövdeyi değiştirerek çözüm üretme.
- Depoda mevcut uygulanmış tarihsel kaynak: work-output/news-monthly-separation-20261025/page-muzik-haberleri.php, blob03796c3910ee6e507b1f6f2b3cce804201eae4d9.
- Aynı klasörde report.md açıkça canlı TR listesini bu dosyanın ve oldies_latest_news_items() fonksiyonunun ürettiğini açıklıyor. EN tarafı ayrı WP_Query ve image_mode=cover kullanıyor; inc/ai-english.php haber şablonuna izin veren filtreyi içeriyor.
- Mevcut live stylesheet: /wp-content/themes/oldies-radyo-1950s-theme/style.css?m=1788166868. .news-card img yüksekliği240px; mobil kural220px. Bu kurallar .home-news-card ile ortak; düzeltme haber sayfasına kapsamlanmalı.
- Ortak aylık bölüm aynı PHP dosyasında monthly-news döngüsüdür. Aylık slug ayrımı korunmalı. Yeni görselli ay banner'ı bu render yoluna bağlanmalı; site geneli rastgele override yapılmamalı.
- Bu dosya 25 Ekim teslimidir; 17 Kasım kurulu PHP ile byte/hash eşitliği henüz doğrulanmadı. Kaynak bulundu demek kurulu dosyanın bugün aynen okunduğu anlamına gelmez.

## Elvis: gerçek kök neden ayrımı
1. 15 Kasım TR4880 / EN4881, featured media4568:
   source oldies-en-elvis-presley-archive.webp,1000x1200.
   Canlı TR kartında object-fit:contain;background:#080908.
   Burada ana problem zorunlu cover değildir: sabit yükseklikteki kutuda contain ve düz koyu arka plan boşluk üretiyor. Aynı fotoğraftan blur-fill katmanı gerekir.
2. Eski Elvis Week kartı:
   /elvis-week-2026-graceland-basladi/;
   tema assets/images/news-august-2026/elvis-week-2026.webp;
   canlı object-fit:cover;background:#080908.
   Bu ayrı görseldir; odak/kırpma ayrıca denenmeli. Yalnız4568 düzeltmesini tüm Elvis sorunlarına başarı sayma.
3. Canlı TR kartları hâlâ “Ay İçi Haberler” kullanıyor. Kurucunun sonraki kalıcı “Bu Ay / Geçmiş Aylar” talebiyle 25 Ekim metni çelişiyor; yeni uygulamada güncel tercih geçerli.

## İlk eksik uygulama adımı
Mevcut yetkili erişimle kurulu page-muzik-haberleri.php, functions.php içindeki oldies_latest_news_items(), style.css ve inc/ai-english.php'yi yalnız okuyup güncel hash/yedek al. Eski şablonu körlemesine yeniden kurma.
Ardından bu gerçek markup üzerinde staging: haber sayfasıyla sınırlı blur-fill ve odak istisnası; aynı döngüye TR/EN dinamik ay görselli banner. 390/768/1200/1440px ve en az10 gerçek kart; Elvis'in iki ayrı kaynağı dahil.
Canlı deploy önceki #43 sınırında: staging + bağımsız QA + kurucu nihai görsel/canlı kabulü. Bu oturum kod, tema, yayın veya scheduler değiştirmedi; yeni medya üretmedi.

## Kanıtlar
- control-center/work-state.json (okunan updated_at 2026-11-17T06:42:20.584Z)
- work-output/facebook-live-20261117/VERIFIED.md
- work-output/first-three-closure-20261116/CHECKPOINT.md
- work-output/two-deliveries-20261116/CHECKPOINT.md (merkezi kayıttaki son IG kanıtı; bu oturum başarısız sorguları yinelemedi)
- work-output/news-monthly-separation-20261025/report.md
- #43 ve part-002-implementation-instructions.md
- 17 Kasım canlı WordPress theme_active, pages630/1714, Elvis post listesi ve media4568
- 17 Kasım canlı anonim TR/EN HTML ve style.css
