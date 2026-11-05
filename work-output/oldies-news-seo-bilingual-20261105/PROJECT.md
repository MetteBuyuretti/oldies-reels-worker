# OLDIES RADYO — TR/EN HABER YAYIN KALİTESİ + SEO + GOOGLE DİZİNİ | MASTER PROJE TALİMATI
**Görev ID:** `oldies-news-seo-bilingual-20261105`  
**Tarih:** 05.11.2026 (TSİ)  
**Komuta / hesap veren:** WORK MASTER  
**Uygulayıcı:** Master'ın yetki ve erişimini doğruladığı teknik operatör (Codex/Work/WordPress); tek kaynak yazarı  
**Bağımsız kabul:** WORK WATCHDOG / ayrı QA; kurucunun onayı canlıya alma kapısı  
**İlk statü:** QUEUED — devredilecek, otomatik uyanma veya gerçek iş kabulü henüz kanıtlanmadı.  
**Hedef alan:** https://oldiesradyo.com (TR) ve https://oldiesradyo.com/en/ (EN). Ayrı bir İngilizce domaini yok.

## 0. Emrin özü
Sitemize giren **her uygun yeni müzik haberi**, doğrulanmış Türkçe ve doğal/özgün İngilizce yayın sürümlerine **tekrar, atlama, yanlış dil/yanlış bağlantı olmadan** dönüşmeli. Her iki sürüm anlaşılır başlık, doğru kategoriler, temiz slug, kısa özgün özet/meta açıklaması, uygun görsel/alt, sınırlı anlamlı tag, kaynak gösterimi, dahili bağlantı, doğru Polylang ilişkisi ve crawl/index sinyalleriyle kaydedilmeli. Google'a sunulmuş olmak Google'da indekslendi anlamına gelmez: bunu Search Console verisiyle ayır.

## 1. Kanıtlanmış başlangıç — 05.11.2026
- WordPress: `Oldies Radyo TR→EN News Guard 1.0.4`, `Polylang 3.9.1`, `Oldies Polylang MCP Helper 1.3.0`, `Oldies Site Integrity 0.2.1`, `Site Kit by Google 1.187.0` aktif. Aktif eklenti, bütün otomatik akışın %100 başarılı çalıştığı kanıtı değildir.
- Son tarihli 13 TR yazının 13 EN karşılığı WordPress'te yayımlanmış; 13 çiftin tamamı Polylang ilişkileri üzerinden ayrı ayrı doğrulandı. Örnekler: Bowie TR #4882 ↔ EN #4883, Fleetwood Mac #4878 ↔ #4879, Rolling Stones #4876 ↔ #4877.
- 02.10–04.11 aralığındaki 26 yayın kaydında tag listesi boş, fakat 26/26 featured image ve excerpt mevcut.
- Altı yeni haber örneğinde `advanced_seo_description` ve `jetpack_seo_html_title` özel alanları boş; `jetpack_seo_noindex=false`. Sonuç: özel SEO alanı boş; sayfanın HTML head'inde SEO meta üretimi ayrıca **canlı HTML ile doğrulanmalı**; boş alan tek başına SEO başarısızlığının tamamı değildir.
- Bowie TR #4882 içeriğinde 4 H2, 2 dış bağlantı, **0 iç bağlantı**; site içi ilişkili haber bağlantısı kontrolü gerekiyor.
- GSC Wizard üçüncü taraf denemesi bitti / `payment_required`; **Google Search Console hesabının silindiği anlamına gelmiyor**. `Site Kit` aktif, fakat GSC mülkiyet ve fiilî sayfa indeks durumu bu denetimde doğrulanamadı.
- `control-center/work-state.json`: `tr-en-parity-20261004` hâlen **in_progress** — önceki kayıt 59 eşleşmemiş içerik ve içerik kalitesi kuyruğunu belirtiyor. Bu sayı güncel canlının kesin sayısı değildir. **Mevcut backlog görevini yeniden açma / üzerine paralel yazma.** `site-integrity-20261003` done; sistem denetimi kullanılacak.

