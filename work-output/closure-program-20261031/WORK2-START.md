# HARİCİ WORK2 — Türkçe Reels somut ön üretim teslimi
**31.10.2026 | 02:41 TSİ (UTC+3)**  
İş: WORK2-TR-PREPRODUCTION-20261031-01. Operasyontakibi: mevcutWORKKOORDİNATÖRÜ; nihaiMASTER: mevcutWork1/root; bağımsızdenetçi: mevcutWORKWATCHDOG.

**Durum HAZIR:** Bu dosya hariciWork2'ye yöneliktir. Yazılmış olması yeni alım veya başlangıç değildir. ÖncekiFBPR36teslimi korunur; aynıiki kapanışın kimliği/bağımsızkabulü yeniden aranmaz.

## Amaç
MevcutTürkçeReelsPR33hattının ilkeksik önüretim parçasını somutlaştır: kullanılanpreviewgirişinin kaynağa bağlıharitası, tamözgünDJmetni, olgu→kaynakkanıtı ve hikâyeye bağlıgörselstoryboard. Sırf geneldurum raporuyla bitirme. Eski dosyalarda zaten kabul edilmiş parça varsa yeniden üretmeden ilkeksik/retgerekçesini gider.

## Gerçek başlangıç
1. MainAGENTS.md, control-center/work-state.json, aynıklasördePROGRAM.md veCOORDINATOR.md; #31/6495357982 sonWATCHDOGsürüm/çağrıyolu düzeltmesini oku. Sonrakiüretim sınırları mevcut.
2. #32'ye işIDile **HARİCİWORK2ALINDI/BAŞLADI** yaz: gerçekTSİ, erişebildiğin araçlar, seçtiğinref/dal ve ilk20dakikalıkparçanın gerçekçi kontrolsaati. Ortam/erişimyoksa başlamış/testetmiş sayma.
3. PR33head'ini doğrula. Bu görevin tabanı `073e7665d9d381e7c8d595fcd60b905a9071490a`; güncelheaddeğişmişse kör varsayma. Bu ref'ten ayrı `work2/tr-preproduction-20261031` dalı. İsim zaten varsa sahibini/soncheckpoint'i uzlaştır, reset/overwrite yok.
4. **İlkparçada yalnız** `work-output/work2-tr-preproduction-20261031/` dosyalarına yaz. PR36FBdalını/PR22/PR33/main/PR35/monitoring/Windows/Commander/Jinglekaynaklarını değiştirme. MerkezstateKoordinatör'dedir; kendigörevcheckpoint'ini kendiçıktıklasöründe tut.

## İlk somut paket — T1
- **ENTRY-MAP.md:** İlgiliiş→GitHub/yerelgiriş→worker/prepare_preview→local_voiceover/renderer→ref/hash→geçerliprofil. PR33preview `synthesize_google_voice` çağırmaz; orayaTTSyaması yazıp kullanılan sesi düzelmiş sayma. WindowsCodexR0kaynağı #32/6528707165'te; LOCAL_REELS_1HEAD073e… tamworktree/aktiflauncherkanıtıdeğildir. Bilinmeyenaktifgirişi varsaymadan ayrı yaz.
- **PREPRODUCTION.md:** Mevcut doğrulanmışolay/olgu/öncekimetin ve fotoğraftaslaklarını önce oku. Önceki kullanıcıretleri ve onaylıparçalar korunur. Yeni“bugün”gerekmiyorsa eskiolayı bugüntarihiyle etiketleme. TamTRDJmetni: kişi/neoldu/tarih/olayaözgü1–2ayrıntı/ilginçbağlam ve mevcutTürkçemarka kapanışı. KaynağısatırsatırTürkçeyeçevirerekprodüksiyonmetniyapma; yalnız yabancıgüvenilirkaynaklardan bağımsızözgünanlatım. Olgu→doğrudankaynakURL→metindekicümle tablosu. Yeniaraştırma yalnız eksik olguyapılacak; genişbaşlangıçtaraması yok.
- **STORYBOARD.md:** Her sahneye anlatıparçası, gerçekdoğruyıl/kadro/kişi, görselURL/kredi/hakkayıtı, kompozisyon/mobilokunurluk ve seçimgerekçesi. Aynı3fotoğrafı9–11sahnede mekanikdöndürmek kabul değil. Daha önce reddedilenHarrisonfoto/ses veya heykel/AIikamesi geri getirilmez. Uygunfoto yoksa kanıtsızfotoPASS yerine tekeksikgirdi kaydedilir.
- Hedefprofil açık olacak: mevcutlegacy25–30skısa sözleşme ve10sretkorunur; uzunstory/ayrı59sDJprojesi mevcutkısaakışın üstüneyazılmaz. Metni hızlandırma/kesme/doldurma yok. Sesüretmeden tahminiokumasüresini **tahmin** diye yaz; gerçekses/filmölçümü sayma. Hedefprofil belli değilse yaratıcıönkabul için somutmetin/storyboard teslim et; toplukodlimitini değiştirme.

## İkinci parça — yalnız somut eksik için
T1'i sabitcommit/RESULT/HANDOFFilecheckpoint'le. İlkbulgunun gerektirdiği dar kod/sözleşme farkı varsa kullanılanPR33profilini ve mevcutyetkiyi açıkayırt ederek **yalnız ayrıdalda adaydiff ve odaklıtest** öner; ilkparçada kökkoddosyalarınıdeğiştirme. Koordinatör dosyasahipliğini doğruladıktan sonra gerekli4–5modüldeki hedefliyama işine geçilir; yeni genelanaliz döngüsü yok. Tammetin/storyboard önkabulü gerektiren aşamayı sahteonaybayrağıyla aşma.

## Korunacaklar / sınırlar
- CommandergerçekdarnihaiPASS tamam: yenidenkurulum/anahtar/refresh/kabultestiyok. Mevcut6proje aracı genelWindows/Jingle/Reelsköküne erişim değildir.
- İngilizcekapanışlar calm/energetic yalnızENistasyonkapanışlarıdır; tamTRhikâyesesiyerine kullanma. FBPR36kod/testteslimini, seskimliği veyaV3.1'i yenidenyapma.
- YeniAPI/TTS/provider/ücret/gerçekmedya/MP4/render/indirme/import/miks yok. Workflowdispatch/merge/deploy/scheduler/platformyayını/claimreset yok. Hamözelmedya/config/credential publicrepoya yüklenmez.
- Testyazıldı/çalıştı/kuruldu/gerçekçıktı/bağımsızkabul ayrı. Work2çalışmaortamıhâlâaçılamıyorsa NOTRUNbırak; anlamlıodaklıtestkaynağını teslim et, Work1 uygunortamda gerçekçalıştıracak. Eski43/36başarıyı yenitest sayma.

## Teslim
Kendidalında RESULT.md + HANDOFF.json: işID/aktör/gerçekalımTSİ/tabanref/dal/head/değişendosyalar/gerçekdoğrulamalar/NOTRUN/sınırlar/kalanengel/teksonrakihamle. #32'ye kısa teslim + **sabitcommit** bağlantıları. Kullanıcıdan raportaşımasını isteme. Koordinatör/MASTER sonrakiaktifokumada doğrudan devralır; kayıt başka sohbeti kendiliğinden uyandırmaz.
