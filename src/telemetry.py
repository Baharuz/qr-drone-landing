"""Salt okunur yerel SITL bağlantı testi; uçuş komutu göndermez."""
import asyncio,json,socket,os
from mavsdk import System
async def main():
 port=int(os.environ.get('QR_SITL_PORT','14540'))
 if port not in (14540,14541): raise ValueError('Yalnız yerel SITL portları')
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
 try: s.bind(('0.0.0.0',port))
 finally: s.close()
 drone=System(port=50051 if port==14540 else 50052); result={'connected':False}
 try:
  await asyncio.wait_for(drone.connect(system_address=f'udpin://0.0.0.0:{port}'),15)
  async def connected():
   async for state in drone.core.connection_state():
    if state.is_connected: return
  await asyncio.wait_for(connected(),15); result['connected']=True
  async def sample(name,stream):
   try: result[name]=str(await asyncio.wait_for(anext(stream),8))
   except TimeoutError: result[name]='TIMEOUT'
   finally: await stream.aclose()
  await asyncio.gather(sample('position',drone.telemetry.position()),sample('local_ned',drone.telemetry.position_velocity_ned()),sample('health',drone.telemetry.health()),sample('armed',drone.telemetry.armed()))
 finally:
  drone._stop_mavsdk_server(); drone._server_process=None
  print(json.dumps(result,indent=2))
 if not result['connected'] or result.get('local_ned')=='TIMEOUT': raise SystemExit(2)
if __name__=='__main__': asyncio.run(main())
