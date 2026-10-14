# Canlı doğrulama raporu — 14 Ekim 2026

Proje: `/home/bahar/qr-drone-landing`. PX4: `/home/bahar/PX4-Autopilot`, `v1.16.0-rc1-673-g8b58c01cd7-dirty` (önceden mevcut durum). Gazebo 8.10.0 / Harmonic, Python 3.12.3. Orijinal PX4 kaynak/model/dünya dosyaları ve iç içe diğer depolar değiştirilmedi. Testler doğrudan Linux'ta çalıştı.

## Geçen testler

| Test | Gerçek gözlem | Kayıt |
|---|---|---|
| QR PNG dosyası | OpenCV `LANDING_PAD_01` çözdü | `scripts/generate.py`, PNG |
| Sabit Gazebo kamerası | İlk test 184 kare/20 s; QR çözüldü, son yaş 70 ms | `logs/fixed_camera.json` |
| Sabit tutulan hazır drone kamerası | 539 kare/20 s; QR çözüldü, son yaş 16 ms | `logs/drone_camera.json` |
| Kamera eksenleri, statik render | Öndeki hedef `(ex,ey)=(-0.5,-175.5)` px; sağdaki hedef `(174.5,-0.5)` px | `logs/axis_forward.json`, `logs/axis_right.json` |
| Kullanıcının mevcut kamerası | Duraklama kaldırıldıktan sonra 357 kare/12 s, son yaş 22 ms | `logs/existing_camera.json` |
| MAVSDK / yerel instance 1 | Bağlandı; NED, GPS ve sağlık telemetrisi geldi; sensör kalibrasyonları ve armable doğru | `logs/telemetry_instance1.log` |
| Son izleme penceresi | `--show` ile gerçek pencere açıldı; 100 kare/10 s, QR doğru, son yaş 11 ms | `logs/final_window_qr.json`, `logs/camera.png` |
| İlk tamamlanan otonom görev | Kalkış, arama, hizalanma, alçalma, LAND; yerde ve otomatik disarm doğrulandı; hata **4.67 cm** | `logs/final_position.json`, `logs/flight.jsonl` |
| İrtifa tutma eklenmiş tam görev | Aynı aşamalar geçti; **47.42 s**; hata **1.89 cm**, tolerans **25 cm** | `logs/height_hold_final_position.json`, `logs/height_hold_flight_console.log` |
| Normal kullanıcı iptali | Uygulamaya gerçek SIGINT; görev iptal edildi, LAND ve yerde olma doğrulandı | `logs/failure_tests.json`, `logs/cancel_flight.log` |
| QR kaybı | Sadece proje dünyasındaki `qr_pad` kaldırıldı; yeniden algılama süresi dolunca LAND, yerde olma doğrulandı | `logs/failure_tests.json`, `logs/qr_loss_flight.log` |
| Bayat görüntü | Alçalma sırasında kamera aboneliği kontrollü kesildi; bayatlık algılandı, alçalma durduruldu; LAND ve yerde olma doğrulandı | `logs/stale_test.json`, `logs/stale_flight.log` |

Son başarılı uçuşta arama/hizalanma sırasında kullanılan NED yüksekliği 2.71–2.91 m aralığındaydı (kalkış hedefi 3 m). İşlenen görüntünün en büyük ölçülen yaşı 174 ms; sınır 300 ms. Canlı ileri/sağ hareket testleri görsel hatayı sırasıyla yaklaşık 0.377 m ve 0.155 m azalttı. Dünya hedef konumu bu kontrol hesaplarına verilmedi.

Son ölçümde drone dünya pozu `x=0.990174`, `y=0.016162` m; QR merkezi yalnız sonuç ölçümünde `(1,0)` m alındı. Yatay hata `sqrt((x-1)^2+y^2)=0.018914` m. Modelin referans noktasındaki `z=-0.013` m değeri tek başına iniş kriteri değildir; PX4 ON_GROUND, in_air=false ve armed=false birlikte doğrulandı.

Arıza/iptal görevlerinin çıkış kodu 1 olması beklenir: hedef görev tamamlanmadı, güvenli dönüş doğrulandı. Bunları başarılı QR inişi olarak saymadık. Test harness'i bu beklenen sonuçları kontrol ederek 0 ile çıktı. Son sürümde iptal ve QR kaybı yeniden çalıştırıldı; bayat görüntü testi ayrıca alçalma aşamasına ulaştığını doğruladı.

## Başarısız denemeler ve düzeltmeler

