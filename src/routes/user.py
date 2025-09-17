from flask import Blueprint, jsonify, request
from models import db, Usuario, Favorito, Planeta, Personaje

user_bp = Blueprint('user_bp', __name__)

#Crear Usuario

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    #Validar campos obligatorios
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    email = data.get('email')
    password = data.get('password')
    
    if not nombre:
        return jsonify({"error": "El campo 'nombre' es obligatorio"}), 400
    if not apellido:
        return jsonify({"error": "El campo 'apellido' es obligatorio"}), 400
    if not email:
        return jsonify({"error": "El campo 'email' es obligatorio"}), 400
    if not password:
        return jsonify({"error": "El campo 'password' es obligatorio"}), 400

    usuario_existe = Usuario.query.filter_by(email=email).first()
    if usuario_existe:
        return jsonify({"error": "El usuario ya existe"}), 400

    #Crear nuevo usuario
    nuevo_usuario = Usuario(
        nombre=nombre,
        apellido=apellido,
        email=email,
        password=password
    )

    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({"message": "Usuario creado exitosamente"}, nuevo_usuario.serialize()), 201


# Listar todos los usuarios 
@user_bp.route('/users', methods=['GET'])
def get_all_users():
    usuarios = Usuario.query.all()
    usuarios_serializados = [usuario.serialize() for usuario in usuarios]
    
    if usuarios_serializados:
        return jsonify(usuarios_serializados), 200
    else:
        return jsonify({"message": "No Existen Usuarios"}), 404
    

    
@user_bp.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400
    
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400
    
    # Verificar que el usuario existe
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404
    
    # Obtener favoritos del usuario
    favoritos = Favorito.query.filter_by(usuario_id=user_id).all()
    
    if not favoritos:
        return jsonify({"message": "No se encontraron favoritos para este usuario"}), 404
    
    resultado = []
    for fav in favoritos:
        if fav.planeta_id and fav.planeta:
            resultado.append({
                "id": fav.id,
                "type": "planet",
                "planet": fav.planeta.serialize()
            })
        elif fav.personaje_id and fav.personaje:
            resultado.append({
                "id": fav.id,
                "type": "people",
                "people": fav.personaje.serialize()
            })
    
    return jsonify(resultado), 200


#Agregar planeta a favoritos del usuario actual
@user_bp.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    # Obtener el ID del usuario desde query parameter
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400
    
    # Convertir user_id a entero y validar
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400
    
    # Verificar que el usuario existe en la base de datos
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404
    
    # Verificar que el planeta existe en la base de datos
    planeta = Planeta.query.get(planet_id)
    if not planeta:
        return jsonify({"message": "ID de Planeta no encontrado"}), 404
    
    # Verificar si el planeta ya está en favoritos del usuario (evitar duplicados)
    favorito_existente = Favorito.query.filter_by(
        usuario_id=user_id, 
        planeta_id=planet_id
    ).first()
    
    if favorito_existente:
        return jsonify({"message": "El planeta ya está en favoritos"}), 409
    
    # Crear nuevo registro de favorito
    nuevo_favorito = Favorito(
        usuario_id=user_id,
        planeta_id=planet_id,
        personaje_id=None  # Solo planeta, no personaje
    )
    
    # Guardar en la base de datos
    db.session.add(nuevo_favorito)
    db.session.commit()
    
    # Respuesta exitosa con los datos del favorito creado
    return jsonify({
        "message": "Planeta agregado a favoritos exitosamente",
        "favorite": nuevo_favorito.serialize()
    }), 201
    
    
    
    
# Agregar personaje a favoritos del usuario actual
@user_bp.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    # Obtener el ID del usuario desde query parameter
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400
    
    # Convertir user_id a entero y validar
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400
    
    # Verificar que el usuario existe en la base de datos
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404
    
    # Verificar que el personaje existe en la base de datos
    personaje = Personaje.query.get(people_id)
    if not personaje:
        return jsonify({"message": "ID de Personaje no encontrado"}), 404
    
    # Verificar si el personaje ya está en favoritos del usuario (evitar duplicados)
    favorito_existente = Favorito.query.filter_by(
        usuario_id=user_id, 
        personaje_id=people_id
    ).first()
    
    if favorito_existente:
        return jsonify({"message": "El personaje ya está en favoritos"}), 409
    
    # Crear nuevo registro de favorito
    nuevo_favorito = Favorito(
        usuario_id=user_id,
        planeta_id=None,  # Solo personaje, no planeta
        personaje_id=people_id
    )
    
    # Guardar en la base de datos
    db.session.add(nuevo_favorito)
    db.session.commit()
    
    # Respuesta exitosa con los datos del favorito creado
    return jsonify({
        "message": "Personaje agregado a favoritos exitosamente",
        "favorite": nuevo_favorito.serialize()
    }), 201
    
    

# Eliminar planeta de favoritos del usuario actual
@user_bp.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    # Obtener el ID del usuario desde query parameter
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Falta user_id en query"}), 400
    
    # Convertir user_id a entero y validar
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id debe ser un número"}), 400
    
    # Verificar que el usuario existe en la base de datos
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404
    
    # Buscar el favorito específico del usuario para ese planeta
    favorito = Favorito.query.filter_by(
        usuario_id=user_id, 
        planeta_id=planet_id
    ).first()
    
    # Si no existe el favorito, devolver error
    if not favorito:
        return jsonify({"message": "Favorito de planeta no encontrado para este usuario"}), 404
    
    # Eliminar el favorito de la base de datos
    db.session.delete(favorito)
    db.session.commit()
    
    # Respuesta exitosa
    return jsonify({"message": "Planeta eliminado de favoritos exitosamente"}), 200
