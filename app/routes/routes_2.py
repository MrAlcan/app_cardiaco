#SERVICIOS
from app.services.serviciosAlerta import ServiciosAlerta
from app.services.serviciosClasificacion import ServiciosClasificacion
from app.services.serviciosFrecuencia import ServiciosFrecuencia
from app.services.serviciosPaciente import ServiciosPaciente
from app.services.serviciosRol import ServiciosRol
from app.services.serviciosSonido import ServiciosSonido
from app.services.serviciosUsuario import ServiciosUsuario
#

from flask import Blueprint, render_template, request, jsonify
 
#from app.routes.conexion import db, cursor
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
 
from flask import session
from flask import jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import re
routes = Blueprint("routes", __name__)

from functools import wraps
from flask import redirect, url_for, session
import requests
import os
import firebase_admin
from google.oauth2 import service_account
import google.auth.transport.requests


services_account_file = os.path.join(os.getcwd(), 'app', 'routes', "freqcard-firebase-adminsdk-fbsvc-9423d81a63.json")
#credentials = service_account.Credentials.from_service_account_file(services_account_file, scopes="https://www.googleapis.com/auth/cloud-plataform") # https://www.googleapis.com/auth/firebase.messaging
#default_app = firebase_admin.initialize_app()

def _get_access_token():

    credentials = service_account.Credentials.from_service_account_file(services_account_file, scopes=["https://www.googleapis.com/auth/firebase.messaging"])
    
    request = google.auth.transport.requests.Request()
    #print('-*-'*100)
    #print(request)
    credentials.refresh(request)
    return credentials.token

FCM_URL = "https://fcm.googleapis.com/v1/projects/freqcard/messages:send"

