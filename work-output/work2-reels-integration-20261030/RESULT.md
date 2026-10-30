# WORK2 — R1/R2 kod adayı ve teslim kaydı

**İş:** WORK2-REELS-INTEGRATION-20261030-01  
**Durum:** KOD / TEST KAYNAĞI HAZIR; PYTHON DOĞRULAMASI BLOCKED — tamamlanmış test/uygulama/kabul değildir.  
**Alım:** 30.10.2026 19:58 TSİ · **Uygulayıcı:** WORK2 · **Devralan:** WORK MASTER  
**Dal:** work2/reels-integration-20261030  
**Sabit kod/test snapshot:** 8e4d5451737e816fc4c2c91badbb9f0f6af625e8  
**Draft PR:** https://github.com/MetteBuyuretti/oldies-reels-worker/pull/36 — hedef PR22 dalı fix/facebook-global-dj-voice.  
**Taban:** PR22 / 9ad08776e882af386f2897ac43e85eaeb28f029e; OPEN/DRAFT/unmerged okundu.

## Sorun → son aday davranışı

**R1:** Eski PR22 validate_template yalnız sakin path'i kilitliyordu; hash/onay cache koşulu sağlanmazsa preview kapanışı yeniden TTS ile üretebiliyordu. Gerçek worker.synthesize_google_voice (facebook_dj) → facebook_global_audio.synthesize_dj çağrı yolunda seçim artık calm/energetic → kabul edilmiş dosyanın bytes/SHA256 kontrolü → aynı bytes'ın gerçek FFmpeg concat girdisine kopyalanması → dj_recording profil/hash/kaynak/kanıt/süre bağıdır. Bilinmeyen profil, eksik/değişmiş dosya, yanlış recording bağı kapalı durur. Kabul edilmiş kapanış için advert TTS fallback yoktur.

Kimlik kanıtı #32/6509320201 ve e1c87bd0616ca763a2362282ff4d878aab3f02f4 içindeki reels-signoff-identities.json'dur. Sakin 26880 bytes / 6.720s; enerjik 21120 bytes / 5.280s. Tam hashler SIGNOFFS içindedir. Calm repo varlığını kullanır. Energetic yalnız mevcut özgün yerel dosyanın OLDIES_FACEBOOK_ENERGETIC_SIGNOFF_PATH mutlak yol eşlemesini kullanır; eşleme verilmezse reddeder. Yeni binary/özel kaynak yüklenmedi.

Ses kimliği kabulü ile yayın onayı ayrıdır: advert_approved=false, advert_sha256 boş, advert_approval=null korunmuştur; approver/tarih üretilmedi. final_media_approved=false. require_approved_signoff ayrı üretim kapısını tutar. İki kabul edilmiş kapanış, bütün hikâye veya MP4 kabulü sayılmaz.

**R2:** Aynı Facebook adayında eski 18s/17.4s, renderer'daki 15s taban ve medya kapısındaki 10–18s kabulü birlikte değiştirildi. Doğal hikâye + seçilmiş kapanışın ölçülen süresi + mevcut 1.1s sessiz aralık, sabit 0.6s görsel kuyrukla 25–30s olmalıdır. Yalnız kuyruk 30fps kare sınırına yuvarlanır. Kısa/uzun/sonlu olmayan ölçümler, segment toplamı/recording/render sapması, kesilmiş final ve tempo müdahalesi reddedilir. TTS çıktısı atempo ile uzatılmaz/hızlandırılmaz. Synth, gerçek Facebook renderer ve medya/recording kapısı aynı hesapla bağlandı.

Eski 25 kelime / ilk cümle 20 kelime sınırı 52 kelimelik üst sınıra çıkarıldı; kelime sayısı süre kanıtı değildir. Genel doğum/ölüm cümlesi veya kısa hikâye süreyi sağlayamazsa durur; doldurma metni eklenmez. PR22'nin mevcut ilk kaynak cümlesinden metin kurması ve editoryal derinlik/orijinallik eksikleri bu dar süre yamasıyla kabul edilmiş sayılmadı. Kaynak doğrulaması, olaya özel doğal anlatım ve gerçek fotoğraf/film için bağımsız yaratıcı kabul hâlâ gereklidir.

## Değişiklik kapsamı

| Dosya | Değişiklik |
|---|---|
| facebook_global_audio.py | Gerçek kapanış tüketimi/recording bağı, üretim kapısı ayrımı, doğal süre hesabı ve MP4 uyumu |
| facebook-global-template.json | Profil varsayılanı calm; yeniden üretim kapalı; yalnız Facebook 25–30s süre sözleşmesi |
| facebook_global_visuals.py | Renderer başlangıcında aynı doğal recording/süre kapısını çağırır |
| test_facebook_signoff_integration.py | 12 yeni fixture/stub test metodu |
| test_facebook_global_audio.py | 14 fixture/stub test metodu; eski preview regeneration / 10–18s beklentilerinin yeni sözleşmeye taşınması |

