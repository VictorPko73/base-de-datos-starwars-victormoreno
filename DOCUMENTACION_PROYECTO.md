# Documentación detallada del proyecto: base-de-datos-starwars-victormoreno

## Índice

1. Introducción
2. Estructura del proyecto
3. Descripción general del backend
4. Archivos clave (explicación y ejemplos con comentarios inline)
   - `src/app.py`
   - `src/models.py`
   - `src/utils.py`
   - `src/routes/people.py`
   - `src/routes/planets.py`
   - `src/routes/user.py`
5. Endpoints disponibles (resumen)
6. Flujo de uso y ejemplos curl
7. Cómo ejecutar localmente (entorno mínimo)
8. Buenas prácticas, pruebas rápidas y siguientes pasos

---

## 1. Introducción

Este repositorio contiene una API REST minimalista construida con Flask y SQLAlchemy para gestionar usuarios, personajes, planetas y favoritos (estilo Star Wars). El objetivo de este documento es ofrecer una guía clara del proyecto, describir los archivos principales y mostrar fragmentos de código con comentarios inline que expliquen qué hace cada parte.

El documento está pensado para desarrolladores que quieran entender rápidamente la arquitectura, ejecutar el proyecto en local y conocer los endpoints disponibles.

## 2. Estructura del proyecto

Resumen de la estructura principal (solo los archivos relevantes):

```
.
├── src/
│   ├── app.py                # Entrypoint de la aplicación Flask
│   ├── models.py             # Modelos SQLAlchemy (Usuario, Planeta, Personaje, Favorito)
│   ├── utils.py              # Utilidades: manejo de errores y generador de sitemap
│   ├── admin.py              # (setup_admin) configuración del admin
│   ├── routes/
│   │   ├── people.py         # Endpoints relacionados con personajes
│   │   ├── planets.py        # Endpoints relacionados con planetas
│   │   └── user.py           # Endpoints de usuarios y favoritos
│   └── wsgi.py               # (posible) para despliegue
├── migrations/               # Carpetas y archivos de Alembic
├── Pipfile                   # Dependencias del proyecto
├── README.md
└── DOCUMENTACION_PROYECTO.md # (este archivo)
```

## 3. Descripción general del backend

La aplicación es una API REST construida con Flask que utiliza SQLAlchemy como ORM. Las rutas están organizadas en blueprints dentro de `src/routes/`. Se soportan operaciones CRUD básicas para personajes y planetas, y gestión de usuarios y favoritos.

Puntos clave:

- Base de datos configurable vía `DATABASE_URL` (si no existe, usa SQLite temporal).
- Blueprints para separar dominios (people, planets, user).
- Modelos con método `serialize()` para devolver representación JSON.
- Utilidad `generate_sitemap(app)` para listar endpoints navegables.

## 4. Archivos clave (explicación y ejemplos con comentarios inline)

Abajo hay extractos de los archivos principales adaptados con comentarios en línea en español para explicar su funcionamiento. Los fragmentos se han reducido a lo esencial para facilitar la lectura.

### `src/app.py`

