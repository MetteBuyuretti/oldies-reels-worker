# ENTRY-MAP — kullanılan TR önizleme yolu

İş: WORK2-TR-PREPRODUCTION-20261031-01. Hedef: **legacy kısa 25–30s / TR / tarihli arşiv pilotu**.
PR33 073e7665d9d381e7c8d595fcd60b905a9071490a bu oturumda OPEN/DRAFT/unmerged doğrulandı. Work2 dalı bu sabit ref'ten oluşturuldu; kurulu/aktif Windows sürümü diye sunulmaz.

## İş → giriş → tüketici → profil

| İş / kanıt | Giriş | Gerçek tüketim yolu | Ref / geçerli durum |
|---|---|---|---|
| PR33 TR yerel preview adayı | worker.py main; OLDIES_REELS_LANGUAGE=tr, OLDIES_ZERO_COST_DATE hedef arşiv günü, OLDIES_EDITORIAL_PACKET workspace içindeki JSON | prepare_preview → check_script → check_photo_evidence → hash/çözünürlük kontrolü → packet.local_voiceover + voice_evidence → inspect_audio → worker.render_preview → build_timeline → make_timeline_scenes → render_timeline → check_media_duration | 073e7665d9d381e7c8d595fcd60b905a9071490a; TR legacy 25–30s. Bu görevde worker/render çalıştırılmadı. |
| PR33 GitHub workflow | .github/workflows/reels-worker.yml → python worker.py | Job yalnız workflow_dispatch ve preview_only=true koşulunda. Workflow'da TTS/voiceover_url input isimleri kalmış olsa da main bu adaptörleri çağırmaz. OLDIES_EDITORIAL_PACKET workflow env listesinde yok; discovery otomatik doğrulanmış paket üretmez. | Kaynak okunması; dispatch yok, workflow değişikliği yok. |
| PR33 ücretli-capable eski yardımcı | synthesize_google_voice | main/prepare_preview yolundan çağrılmıyor. Buraya prompt/voice değişikliği yapmak kullanılan local_voiceover'ı değiştirmez. | Yalnız kaynak bulgusu; bu görevde değiştirilmedi/çağrılmadı. |
| Windows LOCAL_REELS_1 | #32/6528707165 ve 6bbf8ace... reels-r0-input.json | R0 beyanı: worker main → prepare_preview → packet.local_voiceover → inspect_audio → render_preview → render_timeline | Git HEAD 073e7665d9d381e7c8d595fcd60b905a9071490a; dört modül eşit, worker ve kalite kapısı farklı. Aktif launcher/worktree kanıtı değildir. |
| Windows LOCAL_REELS_2 | Aynı R0 makbuzu | NO_GIT_METADATA; media_evidence.py yok | İlk adayın aktif kopyası varsayılmadı. |
| Eski İngilizce pilot / FB PR36 | R0'da 18 Ekim EN WAV paketi; ayrıca PR36 facebook_dj consumer | EN WAV, TR tam hikâye sesi değildir. Kabul edilmiş calm/energetic varlıklar yalnız EN istasyon kapanışıdır. | PR36/native kazanımı korunur; bu TR adayına taşınmadı. |
| Bugün çalışan Windows TR launcher | Bu Work2 oturumunda okunmuş/kanıtlanmış giriş yok | Bilinmiyor | Cihaz genelinde yokluk iddiası yok; ana kaynak dalıyla otomatik eşitlenmez. |

## Gerçek hash karşılaştırması

GitHub'dan alınan UTF-8 bytes'ın Git blob kimliği altı dosyada doğrulandı. Aşağıdaki SHA256 değerleri yeniden hesaplandı; Windows karşısı yalnız önceki R0 makbuzudur, yeni Windows ölçümü değildir.