def send_fcm_notification(device_token, title, body, data=None):
    headers = {
        "Authorization": 'Bearer ' + _get_access_token(),
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "token" : device_token,
            "notification": {
                "title": title,
                "body": body
            }#,
            #"data": data or {}
        }
    }
    try:
        response = requests.post(FCM_URL, headers=headers, json=payload)
        print('/*/*'*100)
        print(response)
        print(response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        # Captura cualquier error relacionado con la solicitud (como problemas de red o problemas con la URL)
        print(f"Error en la solicitud: {e}")
        return {"error": "Error en la solicitud"}

    except ValueError as e:
        # Captura cualquier error relacionado con la conversión de la respuesta a JSON
        print(f"Error al convertir la respuesta a JSON: {e}")
        return {"error": "Error al procesar la respuesta JSON"}

    except Exception as e:
        # Captura cualquier otro error no esperado
        print(f"Ha ocurrido un error inesperado: {e}")
        return {"error": "Error inesperado"}

 

from flask import Flask, session, redirect, url_for, jsonify
def login_requerido(f):
    @wraps(f)
    def check_login(*args, **kwargs):
        if "usuario_id" not in session:  
            return redirect(url_for("login"))  
        return f(*args, **kwargs)   
    return check_login


@routes.route("/dashboard")
@login_requerido
def inicio():
    username = session.get('username', 'Usuario Invitado')

    total_pacientes = ServiciosPaciente.obtener_todos()
    if not total_pacientes:
        total_pacientes = 0
    else:
        total_pacientes = len(total_pacientes)
     
    '''cursor.execute("SELECT COUNT(*) AS total FROM paciente")
    total_pacientes = cursor.fetchone()['total']  # Obtén el valor del total'''

    total_usuarios = ServiciosUsuario.obtener_todos()
    if not total_usuarios:
        total_usuarios = 0
    else:
        total_usuarios = len(total_usuarios)
    

    '''cursor.execute("SELECT COUNT(*) AS total FROM usuario")
    total_usuarios = cursor.fetchone()['total']'''
    session['total_pacientes'] = total_pacientes
    session['total_usuarios'] = total_usuarios
 
    username = session.get('username', 'Usuario Invitado')
   
    return render_template("index.html", username=username, total_usuarios=total_usuarios, total_pacientes=total_pacientes)
   

@routes.route("/")
def pagina_inicio():
    return render_template("inicio.html")

@routes.route("/login", methods=["GET"])
def login():
    
    return render_template("login.html") 

 



 

@routes.route("/cerrar_sesion", methods=["POST"])
def cerrar_sesion():
    try:
        session.pop("usuario_id", None)
        return jsonify({"mensaje": "Cierre de sesión exitoso", "redirect": "/login"}), 200

    except Exception as e:
        return jsonify({"mensaje": f"Error en el cierre de sesión: {str(e)}"}), 500


@routes.route("/verificar_login", methods=["POST"])
def verificar_login():
    try:
        datos = request.get_json()
        correo = datos.get("correo")
        password = datos.get("password")
        if not correo or not password:
            return jsonify({"mensaje": "Faltan datos"}), 400
        usuario = ServiciosUsuario.obtener_por_correo(correo)
        '''cursor.execute("SELECT id_usuario, password, correo FROM usuario WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()'''
    
        if not usuario:
            return jsonify({"mensaje": "Correo o contraseña incorrectos"}), 401

         
        if usuario:  
            session["usuario_id"] = usuario["id_usuario"]
            
            return jsonify({"mensaje": "Inicio de sesión exitoso", "redirect": "/dashboard"}), 200

        session['username'] = usuario["nombre"]
        return jsonify({"mensaje": "Correo o contraseña incorrectos"}), 401

    except Exception as e:
        print(e)   
        return jsonify({"mensaje": "Error en el inicio de sesión"}), 500


# ------------------- USUARIOS -------------------
@routes.route("/usuarios")
@login_requerido
def usuarios():

    usuarios = ServiciosUsuario.obtener_todos()


    '''cursor.execute("SELECT u.id_usuario, u.nombre, u.correo, u.activo, u.carnet, u.telefono, r.nombre AS rol FROM usuario u JOIN roles r ON u.id_rol = r.id_rol ")
    usuarios = cursor.fetchall()'''

    roles = ServiciosRol.obtener_todos()


    '''cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()'''


    username = session.get('username', 'Usuario Invitado')
    total_pacientes = session.get('total_pacientes')
    total_usuarios = session.get('total_usuarios')
    return render_template("usuario.html", usuarios=usuarios, roles=roles,username=username, total_pacientes= total_pacientes, total_usuarios= total_usuarios)

 

# Ruta para agregar un nuevo usuario
@routes.route("/agregar_usuario", methods=["POST"])
@login_requerido
def agregar_usuario():
    
        datos = request.get_json()
        
        nombre = datos.get("nombre")
        correo = datos.get("correo")
        carnet = datos.get("carnet")
        telefono = datos.get("telefono")
        password = datos.get("password")
        id_rol = datos.get("rol")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):    
            return jsonify({"mensaje": "Correo electrónico inválido"}), 400

        # Generar el hash de la contraseña antes de almacenarla
        
        usuario_nuevo = ServiciosUsuario.crear(nombre, correo, carnet, telefono, password, id_rol)

        # Insertar el nuevo usuario con la contraseña hasheada
        '''cursor.execute(
            """
            INSERT INTO usuario (nombre, correo, carnet, telefono, password, id_rol) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """, 
            (nombre, correo, carnet, telefono, password, id_rol)
        )
        db.commit()'''

        if usuario_nuevo:

            return jsonify({"mensaje": "Usuario agregado con éxito", "redirect": "/usuarios"}), 200
        else:
            return jsonify({"mensaje": "Error al agregar usuario"}), 500
        