```python
"""
Módulo principal que arranca el servidor, carga la BD y registra blueprints.

Esta sección incluye comentarios detallados por línea para que entiendas
por qué se hacen ciertas configuraciones (por ejemplo, la conversión
de `postgres://` a `postgresql://`) y qué efectos tienen en runtime.
"""

# Importes estándar y de Flask
import os  # para leer variables de entorno
from flask import Flask, jsonify  # Flask core y helper jsonify para respuestas de error
from flask_migrate import Migrate  # para migraciones de DB (alembic integration)
from flask_cors import CORS  # para permitir llamadas desde orígenes distintos (frontends)

# Importamos utilidades y blueprints desde módulos locales
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db
from routes.people import people_bp
from routes.planets import planeta_bp
from routes.user import user_bp

# Instancia principal de la app
app = Flask(__name__)

# Evita que Flask requiera slash exacto en las rutas (p. ej. /people y /people/)
app.url_map.strict_slashes = False

# Configuración de la base de datos:
# - Lee la variable de entorno DATABASE_URL si está definida (útil para Heroku, Docker, CI)
# - Algunos proveedores devuelven una URL con esquema `postgres://` que SQLAlchemy
#   no reconoce en versiones recientes; por eso se hace el replace a `postgresql://`.
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    # Sustituir solo el prefijo, sin alterar el resto de la cadena
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    # Fallback local: un SQLite temporal en /tmp (útil para tests rápidos)
    # Nota: usar sqlite:///./db.sqlite para persistencia en el repo si lo prefieres
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

# Desactivamos el tracking de modificaciones para ahorrar memoria (se suele dejar False)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# ---------- Inicialización de extensiones ----------
# Migrate: prepara Alembic/Flask-Migrate para gestionar versiones de la BD
MIGRATE = Migrate(app, db)

# Inicializa SQLAlchemy con la app actual (registra engines y session factory)
db.init_app(app)

# Habilita CORS para permitir peticiones desde frontends o herramientas de desarrollo
CORS(app)

# Configura el panel administrativo (si `admin.py` define modelos/handlers)
setup_admin(app)


# ---------- Registro de blueprints (modularización de rutas) ----------
# Registrar los blueprints despues de inicializar db y otras extensiones
app.register_blueprint(people_bp)
app.register_blueprint(planeta_bp)
app.register_blueprint(user_bp)


# ---------- Manejo de errores personalizados ----------
# Intercepta excepciones levantadas con APIException y devuelve JSON
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    # `error.to_dict()` devuelve la estructura serializable con `message` y payload
    return jsonify(error.to_dict()), error.status_code


# Ruta raíz: devuelve sitemap con endpoints navegables
@app.route('/')
def sitemap():
    # generate_sitemap itera sobre app.url_map y filtra endpoints adecuados
    return generate_sitemap(app)


# Solo arrancar el servidor cuando este módulo se ejecute como script
if __name__ == '__main__':
    # Leer el puerto de la variable PORT o usar 3000 por defecto
    PORT = int(os.environ.get('PORT', 3000))
    # host 0.0.0.0 para aceptar conexiones desde otras máquinas (útil en Docker)
    app.run(host='0.0.0.0', port=PORT, debug=False)
```

### `src/models.py`

Los modelos definen las tablas: `Usuario`, `Planeta`, `Personaje` y `Favorito`.
Cada clase incluye un método `serialize()` que produce un diccionario listo para JSON.

```python
# Imports de SQLAlchemy y utilidades de tipado
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, mapped_column, Mapped
import datetime

# Instancia global de SQLAlchemy que se inicializa en app.py con `db.init_app(app)`
db = SQLAlchemy()


class Usuario(db.Model):
    """Modelo que representa a un usuario del sistema.

    Comentarios línea a línea:
    - __tablename__: nombre explícito de la tabla en la BD.
    - id: PK autoincremental.
    - nombre/apellido/email: campos básicos, `email` único para autenticación.
    - password: campo para contraseña (actualmente en texto plano en el código base, ver notas).
    - fecha_suscripcion: timestamp con valor por defecto la hora actual.
    - favoritos: relación uno-a-muchos con `Favorito` (back_populates sincroniza ambos lados).
    """

    __tablename__ = 'usuarios'
    # Mapped[...] es una forma más explícita y compatible con typing del mapeo
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    apellido: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_suscripcion: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    favoritos: Mapped[list["Favorito"]] = relationship(back_populates="usuario")

    def serialize(self) -> dict:
        """Retorna una representación segura del usuario para la API.

        Importante: aquí no incluimos `password`. Si necesitas exponer
        más campos, piensa en filtros por roles o usar un schema (marshmallow/pydantic).
        """
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "fecha_suscripcion": self.fecha_suscripcion.isoformat()
        }



class Planeta(db.Model):
    """Modelo para planetas.

    Campos:
    - nombre: obligatorio.
    - clima: texto descriptivo.
    - poblacion: entero (puede ser None si se desconoce).
    - favoritos: relación con Favorito.
    """

    __tablename__ = 'planetas'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    clima: Mapped[str] = mapped_column(String(100))
    poblacion: Mapped[int] = mapped_column(Integer)
    favoritos: Mapped[list["Favorito"]] = relationship(back_populates="planeta")

    def serialize(self) -> dict:
        # Convierte a tipos JSON-friendly
        return {"id": self.id, "nombre": self.nombre, "clima": self.clima, "poblacion": self.poblacion}



class Personaje(db.Model):
    """Modelo para personajes.

    Observaciones:
    - `genero` y `nacimiento` son opcionales (pueden ser None).
    - `favoritos` guarda relaciones inversas con Favorito.
    """

    __tablename__ = 'personajes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    genero: Mapped[str] = mapped_column(String(20))
    nacimiento: Mapped[str] = mapped_column(String(20))
    favoritos: Mapped[list["Favorito"]] = relationship(back_populates="personaje")

    def serialize(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "genero": self.genero, "nacimiento": self.nacimiento}



class Favorito(db.Model):
    """Modelo que representa un favorito del usuario.

    Diseño:
    - Un Favorito puede apuntar a un `planeta` o a un `personaje` (o teóricamente a ambos),
      por eso ambos campos son nullable.
    - `usuario_id` es obligatorio: un favorito siempre pertenece a un usuario.
    - Se usan ForeignKey para integridad referencial.
    """

    __tablename__ = 'favoritos'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey('usuarios.id'), nullable=False)
    planeta_id: Mapped[int] = mapped_column(Integer, ForeignKey('planetas.id'), nullable=True)
    personaje_id: Mapped[int] = mapped_column(Integer, ForeignKey('personajes.id'), nullable=True)
    usuario: Mapped["Usuario"] = relationship(back_populates="favoritos")
    planeta: Mapped["Planeta"] = relationship(back_populates="favoritos")
    personaje: Mapped["Personaje"] = relationship(back_populates="favoritos")

    def serialize(self) -> dict:
        # Devuelve ids que permiten al cliente decidir cómo renderizar el favorito
        return {"id": self.id, "usuario_id": self.usuario_id, "planeta_id": self.planeta_id, "personaje_id": self.personaje_id}
```

**Notas de seguridad y diseño:**

- En el código actual `password` se guarda tal cual en la columna `password`. Esto es inseguro. Recomendación:
  - Añadir métodos en `Usuario` como `set_password(self, pw)` que almacene el hash con `werkzeug.security.generate_password_hash` y `check_password(self, pw)` con `check_password_hash`.
  - Nunca devolver `password` en `serialize()` ni en ningún endpoint.
- Valora usar esquemas de validación (pydantic o marshmallow) para sanear input/output y mantener contratos claros.

### `src/utils.py`

Contiene la excepción personalizada `APIException` y un generador de sitemap que lista las rutas navegables.

```python
from flask import jsonify, url_for


class APIException(Exception):
    """Excepción base utilizada en la API para errores controlados.

    Uso típico:
        raise APIException('Recurso no encontrado', status_code=404)

    Atributos:
    - status_code: código HTTP por defecto (400)
    - message: mensaje legible para el cliente
    - payload: datos adicionales opcionales
    """

    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        # Llamamos al constructor base por compatibilidad
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        # Convierte la excepción a dict para serializarla con jsonify
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def generate_sitemap(app):
    """Genera una lista de URLs navegables en la app.

    - Filtra reglas que acepten GET y no requieran parámetros obligatorios.
    - Excluye rutas administrativas por defecto.
    """

    links = ['/admin/']

    # iter_rules devuelve objetos Rule que contienen endpoint, methods, arguments, defaults...
    for rule in app.url_map.iter_rules():
        # Solo consideramos rutas accesibles con GET y sin parámetros sin default
        if "GET" in rule.methods and has_no_empty_params(rule):
            # url_for construye la URL para el endpoint con valores por defecto
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            # Omitir rutas de admin para no listarlas en el API público
            if "/admin/" not in url:
                links.append(url)

    links.sort()
    return jsonify(links)


def has_no_empty_params(rule):
    """Comprueba si una regla tiene todos sus parámetros con defaults o no tiene argumentos.

    - Si `arguments` > `defaults` significa que la ruta requiere valores que no se pueden
      generar sin parámetros (p. ej. `/users/<int:id>`), y por tanto no es navegable directamente.
    """

    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)
```

### `src/routes/people.py` (fragmento y comportamiento)

```python
# Rutas relativas a personajes (people)
from flask import Blueprint, jsonify, request
from models import db, Personaje

people_bp = Blueprint('people_bp', __name__)


@people_bp.route('/people', methods=['POST'])
def create_person():
    """Crear un nuevo personaje.

    Flujo detallado:
    1. `request.get_json()` obtiene el payload JSON; puede devolver None si no es JSON válido.
    2. Extraemos campos esperados y validamos `nombre` (requerido).
    3. Creamos la instancia, añadimos a la sesión y hacemos commit.
    4. Devolvemos 201 con el recurso creado.

    Errores y consideraciones:
    - Si `data` es None, `data.get` fallaría; por eso en producción conviene comprobar `if not data`.
    - Validar tipos y longitudes antes de persistir.
    """

    data = request.get_json()  # puede ser None si la petición no tiene JSON válido
    if not data:
        # 400 es apropiado para payload inválido
        return jsonify({"message": "JSON inválido o ausente"}), 400

    # Lectura de campos con .get para permitir valores opcionales
    nombre = data.get('nombre')
    genero = data.get('genero')
    nacimiento = data.get('nacimiento')

    # Validación mínima
    if not nombre:
        return jsonify({"message": "El nombre es obligatorio"}), 400

    # Construcción del objeto (sin validaciones avanzadas)
    nuevo_personaje = Personaje(nombre=nombre, genero=genero, nacimiento=nacimiento)

    # Persistencia: añadir objeto y commit. Si ocurre excepción DB, se debe hacer rollback.
    db.session.add(nuevo_personaje)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # En producción devolver un mensaje genérico y loggear el error real
        return jsonify({"message": "Error al crear personaje"}), 500

    # Respuesta: devolver el recurso creado y un mensaje
    return jsonify({"message": "Personaje Creado", "personaje": nuevo_personaje.serialize()}), 201


@people_bp.route('/people', methods=['GET'])
def get_all_people():
    """Listar todos los personajes.

    Observación de diseño: el código original devolvía 404 si no había personajes.
    En APIs REST convencionales suele devolverse 200 con una lista vacía para
    facilitar el manejo en cliente (no tener que tratar 404 como error).
    Aquí se mantiene la lógica original pero te recomiendo devolver [] y 200.
    """

    personajes = Personaje.query.all()
    # Serializamos cada instancia con el método serialize()
    personajes_serializados = [personaje.serialize() for personaje in personajes]

    if personajes_serializados:
        return jsonify(personajes_serializados), 200
    else:
        # Alternativa recomendada: `return jsonify([]), 200`
        return jsonify({"message": "No Existen Personajes"}), 404


@people_bp.route('/people/<int:people_id>', methods=['GET'])
def get_person_by_id(people_id):
    """Obtener personaje por su id.

    - Si existe, devolvemos 200 con la representación.
    - Si no, 404.
    """

    personaje = Personaje.query.get(people_id)
    if personaje:
        return jsonify(personaje.serialize()), 200
    else:
        return jsonify({"message": "ID de Personaje no encontrado"}), 404
```

### `src/routes/planets.py` (fragmento y comportamiento)

```python
from flask import Blueprint, jsonify, request
from models import db, Planeta

planeta_bp = Blueprint('planeta_bp', __name__)


@planeta_bp.route('/planets', methods=['POST'])
def create_planet():
    """Crear un nuevo planeta.

    Notas:
    - Validar que `data` existe y que `nombre` no esté vacío.
    - `poblacion` podría llegar como string desde un cliente; conviene validar/convertir.
    """

    data = request.get_json()
    if not data:
        return jsonify({"message": "JSON inválido o ausente"}), 400

    nombre = data.get('nombre')
    clima = data.get('clima')
    poblacion = data.get('poblacion')

    if not nombre:
        return jsonify({"message": "El nombre es obligatorio"}), 400

    nuevo_planeta = Planeta(nombre=nombre, clima=clima, poblacion=poblacion)
    db.session.add(nuevo_planeta)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Error al crear planeta"}), 500

    return jsonify({"message":"Planeta Creado", "planeta": nuevo_planeta.serialize()}), 201


@planeta_bp.route('/planets', methods=['GET'])
def get_all_planets():
    """Listar todos los planetas. Similar comentario que en /people: conviene devolver [] y 200."""

    planetas = Planeta.query.all()
    planetas_serializados = [planeta.serialize() for planeta in planetas]
    if planetas_serializados:
        return jsonify(planetas_serializados), 200
    else:
        return jsonify({"message": "No Existen Planetas"}), 404


@planeta_bp.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet_by_id(planet_id):
    planeta = Planeta.query.get(planet_id)
    if planeta:
        return jsonify(planeta.serialize()), 200
    else:
        return jsonify({"message": "ID de Planeta no encontrado"}), 404
```

### `src/routes/user.py` (fragmento y comportamiento)

Este fichero maneja creación/listado de usuarios y la gestión de favoritos (añadir/eliminar
planetas o personajes favoritos para un usuario dado). A continuación se describen
las partes más críticas con comentarios detallados.

```python
from flask import Blueprint, jsonify, request
from models import db, Usuario, Favorito, Planeta, Personaje

user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/users', methods=['POST'])
def create_user():
    """Crear un usuario.

    Validaciones y flujo:
    - Comprobar que `data` es JSON.
    - Validar campos obligatorios: nombre, apellido, email, password.
    - Comprobar unicidad de email antes de crear.
    - Guardar el usuario y devolver 201.

    Observaciones de seguridad:
    - El código base guarda la contraseña tal cual. Debemos reemplazar esto por hashing.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o ausente"}), 400

    nombre = data.get('nombre')
    apellido = data.get('apellido')
    email = data.get('email')
    password = data.get('password')

    # Validaciones simples por campo
    if not nombre:
        return jsonify({"error": "El campo 'nombre' es obligatorio"}), 400
    if not apellido:
        return jsonify({"error": "El campo 'apellido' es obligatorio"}), 400
    if not email:
        return jsonify({"error": "El campo 'email' es obligatorio"}), 400
    if not password:
        return jsonify({"error": "El campo 'password' es obligatorio"}), 400

    # Comprobar si ya existe usuario con ese email
    usuario_existe = Usuario.query.filter_by(email=email).first()
    if usuario_existe:
        return jsonify({"error": "El usuario ya existe"}), 400

    # Aquí deberías hashear la contraseña antes de asignarla al modelo, por ejemplo:
    # hashed = generate_password_hash(password)
    # nuevo_usuario = Usuario(..., password=hashed)
    nuevo_usuario = Usuario(nombre=nombre, apellido=apellido, email=email, password=password)

    db.session.add(nuevo_usuario)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error al crear usuario"}), 500

    return jsonify({"message": "Usuario creado exitosamente", "usuario": nuevo_usuario.serialize()}), 201


