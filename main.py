# 1. UML -> POO


# 2. Conexion con la base de datos
import os
from dotenv import load_dotenv
load_dotenv()
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
api_clima = APIClima( token = os.getenv("token_weather_api") )

def main():
    while True:
     clima = input(str("Ingrese el lugar de donde quiere obtener el clima: "))
     clima_real = api_clima.obtener_clima(location=clima)
     if clima == "exit":
           print("Saliendo del programa")
           break
     print(clima_real)
     
main()
