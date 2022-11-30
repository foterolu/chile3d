from pydantic import BaseModel
from datetime import datetime,date
import geojson_pydantic


class Admin(BaseModel):
    id : int
    institucion_id : int
    nombre : str
    email : str
    rut : str
    celular : str
    insitucion : str
    area_trabajo : str
    is_superadmin : bool = False
    password : str
    created_at = datetime.utcnow()

class Archivo(BaseModel):
    admin_id :int
    nombre :str
    descripcion :str
    extension :str
    espg :str
    fecha_creacion :datetime
    fecha_modificacion :datetime
    minx :float
    miny :float
    maxx :float
    maxy :float
    url :str
    keyword :str
    topic_category :str
    institucion :str
    cantidad_descargas :int


