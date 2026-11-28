# OLDIES RADYO — Web sitesi ve yarım kalan işler: 28 Kasım 2026 denetimi

**Tarih/saat:** 28.11.2026 | 04:37 TSİ (UTC+3)  
**Durum:** SALT-OKUNUR DENETİM. WordPress/tema/plugin/SEO ayarı, GSC doğrulaması, yayın, otomasyon veya maliyet değiştirilmedi.  
**Kaynak:** Ana Kumanda mevcut oturumu; canlı WordPress.com / Jetpack Stats, WordPress REST, 8 anonim HTML, WordPress Polylang MCP, GitHub görev kaydı ve Gmail GSC bildirimleri. Genel WordPress sağlık göstergesi gerçek SEO indeks kabulü sayılmaz.

## KISA SONUÇ

Site canlı ve haber/araştırma yayınları var. Son 30 günlük toplam görüntülenme +%5,7, benzersiz tarayıcı sayısı +%17,4; ancak rakamlar küçük. Yeni haber yayınında 20 Kasım'dan 27 Kasım sonuna dek yayımlanmış yeni post yok; 24 Kasım Beatles TR/EN çifti taslakta. Haftalık 1960'lar ülke serisi 27 Kasım'da Norveç TR/EN ile devam etmiş. İngilizce yeni haberlerin ve araştırmaların örneklemlerde karşılığı/doğal anlatımı sağlam; eski İngilizce arşivin genel eksiklik kuyruğu hâlâ açık. #41 SEO/GSC ve #43 haber görsel/banner geliştirmesi kapanmadı.

## GERÇEKLEŞEN — CANLI KANIT

### 1) Trafik, izlenme ve abone
- **Jetpack son tamamlanmış 30 gün (29 Eki–27 Kas):** 446 sayfa görüntülenme, 250 tarayıcı ziyaretçi; önceki eşdeğer 30 gün 422/213, sırasıyla **+%5,7 / +%17,4**. Bu WordPress ölçüsüdür, aynı kullanıcıların cihazları farklı görünebilir. 7 gün 103 görüntülenme, önceki 7 gün 112 (**-%8,0**).
- **Takvim ayları:** Ekim 444 görüntülenme/223 ziyaretçi; Kasım 1–27 416 görüntülenme/233 ziyaretçi. Kasım henüz tamamlanmadı. Son 30 gün en çok: EN Live Radio 47, TR Canlı Dinle 36, EN 1960s Almanya 34, EN İtalya 26, EN Fransa 23, EN Yunanistan 18.
- **Jetpack arama yönlendirmeleri son 30 gün:** arama motorlarından 209 görüntülenme; Google Search 187, Bing 10, Yahoo 8, DuckDuckGo 2, Yandex 2. Facebook 5, Instagram 2. Bunlar Google Search Console tıklaması/indeks kanıtı değildir.
- **Takipçiler:** 1 email abonesi (Haziran–Kasım değişim 0), 0 WordPress Reader takipçisi. Jetpack sosyal `publicize` boş ve Metricool hesabı sosyal ağa bağlı değil; **Instagram ve Facebook canlı takipçi büyümesi doğrulanmadı**. Gönderilen son bültenlerde 1 alıcı, 0 tıklama.
- **WordPress durum:** aktif site/healthy (WordPress dashboard göstergesi), 28 aktif eklenti. Güncelleme bildirimi Site Kit 1.192.0, miniOrange MCP 1.5.10 ve HFCM 1.1.47 için var; hiçbir eklenti otomatik güncellenmedi.

