"""Gazebo Transport: tek güncel kare; damga ve duvar saatiyle bayatlık kontrolü."""
import argparse, json, threading, time
from pathlib import Path
import cv2
import numpy as np
from gz.transport13 import Node
from gz.msgs10.image_pb2 import Image
from gz.msgs10.world_stats_pb2 import WorldStatistics
DEFAULT='/world/default/model/x500_mono_cam_down_0/link/camera_link/sensor/imager/image'
class Camera:
    def __init__(self, topic):
        self.topic=topic; self.stats_topic="/world/"+(topic.split("/")[2] if topic.startswith("/world/") else "qr_test")+"/stats"; self.lock=threading.Lock(); self.latest=None; self.count=0; self.last_stamp=None
        self.node=Node(); self.node.subscribe(Image,topic,self.receive)
    def receive(self,m):
        stamp=(m.header.stamp.sec,m.header.stamp.nsec)
        formats={1:1,3:3,4:4} # L_INT8, RGB_INT8, RGBA_INT8
        channels=formats.get(m.pixel_format_type)
        if not channels or not m.width or m.step<m.width*channels or len(m.data)<m.height*m.step: return
        a=np.frombuffer(m.data,np.uint8).reshape(m.height,m.step)[:,:m.width*channels].reshape(m.height,m.width,channels).copy()
        if channels==3: a=cv2.cvtColor(a,cv2.COLOR_RGB2BGR)
        elif channels==4: a=cv2.cvtColor(a,cv2.COLOR_RGBA2BGR)
        else: a=a[:,:,0]
        with self.lock:
            if stamp==self.last_stamp: return
            self.last_stamp=stamp; self.count+=1; self.latest=(time.monotonic(),stamp,a)
    def close(self):
        self.node.unsubscribe(self.topic)
        self.node.unsubscribe(self.stats_topic)
        time.sleep(.2)
    def snapshot(self):
        with self.lock: return self.latest

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--topic',default=DEFAULT); ap.add_argument('--seconds',type=float,default=15); ap.add_argument('--show',action='store_true'); ap.add_argument('--save',default='logs/camera.png'); args=ap.parse_args()
    c=Camera(args.topic); detector=cv2.QRCodeDetector(); start=time.monotonic(); previous=None; stable=0; decoded=set(); stats={}; error=None; value=''; points=None
    def stat(m): stats.update(paused=m.paused,iterations=m.iterations,sim_time=m.sim_time.sec)
    c.node.subscribe(WorldStatistics,c.stats_topic,stat)
    try:
        while time.monotonic()-start<args.seconds:
            frame=c.snapshot(); new=False
            if frame:
                received,stamp,raw=frame; age=time.monotonic()-received; a=raw.copy()
                if stamp!=previous:
                    new=True; previous=stamp
                    value,points,_=detector.detectAndDecode(raw)
                    stable=stable+1 if value=='LANDING_PAD_01' and time.monotonic()-received<.3 else 0
                    if value: decoded.add(value)
                age=time.monotonic()-received
                if age>.3: stable=0
                h,w=a.shape[:2]; cv2.drawMarker(a,(w//2,h//2),(0,255,255),cv2.MARKER_CROSS,20)
                error=None
                if points is not None:
                    pts=points.reshape(4,2); center=pts.mean(axis=0); error=(center-[w/2,h/2]).round(1).tolist(); cv2.polylines(a,[pts.astype(int)],True,(0,255,0),2)
                status='STALE' if age>.3 else value or 'NO QR'
                cv2.putText(a,f'{status} error={error} age={age:.3f}s stable={stable}',(15,35),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,0,255),2)
                if new:
                    Path(args.save).parent.mkdir(parents=True,exist_ok=True); cv2.imwrite(args.save,a)
            else:
                a=np.zeros((480,640,3),np.uint8); cv2.putText(a,'NO IMAGE',(15,35),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,0,255),2)
            if args.show:
                cv2.imshow('QR takip',a)
                if cv2.waitKey(1)&255==ord('q'): break
            time.sleep(.03)
        frame=c.snapshot(); result=dict(frames=c.count,decoded=sorted(decoded),age=None if not frame else time.monotonic()-frame[0],stats=stats,error=error,stable=stable)
        print(json.dumps(result,indent=2))
        if c.count<3 or not frame or time.monotonic()-frame[0]>.5: raise SystemExit(2)
    finally:
        c.close(); cv2.destroyAllWindows()
if __name__=='__main__':
    import os
    pidfile=Path(__file__).resolve().parents[1]/'logs/monitor_process.json'
    pidfile.parent.mkdir(parents=True,exist_ok=True); pidfile.write_text(json.dumps({'pid':os.getpid()}))
    try: main()
    finally: pidfile.unlink(missing_ok=True)
