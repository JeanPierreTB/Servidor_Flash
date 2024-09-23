from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import threading
import logging
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler

# Configurar el logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Configurar la base de datos PostgreSQL con la URL externa
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dataset_estres_user:KIDw4oaKu2uWIbijxgOCfkCOwRWIsB5V@dpg-crmpfndumphs739ip24g-a.oregon-postgres.render.com/dataset_estres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Cargar el modelo al iniciar la aplicación
modelo = load_model('best_lstm_model_f.h5')

# Definir el modelo de la tabla donde se almacenarán los datos
class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    acc_X = db.Column(db.Float, nullable=False)
    acc_Y = db.Column(db.Float, nullable=False)
    acc_Z = db.Column(db.Float, nullable=False)
    temperatura = db.Column(db.Float, nullable=False)
    frecuencia = db.Column(db.Float, nullable=False)
    estresado = db.Column(db.Integer, nullable=True)  # Permitimos nulos
    persona = db.Column(db.String(100), nullable=False)

# Crear la tabla si no existe
with app.app_context():
    db.create_all()

def realizar_prediccion(datos_normalizados_timestep, new_data):
    logging.info("Prediciendo modelo...")
    probabilidad = modelo.predict(datos_normalizados_timestep)
    umbral = 0.5
    estresado = int(probabilidad > umbral)
    
    # Actualizar el registro con la predicción
    new_data.estresado = estresado
    db.session.commit()

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
            persona=data.get('persona')
        )

        # Agregar el nuevo registro a la sesión
        db.session.add(new_data)
        db.session.commit()

        # Consultar los últimos 5 datos de sensores de la base de datos
        datos_anteriores = SensorData.query.with_entities(
            SensorData.acc_X,
            SensorData.acc_Y,
            SensorData.acc_Z,
            SensorData.frecuencia,
            SensorData.temperatura
        ).order_by(SensorData.id.desc()).limit(5).all()

        # Convertir a array de numpy
        datos_anteriores_array = np.array(datos_anteriores)

        if len(datos_anteriores_array) == 0:
            # No hay registros anteriores, no se normaliza
            datos_normalizados = np.array([[data.get('acc_X'),
                                            data.get('acc_Y'),
                                            data.get('acc_Z'),
                                            data.get('frecuencia'),
                                            data.get('temperatura')]])
        else:
            # Ajustar el scaler con los datos anteriores
            logging.info("Entrando a normalizar...")
            scaler = StandardScaler()
            scaler.fit(datos_anteriores_array)

            # Normalización de los nuevos datos para la predicción
            nuevos_datos = np.array([[data.get('acc_X'), 
                                       data.get('acc_Y'),
                                       data.get('acc_Z'),
                                       data.get('frecuencia'),
                                       data.get('temperatura')]])
            datos_normalizados = scaler.transform(nuevos_datos)
            logging.info("Normalización terminada.")

        # Preparar los datos en el formato adecuado para el modelo
        datos_normalizados_timestep = np.expand_dims(datos_normalizados, axis=1)

        # Iniciar el hilo para realizar la predicción
        threading.Thread(target=realizar_prediccion, args=(datos_normalizados_timestep, new_data)).start()
        
        # Devolver una respuesta inmediata
        return jsonify({"status": "datos recibidos y almacenados, predicción en curso"}), 200
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

@app.route('/sensor-data/latest', methods=['GET'])
def obtener_datos_ultima_persona():
    try:
        # Obtener la última entrada en la base de datos
        last_entry = SensorData.query.order_by(SensorData.id.desc()).first()
        
        if last_entry:
            # Obtener el nombre de la última persona registrada
            nombre_ultima_persona = last_entry.persona
            
            # Obtener todos los datos de la última persona
            datos_ultima_persona = SensorData.query.filter_by(persona=nombre_ultima_persona).all()
            
            # Formatear el resultado
            result = []
            for data in datos_ultima_persona:
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
        else:
            return jsonify({"message": "No se encontraron datos"}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset-database', methods=['GET'])
def reset_database():
    try:
        with app.app_context():
            db.drop_all()  # Eliminar la tabla
            db.create_all()  # Crear la tabla de nuevo
        return jsonify({"status": "base de datos restablecida"}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"message": "El servidor está funcionando correctamente"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
