from flask import Flask, render_template, request, g, jsonify
from redis import Redis, RedisError
import mysql.connector
import random
import json
import logging

app = Flask(__name__)

# Configuración de la base de datos MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678',
    'database': 'voting_app'
}

# Configuración de la cola Redis
redis_host = 'localhost'
redis_port = 6379

# Configurar el registro de errores
gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_db():
    """Obtener una conexión a la base de datos MySQL."""
    if not hasattr(g, 'mysql_db'):
        g.mysql_db = mysql.connector.connect(**db_config)
    return g.mysql_db

def emit_user_created_event(user_id):
    """Emitir un evento de nuevo usuario a través de Redis."""
    redis_conn = get_redis()
    if redis_conn is not None:
        event_data = json.dumps({'event_type': 'user_created', 'user_id': user_id})
        redis_conn.rpush('events', event_data)
    else:
        app.logger.error("Redis no disponible, no se pudo emitir el evento de nuevo usuario.")
        return None

def emit_vote_created_event(user_id, movie_id):
    """Emitir un evento de nueva votación a través de Redis."""
    redis_conn = get_redis()
    if redis_conn is not None:
        event_data = json.dumps({'event_type': 'vote_created', 'user_id': user_id, 'movie_id': movie_id})
        redis_conn.rpush('events', event_data)
    else:
        app.logger.error("Redis no disponible, no se pudo emitir el evento de nueva votación.")
        return None

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        # Obtener el ID de la película votada desde el formulario
        movie_id = request.form.get('vote')

        if movie_id is None:
            return jsonify({"error": "El campo 'vote' no se encontró en la solicitud POST"}), 400

        # Obtener la IP del cliente como identificador único
        ip_address = request.remote_addr

        # Verificar si el usuario ya existe en la base de datos
        user_id = get_or_create_user_id(ip_address)

        # Verificar si el usuario ya votó por esta película
        if not has_user_voted(user_id, movie_id):
            # Emitir un evento de nueva votación
            emit_vote_created_event(user_id, movie_id)
            confirmation_message = "Voto registrado para usuario ID: {}, película ID: {}".format(user_id, movie_id)
        else:
            confirmation_message = "¡Ya has votado por esta película anteriormente!"

        # Obtener lista de películas
        movies = get_movies()
        voter_id = request.cookies.get('voter_id') or hex(random.getrandbits(64))[2:-1]

        return render_template('index.html', movies=movies, voter_id=voter_id, confirmation_message=confirmation_message)

    # Obtener lista de películas
    movies = get_movies()
    voter_id = request.cookies.get('voter_id') or hex(random.getrandbits(64))[2:-1]

    return render_template('index.html', movies=movies, voter_id=voter_id)

def get_or_create_user_id(ip_address):
    """Obtener o crear ID de usuario basado en la dirección IP."""
    db = get_db()
    cursor = db.cursor()

    try:
        # Buscar usuario por dirección IP
        cursor.execute("SELECT id FROM users WHERE username = %s", (ip_address,))
        user = cursor.fetchone()

        if not user:
            # Crear nuevo usuario si no existe
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (ip_address, ''))
            db.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user[0]

        # Consumir todos los resultados para evitar el error
        cursor.fetchall()

        return user_id
    except mysql.connector.Error as err:
        app.logger.error(f"Error al obtener/crear usuario: {err}")
        db.rollback()
        return None
    finally:
        cursor.close()

def has_user_voted(user_id, movie_id):
    """Verificar si el usuario ya votó por la película."""
    db = get_db()
    cursor = db.cursor()

    try:
        # Verificar si existe un voto para este usuario y película
        cursor.execute("SELECT id FROM votes WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
        vote = cursor.fetchone()

        return vote is not None
    except mysql.connector.Error as err:
        app.logger.error(f"Error al verificar si el usuario ha votado: {err}")
        return False
    finally:
        cursor.close()

def get_movies():
    """Obtener la lista de películas disponibles desde MySQL."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id, title, category FROM movies")
    movies = cursor.fetchall()

    cursor.close()
    return movies

def get_redis():
    """Obtener una conexión a Redis."""
    if not hasattr(g, 'redis'):
        try:
            g.redis = Redis(host=redis_host, port=redis_port, socket_timeout=5)
        except RedisError as e:
            app.logger.error(f"Error de conexión Redis: {str(e)}")
            g.redis = None
    return g.redis

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