@routes.route("/user/crear_usuario", methods=["POST"])
def crear_usuario_app():
    
        datos = request.get_json()

        print('/*/'*100)
        print(datos)
        
        carnet = datos.get("id")
        nombre = datos.get("name")
        edad = int(datos.get("age"))
        telefono = datos.get("rate")

        hoy = datetime.today()

        # Restar los años de la edad a la fecha de hoy
        fecha_nacimiento = hoy.replace(year=hoy.year - edad)

        # Verificar si ya pasó el cumpleaños este año
        # Si la fecha de nacimiento es después de la fecha actual, restamos un año adicional
        if hoy.month < fecha_nacimiento.month or (hoy.month == fecha_nacimiento.month and hoy.day < fecha_nacimiento.day):
            fecha_nacimiento = fecha_nacimiento.replace(year=hoy.year - edad - 1)

        fecha_nacimiento = fecha_nacimiento.strftime('%Y-%m-%d')

        paciente = ServiciosPaciente.crear(1, fecha_nacimiento, 0, nombre, carnet)

        

        '''if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):    
            return jsonify({"mensaje": "Correo electrónico inválido"}), 400

        # Generar el hash de la contraseña antes de almacenarla
        
        usuario_nuevo = ServiciosUsuario.crear(nombre, correo, carnet, telefono, password, id_rol)'''

        # Insertar el nuevo usuario con la contraseña hasheada
        '''cursor.execute(
            """
            INSERT INTO usuario (nombre, correo, carnet, telefono, password, id_rol) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """, 
            (nombre, correo, carnet, telefono, password, id_rol)
        )
        db.commit()'''

        if paciente:

            return jsonify({"mensaje": "Usuario agregado con éxito", "redirect": "/usuarios"}), 200
        else:
            return jsonify({"mensaje": "Error al agregar usuario"}), 500





@routes.route("/editar_usuario", methods=["POST"])
@login_requerido
def editar_usuario():
    datos = request.get_json()
    id_usuario = datos.get("id")
    nombre = datos.get("nombre")
    correo = datos.get("correo")
    carnet = datos.get("carnet")
    telefono = datos.get("telefono")
    
    if not all([id_usuario, nombre, correo, carnet, telefono]):
        return jsonify({"mensaje": "Faltan datos"}), 400
    
    usuario_editado = ServiciosUsuario.modificar(id_usuario, nombre=nombre, correo=correo, carnet=carnet, telefono=telefono)

     
    '''cursor.execute("""
        UPDATE usuario
        SET nombre = %s, correo = %s, carnet = %s, telefono = %s
        WHERE id_usuario = %s
    """, (nombre, correo, carnet, telefono, id_usuario))

    db.commit()'''

    return jsonify({"mensaje": "Usuario actualizado con éxito", "redirect": "/usuarios"})


@routes.route("/eliminar_usuario/<int:id_usuario>", methods=["POST"])
@login_requerido
def eliminar_usuario(id_usuario):

    usuario = ServiciosUsuario.obtener_id(id_usuario)

    '''cursor.execute("SELECT activo FROM usuario WHERE id_usuario = %s", (id_usuario,))
    usuario = cursor.fetchone()'''

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    
    estado_actual = usuario['activo']

    if estado_actual == 1:
        usuario_m = ServiciosUsuario.desactivar(id_usuario)
        mensaje = "Usuario desactivado con éxito"
    else:
        usuario_m = ServiciosUsuario.activar(id_usuario)
        mensaje = "Usuario activado con éxito"
    


    '''estado_actual = usuario['activo']
    nuevo_estado = 0 if estado_actual == 1 else 1   
    cursor.execute("UPDATE usuario SET activo = %s WHERE id_usuario = %s", (nuevo_estado, id_usuario))
    db.commit()'''

    '''if nuevo_estado == 0:
        mensaje = "Usuario desactivado con éxito"
    else:
        mensaje = "Usuario activado con éxito"'''

    return jsonify({"mensaje": mensaje, "redirect": "/usuarios"})

# ------------------- PACIENTES -------------------


