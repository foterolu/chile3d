from fastapi import FastAPI, Request
import geojson
import laspy





app = FastAPI()

@app.get('/')

def read_root():
    
    return {"Hello": "World"}

@app.post('/geojson')
async def read_geojson(request: Request):
    target = 'PNOA_2010_Lote7_CYL-MAD_438-4476_ORT-CLA-CIR.laz'
    body = await request.body()
    gj = geojson.loads(body)
    if gj.is_valid:
        for features in gj['features']:
           
            
            with laspy.open(target, mode = "r") as data:
                print(str(data.header.vlrs[-1]))

        return {"status": "ok"}
    else:
        return {"status": "error, bad geojson file"}
  