- İstenen proje yolu yokken yazma izni verilmiş olmasına rağmen üst dizin salt okunurdu; `mkdir` ve venv oluşturma engellendi. Çalışma önce yazılabilir alanda hazırlandı. Kullanıcı dizini oluşturunca kaynaklar korumalı kopyalandı ve sanal ortam gerçek proje konumunda yeniden kuruldu. Bu bir uygulama hatası değildi.
- Sistem OpenCV'si kullanıcı NumPy 2.3.2 ile yüklenemedi. Sadece proje venv'inde NumPy 1.26.4 sabitlendi; sistem Python'u değiştirilmedi.
- İlk MAVSDK bağlantısında kullanıcı cache dizini salt okunurdu; bağlantı zaman aşımına uğradı. Desteklenen izin mekanizmasıyla cache yazılabilir oldu; yerel SITL keşfi ve bağlantı geçti.
- İlk proje dünyasında görüntü sensörü vardı, IMU/barometre/pusula/GNSS sistemleri eksikti. PX4 hazırlık kontrolleri bunu reddetti. Dünya eklentileri eklendi; güvenlik kontrolleri kapatılmadı.
- İlk bağımsız PX4 başlatmada veri dizini yanlış geçirildi ve `rcS` bulunamadı. Hazır build'in `etc` dizini, ayrı proje çalışma diziniyle kullanılarak düzeltildi.
- İlk statik ileri eksen testinde interpreter kapanışında pybind11/GIL hatası oluştu. Explicit unsubscribe eklendi; iki eksen testi temiz çıkışla tekrar geçti.
- İlk uçuş, hareket yönlerini doğruladıktan sonra QR kaybıyla durdu ve güvenli indi; yatay hata 61.4 cm olduğundan QR inişi geçmedi.
- Bazı yeniden bağlantı denemelerinde PX4 hazırlık koşulları hazır değildi; kalkış engellendi. Hazırlık için süre sınırlı bekleme eklendi.
- 0.55 m son LAND devri denenirken büyük QR görüntü sınırına yaklaşarak okumayı aralıklı yaptı. Son LAND devri 0.95 m NED yüksekliğine alındı.
- Bir tekrar uçuşunda hizalanma sırasında irtifa kaybı QR'ın kadrajdan çıkmasına yol açtı; güvenli iniş uygulandı. Arama/hizalanmada NED yüksekliğine dayanan irtifa tutma eklendi. Ardından tam görev 1.89 cm hatayla geçti.
- Araç terminalinin zorla sonlandırdığı bir deneme uygulamanın normal iptal yolunu çalıştırmadı; PX4 failsafe ve iniş logları görüldü. Bu normal iptal testi sayılmadı. Normal SIGINT daha sonra uygulamanın kendi sürecinde ayrı olarak gönderilip LAND/yerde olma doğrulandı.

## Sınırlar ve doğrulanmayanlar

- Tam ağ/telemetri kopması ayrıca zorlanmadı. Kod taze NED verisi/bağlantı yoksa görevi keser ve LAND dener; kopmuş bağlantıda komutun teslimi veya iniş garanti edilmez ve görev başarılı sayılmaz. PX4'ün kendi failsafe davranışı korunur.
- Orijinal Gazebo Image Display panelinin doğrudan UI incelemesi yapılmadı; mesaj akışı ve proje OpenCV penceresi doğrulandı. Entity Tree görüntüsünden model silindi sonucu çıkarılmadı.
- Donanım GPU erişimi ve tam renderer/driver seçimi kesin belirlenmedi. `/dev/dri` görünmedi; gerçek görüntü testleri Mesa uyarılarına rağmen geçti. Sürücü değiştirilmedi.
- Statik kameralı/model testleri uçuş değildir. Simülasyon sonuçları gerçek donanım uçuşu veya istatistiksel güvenilirlik garantisi değildir.
- Kullanılan yükseklik yerel NED tahminidir; düz zemine/aynı referansa bağlıdır. Kontrol algoritması lidar kullanmaz. Kamera intrinsics/focal, mevcut modelin 1.74 rad yatay FOV ve kare genişliğinden çıkarılır; farklı model için yeniden doğrulama gerekir.

Testler sonunda projeye ait instance 1 ve render süreçleri kapatıldı. `14581/18571/14541` portları boşaldı; kullanıcının mevcut instance 0 portları `14580/18570` açık kaldı. Genel pkill/killall, commit veya push yapılmadı.
