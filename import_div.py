import requests
def import_quote(symbol, from_date, to_date):
  url = "https://api.nasdaq.com/api/quote/TSLA/historical"
  headers = {
      "User-Agent": "Mozilla/5.0",  # Nasdaq blocks requests without a user-agent
      "Accept": "application/json"
  }

  params = {
      "assetclass": "stocks",
      "fromdate": from_date,
      "todate": to_date,
      "limit": 9999,
      "random": 22
  }

  response = requests.get(url, headers=headers, params=params)

  if response.status_code == 200:
      data = response.json()
      print(data)
  else:
      print("Request failed:", response.status_code)