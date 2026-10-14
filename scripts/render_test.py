import os,signal,subprocess,sys,time
from pathlib import Path
p=Path(__file__).resolve().parents[1]; os.chdir(p)
(p/'logs').mkdir(exist_ok=True)
px4=Path(os.environ.get('PX4_DIR',str(Path.home()/'PX4-Autopilot'))).expanduser()
env=dict(os.environ,GZ_PARTITION='qr_landing_diagnostic',GZ_SIM_RESOURCE_PATH=str(p/'models')+':'+str(px4/'Tools/simulation/gz/models'),GZ_IP='127.0.0.1')
log=open(p/'logs/render.log','w')
proc=subprocess.Popen(['gz','sim','-s','-r','--render-engine-server',os.environ.get('QR_RENDER_ENGINE','ogre'),'-v','4',str(p/'worlds'/os.environ.get('QR_TEST_WORLD','fixed.sdf'))],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
pidfile=p/'logs/render_process.json'
pidfile.write_text(str(proc.pid))
try:
 time.sleep(3)
 if proc.poll() is not None: raise RuntimeError(f'Gazebo exited {proc.returncode}')
 result=subprocess.run([sys.executable,'src/camera.py','--topic',os.environ.get('QR_TEST_TOPIC','/qr/fixed/image'),'--seconds','10']+(['--show'] if os.environ.get('QR_TEST_SHOW') else []),env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
 (p/'logs/camera_stderr.log').write_text(result.stderr)
 (p/'logs'/os.environ.get('QR_TEST_REPORT','fixed_camera.json')).write_text(result.stdout); print(result.stdout); sys.exit(result.returncode)
finally:
 if proc.poll() is None:
  os.killpg(proc.pid,signal.SIGTERM)
  try: proc.wait(timeout=5)
  except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL); proc.wait()
 pidfile.unlink(missing_ok=True)
 log.close()
