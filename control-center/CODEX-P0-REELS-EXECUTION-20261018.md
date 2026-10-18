# OLDIES RADYO — CODEX P0 REELS KURTARMA / UYGULAMA EMRİ
**Tarih:** 18 Ekim 2026 (TRT)  
**Sorumlu:** MASTER; **uygulayıcı:** Codex; **bağımsız kabul:** Work-1 + WATCHDOG + kullanıcı  
**İş:** #30; **merkezi denetim:** #32; **kod PR:** #33; **FB referansı:** #22  
**Durum:** HAZIRLANIYOR — değişiklikler sadece PR #33 dalında; CANLIDA DEĞİL.

## 0 — İlk 5 dakika: Kaldığın yerden devam et
1. `AGENTS.md`, `control-center/work-state.json`, #30, #31, #32 ve PR #33 diff/CI'ı oku. Tamamlanan işleri yeniden yapma.
2. Çalışılacak **tek** dal: `fix/p0-evidence-based-reels-qc-20261016`; başlangıç head `8df9ad496267a809c11dce05334a81a7dc116994`. Bu SHA değişmişse önce diff'i ve diğer yazarları uzlaştır; kör force-push yapma.
3. **Mevcut tamamlanmış ilk checkpoint:** `video_factory.py` artık 25–30s doğal ses süresini zorluyor. 10s sınırına ait test güncellendi, `test_reels_duration_contract.py` eklendi, offline kalite CI'ı genişletildi. [CI run 39092267714](https://github.com/MetteBuyuretti/oldies-reels-worker/actions/runs/39092267714) PASS. **Tekrar yazma, devam et.**
4. Yarım kalan yerel Codex çalışmasını SİLME veya ÜZERİNE YAZMA: `C:\Users\METE\Documents\Oldies-Radyo-Automation\Codex-P0-Review\Reels-20261016\source\oldies-reels-worker-fix-p0-evidence-based-reels-qc-20261016`. Orada `worker.py`, `video_factory.py`, `source_evidence.py`, `editorial_quality_gate.py`, `zero_cost.py`, `reels_preview.py` kısmi fikir ve kodları var. Önce main + PR #33 + yerel snapshot üçlü karşılaştırması; yararlı kısımları seçerek aktar, kör kopyalama yok.
5. **Bilinen snapshot kırıkları:** `test_editorial_quality_gate.py` eski `measured_duration` argümanıyla çağırıyor fakat kurtarılan gate bu argümanı kaldırmış; `worker.py` kısmi düzenlemede Google authentication isimlerinin tanımlanması/ithali uyumsuz olabilir; yerel Jingle .venv'de `requests` eksik. Windows snapshot'ta `py_compile` PASS, hedefli test 11 error/11 test FAIL; bu, kodun üretime hazır olduğu anlamına gelmiyor. Çözüm: uygun izole dependency/runtime, gerçek MP4 FFprobe, revize edilmiş doğru test sözleşmesi. Sağlam güvenlik kapısını test uğruna gevşetme.
6. Codex Cloud ortamı bu repo için tanımlı değilse veya aktif yerel Codex oturumu salt-okunursa **BLOCKED/ortam engeli** kaydet; çalıştığını iddia etme, paralel/çakışan ikinci oturum açma. Mevcut Etsy Codex oturumuna dokunma.