### 2) SEO, robots, sitemap, HTML head
- Canlı 8 örnek (ana sayfa TR/EN, Haberler TR/EN, David Bowie haber TR/EN, Norveç araştırma TR/EN) **8/8 HTTP 200**, **8/8 tek meta description**, **8/8 tek canonical**, **8/8 karşılıklı tr/en hreflang**. Önceki 5 Kasım çift-description kusurunun görünür HTML çıktısı, kurulu **Oldies Radyo #41 Head and Draft Language Link Repair v0.1.2 ACTIVE** sayesinde düzelmiş görünüyor. Bu kod bir frontend filtre; alttaki iki üretici kaynağını kaldırmıyor. **Tekrar onarma.**
- `robots.txt`, `sitemap.xml`, `news-sitemap.xml`, `oldies-english-sitemap.xml` anonim GET ile 200. GSC #41 17 exact 301 ve 9 EN RSS onarımı 12 Kasım'da canlı test edildi, ilgili iki eklenti bugün de **ACTIVE**; tüm 26 URL bu oturumda yeniden test edilmedi.
- Canlı TR Bowie ve TR Norveç araştırma HTML çıktısında **2 Article JSON-LD node**, İngilizcelerinde **1**. Birden çok Article node tek başına yanlışlık kanıtı değil; semantik @id/çelişkili veri kontrolü hâlâ gerekli.
- **Google'ın indeks durumu doğrulanamadı.** GSC Wizard `payment_required`; Windsor.ai 3 bağlı kaynak/ücretsiz plan 1 kaynak sınırından dolayı bütün `get_data` çağrılarını reddetti. İki serviste de abonelik/silme işlemi yapılmadı.
- **19 Kasım 2026 Google Search Console e-postaları:** domain ve URL-prefix görünümünde 'Başka bir 4xx sorunu nedeniyle engellendi' bildirimi var; **12 Kasım onarımından sonra** gelen ayrı bir uyarı. Etkilenen gerçek URL listesi okunmadan bunun eski 7 kasıtlı 404 mü yoksa yeni problem mi olduğu anlaşılamaz. **Kör toplu GSC Validate Fix yapma.**

### 3) Türkçe / İngilizce içerik ve otomasyon
- Canlı WP REST'te `Yeni Müzik Haberleri` kategorileri: **24 TR yayımlanmış / 24 EN yayımlanmış**. Bu 24'ün hepsinin native eşleşmesi ve editoryal doğruluğu bu turda tek tek incelenmedi.
- Canlı WP REST'te Avrupa 1960s araştırmaları: **12 TR / 12 EN yayımlanmış**. 27 Kasım Norveç, 20 Kasım İsveç çiftleri içerik örneklemi olarak incelendi; sanatçı isimleri ve yedi ana bölüm karşılıklı tutarlı, Norveç'te 5 görsel/5 alt, 4 iç link/19 dış link; İsveç'te 4 görsel/4 alt,4 iç link/16 dış link. Haber örnekleri (Brian Eno, Duran Duran) İngilizce okunabilir, ancak kimi haberde 0 ilgili iç bağlantı ve 0 tag var. 0 tag otomatik SEO cezası anlamına gelmez.
- Polylang MCP ile **4 örnek çift iki yönde publish + doğru dil bağı** doğrulandı: Norveç #4471↔#4472, İsveç #4469↔#4470, Brian Eno #5029↔#5030, Duran Duran #5007↔#5008.
- **Son yeni haber yayını 20 Kasım** (Peter Gabriel, Brian Eno iki dilde). **21–27 Kasım arası Yeni Haberler kategorisinde yeni yayın yok.** Ancak **24 Kasım Beatles 'In My Life' TR #5198 / EN #5199** kayıtları `draft`; yayına otomatik hazırlık/akış neden durdu sorusu kaynak ve log incelemesi ister. Taslaklara dokunulmadı.
- 27 Kasım Norveç TR/EN araştırmaları WordPress Activity Log'da `post__published`, aktör `is_cron=true`: haftalık araştırma yayın akışının en az bu günü çalıştığı doğrulandı.
- Eski TR→EN eşitleme `tr-en-parity-20261004` `in_progress`, checkpoint Ekim4. O tarihte 70 tam çeviri yapılmış, **59 eşleşmemiş ve 450 kısa EN inceleme adayı** bulunmuştu; bu sayılar **güncel yeniden sayım değildir**. Yeni haberlerin iyi olması, eski büyük arşivin bütünüyle iyi olduğunu kanıtlamaz.

## BEKLEYEN / ÖNCELİK

**P1 — Google indeks ve 4xx:** 19 Kasım yeni resmî uyarılar için GSC'deki exact URL listesi ve Search Console canlı ölçümleri, 12 Kasım onarımı sonrası crawl, gerçek indeks sayısı ve tıklama/impressions/CTR; 7 kasıtlı 404'ü otomatik yönlendirme / yeniden doğrulama YOK. #41 bağımsız WATCHDOG kabulü henüz kanıtlanmış değil.

