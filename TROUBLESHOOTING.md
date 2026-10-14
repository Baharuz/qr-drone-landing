# Kamera ve ortam teşhisi


- Kullanıcının `default` dünyası `paused=true`, `iterations=0` idi. `pause:false` dünya kontrol isteği sonrası 12 s'de 357 güncel görüntü alındı. Kamera yayını başarılı; yerdeki zeminin tek renk görünmesi tek başına boş mesaj değildir.
- İlk sahne sorgusu yalnız zemin/güneş döndürürken kamera yayıncısı kayıtlıydı. Bu veri tek başına model silindi sonucunu desteklemez. Host süreç listesi seçilen depodan bir PX4 ve bir Gazebo sunucusu gösterdi. Terminal süreç görünümü yalıtılmış olduğundan host PID sahipliği kullanıcı çıktısıyla doğrulandı.
- `gz_frame_id` SDF uyarısı doğru QR görüntüsünün alındığı testte de vardı; bu testte engelleyici değildi. `No connection to the GCS` kamera renderından bağımsızdır; MAVSDK bağlanınca GCS geri geldi.
- Mesa/DRM/iris uyarıları ayrı sabit ve drone kamera testlerinde görüntüyü engellemedi. Bu ortamda `/dev/dri` yok. Testler `--headless-rendering`, Ogre2 ile yürütüldü; rastgele sürücü değişikliği veya grafik ortam değişkeni uygulanmadı. Donanım hızlandırma/renderer türü kesin doğrulanmadı; fallback yazılım renderı mümkün, CPU maliyeti donanımdan yüksek olabilir. Drone kamera testinde yaklaşık 27 kare/s gözlendi, kapsamlı performans ölçümü yapılmadı.
- QR malzemesinde ambient/diffuse `1 1 1 1`, albedo PNG, explicit OBJ UV ve +Z normal kullanıldı. Siyah kare sorunu test renderlarında görülmedi.
- Dünya sensörleri eksikse PX4 `Gyro/Accel/barometer missing` verir. Proje dünyasında Imu, AirPressure, Magnetometer, NavSat, AirSpeed ve görüntü Sensors eklentileri açıkça eklenmiştir. Sistem server.config değiştirilmedi.
- MAVSDK cache için `~/.cache/mavsdk` yazılabilir olmalıdır. Bu oturumdaki salt okunur cache sorunu izin mekanizmasıyla giderildi. `.gz` iç log yazma uyarıları renderer testini durdurmadı; stdout/stderr proje `logs/` altında saklanır.
- Port doluysa `ss -lunp` ile sahibini belirleyin. Mevcut instance 0'ın `14580/18570` portları tespit edildi; testler instance 1'e ayrıldı.
- Kamera testinde kapanıştaki pybind11/GIL hatası abonelikler kapanmadan interpreter kapandığında görüldü; açık unsubscribe ve kısa callback kapanış beklemesi eklendi, yön testleri temiz çıkışla tekrar geçti.