## 1 — Kurallar: Değiştirilemez güvenlik sınırı
- `main`, `reels-worker.yml` ve `facebook-global-en.yml` yayın güvenlik kilitlerini değiştirme. TR `create-draft` sadece manuel `preview_only=true`; FB `publish-facebook` `if:false`. Cron, concurrency, dedupe ve imzalı artefact mekanizmaları korunacak.
- PR #33 ve FB PR #22 **DRAFT kalacak, MERGE YASAK**; PR #22'nin `mergeable=false` gerçeğini görmezden gelme. Sahte onay oluşturma. WordPress'e yeni `DRAFT_REVIEW` gönderme; Facebook/Instagram/YouTube'a yayın yapma. Mevcut taslak ve medyayı silme/değiştirme.
- Jingle Factory, Etsy, Pinterest, radyonun canlı altyapısı, WordPress ana site, mevcut token/secret ve diğer Codex oturumları KAPSAM DIŞI.
- **SIFIR EK MALİYET:** Yeni ücretli API, lisans, görsel servisi/aboneliği veya üretim kredisi yok; izinsiz Gemini/Google/Meta gerçek çağrısı yok. İlk faz sadece repo + offline test. Gerçek önizleme için ücret/limit/kimlik belirsizse açıkça DUR.
- Kod onarımı `preview-only` ile ayrı, geri alınabilir commit'ler ve her değişiklik için hedefli test. Yeni sistem/repo/yeniden mimari yazımı yok; mevcut entegrasyon korunacak.

## 2 — Üretim onarımı: Başarı sırası

### A. Tek araştırma ve tarihsel kanıt sözleşmesi
- `zero_cost.py` `fetch_music_history_candidates`, `build_history_candidates`, `score_candidate` ile `worker.py` seçim yerlerini onar. **İlk aday kaynağı yalnız günün This Day In Music sayfası**, `/on-this-day-in-music-<month>-<day>/` (Europe/Istanbul günü). Soundod/Wikipedia/Wikidata birincil aday olarak öne geçmeyecek. Bu siteler ancak uygun *bağımsız olgu doğrulaması* için kullanılabilir; TDiM ile aynı grup sahibi ikinci kaynakmış gibi sayma.
- Kullanılan dönem onaylı 1950–1990 bağlamı. Kaynak yetersiz/çelişkiliyse diğer olaya geç; eski müzik videosunu veya tarihsiz olayı tekrar kullanma. Wikipedia/Wikidata tek başına kaynak kanıtı olmasın.
- Olay türü `release/chart/concert/tour/collaboration/award/recording/birth/death/other` olabilir. **Her habere şarkı/album zorunlu değil.** Sanatçı, olayın ne olduğu, doğrulanmış tarih, 1–2 olaya özgü ayrıntı ve neden ilginç olduğu şart. Chart olayında eser/liste/sonuç; yaşam olayında insani bağlam. Ölüm, hastalık, dava için iki otorite.
- Kanıt paketi: tam URL, retrieval timestamp, kısa kaynak özeti/alinti, excerpt SHA, claim/artist/date eşleşmesi, kullanıldığı DJ cümlesine bağ ve bağımsız doğrulama. `source_evidence.py` yararlı başlangıç; hash ve URL varlığı **doğruluk ispatı DEĞİL**; insan/hakem doğrulaması ayrıdır.

### B. Editoryal çekirdek ve doğal DJ
- `worker.py::build_turkish_gemini_script` ve `turkish_gemini_style_prompt` içindeki `facts[0]` tek cümle fallback, jenerik doğum/ölüm cümleleri ve **9–10 saniye** talimatını kaldır/uygun biçimde değiştir. Eski `DURATION=15`, TTS 7–18.5s aralığını 25–30s standardı ile uyumlaştır; yalnız bir sabiti değiştirmek yeterli değil.
- Kaynaklı olaydan **özgün, sıcak, deneyimli DJ hikâyesi**: merak uyandıran giriş, iki somut detay, doğal kapanış. Telifli kaynağı aynen tercüme edip okuma. Anlatıcıya uydurma/ilave olgu icat ettirme. Bir örnek uzunluğa kör kelime ekleme veya acele ettirme yok.
- TR kapanışı **“Oldies Radyo. Dinle, beğen, paylaş.”**; EN kapanışı **“Oldies Radyo. Timeless music. Listen, enjoy, share.”**; marka yazımı OLDIES RADYO. Dil sızıntısı, okunmayan özel ad, eser adı yazım hatası, tekrarlanan cümle RED.
- TR ve EN aynı kanıt/araştırma çekirdeğinden beslenebilir, fakat TTS, ses tonu, süre, slogan, teslim statüsü, hak/territory ayrı adaptörlerdir. EN için PR #22'deki yararlı DJ fikirlerini oku ama PR #22 merge/deploy yapma.
- Son ses doğal okuma 25–30 saniyelik gerçek nihai MP4'e yetmeli; `video_factory.py` yeni `final_reel_duration` kontratı korunacak. 10 saniyeyi sessiz beklemeyle 27 saniyeye uzatmak, ses yavaşlatıp hızlandırmak, intro/sonu tekrarlamak RED.

