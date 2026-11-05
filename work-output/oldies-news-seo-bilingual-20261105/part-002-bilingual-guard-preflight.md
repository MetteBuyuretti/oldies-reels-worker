# PART-002 ÖN KONTROL | News Guard sürüm provenance ve SEO kaynak ayrımı

**Tarih:** 05.11.2026 | 07:20 TSİ (UTC+3)  
**Statü:** KISMİ / SALT-OKUNUR; Paket B henüz bitmedi, canlı onarım YOK.  
**Görev:** `oldies-news-seo-bilingual-20261105` / Issue #41.

## GERÇEKLEŞEN

- WordPress.com üzerinden **canlı bağlı site** `oldiesradyo.com` için `wpcom_plugin_list` salt-okunur kontrolü yapıldı (Atomic site, blog ID 14144069). İlgili aktif eklentiler: **Oldies Radyo TR→EN News Guard 1.0.4**; **Polylang 3.9.1**; **Oldies Polylang MCP Helper 1.3.0**; **Oldies Site Integrity 0.2.1**; **Site Kit by Google 1.187.0**; **Jetpack 16.4**; ayrıca **Header Footer Code Manager 1.1.46**. Bu sürümler 05.11 tarihli canlı bağlı WordPress envanterinde doğrulandı.
- Bilgisayardaki tarihsel, salt-okunur dosya: `C:\Users\METE\Documents\Oldies-AI-Calismalari\Arsiv\Oldies-System-Archive\2026-10-06-cleanup\Downloads-Dev-Artifacts\oldies-tr-en-news-guard-v103-package\oldies-tr-en-news-guard\oldies-tr-en-news-guard.php` **v1.0.3** sürümüdür; **kurulu v1.0.4 değildir**.
- **Yalnız v1.0.3 kaynağında görülen akış:** `transition_post_status` ile yayımlanmış TR haber tetikleme; kategori slugs `muzik-haberleri` ve `yeni-muzik-haberleri`; `pll_get_post('en')` ve ilişki meta alanlarıyla önce mevcut EN çiftini arama; transient lock + `wp_next_scheduled` koruması; 15 sn sonra tekli translate event ve imzalı loopback; günde iki kez safety scan, pass başına en çok 10 eksik; İngilizce çeviri **taslak** olarak `wp_insert_post(post_status=draft)` ile açılır, Polylang/meta bağlantısı kurulur; hata meta/option kaydı tutulur. Bu akış **v1.0.4'e aynen aktarılmış sayılamaz**.
- Canlı eklenti açıklamasında **v1.0.4 için** `Automatically creates, pairs and publishes English versions ...` yazıyor; bu, tarihsel v1.0.3'ün *yalnız taslak* davranışından önemlice farklı. V1.0.4 kodu/logu okunmadığı için yayın kapısının, retry ve yarış koşulu idempotency uygulamasının ayrıntıları **DOĞRULANMADI**.
- PART-001'in canlı HTML kanıtı 20/20 çift description ve 20/20 iki JSON-LD bloğu; Bowie TR'de blokların her ikisinde `Article` var. En az bir description, HTML'de `<!-- Oldies Radyo SEO fallback v3.5 -->` yorumuna bitişik; diğerinin kesin kaynak hook'u **belirsiz**. Eklenti kapatılarak test yapılmadı.
- Canlı `news-sitemap.xml` XML parse kontrolünde Bowie TR ve EN `news:title` değerlerinde XML çözüldükten sonra bile **`&#039;` literal metin olarak kalıyor** (`&amp;#039;` çift entity). URL ve başlıklar indeks bildirimi sinyali olabilir fakat Google indeks kanıtı değildir.

## BEKLEYEN / RİSK

1. **Aktif v1.0.4 PHP kaynağı / kendi hata-kuyruk logları** yetkili bağlantıdan görülmedi: eski v1.0.3'ü canlıya kurmak veya kopyalamak YASAK.
2. Çift meta description ve çift `Article` gerçek canlı kusurdur; hangisinin otorite olacağı canlı hook/Jetpack/SEO fallback/HFCM kaynağı görülmeden seçilemez. Plugin/tema değiştirme YOK.
3. GSC Wizard yalnız salt-okunur çağrıda `payment_required` döndü. Ücretli servis başlatılmadı; Site Kit kurulumu Google URL inspection kanıtı değildir.
4. 1 Ekim sonrası haberlerin editoryal içerik/alt/metin ve gerçekten ilgili dahili bağları sistematik içerik düzeyinde henüz 20/20 kontrol edilmedi.

## PLANLANAN — STAGING / FIXTURE

- V1.0.4 **gerçek kaynak sürümü** yalnız yetkili salt-okunur yöntemle açılabilirse tetikleme/idempotency/dil sınırları için test tablosu çıkar: yayımlanan TR haber → EN yok → tek görev; EN önceden var → sıfır yeni yazı; eşzamanlı iki tetikleme → en fazla tek EN; 429/timeout → görünür hata ve sınırlı tekrar; yanlış kategori → hayır; başka dil → hayır; geri dönüş → çift kaybolmaz.
- SEO çıkışında iki açıklamayı/iki Article graph'ı izole etmek için **mevcut canlı çıktıyı değiştirmeyen fixture** hazırlanacak. Canonical/hreflang 20/20 doğru olduğundan koruma regresyonları zorunlu.
- News sitemap XML entity testini bağımsız vaka olarak ekle: başlıkta kesme işareti son parse sonrasında `&#039;` kalmamalı; telif, haber içeriği veya slug değiştirilmemeli.
- **Uygulama izni kapısı:** Gerekli WATCHDOG ve kurucu onayı olmadan canlı eklenti, tema, SEO snippets, sitemap, otomatik yayın veya bülten ayarı değiştirilmeyecek.

**Durum:** Paket B başlandı, kaynak provenance okuması mevcut; aktif v1.0.4 kod/çalışma-logu görülmeden Paket B tamamlandığı iddia edilmez.