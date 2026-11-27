# Filtrar valores de clima_real

Started 2026-11-27 00:05 UTC · Last updated 2026-11-27 01:26 UTC · 10 messages


---

### You · 2026-11-27 00:05 UTC

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
    e = str
    while True:
     clima = input(str("Ingrese el lugar de donde quiere obtener el clima: "))
     clima_real = api_clima.obtener_clima(location=clima)
     if clima == "exit":
           print("Saliendo del programa")
           break
     print(clima_real)
main()


how do i make this only output certain values from clima_real

---

### Claude · 2026-11-27 00:05 UTC

You can pull specific values out of the dictionary that `response.json()` returns. WeatherAPI's `current.json` response looks like this:

```json
{
  "location": {"name": "Santiago", "region": "...", "country": "Chile", "localtime": "..."},
  "current": {"temp_c": 18.0, "condition": {"text": "Soleado"}, "humidity": 40, "wind_kph": 12.0, ...}
}
```

So you access values with nested keys: `data["current"]["temp_c"]`.

Here's your code with that applied, plus a few small fixes:

```python
import os
from dotenv import load_dotenv
import requests

load_dotenv()

class APIClima:
    def __init__(self, token):
        self.__base_url = "https://api.weatherapi.com/v1/current.json"
        self.__token = token

    def obtener_clima(self, location: str):
        payload = {"q": location, "lang": "es", "key": self.__token}
        response = requests.get(url=self.__base_url, params=payload)
        return response.json()

api_clima = APIClima(token=os.getenv("token_weather_api"))

def main():
    while True:
        lugar = input("Ingrese el lugar de donde quiere obtener el clima: ")

        if lugar == "exit":
            print("Saliendo del programa")
            break

        data = api_clima.obtener_clima(location=lugar)

        # The API returns an "error" key if the location is invalid
        if "error" in data:
            print("Error:", data["error"]["message"])
            continue

        print(f"Ciudad: {data['location']['name']}, {data['location']['country']}")
        print(f"Temperatura: {data['current']['temp_c']} °C")
        print(f"Condición: {data['current']['condition']['text']}")
        print(f"Humedad: {data['current']['humidity']}%")
        print(f"Viento: {data['current']['wind_kph']} km/h")

main()
```

What changed:

- **Selecting values:** `data['current']['temp_c']` digs into the nested dictionaries. Add or remove lines for whatever fields you want. You can print `data` once to see all available keys.
- **Moved the `exit` check before the API call.** Before, typing "exit" made a pointless request to the API first.
- **Error handling:** an invalid city returns `{"error": {...}}` instead of `location`/`current`, which would otherwise cause a `KeyError`.
- **Removed `e = str`** (unused) and `input(str(...))` (the `str()` is redundant).

If you'd rather have the class return only the values you need, you can do the filtering inside `obtener_clima` and return a smaller dict:

```python
        data = response.json()
        if "error" in data:
            return data
        return {
            "ciudad": data["location"]["name"],
            "temp_c": data["current"]["temp_c"],
            "condicion": data["current"]["condition"]["text"],
        }
```

Safer still, use `.get()` (e.g. `data["current"].get("uv")`) for fields that might be missing, since it returns `None` instead of raising an error.

---

### You · 2026-11-27 00:17 UTC

add an error handler if the API returns an error like 400, 404, 401 and so on

---

### Claude · 2026-11-27 00:17 UTC

Here's a version with error handling at two levels: HTTP status codes, and network failures (no internet, timeout).

```python
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
```

Key points:

- **`response.ok`** is `True` for status codes below 400, so any 4xx or 5xx goes into the error branch without listing each code.
- **`MENSAJES_HTTP`** gives a friendly message per code. Unlisted codes fall back to "Error desconocido".
- **The JSON body detail** is appended because WeatherAPI explains the real cause there (e.g. "No matching location found").
- **`timeout=10`** matters: without it, `requests` can hang forever if the server doesn't respond.
- **Custom exception:** the class raises `ErrorAPIClima` and `main()` decides what to do (print and continue). This keeps the API class free of `print` calls, so it's reusable.

WeatherAPI doesn't return 404 for an unknown city. It returns **400** with an error code of 1006 ("No matching location found"). Likewise, a bad key gives 401 and an exceeded quota gives 403, so your 400/401 cases will be the ones you hit most.

Also, `os.getenv("token_weather_api")` returns `None` if the variable is missing from your `.env`. You could add a check in `__init__` that raises an error early if `token is None`.

---

### You · 2026-11-27 00:42 UTC

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