### C. Gerçek görsel kimliği ve hakları
- `worker.py::image_matches_artist`, `download_commons_photos`, `zero_cost.py::score_candidate` delilsiz `visual_strength=15` ve genel True geçişlerini kaldır. Galeri tercihi gerçek arşiv fotoğrafı; doğru sanatçı/grup, makul yıl/dönem ve olay uyumu, kaynak fotoğraf URL, lisans türü, creator, kredi, kullanım yeri/territory, çözünürlük ve seçilen kare kanıtları tutulmalı.
- Her pilotta en az 3 gerçekten uygun ve birbirinden farklı fotoğraf veya onaylı eşdeğer görsel planı; aynı fotoğrafı/ilgili olmayan simgeyi tekrarlama. Fotoğraf yoksa aday değiştir, sahte uygunluk üretme.
- Negatif regresyon: `Eagles` hayvan/şato; Bee Gees heykel/maket; Madonna heykel/dini imge/ilgisiz kişi; waxwork, çizim, poster, kapak görseli, logo, AI tarihi fotoğraf gibi sunma; tarih/artist/lisans bilinmiyorsa RED.
- Otomatik `metadata match` insanın görsel ve lisans incelemesi yerine geçemez. PR #33 `editorial_quality_gate.py` içine kanıtı kesin olmayan fotoğraf için FAIL CLOSED koşulu korunacak.

### D. Gerçek video ve QA
- `video_factory.py` ve worker entegrasyonunda ses + görsel + SRT zaman çizelgesini tutarlı üret; 9:16, tercihen 1080×1920 ve 30fps. Yumuşak geçiş, okunur Türkçe/İngilizce caption, doğal ses, kapanışın duyulur olması. Kopya/bozuk/sessiz içerik RED.
- Nihai MP4 **25.00–30.00 s** `ffprobe` ile ölçülecek; ses track'i de mevcut ve süreyle tutarlı olacak. `sha256`, kaynağı, fotoğraf lisans dosyaları ve zaman çizelgesini bağla; sadece TTS veya FFmpeg 0 exit kodunu `PASS` sayma.
- Müzik eklenmesi kullanıcı/editör tarafından yapılacaksa müzik aşaması atlanıp otomatik yayın yapılmasın. Taslak, bağımsız kalite, kullanıcı onayı, teslim ve platform alındısı ayrı durumlar olsun: `DRAFT → RENDERED → QC_PASS → OWNER_APPROVED → DELIVERED → PLATFORM_VERIFIED`. FB API response `success=true` gerçek yayın kanıtı değil.
- Kalite kontrol dış teslimden ÖNCE; PR #33'teki fail-closed denetimi zayıflatma. Pozitif fixture'da sahte MP4 baytları ve elle `measured_duration=27.1` **gerçek medya PASS kanıtı değildir**; gerçek FFprobe girdiyle ayrı entegrasyon testi üret.

