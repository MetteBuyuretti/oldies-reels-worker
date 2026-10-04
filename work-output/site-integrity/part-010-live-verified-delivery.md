# Site Integrity checkpoint010 — installed and verified, 2026-10-04

**DÜZELTİLDİ**

- Site Integrity v 0.2.1 canlıda kuruldu ve etkinleştirildi.
- Araştırmalar: doğru dil+kategori sorgusu, iki pin+son yayınlar.4308/4457/4274 ve EN karşılıkları görselli kart olarak doğrulandı.
- TR/EN araştırma arşivleri 200; EN eski sayfa yönlendirmesi çakışması giderildi. EN haber sorgusu doğru kategoriye bağlandı.
-4300/4286/4343 kategori eşleşmeleri düzeltildi; gövde/başlık/alıntı değişmedi.
-4300/4301 featured image, HTTP 200 ve gerçek ana sayfa haber kartıyla doğrulandı.

**OTOMATİK KORUMA EKLENDİ**

Yayın kapısı, yayın sonrası frontend kontrolü, menü master kilidi, her gece 03:30 İstanbul tam tarama, Ana Kumanda paneli ve güvenli inceleme kuyruğu aktif.50 PHP testi geçti. Canlı yazmasız filtre testi: yayın 422, menü ekleme engellendi. Kaynak yedekleri, rollback ve GitHub checkpoint kayıtları saklandı. WP-Cron gecikirse bir sonraki site isteğinde çalışır.

**BULUNAN DİĞER HATALAR**

|Bulgu|Kayıt|
|---|---:|
|Görselsiz/kategorisiz eski yazı|13|
|TR/EN karşılığı eksik içerik|61|
|Editör gövdesi boş/yalnız başlık işareti|13|
|Eksik karşı dil gövdesi işareti|6|
|Karşılığı henüz yayında olmayan kayıt|5|
|Diğer kategori eşleşme uyuşmazlığı|5|
|Şablon ön yüz incelemesi bekleyen sayfa|568|
|Navigasyon incelemesi bekleyen sayfa|40|

Sayılar çakışabilir.568 sayfa bozuk ilan edilmedi; tema gerçek içerik üretebilir. Her kayıt kaynak/şablon ve gerçek karşı dil gövdesiyle incelenecek; otomatik toplu gövde değişikliği yok.

TR/EN Canlı Dinle sayfalarında oynatıcı/oynat düğmesi görülmedi; ayrı kontrol gerekiyor. Stream ayarları değiştirilmedi. Google indeks durumu doğrulanmadı; öncelikli URL'ler 200 ve noindex taşımıyor.

**KULLANICI ONAYI GEREKENLER**

Aynı konum ve URL'lerde mevcut Hizmetler→DJ & Seslendirme Hizmetleri; Services→DJ & Voice Services. Yeni üst menü maddesi yok. Canlı adlar mevcut halleriyle kilitli, etiket değişikliği onay bekliyor.

**SITE INTEGRITY**

Koruma AKTİF; menü LOCKED / HEALTHY. Öncelikli yayınlar 8/8 sağlıklı. Yapısal kontrol%47,4:1160 kaydın 550'si bütün kuralları karşılıyor,610 kayıt inceleme kuyruğunda. Bu tüm ön yüzün sağlık yüzdesi değildir.

Son tam tarama 4 Ekim 2026 03:16:15 İstanbul. Sonraki günlük cron 5 Ekim 2026 03:30 İstanbul.


Evidence: native-audit-final.json; final-frontend-checks-20261004.json (21 bounded anonymous GETs); live-guard-probe.json; targeted category backup/after comparison; active dashboard screenshot; PHP8.3.33 syntax lint and50 passing behavior checks. No expected module card is inferred from a script string or generic footer link. News4300/4301 were verified inside real hero/news cards after the final core update. Menus match the exact pre-change master on TR/EN homepage, Features and research archives.

Delivery persisted: Oldies_Site_Integrity_20261003.zip, existing artifact ID libfile_725110e0678c8191b803ddcbd22a4006, version4,1147863bytes. Includes current install ZIP, source/config backups and hashes, tested v0.2.1 source, final audit,610-record safe editorial queue,40 navigation-review entries, reports and screenshot. Does not contain credentials or a full database snapshot.

Rollback: deactivate this isolated plugin; original theme/HFCM/other plugin source was left intact. Restore the backed-up category arrays for4300/4286/4343 if needed. Body/title/excerpt reloads compare exactly. Baseline/report options survive deactivation.

Remaining editorial queue is explicit and does not auto-change bodies. Service-label preview is recorded, same URLs/order and no new top-level item; owner approval required. Radio pages expose no visible audio/play control in observed DOM; separate review, no playback or stream mutation. WordPress-level guards do not govern direct host filesystem/DB writes or owner deactivation.

Status: authorized system installation and validation completed; no deployment blocker. Do not reinstall on reconnect. Resume future editorial work from queue and only apply approved menu changes after fresh backup/preview.
