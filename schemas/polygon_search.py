import geojson_pydantic
from pydantic import validator, BaseModel
import datetime
from typing import List, Dict

class PolygonSearch(BaseModel):
    fetch: int = 10
    skip: int = 0
    institucion: str = None
    nombre: str = None
    descripcion: str = None
    extension: str = None
    espg: str = None
    fecha_inicio: str = None
    fecha_fin: str = None
    url: str = None
    keyword: str = None
    topic_category: str = None

    @validator('fecha_inicio', 'fecha_fin', each_item=True)
    def dates_must_be_valid(cls, value):
        if value:
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError("fecha_inicio y fecha_fin deben ser del formato YYYY-MM-DD")
        return value