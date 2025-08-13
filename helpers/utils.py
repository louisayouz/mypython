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

## 0HAKSH241QPKW7EK https://www.alphavantage.co/support/#api-key