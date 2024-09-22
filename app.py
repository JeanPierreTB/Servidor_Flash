from flask import Flask, request, jsonify 
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import os
import logging

# Configurar el logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Configurar la base de datos PostgreSQL con la URL externa
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dataset_estres_user:KIDw4oaKu2uWIbijxgOCfkCOwRWIsB5V@dpg-crmpfndumphs739ip24g-a.oregon-postgres.render.com/dataset_estres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definir el modelo de la tabla donde se almacenarán los datos
class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    acc_X = db.Column(db.Float, nullable=False)
    acc_Y = db.Column(db.Float, nullable=False)
    acc_Z = db.Column(db.Float, nullable=False)
    temperatura = db.Column(db.Float, nullable=False)
    frecuencia = db.Column(db.Float, nullable=False)
    estresado = db.Column(db.Integer, nullable=True)  # Permitir nulos
    persona = db.Column(db.String(100), nullable=False)

# Crear la tabla si no existe
with app.app_context():
    db.create_all()

@app.route('/sensor-data', methods=['POST'])
def recibir_datos():
    try:
        data = request.json

        # Crear un nuevo registro en la base de datos
        new_data = SensorData(
            acc_X=data.get('acc_X'),
            acc_Y=data.get('acc_Y'),
            acc_Z=data.get('acc_Z'),
            temperatura=data.get('temperatura'),
            frecuencia=data.get('frecuencia'),
            estresado=data.get('estresado', None),  # Asignar None si no se pasa
            persona=data.get('persona')
        )
        db.session.add(new_data)
        db.session.commit()

        return jsonify({"status": "datos recibidos y almacenados"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/sensor-data', methods=['GET'])
def obtener_datos():
    try:
        # Obtener los datos almacenados en la base de datos
        data_list = SensorData.query.all()
        result = []
        for data in data_list:
            result.append({
                'id': data.id,
                'acc_X': data.acc_X,
                'acc_Y': data.acc_Y,
                'acc_Z': data.acc_Z,
                'temperatura': data.temperatura,
                'frecuencia': data.frecuencia,
                'estresado': data.estresado,
                'persona': data.persona
            })

        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"message": "El servidor está funcionando correctamente"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