**P1 — Yeni haber üretim kontrolü:** 20–27 Kasım yeni haber yayın boşluğu ve 24 Kasım iki Beatles taslağının durumu; TR→EN Guard v1.0.4 gerçek PHP/cron/error log ve idempotency testleri. Var olan yayınları tekrar oluşturma, taslakları kullanıcı QA olmadan publish etme YOK.

**P2 — Eski EN arşiv:** eski translation backlog sahipliği/counters yeniden ölçülmeli; 59/450 eski sayıları güncel gerçek sayı sayma. İki örnek ülke yazısı olumlu fakat bütün site PASS değil.

**P2 — Görsel tasarım:** [Issue #43](https://github.com/MetteBuyuretti/oldies-reels-worker/issues/43) haber fotoğraflarının 4:3 crop/blur-fill, dinamik görselli aylık TR/EN banner, 390px mobil QA. Aktif tema kaynak haritası 17 Kasım'da doğrulandı fakat staging/canlı uygulama/kurucu görsel kabulü kanıtlanmadı. Aylık/tekil haber ayrımı 25 Ekim'de zaten DONE, **yeniden kurma**.

**P2 — Article JSON-LD ve meta kaynak bakım:** #41 v0.1.2 frontend görünümü doğru; tekrar eden TR Article düğümlerinin çakışma içerip içermediği ve iki üretici hook'u ayrıntılı test bekliyor; canlı eklentileri rastgele kaldırma YOK.

**P3 — Bülten ve takipçi:** 1 abone; içerik üretiminin aboneliğe/sosyal trafiğe dönüşümü yok denecek kadar az. Geri dönüşümsüz pazarlama veya yayın ayarı açmadan mevcut CTA, SEO iç bağlantı ve ölçümler incelenebilir. Sosyal takipçi büyümesini görmek için Instagram/Facebook'un gerçek Insights bağlantısı gerekli.

## UYGULAMA SINIRLARI

Bu denetimde **hiçbir canlı site içeriği, tema, WordPress SEO ayarı, plugin, abonelik, otomatik gönderim, GSC doğrulama, sosyal hesap veya ücretli servis değiştirilmedi**. GitHub raporu salt-okunur saha denetiminin kalıcı kanıtıdır, başka Work veya WATCHDOG oturumunu otomatik tetiklemez. Kritik düzeltmeler için önce mevcut kaynak/backup, staging, bağımsız WATCHDOG ve kurucu onayı.

## KAYNAKLAR
- GitHub [#41](https://github.com/MetteBuyuretti/oldies-reels-worker/issues/41), [12 Kasım SEO head onarım kabulü](https://github.com/MetteBuyuretti/oldies-reels-worker/blob/main/work-output/oldies-news-seo-bilingual-20261105/08-live-head-nav-fix-acceptance-20261112.md), [work-state](https://github.com/MetteBuyuretti/oldies-reels-worker/blob/main/control-center/work-state.json).
- GitHub [#43 haber kartları/banner](https://github.com/MetteBuyuretti/oldies-reels-worker/issues/43), [kaynak haritası](https://github.com/MetteBuyuretti/oldies-reels-worker/blob/main/work-output/news-visual-refresh-20261115/part-003-theme-mapping.md).
- Canlı [TR haberler](https://oldiesradyo.com/muzik-haberleri/) · [EN haberler](https://oldiesradyo.com/en/music-news/) · [TR Norveç](https://oldiesradyo.com/2026/11/27/1960larda-norvec-10-unlu-sarkici/) · [EN Norveç](https://oldiesradyo.com/en/2026/11/27/1960s-norwegian-singers/) · [robots](https://oldiesradyo.com/robots.txt) · [sitemap](https://oldiesradyo.com/sitemap.xml).
- Bağlı WordPress.com Jetpack Stats overview/visits/insights/followers/top-content/referrers, WP REST, WP Activity Log, WP plugins. Gmail 19 Kasım resmî GSC uyarısı; GSC ve GA4 query servisi erişim engelli (rakam uydurulmadı).
