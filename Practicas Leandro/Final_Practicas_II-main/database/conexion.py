# database.py
from mysql.connector import MySQLConnection, Error
from PyQt5.QtWidgets import QMessageBox
from database.python_mysql_config import config_db
from error.logger import log  
from datetime import datetime

class Database:
    def __init__(self):
        self.db = None
        self.cursor = None

    def conneccion(self):
        """Establece conexión con la base de datos."""
        try:
            db_config = config_db()
            self.db = MySQLConnection(**db_config)
            self.cursor = self.db.cursor()
        except Error as error:
            log(error, "error")
            QMessageBox.warning(self, 'Error', 'No se pudo finalizar el proceso debido a un error con la base de datos.')

    def desconeccion(self):
        """Cierra la conexión a la base de datos."""
        if self.cursor:
            self.cursor.close()
        if self.db and self.db.is_connected():
            self.db.close()
    
    def obtener_historial(self):
        """Obtiene todos los usuarios de la base de datos."""
        try:
            self.conneccion()
            self.cursor.execute("SELECT * FROM historial") 
            return self.cursor.fetchall()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta: {e}")
        finally:
            self.desconeccion()
    
    def registrar_historial_usuario(self, id_usuario, accion):
        """Registra una acción general realizada por el usuario."""
        try:
            self.conneccion()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = """
                INSERT INTO historial (IdUsuario, Fecha_Hora, Accion)
                VALUES (%s, %s, %s)
            """
            self.cursor.execute(query, (id_usuario, fecha_actual, accion))
            self.db.commit()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al registrar historial de usuario: {e}")
        finally:
            self.desconeccion()
    
    def obtener_usuario_por_id(self, user_id):
        """Obtiene el usuario por su ID."""
        try:
            self.conneccion()
            self.cursor.execute('SELECT * FROM usuarios WHERE IdUsuarios = %s', (user_id,))
            return self.cursor.fetchone()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta: {e}")
        finally:
            self.desconeccion()


    def obtener_usuario(self, nombre):
        """Obtiene el usuario"""
        try:
            self.conneccion()
            self.cursor.execute('SELECT * FROM usuarios WHERE NombreUsuario = %s', (nombre,))
            return self.cursor.fetchone()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta: {e}")
        finally:
            self.desconeccion()

    def obtener_usuarios(self):
        """Obtiene todos los usuarios de la base de datos."""
        try:
            self.conneccion()
            self.cursor.execute("SELECT * FROM usuarios") 
            return self.cursor.fetchall()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta: {e}")
        finally:
            self.desconeccion()
    
    def insertar_usuario(self, nombre, contrasena, rol,feha_creacion):
        """Inserta un nuevo usuario con un rol en la base de datos."""
        try:
            self.conneccion()
            query = "INSERT INTO usuarios (NombreUsuario, Contrasena,Grupo,FechaCreacion) VALUES (%s, %s, %s,%s)"
            self.cursor.execute(query, (nombre, contrasena, rol,feha_creacion))
            self.db.commit()  
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al insertar usuario: {e}")
        finally:
            self.desconeccion()

    def eliminar_usuario(self, user_id):
        """Elimina un usuario de la base de datos por su ID."""
        try:
            self.conneccion()
            query = "DELETE FROM usuarios WHERE IdUsuarios = %s"
            self.cursor.execute(query, (user_id,))
            self.db.commit()  
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al eliminar usuario: {e}")
        finally:
            self.desconeccion()

    def actualizar_ultimo_acceso(self, user_id):
        """Actualiza el último acceso del usuario en la base de datos."""
        try:
            self.conneccion()
            query = "UPDATE usuarios SET FechaUltimoAcceso = %s WHERE IdUsuarios = %s"
            self.cursor.execute(query, (datetime.now(), user_id))
            self.db.commit()  
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al eliminar usuario: {e}")
        finally:
            self.desconeccion()
    
    def modificar_usuario(self, user_id, nuevo_nombre, nueva_contrasena, nuevo_rol, fecha_modificacion):
        """Modifica los datos de un usuario en la base de datos."""
        try:
            self.conneccion()  
            query = """UPDATE usuarios 
                    SET NombreUsuario = %s, Contrasena = %s, Grupo = %s, FechaModificacion = %s
                    WHERE IdUsuarios = %s"""
            self.cursor.execute(query, (nuevo_nombre, nueva_contrasena, nuevo_rol, fecha_modificacion, user_id))
            self.db.commit()
            
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al modificar usuario: {e}")
            
        finally:
            self.desconeccion() 
    
    def obtener_peliculas(self):
        """Obtiene todas las películas de la base de datos."""
        try:
            self.conneccion()
            self.cursor.execute("SELECT * FROM peliculas")  
            return self.cursor.fetchall()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de películas: {e}")
        finally:
            self.desconeccion()
    

    def insertar_pelicula(self, nombre, resumen, pais_origen, fecha_estreno, duracion, clasificacion, imagen_ruta, fecha_inicio, fecha_fin):
        """Inserta una nueva película en la base de datos y retorna el ID de la película."""
        try:
            self.conneccion()

            # Consulta SQL para insertar en la base de datos
            query = """
            INSERT INTO peliculas (NombrePelicula, Resumen, Imagen, PaisOrigen, FechaEstrenoMundial, FechaInicio, FechaFin, Duracion, Clasificacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            valores = (nombre, resumen, imagen_ruta, pais_origen, fecha_estreno, fecha_inicio, fecha_fin, duracion, clasificacion)

            self.cursor.execute(query, valores)
            self.db.commit()  # Confirmar la transacción

            # Obtener el ID de la película recién insertada
            return self.cursor.lastrowid

        except Error as e:
            log(e, "error")
            raise Exception(f"Error al insertar película: {e}")

        finally:
            self.desconeccion()

    def modificar_pelicula(self, idPelicula, nombre, resumen, pais_origen, fecha_estreno, duracion, clasificacion, imagen_ruta, fecha_inicio, fecha_fin):
        """Modifica los datos de una película existente en la base de datos."""
        try:
            self.conneccion()

            # Consulta SQL para actualizar la película
            query = """
                UPDATE peliculas
                SET NombrePelicula = %s, Resumen = %s, Imagen = %s, PaisOrigen = %s,
                    FechaEstrenoMundial = %s, FechaInicio = %s, FechaFin = %s, 
                    Duracion = %s, Clasificacion = %s
                WHERE IdPelicula = %s
            """
            valores = (nombre, resumen, imagen_ruta, pais_origen, fecha_estreno, 
                    fecha_inicio, fecha_fin, duracion, clasificacion, idPelicula)

            self.cursor.execute(query, valores)
            self.db.commit()  # Confirmar la transacción

            if self.cursor.rowcount == 0:
                # Si no se afectó ninguna fila, no hubo cambios, pero no es un error
                print("No se realizaron cambios en los datos de la película.")
            return True  # Retorna True incluso si no hubo cambios

        except Exception as e:
            log(e, "error")
            raise Exception(f"Error al actualizar película: {e}")

        finally:
            self.desconeccion()




    def eliminar_pelicula(self, pelicula_id):
        """Elimina una película de la base de datos por su ID."""
        try:
            self.conneccion()
            query = "DELETE FROM peliculas WHERE IdPelicula = %s"
            self.cursor.execute(query, (pelicula_id,))
            self.db.commit()  # Confirma los cambios en la base de datos.
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al eliminar película: {e}")
        finally:
            self.desconeccion()
    
    def obtener_generos(self):
        """Obtiene todos los géneros de la base de datos."""
        try:
            self.conneccion()
            self.cursor.execute("SELECT * FROM generos")  
            return self.cursor.fetchall()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de géneros: {e}")
        finally:
            self.desconeccion()

    def insertar_generos(self, id_pelicula, id_genero):
        """Inserta un registro en la tabla peliculagenero."""
        try:
            self.conneccion()
            query = """
            INSERT INTO peliculagenero (IdPelicula, IdGenero)
            VALUES (%s, %s)
            """
            valores = (id_pelicula, id_genero)
            self.cursor.execute(query, valores)
            self.db.commit()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al insertar el género para la película: {e}")
        finally:
            self.desconeccion()
    
    def obtener_generos_pelicula(self, pelicula_id):
        """Obtiene los géneros asociados a una película por su ID."""
        try:
            self.conneccion()
            query = """
            SELECT g.NombreGenero 
            FROM peliculagenero pg
            JOIN generos g ON pg.IdGenero = g.IdGeneros
            WHERE pg.IdPelicula = %s
            """
            self.cursor.execute(query, (pelicula_id,))
            return [row[0] for row in self.cursor.fetchall()]  # Retorna una lista de nombres de géneros
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de géneros de la película: {e}")
        finally:
            self.desconeccion()


    def obtener_id_genero_por_nombre(self, nombre_genero):
        """Obtiene el ID de un género por su nombre."""
        try:
            self.conneccion()
            query = "SELECT IdGeneros FROM generos WHERE NombreGenero = %s"
            self.cursor.execute(query, (nombre_genero,))
            resultado = self.cursor.fetchone()
            return resultado[0] if resultado else None
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al obtener el ID del género: {e}")
        finally:
            self.desconeccion()
    
    def obtener_datos_pelicula(self, pelicula_id):
        """Obtiene los datos de una película por su ID."""
        try:
            self.conneccion()
            query = "SELECT NombrePelicula, Resumen, PaisOrigen, FechaEstrenoMundial, FechaInicio, FechaFin, Duracion, Clasificacion, Imagen FROM peliculas WHERE IdPelicula = %s"
            self.cursor.execute(query, (pelicula_id,))
            resultado = self.cursor.fetchone()

            if resultado:
                # Mapear los resultados a un diccionario
                datos_pelicula = {
                    'nombre': resultado[0],
                    'resumen': resultado[1],
                    'pais_origen': resultado[2],
                    'fecha_estreno': resultado[3],
                    'fecha_inicio': resultado[4],
                    'fecha_fin': resultado[5],
                    'duracion': resultado[6],
                    'clasificacion': resultado[7],
                    'imagen': resultado[8]
                }
                print(resultado)
                return datos_pelicula
            else:
                return None

        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de la película: {e}")
        
        finally:
            self.desconeccion()
    
    def eliminar_generos_pelicula(self, id_pelicula):
        """Elimina todos los géneros asociados a una película."""
        try:
            self.conneccion()
            query = """
            DELETE FROM peliculagenero WHERE IdPelicula = %s
            """
            self.cursor.execute(query, (id_pelicula,))
            self.db.commit()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al eliminar géneros de la película: {e}")
        finally:
            self.desconeccion()

    def obtener_id_genero(self, nombre_genero):
        """Obtiene el ID de un género por su nombre."""
        try:
            self.conneccion()
            query = """
            SELECT IdGeneros FROM generos WHERE NombreGenero = %s
            """
            self.cursor.execute(query, (nombre_genero,))
            resultado = self.cursor.fetchone()
            return resultado[0] if resultado else None
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al obtener el ID del género: {e}")
        finally:
            self.desconeccion()
    
    def obtener_salas(self):
        """Obtiene todos las salas de la base de datos."""
        try:
            self.conneccion()
            self.cursor.execute("SELECT * FROM salas")  
            return self.cursor.fetchall()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de salas: {e}")
        finally:
            self.desconeccion()

    def obtener_funciones(self):
        """Obtiene todos las salas de la base de datos."""
        try:
            self.conneccion()
            self.cursor.execute("SELECT * FROM funciones")  
            return self.cursor.fetchall()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de funciones: {e}")
        finally:
            self.desconeccion()
    
    def insertar_funcion(self, idPelicula, fecha_hora, idSala, precio):
        """Inserta una nueva función en la base de datos."""
        try:
            self.conneccion()  # Asegúrate que se conecta correctamente
            query = "INSERT INTO funciones (IdPelicula, Fecha_hora, IdSala, Precio) VALUES (%s, %s, %s, %s)"
            self.cursor.execute(query, (idPelicula, fecha_hora, idSala, precio))
            self.db.commit()
            print("Función insertada correctamente.")
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al insertar función: {e}")
        finally:
            self.desconeccion()
    
    def funcion_ya_existe(self, fecha_hora, idSala):
        """Verifica si ya existe una función en la misma sala y hora."""
        try:
            self.conneccion()
            query = """SELECT COUNT(*) FROM funciones WHERE Fecha_hora = %s AND IdSala = %s"""
            self.cursor.execute(query, (fecha_hora, idSala))
            resultado = self.cursor.fetchone()[0]
            return resultado > 0  # True si ya existe una función
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al verificar función: {e}")
        finally:
            self.desconeccion()

    def obtener_funcion_por_id(self, funcion_id):
        """Obtiene la información de una función por su ID."""
        try:
            self.conneccion()
            query = """SELECT IdFunciones, IdPelicula, Fecha_hora, IdSala, Precio FROM funciones WHERE IdFunciones = %s"""
            self.cursor.execute(query, (funcion_id,))
            funcion = self.cursor.fetchone()  # Obtiene una única fila
            return funcion
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al obtener la función: {e}")
        finally:
            self.desconeccion()


    def eliminar_funcion(self, funcion_id):
        """Elimina una función de la base de datos por su ID."""
        try:
            self.conneccion()
            query = """DELETE FROM funciones WHERE IdFunciones = %s"""
            self.cursor.execute(query, (funcion_id,))
            self.db.commit()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al eliminar la función: {e}")
        finally:
            self.desconeccion()
    
    def actualizar_funcion(self, funcion_id, idPelicula, fecha_hora, idSala, precio):
        """Actualiza una función en la base de datos."""
        try:
            self.conneccion()
            query = """UPDATE funciones SET IdPelicula = %s, Fecha_hora = %s, IdSala = %s, Precio = %s WHERE IdFunciones = %s"""
            self.cursor.execute(query, (idPelicula, fecha_hora, idSala, precio, funcion_id))
            self.db.commit()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al actualizar la función: {e}")
        finally:
            self.desconeccion()
    
    def funcion_ya_existe(self, fecha_hora, idSala, idFuncion=None):
        """Verifica si ya existe una función en la misma sala y hora, excluyendo una función específica."""
        try:
            self.conneccion()
            query = """SELECT COUNT(*) FROM funciones 
                    WHERE Fecha_hora = %s AND IdSala = %s"""
            params = [fecha_hora, idSala]

            if idFuncion:
                query += " AND IdFunciones != %s"
                params.append(idFuncion)

            self.cursor.execute(query, tuple(params))
            resultado = self.cursor.fetchone()[0]
            return resultado > 0  # True si ya existe otra función en esa sala y hora
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al verificar función: {e}")
        finally:
            self.desconeccion()
    
    def contar_funciones_por_dia(self, fecha, idSala):
        """Cuenta cuántas funciones hay en la misma sala en un día específico."""
        try:
            self.conneccion()
            query = """SELECT COUNT(*) FROM funciones 
                    WHERE DATE(Fecha_hora) = %s AND IdSala = %s"""
            self.cursor.execute(query, (fecha, idSala))
            return self.cursor.fetchone()[0]
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al contar funciones: {e}")
        finally:
            self.desconeccion()
    
    def obtener_funciones_desde_hoy(self, fecha_actual):
        """Obtiene todas las funciones desde el día especificado en adelante."""
        try:
            self.conneccion()
            query = "SELECT * FROM funciones WHERE DATE(Fecha_hora) >= %s ORDER BY Fecha_hora ASC"
            self.cursor.execute(query, (fecha_actual,))
            return self.cursor.fetchall()
        except Error as e:
            print("Error al obtener funciones desde hoy:", e)
            return None
        finally:
            self.desconeccion()
    
    
    def obtener_Ventas_idFuncion(self, funcion_id):
        """Obtiene todas las ventas de la base de datos relacionadas con un ID de función específico."""
        try:
            self.conneccion()
            query = """SELECT * FROM ventaboletos WHERE IdFuncion = %s"""
            self.cursor.execute(query, (funcion_id,))
            return self.cursor.fetchall()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de ventaboletos: {e}")
        finally:
            self.desconeccion()
    
    def obtener_asientos_reservados(self, id_funcion):
        """Obtiene los asientos reservados de la base de datos para una función específica."""
        try:
            self.conneccion()
            query = """SELECT NumeroButaca FROM ventaboletos WHERE IdFuncion = %s"""
            self.cursor.execute(query, (id_funcion,))
            asientos_reservados = [fila[0] for fila in self.cursor.fetchall()]
            return asientos_reservados
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de asientos reservados: {e}")
        finally:
            self.desconeccion()
    
    def obtener_sala_por_id(self, sala_id):
        """Obtiene la información de una sala específica por su ID."""
        try:
            self.conneccion()
            query = """SELECT * FROM salas WHERE IdSalas = %s"""
            self.cursor.execute(query, (sala_id,))
            sala = self.cursor.fetchone()
            return {
                'IdSala': sala[0],
                'NombreSala': sala[1],
                'NumeroButacas': sala[2]
            }
        except Error as e:
            log(e, "error")
            raise Exception(f"Error durante la consulta de la sala: {e}")
        finally:
            self.desconeccion()
        
    def guardar_asientos(self, id_funcion, id_usuario, asientos):
        try:
            self.conneccion()
            query = """INSERT INTO ventaboletos (IdFuncion, IdUsuario, Fecha_hora, NumeroButaca)
                    VALUES (%s, %s, NOW(), %s)"""
            for asiento in asientos:
                self.cursor.execute(query, (id_funcion, id_usuario, asiento)) 
            self.db.commit()
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al guardar los asientos: {e}")
        finally:
            self.desconeccion()
    
    def obtener_peliculas_mas_vistas(self):
        try:
            self.conneccion()
            
            # Define la consulta SQL para obtener las 10 películas más vistas incluyendo el nombre de la película
            query = """
                SELECT p.IdPelicula, p.NombrePelicula, COUNT(v.IdVenta) AS CantidadVentas
                FROM peliculas p
                JOIN funciones f ON p.IdPelicula = f.IdPelicula
                JOIN ventaboletos v ON f.IdFunciones = v.IdFuncion
                GROUP BY p.IdPelicula, p.NombrePelicula
                ORDER BY CantidadVentas DESC
                LIMIT 10
            """
            
            # Ejecuta la consulta y obtiene los resultados
            self.cursor.execute(query)
            peliculas_mas_vistas = self.cursor.fetchall()
            
            # Procesa y devuelve los resultados
            resultado = [{"IdPelicula": row[0], "NombrePelicula": row[1], "CantidadVentas": row[2]} for row in peliculas_mas_vistas]
            return resultado
        
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al obtener las películas más vistas: {e}")
        
        finally:
            self.desconeccion()

    
    def obtener_generos_mas_rentables(self):
        try:
            self.conneccion()
            
            # Define la consulta SQL para obtener los 5 géneros más rentables
            query = """
                SELECT g.NombreGenero, SUM(f.Precio) AS ingresos_totales
                FROM ventaboletos vb
                JOIN funciones f ON vb.IdFuncion = f.IdFunciones
                JOIN peliculas p ON f.IdPelicula = p.IdPelicula
                JOIN peliculagenero pg ON p.IdPelicula = pg.IdPelicula
                JOIN generos g ON pg.IdGenero = g.IdGeneros
                GROUP BY g.NombreGenero
                ORDER BY ingresos_totales DESC
                LIMIT 5
            """
            
            # Ejecuta la consulta y obtiene los resultados
            self.cursor.execute(query)
            generos_mas_rentables = self.cursor.fetchall()
            
            # Procesa y devuelve los resultados
            resultado = [{"Genero": row[0], "IngresosTotales": row[1]} for row in generos_mas_rentables]
            return resultado
        
        except Error as e:
            log(e, "error")
            raise Exception(f"Error al obtener los géneros más rentables: {e}")
        
        finally:
            self.desconeccion()


    
