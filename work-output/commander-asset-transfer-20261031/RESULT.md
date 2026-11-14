# COMMANDER-ASSET-TRANSFER-20261031-07

31.10.2026 | 20:02 TSİ. Mevcut Windows Codex; alım #32/6546409052, ilk hedef20:18. Durum **TEST EDİLDİ — izole aday; etkin değil**.

## Gerçek kaynak ve sınır

Mevcut `oldies-commander-supervised-read.yaml` aynı tünelde `work-output/local-exec-20261029/commander/gateway.candidate.cjs` ve private policy dosyasını çağırıyor. Gateway SHA `696ff10d1de5f4912873ad1c568a9744e5f11fd3875229cb998ca380ee413fc5`; project-tools SHA `f8e5316c2831adb7d4be189e35f75ba3f7d9ed6cae9751c5ddf9592340805e4d`; profile SHA `b1c71c3581b32fd67b6e3cc197f6fc058df72e3b6796ffb261082181185b1809`. Gerçek katalog eski sabit rapor+altı pinned kaynak/staging/parser aracı. Gateway server list/call yönlendirmesi ve upstream allowlist/pin denetimi okundu; tünel anahtarı okunmadı. Çalışan dosyalar ve bağlantı değiştirilmedi. Mevcut source ve project-tools'un izole kopyaları yerel `legacy-fixture/` içinde; live rollback gerektiren uygulama yapılmadı.

## Aday ve gerçek fixture dosyası

`asset_service.py`, `asset-tools.cjs`, `gateway-asset.diff` ve `prepare_gateway.py`: yalnız private manifest asset kimliğiyle seçilen HTTPS kaynağı; tek yapılandırılmış root; basit dosya adı; PNG/JPEG/WebP MIME, gerçek Pillow decode, 20 MiB/50 milyon piksel sınırı; SHA256/bytes/pixel makbuzu. DNS yanıtlarının tümü global IP olmalı, bağlantı doğrulanmış IP'ye sabitlenir ve TLS hostname doğrulanır; redirect hedefleri tekrar HTTPS/izinli host/public IP kontrolünden geçer. URL/query makbuzda yok. Root/ebeveyn ve dosya symlink/reparse reddi; exclusive temp + hardlink ile mevcut dosyayı ezmeden atomik hedef oluşturma; aynı hash'te idempotent, farklı hash'te ret. Hedef dosya gerçekten geri okunup yeniden decode/hash doğrulanır. Aranan asset ID ve çıktı adı dışında URL/path/komut girdisi açılmaz.

MCP adayındaki üç araç: `import_approved_image`, `verify_asset_file`, `read_asset_receipt`. Sonuncusu diskteki dosyadan **yeniden hesaplanan** makbuzdur, imzalı geçmiş işlem makbuzu değildir. Katalog açıklamasında yapılandırılmış root görünür. Önerilen root `C:\Users\METE\Oldies-Radyo-Assets\incoming`: **öneri, oluşturulmadı/izin verilmedi**. Örnek manifest `sources={}` ile kapalıdır; onaylı asset/source host'ları ve root, helper, Python/Pillow kimlikleri özel policy'de ayrıca pinlenmeden aktivasyon yapılmamalı. Eski yedi araç erişimi ya da genel shell yetkisi genişletilmedi.

Gerçek Windows fixture: Node MCP handler → fixture-only Python helper → doğrulanmış sentetik PNG bytes → gerçek dosya → dosyadan geri okuma → SHA `05456723ade4e3e6262d52fbdc132f8dbde05a361d633aeadd50af557e4a8e88`, **74 byte, 4×3**; üç aday handler ve aynı-hash idempotence PASS. Testte kaynak bytes yerel etkisiz fixture'dan enjekte edildi: **gerçek HTTPS indirmesi veya mevcut Work üzerinden ağ/uçtan uca MCP kabulü değildir**.

Python çekirdeği 7 test PASS: gerçek byte/dosya/makbuz/idempotence, traversal/ADS/UNC/reserved ad ve alias reddi, farklı hash üzerine yazma reddi, yanlış MIME/bozuk içerik, boyut sınırı, özel IP ve izin verilmeyen redirect, izin verilmeyen host. İlk varsayılan sandbox denemesinde Windows hardlink işlemi WinError5 ile reddedildi; izole workspace için yetkili işlemde aynı testler PASS. Gerçek mevcut altı project aracı izole kopyasında15/15 regresyon; aday gateway'in sabit rapor aracı kabul+yanlış alias reddi PASS. Eski gerçek Work bağlantı/kabul testi tekrarlanmadı. Aday gateway/Node syntax PASS.

## 1956 kaynağı ve açık işler

`TeePublic Görev Devri` sohbetinde kalıcı kaynak ChatGPT Library dosyası (TeePublic Görev Devri sohbetindeki kaynak kaydı) olarak bulundu. Bu oturumdaki araç kataloğunda bu Library dosyasının ham bytes'ını yetkili biçimde çıkaran aktarım yeteneği bulunmadı; Google Drive'da RocknRoll_Exploded/1956/TeePublic görsel araması ve bilinen Downloads/Pictures dosya yolları eşleşmedi. Sohbette listelenen geçici orijinal sweatshirt görseli, 6000×7500 baskı dosyası olarak kabul edilmedi. Dolayısıyla **1956 dosyası aktarılmadı**. Gerekli girdi: bu Library dosyası için yetkili materialize edilmiş dosya/izinli süreli kaynak ve onun kaynak hash'i; imzalı URL/query public kayda konmaz.

| Yetenek | Mevcut üretim | Bu aday |
|---|---|---|
| Üç pinned Tumblr kaynağı oku / sınırlı staging yaz | DESTEKLENİYOR | Korunur |
| Onaylı resim alma / dosya doğrulama | EKSİK | Kod+fixture testli, etkin değil |
| Genel proje liste/oku/yaz/kopyala | EKSİK | EKSİK |
| Belirli staging syntax parser | DESTEKLENİYOR | Korunur |
| Genel terminal/test, serbest URL veya ek kök | EKSİK | EKSİK |
| Gerçek iş/teslim ve yetkili sayfa durumu | EKSİK | EKSİK |

## Güvenli devreye alma ve geri dönüş

MASTER/WATCHDOG dar incelemesi, root ve tekil kaynak manifest onayı, yeni Python/Pillow ve modül pinleri, mevcut aktif gateway/policy preimage yedeği ve aynı desteklenen yönetilen yeniden başlatma/rollback yolu ayrıca gerekir. Dosya yolu/reparse kontrolleri açma işleminden önce ve sonra tekrar edilir, ancak düşmanca eşzamanlı yerel süreç tarafından yapılan değiştirme yarışına karşı handle-tabanlı bir garanti gösterilmedi; aktivasyon öncesi bu sınır ayrıca çözülmeli veya kabul edilmelidir. Asset helper için gerçek HTTPS/TLS ve canlı MCP wire testi yapılmadı. Bu teslim production restart, policy/scope değiştirme, ücret, kullanıcı asset transferi veya genel-PC yetkisi değildir. Adayın silinmesi/geri alınması yalnız yeni workspace/branch dosyalarıdır; mevcut production yapılandırmasına dokunulmadı. Gerçek endpoint→Windows→Work readback ve gerçek 1956 dosya makbuzu sonraki ayrı kabul sınırıdır.