implement try/except for managing exceptions

---

### Claude · 2026-11-27 00:43 UTC

Your code already uses `try/except` for the request and for `ErrorAPIClima`. What's still unprotected is:

- Parsing the response (`KeyError` if a field is missing)
- A missing token (`None` from `.env`)
- Ctrl+C or Ctrl+D while at the `input()` prompt
- Any other unexpected error crashing the loop

Here's a version that covers those:

```python
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
        if not token:
            raise ValueError("Falta el token. Define 'token_weather_api' en tu archivo .env")
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

        if not response.ok:
            mensaje = self.MENSAJES_HTTP.get(response.status_code, "Error desconocido")
            try:
                detalle = response.json()["error"]["message"]
            except (ValueError, KeyError, TypeError):
                detalle = response.text[:100]
            raise ErrorAPIClima(f"[{response.status_code}] {mensaje}: {detalle}")

        try:
            return response.json()
        except ValueError:
            raise ErrorAPIClima("La API devolvió una respuesta que no es JSON válido")


def mostrar_clima(data: dict):
    """Imprime los datos. Lanza KeyError si falta algún campo esperado."""
    print(f"Ciudad: {data['location']['name']}, {data['location']['country']}")
    print(f"Temperatura: {data['current']['temp_c']} °C")
    print(f"Condición: {data['current']['condition']['text']}")
    print(f"Humedad: {data['current']['humidity']}%")
    print(f"Viento: {data['current']['wind_kph']} km/h")


def main():
    try:
        api_clima = APIClima(token=os.getenv("token_weather_api"))
    except ValueError as e:
        print("Error de configuración:", e)
        return

    while True:
        try:
            lugar = input("Ingrese el lugar de donde quiere obtener el clima: ").strip()

            if lugar.lower() == "exit":
                print("Saliendo del programa")
                break

            if not lugar:
                print("Debes ingresar un lugar.")
                continue

            data = api_clima.obtener_clima(location=lugar)
            mostrar_clima(data)

        except ErrorAPIClima as e:
            print("Error de la API:", e)
        except (KeyError, TypeError) as e:
            print(f"La respuesta de la API no tiene el formato esperado (falta: {e})")
        except (KeyboardInterrupt, EOFError):
            print("\nPrograma interrumpido. Saliendo...")
            break
        except Exception as e:
            print(f"Error inesperado: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
```

What changed:

- **Token validation in `__init__`:** raises `ValueError` if the token is missing, and `main()` catches it and exits cleanly instead of sending a request that fails with 401.
- **The `api_clima` object is created inside `main()`**, so that configuration error can be handled with `try/except`. At module level it would crash on import.
- **`mostrar_clima()` is a separate function:** the printing is where `KeyError` can happen, so it sits inside the `try`, and the `except (KeyError, TypeError)` branch handles it.
- **Everything in the loop is inside one `try`:** each exception type gets its own message, in order from most specific to most general. `except Exception` must come last, otherwise it would swallow the others.
- **`KeyboardInterrupt` and `EOFError`:** Ctrl+C or Ctrl+D now exit gracefully instead of printing a traceback.
- **Input cleanup:** `.strip()` and `.lower()` make `" Exit "` work, and empty input is rejected without hitting the API.
- **`if __name__ == "__main__":`** keeps `main()` from running if you import this file elsewhere.

If you want a failure to stop the program instead of continuing the loop, replace `continue` or the fall-through with `break` in the relevant `except` branch.

---

### You · 2026-11-27 01:23 UTC

import os
from dotenv import load_dotenv
import requests
load_dotenv()





url = "https://currencyapi.net/api/v2/rates"
params = {
    "key": os.getenv("CURRENCY_API_KEY"),
    "base": "USD",
    "output": "JSON"
}

response = requests.get(url, params=params)
data = response.json()

print(data)


make this print the data neatly, catch errors and display the reason, and then give the user the choice on how much dollars to convert to

---

### Claude · 2026-11-27 01:23 UTC

Here's a version that fetches the rates, prints them in a table, handles errors with the reason, and lets the user choose an amount and a target currency.