# Listar todos los usuarios
@user_bp.route('/users', methods=['GET'])
def get_all_users():
    usuarios = Usuario.query.all()
    usuarios_serializados = [usuario.serialize() for usuario in usuarios]
    if usuarios_serializados:
        return jsonify(usuarios_serializados), 200
    else:
        return jsonify({"message": "No Existen Usuarios"}), 404


# Obtener los favoritos del un usuario mediante query param ?user_id=<id>
@user_bp.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    # Extraer user_id desde query string
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400

    # Validar que user_id es entero
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400

    # Verificar existencia del usuario
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404

    # Obtener favoritos del usuario
    favoritos = Favorito.query.filter_by(usuario_id=user_id).all()
    if not favoritos:
        return jsonify({"message": "No se encontraron favoritos para este usuario"}), 404

    resultado = []
    for fav in favoritos:
        # Si el favorito apunta a un planeta, añadimos su serialización
        if fav.planeta_id and fav.planeta:
            resultado.append({
                "id": fav.id,
                "type": "planet",
                "planet": fav.planeta.serialize()
            })
        # Si apunta a un personaje, hacemos lo mismo
        elif fav.personaje_id and fav.personaje:
            resultado.append({
                "id": fav.id,
                "type": "people",
                "people": fav.personaje.serialize()
            })

    return jsonify(resultado), 200


