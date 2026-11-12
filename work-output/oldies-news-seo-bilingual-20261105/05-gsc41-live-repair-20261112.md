# OLDIES RADYO — #41 Canlı 404 Onarım Sonuç Raporu
**12 Kasım 2026 | 03:57 TSİ (UTC+3)**  
**Sorumlu:** Ana Kumanda mevcut oturum, uygulama operatörü · **Operasyon sahibi:** WORK MASTER (ayrı oturumda teslim kabulü kanıtlanmadı)  
**Durum:** **26/33 URL CANLIDA ONARILDI + TEST EDİLDİ** · **7 URL İÇİN KASITLI / GEÇERLİ 404 KORUNUYOR** · **GOOGLE YENİ DOĞRULAMA BAŞLATILMADI**

## KURUCU İÇİN KISA RAPOR

- **GERÇEKLEŞEN:** `oldiesradyo.com` WordPress'e **iki dar kapsamlı, kaldırılabilir eklenti** yüklendi ve etkinleştirildi. İlk eklenti 16 tarihsel 1950'ler slugını ve içerik eşdeğeri bulunan 2015 #303 arşiv aliasını düzeltir: **17/17 kaynak → tek adım HTTP 301 → hedef HTTP 200** (12.11 tam yeniden canlı regresyon testi).
- **GERÇEKLEŞEN:** Yalnız 8 İngilizce yayınlanmış haberin yorum RSS'si ve 1 İngilizce kategori RSS'si onarıldı: **9/9 HTTP 200 + tam XML parse**; 8 RSS kanal başlığı ilgili İngilizce haberle eşleşti, kategori kanalı 9 öğe içeriyor.
- **GERÇEKLEŞEN:** Ana sayfa 200, kök TR RSS `/feed/` 200/XML, iki tarihsel 301 örneği ve mevcut 1950'ler sayfaları çalışıyor. WordPress yeni plugin listesinde her ikisi de `active`.
- **BEKLEYEN:** 7 kalan URL: 3 güvenlik/joker kalıbı (denenmez/yönlendirilmez), 2 taslak içeriğe karşılık gelen eski URL (#77 ve #4974, yayımlanmaz), 2 hatalı `/oldiesradyo.com...` yolu (kör 301 yok; kaynak varsa kaldırma). Lionel TR header EN seçicisi halen `/en/?p=4974` taslağa işaret ediyor; bu ayrı kaynak düzeltmesi gerektirir. Hiçbiri rastgele homepage'e yönlendirilmedi.
- **GOOGLE:** GSC'de yeni Validation başlatılmadı. Bilerek 404 korunan 7 URI nedeniyle "33/33 Google PASS" iddiası uygun değildir. Google'ın 26 düzeltilmiş URL'yi yeniden taraması ve kalanların meşru 404 olarak değerlendirilmesi sonraki bağımlılıktır.

## UYGULANAN DEĞİŞİKLİKLER

| Eklenti | Canlı sürüm | Durum | Etki |
|---|---|---|---|
| `oldies-gsc41-exact-redirects` | **1.0.1** | **ACTIVE** | Tam 16 eski 1950 slug + 1 yayımlanmış 2015 arşiv aliası, exact 301 |
| `oldies-gsc41-en-feed-repair` | **0.1.0** | **ACTIVE** | Tam 8 EN comment RSS + 1 EN category RSS; request filtresi priority 999 |
 
**Yüklenen ZIP SHA-256:**
- `oldies-gsc41-exact-redirects-v1.0.1.zip`: `b13a7f340607005ecf7f67721dc5f79a3474c2b4daf129d9ded1999eaa6dd585`
- `oldies-gsc41-en-feed-repair.zip`: `36f854d2c5785090111b56341ba71577dfe5cd3b4e8f1bba3f06ebbe0e775cc8`

**Geri alma:** Her eklenti bağımsız olarak WP Plugins listesinden **deactivate** edilir. Ana site DB tabloları, 93 önceki yönlendirme, şablonlar, içerik, yayınlar veya Polylang ayarları değiştirilmedi. Jetpack Backup `state=active`, önceki yedek başarılı; ancak restore testi yapılmadı. Geri alma gerektirmedi.

## KANITLAR VE SINIRLAR

- [GSC kaynak 129 URL](404-gsc-validation-20261111.csv), [asıl 33 başarısız URL](404-gsc-failed-triage-20261111.csv).
- [12 Kasım 33 URL son karar matrisi](404-gsc-resolution-20261112.csv): **17 exact 301**, **9 RSS**, **7 404 korunuyor**.
- Canlı HTTP ölçümü: 17/17 redirect **301 exact Location → GET target 200**. Her 1950 hedefi farklı kodlu 12 canonical arasında; 2015 arşivinde WordPress yayımlanmış #303, eski /en alias 404 iken yeni 301.
- RSS ölçümü: 9/9 HTTP200 ve RSS2 XML; 8 comment kanalı doğru yazı başlığı/URL'si, kategori 9 item. İlk XML örneklemesindeki `unclosed CDATA` uyarısı, içeriği 90kB ile kesmekten kaynaklandı; kategori feed'in **310437 bayt tam** XML cevabı yeniden indirildi ve başarıyla parse edildi.
- Kök `/feed/` RSS ve ana sayfa HTTP200, iki eski 301 örneği korunmuş durumda.
- 7 URL'nin 3'ü wildcard/güvenlik patternidir; bot yollarının gerçek 404 dönmesi kabul edilebilir. WP #77 ve EN #4974 **draft** (WordPress canlı kaydı); otomatik yayın yok. Hatalı alan adı tekrarı için WordPress içeriğinde 37 eşleşen arama sonucu incelendi; bu örnekte protokolsüz /oldiesradyo.com... URL kullanımına rastlanmadı, ancak bütün kaynaklar tüketildi iddiası yok.
- 7 URL'yi GSC doğrulamasında "PASS" saymak için kanıt yok. Genel site SEO kapsamı (TR/EN News Guard, çift meta, JSON-LD, sitemap, Google indeks) #41'de **ayrı açık kalite alt işleri** olarak sürüyor.
- Bu operatörün QA'sı ve canlı GET/HTTP kanıtı vardır; **ayrı WORK WATCHDOG oturumunun bağımsız kabulü olmadığı** için resmî WATCHDOG PASS ileri sürülmez. Anayasa V3.0 uyarınca sonradan bağımsız denetim istenir.

## SONRAKİ İŞ (TEKRAR ONARIM YOK)

1. WORK MASTER / WATCHDOG: 26 düzeltilmiş URL'nin kanıtını ve eklenti sürümlerini ortak kayıttan oku; yeniden plugin kurma veya 93 tarihsel 301'e dokunma.
2. Lionel Richie yayımlanmış TR #4261 üst navigasyonda EN taslak #4974 bağlantısını kaldıracak **yerel şablon düzeltmesini** güncel tema kodu üzerinden ayrıca QA et; taslak yayımlama yetkisi yok.
3. İki `/oldiesradyo.com...` hatalı yolun sitemap/iç bağlantı/log kökenini teyit et; gerçek kaynak bulunmazsa 404 kalsın. #77 ve #4974 taslak, 3 güvenlik probe mevcut 404 olarak kalır.
4. GSC'de 26 düzeltilmiş URL'nin yeni crawl sonucu gözlensin. 7 beklenen 404 ayıklanmadan toplu “Start New Validation” butonuna basıp aynı başarısızlığı tekrar üretme. Gereken tek ek karar, kalıcı arşiv/EN yayın içeriğinin editoryal onayıdır.

**Bu belgenin anlamı:** 404 kaynak listesinde teknik olarak düzeltilebilen 26 URL sitede gerçekten düzeltildi. GSC raporunun tümü henüz otomatik başarılı sayılamaz ve #41 diğer geniş SEO alt işleri nedeniyle kapatılmış sayılmaz.