```python
import os
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

URL = "https://currencyapi.net/api/v2/rates"


class ErrorAPIMoneda(Exception):
    """Error personalizado para fallos de la API de divisas."""
    pass


def obtener_tasas(base: str = "USD") -> dict:
    api_key = os.getenv("CURRENCY_API_KEY")
    if not api_key:
        raise ErrorAPIMoneda("Falta CURRENCY_API_KEY en tu archivo .env")

    params = {"key": api_key, "base": base, "output": "JSON"}

    try:
        response = requests.get(URL, params=params, timeout=10)
    except requests.exceptions.Timeout:
        raise ErrorAPIMoneda("La solicitud tardó demasiado (timeout)")
    except requests.exceptions.ConnectionError:
        raise ErrorAPIMoneda("No se pudo conectar. Revisa tu conexión a internet")
    except requests.exceptions.RequestException as e:
        raise ErrorAPIMoneda(f"Error inesperado en la solicitud: {e}")

    # Try to parse the body first: the API may explain the error there
    try:
        data = response.json()
    except ValueError:
        data = None

    if not response.ok:
        detalle = _extraer_detalle(data) or response.text[:100] or response.reason
        raise ErrorAPIMoneda(f"HTTP {response.status_code}: {detalle}")

    if data is None:
        raise ErrorAPIMoneda("La API devolvió una respuesta que no es JSON válido")

    # Some APIs return HTTP 200 with an error inside the body
    if data.get("valid") is False or "error" in data:
        raise ErrorAPIMoneda(_extraer_detalle(data) or "La API reportó un error sin detalles")

    if "rates" not in data:
        raise ErrorAPIMoneda("La respuesta no contiene el campo 'rates'")

    return data


def _extraer_detalle(data) -> str | None:
    """Intenta sacar un mensaje de error del cuerpo JSON."""
    if not isinstance(data, dict):
        return None
    error = data.get("error")
    if isinstance(error, dict):
        return error.get("message") or error.get("info") or str(error)
    if error:
        return str(error)
    return data.get("message")


def mostrar_tasas(data: dict, columnas: int = 4):
    rates = data["rates"]
    base = data.get("base", "USD")
    actualizado = data.get("updated")

    print(f"\nTasas de cambio (base: {base})")
    if actualizado:
        fecha = datetime.fromtimestamp(actualizado).strftime("%Y-%m-%d %H:%M")
        print(f"Actualizado: {fecha}")
    print("-" * (columnas * 22))

    items = sorted(rates.items())
    for i in range(0, len(items), columnas):
        fila = items[i:i + columnas]
        print("".join(f"{moneda:<5}{valor:>14,.4f}   " for moneda, valor in fila))
    print()


def pedir_monto() -> float:
    while True:
        entrada = input("¿Cuántos dólares (USD) quieres convertir? ").strip().replace(",", "")
        try:
            monto = float(entrada)
            if monto <= 0:
                print("El monto debe ser mayor que 0.")
                continue
            return monto
        except ValueError:
            print("Ingresa un número válido (ej: 150 o 99.50).")


def pedir_moneda(rates: dict) -> str:
    while True:
        moneda = input("¿A qué moneda quieres convertir? (ej: CLP, EUR) ").strip().upper()
        if moneda in rates:
            return moneda
        print(f"'{moneda}' no está disponible. Revisa la tabla de arriba.")


def main():
    try:
        data = obtener_tasas("USD")
    except ErrorAPIMoneda as e:
        print("Error:", e)
        return

    mostrar_tasas(data)

    try:
        while True:
            monto = pedir_monto()
            moneda = pedir_moneda(data["rates"])
            resultado = monto * data["rates"][moneda]
            print(f"\n{monto:,.2f} USD = {resultado:,.2f} {moneda}\n")

            if input("¿Otra conversión? (s/n) ").strip().lower() != "s":
                break
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido. Saliendo...")


if __name__ == "__main__":
    main()
```

How it works:

- **Neat output:** `mostrar_tasas()` prints the rates in aligned columns, sorted alphabetically, with thousands separators and 4 decimals. It also converts the `updated` timestamp to a readable date.
- **Error reasons:** network failures (timeout, no connection) and HTTP errors (4xx/5xx) raise `ErrorAPIMoneda` with the status code and the message from the API's JSON body, falling back to the raw text if there is none.
- **Errors inside a 200 response:** some APIs report problems in the body with a success status. The check on `valid` and `error` catches those.
- **Missing key:** if `CURRENCY_API_KEY` isn't in your `.env`, you get a clear message instead of a confusing 401.
- **User choice:** the program asks for an amount and a target currency, validates both (rejecting letters, negatives, zero and unknown codes), and offers another conversion afterwards.
- **Unverified error format:** I'm not certain of the exact JSON shape currencyapi.net uses for errors, so `_extraer_detalle()` checks a few common shapes. If you trigger an error (e.g. a wrong key) and the message looks off, print `data` once and adjust that function.

