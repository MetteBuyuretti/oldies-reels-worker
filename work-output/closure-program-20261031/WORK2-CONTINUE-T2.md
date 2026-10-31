# WORK2 — Türkçe Reels uygulama, görsel paket ve teslimi sonuçlandır
**Düzenleme: 31.10.2026 | 05:18 TSİ (UTC+3)**
**Görev:** WORK2-TR-INTEGRATION-20261031-02
**Sorumlu:** Mevcut harici Work2. Yönetim: WORK MASTER/Work1. Bağımsız nihai denetim: mevcut WORK WATCHDOG.
**Durum:** HAZIR; bu kayıt ALINDI/BAŞLADI veya otomatik sohbet tetikleme değildir.

## Dayanak ve hedef
Kurucunun son talebi: Work1 limitini tüketmeden Work2'ye uzun ve çok yönlü, somut sonuç üreten devam işi verilsin. #32/6536371652 teslimini, 3b71f9debc4becc4b2a868796b88897ad1da484d sabit T1 paketini, NEXT-CODE-SCOPE ve STORYBOARD'u okudum. Teslim alınmıştır; gerçek ses/film/görsel veya bağımsız kalite kabulü verilmemiştir.

T1'i yeniden yazmadan şu üç çıktıyı birlikte sonuçlandır: (1) caption değiştikçe fotoğrafı döndüren kusurun çalışan çağrı zincirinde düzeltildiği aday kod ve test, (2) kaynak/hak/gerçek dosya incelemesine bağlı görsel aday paketi, (3) Windows Codex'in doğrudan uygulayabileceği sabit sürüm/test/geri dönüş teslimi. Yalnız plan veya öneriyle işi bitirme.

## Başlangıç, sahiplik ve çalışma düzeni
1. Projedeki kurucu onaylı V3.0 anayasanın tamamını, AGENTS.md, continuity protokolünü, güncel work-state ve #32'nin T1 sonrası yorumlarını oku. Erişilmeyeni doğrulanmış sayma.
2. #32'ye görev kimliği, gerçek TSİ, erişim/branch/base SHA, ilk 20 dakikalık hedef ve planlanan diğer parçalarla ALINDI/BAŞLADI yaz. Önceki T1 beş kontrolü veya eski 43 testi yeni test diye sayma.
3. Mevcut kendi work2/tr-preproduction-20261031 dalından devam et; başlangıç SHA ve PR33 tabanı 073e7665 farkını kaydet. PR33'ü veya başka yazarın dalını doğrudan değiştirme.
4. Bu görevde, kendi izole dalında yalnız reels_preview.py, worker.py, video_factory.py, editorial_quality_gate.py ve bu değişikliklere özgü yeni test dosyaları ile work-output/work2-tr-integration-20261031/ senin uygulama kapsamındır. Son #32'de aynı kapsam için yeni yazar varsa yalnız çakışan dosyayı durdur; diğer parçaları sürdür ve somut çakışmayı kaydet. Work1 monitoring dosyaları, İngilizce Reels PR36/22, PR35, Windows ve merkez durum dosyaları sana devredilmedi.
5. İşi 10–20 dakikalık doğal checkpoint'lere böl; her checkpoint'i kendi dalında kalıcı kaydet ve #32'ye kısa kanıt linki bırak. Merkez work-state tek yazarlığını koru: görev güncellemesini kendi HANDOFF.json/STATE-PATCH.json dosyanda öner; merkezi kaydı doğrudan değiştirme. Bir parçanın erişim engeli bütün işi durdurmasın. Hazır sonraki parçaya ek Work1 talimatı beklemeden geç.

## A — Gerçek tüketim yolundaki kod düzeltmesi
- NEXT-CODE-SCOPE'taki dört modüllük öneriyi uygulamadan önce gerçek main → prepare_preview → render_preview → renderer zincirini doğrula. Yeni yardımcı fonksiyonun çağrılmaması teslim sayılmaz.
- Caption zamanlarını fotoğraf sahnesi zamanlarından ayır; 8 caption için açık üç fotoğraf sahnesi S1→S2→S3 olsun. Fotoğrafı caption modulo hesabıyla seçme, aynı fotoğrafı caption değişiminde yeniden başlatma.
- Yeni görsel sözleşmeyi sürüm, script SHA, özgün görsel SHA, kaynak/kanıt paketi kimliği, sıralı ve eksiksiz aralıklar üzerinden doğrula. Kelime aralığını ölçülmüş ses zaman damgası sayma. Çalışan zamanlama/hizalama girdisi yoksa gerçek medya aşamasını açık eksik bırak; tahmini değeri ölçüm diye geçirmek yok.
- Eksik/yanlış hash, bilinmeyen sürüm, boşluk/çakışma, eksik fotoğraf veya retli varlıkta render/provider çağrısından önce güvenli ret ver. Yeni plan istenmişse sessiz legacy modulo fallback yapma.
- source_evidence.py/media_evidence.py, TTS/model/sessizlik/süre eşikleri ve eski yayın/bağımsız kabul kapıları aynı kalsın. Kapsam dışı modüle gereksinim çıkarsa gerekçeyi somut diff ile kaydet; önce kapsam içi alternatif uygula.
- Legacy 25–30 saniyelik profil ve mevcut kapanış korunur. Ayrı 59 saniyelik Mete videolu projeyi bu işe katma.

