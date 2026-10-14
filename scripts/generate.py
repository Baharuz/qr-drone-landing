from pathlib import Path
import qrcode,cv2
p=Path(__file__).resolve().parents[1]; m=p/'models/qr_pad'; (m/'materials/textures').mkdir(parents=True,exist_ok=True)
img=qrcode.make('LANDING_PAD_01'); img.save(m/'materials/textures/pad.png')
assert cv2.QRCodeDetector().detectAndDecode(cv2.imread(str(m/'materials/textures/pad.png')))[0]=='LANDING_PAD_01'
# Üst yüzey +Z normal, iki üçgen, açık UV koordinatları.
(m/'pad.obj').write_text('v -0.6 -0.6 0\nv 0.6 -0.6 0\nv 0.6 0.6 0\nv -0.6 0.6 0\nvt 0 0\nvt 1 0\nvt 1 1\nvt 0 1\nvn 0 0 1\nf 1/1/1 2/2/1 3/3/1\nf 1/1/1 3/3/1 4/4/1\n')
(m/'model.config').write_text('<model><name>QR Pad</name><version>1.0</version><sdf version="1.9">model.sdf</sdf></model>')
(m/'model.sdf').write_text('''<sdf version="1.9"><model name="qr_pad"><static>true</static><link name="pad"><visual name="qr"><geometry><mesh><uri>model://qr_pad/pad.obj</uri></mesh></geometry><material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse><pbr><metal><albedo_map>model://qr_pad/materials/textures/pad.png</albedo_map><metalness>0</metalness><roughness>1</roughness></metal></pbr></material></visual></link></model></sdf>''')
base='''<sdf version="1.9"><world name="qr_test"><physics name="physics" type="ignored"><max_step_size>0.004</max_step_size><real_time_factor>1</real_time_factor></physics>
<plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
<plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
<plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
<light name="sun" type="directional"><pose>0 0 10 0 0 0</pose><diffuse>1 1 1 1</diffuse><direction>0 0 -1</direction></light>
<model name="ground"><static>true</static><link name="ground"><collision name="ground"><geometry><plane><normal>0 0 1</normal><size>20 20</size></plane></geometry></collision><visual name="ground"><geometry><plane><normal>0 0 1</normal><size>20 20</size></plane></geometry><material><ambient>0.6 0.6 0.6 1</ambient><diffuse>0.6 0.6 0.6 1</diffuse></material></visual></link></model>
<include><uri>model://qr_pad</uri><pose>1 0 0.015 0 0 0</pose></include>
'''
fixed='''<model name="fixed_camera"><static>true</static><pose>1 0 3 0 1.57079632679 0</pose><link name="camera"><sensor name="imager" type="camera"><topic>/qr/fixed/image</topic><always_on>true</always_on><update_rate>10</update_rate><camera><horizontal_fov>1.2</horizontal_fov><image><width>640</width><height>480</height><format>R8G8B8</format></image><clip><near>0.1</near><far>30</far></clip></camera></sensor></link></model>'''
base=base.replace('<light name="sun"','<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/><plugin filename="gz-sim-magnetometer-system" name="gz::sim::systems::Magnetometer"/><plugin filename="gz-sim-air-pressure-system" name="gz::sim::systems::AirPressure"/><plugin filename="gz-sim-air-speed-system" name="gz::sim::systems::AirSpeed"/><plugin filename="gz-sim-navsat-system" name="gz::sim::systems::NavSat"/><gravity>0 0 -9.81</gravity><magnetic_field>6e-06 2.3e-05 -4.2e-05</magnetic_field><spherical_coordinates><surface_model>EARTH_WGS84</surface_model><world_frame_orientation>ENU</world_frame_orientation><latitude_deg>47.397971</latitude_deg><longitude_deg>8.546164</longitude_deg><elevation>0</elevation></spherical_coordinates>'+'<light name="sun"')
(p/'worlds/fixed.sdf').write_text(base+fixed+'</world></sdf>')
(p/'worlds/qr_test.sdf').write_text(base+'</world></sdf>')
print('QR dosyadan okundu: LANDING_PAD_01')
