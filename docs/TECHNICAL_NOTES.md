# QR üzerine iniş — PX4 / Gazebo Harmonic

Ubuntu 24.04, Python 3.12, Gazebo 8.10.0; yalnız `/home/bahar/PX4-Autopilot` kullanılır. PX4 kaynakları değiştirilmedi. Proje dünyası `qr_test`, Gazebo bölümü `qr_landing_project`. İlk hedef `LANDING_PAD_01`, 1.2 m beyaz QR levhasıdır. Canlı son görev 1.89 cm yatay hatayla geçti; ayrıntılar [VALIDATION.md](VALIDATION.md) dosyasında.

## Kurulum ve terminaller

```bash
cd /home/bahar/qr-drone-landing
bash scripts/setup.sh
```

Kurulum sistem Python'una pip yazmaz. OpenCV ve Gazebo Python modülleri Ubuntu paketlerinden alınır; sanal ortam NumPy 1.26.4 ile sistem OpenCV'sinin NumPy 2 uyumsuzluğunu giderir. MAVSDK-Python 3.15.3 sabitlendi; 4.x paketinin Python API'si değişmiştir. ROS 2 Jazzy mevcut ama gerekli değil: görüntü, Gazebo Transport Python üzerinden doğrudan alınır; ek ROS köprüsü yoktur.

Mevcut SITL korunurken testlerde instance 1 kullanıldı. `14540` instance 0 için UDP dinleme portudur; `0.0.0.0` uzak hedef değildir. Instance 1 için `14541`, PX4 tarafında `14581` kullanılır. gRPC portu sırasıyla 50051/50052. Uygulamalar yalnız bu yerel SITL bağlantılarına izin verir. Aynı UDP portunda görüntüden bağımsız iki MAVSDK uygulamasını çalıştırmayın.

**Terminal 1 — simülasyon:**
```bash
bash scripts/start.sh --instance 1
```

**Terminal 2 — görüntü:**
```bash
QR_SITL_INSTANCE=1 bash scripts/image.sh
```
Tek pencerede QR sınırı, içerik, merkez, piksel sapması, kare yaşı ve kararlı kare sayısı gösterilir. `q` kapatır. En son kare saklanır, işleme kuyruğu biriktirilmez; aynı zaman damgalı kareler atılır.

**Terminal 3 — önce telemetri, ardından ayrı uçuş testi:**
```bash
QR_SITL_PORT=14541 .venv/bin/python src/telemetry.py
QR_SITL_INSTANCE=1 bash scripts/flight.sh
```

Uçuş: hazırlık → 3 m kalkış → sınırlı arama → hizalanma → alçalma → LAND → yerde ve otomatik disarm doğrulaması. Maksimum gövde hızı 0.25 m/s, alçalma 0.15 m/s. Arama 60 s, alan kalkışa göre ±3 m, görev 180 s. Hedefin dünya konumu kontrol algoritmasına verilmez. Yalnız `src/measure.py` sonuç ölçümü için levhanın dünya konumunu kullanır:
```bash
GZ_PARTITION=qr_landing_project GZ_IP=127.0.0.1 .venv/bin/python src/measure.py
```
Başarı toleransı yatay 0.25 m; yerde olma doğrulanması ve ölçülen son hata ayrı kriterlerdir.

## Koordinatlar, yükseklik ve hata davranışı

Hazır aşağı kamera SDF'sindeki +π/2 pitch nedeniyle görüntü sağ yönü gövde sağ, görüntü aşağı yönü gövde geri yönüdür: ileri hata = `-ey*h/f`, sağ hata = `ex*h/f`. Statik Gazebo render testlerinde ileri hedef `ey<0`, sağ hedef `ex>0` verdi. Her uçuşta 3 m civarında kısa ileri/sağ hareketle sapmanın azalma yönü tekrar ölçülür; doğrulanmazsa LAND uygulanır, alçalma başlamaz.

