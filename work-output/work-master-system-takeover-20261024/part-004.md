# WORK MASTER — WordPress kaynak incelemesi, bölüm 2
**24.10.2026 | 05:11 TSİ (UTC+3)**

## Sonuç ve kapsam

- **GERÇEKLEŞEN:** 61 kurulu eklentinin envanteriyle 24 aktif bileşenin sorumluluk ve bağımlılık haritası birleştirildi; 14 mevcut paket üzerinde statik kaynak incelemesi yapıldı.
- **GERÇEKLEŞEN:** Haber, Etsy, çeviri, Facebook/Reels, yönlendirme ve içerik korumasında kritik çağrı sıraları ve kayıt yan etkileri ayrıştırıldı. Öncelikli bulgular bölüm1'dedir.
- **BEKLEYEN:** Canlı kaynak hashleri, Guard/Token Bridge kodları, güncel dört özel modül kaynağı ve doğal cron/teslim kayıtları eksik. Bütün eklenti kodları ve uçtan uca işler tamamlanmış sayılmaz.
- **PLANLANAN:** Haber cron/doğal işlem kanıtı ve güncel Guard kodu ilk sırada; Etsy'de tam ERROR kimlikleri/token durum yolu ikinci sırada. Onarım öncesi güncel kaynakla bulgu doğrulanmalı.
- **SINIR:** Bu çalışma okuma, statik inceleme ve yönetim kayıtlarının güncellenmesidir. Canlı Dinle kurucu Mete'dedir; üretim, render, retry, yayın veya zamanlı görev açma yapılmadı. Önceki panel açılışının koşullu DB yazma belirsizliği bölüm1'de açıkça düzeltilmiştir.

## 14 özel aktif eklentinin sorumluluk kartları

“Aynı sürüm” yalnız arşiv başlığı ile canlı envanterin eşleşmesidir; canlı dosya eşitliği değildir. “Tarihsel” kaynak, güncel modül davranışını kanıtlamaz. “Kaynak yok” tam kodun bulunamadığı anlamındadır.

