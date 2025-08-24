import os
import bcrypt
import psycopg2
from psycopg2 import sql, OperationalError, IntegrityError
from helpers.utils import get_stock_info, nearest_weekday
from collections import defaultdict
from decimal import Decimal
from datetime import datetime
import json

from flask import g

def get_db_connection():
    if 'db' not in g:
        db_url = os.environ.get("DATABASE_URL")
        g.db = psycopg2.connect(db_url)

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_user_by_username(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, password, id, password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    return user

#insert secure user password
def save_new_user(username, userpass):
    if not is_valid_string(username) or not is_valid_string(userpass):
        return False

    pass_hash = bcrypt.hashpw(userpass.encode("utf-8"), bcrypt.gensalt())
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password, password_hash) VALUES(%s, %s, %s)", (username, userpass, pass_hash))
    conn.commit()
    cur.close()
    return True

def portfolio_data(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, portfolio_name FROM portfolios WHERE user_id = %s", (user_id,))
    data = cur.fetchall()
    cur.close()
    return data

def create_portfolio(user_id, name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO portfolios (user_id, portfolio_name)  VALUES(%s, %s)", (user_id, name))
    conn.commit()
    cur.close()
    return True

def delete_portfolio(user_id, portfolio_id):
    conn = get_db_connection()
    cur = conn.cursor()
    res = cur.execute("DELETE FROM portfolios WHERE user_id=%s AND id=%s", (user_id, portfolio_id))
    conn.commit()
    cur.close()

    if res is None:
        return False

    cur = conn.cursor()
    cur.execute("DELETE FROM portfolio_quotes WHERE portfolio_id = %s", (portfolio_id,))
    conn.commit()
    cur.close()
    return True


def portfolio_quotes(portfolio_id, calc_year=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if calc_year is None:
        for_year = datetime.now().year
    else:
        for_year = calc_year
#for dividends only check existance for according year.
# Summary payment do in stand alone request
    stmt ="""
    SELECT portfolio_quotes.id AS id, portfolio_quotes.quote_name
    AS quote_name, buy_price, buy_count,
    buy_price * buy_count AS SS, NN, from_month, to_month,
    current_quotes_count
    FROM portfolio_quotes
    LEFT JOIN (
    SELECT
       DISTINCT quote_name, SUM(div_price) as NN
    FROM
        quote_dividents
    WHERE pay_year = %s
	GROUP by quote_name
	) qq
    ON qq.quote_name = portfolio_quotes.quote_name
    WHERE portfolio_id=%s AND from_year<=%s AND ( to_year IS NULL OR to_year=%s)
    ORDER BY portfolio_quotes.quote_name, id DESC
    """
    #print(stmt)
    cur.execute(stmt,(for_year, portfolio_id, for_year, for_year) )
    data = cur.fetchall()
    cur.close()
    modified_data = [add_div_for_row(row, for_year) for row in data]
    #add_allowed

    return sign_first_quote_same_quote_add(modified_data)

def sign_first_quote_same_quote_add(data):
    last_prices = get_last_prices()
    #print(last_prices)
    modified_data = []
    last_name = ''
    for row in data:
        cur_name = row[1]
        val = ''
        if (cur_name != last_name) and (row[7] != 12):
            val = 'add'

        last_price = last_prices[cur_name][0] #22.11
        last_date =  last_prices[cur_name][1] #'2025-08-21'

        last_name = cur_name
        modified_data.append(row+(val, last_price, last_date ))

    return modified_data

def div_for_quote_and_year(quote_name, for_year, from_month, to_month):

    stmt ="""
        SELECT pay_month, div_price FROM quote_dividents
        WHERE quote_name = %s AND pay_year = %s
        AND pay_month <= %s AND pay_month >= %s AND div_price >0
        ORDER BY pay_year DESC, pay_month DESC
        """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(stmt,(quote_name, for_year, to_month, from_month) )
    div_data = cur.fetchall()
    data = [{"month": row[0], "price": row[1]} for row in div_data]
    cur.close()
    return data

def add_div_for_row(row, for_year):

    from_month = row[6]
    if row[7]:
       to_month = row[7]
    else:
       to_month = datetime.now().month

    stmt ="""
    SELECT div_price, pay_month FROM quote_dividents
    WHERE quote_name = %s AND pay_year = %s
    AND pay_month <= %s AND pay_month >= %s
    """
    #print("divs:" + stmt + row[1], for_year , to_month, row[6] )
    conn = get_db_connection()
    cur2 = conn.cursor()
    cur2.execute(stmt,(row[1], for_year, to_month, row[6]) )
    quantity = row[8] #current for dividend quotes amount
    #print(row)
    div_payed = 0
    div_data = cur2.fetchall()
    if div_data:
        for div_row in div_data:
            div_payed = div_payed + (quantity *  div_row[0])

    cur2.close()
    return row + (div_payed,)

def add_quote(portfolio_id, symbol, price, quotes_count, from_year, from_month, to_year=None, to_month=None):
    conn = get_db_connection()

    cur_to_quotes = conn.cursor()
    cur_to_quotes.execute("SELECT id FROM quotes WHERE quote_name=%s", (symbol,))
    res = cur_to_quotes.fetchone()
    cur_to_quotes.close()

    current_quotes_count = calc_current_quotes_count_by_symbol(conn, symbol, portfolio_id, quotes_count)

    cur = conn.cursor()
    add_full_year_dividents = False
    try:
        cur.execute(
        "INSERT into portfolio_quotes (portfolio_id, quote_name, buy_price, buy_count,from_year,from_month, to_year, to_month, current_quotes_count) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (portfolio_id, symbol, price, quotes_count, from_year, from_month, to_year, to_month, current_quotes_count))
        conn.commit()

        if res is None:
            cur_to_quotes = conn.cursor()
            cur_to_quotes.execute("INSERT INTO quotes (quote_name) VALUES(%s)", (symbol,))
            cur_to_quotes.close()
            conn.commit()

        add_full_year_dividents = True

    except psycopg2.Error as e:
        print("SQL error:", e)
    finally:
      cur.close()

      if add_full_year_dividents:
        add_full_year_div( symbol, from_year, True)

    return True

def delete_symbol(symbol):

    if is_symbol_in_any_portfolio(symbol):
       return False

    conn = get_db_connection()
    cur_to_quotes = conn.cursor()
    cur_to_quotes.execute("DELETE FROM quotes WHERE quote_name=%s", (symbol,))
    cur_to_quotes.close()
    conn.commit()
    return

def is_symbol_in_any_portfolio(symbol):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM portfolio_quotes WHERE quote_name=%s LIMIT 1", (symbol,) )
    row = cur.fetchone()

    cur.close()

    if row:
        return True

    return False

def edit_quote(portfolio_id, quote_id, price, quotes_count, from_year, from_month, to_year, to_month):
    conn = get_db_connection()
    current_quotes_count = calc_current_quotes_count_with_quote_id(conn, quote_id, portfolio_id, quotes_count)

    cur = conn.cursor()
    stmt = """
    UPDATE portfolio_quotes SET buy_price=%s, buy_count=%s,
        from_year=%s, from_month=%s, to_year=%s, to_month=%s,
        current_quotes_count=%s
    WHERE portfolio_id=%s AND id=%s
    """
    #print (stmt)
    cur.execute(stmt, (price, quotes_count, from_year, from_month, to_year, to_month, current_quotes_count, portfolio_id, quote_id, ))

    conn.commit()
    cur.close()
    return True

def calc_current_quotes_count_by_symbol(conn, symbol, portfolio_id, quotes_count):
    st = """
        SELECT current_quotes_count FROM portfolio_quotes A
        WHERE portfolio_id=%s AND  quote_name = %s
        ORDER BY from_year DESC, from_month DESC LIMIT 1
        """
    ex_cur = conn.cursor()
    ex_cur.execute(st, ( portfolio_id, symbol))
    current_quotes_count_row = ex_cur.fetchone()
    ex_cur.close()

    row = current_quotes_count_row or [0]
    current_quotes_count = int(row[0])

    return calc_current_quotes_count(quotes_count, current_quotes_count)


def calc_current_quotes_count_with_quote_id(conn, quote_id, portfolio_id, quotes_count):
    st = """
        SELECT A.current_quotes_count as CC FROM portfolio_quotes A
        LEFT JOIN portfolio_quotes B ON B.id=%s
        WHERE A.portfolio_id=%s AND A.quote_name = B.quote_name AND A.id <> %s
        ORDER BY A.from_year DESC, A.from_month DESC
        """
    ex_cur = conn.cursor()
    ex_cur.execute(st, (quote_id, portfolio_id, quote_id))
    current_quotes_count_row = ex_cur.fetchone()
    ex_cur.close()


    row = current_quotes_count_row or [0]
    current_quotes_count = int(row[0])

    return calc_current_quotes_count(quotes_count, current_quotes_count)

def calc_current_quotes_count(quotes_count, current_quotes_count=0):
    if  (current_quotes_count == 0):  return quotes_count

    return int(current_quotes_count) + int(quotes_count)

def delete_protfolio_quote(portfolio_id, quote_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM portfolio_quotes WHERE portfolio_id=%s AND id=%s",
                (portfolio_id, quote_id))
    conn.commit()
    cur.close()

    return True

def add_div(symbol, div_price, pay_year, pay_month):
    conn = get_db_connection()
    cur = conn.cursor()
    try:

      cur.execute("INSERT INTO quote_dividents (quote_name, div_price, pay_year, pay_month)  VALUES(%s, %s, %s, %s)",
                  (symbol, div_price, pay_year, pay_month))
      conn.commit()
    except psycopg2.Error as e:
        print("SQL error:", e)
    finally:
      cur.close()

    return True

def add_div(symbol, div_price, pay_year, pay_month):
    conn = get_db_connection()
    cur = conn.cursor()
    try:

      cur.execute("INSERT INTO quote_dividents (quote_name, div_price, pay_year, pay_month)  VALUES(%s, %s, %s, %s)",
                  (symbol, div_price, pay_year, pay_month))
      conn.commit()
    except psycopg2.Error as e:
        print("SQL error:", e)
    finally:
      cur.close()

    return True

def add_full_year_div(symbol, pay_year, check_for_exist = False):
    values = ''
    for for_month in range(12):  # Iterates from 0 to 4
        values  = f"{values} ('{symbol}', 0.0, {pay_year} , {for_month+1}),"

    values = values[:-1]

    conn = get_db_connection()
    if check_for_exist:
        existance_stmt = f"SELECT id FROM quote_dividents WHERE quote_name='{symbol}' AND pay_year={pay_year} LIMIT 1"
        ex_cur = conn.cursor()
        ex_cur.execute(existance_stmt)
        ex_quote_div = ex_cur.fetchone()
        ex_cur.close()
        if ex_quote_div:
            print("quote already exist")
            return True

    cur = conn.cursor()
    try:
      cur.execute(
        f"INSERT INTO quote_dividents (quote_name, div_price, pay_year, pay_month) VALUES {values}")
      conn.commit()
    except psycopg2.Error as e:
        print("SQL error:", e)
    finally:
      cur.close()
    return True

def delete_div(id, symbol):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
      cur.execute("DELETE FROM quote_dividents WHERE id=%s AND quote_name=%s",
                  (id, symbol))
      conn.commit()
    except psycopg2.Error as e:
        print("SQL error:", e)
    finally:
      cur.close()
    return True

def edit_div(id, new_price):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
      cur.execute("UPDATE quote_dividents SET div_price=%s WHERE id=%s",
                  (new_price, id))
      conn.commit()
    except psycopg2.Error as e:
        print("SQL error:", e)
    finally:
      cur.close()
    return True

def all_dividents(symbol=None):
    conn = get_db_connection()
    cur = conn.cursor()

    if symbol:
        whereclause = " WHERE quote_name = '" + symbol +"'"
    else:
        whereclause = ""
    stmt = """
        SELECT id, quote_name, div_price, pay_year, pay_month FROM quote_dividents
    """
    order_by = " ORDER BY pay_year DESC, pay_month DESC"

    #print(stmt + whereclause + order_by)
    cur.execute(stmt + whereclause +order_by)
    column_names = [desc[0] for desc in cur.description]

    rows = cur.fetchall()
    data = [dict(zip(column_names, row)) for row in rows]
    cur.close()

    converted = data_convert(data)
    return converted

def data_convert(rows):
    data = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        nn = row['id']
        quote = row['quote_name']
        year = row['pay_year']
        month = row['pay_month']
        price = str(row['div_price'])

        data[quote][year][month] = [nn, price]

    #convert to the json array
    json_ready = {q: {y: dict(m) for y, m in years.items()} for q, years in data.items()}
    #print(json_ready)
    return json_ready

def all_symbols():
    conn = get_db_connection()
    cur = conn.cursor()

    stmt = """
       SELECT Q.id, Q.quote_name, close_price, last_date_at
        FROM quotes Q
        LEFT JOIN LATERAL(
            SELECT QP.*
            FROM  quotes_price QP
            WHERE Q.quote_name=QP.quote_name
            ORDER BY QP.quote_name, QP.last_date_at DESC
            LIMIT 1

        )QP on TRUE
    """

    cur.execute(stmt)
    data = cur.fetchall()
    cur.close()

    new_data = [
    (number, name, 'used', close_price, last_date_at) if is_symbol_in_any_portfolio(name) else (number, name, 'not_used')
     for  number, name, close_price, last_date_at in data
    ]
    return new_data

def refresh_quotes():
    conn = get_db_connection()
    cur = conn.cursor()
    stmt = """
        SELECT DISTINCT quote_name FROM quotes GROUP BY quote_name
    """

    cur.execute(stmt)
    quotes = cur.fetchall()
    cur.close()
    for_day = nearest_weekday()

    data = []
    for row in quotes:
        close_val = get_stock_info(row[0], for_day)
        data.append([row[0],close_val])

    update_quote_prices(data, for_day)
    return all_symbols()

def update_quote_prices(data, for_day):

    #data=[{'NAV': 0.0}, {'BAC': 49.48}, {'XYLD': 38.87}, {'QYLD': 16.65}, {'GOF': 14.85}, {'IAF': 4.64}, {'AZN': 80.97}, {'APLE': 12.87}, {'AAPL': 227.76}, {'QQQ': 571.97}, {'BGY': 5.78}]
    print(data)

    values = ", ".join(
        "(" + ", ".join(
            repr(x) if isinstance(x, str) else str(x)
            for x in row
        ) + f", '{for_day}', NOW(), NOW())"
        for row in data
    )

    print(values)
    conn = get_db_connection()
    cur = conn.cursor()
    stmt = f"""
    INSERT INTO quotes_price (quote_name, close_price, last_date_at, created_at, updated_at)
    VALUES {values}
    ON CONFLICT (quote_name, last_date_at) DO UPDATE
    SET close_price = EXCLUDED.close_price,
        quote_name = EXCLUDED.quote_name,
        updated_at = EXCLUDED.updated_at;
    """

    try:
      cur.execute(stmt)
      conn.commit()
    except psycopg2.Error as e:
        print("SQL error:", e)
    finally:
      cur.close()

def get_last_prices():
    conn = get_db_connection()
    cur = conn.cursor()
    stmt = f"""
       SELECT Q.quote_name, close_price, last_date_at
        FROM quotes Q
        LEFT JOIN LATERAL(
            SELECT QP.*
            FROM  quotes_price QP
            WHERE Q.quote_name=QP.quote_name
            ORDER BY QP.quote_name, QP.last_date_at DESC
            LIMIT 1
        )QP on TRUE
    """
    cur.execute(stmt)
    quote_prices = cur.fetchall()
    cur.close()
    rebuilt_quotes_prices = {}
    if quote_prices:
       # rebuilt_quotes_prices =  {{row[0]: (float(row[1]), row[2].strftime("%Y-%m-%d"))} for row in quote_prices }
        rebuilt_quotes_prices =  {row[0]: (float(row[1]), row[2].strftime("%Y-%m-%d")) for row in quote_prices}

    return rebuilt_quotes_prices