@routes.route("/pacientes")
@login_requerido
def pacientes():

    pacientes_lista = ServiciosPaciente.obtener_pacientes_con_encargado()

    '''cursor.execute("""
        SELECT p.id_paciente, p.fecha_nacimiento, p.frecuencias, p.tasa, p.token_acceso, p.activo, p.nombre, p.carnet, p.diagnostico,
               u.nombre AS encargado, u.correo, u.telefono , u.id_usuario
        FROM paciente p
        JOIN usuario u ON p.id_encargado = u.id_usuario
    """)
    pacientes_lista = cursor.fetchall()  '''

    encargados_lista = ServiciosUsuario.obtener_usuarios_con_rol(2)

    '''cursor.execute("""
        SELECT u.id_usuario, u.nombre, u.correo, u.carnet, u.telefono, r.nombre AS rol
        FROM usuario u
        JOIN roles r ON u.id_rol = r.id_rol
        WHERE u.id_rol = 2
    """)
    encargados_lista = cursor.fetchall()  '''
    pacientes_con_edad = []
    today = datetime.today()

    for paciente in pacientes_lista:
        fecha_nacimiento = paciente['fecha_nacimiento']
        # Calcular la edad
        edad = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        paciente['edad'] = edad  
        pacientes_con_edad.append(paciente)
    total_pacientes = session.get('total_pacientes')
    total_usuarios = session.get('total_usuarios')

    username = session.get('username', 'Usuario Invitado')
    return render_template("pacientes.html", pacientes=pacientes_con_edad, encargados=encargados_lista,username=username, total_pacientes= total_pacientes, total_usuarios=total_usuarios)

@routes.route("/agregar_paciente", methods=["POST"])
@login_requerido
def agregar_paciente():
    datos = request.get_json()
    id_encargado = datos.get("id_encargado")
    fecha_nacimiento = datos.get("fecha_nacimiento")
    tasa = datos.get("tasa")
    token_acceso = datos.get("token_acceso")
    nombre = datos.get("nombre") 
    carnet = datos.get("carnet") 
    diagnostico = datos.get("diagnostico")  

    encargado = ServiciosUsuario.obtener_id(id_encargado)

    if not encargado:
        return jsonify({"mensaje": "El encargado no existe"}), 400
    '''cursor.execute("SELECT id_usuario FROM usuario WHERE id_usuario = %s", (id_encargado,))
    if not cursor.fetchone():
        return jsonify({"mensaje": "El encargado no existe"}), 400'''
    
    nuevo_paciente = ServiciosPaciente.crear(id_encargado, fecha_nacimiento, tasa, nombre, carnet, diagnostico)

    '''cursor.execute("""
        INSERT INTO paciente (id_encargado, fecha_nacimiento, tasa, token_acceso, nombre, carnet, diagnostico)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (id_encargado, fecha_nacimiento, tasa, token_acceso, nombre, carnet, diagnostico))
    db.commit()'''

    return jsonify({"mensaje": "Paciente agregado con éxito", "redirect": "/pacientes"})


@routes.route("/editar_paciente", methods=["POST"])
@login_requerido
def editar_paciente():
    datos = request.get_json()
    id_paciente = datos.get("id")
    id_encargado = datos.get("encargado")
    fecha_nacimiento = datos.get("fecha_nacimiento")
    tasa = datos.get("tasa")
    token_acceso = datos.get("token_acceso")
    nombre = datos.get("nombre")  
    carnet = datos.get("carnet")  
    diagnostico = datos.get("diagnostico") 

    encargado = ServiciosUsuario.obtener_id(id_encargado)

    '''cursor.execute("SELECT id_usuario FROM usuario WHERE id_usuario = %s", (id_encargado,))
    if not cursor.fetchone():
        return jsonify({"mensaje": "El encargado no existe"}), 400'''
    
    if not encargado:
        return jsonify({"mensaje": "El encargado no existe"}), 400
    
    paciente = ServiciosPaciente.modificar(id_paciente, encargado=id_encargado, nacimiento=fecha_nacimiento, tasa=tasa, nombre=nombre, carnet=carnet, diagnostico=diagnostico)

    '''cursor.execute("""
        UPDATE paciente
        SET id_encargado = %s, fecha_nacimiento = %s, tasa = %s, token_acceso = %s, nombre = %s, carnet = %s, diagnostico = %s
        WHERE id_paciente = %s
    """, (id_encargado, fecha_nacimiento, tasa, token_acceso, nombre, carnet, diagnostico, id_paciente))
    db.commit()'''

    return jsonify({"mensaje": "Paciente actualizado con éxito", "redirect": "/pacientes"})


