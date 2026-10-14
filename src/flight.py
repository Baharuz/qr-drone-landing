"""Yalnız proje SITL'i. Görsel hizalama, kontrollü alçalma, kayıpta LAND."""
import asyncio,json,math,signal,time,os
from pathlib import Path
import cv2
import numpy as np
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed
from mavsdk.telemetry import LandedState
from camera import Camera
P=Path(__file__).resolve().parents[1]
async def mission():
 cfg=json.loads((P/'config.json').read_text())
 instance=int(os.environ.get('QR_SITL_INSTANCE','0'))
 if instance not in (0,1): raise RuntimeError('Yalnız SITL 0/1')
 cfg['model']=f'x500_mono_cam_down_{instance}'
 port=14540+instance
 if not cfg['axes_verified']: raise RuntimeError('Kamera yön testleri doğrulanmadan uçuş engellendi.')
 topic=f"/world/{cfg['world']}/model/{cfg['model']}/link/camera_link/sensor/imager/image"
 cam=Camera(topic); detector=cv2.QRCodeDetector(); d=System(port=50051+instance); tasks=[]; t={}; armed_here=False; offboard=False; motion_verified=False; height_hold=cfg['takeoff_m']; last_down=0; log=open(P/'logs/flight.jsonl','a')
 def state(s,**kw):
  if s in ('kalkış','tamamlandı','güvenli iniş doğrulandı'):
   (P/'logs/flight_safety.json').write_text(json.dumps({'pid':os.getpid(),'landed':s!='kalkış','state':s}))
  print(s,flush=True); log.write(json.dumps(dict(time=time.time(),state=s,**kw))+'\n'); log.flush()
 async def watch(name,stream):
  async for v in stream: t[name]=(time.monotonic(),v)
 def value(name):
  x=t.get(name)
  if not x or (name=='local' and time.monotonic()-x[0]>2): raise RuntimeError('Telemetri bayat: '+name)
  return x[1]
 async def wait_for(predicate,seconds):
  start=time.monotonic()
  while not predicate():
   if time.monotonic()-start>seconds: raise TimeoutError('Durum zaman aşımı')
   await asyncio.sleep(.1)
 origin_down=None
 async def velocity(f=0,r=0,down=0):
  nonlocal height_hold,last_down
  if 'local' in t and origin_down is not None:
   h=origin_down-value('local').position.down_m
   if down==0:
    if last_down!=0: height_hold=h
    vertical=float(np.clip(.8*(h-height_hold),-.3,.15))
   else: height_hold=h; vertical=down
  else: vertical=down
  last_down=down
  log.write(json.dumps(dict(time=time.time(),command_forward=f,command_right=r,command_down=vertical))+'\n'); log.flush()
  speed=cfg['speed_mps']; await asyncio.wait_for(d.offboard.set_velocity_body(VelocityBodyYawspeed(float(np.clip(f,-speed,speed)),float(np.clip(r,-speed,speed)),vertical,0)),2)
 async def land_and_verify():
  # Havada disarm yok. Offboard sürerken LAND istenir; tekrar mod değiştirilmez.
  await asyncio.wait_for(d.action.land(),5)
  await wait_for(lambda: 'landed' in t and value('landed')==LandedState.ON_GROUND and not value('in_air'),60)
  await wait_for(lambda: not value('armed'),15)
 loop=asyncio.get_running_loop(); current=asyncio.current_task()
 if os.environ.get('QR_TEST_CAMERA_LOSS_AFTER'):
  def stop_test_camera():
   state('test: kamera aboneliği kesildi'); cam.node.unsubscribe(cam.topic)
  loop.call_later(float(os.environ['QR_TEST_CAMERA_LOSS_AFTER']),stop_test_camera)
 if os.environ.get('QR_TEST_CANCEL_AFTER'): loop.call_later(float(os.environ['QR_TEST_CANCEL_AFTER']),lambda: os.kill(os.getpid(),signal.SIGINT))
 for sig in [signal.SIGINT,signal.SIGTERM]: loop.add_signal_handler(sig,current.cancel)
 try:
  (P/'logs/flight_process.json').write_text(json.dumps({'pid':os.getpid(),'start':Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]}))
  state('hazırlık'); await asyncio.wait_for(d.connect(system_address=f'udpin://0.0.0.0:{port}'),15)
  process_record=json.loads((P/'logs/flight_process.json').read_text()); process_record['mavsdk_pid']=d._server_process.pid; (P/'logs/flight_process.json').write_text(json.dumps(process_record))
  for name,stream in [('connection',d.core.connection_state()),('health',d.telemetry.health()),('local',d.telemetry.position_velocity_ned()),('in_air',d.telemetry.in_air()),('armed',d.telemetry.armed()),('landed',d.telemetry.landed_state())]: tasks.append(asyncio.create_task(watch(name,stream)))
  await wait_for(lambda: all(k in t for k in ['connection','health','local','in_air','armed','landed']),15)
  if not value('connection').is_connected or value('armed') or value('in_air') or value('landed')!=LandedState.ON_GROUND: raise RuntimeError('Bağlantı/başlangıç güvenliği sağlanmadı')
  (P/'logs/flight_safety.json').write_text(json.dumps({'pid':os.getpid(),'landed':True,'state':'yerde hazırlık doğrulandı'}))
  await wait_for(lambda: value('health').is_local_position_ok and value('health').is_global_position_ok and value('health').is_home_position_ok and value('health').is_armable,30)
  health=value('health')
  if not (health.is_local_position_ok and health.is_global_position_ok and health.is_home_position_ok): raise RuntimeError('PX4 konum ve home hazır değil')
  await asyncio.sleep(1); frame=cam.snapshot()
  if cam.count<3 or not frame or time.monotonic()-frame[0]>cfg['max_frame_age_s']: raise RuntimeError('Canlı kamera hazır değil')
  origin=value('local').position; origin_down=origin.down_m; origin_n=origin.north_m; origin_e=origin.east_m
  if (P/'logs/cancel_requested').exists():
   (P/'logs/cancel_requested').unlink(); raise asyncio.CancelledError('Hazırlıkta iptal')
  await d.action.set_takeoff_altitude(cfg['takeoff_m']); armed_here=True; state('kalkış'); await d.action.arm()
  if (P/'logs/cancel_requested').exists():
   (P/'logs/cancel_requested').unlink(); raise asyncio.CancelledError('Kalkış öncesi iptal')
  await d.action.takeoff()
  await wait_for(lambda: origin_down-value('local').position.down_m>2.7,30)
  await velocity(); await d.offboard.start(); offboard=True
  state('arama'); mode='arama'; start=time.monotonic(); search_start=start; last_seen=start; stable=0; aligned=0; previous=None; last_good=None
  while time.monotonic()-start<cfg['mission_timeout_s']:
   if not value('connection').is_connected: raise RuntimeError('SITL bağlantısı koptu')
   if (P/'logs/cancel_requested').exists():
    (P/'logs/cancel_requested').unlink(); raise asyncio.CancelledError('Kullanıcı iptali')
   pos=value('local').position; height=origin_down-pos.down_m
   if abs(pos.north_m-origin_n)>3 or abs(pos.east_m-origin_e)>3 or height>4: raise RuntimeError('Test sınırı aşıldı')
   frame=cam.snapshot(); now=time.monotonic(); fresh=frame and now-frame[0]<cfg['max_frame_age_s']
   if fresh and frame[1]!=previous:
    previous=frame[1]; a=frame[2]; value_qr,points,_=detector.detectAndDecode(a)
    cv2.imwrite(str(P/'logs/flight_camera.png'),a)
    log.write(json.dumps(dict(time=time.time(),frame_qr=value_qr,height=height,stable=stable,frame_age=time.monotonic()-frame[0]))+'\n'); log.flush()
    now=time.monotonic(); fresh=now-frame[0]<cfg['max_frame_age_s']
    if fresh and value_qr==cfg['target'] and points is not None:
     center=points.reshape(4,2).mean(axis=0); h,w=a.shape[:2]; focal=w/(2*math.tan(1.74/2))
     # SDF pitch +pi/2: image down = body -forward; image right = body right.
     ex,ey=center-np.array([w/2,h/2]); last_good=(-float(ey)*(height+.1)/focal,float(ex)*(height+.1)/focal); stable+=1; last_seen=now
    else: stable=0; last_good=None; aligned=0
   if not fresh:
    stable=0; last_good=None; aligned=0
    await velocity()
    if now-last_seen>cfg['loss_timeout_s']: raise RuntimeError('Görüntü bayat/kayıp')
   elif stable>=cfg['stable_frames'] and last_good:
    if mode=='arama': mode='hizalanma'; state(mode)
    if not motion_verified:
     state('hareket yönü testi')
     async def sample_error():
      frame=cam.snapshot()
      if not frame or time.monotonic()-frame[0]>.3: raise RuntimeError('Yön testinde bayat kamera')
      a=frame[2]; q,pts,_=detector.detectAndDecode(a)
      if q!=cfg['target'] or pts is None: raise RuntimeError('Yön testinde QR kayboldu')
      ih,iw=a.shape[:2]; fx=iw/(2*math.tan(1.74/2)); ex,ey=pts.reshape(4,2).mean(axis=0)-[iw/2,ih/2]
      z=origin_down-value('local').position.down_m+.1
      return np.array([-ey*z/fx,ex*z/fx])
     changes=[]
     for axis in (0,1):
      before=await sample_error()
      for _ in range(10):
       await velocity(.15 if axis==0 else 0,.15 if axis==1 else 0,0); await asyncio.sleep(.1)
      for _ in range(20): await velocity(); await asyncio.sleep(.1)
      after=await sample_error(); changes.append(float(after[axis]-before[axis]))
      if changes[-1]>-.025: raise RuntimeError('Hareket yönü görsel olarak doğrulanamadı')
     motion_verified=True; last_seen=time.monotonic(); state('hareket yönleri doğrulandı',changes_m=changes); stable=0; aligned=0
     continue
    ef,er=last_good; error=math.hypot(ef,er); aligned=aligned+1 if error<.12 else 0
    down=0
    if aligned>=10:
     if mode!='alçalma': mode='alçalma'; state(mode)
     down=.15
    if error>.2: aligned=0; down=0
    await velocity(ef*.5,er*.5,down)
    if height<.95 and error<.12 and aligned>=10:
     await velocity(); state('iniş'); await land_and_verify(); state('tamamlandı',local_north=value('local').position.north_m,local_east=value('local').position.east_m); return
   elif mode=='arama':
    if now-search_start>cfg['search_timeout_s']: raise RuntimeError('Arama zaman aşımı')
    # Sınırlı kare tarama; hedef dünya konumuna erişim yok.
    leg=int((now-search_start)//8)%4; f,r=[(.2,0),(0,.2),(-.2,0),(0,-.2)][leg]; await velocity(f,r,0)
   else:
    await velocity()
    if now-last_seen>cfg['loss_timeout_s']: raise RuntimeError('QR kaybı; yeniden algılama süresi doldu')
   await asyncio.sleep(.1)
  raise TimeoutError('Görev süresi doldu')
 except BaseException as e:
  state('iptal/hata',reason=repr(e))
  if armed_here:
   try:
    if offboard:
     height_hold=origin_down-value('local').position.down_m; await velocity()
    await asyncio.shield(land_and_verify()); state('güvenli iniş doğrulandı')
   except BaseException as recovery: state('iniş doğrulanamadı',reason=repr(recovery))
  raise
 finally:
  for task in tasks: task.cancel()
  await asyncio.gather(*tasks,return_exceptions=True); cam.close(); d._stop_mavsdk_server(); d._server_process=None; log.close(); (P/'logs/flight_process.json').unlink(missing_ok=True); del d
if __name__=='__main__': asyncio.run(mission())
