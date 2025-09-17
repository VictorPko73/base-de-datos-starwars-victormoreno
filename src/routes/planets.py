from flask import Blueprint, jsonify, request
from models import db, Planeta

planeta_bp = Blueprint('planeta_bp', __name__)


# Crear un nuevo planeta
@planeta_bp.route('/planets', methods=['POST'])
def create_planet():
    data = request.get_json()
    nombre = data.get('nombre')
    clima = data.get('clima')
    poblacion = data.get('poblacion')
    if not nombre:
        return jsonify({"message": "El nombre es obligatorio"}), 400
    nuevo_planeta = Planeta(nombre=nombre, clima=clima, poblacion=poblacion)
    db.session.add(nuevo_planeta)
    db.session.commit()
    return jsonify({"message":"Planeta Creado"},nuevo_planeta.serialize()), 201

@planeta_bp.route('/planets', methods=['GET'])
def get_all_planets():
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





