# LOCAL-CANONICAL-HANDOFF-BRIDGE-20261031-05

31.10.2026 | 17:26 TSİ. Durum: **TEST EDİLDİ — izole aday**. Alım #32/6544645532, ilk hedef 17:44 TSİ.

Canonical `src/jingle_factory.py` CLI `--music-handoff` ve `Factory(music_handoff=args.music_handoff)` yolunu destekliyor. Mevcut `scripts/Run-Factory.ps1` bu parametreyi iletmiyor; gerçek launcher baseline fixture'ında verilen parametre Python child'a ulaşmadı. Aday yalnız açık `-MusicHandoff` için mevcut dosyayı doğrular, yolu mutlaklaştırır, utility modlarıyla çatışmayı reddeder ve Windows CreateProcess kurallarına göre `--music-handoff` ile tek child argüman olarak iletir. Parametresiz `--evening` davranışı korunur. Sonrasında gün/slot/job/hash/kök kontrolleri mevcut Python validatörüne aittir; yeni bypass, otomatik arama, tarih değiştirme veya eski receipt yeniden kullanımı yok.

Kaynak launcher SHA256 `1300e811e001719fbe1d2b6fa581bd2f7b1f1297ea457117d2a51fe30973934d`; Factory SHA256 `68ad43649497eabbc828c30c06ebc4b4944a616de0c83c7c2dfbdb78043298bf`; aday SHA256 `21a6c0ea568a3fad76e7e33a843204f41eb7054d28cdca9a3fa7b8d84b5cc2f4`. Launcher/Factory pre/post aynı.

Gerçek wrapper kaynakları yalnız test fixture kopyasında çalıştırıldı; mevcut kullanıcı secret okuması fixture'da `$null` ile değiştirildi. Fake `python.exe` C# child, Windows PowerShell 5 üzerinden gerçekten aldığı argv'yi kaydetti. Baseline parametreyi düşürdü; aday default argümanı, boşluk/$/&/Unicode/köşeli parantez içeren dosya yolunu tek argüman olarak ve sentetik validator exit42'yi doğru taşıdı. Boş ve olmayan yol, utility çatışması child öncesi reddedildi. `fixture-results.json`: bir beklenen baseline kusuru ve altı aday kontrolü. Exit42 validator reddinin **simülasyonudur**; gerçek Python Factory/validator çalıştırılmadı, dış-kök/gün/slot/job/hash koşulları için canlı kabul iddiası yok.

Geri dönüş: kurulu kaynak değiştirilmedi; `backup.private/Run-Factory.ps1` özgün hash ile doğrulandı. İleride ayrı yetkili uygulamada exact preimage ve bağımlılıklar tekrar kontrol edilip yalnız launcher değişikliği geri alınmalıdır. İzole aday, onaylı ses ve STAGE kurulumu korunur. Gerçek üretim için bugüne/slot'a bağlı yetkili iş, canonical root'ta doğrulanmış handoff.json, job/receipt ve kaynak SHA256 ile geçerli provider/activation gereklidir; bunlar bu testte oluşturulmadı.

## Sosyal güncel yerel kayıt

31 Ekim 09:20 TSİ Tumblr launcher fresh raporu exit1/ERROR. Hata `scrollIntoViewIfNeeded` sırasında DOM'dan ayrılan element; o koşuda queued=0, published=0. Editorial health raporu readyForDraft=0/verifiedDrafts=0; publisher hata ile bittiğinden platformun bugünkü eksiksiz stok/queue sayısı doğrulanmadı. Intake 306 aday, onaylanmış yeni stok sayısı değildir.

Pinterest yerel `pinterest-90-pin-queue.json` üretim zamanı 31 Ekim 15:40:19 TSİ, kaynak41, 90 plan satırı, bugün3 `PENDING_PINTORA`; bunlar platformda planlanmış/yayımlanmış pinler değildir. Son ayrı platform reconcile kaydı 30 Ekim22:10: 94 o anda gözlenen pin, 0 yeni yayın ve bulk acceptance NOT_VERIFIED. Taze platform queue hedefi/freshness/job-platform receipt mevcut kayıtlardan doğrulanamadı.

Tumblr mevcut publisher, CDP ile yeni sayfa açıp queue DOM okuduktan sonra journal yazdığı için bütünü salt okunur GET değildir; Pinterest launcher log yazar ve token refresh edebilir. Bu süreçler çalıştırılmadı. Taze hedef için mevcut yetkili oturumda token yenilemeyen, state/log yazmayan açık queue GET/yanıt yeteneği ve iş↔platform kimliği gerekir. Üretim/queue write/publisher/refresh yapılmadı. Work2 07:40 raporu devralındı; önceki STAGE kurulumu tekrarlanmadı.
