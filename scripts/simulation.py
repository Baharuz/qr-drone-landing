"""Foreground supervisor: proje süreç grupları, PID + /proc başlangıç kimliği."""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parents[1]; PX4=Path(os.environ.get('PX4_DIR', str(Path.home()/'PX4-Autopilot'))).expanduser(); STATE=P/'logs/processes.json'
def identity(pid): return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]
def stop():
 if not STATE.exists(): return
 safety=P/'logs/flight_safety.json'
 if safety.exists() and not json.loads(safety.read_text()).get('landed'):
  (P/'logs/cancel_requested').touch()
  start=time.monotonic()
  while not json.loads(safety.read_text()).get('landed'):
   if time.monotonic()-start>70: raise RuntimeError('İniş doğrulanmadı; simülasyon durdurulmadı')
   time.sleep(.2)
 for x in json.loads(STATE.read_text()):
  try:
   if identity(x['pid'])==x['start']: os.killpg(x['pid'],signal.SIGTERM)
  except (ProcessLookupError,FileNotFoundError): pass
 # Kimlik değişmiş bir PID'ye sinyal gönderilmez.
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['start','stop']); ap.add_argument('--instance',type=int,choices=[0,1],default=0); args=ap.parse_args()
 if args.action=='stop': stop(); return
 if STATE.exists():
  for x in json.loads(STATE.read_text()):
   try:
    if identity(x['pid'])==x['start']: raise SystemExit('Proje zaten çalışıyor')
   except FileNotFoundError: pass
 # Başka PX4 instance 0 ile aynı MAVLink portlarını kullanmayın.
 ports=subprocess.run(['ss','-lunp'],capture_output=True,text=True,check=True).stdout
 if f':{14580+args.instance} ' in ports or f':{18570+args.instance} ' in ports: raise SystemExit('PX4 instance 0 portları dolu. Önce host süreç/port sahibini belirleyin; genel pkill kullanmayın.')
 (P/'logs').mkdir(exist_ok=True)
 env=dict(os.environ,GZ_PARTITION='qr_landing_project',GZ_IP='127.0.0.1',GZ_SIM_RESOURCE_PATH=str(P/'models')+':'+str(PX4/'Tools/simulation/gz/models'),PX4_GZ_STANDALONE='1',PX4_GZ_WORLD='qr_test',PX4_GZ_MODELS=str(PX4/'Tools/simulation/gz/models'),PX4_SIM_MODEL='gz_x500_mono_cam_down',PX4_SYS_AUTOSTART='4014',HEADLESS='1')
 (P/'runtime').mkdir(exist_ok=True)
 runtime_log=P/'runtime/log'; log_dir=P/'logs/px4_ulg'
 if runtime_log.exists() and not runtime_log.is_symlink():
  if log_dir.exists(): runtime_log.rename(P/'logs'/f'px4_ulg_saved_{int(time.time())}')
  else: runtime_log.rename(log_dir)
 log_dir.mkdir(exist_ok=True)
 if not runtime_log.exists(): runtime_log.symlink_to(log_dir,target_is_directory=True)
 children=[]; logs=[]
 def launch(cmd,name,cwd):
  log=open(P/'logs'/f'{name}.log','w'); logs.append(log)
  proc=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True); children.append(proc)
  STATE.write_text(json.dumps([{'pid':c.pid,'start':identity(c.pid)} for c in children])); return proc
 def interrupted(*_): raise KeyboardInterrupt
 signal.signal(signal.SIGTERM,interrupted); signal.signal(signal.SIGINT,interrupted)
 try:
  gz=launch(['gz','sim','-s','-r','--render-engine-server',os.environ.get('QR_RENDER_ENGINE','ogre'),str(P/'worlds/qr_test.sdf')],'gazebo',P)
  time.sleep(3)
  if gz.poll() is not None: raise RuntimeError('Gazebo başlangıçta kapandı')
  px=launch([str(PX4/'build/px4_sitl_default/bin/px4'),'-d','-i',str(args.instance),str(PX4/'build/px4_sitl_default/etc'),'-w',str(P/'runtime')],'px4',P/'runtime')
  deadline=time.monotonic()+120
  while time.monotonic()<deadline:
   if any(c.poll() is not None for c in children): break
   if 'Startup script returned successfully' in (P/'logs/px4.log').read_text(): break
   time.sleep(.5)
  if any(c.poll() is not None for c in children): raise RuntimeError('Başlatılan süreç kapandı; logs/ inceleyin')
  if 'Startup script returned successfully' not in (P/'logs/px4.log').read_text(): raise RuntimeError('PX4 başlangıcı doğrulanamadı')
  print('Gazebo ve PX4 ayakta; görüntü ve telemetri testini ayrı terminalde çalıştırın.',flush=True)
  while all(c.poll() is None for c in children): time.sleep(1)
  raise RuntimeError('Proje süreci beklenmedik kapandı')
 except KeyboardInterrupt: pass
 finally:
  stop()
  for c in children:
   try: c.wait(timeout=5)
   except subprocess.TimeoutExpired:
    if identity(c.pid)==next(x['start'] for x in json.loads(STATE.read_text()) if x['pid']==c.pid): os.killpg(c.pid,signal.SIGKILL)
    c.wait()
  STATE.unlink(missing_ok=True)
  for log in logs: log.close()
if __name__=='__main__': main()
