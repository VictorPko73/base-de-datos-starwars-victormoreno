from flask import Blueprint, jsonify, request
from models import db, Personaje

people_bp = Blueprint('people_bp', __name__)


# Crear un nuevo personaje
@people_bp.route('/people', methods=['POST'])
def create_person():
    data = request.get_json()
    nombre = data.get('nombre')
    genero = data.get('genero')
    nacimiento = data.get('nacimiento')
    if not nombre:
        return jsonify({"message": "El nombre es obligatorio"}), 400
    nuevo_personaje = Personaje(nombre=nombre, genero=genero, nacimiento=nacimiento)
    db.session.add(nuevo_personaje)
    db.session.commit()
    return jsonify({"message": "Personaje Creado"}, nuevo_personaje.serialize()), 201



#Obtenr todos los personajes
@people_bp.route('/people', methods=['GET'])
def get_all_people():
    personajes = Personaje.query.all()
    personajes_serializados = [personaje.serialize() for personaje in personajes]
    
    if personajes_serializados:
        return jsonify(personajes_serializados), 200
    else:
        return jsonify({"message": "No Existen Personajes"}), 404


@people_bp.route('/people/<int:people_id>', methods=['GET'])
def get_person_by_id(people_id):
    personaje = Personaje.query.get(people_id)
    if personaje:
        return jsonify(personaje.serialize()), 200
    else:
        return jsonify({"message": "ID de Personaje no encontrado"}), 404


