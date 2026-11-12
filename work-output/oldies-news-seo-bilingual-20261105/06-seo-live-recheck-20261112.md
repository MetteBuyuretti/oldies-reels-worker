# #41 — 12 Kasım 2026 Canlı SEO kontrolü (salt-okunur)
**İş:** oldies-news-seo-bilingual-20261105
**Operatör:** Oldies Master Kumanda (Work olmayan oturum)
**Kapsam:** Mevcut #41; yeni proje/issue yok.

## Bağımsız doğrulanan
- WordPress bağlı site eklenti envanteri: `oldies-gsc41-exact-redirects` **v1.0.1 active**, `oldies-gsc41-en-feed-repair` **v0.1.0 active**, News Guard **1.0.4 active**, Polylang **3.9.2 active**, Site Integrity **0.2.1 active**. WP aktivite kaydı 12 Kasım kurulum/aktivasyon olaylarıyla tutarlı.
- Jetpack Backup: **active**; en son 11 Kasım yedek denemesi `finished`, `last_attempt_failed=false`. `restore_preflight_status=null`: restore kabulü değil.
- Gerçek canlı GET HTML, Bowie TR #4882: **2× meta[name=description]**, **2× Article @type**. `<!-- Oldies Radyo SEO fallback v3.5 -->` görüldü. İlk description fallback yakınında, ikinci description çok daha aşağıda head içinde. İki açıklama bu örnekte aynı; diğer sayfalarda farklılaşabiliyor. İki Article üreticisinin kod kaynağı kesinleştirilmedi.
- Bowie EN #4883: **2× meta[name=description]**, **1× Article @type**; meta açıklamaları farklı uzunlukta (ilkinde ellipsis var), bu yalnız kozmetik değil.
- Lionel Richie TR #4261: **2× meta[name=description]**, **2× Article @type**. Sayfanın header EN dil seçicisi hâlâ `https://oldiesradyo.com/en/?p=4974` adresini sunuyor. WordPress kayıtlarında #4261 **publish**, EN #4974 **draft**. Head hreflang-en sızıntısı diye yanlış sınıflama yapılmaz; sorun header dil seçicisindedir.
- `news-sitemap.xml` okunabilir. Haber sitemap'inde eski çift entity bulgusunun mevcut kayıtta devam ettiği **yeniden ispatlanmadı**; değişiklik yapılmadı.

## Yanlış DONE sayılmaması gerekenler
- #41 03:57 TSİ onarım raporundaki **17 exact 301 + 9 RSS = 26/33** canlı QA sonucu geçerlidir; bu kontrol sırasında 26 URL için yeniden tam regresyon yapılmadı. Önceki başarıyı silme, yeniden plugin kurma, tarihsel 93 redirect'e dokunma.
- 7 meşru 404 (3 wildcard security probe + 2 draft + 2 malformed path) otomatik ana sayfaya yönlendirilmez.
- Genel SEO kalite kapısı, Guard v1.0.4 idempotency/retry, tek meta/head üreticisi, Article graph, Polylang draft link ve Search Console indeks kabulü **tamamlanmadı**.
- Google toplu Validate Fix çalıştırılmadı, yeni ücretli üyelik açılmadı, canlı WordPress kodu değiştirilmedi.

## Tek seferde çözüm için teknik uygulama kapısı
1. **Kurulu v7.3.7.1 tema ve News Guard 1.0.4 güncel PHP kaynağı** (eski arşiv kaynaklarıyla değil) üzerinden v3.5 fallback output ve ikinci meta/schema üreten WordPress hook/callback'i tam tespit et.
2. Tek açıklama üreten, mevcut canonical/hreflang/OG/Twitter meta değerlerini koruyan **dar, geri alınabilir değişiklik** hazırla. Article graph'ları semantik karşılaştırmadan birini körlemesine silme; gerçek çoklu Article yalnızca doğrulanmış sayfalarda giderilsin.
3. Header EN dil seçicisi, hedef EN kayıt `publish` değilse taslağa link üretmesin. #4974'ü kendiliğinden yayımlama veya native Polylang eşleşmesini bozma.
4. Güncel News Guard kaynak/log üzerinden eşzamanlı tetik, yinelenen EN üretimi, sınırlı retry ve yayın davranışı kontrol; iki TR/EN staging/draft pilot. Mevcut sitemap title double-encoding iddiasını yeni XML parse ile doğrula.
5. Ayrı WATCHDOG kalite kabulü + canlı kod erişimi/geri alma güvencesi sonrası tek kontrollü uygulama ve TR/EN HTML + RSS + redirect + sitemap regresyonu. GSC'de 26 onarılmış URL'nin tarama/indeks bilgisi ayrıca ölçülsün.
6. İş kapanışı yalnız **canlı QA + ayrı kabul** sonrası; bu belge inceleme checkpoint'idir, DONE değildir.

**İlk blokaj:** Bu oturumun WordPress bağlı araçları etkin eklenti sürümlerini ve içerikleri okuyabiliyor, ancak kurulu PHP tema/plugin kaynaklarını doğrudan okumak veya satır düzeyinde güvenli düzenlemek için yetkili kaynak erişimi sunmuyor. Bu nedenle kör yeni plugin/HTML çıktısı tamponlama/tema hack'i kurulmadı.
