import os
from dotenv import load_dotenv
import requests

load_dotenv()

class ErrorAPIClima(Exception):
    """Error personalizado para fallos de la API del clima."""
    pass

class APIClima:
    MENSAJES_HTTP = {
        400: "Solicitud inválida (¿el lugar existe?)",
        401: "API key inválida o no proporcionada",
        403: "Acceso denegado (cuota excedida o key deshabilitada)",
        404: "Recurso no encontrado",
        429: "Demasiadas solicitudes, intenta más tarde",
        500: "Error interno del servidor",
        502: "Bad gateway",
        503: "Servicio no disponible",
    }

    def __init__(self, token):
        self.__base_url = "https://api.weatherapi.com/v1/current.json"
        self.__token = token

    def obtener_clima(self, location: str):
        payload = {"q": location, "lang": "es", "key": self.__token}

        try:
            response = requests.get(url=self.__base_url, params=payload, timeout=10)
        except requests.exceptions.Timeout:
            raise ErrorAPIClima("La solicitud tardó demasiado (timeout)")
        except requests.exceptions.ConnectionError:
            raise ErrorAPIClima("No se pudo conectar. Revisa tu conexión a internet")
        except requests.exceptions.RequestException as e:
            raise ErrorAPIClima(f"Error inesperado en la solicitud: {e}")

        if not response.ok:  # any status code 400 or above
            mensaje = self.MENSAJES_HTTP.get(response.status_code, "Error desconocido")

            # WeatherAPI usually includes details in the JSON body
            try:
                detalle = response.json()["error"]["message"]
            except (ValueError, KeyError):
                detalle = response.text[:100]

            raise ErrorAPIClima(f"[{response.status_code}] {mensaje}: {detalle}")

        try:
            return response.json()
        except ValueError:
            raise ErrorAPIClima("La API devolvió una respuesta que no es JSON válido")

api_clima = APIClima(token=os.getenv("token_weather_api"))

def main():
    while True:
        lugar = input("Ingrese el lugar de donde quiere obtener el clima: ")

        if lugar == "exit":
            print("Saliendo del programa")
            break

        try:
            data = api_clima.obtener_clima(location=lugar)
        except ErrorAPIClima as e:
            print("Error:", e)
            continue

        print(f"Ciudad: {data['location']['name']}, {data['location']['country']}")
        print(f"Temperatura: {data['current']['temp_c']} °C")
        print(f"Condición: {data['current']['condition']['text']}")
        print(f"Humedad: {data['current']['humidity']}%")
        print(f"Viento: {data['current']['wind_kph']} km/h")

main()