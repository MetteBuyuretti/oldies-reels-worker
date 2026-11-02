# OLDIES Commander — salt-okunur ilk kapı adayı
**Tarih:** 2026-11-02 (TSİ) · **Görev:** COMMANDER-INDEPENDENT-PC-20261031-07 altında izole inceleme · **Durum:** KOD/İZOLE TEST TAMAM, GERÇEK WINDOWS/WORK KABULÜ YOK.

## Kanıta dayalı mevcut durum
- Önceden görülen `project-tools.cjs` dışarı yalnız Tumblr kaynak/staging/parser işlemlerini veriyor.
- Aday `gateway-asset.cjs` içinde upstream `get_config` sonuçlarındaki `allowedDirectories` değerleri ayrıca kontrol ediliyor; gateway tool kataloğu da ayrı filtre.
- 02.11 kontrolünde `OLDIES_Commander__list_project_files` MCP SSE probe 429 döndürdü. Remote Desktop cihazı `Mete-DELL-2025` offline/last seen 96h olarak döndü. Bu iki erişim engeli canlı Windows'a bakılmasını önlüyor; Windows bilgisayarının fiziksel olarak kapalı olduğunu kanıtlamıyor.

## Bu dalda gerçek teslim
- `readonly-pilot.cjs`: **yalnız bir policy-bound test kökü**, gerçek upstream `allowedDirectories` kapsamı içinde olma zorunluluğu, gizli/dot dosyaları reddi, symlink/reparse denetimi, 64 KiB UTF-8 metin + SHA256, en fazla 100 dizin girdisi.
- `pilot_powershell_info`: herhangi bir serbest komut, argüman veya shell girdisi kabul etmez; Windows PowerShell binary SHA256 ile sabitlenmiş olmalı; yalnız sürüm ve çalışma dizini sorgusu; exit code ve hatalar ayrı.
- Kod halen bir **bağımsız modüldür**. Mevcut gateway'e bağlanmadı, Windows'a kurulmadı, credential/tunnel/scheduler değişmedi.

## Test kanıtı
- İzole Linux Node v22.16.0: `node --test readonly-pilot.test.cjs` → **14/14 PASS** (geçici gerçek dosya/dizin üzerinde).
- Testler: doğru okuma/hash, gizli dosya engeli, `..` ve Windows mutlak yol/ADS reddi, bilinmeyen proje/ek argüman reddi, yetkisiz root reddi, symlink reddi, büyük/geçersiz UTF-8 reddi, Windows dışında çalışmama, pin olmadan/yanlış pinle çalışmama, sabit komut parametrelerinin **sentetik Windows runner ile** doğrulanması, nonzero exit ve timeout durumları.
- **Gerçek Windows PowerShell yürütülmedi**; Windows komutu için mock runner kullanıldı. Bir adversarial eşzamanlı reparse/TOCTOU garantisi kurulmadı; gerçek Windows üzerinde bu sınır ayrıca incelenmeli.
- Kod yerel SHA256: `ad26f1606e430e0aa1279320d8ff2a6bd351b1c783635eaa37243022850519ac`. Yerel test kaynağı SHA256: `178e2c779921e8615a3d0efeff1bb17071dbaa11a1503021c433d0831302ba8b`. GitHub test kaydı yalnız bir boş satır farkıyla aynı test ifadelerini içerir; bu SHA yerel kopyaya aittir.

## Tek sonraki gerçek kapı
1. Çalışan Windows gateway/profile SHA, gerçek upstream `get_config` ve `list_tools`, izinli bir Tumblr dışı **test klasörü**, PowerShell binary hash ve geri dönüş dosyaları local read-only doğrulansın. Gerçek policy/secret açık GitHub'a yazılmasın.
2. Dar adayın arayüze bağlanacağı test sürümünde, ayrı izin/etkinleştirme kontrolüyle **gerçek Windows okuma → SHA geri okuma → sabit PowerShell exit code** ölçülsün. Bu aşamada geniş shell, yayın, yazma, restart veya genel-PC izni açılmasın.
3. **Aynı ChatGPT Work bağlantısından gerçek MCP çağrısı** ve mevcut yedi aracın regresyonu da geçerse dar pilot GO; aksi durumda NO-GO, rollback.
4. Bu dar GO yalnız salt-okunur ilk kapıdır; genel PC komut/oturum, çoklu proje yazma/arama ve çift yönlü medya transferi için ayrı kanıt gerekir. Kurucunun esas hedefi daraltılmış sayılmamalı.

**Bildirim:** Bu branch/draft PR mevcut `07` görevinin ek deneyidir, yeni uygulanmış sistem veya otomatik MASTER/WATCHDOG çağrısı değildir. Bağımsız inceleme olmadan production merge/deploy yok.
