from datetime import date, timedelta
import os
import requests

def validate_int(var):
   try:
      i_val = int(var)
      return i_val
   except ValueError:
      return 0

def validate_string(var):
    if var is not None:
      return var
    return ''

def validate_numeric(var):
   try:
      f_val = float(var)
      return f_val
   except ValueError:
      return 0

def symbols_as_array(data):
   symbols = []
   for row in data:
      if row[1] in symbols:
         continue
      else:
         symbols.append(row[1])
   return symbols

def is_valid_string(s: str) -> bool:
    """
    Check if a string is not None, not empty,
    and not just whitespace.
    """
    return bool(s and s.strip())

def get_stock_info(symbol, for_day):
   #import requests
   token = os.getenv("TIINGO_TOKEN")

   headers = {
      'Content-Type': 'application/json'
   }

   #for_day = nearest_weekday()
   #requestResponse = requests.get("https://api.tiingo.com/tiingo/daily/{symbol}?token={token}", headers=headers)
   print ( f"https://api.tiingo.com/tiingo/daily/{symbol}/prices?startDate={for_day}&token={token}")
                                   #https://api.tiingo.com/tiingo/daily/aapl/prices
   requestResponse = requests.get(f"https://api.tiingo.com/tiingo/daily/{symbol}/prices?startDate={for_day}&token={token}", headers=headers)
   #print(requestResponse.json())
   res = requestResponse.json()
   print(res)
   if res:
      return float(res[0]['close'])
   else:
      return float(0.0)
  #requestResponse = requests.get("https://api.tiingo.com/tiingo/daily/{symbol}?token={token}", headers=headers)

def nearest_weekday():
   start_date = date.today()
   start_date -= timedelta(days=1)

   while start_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
         start_date -= timedelta(days=1)

   return start_date.strftime("%Y-%m-%d")