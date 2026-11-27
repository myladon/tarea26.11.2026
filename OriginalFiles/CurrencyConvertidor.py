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