| Bileşen / canlı sürüm | Kaynak kapsamı | Tetikleyici, bağımlılık ve kayıt davranışı | İnceleme sonucu / açık ihtiyaç |
|---|---|---|---|
| Social & News1.7.5 | Aynı sürüm; aktif kök farklı | WordPress cron; RSS/HTTP→doğrulama→iki dil→medya→WordPress. Eski IG/FB/YouTube/Etsy ve retention da aynı paket içinde | Haber hatası sessiz kalabilir. Günlük sosyal içerik üretimi yayın OFF/dry-run olsa da AI/görsel adımına ulaşabilir; yayın kapısı üretim kapısı değildir. Canlı hook ve ayar kanıtı eksik |
| Etsy Distribution1.2.1 | Aynı sürüm | 48 saat keşif,5 dakika render poll; OAuth Bridge + mevcut uzak worker; ürün ve distribution tabloları ayrı | TokenExpired ön kontrolü, ilk100 ilan sınırı, ekran açılışında koşullu yazma. META_FINAL elle eklenmeden platform finali sayılmaz |
| Etsy OAuth Bridge1.2.1 | Aynı sürüm | Yönetici OAuth/PKCE, API isteğinde refresh; şifreli token kaydı | Connection status kontrolü yenileme yapmaz. Bağlantı testi/ilan okuması refresh tetikleyebilir. Sırf okuma hedefiyle bile API isteği token yazabilir |
| FB MCP Bridge1.0.5 | Aynı sürüm | WordPress Abilities API→Companion health/render/status/publish; manage_options | Kendi render/yayın motoru yok. read-only etiketi alttaki fonksiyona göre değerlendirilir; health worker'a ağ isteği yapabilir |
| FB Companion1.0.7-R7 | Tarihsel1.0.3-R3 | REST/bearer veya yönetici→imzalı worker→Meta upload start/upload/finish; content_id tekilleştirme | Tarihsel health yalnız workerREADY ve ayar varlığını gösterir; tokenın Meta'da geçerliliğini kanıtlamaz. Güncel R7 retry/kimlik önceliği için güncel kaynak gerekir |
| FB Settings1.1.0 | Tarihsel1.0.1 | plugins_loaded priority1 ile kayıtlı Global Page ID/tokenı ortam değişkenlerine aktarır; yönetici formunda nonce/capability | Tarihsel Companion token için Social kayıtlı değeri ortamdan önce seçer; Global ayara yeni token girmek bu eski sırada yeterli olmayabilir. Canlı1.1/R7/TokenBridge birlikte doğrulanmadan arıza ilan edilemez |
| FB Token Bridge2.0.0 | Kaynak yok | Ayrı kimlik bilgisi geçiş katmanı; canlı envanterde aktif | Hangi kayıtları hangi sırayla etkilediği tam kodla doğrulanmadı. Token değerleri rapora alınmaz |
| Reels Bridge2.3.7-YT8-SAFE2 | Tarihsel2.1.10 | REST/ability/admin; Social Settings, kuyruk, Meta ve Edits devri; günlük dosya temizliği | Tarihsel Prepare for Edits statü yazar; Get Handoff/List okur. Eski Meta dry-run media container oluşturabilir. Güncel2.3.7 kaynağı olmadan eski canlı yayın yolları var sayılmaz |
| Command Center1.0.9 | Kısmi tarihsel1.0.6 | Admin paneli/adaptörler/gateway ve heartbeat; mevcut motorlara bağlanır | Okunan menü kabuğu eklentileri devre dışı bırakmaz, yalnız eski menüleri saklar. Menü yokluğu motor yokluğu değildir. Güncel gateway/adaptör kaynakları eksik |
| TR→EN News Guard1.0.4 | Kaynak yok | Canlı panelde TR yayınından EN eş üretimi/yayını hedefleyen ayrı kuyruk | Haber üreticisi, tema HTML çevirisi ve pasif EN Draft Agent ile aynı iş değildir. Hook/tekilleştirme/yeniden deneme kodu ve son doğal koşu lazım |
| Polylang MCP Helper1.3.0 | Aynı sürüm | Abilities + post meta ekleme/güncelleme hookları→Polylang API | Status/get/preview salt inceleme; pair ve REST meta yazmadır. REST pair mevcut çakışmayı reddeder; genel pair yolu aynı kontrolü yapmaz. Eşleme kalitesi üretim/yayın kalitesi değildir |
| Global Router1.0.10 | Aynı sürüm | Frontend JS, ülke REST okuması, dil/mağaza shortcode; Polylang ve ürün meta eşlemesi | Safe Mode dinamik yönlendirmeyi kapatır; kaynak varsayılanı mevcut canlı değer değildir. Ülke bilinmiyorsa UNKNOWN, dış GeoIP servisi yok. Dil önerisi kullanıcı tıklamasıyla geçiş yapar; otomatik zorlamalı dil atlaması görülmedi |
| Revenue CTA1.3.1 | 4Ekim yedeğinde aynı sürüm | template_redirect priority20 output buffer; hedef temada belirli Shopier linklerini mailto yapar | Gövde veritabanını değiştirmeden görünümü değiştirir. Hizmet menüsü4540/4541'in publish olmasına bağlı; eski4397/4398 görev kaydı güncel sayfa kimliği kabul edilemez |
| Site Integrity0.2.1 | Aynı sürüm | REST/klasik yayın kapısı; menü/kategori/ayar koruması; günlük audit,batch,30 saniye sonrası frontend doğrulama; dış tampon priority−1000 | Korumayı gevşetmek çözüm değildir. Gerçek yayıncı sonucu ile status geri okunmalı. Dinamik TR sayfasında kısa editör gövdesi tek başına boş sayfa kanıtı değildir |

## Standart 10 aktif eklenti

Bu tablo resmi ürün belgeleriyle işlev/bağımlılık çalışmasıdır. Bu10 eklentinin bütün kaynak dosyaları, canlı ayarları ve her modülü bu tur denetlenmedi. Sürümler site envanterindendir; internetteki son sürüm etiketleriyle değiştirilmedi.