## 2. Master'ın icra sırası — her paket 10–20 dk, checkpoint zorunlu
### Paket A — ENVANTER / KÖK NEDEN / DURUM (salt okunur)
1. `AGENTS.md`, `control-center/work-state.json`, `control-center/WORK_CONTINUITY_PROTOCOL.md`, mevcut `tr-en-parity-20261004`, `site-integrity-20261003`, WordPress Guard, Social News Automation, Polylang Helper ve Google Site Kit kurulumunu oku. Kaynak görülmediyse "görülmedi" diye kaydet.
2. Son 30 yeni haber çiftinin ID/URL/dil/Polylang eşleşmesi/çeviri kalitesi/başlık/excerpt/görsel/alt/meta/tag/kategori/slug/links/canonical/hreflang/noindex ve gerçek HTML head denetimini yap. 30 çifte ulaşılamazsa n örnek sayısını ve kapsamı raporla.
3. Şu uç noktaları ve durumlarını dışarıdan **salt okunur** doğrula: robots.txt, geçerli sitemap indeksleri, hem TR hem EN sitemap URL'leri, gerçek HTTP 200/redirect/canonical/hreflang, gerekirse NewsArticle structured data. URL uydurma; mevcut sitemap'i keşfet.
4. Site Kit'teki Google Search Console mülkiyet/erişim durumu ile sayfa dizini verisini **yetki içinde** doğrula; Google raporuna erişilemiyorsa `UNVERIFIED_GSC_ACCESS` olarak işaretle. Abonelik satın alma yok; GSC Wizard yoksa doğrudan ücretsiz Search Console kullanılabilir.

**Çıktı:** `work-output/oldies-news-seo-bilingual-20261105/part-001-audit.md` + örneklem CSV/JSON; doğru/eksik/kanıtsız ayrı; hata önceliği ve riskli değişiklikler.

### Paket B — YENİ HABER ÇİFTLEME KALİTE KAPISI (önce taslak/test)
1. TR→EN Guard'ın **hangi yazıları kapsadığını, hangi koşulda tetiklendiğini, başarısız/atlanan işi ve retry/idempotency davranışını** kaynak + log ile belirle. Eski backlog `tr-en-parity-20261004` sahibiyle sınır ayrımı yap.
2. Yeni uygun TR haber için EN eksikse otomatik tespit/iş kuyruğu ve güvenli yeniden deneme; karşılık varsa **ikinci İngilizce yazı oluşturmama**. Gecikme/çeviri hata kodunu görünür kıl.
3. Her iki yazının Polylang çeviri ilişkisi, dil URL'leri, doğal İngilizce metin, bozuk/boş içerik, dil karışması ve tarihler kontrolünden sonra yayına uygunluk kararı ver. Mevcut haberleri otomatik yeniden yayımlama yok.
4. Hiçbir değişiklik canlıya kurulmadan önce yerel/staging/draft testleri + regresyon raporu hazırlanmalı.

**Çıktı:** `part-002-bilingual-guard.md` + test-fixture/kanıt + gerekiyorsa geri alınabilir diff/draft PR; gerçek canlı kurulum ayrı onay kapısında.

### Paket C — SEO YAYIN ŞARTNAMESİ (TR VE EN BAĞIMSIZ)
1. H1 başlık, özgün dilde excerpt/meta description (yaklaşık 140–160 karakter hedefi, zorunlu uzunluk garantisi yok), açıklayıcı URL, tutarlı kategori, 0–6 **anlamlı** tag, H2 yapısı, lisanslı/dönem uyumlu görsel, benzersiz alt metin, en az bir **gerçekten ilgili ve mevcut** dahili bağlantı mümkün olduğunda, kaynak ve olay tarihi.
2. Teknik: HTML `title`, gerçek `meta name=description`, canonical self/istisna, karşılıklı `hreflang=tr/en` ve varsa x-default politika, robots noindex, sitemap'de indexlenebilir URL; eşdeğer içerik ve otomatik çeviri sürümlerinin doğru bağlanması. WordPress'te farklı SEO eklentisi kurulmasını varsayma; mevcut Jetpack/tema/Site Kit çıktılarını önce test et.
3. JSON-LD `Article`/`NewsArticle` gerekiyorsa tek, tutarlı şema; gerçek `datePublished`, `dateModified`, `author`, `publisher`, `image`; yanlış iddia / tarih / etiket yok. Google'da dizin garantisi verme.
4. SEO alanları boşsa post excerpt'ten güvenli fallback kullan; mevcut tema/Jetpack tarafından zaten meta üretiliyorsa **çift meta** oluşturma. Alt ve iç linklerde olmayan varlık uydurma.
5. 2 hazır haber çifti üzerinde kodsuz/draft veya staging pilot; eski bülten ayarı `email_content_format=excerpt` **korunacak**, testte aboneye e-posta gönderilmeyecek.

