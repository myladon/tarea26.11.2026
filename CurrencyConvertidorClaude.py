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