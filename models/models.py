from pydantinc import BaseModel
from datetime import datetime,date


class Admin(BaseModel):
    id = int
    institucion_id = int
    nombre = str
    email = str
    rut = str
    celular = str
    insitucion = str
    area_trabajo = str
    is_superadmin = bool
    password = str

