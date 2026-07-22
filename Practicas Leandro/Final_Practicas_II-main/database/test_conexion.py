from mysql.connector import MySQLConnection, Error

from python_mysql_config import config_db


def test_conectar():
    db_config = config_db()
    #{'host':'localhost','port':3306}

    conn = None
    try:
        print('Conctando a la base de datos....')
        conn = MySQLConnection(**db_config)
        if conn.is_connected():
            print('Coneccion establecida')
        else:
            print('No se pudo conectar')
    except Error as error:
        print(error)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
            print('Coneccion cerrada')

if __name__ == '__main__':
    test_conectar()
