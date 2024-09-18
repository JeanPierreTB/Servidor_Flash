from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text  # Importar la función text
import logging

# Configurar el logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgre@localhost:5432/Sensores2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definición del modelo de datos
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    acc_X = db.Column(db.Float)
    acc_Y = db.Column(db.Float)
    acc_Z = db.Column(db.Float)
    temperatura = db.Column(db.Float)
    frecuencia = db.Column(db.Integer)

    def __init__(self, acc_X, acc_Y, acc_Z, temperatura, frecuencia):
        self.acc_X = acc_X
        self.acc_Y = acc_Y
        self.acc_Z = acc_Z
        self.temperatura = temperatura
        self.frecuencia = frecuencia

def test_db_connection():
    with app.app_context():
        try:
            # Ejecutar una consulta de prueba para verificar la conexión
            result = db.session.execute(text('SELECT 1'))
            logging.info("Conexión a la base de datos exitosa.")
        except Exception as e:
            logging.error(f"Error al conectar a la base de datos: {str(e)}")

def create_tables():
    with app.app_context():
        try:
            db.create_all()
            logging.info("Tablas creadas exitosamente.")
        except SQLAlchemyError as e:
            logging.error(f"Error al crear tablas: {str(e)}")

@app.route('/sensor-data', methods=['POST'])
def recibir_datos():
    try:
        data = request.json
        new_data = SensorData(
            acc_X=data.get('acc_X'),
            acc_Y=data.get('acc_Y'),
            acc_Z=data.get('acc_Z'),
            temperatura=data.get('temperatura'),
            frecuencia=data.get('frecuencia')
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
        all_data = SensorData.query.all()
        result = [
            {
                'id': data.id,
                'acc_X': data.acc_X,
                'acc_Y': data.acc_Y,
                'acc_Z': data.acc_Z,
                'temperatura': data.temperatura,
                'frecuencia': data.frecuencia
            }
            for data in all_data
        ]
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"message": "El servidor está funcionando correctamente"}), 200

if __name__ == '__main__':
    with app.app_context():
        test_db_connection()  # Verificar la conexión a la base de datos antes de iniciar el servidor
        create_tables()       # Crear las tablas en la base de datos
    app.run(host='0.0.0.0', port=5000)

