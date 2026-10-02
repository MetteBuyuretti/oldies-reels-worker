# Work Başlangıç Talimatı — Kopyala / Yapıştır

Bu görev uzun sürebilir ve bağlantı kesilebilir. Çalışmaya başlamadan önce GitHub repository `MetteBuyuretti/oldies-reels-worker` içindeki `AGENTS.md`, `control-center/WORK_CONTINUITY_PROTOCOL.md` ve `control-center/work-state.json` dosyalarını oku.

Kurallar:
- İşi tek parçada yürütme; doğal 10–20 dakikalık teslimat paketlerine böl.
- Her paket bittiğinde sonucu kalıcı dosyaya kaydet.
- Sonra `work-state.json` içinde ilgili görevin checkpoint'ini güncelle.
- Checkpoint oluşmadan sonraki pakete geçme.
- Bağlantı / oturum kesintisinden sonra işi sıfırdan başlatma.
- Yeniden bağlandığında önce durum dosyasını ve mevcut çıktıları oku, ilk eksik paketten devam et.
- Tamamlanmış işi tekrar üretme.
- Çelişki varsa mevcut çıktı dosyalarını gerçek kaynak kabul et ve durumu onlarla uzlaştır.
- Gizli anahtarları, tokenları veya parolaları durum dosyasına yazma.

Görev bu repository'deki mevcut kayıtlardan biriyle eşleşiyorsa aynı task id'yi kullan. Yeni görevse önce yeni task id oluşturup durum dosyasına ekle.