# Añadir planeta a favoritos: POST /favorite/planet/<planet_id>?user_id=1
@user_bp.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    # Validaciones similares: comprobar user_id en query string y que el usuario/planeta existan
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404

    planeta = Planeta.query.get(planet_id)
    if not planeta:
        return jsonify({"message": "ID de Planeta no encontrado"}), 404

    # Evitar duplicados: comprobar si ya existe ese favorito
    favorito_existente = Favorito.query.filter_by(usuario_id=user_id, planeta_id=planet_id).first()
    if favorito_existente:
        return jsonify({"message": "El planeta ya está en favoritos"}), 409

    nuevo_favorito = Favorito(usuario_id=user_id, planeta_id=planet_id, personaje_id=None)
    db.session.add(nuevo_favorito)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Error al agregar favorito"}), 500

    return jsonify({"message": "Planeta agregado a favoritos exitosamente", "favorite": nuevo_favorito.serialize()}), 201


# Añadir personaje a favoritos: POST /favorite/people/<people_id>?user_id=1
@user_bp.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404

    personaje = Personaje.query.get(people_id)
    if not personaje:
        return jsonify({"message": "ID de Personaje no encontrado"}), 404

    favorito_existente = Favorito.query.filter_by(usuario_id=user_id, personaje_id=people_id).first()
    if favorito_existente:
        return jsonify({"message": "El personaje ya está en favoritos"}), 409

    nuevo_favorito = Favorito(usuario_id=user_id, planeta_id=None, personaje_id=people_id)
    db.session.add(nuevo_favorito)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Error al agregar favorito"}), 500

    return jsonify({"message": "Personaje agregado a favoritos exitosamente", "favorite": nuevo_favorito.serialize()}), 201


