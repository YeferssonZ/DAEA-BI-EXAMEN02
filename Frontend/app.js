const express = require('express');
const app = express();
const path = require('path');
const mysql = require('mysql');
const cookieParser = require('cookie-parser');
const helmet = require('helmet');

// Configurar el motor de plantillas
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// Middleware para analizar el cuerpo de las solicitudes
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Middleware para analizar las cookies
app.use(cookieParser());

// Middleware para la seguridad (helmet)
app.use(helmet());

// Configuración de la conexión a MySQL
const connection = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: '12345678',
  database: 'voting_app'
});

// Ruta raíz para ingresar el nombre o ID del usuario
app.get('/', (req, res) => {
  res.render('index');
});

// Ruta para manejar el formulario de nombre o ID del usuario
app.post('/login', (req, res) => {
  const userId = req.body.userId; // Obtener el nombre o ID del usuario desde el formulario
  res.cookie('userId', userId); // Establecer la cookie del usuario
  res.redirect('/user'); // Redirigir al perfil del usuario
});

// Ruta para manejar el formulario de nombre o ID del usuario
app.post('/login', (req, res) => {
  const userId = req.body.userId; // Obtener el nombre o ID del usuario desde el formulario
  let query;

  if (isNaN(userId)) {
    // Si userId no es un número, asumimos que es un nombre de usuario
    query = 'SELECT id FROM users WHERE username = ?';
  } else {
    // Si userId es un número, lo tratamos como ID de usuario
    query = 'SELECT id FROM users WHERE id = ?';
  }

  // Ejecutar la consulta SQL correspondiente
  connection.query(query, userId, (error, results) => {
    if (error) {
      throw error;
    } else if (results.length > 0) {
      const foundUserId = results[0].id;
      res.cookie('userId', foundUserId); // Establecer la cookie del usuario
      res.redirect('/user'); // Redirigir al perfil del usuario
    } else {
      // Usuario no encontrado, manejar el caso en consecuencia
      res.send('Usuario no encontrado');
    }
  });
});

// Ruta para mostrar las películas votadas por el usuario y las relaciones entre usuarios
app.get('/user', (req, res) => {
  const userId = req.cookies.userId;

  // Obtener las películas votadas por el usuario actual
  connection.query('SELECT m.title, m.category FROM movies m INNER JOIN votes v ON m.id = v.movie_id WHERE v.user_id = ?', userId, (error, userVotes) => {
    if (error) throw error;

    // Obtener la tabla de usuarios y sus películas votadas (excluyendo al usuario actual)
    connection.query('SELECT u.username, m.title, m.category FROM users u INNER JOIN votes v ON u.id = v.user_id INNER JOIN movies m ON v.movie_id = m.id WHERE u.id != ?', userId, (error, userMovies) => {
      if (error) throw error;

      // Calcular relaciones basadas en las categorías de las películas votadas
      const userRelations = calculateUserRelations(userVotes, userMovies);

      res.render('user', { userVotes, userRelations });
    });
  });
});

// Función para calcular las relaciones entre usuarios basadas en categorías de películas votadas
function calculateUserRelations(userVotes, userMovies) {
  const userRelations = {};

  userMovies.forEach(userMovie => {
    const { username, title, category } = userMovie;
    if (!userRelations[username]) {
      userRelations[username] = [];
    }
    if (userVotes.some(vote => vote.title === title && vote.category === category)) {
      userRelations[username].push({ title, category });
    }
  });

  // Calcular porcentaje de compatibilidad basado en películas votadas en común
  Object.entries(userRelations).forEach(([username, movies]) => {
    const commonVotesCount = movies.length;
    const totalUserVotesCount = userVotes.length;
    const compatibilityPercentage = (commonVotesCount / totalUserVotesCount) * 100;
    userRelations[username] = { movies, compatibilityPercentage };
  });

  return userRelations;
}


// Iniciar el servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor iniciado en http://localhost:${PORT}`);
});