| Eklenti / canlı sürüm | Görev | OLDIES açısından doğrulanacak bağ |
|---|---|---|
| Akismet5.7.2 | Yorum/form spam denetimi | Haber üretim motoru değildir. Canlı anahtar ve yorum kuyruğu bu kapsamda test edilmedi |
| CoBlocks3.1.17 | Gutenberg için ek sayfa blokları | Hangi canlı yazıların CoBlocks kullandığı tam taranmadı; kaldırma kararı verilmedi |
| Gutenberg24.2.0 | Blok editörü | Klasik temanın frontend şablonlarıyla ayrı katman. Editör çalışması haber cronunun çalıştığı anlamına gelmez |
| Gravatar Enhanced0.14.0 | Avatar/hovercard/proxy | Resmi belge Jetpack hovercard ayarının önceliğini belirtir. Proxy özelliği varsa cron temizliği ve yerel avatar kopyası olabilir; canlı modül açık mı bilinmiyor |
| HFCM1.1.46 | Header/footer HTML,CSS,JS parçaları | 4Ekim yedeğindeki snippet#1, araştırma kartlarını DOMContentLoaded'da elle ekler. Güncel snippet bu tur hash ile doğrulanmadı |
| Jetpack16.4-a.3 | Site bağlantısı ve etkinleştirilen modüller; görsel CDN dahil | Origin dosya, i0.wp.com görseli ve tarayıcı sertifika hatası ayrı kontrol edilir. Aktif eklenti bütün Jetpack modülleri açık demek değildir |
| Page Optimize0.6.4 | CSS/JS birleştirme ve script zamanlaması | HFCM/Router DOM davranışıyla beraber değerlendirilir. Olası etkileşim, kanıtlanmış OLDIES arızası değildir; ayarlar değiştirilmedi |
| Polylang3.9.1 | Dil ataması ve karşılık ilişkileri | Otomatik tam metin çeviricisi değildir. Kategori dili ve iki yönlü eş, haber yayın kapısının parçasıdır |
| miniOrange Secure MCP1.4.8 | WordPress yeteneklerini yetkili AI bağlantısına sunar | Yalnız görünen/izinli yetenekler kullanılabilir. Resmi değişiklik kaydındaki cron/log bakım yetenekleri1.4.13'te eklenmiş; bunların1.4.8'de görünmemesi tek başına yeni bir erişim arızası kanıtı değildir. Güncelleme yapılmadı |
| Site Kit1.187.0 | Bağlı Google servislerinin ölçüm/raporları | Analytics ziyaretçisi ile Search Console gösterim/tıklaması ayrı ölçülerdir. Güncel ölçüm etiketi, mükerrerlik ve hesap bağlantısı bu tur doğrulanmadı |

## Görünümün hangi katmanda değiştiği

Sitede yalnız yazı gövdesini okumak yeterli değildir. Okunan kaynakta tema HTML üretir; tema İngilizce tamponu gerekirse HTML önbelleği verir; Revenue CTA hedef linkleri yeniden yazar; Site Integrity en dış tamponda kilitli menüyü ve araştırma modülünü uygular. HFCM ise tarayıcıda ayrı JS çalıştırabilir. Page Optimize scriptlerin yüklenme biçimine etki edebilir; Jetpack görsel URL'sini CDN'e çevirebilir.

Integrity `integration.php`8–12,35–74 dış tamponu−1000 önceliğiyle açar ve `menu-master.json` içindeki TR/EN menüyü uygular. Revenue priority20, eski tema English priority99 iç tamponlardır. Bu yüzden bir eklentide veya yazı gövdesinde yapılan link değişikliği son görünen menüde etkisiz kalabilir. Menü değişikliğini “kayıt tutmadı” diye tekrarlamadan bu sıra kontrol edilmelidir.

HFCM yedeği TR araştırma şeridini iki sabit kartla üretir ve `.home-research-strip` varsa çıkış yapar. Integrity ise aynı alanı sunucuda üretir. Güncel HTML/JS katmanları görülmeden sabit kartlar yeni tasarım diye tekrar eklenmez. Bu tespit oynatıcı işini açmaz.

## Başarı etiketlerinin sınırları

