from pydantic import BaseModel,Field,json
from datetime import datetime,date
from bson import ObjectId
import geojson_pydantic

json.ENCODERS_BY_TYPE[ObjectId]=str


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")
class Admin(BaseModel):
    id : PyObjectId = Field(default_factory=PyObjectId, alias="id")
    institucion_id : str
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
    id : PyObjectId = Field(default_factory=PyObjectId, alias="id")
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

class Institucion(BaseModel):
    id : PyObjectId = Field(default_factory=PyObjectId, alias="id")
    nombre : str
    descripcion : str
    sitio_web : str
    email : str
    telefono : str
    direccion : str
    area_trabajo : str
    tipo_institucion : str
    created_at = datetime.utcnow()

data = {
   "institucion_id" : "638e0054212b2fe7c2d445e7",
    "nombre" : "Nicola Tesla",
    "email" : "nicola.tesla@sansano.usm.cl",
    "rut" : "19732182-9",
    "celular" : "+569 12345678",
    "insitucion" : "Universidad Técnica Federico Santa María",
    "area_trabajo" : "Ciencias de la ingeneria",
    "is_superadmin" : False,
    "password" : "chile3d",
   }