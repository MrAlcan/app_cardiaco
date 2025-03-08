from app.models.frecuencia import Frecuencia
from app.models.clasificacion import Clasificacion
from app.serializer.serializadorUniversal import SerializadorUniversal
from app.config.extensiones import db
from datetime import datetime
from sqlalchemy import func, extract

class ServiciosFrecuencia():
    def crear(paciente, ritmo, clasificacion, valor, estado=None):
        frecuencia = Frecuencia(paciente, ritmo, clasificacion, valor, estado)

        db.session.add(frecuencia)
        db.session.commit()

        return True
    
    def modificar(id, clasificacion):
        frecuencia = Frecuencia.query.get(id)
        frecuencia.id_clasificacion = clasificacion
        db.session.commit()
        return frecuencia
    
    def obtener_todos():

        frecuencias = Frecuencia.query.all()

        datos_req = ['id_frecuencia','id_paciente', 'ritmo', 'id_clasificacion', 'valor', 'id_estado', 'activo', 'fecha']

        respuesta = SerializadorUniversal.serializar_lista(frecuencias, datos_req)

        return respuesta
    
    def obtener_por_paciente(paciente):
        frecuencias = Frecuencia.query.filter_by(id_paciente = paciente)

        datos_req = ['id_frecuencia','id_paciente', 'ritmo', 'id_clasificacion', 'valor', 'id_estado', 'activo', 'fecha']

        respuesta = SerializadorUniversal.serializar_lista(frecuencias, datos_req)

        return respuesta
    
    def obtener_por_fecha(fecha):
        frecuencias = Frecuencia.query.filter_by(fecha = fecha)

        respuestas_mod = []

        for fila in frecuencias:
            fecha_reg = fila.fecha.strftime('%Y-%m-%d')
            if fecha == fecha_reg:
                respuestas_mod.append(fila)

        datos_req = ['id_frecuencia','id_paciente', 'ritmo', 'id_clasificacion', 'valor', 'id_estado', 'activo', 'fecha']

        respuesta = SerializadorUniversal.serializar_lista(respuestas_mod, datos_req)

        return respuesta
    
    def obtener_por_paciente_fecha(paciente, fecha):
        frecuencias = Frecuencia.query.filter_by(id_paciente = paciente, fecha = fecha)
        
        respuestas_mod = []

        for fila in frecuencias:
            fecha_reg = fila.fecha.strftime('%Y-%m-%d')
            if fecha == fecha_reg:
                respuestas_mod.append(fila)

        datos_req = ['id_frecuencia','id_paciente', 'ritmo', 'id_clasificacion', 'valor', 'id_estado', 'activo', 'fecha']

        respuesta = SerializadorUniversal.serializar_lista(respuestas_mod, datos_req)

        return respuesta

    def obtener_frecuencias_por_paciente_y_fecha(id_paciente, fecha):
        # Convertir la fecha a formato datetime si no lo es
        fecha = str(fecha)
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')  # Suponiendo que la fecha es un string con formato YYYY-MM-DD

        # Realizar la consulta
        frecuencias = db.session.query(
            Frecuencia.id_frecuencia,
            Frecuencia.ritmo,
            Frecuencia.valor,
            Frecuencia.fecha,
            Clasificacion.nombre.label('clasificacion')
        ).join(Clasificacion, Frecuencia.id_clasificacion == Clasificacion.id_clasificacion) \
        .filter(Frecuencia.id_paciente == id_paciente) \
        .filter(func.date(Frecuencia.fecha) == func.date(fecha_obj)) \
        .all()

        # Retornar los resultados como lista de diccionarios para facilidad
        resultados = []
        for frecuencia in frecuencias:
            resultados.append({
                'id_frecuencia': frecuencia.id_frecuencia,
                'ritmo': frecuencia.ritmo,
                'valor': frecuencia.valor,
                'fecha': frecuencia.fecha,
                'clasificacion': frecuencia.clasificacion
            })

        return resultados
    

    def obtener_frecuencias_por_paciente_mes_actual(id_paciente):
        # Obtener el año y mes actuales
        current_year_month = datetime.now().strftime('%Y-%m')  # Año y mes en formato 'YYYY-MM'
        
        # Realizar la consulta
        frecuencias = db.session.query(
            Frecuencia.id_frecuencia,
            Frecuencia.ritmo,
            Frecuencia.valor,
            Frecuencia.fecha,
            Clasificacion.nombre,
            Clasificacion.id_clasificacion
        ).join(Clasificacion, Frecuencia.id_clasificacion == Clasificacion.id_clasificacion) \
        .filter(Frecuencia.id_paciente == id_paciente) \
        .filter(extract('year', Frecuencia.fecha) == datetime.now().year) \
        .filter(extract('month', Frecuencia.fecha) == datetime.now().month) \
        .all()

        # Retornar los resultados como lista de diccionarios
        resultados = []
        for frecuencia in frecuencias:
            resultados.append({
                'id_frecuencia': frecuencia.id_frecuencia,
                'ritmo': frecuencia.ritmo,
                'valor': frecuencia.valor,
                'fecha': frecuencia.fecha,
                'clasificacion': frecuencia.nombre,
                'id_clasificacion': frecuencia.id_clasificacion
            })

        return resultados