| Görülen değer | Tek başına kanıtlamadığı şey |
|---|---|
| Eklenti active | Cronun tetiklenmesi, geçerli token, doğru çıktı veya teslim |
| health/worker READY | Üretim tamamlanması veya Facebook/Instagram yayınının görünürlüğü |
| PUBLISHED | Her alt sistemde gerçek platform finali: SocialJobManager dry-run başarısını da PUBLISHED durumuna taşıyabilir; Distribution manuel URL kaydeder; NewsPublisher amaçlanan durumdan sonuç çıkarır |
| READY_FOR_EDITS | Edits'te ses/müzik/final işleminin tamamlanması veya IGfinalID |
| VERIFIED ilişki / Polylang eş | Çevirinin tamlığı, haber doğruluğu veya iki dilin yayında oluşu |
| Integrity49.1% | Sitenin ziyaretçiye görünen tüm sayfalarının sağlık yüzdesi; bu değer editoryal kurallara uyum/inceleme taramasıdır |
| Dry-run | Hiçbir yazma, dış API çağrısı veya üretim maliyeti olmaması; kod yoluna göre ayrıca değerlendirilir |

Social kaynak `Social/SocialJobManager.php`150–175,285–338 dry-run'da da iş attempt/status kaydı günceller; yayıncıların başarı sonuçları iş durumunu PUBLISHED yapabilir. Gerçek platform ID/URL ve dry_run alanı birlikte okunmalıdır. Tarihsel Reels2.1.10 `publishReelDirect` ve `publishReelWithAudio` Meta container oluşturmayı dry_run dönüşünden önce yapar. Bu yollar bu tur çağrılmadı.

## Temizlik, log saklama ve eski işlerin kaybı

Social `Maintenance/RetentionCleaner.php` günlük bakımda iş kayıtlarını/diagnostics'i ve izin verilen dizinlerde eski medya dosyalarını silebilir. Kaynak varsayılanları yayın iş geçmişi30gün,diagnostics7gün,arşiv200kayıttır; bunlar canlı ayar değerleri olarak doğrulanmadı. Korunan Etsy inceleme statüleri ve tamamlanmış işler ayrı seçilir. Ayrı Distribution tablosu ile eski Social Etsy tablosu aynı retention hedefi varsayılamaz.

Bu nedenle eski job4–6'nın yeni panelde görünmemesi, silindiği veya yeni işlerce değiştirildiği sonucunu tek başına vermez. İlgili tablo, gerçek jobUUID/listingID, kaynak sürümü, retention ve zaman damgası beraber eşleştirilmelidir. Kayıtlar topluca temizlenmedi veya tekrar üretilmedi.

## Öncelikli doğrulama ve onarım kabul ölçütleri

| Sıra | Kanıtla yapılacak sonraki iş | Başarı ölçütü | Şimdiki durum |
|---|---|---|---|
|1 Haber/Guard | Güncel Guard + Social dosyalarını hashli salt okunur dışa aktarımla eşleştir; gerçek cron olayı,son/doğal koşu,lock ve hata kaydını oku | Tarama zamanının gerçek doğal koşuyla ilerlemesi; hata varsa açık kaydı; tek kaynaklı haberi VERIFIED yapmama | Kaynak/cron kanıtı eksik; scan22Eylül gözlemi korunur |
|2 Yayın sırası | Güncel NewsPublisher/Integrity sürümüne göre iki taslak→dil/kategori/görsel/eşleme→yayın tasarımını doğrula | İki gerçek post_status,pair,URL ve tablo sonucu aynı; yinelenen yazı yok | Statik uyumluluk bulgusu; canlı onarım uygulanmadı |
|3 Etsy | TokenExpired kontrolünün canlı kod sırasını ve10ERROR tam hata/UUID kayıtlarını eşleştir | Geçerli refresh yoluna erişim ve tek işe ait açık hata; toplu retry veya yeni render olmadan teşhis | Kaynakta aday neden var; canlı API/refresh yapılmadı |
|4 Reels/FB | Güncel R7/Settings/TokenBridge/2.3.7 kaynaklarıyla kimlik ve dry-run/yayın yollarını eşleştir | Gerçek finalID/URL ile kontrol kayıtları uyumlu; tekilleştirme korunmuş | Güncel kaynaklar kısmen yok; üretim kapalı |
|5 Görünüm/ölçüm | Güncel snippet,buffer,CDN ve ölçüm yapılandırmasını hedef URL ile eşleştir | Hangi katmanın ne ürettiği belli; yanlış gövde veya menü müdahalesi yapılmıyor | Bu tur statik harita var; tüm sayfaların E2E testi yok |

