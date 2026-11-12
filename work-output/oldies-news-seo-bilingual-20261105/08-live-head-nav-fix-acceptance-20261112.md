# #41 — Canlı SEO head + dil seçici onarım QA
**Tarih:** 12 Kasım 2026
**Operatör:** Oldies Master Kumanda (Work olmayan oturum)
**Durum:** Kapsamlı SEO head + Lionel bağlantı alt paketi **CANLIDA / ÖRNEKLEMLE TEST EDİLDİ**. Genel #41/GSC indeks henüz kapanmadı.

## Uygulanan tek düzeltme eklentisi
- **Oldies Radyo #41 Head and Draft Language Link Repair** (plugin slug `oldies-seo41-head-nav-fix`) **v0.1.2, ACTIVE**.
- Kaynak: [07-oldies-seo41-head-nav-fix-candidate.php](07-oldies-seo41-head-nav-fix-candidate.php). Aracın native WordPress plugin-upload kanalıyla aynı kapsam altında kuruldu, önce 0.1.0 pilot, ardından 0.1.1 ve 0.1.2 dar revizyonları yapıldı.
- PHP `-l` syntax PASS; son yerel PHP fixture **13/13 PASS**, idempotence, canonical/OG korunması, tek meta açıklama, Lionel draft link ayıklama, başka postlara dokunmama, olmayan HEAD/RSS bozulmaması. Bu testler kurulu WP'nin bütün yol türlerinin garantisi değildir.
- Kapsam: WordPress frontend tekil içerik (post/page), ana sayfa, kategori ve etiket arşivlerinde `meta name=description` tekrarlarını filtreler. Aynı sayfada birden fazla varsa en uzun mevcut açıklama korunur; geri kalan head etiketleri, Polylang ilişkileri, içerik, yayın, slug, feed ve redirect mekanizmaları değiştirilmez.
- Yalnız TR Lionel #4261 için header EN seçicisindeki `https://oldiesradyo.com/en/?p=4974` (EN draft) linki görünür HTML'den kaldırıldı. EN #4974 yayımlanmadı, dil bağları yeniden yazılmadı.
- **Rollback:** WordPress Plugins ekranından yalnız `oldies-seo41-head-nav-fix` eklentisini deactivate; veritabanı/içerik/tema değiştirilmedi. Bu frontend çıktı filtresidir; alttaki iki metadata üreticisinin PHP kök kaynağı değiştirilmedi.

## Canlı GET regresyonu
Son v0.1.2 kurulu iken farklı cache-bypass query'leriyle doğrulanan URL örneklemi:
| URL | SEO description | Canonical | Ek |
|---|---|---|---|
| Anasayfa / | **1** | **1** | Oldies Radyo ayrıntılı tanıtımı korundu |
| /1950ler/bo-diddley/ | **1** | **1** | Daha uzun Bo Diddley'e özel açıklama korundu; kısa genel fallback çıkarıldı |
| Bowie TR #4882 | **1** | **1** | TR açıklaması korundu |
| Bowie EN #4883 | **1** | **1** | Eksiksiz EN açıklaması korundu |
| Lionel TR #4261 | **1** | **1** | Hatalı /en/?p=4974 header linki yok; #4974 halen draft |

TR/EN haber örneklerinde hreflang işaretleri gözlendi. Daha önceki v0.1.1 kontrolünde kök `/feed/` RSS çıktı verdi; v0.1.2 sürümünde RSS filtreden muaf; v0.1.2 sonrası doğrudan kök RSS tekrar edilmedi. EN post comment RSS örneği yeni revizyonda XML içerikle döndü. 17 301'in tamamı bu yeni operatör tarafından tekrar test edilmedi, önceki 12 Kasım 17/17 canlı QA kayıtları korunuyor.

## Polylang bağımsız okuma — 10/10 eşleşme, çift yön
05 Kasım auditindeki 10 TR/EN aday çiftinin tamamı **bağlı sitenin native Polylang API'sından** salt-okunur tek tek incelendi:
`4882↔4883, 4878↔4879, 4876↔4877, 4874↔4875, 4872↔4873, 4817↔4818, 4805↔4806, 4300↔4301, 4133↔4258, 2240↔2241`.
**10/10 TR→EN ve 10/10 EN→TR ilişkisi** `publish` + doğru `language` + karşılık `translations` kimliği ile PASS.
Bu, News Guard'ın yeni görevlerde gelecekte her zaman %100 tekrar koruduğunun kanıtı değildir; v1.0.4 çalışan PHP log/kodu bağımsız okunmadı.

## Açık kalan gerçek bağımlılıklar (bu başarıyı geri almaz)
1. Google Search Console, 26 onarılan kaynak URL'nin yeniden tarama/indeks durumunu henüz kanıtlamadı. 7 başka URL, önceki sınıflandırmadaki meşru 404 (3 security/wildcard, 2 draft, 2 malformed). 7 404 dururken kör toplu Validate Fix yapılmadı.
2. Bowie TR / Lionel TR sayfalarında iki ayrı `Article` JSON-LD nesnesi mevcut; kaynağın anlamsal çakışması ve zengin sonuç geçerliliği doğrulanmadan körlemesine script silinmedi. Google bir sayfada birden fazla yapılandırılmış öğeyi destekler, bu sayı tek başına hata değildir.
3. News Guard v1.0.4 retry/idempotency gerçek kaynak/log testi, sonraki iki yeni staging/draft pilot ve bağımsız WORK WATCHDOG resmî kabulü ayrı P1/P2 kapsamı olarak açık.
4. Metadata kaynak kodları tema/plugin katmanında halen üretiliyor; çıktı filtresi görünür HTML hatasını düzeltiyor, kaynak üreticiyi kaldırmadı. Bu nedenle bakım notu korunmalı.

**Değişmedi:** GSC Validate Fix, Polylang çiftleri, newsletter, içerik yayını, eski 93 301, #41 canlı onarım ilk iki eklentisi, Etsy, Jingle, Reels, Pinterest, ücretli servisler.

**Kanıt zamanı:** 2026-11-12T02:00:13.289Z