Yükseklik kalkış öncesi PX4 yerel NED `down` değerine göre hesaplanır. Kamera montajının +0.1 m yüksekliği projeksiyonda eklenir. Bu, düz zemine ve aynı EKF yerel referansına bağlıdır; eğimli/yükseltilmiş arazi için kullanılamaz. Model lidar kanalı yayınlayabilir; kontrol algoritması lidar kullanmaz.

Arama/hizalanmada NED yüksekliği geri beslemesiyle irtifa tutulur; yukarı düzeltme en çok 0.3 m/s'dir. En az 5 ardışık doğru QR karesi gerekir. 0.3 s'den eski görüntü veya QR kaybında yatay/alçalma komutu sıfırlanır, 5 s yeniden algılama denenir; sonra LAND. 0.12 m hizalama korununca alçalır; 0.2 m aşılırsa alçalma durur. Yaklaşık 0.95 m'de son LAND devri yapılır. Ctrl+C/SIGTERM LAND ister ve yerde olmayı doğrulamaya çalışır; havada disarm göndermez. Bağlantı tamamen kaybolursa yazılım LAND'in gerçekleştiğini garanti edemez; sonuç başarısız kalır ve PX4'ün kendi bağlantı kaybı davranışı devrededir. Güvenlik parametreleri kapatılmaz.

Durdurma: `bash scripts/cancel.sh` veya uçuş terminalinde Ctrl+C ile güvenli inişi bekleyin, sonra Terminal 1'de Ctrl+C veya `bash scripts/stop.sh`. Supervisor PID ve `/proc` başlangıç kimliğini kaydeder; yalnız başlattığı süreç gruplarını kapatır. `pkill`/`killall` yoktur. Yeniden başlatmada aynı komutları kullanın. Supervisor, uçuşun yerde olduğunu gösteren kayıt yoksa iptal isteği yazıp iniş doğrulaması bekler; 70 s içinde doğrulanmazsa simülasyonu kapatmaz. Terminali zorla kapatmak/SIGKILL uygulamanın temizleme kodunu çalıştırmayabilir; normal iptal betiğini kullanın.

## Sorun giderme ve render

Detaylar [TROUBLESHOOTING.md](TROUBLESHOOTING.md) dosyasında. Duraklamış dünyada kare gelmez; tek başına `timeout | head` çıktısı kamera arızasını göstermez. `No connection to the GCS` görüntü renderından bağımsızdır.

Testlerde Ogre2 `--headless-rendering` kullanıldı. Bu ortamda `/dev/dri` görünmedi; Mesa uyarıları görüntüyü engellemedi. Donanım hızlandırma/renderer türü kesin doğrulanmadı, yazılım fallback'i mümkün ve CPU yükü daha yüksek olabilir. Sabit tutulan drone kamerada yaklaşık 27 kare/s gözlendi. Sürücü veya rastgele grafik ortam değişkeni değiştirilmedi.

## Doğrulama kayıtları

Ayrıntılı gerçek test sonuçları `VALIDATION.md` ve `logs/` altında. Dosyadan QR çözme, statik render, sabit tutulan drone kamera modeli ve gerçek uçuş ayrı testlerdir. Statik modelle QR okumak, otonom inişin geçtiği anlamına gelmez.

Başlıca kaynaklar: [Gazebo headless rendering](https://gazebosim.org/api/sim/8/headless_rendering.html), [MAVSDK-Python bağlantı örnekleri](https://github.com/mavlink/MAVSDK-Python).

Tekrar testleri: `.venv/bin/python scripts/render_test.py` (sabit kamera), `.venv/bin/python scripts/failure_tests.py` (iptal/QR kaybı), `QR_FAILURE_TESTS=stale .venv/bin/python scripts/failure_tests.py` (bayat görüntü). Arıza testleri kendi instance 1 simülasyonunu başlatır; çalışan proje simülasyonu varsa önce güvenli durdurun.
