# OLDIES RADYO — PART-001 | TR/EN HABER SEO & INDEX SALT-OKUNUR DENETİMİ

**Kayıt:** 05.11.2026 | 07:14 TSİ (UTC+3)  
**Görev:** `oldies-news-seo-bilingual-20261105` / [#41](https://github.com/MetteBuyuretti/oldies-reels-worker/issues/41)  
**Uygulama oturumu:** Ana Kumanda mevcut oturumu; gerçek erişim: GitHub okuma/yazma, WordPress Polylang MCP salt-okunur, Windows Remote Desktop Commander aracılığıyla anonim canlı HTTP. Ayrı Work Master oturumunun otomatik başladığı iddia edilmez.  
**Kapsam:** PROJECT.md Paket A. **Canlı kod/tema/eklenti/ayar, yayın ve otomasyon değişikliği: SIFIR.**

## GERÇEKLEŞEN — kanıtlarıyla

1. `AGENTS.md`, `control-center/work-state.json`, `control-center/WORK_CONTINUITY_PROTOCOL.md` ve `PROJECT.md` okundu. Mevcut `site-integrity-20261003` `done`, `tr-en-parity-20261004` `in_progress`; **ikisine de yazılmadı / eski içerik üretimi tekrar edilmedi**.
2. Canlı WordPress REST, kategori ve HTML okuması: toplam **59 published post**; `Yeni Müzik Haberleri` kategorisinde **10 TR + 10 EN** kayıt bulundu. Aynı görsel ID + yakın yayımlanma tarihi üzerinden **10 eşleştirme ADAYI** kuruldu; native Polylang doğrulaması ayrıca yalnız **4 çiftte** yapıldı: #4882↔#4883, #4878↔#4879, #4876↔#4877, #4817↔#4818 (her iki yönde). Bu aday eşleştirmesini 10/10 native kabul gibi sunma.
3. **20/20 canlı haber sayfası HTTP 200**, **20/20 tek self-canonical**, **20/20 TR/EN hreflang**, **20/20 karşı dildeki eşin URL'si hreflang'de**; test edilen 20 sayfada açık `noindex` yok. `x-default` TR'ye yönleniyor (Bowie çiftinde görüldü). Frontend linklerinin varlığı Google indeks kanıtı değildir.
4. **HATA — 20/20 sayfada iki `meta name="description"`**. Özellikle bir meta `<!-- Oldies Radyo SEO fallback v3.5 -->` yorumunun yanında; ikinci meta başka WordPress head çıktısında. Bazı haberlerde iki açıklama farklı uzunlukta (Fleetwood/Bowie), bu nedenle yalnız kozmetik değil. Kök nedenin kesin PHP hook'u **henüz okunmadı**; tema fallback ile diğer head çıktısı çakışması güçlü hipotez, **canlı düzeltme yapılmadı**.
5. **20/20 sayfada iki `application/ld+json` bloğu**. Bowie TR örneğinde blok-1: `Person, Article, BreadcrumbList`; blok-2: `Organization, WebSite, Person, BreadcrumbList, WebPage, Article`. Aynı sayfada birden çok `Article` ifadesi var. Birebir aynı yapılandırılmış veri olduğu henüz ispatlanmadı; graph düğümleri/ID eşitlikleri ve sağlayıcı düzeyi ayrı denetim ister.
6. **17/20 sayfada hiç tag yok**, buna karşın **20/20 excerpt dolu**, **20/20 featured media ID mevcut**. “Tag yok” tek başına sıralama engeli sayılmaz; planın 0–6 anlamlı tag standardı için örnekleri değerlendir. Görsel alt yazısı ve içerik çeviri kalitesi 20/20 olarak doğrulanmadı.
7. Son 10 çiftin **7 çifti 1 Ekim ve sonra yayımlandı**, 3 çift daha eski. Dolayısıyla **30 yeni haber çifti bu kategoride erişilebilir değil**: örneklem genişliği gerçekçi olarak 10 kategori çifti / 20 sayfadır. 1 Ekim sonrası 7 çiftin biri **Eylül 2026 aylık arşiv** içeriğidir; yeni gündem haberi gibi sayılmamalıdır. Önceki 13 son tarihli TR/EN yayın çiftinin içinde araştırma gibi başka kategoriler de vardır; onları bu yeni-haber kapsamına sessizce karıştırma.
8. `robots.txt` HTTP 200 ve `/wp-admin/` disallow + WordPress AJAX allow; bildirilen sitemaps: `sitemap.xml`, `news-sitemap.xml`, `oldies-english-sitemap.xml`. Üçü de HTTP 200. Jetpack `sitemap.xml` → `sitemap-index-1.xml` → `sitemap-1.xml` / `sitemap-2.xml` zinciri keşfedildi. `news-sitemap.xml` içinde son 4 Kasım Bowie TR/EN URL'leri var; EN özel sitemap'te Bowie EN URL'si var. Ana sitemap-index'in kendisinde tekil haber URL'sinin doğrudan olmaması sorun sayılmaz; alt sitemaplerde görünürlük ayrıca tam taranmalı.
9. **GSC erişimi BLOKLU:** `GSC_Wizard.list_sites` salt-okunur çağrısı `payment_required / subscription_required` döndü. **Ücretli üyelik açılmadı**, yeniden çağrı döngüsü yapılmadı. `Site Kit` aktif olduğu proje dosyasında kayıtlı, ancak bu denetimde doğrudan GSC mülkiyeti/URL inspection/indeks görünümü okunamadı. **Google'da indekslendi iddiası YOK.**
10. PROJECT.md ilk kanıtındaki `TR→EN News Guard 1.0.4`, `Polylang 3.9.1`, `Oldies Site Integrity 0.2.1`, `Google Site Kit 1.187.0` sürümleri mevcut görev planından alınmış **önceki denetim bulgusudur**; bu teslimde aktif eklentilerin yeniden sürüm sayımı yapılmamıştır.

## Örnekler ve canlı kanıt

| Çift | TR ↔ EN | Sonuç |
|---|---|---|
| Bowie | 4882 ↔ 4883 | 200/200, native Polylang doğru, canonical+hreflang var; **iki description** / iki Article JSON-LD bloğu |
| Fleetwood Mac | 4878 ↔ 4879 | 200/200, native Polylang doğru, bazı meta description değerleri farklı uzunlukta |
| Rolling Stones | 4876 ↔ 4877 | 200/200, native Polylang doğru, iki description |
| Eylül aylık | 4817 ↔ 4818 | 200/200, native Polylang doğru; **yayımlanma tarihi Ekim fakat içerik dönemi Eylül** |

- [Bowie TR](https://oldiesradyo.com/2026/11/04/david-bowie-1978-stage-konser-goruntuleri-2027/) — [Bowie EN](https://oldiesradyo.com/en/2026/11/04/david-bowie-1978-stage-immersive-concert-2027/)
- [robots](https://oldiesradyo.com/robots.txt) · [sitemap](https://oldiesradyo.com/sitemap.xml) · [news sitemap](https://oldiesradyo.com/news-sitemap.xml) · [English sitemap](https://oldiesradyo.com/oldies-english-sitemap.xml)
- Yerel makinedeki ayrıntılı örneklem: `C:\Users\METE\Documents\Oldies-AI-Calismalari\Web-SEO-20261105\audit-public-sample.json` ve `audit-public-sample.csv`. Kamuya açık veriler, kişisel anahtar içermez.

## RİSK / SINIR / GERİ DÖNÜŞ

- **P1 hata:** Çift meta description 20/20, en az bir örnekte iki Article JSON-LD. Doğrudan plugin kapatma veya tema değişimi **yasak**; önce `SEO fallback v3.5` ve ikinci çıktının PHP hook/ayar kaynağı ile HTML fixture kontrolü.
- **P2 içerik kalite kuyruğu:** 17/20 tag boş, iç bağlantı/alt lisans/özgün EN doğrulaması örneklemle genişletilecek; içerik değiştirilmedi.
- **BLOKER:** GSC Wizard üyeliği durmuş. Google Search Console özgün ücretsiz erişimi/WordPress Site Kit içindeki okunabilir metrikleri varsa yetki içinde kullan; erişim yoksa `UNVERIFIED_GSC_ACCESS`.
- **Korunan:** Eski `tr-en-parity-20261004` backlog'u, Site Integrity, bülten `email_content_format=excerpt`, otomatik yayın ve diğer Oldies sistemleri değişmedi. Hiçbir abonelik e-postası gönderilmedi.
- **Rollback:** Bu aşama salt-okunur + GitHub kanıt kaydıdır; canlı sistemde geri dönecek değişiklik yok.

## SONRAKİ ADIM — PAKET B'YE GEÇİŞ ÖNCESİ DARALTMA

1. Head çift-üreticisinin **tam kaynak/çalışma hook'unu** erişim dâhilinde salt-okunur bul. Tek description ve tek tutarlı `Article` üretilecek, mevcut self canonical/hreflang korunacak şekilde **izole/staging test** yap.
2. News Guard gerçek tetikleme/kapsam/retry/idempotency kodunu/loglarını **salt-okunur** incele; eski çeviri backlog'una dokunma.
3. İki hazır TR/EN çiftinde içerik iç link, görsel alt, dil ve SEO kontrolü; kontrol sonucuna göre yalnız geri alınabilir minimal taslak üret.
4. **Canlı tema/eklenti değişikliği için mevcut onay kapısı ve bağımsız WATCHDOG QA gerekir.** Kullanıcı kritikte karar verir; bu kayıt canlı yetkisini artırmaz.

**Durum:** Paket A sınırlı ama somut salt-okunur envanter/teknik-head denetimi teslim edildi. **Teknik denetim çıktılandı; canlı SEO düzeltmesi/Google indeksi henüz yapılmadı.**