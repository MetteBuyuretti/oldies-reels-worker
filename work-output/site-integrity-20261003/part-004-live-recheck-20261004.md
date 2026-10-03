# Oldies Radyo — Site Integrity durum raporu

4 Ekim 2026, İstanbul · canlı kontroller 01:38

## DÜZELTİLDİ

- Önceki çalışmada EN Yunanistan (4343) ve EN rock yıldızları (4286) mevcut EN Araştırmalar kategorisine eklenmişti. Bu atamalar hâlâ doğru; aynı değişiklik tekrar yapılmadı.
- Referans 4308, 4457, 4274, 4300 ve EN karşılıklarının tamamı HTTP 200; görseller gerçek img etiketlerinde mevcut; Polylang çiftleri karşılıklı doğru.
- Hazır koruma kodunun v0.1.1 sürümünde frontend doğrulaması düzeltildi: yalnız Araştırmalar modülündeki kart kabul edilir; kart görseli ve dolu h3 başlığı aranır. Haberler bölümündeki bağlantı başarı sayılmaz.
- PHP 8.3.33 sözdizimi ve 29 davranış kontrolü başarılı; 7 JS senaryosu başarılı. Bunlar yerel aday kod testleridir, canlı kurulum testi değildir.

## OTOMATİK KORUMA EKLENDİ

Canlıda henüz eklenmedi. Yayın kapısı, mimari koruma, pin + kategori sorgusu, günlük tarama ve rapor kodu aday paketinde bulunuyor. Canlı Site Integrity endpoint’i 404; aktif eklenti listesinde bu eklenti yok.

## BULUNAN DİĞER HATALAR

- TR ana sayfanın sunucu HTML’sinde Araştırmalar bölümü yok. HFCM #1 iki sabit TR kartını JavaScript ile ekliyor; Belçika yok.
- EN ana sayfada HFCM #1 yanında sunucu tarafından üretilen ikinci bir Araştırmalar modülü de var. Bu modülün başlıkları ve bağlantıları TR; EN yazıların Haberler alanında bulunması Araştırmalar doğrulamasını karşılamıyor. Kaynak incelemesi iki üreticiyi de kapsamalı.
- EN Araştırmalar kategori adresi HTTP 404: https://oldiesradyo.com/en/category/ozel-dosyalar-en/arastirmalar-en/
- TR Araştırmalar kategori adresi HTTP 200; tam yazı gövdeleri basılıyor. Belçika/Yunanistan başlıkları var. Öz bağlantının bulunmaması tek başına orphan kanıtı değildir; arşiv şablonu incelenecek.
- Özel Dosyalar / Features sayfalarında referans araştırmaların doğrudan bağlantıları doğrulanamadı.
- Güncel 30 yayındaki 13 eski yazıda featured image yok ve kategori yalnız Uncategorized. Mevcut kayıtlar otomatik değiştirilmedi.
- Yayınlanmış sayfa toplamı 1.130. Önceki envanterdeki 581 kısa/boş editör gövdesi işareti gerçek boş frontend sayfa sayısı değildir; tema kaynaklarıyla kontrol edilecek. Tüm arşivin native TR/EN parity denetimi henüz tamamlanmadı.

## KULLANICI ONAYI GEREKENLER

1. Mevcut WordPress araçları özel eklenti yükleme, HFCM ve klasik PHP kaynak düzenleme sunmuyor. Tarayıcı aracının fallback kuralı, yetersiz bağlantıdan tarayıcıya geçmeden kullanıcı onayı gerektiriyor. Onay sonrası ayrı yönetim erişiminde kaynak/yedek kontrolü, staging, eklenti kurulumu, yerinde modül onarımı ve canlı doğrulama yapılacak.
2. Hizmetler etiketi için somut öneri; URL ve üst menü sırası korunacak:

| Dil | Mevcut | Önerilen |
|---|---|---|
| TR | Hizmetler | DJ & Seslendirme Hizmetleri |
| EN | Services | DJ & Voice Services |

Bu isimlendirme uygulanmadı; onay sonrası kesin menü kaynağı ve önizleme üzerinden değiştirilecek. Yeni üst seviye menü eklenmeyecek.

## SITE INTEGRITY

Genel yüzde henüz hesaplanamaz. 8/8 referans URL, görsel ve Polylang çiftleri doğru; ana sayfa modülleri sağlıklı değil; EN Araştırmalar arşivi 404; canlı menü koruması/yayın kapısı/gece taraması etkin değil.

## Checkpoint ve rollback

Bu aşamada canlı mutation yok. Önceki kategori rollback kaydı korunuyor. İlk paketin SHA256 değeri cb977e295a1e81621a511fdbe5c0f8f7533ef2965201346b37d558e2429433f0. Paket güncellemesi v0.1.1; canlı devreye alım öncesi tema/HFCM/ilgili ayarların yeni yedeği şart. Kod deactivation’da günlük/batch/verify işlerini temizler; master ve raporları korur. Kurulumdan sonra sorun çıkarsa yeni eklenti devre dışı bırakılıp değişen kaynakların birebir yedeği geri yüklenecek.

Kalan işler: tüm native çift/kategori denetimi; yanlış EN archive routing; TR/EN modüllerine yerinde PHP entegrasyonu; HFCM çakışmasının giderilmesi; source-level menü master ve izin kontrolü; Ana Kumanda paneli; günlük event ve tamamlanmış tarama doğrulaması.

Updated package SHA256: a9ee89ae28671de53a0ce9e254b06083552df3e3a9cabbb56c2375657576ca82
Package identity: libfile_725110e0678c8191b803ddcbd22a4006
