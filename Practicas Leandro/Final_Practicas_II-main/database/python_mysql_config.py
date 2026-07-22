from configparser import ConfigParser

def config_db(archivo = 'database/config.ini',seccion='mysql'):
    #Crear un ConfigParser y leer el contenido del archivo config.ini
    parser = ConfigParser()
    parser.read(archivo)

    db= {}

    #Si el archivo tiene la seccion pasada por argumento...
    if parser.has_section(seccion):
        #Leer los items de esa seccion
        items = parser.items(seccion)
        #Recorrer los items y guardarlos en el diccionario db
        for item in items:
            db[item[0]] = item[1]

    else:
        #Lanzar una excepcion (error)
        raise Exception('{0} no se encuentra en el archivo {1}'.format(seccion,archivo))
    return db