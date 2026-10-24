# WORK MASTER — WordPress kaynak incelemesi, bölüm 1
**24.10.2026 | 05:11 TSİ (UTC+3)** — Kaynak taraması ve statik değerlendirme; canlı onarım değildir.

- **GERÇEKLEŞEN:** Mevcut arşivlerden 14 paket ayrıştırıldı; haber, Etsy keşif/poll, OAuth, çeviri ve yayın korumasının kritik kod yolları okundu.
- **GERÇEKLEŞEN:** Haber sessiz hata yolu, Etsy token ön kontrolü, yayın sırası/Integrity uyuşmazlığı ve panelin koşullu yazma davranışı belirlendi.
- **BEKLEYEN:** Canlı dosyalarla hash eşitliği, gerçek cron listesi ve son doğal koşu kayıtları. Aynı sürüm etiketi aynı canlı dosya demek değildir.
- **PLANLANAN:** Diğer özel eklentilerin sorumluluk/bağımlılık kartları ve standart eklentilerin işlevleriyle haritayı tamamlamak.
- **KORUMA/DÜZELTME:** Bu bölümde eklenti kodu çalıştırılmadı. Önceki Etsy ekranı açılışının hiç kayıt yazmadığı kanıtlanamaz; aşağıdaki düzeltme önceki kesin ifadelerin yerine geçer.

## Kanıt düzeyleri

14 paket içinde 8 özel eklenti için canlı envanterle aynı sürüm etiketi taşıyan kaynak bulundu: Social & News1.7.5, Etsy Distribution1.2.1, Etsy OAuth1.2.1, FB MCP1.0.5, Global Router1.0.10, Polylang Helper1.3.0, Revenue CTA1.3.1 ve Integrity0.2.1. Hiçbiri canlı dosya hashleriyle eşleştirilmedi. Social paketinin kökü ayrıca aktifteki `oldies-instagram-reconnect-175` kökünden farklıdır.

Command Center1.0.6, FB Companion1.0.3-R3, FB Settings1.0.1 ve Reels Bridge2.1.10 kaynakları tarihsel kopyalardır; canlı sürümler sırasıyla1.0.9,1.0.7-R7,1.1.0 ve2.3.7-YT8-SAFE2'dir. FB Token Bridge2.0.0 ve TR→EN Guard1.0.4 kaynakları bulunamadı. Son ikisinin iç işleyişi incelenmiş sayılmaz.

## Haber: tetikleyici ve durma noktaları

Social `src/Cron/Scheduler.php` satır46,88,115–142,193–212: `oldies_news_check_sources_cron` 15 dakikalıktır; 10 dakikalık transient kilit kullanır. `Throwable` yakalanıp hata kaydı yazılmadan geçilir. Bu kaynakta sessiz arıza mümkündür. Canlıda hangi istisna oluştuğu bilinmiyor.

`src/Plugin.php`295–300,312–323: olayları kurma işlemi aktivasyonda ve DB sürümü farklıyken yapılır. DB sürümü aynı kalırken olay silinmişse olağan init bunu mutlaka geri kurmaz. Bu, 22 Eylül'de kalan taramayı açıklayabilecek bir hipotezdir; mevcut cron listesi olmadan neden ilan edilemez.

`src/News/NewsCoordinator.php::runScheduledCycle`: yalnız bu taramada yeni alınan aday ID'lerini işler. Eski PENDING/NEEDS_REVIEW yığınının her doğal koşuda yeniden ele alınacağı varsayılamaz. `SourceManager::pollAllSources` RSS alma ve kaynak kontrol zamanını AI doğrulamasından önce kaydeder. Dolayısıyla yalnız eksik OpenAI anahtarı, bütün kaynakların son kontrol tarihinin eski kalmasını tek başına açıklamaz.

`NewsVerifier.php` canlı web aramasından iki ayrı güvenilir yabancı alan adı, model teyidi ve çelişkisizlik ister; yapılandırma yoksa NEEDS_REVIEW döner. Bu denetimi kaldırmak onarım değildir. `ArticleGenerator` ve görsel hazırlığı ayrıca dış servis kullanabilir; bu tur tetiklenmedi.

## Haber yayıncısı ile Integrity arasında kaynakta görülen uyumsuzluk

`NewsPublisher.php::publishArticles` önce TR/EN yazılarını hedef durumla `wp_insert_post` üzerinden kaydeder; görsel, dil ve iki yönlü eşlemeyi daha sonra ekler. Sonuçtaki `published` ve tablo PUBLISHED değeri, gerçek `get_post_status` okumak yerine `$shouldPublish` kararından üretilir. İki dile aynı `$categoryId` atanır.

Integrity0.2.1 `oldies-site-integrity.php`189–255,275–294 yeni yayın için görsel/dil/eşleme/kategori uyumu arar; klasik ekleme geçmezse durumu `pending` yapar. Yeni yazının bu alanları sonradan doldurulduğu için kaynakların bu birleşiminde yayıncının PUBLISHED dediği yazı gerçekte pending kalabilir. Ayrıca aynı dil kategorisinin iki dile yazılması yanlış kategori dili kontrolüne takılabilir. Bu, kaynakların birlikte okunmasından çıkarılan somut uyumluluk bulgusudur; canlıda gerçekleştiği henüz kanıtlanmadı. Otomatik yayın zaten OFF olduğundan mevcut173 adayın nedenini tek başına açıklamaz.