Operasyonel sahip WORK MASTER'dır. Bir sonraki kontrol, ilgili mevcut kanıt bu aktif çalışma içinde erişilebilir olduğunda yapılır; yeni sürekli izleme veya ileride kendiliğinden çalışma sözü verilmedi. Eksik güvenli kaynak erişimi, canlı PHP editörü yasağını aşmak için gerekçe yapılmadı. Windows/uzak masaüstü kotası yeniden denenmedi. Kullanıcıdan mesaj veya token taşıması istenmedi.

## Resmi ürün dayanakları

24.10.2026'da rol/özellik karşılaştırması için okundu; bu belgeler sitenin gerçek modül ayarını kanıtlamaz.

- [Akismet](https://wordpress.org/plugins/akismet/), [CoBlocks](https://wordpress.org/plugins/coblocks/), [Gutenberg](https://wordpress.org/plugins/gutenberg/).
- [Gravatar Enhanced](https://support.gravatar.com/gravatar-enhanced-wordpress-plugin/), [HFCM](https://draftpress.com/docs/header-footer-code-manager/).
- [Jetpack Site Accelerator](https://jetpack.com/support/site-accelerator/), [Page Optimize](https://wordpress.org/plugins/page-optimize/).
- [Polylang](https://polylang.pro/documentation/support/getting-started/translating-pages-posts-categories-and-tags/), [miniOrange sürüm kaydı](https://wordpress.org/plugins/miniorange-secure-mcp-server/).
- [Google Site Kit](https://sitekit.withgoogle.com/documentation/how-tos/how-to-use-the-site-kit-dashboard/).

## İncelemenin kapanış sınırı

Mevcut erişilebilir kaynaklar üzerinden görev/bağımlılık ve kritik risk yollarını öğrenme bölümü tamamlandı. Bütün61 eklentinin tam kaynak/güvenlik denetimi, bütün24aktif eklentinin tüm modülleri ve bütün otomasyonların gerçek uçtan uca çalışması tamamlanmadı. Bu ayrım ortak kayıtta korunmalıdır. Kaynak kapsamı1.bölümde ve aşağıdaki envanterde saklanır; sonraki oturum bu kayıttan devam eder.

## Kurulu 61 eklenti: kimlik ve sürüm envanteri

Kaynak: bu oturumdaki canlı envanterin saklanan gözlemi. 24aktif/37pasif; pasiflerin kaynak kodu tam incelenmedi ve hiçbirinin durumu değiştirilmedi. Klasör adı aktif sürüm başlığına göre üstün kanıt değildir.

| # | Eklenti | Durum | Sürüm | Dosya kimliği |
|---|---|---|---|---|
|1|Akismet Anti-spam: Spam Protection|AKTİF|5.7.2|`akismet/akismet`|
|2|Classic Editor|PASİF|1.7.0|`classic-editor/classic-editor`|
|3|CoBlocks|AKTİF|3.1.17|`coblocks/class-coblocks`|
|4|Crowdsignal Dashboard - Polls, Surveys & more|PASİF|3.1.8|`polldaddy/polldaddy`|
|5|Crowdsignal Forms|PASİF|1.8.3|`crowdsignal-forms/crowdsignal-forms`|
|6|Gravatar Enhanced|AKTİF|0.14.0|`gravatar-enhanced/gravatar-enhanced`|
|7|Gutenberg|AKTİF|24.2.0|`gutenberg/gutenberg`|
|8|Header Footer Code Manager|AKTİF|1.1.46|`header-footer-code-manager/99robots-header-footer-code-manager`|
|9|Jetpack|AKTİF|16.4-a.3|`jetpack/jetpack`|
|10|Layout Grid|PASİF|1.8.5|`layout-grid/index`|
|11|Oldies Etsy Automation Keeper|PASİF|1.0.0|`oldies-etsy-automation-keeper/oldies-etsy-automation-keeper`|
|12|Oldies Etsy Automation — 15s Queue|PASİF|1.7.5.10|`oldies-etsy-manual-review-v1752/oldies-radyo-social-automation`|
|13|Oldies Etsy Distribution Center|PASİF|1.2.2|`dist-v122/oldies-etsy-distribution-center`|
|14|Oldies Etsy Distribution Center|PASİF|1.2.2|`oldies-etsy-distribution-center-v1.2.2/dist-v120/oldies-etsy-distribution-center`|
|15|Oldies Etsy Distribution Center|PASİF|1.1.0|`oldies-etsy-distribution-center/oldies-etsy-distribution-center`|
|16|Oldies Etsy Distribution Center|AKTİF|1.2.1|`dist-v120/oldies-etsy-distribution-center`|
|17|Oldies Facebook Global MCP Bridge|PASİF|1.0.1|`oldies-facebook-global-mcp-bridge-v1.0.1-ROOT-DEPLOY/oldies-facebook-global-mcp-bridge`|
|18|Oldies Facebook Global MCP Bridge|PASİF|1.0.3|`oldies-facebook-global-mcp-bridge-v1.0.3-ROOT-DEPLOY/oldies-facebook-global-mcp-bridge`|
|19|Oldies Facebook Global MCP Bridge|AKTİF|1.0.5|`oldies-facebook-global-mcp-bridge-v1.0.5-ROOT-DEPLOY/oldies-facebook-global-mcp-bridge`|
|20|Oldies Facebook Global MCP Bridge|PASİF|1.0.0|`oldies-facebook-global-mcp-bridge-v1.0.0-ROOT-DEPLOY/oldies-facebook-global-mcp-bridge`|
|21|Oldies Facebook Global MCP Bridge|PASİF|1.0.5|`oldies-facebook-global-mcp-bridge-v1.0.5-ROOT-DEPLOY-1/oldies-facebook-global-mcp-bridge`|
|22|Oldies Facebook Global MCP Bridge|PASİF|1.0.2|`oldies-facebook-global-mcp-bridge-v1.0.2-ROOT-DEPLOY/oldies-facebook-global-mcp-bridge`|
|23|Oldies Facebook Global Settings|PASİF|1.1.0|`oldies-facebook-global-settings-v1.1.0-replace/oldies-facebook-global-settings-v1.0.1-ROOT-DEPLOY/oldies-facebook-global-settings`|
|24|Oldies Facebook Global Settings|PASİF|1.0.0|`oldies-facebook-global-settings-v1.0.0-ROOT-DEPLOY/oldies-facebook-global-settings`|
|25|Oldies Facebook Global Settings|AKTİF|1.1.0|`oldies-facebook-global-settings-v1.0.1-ROOT-DEPLOY/oldies-facebook-global-settings`|
|26|Oldies Facebook Token Bridge|AKTİF|2.0.0|`oldies-facebook-token-bridge/oldies-facebook-token-bridge`|
|27|Oldies Global Router|AKTİF|1.0.10|`oldies-global-router/oldies-global-router`|
|28|Oldies Polylang MCP Helper|AKTİF|1.3.0|`oldies-polylang-mcp-helper/oldies-polylang-mcp-helper`|
|29|Oldies Radyo Command Center|AKTİF|1.0.9|`oldies-command-center-phase2/oldies-command-center`|
|30|Oldies Radyo Command Center|PASİF|1.0.4|`oldies-command-center-1.0.4-PHASE2-CANDIDATE/oldies-command-center/oldies-command-center`|
|31|Oldies Radyo Facebook Global Companion|PASİF|1.0.1|`oldies-facebook-global-companion-v1.0.1-ROOT-DEPLOY/oldies-facebook-global-companion`|
|32|Oldies Radyo Facebook Global Companion|PASİF|1.0.0|`oldies-facebook-global-companion-v1.0.0-DEPLOY/oldies-facebook-global-companion/oldies-facebook-global-companion`|
|33|Oldies Radyo Facebook Global Companion|PASİF|1.0.3-R2|`oldies-facebook-global-companion-v1.0.2.2-ROOT-DEPLOY/oldies-facebook-global-companion`|
|34|Oldies Radyo Facebook Global Companion|PASİF|1.0.3-R2|`oldies-facebook-global-companion-v1.0.3-R2-PRODUCTION-DEPLOY/oldies-facebook-global-companion-v1.0.2.2-ROOT-DEPLOY/oldies-facebook-global-companion`|
|35|Oldies Radyo Facebook Global Companion|PASİF|1.0.3-R2.1|`oldies-facebook-global-companion-v1.0.3-R2.1-TEST-CANDIDATE/oldies-facebook-global-companion`|
|36|Oldies Radyo Facebook Global Companion|AKTİF|1.0.7-R7|`oldies-facebook-global-companion-v1.0.3-R3-ROOT-DEPLOY/oldies-facebook-global-companion`|
|37|Oldies Radyo Facebook Global Companion|PASİF|1.0.2.1|`oldies-facebook-global-companion-v1.0.2.1-ROOT-DEPLOY/oldies-facebook-global-companion`|
|38|Oldies Radyo Facebook Global Companion|PASİF|1.0.3-R2.2|`oldies-facebook-global-companion-v1.0.3-R2.2-TEST-CANDIDATE/oldies-facebook-global-companion`|
|39|Oldies Radyo Facebook Global Companion|PASİF|1.0.2|`oldies-facebook-global-companion-v1.0.2-ROOT-DEPLOY/oldies-facebook-global-companion`|
|40|Oldies Radyo Reels Bridge|AKTİF|2.3.7-YT8-SAFE2|`oldies-reels-bridge-r5-FIXED/oldies-reels-bridge`|
|41|Oldies Radyo Reels Bridge|PASİF|2.3.5-YT8|`oldies-reels-bridge-2.3.5-YT8/oldies-reels-bridge-r5-FIXED/oldies-reels-bridge`|
|42|Oldies Radyo Reels Bridge|PASİF|2.1.9-R5|`oldies-reels-bridge-r5-clean/oldies-reels-bridge-r5-clean/oldies-reels-bridge`|
|43|Oldies Radyo Social & News Automation|PASİF|1.7.5|`oldies-social-1.7.5-instagram-reconnect-FULL-PATCHED-LIVE-MERGED/oldies-radyo-social-automation/oldies-radyo-social-automation`|
|44|Oldies Radyo Social & News Automation|PASİF|1.8.0|`oldies-radyo-social-automation-v1.8.0-facebook-global-DEPLOY-1/oldies-radyo-social-automation-v180-global/oldies-radyo-social-automation`|
|45|Oldies Radyo Social & News Automation|PASİF|1.7.5|`oldies-radyo-social-automation/oldies-radyo-social-automation/oldies-radyo-social-automation`|
|46|Oldies Radyo Social & News Automation|AKTİF|1.7.5|`oldies-instagram-reconnect-175/oldies-radyo-social-automation`|
|47|Oldies Radyo Social & News Automation|PASİF|1.7.5|`oldies-radyo-social-automation-v1.7.5-local-render-fix-1/oldies-radyo-social-automation/oldies-radyo-social-automation`|
|48|Oldies Radyo Social & News Automation|PASİF|1.7.5.1|`oldies-instagram-reconnect-175-REPLACE-SCANSAFE-1.7.5.1/oldies-instagram-reconnect-175/oldies-radyo-social-automation`|
|49|Oldies Radyo Social & News Automation|PASİF|1.8.0|`oldies-radyo-social-automation-v1.8.0-facebook-global-DEPLOY/oldies-radyo-social-automation-v180-global/oldies-radyo-social-automation`|
|50|Oldies Radyo Social & News Automation|PASİF|1.7.5|`oldies-radyo-social-automation-v1.7.5-local-render-fix/oldies-radyo-social-automation/oldies-radyo-social-automation`|
|51|Oldies Radyo Social & News Automation|PASİF|1.7.5.1|`oldies-social-scansafe-1751/oldies-social-scansafe-1751/oldies-radyo-social-automation`|
|52|Oldies Radyo Social & News Automation - SCANSAFE FINAL|PASİF|1.7.5.2|`OLDIES-SOCIAL-SCANSAFE-FINAL-1.7.5.2/oldies-social-scansafe-final-1752/oldies-radyo-social-automation`|
|53|Oldies Radyo TR→EN News Guard|AKTİF|1.0.4|`oldies-tr-en-news-guard/oldies-tr-en-news-guard`|
|54|Oldies Radyo — Etsy OAuth Bridge|AKTİF|1.2.1|`oldies-radyo-etsy-bridge/oldies-radyo-etsy-bridge`|
|55|Oldies Revenue CTA Fix|AKTİF|1.3.1|`oldies-revenue-cta/oldies-revenue-cta`|
|56|Oldies Site Integrity|AKTİF|0.2.1|`oldies-site-integrity/oldies-site-integrity`|
|57|Oldies Social SCANSAFE CLEAN|PASİF|1.7.5.4|`OLDIES-SOCIAL-SCANSAFE-CLEAN-20261002/oldies-social-scansafe-clean-20261002/oldies-social-scansafe-clean`|
|58|Page Optimize|AKTİF|0.6.4|`page-optimize/page-optimize`|
|59|Polylang|AKTİF|3.9.1|`polylang/polylang`|
|60|Secure MCP Server for Claude, ChatGPT, Gemini and other AI providers|AKTİF|1.4.8|`miniorange-secure-mcp-server/miniorange-secure-mcp-server`|
|61|Site Kit by Google|AKTİF|1.187.0|`google-site-kit/google-site-kit`|

## İncelenen kaynak paketlerinin SHA256 kayıtları

Bu hashler yerel incelenen arşivlerin kimliğidir; canlı WordPress dosya hashleri değildir.

| Paket | SHA256 |
|---|---|
|OLDIES_ANA_KUMANDA_KURULUM_PAKETI.zip|`cd2177def44ed637a73c66587836fd9ee77618425d132b28c37d7d4caf5934c2`|
|OLDIES_RADYO_WORK1_Kanit_ve_Geri_Donus.zip|`bfaf27440eaa655a3f0625ce002f88e5cda97e3e64f1dd2789ad99f344f8f24e`|
|Oldies_Revenue_Implementation_Pack.zip|`6e377366f33142f3f6108439a06fe3d05b08753a1ba8e386a0d501ee1b42de2c`|
|Oldies_Site_Integrity_20261003.zip|`10c3bafd870f68624b66599d2094bb0628b5e819fe0fa9812597a88cee9b74cb`|
|oldies-en-automation-final.zip|`7c273a707799b48ccfce02cb880da68b22f88588510ce261ae47bd2aee085fc3`|
|oldies-etsy-distribution-center-v1.2.1-MP4-UPLOAD-FIX.zip|`f68a7afb09891fa77e412ff8a1dc75cad7cc14ab933d56ae14661764cc5d993e`|
|oldies-facebook-global-companion-v1.0.3-R3-ROOT-DEPLOY.zip|`56121645ef215506d00f1cc90eac14813efef5a7f4cb187f7e16808879bf93d1`|
|oldies-facebook-global-mcp-bridge-v1.0.5-ROOT-DEPLOY.zip|`b53c7dcf65d028a07f90536758ea580c7547cbeeeef814fec8223f0d07c48fec`|
|oldies-facebook-global-settings-v1.0.1-ROOT-DEPLOY.zip|`7ef5fc61af1e040707cca1dbb6d806123564eccd8a35085ea2a487c51bb5fce0`|
|oldies-global-router-v1.0.10.zip|`69ac1056955adc3fb13e4af5f8c754a9aa52469db80fb012eb940541dce754ea`|
|oldies-polylang-mcp-helper-v1.3.0.zip|`d6e50dea3aa483813ab1d30e4ad320a531ca928e2cc24656711e86b5398aa64d`|
|oldies-radyo-etsy-bridge-v1.2.1(1).zip|`d8deeef2ba379ee08fa2f513c7d3dd7362b0145e33b01b94db742446f0e094e9`|
|oldies-radyo-social-automation-v1.7.5-VERIFIED(1).zip|`5f1a3346191df38a8a070fb1444703335641438b2010941ee366928054f0342f`|
|oldies-reels-bridge-v2.1.10-ZERO-COST-INTAKE-FIX.zip|`c61cb42eee373fab92a6d6bc984a73be018ee7b48502902f9a86832eeb83a408`|