**Çıktı:** `part-003-seo-gate.md`, ölçülebilir otomatik preflight/test raporu, gerekiyorsa minimal diff, uygulanma/geri alma planı.

### Paket D — İNDEKS/ÖLÇÜM ve BAĞIMSIZ KABUL
1. Canlıya **kurucu onayı sonrası** dar geçiş; önce 2 pilot TR/EN çiftinde gerçek WordPress/HTML, sonra 5 doğal yeni yayın çiftinin regresyonu.
2. Her çifte: yayında TR+EN 200, birebir karşılıklı Polylang; tek canonical, karşılıklı hreflang, başlık/description/alt, kategori/ilgili bağlantı ve sitemap görünürlüğü denetlenmiş. Hata halinde fail-closed veya kuyruğa alma, veri kaybı/yinelenen yayın yok.
3. Google Search Console'da **sunulan URL** ve **dizinde URL** sonuçları ayrı kaydedilsin; erişim yoksa "Google indeks doğrulanmadı" yaz. Haftalık sayısal çıktı: TR/EN çiftleme %, SEO alan doluluk %, indekslenen yeni URL sayısı (yalnız GSC kanıtlı), organik tıklama/gösterim/CTR (kanıtlı dönem).
4. WORK WATCHDOG bağımsız QA; ardından Master somut raporla kurucuya kabul için sunar.

**Çıktı:** `part-004-acceptance.md` + kanıt URL'leri, rollback ve 1 haftalık takip planı. **DONE, yalnızca gerçek yayın sonrası kabul kanıtıyla.**

## 3. Başarı ölçütü / kırmızı çizgiler
- **İlk aşamada başarı:** denetim/plan ve 2 pilotun taslak veya staging güvenli testleri; **CANLIDA TAMAMLANDI** denmez.
- **Canlı kabul:** seçilmiş pilotlarda %100 çift/dil bağı, gerçek head/sitemap ve içerik kabulü; ilk doğal beş yeni haber için tekrar etmeyen yayın ve kayıt. Ulaşılamayan dış sistemler ayrı blocker.
- Eski içerikleri topluca değiştirme, arşiv silme/slug değişimi, toplu reindex isteği, yeni ücretli SEO servisi, yeni eklenti, plugin deactivation/update, mevcut WordPress otomasyonu/schedule, radyo, Etsy, Tumblr, Pinterest, Reels, bülten ayarları üzerinde onaysız değişiklik **YOK**.
- **Mevcut TR→EN geçmiş eksikleri göreviyle çakışma yok.** Bu yeni projenin alanı yeni haberler için kalite kapısı ve teknik SEO/Google ölçümü; geçmiş çeviri backlog'u ayrı kalır.
- `SAFE`: salt okunur audit, kanıt dokümanı, staging/draft kod önerisi, izole test.
- `NEEDS_APPROVAL`: canlı WordPress kodu/plugin/tema, otomatik haber yayını, menü/site haritası yeniden tasarımı, abonelik ayarları, maliyet, geniş çaplı toplu içerik değişikliği.
- Repo ve sistem sırları/anahtarları rapora veya issue yorumuna yazılmaz. Issue açılması Master'ın uyandığını / işi aldığını kanıtlamaz.

## 4. Master koordinasyon şartı
- Work Master görevi **alım teyidi** ile üstlenmeli: operatör, erişim, ilk iş paketi, kanıt yeri, blocker, sonraki checkpoint açıkça belirtilmeli. Görev ataması ile yetki var sayılmaz.
- Bu işin sonuçları `work-output/oldies-news-seo-bilingual-20261105/` altında tutulur. Her parça sonrası `control-center/work-state.json` görev girdisi güncellenir ve ilgili GitHub Issue'ya permalink/diff/test raporu düşülür.
- `#32` MASTER merkezine kısa devir kartı gönder; ayrı SEO issue'su yalnız bu yeni iş paketini izlesin. Mevcut #32 Reels/Jingle/Facebook çekirdeği yeniden açılmaz.
- İlk checkpoint yalnız **paket A (read-only)** olarak başlatılır; çözüm mimarisi kanıt geldikten sonra daraltılır.