I assumed "how much dollars to convert to" meant an amount in USD plus a target currency. If you meant something different, such as converting to a fixed currency only, you can drop `pedir_moneda()` and hardcode the currency.

---

### You · 2026-11-27 01:25 UTC

do not ask the user what currency to convert to, simply show every currency in the list that's converted to instead

---

### Claude · 2026-11-27 01:26 UTC

Here's the updated version. It asks only for the USD amount, then prints the converted value for every currency in the list.

```python
import os
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

URL = "https://currencyapi.net/api/v2/rates"


class ErrorAPIMoneda(Exception):
    """Error personalizado para fallos de la API de divisas."""
    pass


def obtener_tasas(base: str = "USD") -> dict:
    api_key = os.getenv("CURRENCY_API_KEY")
    if not api_key:
        raise ErrorAPIMoneda("Falta CURRENCY_API_KEY en tu archivo .env")

    params = {"key": api_key, "base": base, "output": "JSON"}

    try:
        response = requests.get(URL, params=params, timeout=10)
    except requests.exceptions.Timeout:
        raise ErrorAPIMoneda("La solicitud tardó demasiado (timeout)")
    except requests.exceptions.ConnectionError:
        raise ErrorAPIMoneda("No se pudo conectar. Revisa tu conexión a internet")
    except requests.exceptions.RequestException as e:
        raise ErrorAPIMoneda(f"Error inesperado en la solicitud: {e}")

    try:
        data = response.json()
    except ValueError:
        data = None

    if not response.ok:
        detalle = _extraer_detalle(data) or response.text[:100] or response.reason
        raise ErrorAPIMoneda(f"HTTP {response.status_code}: {detalle}")

    if data is None:
        raise ErrorAPIMoneda("La API devolvió una respuesta que no es JSON válido")

    if data.get("valid") is False or "error" in data:
        raise ErrorAPIMoneda(_extraer_detalle(data) or "La API reportó un error sin detalles")

    if "rates" not in data:
        raise ErrorAPIMoneda("La respuesta no contiene el campo 'rates'")

    return data


def _extraer_detalle(data) -> str | None:
    """Intenta sacar un mensaje de error del cuerpo JSON."""
    if not isinstance(data, dict):
        return None
    error = data.get("error")
    if isinstance(error, dict):
        return error.get("message") or error.get("info") or str(error)
    if error:
        return str(error)
    return data.get("message")


def pedir_monto() -> float:
    while True:
        entrada = input("¿Cuántos dólares (USD) quieres convertir? ").strip().replace(",", "")
        try:
            monto = float(entrada)
            if monto <= 0:
                print("El monto debe ser mayor que 0.")
                continue
            return monto
        except ValueError:
            print("Ingresa un número válido (ej: 150 o 99.50).")


def mostrar_conversiones(data: dict, monto: float, columnas: int = 3):
    rates = data["rates"]
    actualizado = data.get("updated")

    print(f"\n{monto:,.2f} USD equivalen a:")
    if actualizado:
        fecha = datetime.fromtimestamp(actualizado).strftime("%Y-%m-%d %H:%M")
        print(f"(tasas actualizadas: {fecha})")
    print("-" * (columnas * 28))

    items = sorted(rates.items())
    for i in range(0, len(items), columnas):
        fila = items[i:i + columnas]
        print("".join(f"{moneda:<5}{monto * tasa:>18,.2f}   " for moneda, tasa in fila))
    print()


def main():
    try:
        data = obtener_tasas("USD")
    except ErrorAPIMoneda as e:
        print("Error:", e)
        return

    try:
        while True:
            monto = pedir_monto()
            mostrar_conversiones(data, monto)

            if input("¿Otra conversión? (s/n) ").strip().lower() != "s":
                break
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido. Saliendo...")


if __name__ == "__main__":
    main()
```

What changed:

- **Removed `pedir_moneda()`** and the currency prompt. The user only enters an amount.
- **`mostrar_conversiones()` replaces `mostrar_tasas()`.** For each currency it prints `monto * tasa`, in alphabetical order and in 3 aligned columns. The raw rate table is no longer shown, since the converted values are what matters.
- **Rates are fetched once** and reused for every new amount, so asking for another conversion doesn't call the API again.

If you want the conversions sorted by value instead of by currency code, change `sorted(rates.items())` to `sorted(rates.items(), key=lambda x: x[1])`. If your list is very long and you only want some currencies, you can filter `rates` against a set like `{"CLP", "EUR", "GBP"}` before printing.