@routes.route("/eliminar_paciente/<int:id_paciente>", methods=["POST"])
@login_requerido
def eliminar_paciente(id_paciente):

    paciente = ServiciosPaciente.obtener_por_id(id_paciente)

    '''cursor.execute("SELECT activo FROM paciente WHERE id_paciente = %s", (id_paciente,))
    paciente = cursor.fetchone()'''

    if not paciente:
        return jsonify({"mensaje": "Paciente no encontrado"}), 404
    


    estado_actual = paciente['activo']

    '''if estado_actual == 1:


    nuevo_estado = 0 if estado_actual == 1 else 1   
    cursor.execute("UPDATE paciente SET activo = %s WHERE id_paciente = %s", (nuevo_estado, id_paciente))
    db.commit()'''

    if estado_actual == 1:
        paciente = ServiciosPaciente.desactivar(id_paciente)
        mensaje = "Paciente desactivado con éxito"
    else:
        paciente = ServiciosPaciente.activar(id_paciente)
        mensaje = "Paciente activado con éxito"

    return jsonify({"mensaje": mensaje, "redirect": "/pacientes"})

 

@routes.route("/cambiar_contrasena/<int:id_usuario>", methods=["POST"])
@login_requerido
def cambiar_contrasena(id_usuario):
    datos = request.get_json()
    nueva_contrasena = datos.get("nuevaContrasena")

    if not nueva_contrasena:
        return jsonify({"mensaje": "La nueva contraseña es requerida"}), 400

  
    #contrasena_hasheada = generate_password_hash(nueva_contrasena)

    usuario = ServiciosUsuario.modificar_contrasena(id_usuario, nueva_contrasena)

    '''cursor.execute("""
        UPDATE usuario
        SET password = %s
        WHERE id_usuario = %s
    """, (contrasena_hasheada, id_usuario)) 
    db.commit()'''

    return jsonify({"mensaje": "Contraseña cambiada con éxito", "redirect": "/usuarios"})


# ------------------- INFORMES -------------------
@routes.route("/informes")
@login_requerido
def informes():
    username = session.get('username', 'Usuario Invitado')
    total_pacientes = session.get('total_pacientes')
    total_usuarios = session.get('total_usuarios')
    return render_template("informes.html", username=username, total_pacientes= total_pacientes, total_usuarios=total_usuarios)
 
  
import locale
 
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

@routes.route("/buscar_frecuencia", methods=["POST"])
@login_requerido
def buscar_frecuencia():
    datos = request.get_json()
    paciente_codigo = datos.get("paciente")
    fecha = datos.get("fecha")
    
    if not paciente_codigo or not fecha:
        return jsonify({"mensaje": "Paciente y fecha son requeridos."}), 400

    try:
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"mensaje": "Formato de fecha incorrecto, debe ser 'YYYY-MM-DD'."}), 400
    
    paciente = ServiciosPaciente.obtener_por_carnet(paciente_codigo)

    '''cursor.execute("""
        SELECT id_paciente, nombre
        FROM paciente
        WHERE carnet = %s
    """, (paciente_codigo,))
    
    paciente = cursor.fetchone()'''

    if paciente is None:
        return jsonify({"mensaje": "Paciente no encontrado con ese código de carnet."}), 404

    if isinstance(paciente, dict):
        id_paciente = paciente['id_paciente']
        nombre_paciente = paciente['nombre']
    else:
        id_paciente = paciente[0]
        nombre_paciente = paciente[1]

    frecuencias = ServiciosFrecuencia.obtener_frecuencias_por_paciente_y_fecha(id_paciente, fecha)

    '''cursor.fetchall()   

    cursor.execute("""
        SELECT f.id_frecuencia, f.ritmo, f.valor, f.fecha, c.nombre AS clasificacion
        FROM frecuencias f
        JOIN clasificacion c ON f.id_clasificacion = c.id_clasificacion
        WHERE f.id_paciente = %s AND DATE(f.fecha) = %s
    """, (id_paciente, fecha))

    frecuencias = cursor.fetchall()'''
    print(frecuencias)
    if not frecuencias:
        return jsonify({"mensaje": "No se encontraron registros de frecuencia."}), 404
    
    frecuencias_formateadas = []
    for frecuencia in frecuencias:
        fecha_formateada = frecuencia['fecha'].strftime("%a, %d %b %Y %H:%M:%S")
        frecuencia['fecha'] = fecha_formateada 
        frecuencia['nombre_paciente'] = nombre_paciente 
        frecuencias_formateadas.append(frecuencia)

    return jsonify({"frecuencias": frecuencias_formateadas})


