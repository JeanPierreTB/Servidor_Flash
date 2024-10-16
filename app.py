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
        data_list = SensorData.query.order_by(SensorData.id).all()
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
            datos_ultima_persona = SensorData.query.filter_by(persona=nombre_ultima_persona).order_by(SensorData.id).all()
            
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

@app.route('/sensor-data/update-predictions', methods=['POST'])
def actualizar_predicciones():
    try:
        data = request.json
        updates = data.get('updates', [])

        for update in updates:
            registro_id = update.get('id')
            estresado = update.get('estresado')

            registro = SensorData.query.get(registro_id)
            if registro:
                registro.estresado = estresado
            else:
                print(f"Registro no encontrado para ID: {registro_id}")

        db.session.commit()
        return jsonify({"status": "predicciones actualizadas"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/sensor-data/delete', methods=['DELETE'])
def eliminar_registros():
    try:
        data = request.json
        ids = data.get('ids', [])

        # Eliminar registros con los IDs proporcionados
        registros_a_eliminar = SensorData.query.filter(SensorData.id.in_(ids)).all()
        
        for registro in registros_a_eliminar:
            db.session.delete(registro)

        db.session.commit()
        return jsonify({"status": "registros eliminados"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/personas', methods=['GET'])
def obtener_personas():
    try:
        # Obtener todos los nombres únicos de la tabla SensorData
        personas = db.session.query(SensorData.persona.distinct()).all()
        nombres = [persona[0] for persona in personas]  # Extraer los nombres de los resultados

        return jsonify(nombres), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/sensor-data/persona/<nombre>', methods=['GET'])
def obtener_datos_por_persona(nombre):
    try:
        # Obtener todos los datos de la persona especificada y ordenarlos por id
        datos_persona = SensorData.query.filter_by(persona=nombre).order_by(SensorData.id).all()
        
        if not datos_persona:
            return jsonify({"message": "No se encontraron datos para la persona especificada"}), 404
        
        result = []
        for data in datos_persona:
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

@app.route('/sensor-data/delete-range/<int:id_inicio>/<int:id_fin>', methods=['DELETE'])
def eliminar_registros_por_rango(id_inicio, id_fin):
    try:
        # Eliminar registros cuyo ID esté dentro del rango especificado
        registros_a_eliminar = SensorData.query.filter(SensorData.id.between(id_inicio, id_fin)).all()
        
        if not registros_a_eliminar:
            return jsonify({"message": "No se encontraron registros en el rango especificado"}), 404

        for registro in registros_a_eliminar:
            db.session.delete(registro)

        db.session.commit()
        return jsonify({"status": f"Registros del ID {id_inicio} al ID {id_fin} eliminados"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
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