| Modül | PR33 bytes SHA256 | R0 LOCAL_REELS_1 SHA256 | Eşit mi? |
|---|---|---|---|
| worker.py | c0c1555cf8ff583f42cc6059ad70e575846f54153d3e99571d152e2a7a221b4c | 90ee2a1955e340af13b6b119dc796e2d40e90805a2f29c297c7222468f813fb1 | HAYIR |
| reels_preview.py | b4a7225e22a8a6a2cbf31dbcfd7c5149411d580277f575e83cfd9945f63e3cd4 | b4a7225e22a8a6a2cbf31dbcfd7c5149411d580277f575e83cfd9945f63e3cd4 | EVET |
| video_factory.py | fbe4aacf901a61cb0b03d7765c46eb9c4b9575ad562f0156aec299a5e6696d96 | fbe4aacf901a61cb0b03d7765c46eb9c4b9575ad562f0156aec299a5e6696d96 | EVET |
| media_evidence.py | c2e30a6d87a66f5b970fcaff680a99f93d2292f4fe0d0bdb1fbf6a0fba7253f2 | c2e30a6d87a66f5b970fcaff680a99f93d2292f4fe0d0bdb1fbf6a0fba7253f2 | EVET |
| source_evidence.py | e7c95765638f7f8708ff3333f41138b09c18693eb5a7329a0f3f3966ea187fd3 | e7c95765638f7f8708ff3333f41138b09c18693eb5a7329a0f3f3966ea187fd3 | EVET |
| editorial_quality_gate.py | 002ee289505c26d80d568a5f1cd7bb5cb04606d5ae118c3a7f8104c0edf7edd1 | 35289752afc2cf975ca53ddfa3998e0b379c534ef52dd7d903917c8a0294f0f8 | HAYIR |

İki farkın nedeni tahmin edilmedi. PR33 HEAD bilgisinden Windows tam kurulumu/aktif scheduler sonucu çıkarılamaz. Tam veri SOURCE-SNAPSHOT.json ve VALIDATION.json'dadır; özel Windows yolları kopyalanmadı.

## Profil ve tarih bağı

- event_date: 1964-10-18, olay **kayıt**. UK yayım: 1964-11-27; US tarihini UK yerine kullanma.
- Gerçek hazırlık/araştırma oturumu: 31.10.2026. Bu bir 31 Ekim “bugün” haberi değildir.
- PR33'ün research_date alanı check_historical_sources içinde istenen önizlemenin takvim gününü temsil ediyor. PREPRODUCTION.json'da 2026-10-18 yalnız arşiv pilot hedef günüdür; actual_research_session_date ve prepared_at gerçek hazırlığı ayrıca gösterir. Geçmişte bu yeni araştırma yapılmış diye yorumlanmaz.
- local_voiceover/voice_evidence bilinçli null; image_credits boş. Paket render'a hazır değildir.
- Kısa ses 24.88–29.88s, final 25–30s; 10s ret korunur. 59s/uzun hikâye profili uygulanmadı.
- Bağımsız exact-packet/final-MP4 onayı ve yayın kilitleri aynen kalır.

## Kaynakla bağlı somut entegrasyon boşluğu

PR33 video_factory.build_timeline 27.0s **stub** süreyle sekiz caption/sahne üretir. worker.make_timeline_scenes içindeki gerçek photo-atama ifadesi bunları P1/P2/P3/P1/P2/P3/P1/P2 olarak döndürür. T1'deki üç anlatı sahnesi böylece kendiliğinden tüketilmez; altyazı bölümü ile fotoğraf sahnesi ayrımı için sonraki dar sözleşme gerekir. Bu beklenen boşluk üretimsiz olarak yeniden gösterildi; onarıldı veya kuruldu denmedi.

Kaynaklar: [PR33 worker](https://github.com/MetteBuyuretti/oldies-reels-worker/blob/073e7665d9d381e7c8d595fcd60b905a9071490a/worker.py), [prepare_preview](https://github.com/MetteBuyuretti/oldies-reels-worker/blob/073e7665d9d381e7c8d595fcd60b905a9071490a/reels_preview.py), [R0](https://github.com/MetteBuyuretti/oldies-reels-worker/blob/6bbf8ace87d096c062dabcdbb09d9dc8b4ae108d/work-output/jingle-j3-20261030/evidence/reels-r0-input.json), [Watchdog sürüm düzeltmesi](https://github.com/MetteBuyuretti/oldies-reels-worker/issues/31#issuecomment-6495357982).

