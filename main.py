# 1. UML -> POO
class Proyecto:
    def __init__(self, id, nombre, pais, ciudad, fecha_entrega):
        self.__id = id
        self.__nombre = nombre
        self.__pais = pais
        self.__ciudad = ciudad
        self.__fecha_entrega = fecha_entrega
    def obtener_id(self): return self.__id
    def obtener_nombre(self): return self.__nombre
    def obtener_pais(self): return self.__pais
    def obtener_ciudad(self): return self.__ciudad
    def obtener_fecha_entrega(self): return self.__fecha_entrega

# 2. Conexion con la base de datos
import oracledb
import os
from dotenv import load_dotenv
load_dotenv()
class Database:
    def __init__(self, user, password, dsn):
        self.__user = user
        self.__password = password
        self.__dsn = dsn
    def get_connection(self):
        connection = oracledb.connect(
            user = self.__user,
            password = self.__password,
            dsn = self.__dsn
        )
        return connection
database = Database(
    user= os.getenv("user"),
    password= os.getenv("password"),
    dsn= os.getenv("dsn")
)
# 3. Repositorios
class RepositorioProyecto:
    def __init__(self):
        pass
    def guardar(self, connection: oracledb.Connection, proyecto: Proyecto):
        cursor = connection.cursor()
        cursor.execute(
            statement = "INSERT INTO PROYECTOS(id, nombre, pais, ciudad, fecha_entrega) VALUES (:id, :nombre, :pais, :ciudad, :fecha_entrega)",
            parameters = { 
                "id":proyecto.obtener_id(), 
                "nombre":proyecto.obtener_nombre(), 
                "pais":proyecto.obtener_pais(), 
                "ciudad":proyecto.obtener_ciudad(), 
                "fecha_entrega":proyecto.obtener_fecha_entrega() 
            }
        )
        connection.commit()
        connection.close()
# 4. Consultas a la API
import requests

class APIClima:
    def __init__(self, token):
        self.__base_url = "https://api.weatherapi.com/v1/current.json"
        self.__token = token
    def obtener_clima(self, location: str):
        payload = { "q" : location, "lang": "es", "key": self.__token}
        response = requests.get(
            url = self.__base_url,
            params = payload
        )
        data = response.json()
        return data

class RepositorioClima:
    def __init__(self):
        pass
    def guardar(self, connection: oracledb.Connection, informacion_climatica):
        cursor = connection.cursor()
        payload = {
            "id_consulta": 1,
            "locacion": informacion_climatica["location"]["name"],
            "region": informacion_climatica["location"]["region"],
            "pais": informacion_climatica["location"]["country"],
            "fecha_consulta": informacion_climatica["current"]["last_updated"],
            "temperatura": informacion_climatica["current"]["temp_c"],
            "humedad": informacion_climatica["current"]["humidity"]
        }
        cursor.execute(
            statement = "INSERT INTO CONSULTAS_CLIMA(id_consulta, locacion, region, pais, fecha_consulta, temperatura, humedad) VALUES (:id_consulta, :locacion, :region, :pais, :fecha_consulta, :temperatura, :humedad)",
            parameters = payload
        )
        connection.commit()
        connection.close()

api_clima = APIClima( token = os.getenv("token_weather_api") )
clima_lampa = api_clima.obtener_clima(location="Lampa, Chile")

repositorio_clima = RepositorioClima()
repositorio_clima.guardar(connection=database.get_connection(), informacion_climatica=clima_lampa )