# ------------------- REPORTES -------------------
@routes.route("/reportes")
@login_requerido
def reportes():
    total_pacientes = session.get('total_pacientes')
    total_usuarios = session.get('total_usuarios')
    username = session.get('username', 'Usuario Invitado')
    return render_template("reportes.html", username=username, total_pacientes=total_pacientes, total_usuarios=total_usuarios)
 
@routes.route('/generar_reporte_mensual', methods=['POST'])
@login_requerido
def generar_reporte_mensual():
    paciente_codigo = request.form.get('paciente')
    
    if not paciente_codigo:
        return jsonify({"mensaje": "Código de paciente es requerido."}), 400
    
    paciente = ServiciosPaciente.obtener_por_carnet(paciente_codigo)

    '''cursor.execute("""
        SELECT id_paciente, nombre
        FROM paciente
        WHERE carnet = %s
    """, (paciente_codigo,))
    
    paciente = cursor.fetchone()'''

    if paciente is None:
        return jsonify({"mensaje": "Paciente no encontrado con ese código de carnet."}), 404

    if isinstance(paciente, dict):
        id_paciente = paciente['id_paciente']
        nombre_paciente = paciente['nombre']
    else:
        id_paciente = paciente[0]
        nombre_paciente = paciente[1]

    #cursor.fetchall()

    frecuencias = ServiciosFrecuencia.obtener_frecuencias_por_paciente_mes_actual(id_paciente)



    '''cursor.execute("""
        SELECT f.id_frecuencia, f.ritmo, f.valor, f.fecha, c.nombre, c.id_clasificacion
        FROM frecuencias f
        JOIN clasificacion c ON f.id_clasificacion = c.id_clasificacion
        WHERE f.id_paciente = %s
        AND DATE_FORMAT(f.fecha, '%%Y-%%m') = DATE_FORMAT(NOW(), '%%Y-%%m')
    """, (id_paciente,))
    
    frecuencias = cursor.fetchall()'''
    fecha_actual = datetime.now()
    meses = [(fecha_actual - timedelta(days=30 * i)).strftime("%Y-%m") for i in range(5)]
    data = {mes: {"bocinas": 0, "ladridos": 0, "petardos": 0} for mes in meses}
    
    for frecuencia in frecuencias:
        if isinstance(frecuencia, dict):
            fecha = frecuencia['fecha']  
            id_clasificacion = frecuencia['id_clasificacion']
            valor = frecuencia['valor']
        else:
            fecha = frecuencia[3]
            id_clasificacion = frecuencia[5]
            valor = frecuencia[2]
        
        period = fecha.strftime("%Y-%m") if isinstance(fecha, datetime) else fecha
        
        if id_clasificacion in [1, 2, 3]:   
            categoria = "bocinas"
        elif id_clasificacion in [4, 5, 6]:   
            categoria = "ladridos"
        elif id_clasificacion in [7, 8, 9]:  
            categoria = "petardos"
        else:
            continue
        
        if period in data:
            data[period][categoria] += valor

    resultado_final = []
    for mes in meses:
        resultado_final.append({
            "period": mes,
            "bocinas": data[mes]["bocinas"],
            "ladridos": data[mes]["ladridos"],
            "petardos": data[mes]["petardos"]
        })
    print(resultado_final)
    return jsonify({"frecuencias": resultado_final})

