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

class Admin_institucion(BaseModel):
    admin_id : PyObjectId = Field(default_factory=PyObjectId, alias="id")
    institucion_id : str
    nombre : str
    insitucion : str
    area_trabajo : str

class Archivo(BaseModel):
    id : PyObjectId = Field(default_factory=PyObjectId, alias="id")
    admin : Admin_institucion
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

class Archivo_edit(BaseModel):
    nombre :str
    descripcion :str
    keyword :str
    topic_category :str
    institucion :str
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
class Institucion_Editar(BaseModel):
    nombre : str
    descripcion : str
    sitio_web : str
    email : str
    telefono : str
    direccion : str
    area_trabajo : str
    tipo_institucion : str