# Eliminar planeta favorito
@user_bp.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404

    favorito = Favorito.query.filter_by(usuario_id=user_id, planeta_id=planet_id).first()
    if not favorito:
        return jsonify({"message": "Favorito de planeta no encontrado para este usuario"}), 404

    db.session.delete(favorito)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Error al eliminar favorito"}), 500

    return jsonify({"message": "Planeta eliminado de favoritos exitosamente"}), 200


# Eliminar personaje favorito
@user_bp.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404

    favorito = Favorito.query.filter_by(usuario_id=user_id, personaje_id=people_id).first()
    if not favorito:
        return jsonify({"message": "Favorito de personaje no encontrado para este usuario"}), 404

    db.session.delete(favorito)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Error al eliminar favorito"}), 500

    return jsonify({"message": "Personaje eliminado de favoritos exitosamente"}), 200
```

## 5. Endpoints disponibles (resumen)

- GET / -> sitemap con rutas públicas
- POST /people -> crear personaje
- GET /people -> listar personajes
- GET /people/<id> -> obtener personaje por id
- POST /planets -> crear planeta
- GET /planets -> listar planetas
- GET /planets/<id> -> obtener planeta por id
- POST /users -> crear usuario
- GET /users -> listar usuarios
- GET /users/favorites -> listar favoritos de un usuario (query param: user_id)
- POST /favorite/planet/<planet_id>?user_id=1 -> agregar planeta favorito
- POST /favorite/people/<people_id>?user_id=1 -> agregar personaje favorito
- DELETE /favorite/planet/<planet_id>?user_id=1 -> eliminar planeta favorito
- DELETE /favorite/people/<people_id>?user_id=1 -> eliminar personaje favorito

> Nota: Algunos endpoints esperan `user_id` como query param (p.e. `?user_id=1`). En producción se recomienda usar autenticación y obtener el usuario desde la sesión o token.

## 6. Flujo de uso y ejemplos curl

Crear un personaje:

```bash
curl -X POST http://localhost:3000/people \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Luke Skywalker","genero":"Masculino","nacimiento":"19BBY"}'
```

Listar planetas:

```bash
curl http://localhost:3000/planets
```

Agregar planeta a favoritos para user_id=1:

```bash
curl -X POST "http://localhost:3000/favorite/planet/1?user_id=1"
```

Obtener favoritos del usuario 1:

```bash
curl "http://localhost:3000/users/favorites?user_id=1"
```

## 7. Cómo ejecutar localmente (entorno mínimo)

Requisitos mínimos: Python 3.10+ (según el entorno del autor), `pipenv` (opcional) o `virtualenv`.

Comandos sugeridos (macOS / zsh):

```bash
# desde la raíz del proyecto
cd "$(dirname "${0}")" || exit  # asegúrate de estar en la carpeta del repo
# Crear e instalar dependencias usando pipenv (si usas Pipfile)
pipenv install --dev