@routes.route('/generar_reporte_diario', methods=['POST'])
@login_requerido
def generar_reporte_diario():
    paciente_codigo = request.form.get('paciente_dia')
    fecha_dia = request.form.get('fecha_dia')
    
    if not paciente_codigo or not fecha_dia:
        return jsonify({"mensaje": "Código de paciente y fecha son requeridos."}), 400
    
    try:
        fecha_dia = datetime.strptime(fecha_dia, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"mensaje": "Formato de fecha incorrecto."}), 400
    
    paciente = ServiciosPaciente.obtener_por_carnet(paciente_codigo)

    id_pac = paciente['id_paciente']
    
    frecuencias = ServiciosFrecuencia.obtener_por_paciente_fecha(id_pac, fecha_dia)
 
    '''cursor.execute("""
        SELECT f.id_frecuencia, f.ritmo, f.valor, f.fecha, c.nombre AS clasificacion
        FROM frecuencias f
        JOIN clasificacion c ON f.id_clasificacion = c.id_clasificacion
        WHERE f.id_paciente = (SELECT id_paciente FROM paciente WHERE carnet = ?)
        AND DATE(f.fecha) = ?
    """, (paciente_codigo, fecha_dia))'''
    
    #frecuencias = cursor.fetchall()
    print('DEBUG')
    print(frecuencias)
    if not frecuencias:
        return jsonify({"mensaje": "No se encontraron registros de frecuencia."}), 404
    
    frecuencias_formateadas = []
    for frecuencia in frecuencias:
        fecha_formateada = frecuencia['fecha'] 
        frecuencias_formateadas.append({
            "id_frecuencia": frecuencia["id_frecuencia"],
            "ritmo": frecuencia["ritmo"],
            "valor": frecuencia["valor"],
            "fecha": fecha_formateada,
            "clasificacion": frecuencia["clasificacion"]
        })
    
    return jsonify({"frecuencias": frecuencias_formateadas})


# ------------------------------------------ -------------------------------------------------

@routes.route('/insertar_latido', methods=['POST'])
def set_latido():

    datos = request.get_json()
    id_user = datos.get('id_user')
    latido = float(datos.get('heart_rate'))
    fecha = datos.get('datetime')
    print(id_user) # ------------------------------------ POSIBLE CARNET
    #date_object = datetime.strptime(fecha, "%a %b %d %H:%M:%S GMT%z %Y")

    paciente = ServiciosPaciente.obtener_por_carnet(id_user)
    id_pac = paciente['id_paciente']

    frecuencia = ServiciosFrecuencia.crear(id_pac, 0, 10, latido)

    '''cursor.execute("""
        INSERT INTO latidos (id_paciente, latido)
        VALUES (%s, %s)
    """, (id_user, latido,))
    db.commit()'''

    if latido >=100.0:

        id_enc = paciente['id_encargado']

        usuario = ServiciosUsuario.obtener_id(id_enc)


        '''cursor.execute("""
            SELECT * FROM paciente WHERE carnet = %s
        """, (id_user,))
        control = cursor.fetchone()  '''

        if usuario:
            token_user = usuario['token']
            print('*/*/'*100)
            print(token_user)
            titulo = "Frecuencia Alta Detectada"
            cuerpo = f"Frecuencia detectada de {latido} bpm"
            result = send_fcm_notification(token_user, titulo, cuerpo)
            return jsonify(result), 200
        else:
            return jsonify({'message':'No hay token'}), 400



    return jsonify({'message': 'Registrado Satisfactoriamente'}), 200

@routes.route('/control/send_notificacions', methods=['POST'])
def send_not():
    datos = request.get_json()
    id_user = datos.get('id_user')
    title = datos.get('title')
    description = datos.get('description')
    print(id_user)

    paciente = ServiciosPaciente.obtener_por_carnet(id_user)

    

    '''cursor.execute("""
            SELECT * FROM paciente WHERE id_paciente = %s
        """, (id_user,))
    control = cursor.fetchone()  '''

    if paciente:
        id_pac = paciente['id_paciente']
        id_enc = paciente['id_encargado']

        usuario = ServiciosUsuario.obtener_id(id_enc)

        token_user = usuario['token']
        print('*/*/'*100)
        print(token_user)
        titulo = title
        cuerpo = description
        result = ''
        result = send_fcm_notification(token_user, titulo, cuerpo)
        return jsonify(result), 200
    else:
        return jsonify({'message':'No hay token'}), 200

    return jsonify({'message': 'Registrado Satisfactoriamente'}), 200

