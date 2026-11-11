# OLDIES RADYO — #41 GSC 404 ONARIM ADAYI QA (CANLI OLMAYAN)
**12 Kasım 2026 | 02:42 TSİ (UTC+3)**  
**İş:** `oldies-news-seo-bilingual-20261105` · **Rol:** Ana Kumanda mevcut oturum teknik QA · **Durum:** TEST EDİLDİ / CANLIYA ALINMADI

## GERÇEKLEŞEN — KANIT

1. [02-oldies-gsc41-repair-candidate.php](02-oldies-gsc41-repair-candidate.php) hazırlandı: 16 **exact-match** 301 adayı ve yalnız GSC listesindeki 9 EN RSS yolu için `request` filtresi; wildcard yok. GitHub blob SHA **95e673edf72ad5edc8b58ab80b7047fb9e9386a6** ile yerel test edilen dosyanın Git object SHA değeri **birebir aynı**. Her iki değişiklik **varsayılan olarak KAPALI** (`OLDIES_GSC41_ENABLE_REDIRECTS`, `OLDIES_GSC41_ENABLE_FEEDS` tanımlı ve true olmadıkça işlevsiz).
2. PHP sözdizimi denetimi: `php -l` → **No syntax errors detected**. Yerel izole PHP harness: **102/102 assert PASS**. Bu harness canlı WP testi değil; whitelist sayıları, redirect map, kategori/post feed değişkenleri, dil, taslak/POST engellerini doğrular. [03 ... offline fixture](03-oldies-gsc41-repair-fixture-test.php) ayrıca repo klasörüne kondu; **repo fixture'ının kendi koşu çıktısı henüz kaydedilmedi**.
3. GSC 33 triyaj CSV içinden tam 16 sayı-ekli kaynak → **12 ayrı** hedef çıkarıldı. Tarihsel 95 envanteriyle 16 kaynak çakışmıyor; öz-yönlendirme yok. Canlı read-only HTML kontrolü: 12 hedefin **12/12 HTTP 200**, `<title>` ve `<h1>` var, `rel=canonical` ve EN dil işareti HTML'de mevcut. Bu kanıt, silinmiş orijinal içeriğin tam eşdeğerliği değildir.
4. EN RSS onarım hedefi: WordPress bağlı site üzerinden 8/8 postun **publish**, 1/1 kategorinin mevcut ve `arastirmalar-en` slug ile **id 786982547**, 9 ilgili HTML'de bozuk RSS duyurusu var (11 Kasım kanıtından). Tarihsel kaynak `ai-english-before.php` içinde `oldies_ai_resolve_english_request` / `$vars['pagename']=$target` görülüyor, ancak **mevcut canlı tema kaynak dosyası/hash'i okunmuş değil**.
5. **ÖNEMLİ RİSK:** Canlı siteye salt-okunur `GET` ile denenen `/?feed=rss2&p=4877&withcomments=1&lang=en`, `/?feed=rss2&p=4877&withcomments=1` ve `/?feed=rss2&cat=786982547&lang=en` **HTTP 404**; buna karşılık `/feed/` **200 ve geçerli RSS XML**. Dolayısıyla 9 EN feed için önerilen query-vars/priority-6 yöntemi izole testte geçse de **gerçek WordPress'te çalışacağı kanıtlanmadı**. FEEDS flag **AÇILMASIN**; WP gerçek route/staging testi gerekiyor.
6. Lionel Richie: WP TR #4261 **publish**, EN #4974 **draft**; canlı TR HTML'de `/en/?p=4974` bağı **header içindeki EN dil seçicisine** ait; `<head>` içinde `rel=alternate hreflang=en` sızıntısı olarak kanıtlanmadı. Bu pakette Lionel yayını veya dil bağlantısı değişikliği yok.

## QA KARARI VE DEVİR

| Alt iş | Teknik QA | Canlı kararı |
|---|---|---|
| 16 exact 301 / 12 hedef | Yerel PHP test ve 12 canlı hedef kontrolü olumlu; eski içerik eşdeğerliği ve site aktif redirect çakışmaları ayrıca teyit | **ŞARTLI ADAY** — bağımsız WATCHDOG + kurucu canlı onayı olmadan AÇMA |
| 9 EN feed | Kaynak hipotezi ve offline test olumlu; doğrudan WP RSS sorguları 404 — **mevcut düzeltme doğrulanmadı** | **BLOKE (FEEDS OFF)**; gerçek site kaynak sürümü ve staging testine dön |
| 8 özel URL | GSC triage / bilinçli joker 404 koruması | İçerik/link kaynak kararı dışında otomatik değişiklik yok |

## BEKLEYEN — SORUMLU / İLK EYLEM

**WORK MASTER / site operatörü:** Kurulu `oldies-radyo-1950s-theme` (Oldies Radyo v7.3.7.1) kaynak fonksiyonlarının gerçek sürüm/hash'ini, 301 etkin mekanizma çakışmalarını ve 9 feed için `WP_Query` sorgu sonucunu staging ya da izinli dar testle doğrulasın. Yalnız gerekli ve çalıştığı kanıtlanan alt paketi canlıya almayı önersin.

**WORK WATCHDOG:** Bu kodun doğrudan değişiklik diff'i, 16 redirect eşdeğerliği, 9 feed regresyon riski, geri dönüş (iki flag kapalı / plugin disable), güvenlik ve aktif sitede öncesi-sonrası kontrolünü **ayrı oturum kimliğiyle** doğrulasın. Bu dosya WATCHDOG kabulü değildir.

**Kurucu:** Kritik canlı uygulama için mevcut onay kaydı varsa onu kullan, yoksa tek somut dar canlı onay paketiyle karar sor. Bu kullanıcıya teknik uygulama ödevi verilmesi değildir.

**GOOGLE:** WordPress onarımı/testi ve gerekli onaylar tamamlanmadan yeniden doğrulama başlatma. GSC 404 listesi tümüyle 301 yapılacak bir görev değil; kasıtlı kaldırılmış adresler meşru 404 kalabilir.

**Korunan:** 93 eski doğru 301, mevcut TR/EN yayın, haber taslakları, Polylang, CMS eklentileri/tema, WordPress canlı kodu, Google Search Console işlemleri ve sıfır ek maliyet.