## 3 — Testler ve P0 negatif kanıtlar
- Eski Michael Jackson “Ben” (14 Ekim) ve Four Tops “Reach Out I'll Be There” (15 Ekim) gerçek **10.000000s** MP4 = mutlaka FAIL. Eski 10s ses sözleşmesi asla geri gelmesin.
- TDiM eksik veya yanlış gün, Soundod-only, Wikipedia-only, chart tarihi uyuşmazlığı (özellikle Bee Gees `Massachusetts`), kaynakta iddia yokluğu, jenerik/İngilizce sızıntı, yanlış şarkı/ad (Neil Diamond `Cracklin' Rosie`), sanatçı/heykel/hayvan, lisanssız fotoğraf, hatalı hash, yanlış kullanıcı onayı = FAIL.
- Pozitif fixture testlerini gerçek dosya/ses/FFprobe ile doğrula; kaynak delili varlığı sahte fotoğraf doğrulaması yapılmış gibi sunulmasın. Yeni veya değişen kod için `py_compile`, modül hedefli pytest/unittest, reproducible offline CI. Tüm geçmiş testlerin yeniden çalışmasını yalnız kapsam gerektirirse yap.
- **İlk teslim**: en az 1 gerçek TR ve 1 gerçek EN **preview-only** MP4 pilotu, her biri 25–30sn, gerçek kaynak+fotoğraf+ses+caption/SRT+SHA/FFprobe kayıtları. Ardından standart genelleniyor mu görmek için her dilde ikinci farklı tarih/olay pilotu. Kullanıcı ve Work-1/Watchdog kabulünden önce CANLIDA/PUBLISHED YAZMA.
- Kaynak veya lisans bulunamazsa sahte medya/pilot gösterme; ilgili pilot için `BLOCKED` ve tek doğrulanabilir neden raporla.

## 4 — Codex çalışma biçimi / checkpoint zorunluluğu
Sıra: (1) üçlü diff ve test kırıkları, (2) araştırma seçimi ve delil, (3) özgün TR/EN ses senaryosu, (4) görsel kanıt, (5) gerçek video/QA, (6) pilot/Work-1. Her etap 1 küçük commit/delil + hedefli test ve kalıcı checkpoint. Gereksiz yeni dosya veya framework yok.
- `work-output/reels-quality-p0-20261018/` altında `CODEX-RESULT.md`, `DIFF-INVENTORY.md`, `TEST-LOG.md`, `PILOT-MANIFESTS/` oluştur (uygun aşamada); job sonucu, SHA, test exit, yanlış negatif/pozitif kontroller, gerçek harcama=0/harcama yapılmadı kanıtı, engel, sonraki adım.
- #30'da her gerçek adımın kanıtını paylaş; #32'ye kısa MASTER devri; Work-1 #31 ayrı denetçi. `AGENTS.md` checkpoint protokolünü uygula. Gerçek sonuç yokken “done”, “tested” veya “published” deme.
- Üretim/QC ve kullanıcı onayı olmadan PR #33'ü READY FOR REVIEW/MERGED, #22'yi MERGED veya canlı cron'u ENABLED yapma.
- **İlk gece hedefi:** üretim zincirini offline kod+test bakımından ayağa kaldır, yarım kalan Codex değişikliklerini tutarlı hale getir, gereksiz servis çağrısı yapmadan QA kanıtı bırak. Gerçek önizleme üretimi uygun/yetkili araçla mümkünse yap; değilse kesin blokajı ve sıradaki tek işlemi raporla.

## 5 — Bitiş tanımı ve rapor
**KOD DÜZENLEME BİTTİ:** Eksik üretici akışı onarıldı, hedefli regresyon CI PASS, değişiklikler tek review branch'inde ve bağımsız denetime hazır.  
**PİLOT ÜRETİMİ BİTTİ:** Gerçek MP4/ses/FFprobe/SHA/fotoğraf-hak-kaynak kanıtı mevcut.  
**CANLIDA:** ancak kullanıcı onayı, Work-1/Watchdog kabulü, kontrollü tek kanal açma ve platform doğrulaması sonrası.

Bu üç aşamayı ASLA birbirine karıştırma. Kullanıcıya “işimiz bitti, şimdi gerçek sonucu bekliyoruz” demek için teknik düzenleme bitmiş olmalı; MP4 çıktısının değerlendirilmesi ayrı raporlanmalı.