Onarım tasarım ilkesi: önce iki taslak + doğru dil kategorileri + görsel + eşleme; sonra mevcut Integrity kapısından yayın; her iki gerçek durum geri okunup sonuç yazılmalı. Şu anda canlı uygulama/ayar değişikliği yapılmadı.

## Etsy: aktif Distribution ve eski Social kolu ayrıdır

Distribution1.2.1 `src/Cron/EtsyAutomationScheduler.php`: keşif `oldies_etsy_dist_discovery_v110` 172800 saniye/48 saat, render kontrolü `oldies_etsy_dist_poll_v110`300 saniye/5 dakika; keşif başına en çok2 yeni başlangıç, poll başına4 iş, kilit240 saniye. Keşfi kapatmak poll'u kendiliğinden kapatmaz. Init eksik olayları koşullu kurabilir.

`src/Etsy/ProductSyncService.php::runScheduledSync` önce `connectionStatus() !== 'Connected'` ise çıkar. OAuth1.2.1 `includes/class-or-etsy-client.php::connection_status` süresi dolmuş erişim tokenına TokenExpired der; kendi başına yenilemez. Yenileme `EtsyBridgeAdapter::request` içindeki `refresh_if_needed(false)` adımındadır ve o adım ön kontrolden sonradır. Bu nedenle süresi dolan erişim tokenı, geçerli refresh tokenı olsa da bu keşif yolu yenilemeye ulaşmadan durabilir. Canlı TokenExpired ekranıyla uyumlu bir aday neden; bütün10ERROR işinin nedeni değildir. Eski Social Etsy senkronunda da benzer sıra vardır.

Keşif yalnız ilk aktif ilan sayfasını (`limit≤100,offset0`) ister; daha fazla ilan için bu metotta sayfalama yoktur. Watermark/zaman damgası ve işlem başına2 başlangıç, aynı zaman damgalı yoğun değişikliklerde ayrı bir sınır incelemesi gerektirir. Kayıp iş olduğu ispatlanmadı; otomatik retry önerilmedi.

Distribution `DistributionCenterService` META_FINAL için120MB sınırı,MP4,10–30 saniye,dikey en az720×1280 ve okunabilir gerçek medya metadatası arar. Manuel IG/FB “PUBLISHED” kaydı URL doğrular; platformda paylaşımın gerçekten var olduğunu bağımsız doğrulamaz. MASTER_SAFE ile META_FINAL ayrımı korunur.

## Önceki salt okunur inceleme ifadesinin düzeltmesi

Distribution `src/Admin/DistributionAdmin.php` tabloyu gösterirken `DistributionCenterService::state` çağırır. Bu metot `dist->ensure` ile satır yaratabilir; master hazır ve sync_hash değişmişse master/META_FINAL/kanal durumlarını ve last_error alanını günceller. Önceki Etsy denetim raporu da aynı yan etkiyi bildiriyordu.

Bu yüzden önceki raporlardaki “yalnız görünüm okundu / WordPress durumu değişmedi” ifadesi kesin güvence olarak kullanılamaz. Açık bir kaydetme, retry veya render komutu verilmedi; ancak önce/sonra DB dökümü olmadığından ekran açılışının koşullu yazma yapmadığı ispatlanamaz. Ekran tekrar açılmadı. “Test Connection” da token yenileyip kayıt yazabilir; adı test diye salt okunur sayılmaz.

## Çeviri katmanları

Haber eklentisinin çift dil üretimi, TR→EN Guard1.0.4, pasif EN Draft Agent ve tema içindeki `inc/ai-english.php` ayrı işlerdir. 4Ekim tema yedeğinde kuyruk `oldies_ai_translation_queue`, worker `oldies_ai_translation_worker`5 dakika, kayıtlar `oldies_ai_en_<path-hash>` HTML önbelleği şeklindedir. Bu, native Polylang EN yazısı üretmekle aynı şey değildir. Native EN yazıları tampon çevirisini atlar. Anahtar yoksa üretim yapılmaz; uygun EN ziyaretinde kuyruk yazılması mümkündür. Günlük istek sınırı ve bekletme/backoff vardır. Güncel temayla eşitliği doğrulanmadı.

Polylang Helper1.3.0 status/get/preview yolları ile pair/meta-repair yazma yollarını ayırır. REST meta pair yolu çakışan mevcut ilişkiyi reddeder; genel `pair(confirm=true)` yolu aynı çakışma kontrolünü içermez. Bu nedenle “preview valid” mevcut ilişkiyi değiştirmeye izin verildiği anlamına gelmez. Hiçbir pair işlemi çalıştırılmadı.

## Devam kaydı

Kaynak dosyalarının yerel yolu `deep_wp_20261024/code/pkg_##` altındadır; yalnız metin çıkarımı/statik okuma yapıldı. Kaynak paket kimlikleri ve kapsam kartları bir sonraki bölümde tamamlanacak. Canlı Dinle/oynatıcı kurucu Mete'dedir ve henüz başlatılmamıştır; MASTER arızası değildir. Eylül4817/4818 taslakları korunur. Jingle ertelemesi ve mevcut üretim/yayın kilitleri sürer.