# Activar el shell virtual creado por pipenv
pipenv shell

# Exportar DB local (opcional) o usar la configuración por defecto (SQLite en /tmp/test.db)
# Si quieres usar Postgres, exporta DATABASE_URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/mi_db"

# Ejecutar la app
python src/app.py
```

Si no usas pipenv, crea un venv y usa `pip install -r requirements.txt` si tienes un fichero con deps.

## 8. Buenas prácticas, pruebas rápidas y siguientes pasos

Recomendaciones de mejoras (prioritarias):

1. Hashear contraseñas antes de guardar (bcrypt o werkzeug.security.generate_password_hash).
2. Añadir autenticación (JWT o sessions) para no depender de `user_id` en query params.
3. Añadir tests unitarios (pytest) para endpoints críticos (crear usuario, añadir favorito, listar favoritos).
4. Corregir retornos de `jsonify` que envían múltiples argumentos (normalizar a un único dict con claves claras).
5. Añadir validaciones y límites (longitud de strings, tipos, saneamiento de inputs).

Pruebas rápidas sugeridas (smoke tests):

- Levantar la app y llamar a `/` para comprobar sitemap.
- Crear un usuario y verificar que aparece en `GET /users`.
- Crear un planeta y un personaje y probar añadir/eliminar favoritos.

### Cobertura de requirements solicitados

- "quiero algo como esto pero referente a este proyecto": He creado este `DOCUMENTACION_PROYECTO.md` en la raíz del repo con:
  - explicación de la estructura del proyecto (Done)
  - descripción de los archivos principales (Done)
  - bloques de código con comentarios inline adaptados (Done)
  - resumen de endpoints, ejemplos curl y pasos para ejecutar (Done)

---

Si quieres, puedo:

- Añadir la versión en PDF y guardarla en la raíz.
- Crear tests unitarios básicos con `pytest` y un script de smoke tests.
- Implementar el hashing de contraseñas y actualizar rutas de usuario.

Dime cuál de las mejoras quieres que haga a continuación y me pongo con ella.
