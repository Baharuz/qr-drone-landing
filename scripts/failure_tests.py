"""Yalnız bu projenin instance 1 süreçlerini başlatır/durdurur."""
import json,os,signal,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parents[1]; os.chdir(P)
env=dict(os.environ,GZ_PARTITION='qr_landing_project',GZ_IP='127.0.0.1',QR_SITL_INSTANCE='1')
results=[]
tests=os.environ.get('QR_FAILURE_TESTS','cancel,qr_loss').split(',')
if not set(tests)<=set(['cancel','qr_loss','stale']): raise ValueError('Geçersiz test')
for test in tests:
 before=len((P/'logs/flight.jsonl').read_text().splitlines()) if (P/'logs/flight.jsonl').exists() else 0
 sim=None; flight=None
 with open(P/'logs'/f'{test}_simulation.log','w') as sl,open(P/'logs'/f'{test}_flight.log','w') as fl:
  try:
   sim=subprocess.Popen([sys.executable,'scripts/simulation.py','start','--instance','1'],env=env,stdout=sl,stderr=subprocess.STDOUT)
   time.sleep(15)
   if sim.poll() is not None: raise RuntimeError('Test simülasyonu başlatılamadı')
   fe=dict(env)
   if test=='cancel': fe['QR_TEST_CANCEL_AFTER']='20'
   if test=='stale': fe['QR_TEST_CAMERA_LOSS_AFTER']='30'
   flight=subprocess.Popen([sys.executable,'src/flight.py'],env=fe,stdout=fl,stderr=subprocess.STDOUT)
   start=time.monotonic(); removed=False
   while flight.poll() is None:
    lines=(P/'logs/flight.jsonl').read_text().splitlines()[before:]
    states=[json.loads(x).get('state') for x in lines]
    if test=='qr_loss' and not removed and 'alçalma' in states:
     r=subprocess.run(['gz','service','-s','/world/qr_test/remove','--reqtype','gz.msgs.Entity','--reptype','gz.msgs.Boolean','--timeout','3000','--req','name: "qr_pad" type: MODEL'],env=env,capture_output=True,text=True,timeout=5)
     if r.returncode or 'true' not in r.stdout: raise RuntimeError('QR kaldırma doğrulanamadı: '+r.stdout+r.stderr)
     removed=True
    if time.monotonic()-start>120: raise TimeoutError('Arıza testi süresi doldu')
    time.sleep(.2)
   lines=(P/'logs/flight.jsonl').read_text().splitlines()[before:]; records=[json.loads(x) for x in lines]; states=[x.get('state') for x in records]
   recovery='güvenli iniş doğrulandı' in states and 'tamamlandı' not in states
   reason=[x.get('reason') for x in records if x.get('state')=='iptal/hata']
   results.append(dict(test=test,reached_descent='alçalma' in states,exit_code=flight.returncode,recovery_verified=recovery,qr_removed=removed,reason=reason))
   (P/'logs'/('stale_test.json' if tests==['stale'] else 'failure_tests.json')).write_text(json.dumps(results,indent=2,ensure_ascii=False)); print(results[-1],flush=True)
   if not recovery: raise RuntimeError('Güvenli geri dönüş testi geçmedi')
  finally:
   if flight and flight.poll() is None:
    (P/'logs/cancel_requested').touch()
    try: flight.wait(timeout=70)
    except subprocess.TimeoutExpired: raise RuntimeError('İniş doğrulanamadı; simülasyon otomatik kapatılmadı')
   if sim and sim.poll() is None:
    sim.send_signal(signal.SIGTERM)
    try: sim.wait(timeout=15)
    except subprocess.TimeoutExpired: raise RuntimeError('Supervisor durmadı')