Mevcut görsel kimlik/lisans/dönem/full-frame kuralları değişmedi: validate_photo, select_period_photos, load_period_photos, full_frame_canvas, make_scenes ve validate_publish fonksiyon gövdeleri tabanla metin olarak eşit karşılaştırıldı. worker.py, diğer kanallar, TR preview, workflow/scheduler ve merkez main work-state değiştirilmedi. PR22/PR33/main/PR35'e kod yazılmadı. Kendi görev work-state.json kaydı bu klasördedir.

## Gerçek doğrulama durumu

- GitHub: dal/commit yazımı ve beş kod/test dosyasının geri okunması başarılı; içerik hazırlanan payload ile eşit. Bu kayıt doğrulamasıdır, Python çalıştırma değildir.
- JavaScript/V8: kaynak payload üzerinde seçim çağrısı, advert TTS fallback yokluğu, atempo yokluğu, renderer ortak kapı çağrısı ve false/boş üretim bayrakları kontrol edildi. Altı mevcut görsel koruma gövdesinin eşitliği kontrol edildi. Bunlar Python davranış testi değildir.
- exec_command ile pwd, python --version ve python -m unittest -v test_facebook_signoff_integration test_facebook_global_audio denenmek istendi. Hepsi yürütme öncesi **No usable execution environment is available** hatası verdi. Oturumun exec-server initialize handshake'i başarısız; hiçbir komut başlamadı.
- **Python syntax: NOT RUN. 26 test metodu: NOT RUN. 0 yeni Python PASS.** Baseline-fail/candidate-pass veya gerçek ffprobe/FFmpeg sonucu iddia edilmiyor.
- Fixture testleri yanlış profil/hash/eksik dosya, recording bağı, önceden kabul edilmiş kapanışın tekrar üretilmemesi, gerçek worker motor yönlendirmesi, üretim onayı kapalı, provider hatasında durma, TTS kapalıyken render/yayın engeli, sessiz/eksik ses, 9:16, aralık ve doğal süre sınırlarını kapsayacak şekilde hazırlandı. Gerçek API/medya kullanılmaz; provider/ölçüm/concat/render stub'dır.
- Önceki başarılı testler yeni test sayısına eklenmedi. Mevcut test_facebook_global_visuals değişmedi ve bu oturumda çalıştırılmadı.

## Tek sonraki teknik adım / engel

Bu sabit kod snapshot'ını yetkili çevrimdışı Python ortamında doğrula:

```text
python -m compileall -q facebook_global_audio.py facebook_global_visuals.py test_facebook_signoff_integration.py test_facebook_global_audio.py
python -m unittest -v test_facebook_signoff_integration test_facebook_global_audio test_facebook_global_visuals
```

Bu komutlar **çalıştırılmış değildir**. Tek mevcut kod-doğrulama engeli çalışır Python yürütme ortamıdır. MASTER bu kaydı doğrudan devralabilir; kullanıcıdan rapor taşıması istenmez. PR22'den miras Google auth/TTS workflow'unu test için dispatch ETME; bu görevde yeni workflow/ücretli provider/gerçek medya yetkisi yoktur.

Windows uygulaması ayrı sınırda: mevcut Windows Codex'ten özgün enerjik dosya eşlemesi ve gerçek aktif giriş/ref makbuzu beklenir; WORK2 genel Commander kapsamını genişletmedi, Windows staging/Jingle dosyalarına yazmadı. Gerçek 25–30s MP4, tam hikâye ve bağımsız medya/kullanıcı kabulü yoktur.

## Checkpoint ve geri dönüş

R1 bağımsız checkpoint: 63395276b95960ce0de54150957c1e5a7d4d9915 (#32/6528536196).
R2 ilk kod checkpoint: 194dc88584b5a1c8004a93e8a1f97da252a3167b.
Son kod/test snapshot: 8e4d5451737e816fc4c2c91badbb9f0f6af625e8.
Sonraki yalnız manifest/rapor commit'i #32'de sabit bağlantıyla yazılır; HANDOFF.head_commit kod/test snapshot'ını ifade eder.

Canlı değişiklik olmadığı için dağıtım geri dönüşü gerekmez. İncelemeyi bırakmak için draft PR36 kapatılabilir; taban PR22/main korunur. Kör reset/force-push/merge yapılmadı. Arka planda çalışan görev veya otomatik sohbet tetikleme iddiası yoktur.
