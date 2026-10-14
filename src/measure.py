"""Gerçek dünya pozu sadece sonuç ölçer; kontrol algoritmasına verilmez."""
import argparse,json,time,threading,math
from gz.transport13 import Node
from gz.msgs10.pose_v_pb2 import Pose_V
ap=argparse.ArgumentParser(); ap.add_argument('--model',default='x500_mono_cam_down_1'); args=ap.parse_args()
n=Node(); latest={}; lock=threading.Lock(); topic='/world/qr_test/pose/info'
def receive(m):
 for p in m.pose:
  if p.name==args.model:
   with lock: latest.update(x=p.position.x,y=p.position.y,z=p.position.z,received=time.monotonic())
n.subscribe(Pose_V,topic,receive); time.sleep(3); n.unsubscribe(topic); time.sleep(.2)
with lock:
 if not latest or time.monotonic()-latest['received']>.5: raise SystemExit('Güncel gerçek poz alınamadı')
 latest['horizontal_error_m']=math.hypot(latest['x']-1,latest['y']); latest['tolerance_m']=.25; latest['within_tolerance']=latest['horizontal_error_m']<=.25
 print(json.dumps(latest,indent=2))