@routes.route('/insertar_tokens', methods=['POST'])
def set_tokens():
    datos = request.get_json()
    id_user = datos.get('id_user')
    print(id_user)
    token = datos.get('token')
    print('/*/'*50)
    print(id_user)
    print(token)

    paciente = ServiciosPaciente.obtener_por_carnet(id_user)

    id_enc = paciente['id_encargado']

    #usuario = ServiciosUsuario.obtener_por_carnet(id_user)

    #id_usuario = usuario['id_usuario']

    usuario = ServiciosUsuario.insertar_token(id_enc, token)

    '''cursor.execute("""
        UPDATE paciente
        SET token_acceso = %s
        WHERE carnet = %s
    """, (token, id_user, ))
    db.commit()'''

    
    return jsonify({'message': 'Registrado Satisfactoriamente'}), 200



@routes.route('/insertar_sonido', methods=['POST'])
def set_sonido():
    datos = request.get_json()
    id_user = datos.get('id_user')
    print(id_user)
    sonido = datos.get('sound')
    fecha = datos.get('datetime')

    clasificacion = 10

    if sonido == 'bocina' or sonido=='sirena':
        clasificacion = 4
    elif sonido == 'ladrido':
        clasificacion = 1
    elif sonido == 'petardo':
        clasificacion = 7

    print(fecha)
    fecha =fecha.replace('GMT', '').strip()

    sonid = ServiciosSonido.crear(id_user, sonido)

    if sonid:
        fecha_sonido = sonid.fecha
        frecuencia_cercana = ServiciosSonido.buscar_registro_cercano(fecha_sonido, id_user)
        if frecuencia_cercana:
            id_frecuecia = frecuencia_cercana['id_frecuencia']
            resultado = ServiciosFrecuencia.modificar(id_frecuecia, clasificacion)


    #date_object = datetime.strptime(fecha, '%a %b %d %H:%M:%S %z %Y')
    
    '''cursor.execute("""
        INSERT INTO sonidos (id_paciente, sonido)
        VALUES (%s, %s)
    """, (id_user, sonido,))
    db.commit()'''

    paciente = ServiciosPaciente.obtener_por_id(id_user)

    '''cursor.execute("""
            SELECT * FROM paciente WHERE id_paciente = %s
        """, (id_user,))
    control = cursor.fetchone()  '''

    if paciente:
        id_enc = paciente['id_encargado']

        usuario = ServiciosUsuario.obtener_id(id_enc)

        token_user = usuario['token']
        print('*/*/'*100)
        print(token_user)
        titulo = "Ruido Molesto Detectado"
        cuerpo = f"Alerta de {sonido}, cerca del paciente"
        result = send_fcm_notification(token_user, titulo, cuerpo)
        return jsonify(result), 200
    else:
        return jsonify({'message':'No hay token'}), 200

    return jsonify({'message': 'Registrado Satisfactoriamente'}), 200

@routes.route('/obtener_paciente', methods=['POST'])
def obtener_paciente():
    datos = request.get_json()
    id_usuario = datos.get("id")
    print(id_usuario)

    pacientes_lista = ServiciosPaciente.obtener_por_carnet(id_usuario)

    '''cursor.execute("""
        SELECT * FROM paciente WHERE paciente.carnet = %s
    """, (id_usuario, ))
    pacientes_lista = cursor.fetchone()'''
    print(pacientes_lista)
    today = datetime.today()
    fecha_nacimiento = pacientes_lista['fecha_nacimiento']
        # Calcular la edad
    edad = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    pacientes_lista['edad'] = edad  
    cuerpo = {
        'id': pacientes_lista['id_paciente'],
        'age' : pacientes_lista['edad'],
        'name' : pacientes_lista['nombre'],
        'rate' : pacientes_lista['carnet']
    }

    return jsonify({'results' : [cuerpo]})
