from bson.objectid import ObjectId
admins = [
    {
        "_id": ObjectId("6390fbdf7f7c68e37cfa72b5"),
        "id": ObjectId("6390fbdf7f7c68e37cfa72b3"),
        "institucion_id": "638e0054212b2fe7c2d445e7",
        "nombre": "Nikola Tesla",
        "email": "nikola.tesla@sansano.usm.cl",
        "rut": "19611109-3",
        "celular": "+569 12345678",
        "area_trabajo": "Ciencias de la ingeniería",
        "is_superadmin": True,
        "password": "$2b$12$qheAs2ecC62q2j8DDJS1QOBjomOVEhiopKsSKBz0gIFl3.IwY/FNm",
        "created_at": {"$date": "2022-12-07T20:47:27.898Z"},
        "institucion": "Universidad Técnica Federico Santa María",
    },
]

institution_documents = [
    {
        "_id": ObjectId("644eadf21ae559eaf38c34ad"),
        "id": ObjectId("644eadf21ae559eaf38c34ab"),
        "nombre": "Universidad Técnica Federico Santa María",
        "descripcion": "Universidad Chilena enfocada en las ciencias de la ingeniería",
        "sitio_web": "https://www.usm.cl/",
        "email": "informaciones.rrhh@usm.cl",
        "telefono": "+56 9 3437 3107",
        "direccion": "Av. España 1680",
        "area_trabajo": "Arquitectura",
        "tipo_institucion": "Publica",
        "created_at": {"$date": "2023-04-30T18:05:38.815Z"},
    },
]

