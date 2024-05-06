using System;
using System.Threading;
using Newtonsoft.Json;
using MySql.Data.MySqlClient;
using StackExchange.Redis;

namespace Worker
{
    public class Program
    {
        private static ConnectionMultiplexer redisConn;
        private static string redisHost = "localhost";
        private static int redisPort = 6379;

        private static string dbConnectionString = "Server=localhost;User=root;Password=12345678;Database=voting_app";

        public static void Main(string[] args)
        {
            try
            {
                // Establecer conexión a Redis
                redisConn = OpenRedisConnection(redisHost, redisPort);

                Console.WriteLine("Worker iniciado. Escuchando en la cola 'events'...");

                // Escuchar constantemente en la cola de Redis "events"
                while (true)
                {
                    // Obtener un evento de Redis
                    string json = redisConn.GetDatabase().ListLeftPop("events");
                    if (!string.IsNullOrEmpty(json))
                    {
                        dynamic eventData = JsonConvert.DeserializeObject(json);

                        string eventType = eventData.event_type;
                        if (eventType == "user_created")
                        {
                            int userId = Convert.ToInt32(eventData.user_id);
                            Console.WriteLine($"Procesando evento 'user_created' para el usuario '{userId}'");

                            // Procesar evento de nuevo usuario creado
                            ProcessNewUserEvent(userId);
                        }
                        else if (eventType == "vote_created")
                        {
                            int userId = Convert.ToInt32(eventData.user_id);
                            int movieId = Convert.ToInt32(eventData.movie_id);
                            Console.WriteLine($"Procesando evento 'vote_created' para el usuario '{userId}' y la película '{movieId}'");

                            // Procesar evento de nueva votación creada
                            ProcessVoteEvent(userId, movieId);
                        }
                    }
                    else
                    {
                        // Dormir durante un breve período si no hay eventos disponibles en Redis
                        Thread.Sleep(100);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error al procesar evento: {ex.Message}");
            }
        }

        private static ConnectionMultiplexer OpenRedisConnection(string host, int port)
        {
            try
            {
                string redisConnectionString = $"{host}:{port}";
                Console.WriteLine($"Conectando a Redis en {redisConnectionString}");
                return ConnectionMultiplexer.Connect(redisConnectionString);
            }
            catch (RedisConnectionException ex)
            {
                Console.Error.WriteLine($"Error de conexión Redis: {ex.Message}");
                throw;
            }
        }

        private static void ProcessNewUserEvent(int userId)
        {
            try
            {
                using (MySqlConnection dbConnection = new MySqlConnection(dbConnectionString))
                {
                    dbConnection.Open();

                    // Verificar si el usuario ya existe en la base de datos
                    string checkUserQuery = "SELECT id FROM users WHERE id = @userId";
                    MySqlCommand checkUserCommand = new MySqlCommand(checkUserQuery, dbConnection);
                    checkUserCommand.Parameters.AddWithValue("@userId", userId);

                    object existingUser = checkUserCommand.ExecuteScalar();
                    if (existingUser == null)
                    {
                        // El usuario no existe, realizar acciones adicionales si es necesario
                        Console.WriteLine($"Nuevo usuario creado con ID: {userId}");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error al procesar evento 'user_created': {ex.Message}");
            }
        }

        private static void ProcessVoteEvent(int userId, int movieId)
        {
            try
            {
                using (MySqlConnection dbConnection = new MySqlConnection(dbConnectionString))
                {
                    dbConnection.Open();

                    // Verificar si el usuario ya ha votado por esta película
                    string checkVoteQuery = "SELECT id FROM votes WHERE user_id = @userId AND movie_id = @movieId";
                    MySqlCommand checkVoteCommand = new MySqlCommand(checkVoteQuery, dbConnection);
                    checkVoteCommand.Parameters.AddWithValue("@userId", userId);
                    checkVoteCommand.Parameters.AddWithValue("@movieId", movieId);

                    object existingVote = checkVoteCommand.ExecuteScalar();
                    if (existingVote == null)
                    {
                        // Insertar nuevo voto
                        string insertVoteQuery = "INSERT INTO votes (user_id, movie_id) VALUES (@userId, @movieId)";
                        MySqlCommand insertVoteCommand = new MySqlCommand(insertVoteQuery, dbConnection);
                        insertVoteCommand.Parameters.AddWithValue("@userId", userId);
                        insertVoteCommand.Parameters.AddWithValue("@movieId", movieId);
                        insertVoteCommand.ExecuteNonQuery();

                        Console.WriteLine($"Voto registrado para usuario '{userId}' y película '{movieId}'");
                    }
                    else
                    {
                        Console.WriteLine($"El usuario '{userId}' ya ha votado por la película '{movieId}' anteriormente.");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error al procesar evento 'vote_created': {ex.Message}");
            }
        }
    }
}