## B — Gerçek görsel inceleme ve uygulanabilir paket
- T1'deki üç LOC adayını öncelikle incele. Bu devam, ücretsiz herkese açık özgün görsellerin ve lisans/kredi sayfalarının indirilmesini, gerçek görüntünün görülmesini, SHA256/çözünürlük kaydını ve inceleme amaçlı contact sheet hazırlanmasını kapsar; ücretli görsel/TTS/video üretimi kapsamaz.
- Yalnız yabancı birincil arşiv/hak kaynakları kullan. Erişim/hak kanıtını tarihli URL ve kısa gerekçeyle bağla; “no known restrictions” ifadesini CC0 veya kesin dünya çapı izin diye yeniden etiketleme. TR/GB/US dayanağı belirsizse bunu açık eksik bırak; hukuki kesinlik uydurma.
- Tam kadro/dönem/kişi, keskinlik, mobil 1080×1920 contain yerleşimi, yüzlerin kesilmemesi, sahnelerin birbirinden farkı ve kredi okunurluğunu gerçekten incele. Eski reddedilmiş dosyayı ad/crop değiştirerek geri getirme.
- P1/P3 çok benzerse veya P2 yetersizse aynı dönem/olayı dürüstçe temsil eden daha iyi arşiv alternatifi bul. İncelenemeyen görsel için PASS verme. Fotoğraf arşiv bağlamını olayın gerçek kayıt günü fotoğrafı diye sunma.
- Çıktı: ASSET-MANIFEST.json, RIGHTS-AND-VISUAL-REVIEW.md, gerçek görsellerden contact sheet ve gerekiyorsa reddetme/alternatif tablosu. Repo'ya büyük özgün dosya yığma; mevcut kalıcı dosya imkânıyla kaydet ve hash+erişilebilir bağlantı ver. Bu Work2'nin ön incelemesidir; bağımsız Watchdog veya kurucu kabulü değildir.
- Erişim engelinde URL/dosya/denenen yol/eksik alan/sahip belirtilen tek girdi paketi bırak ve A/C'yi sürdür.

## C — Odaklı test, teslim ve Windows devri
- Gerçek preview/render callable zincirinde 8 caption/3 sahne, caption değişirken sabit fotoğraf aralığı ve tüm kapanışın kapsanmasını doğrulayan ağsız test çalıştır.
- Negatif testler: yanlış script/foto SHA, eksik/bilinmeyen plan, boşluk/çakışma, retli görsel/türev kimliği, eksik hak/bağımsız kabul, mevcut 10s ve >30s sınırları. Fake fixture yalnız test kanıtıdır; gerçek ses/film kabulü olmaz.
- İlgili mevcut regresyonları değişiklik gerektirdiği ölçüde çalıştır. Gerçek dependency ile çalışanlar ile stub kullanılanları ayrı yaz. Ücretli API ve yayın çağrısı sıfır olmalı.
- İzole dalından taslak PR aç/güncelle: net problem/davranış, değişen dosyalar, test çıktısı, korunmuş sınırlar, gerçek medya eksikleri. main merge, deploy, scheduler açma veya Windows uygulaması yapma.
- RESULT.md, HANDOFF.json, TEST-RESULTS, ENTRY-MAP güncellemesi ve LOCAL-CODEX-HANDOFF.md teslim et. Windows devri tam ref/dosya SHA/preimage-postimage/beklenen çağrı/uygulama önkoşulu/yedek/rollback/üretimsiz doğrulama komutlarını içersin. Windows'ta uygulanmış gibi yazma; yerel hash farkında durma koşulu belirt.
- #32'ye en çok beş maddelik sonuç ve sabit commit/PR/görsel paket linklerini yaz. GERÇEKLEŞEN, BEKLEYEN, PLANLANAN ayrı olsun. Eksik gerçek ses/film/bağımsız kabul veya kurulu uygulama nedeniyle görevi OPERASYONEL PASS diye kapatma.

## Yetki ve bitti ölçütü
Bu iş yalnız izole aday kodu, ücretsiz arşiv incelemesi, çevrimdışı test ve uygulanabilir teslim içindir. Yeni ücret/abonelik, TTS/provider çağrısı, gerçek ses/final film üretimi, canlı kaynak/claim/lock/activation, yayın, merge/deploy yok. Mevcut geçerli onayları tekrar isteme; kapsam içi işleri tamamlamak için her checkpoint'te kullanıcıya dönme.

Bitti ölçütü: çağrılan kod yolu gerçekten düzeltilmiş + anlamlı testleri çalışmış + görsel girdiler gerçek kanıtla ya teslim edilmiş ya da kesin eksik alanları belirlenmiş + Windows uygulanabilir paket ve taslak PR mevcut. Sonucu doğrudan ortak kayda bırak; kullanıcıdan rapor taşımasını isteme. Work1'in sessiz kalması alım/kabul veya yeni yetki değildir.
