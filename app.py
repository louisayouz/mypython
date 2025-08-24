from flask import Flask, render_template, request, url_for, redirect,session,jsonify
from db import get_user_by_username, portfolio_data, create_portfolio, delete_portfolio, portfolio_quotes
from db import add_quote, delete_protfolio_quote, edit_quote, all_dividents, add_div, delete_div, div_for_quote_and_year
from db import all_symbols, add_full_year_div, edit_div, delete_symbol
from db import close_db, refresh_quotes
from helpers.utils import validate_int, validate_string, validate_numeric, symbols_as_array
from import_div import import_quote
from datetime import datetime, timedelta
import os
import bcrypt

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(minutes=10)


@app.teardown_appcontext
def teardown_db(exception):
    close_db()

@app.before_request
def require_login():
    session.permanent = True
    # Skip login check for login page and static files
    if 'username' not in session and request.endpoint not in ['login', 'static']:
        return redirect(url_for('login'))

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)

        result = False
        if user is None:
            return "Invalid credentials!"

        if user[3] is None:
            result = user[1] == password
        else:
            result = bcrypt.checkpw(password.encode("utf-8"), user[3].tobytes())

        if result:
            session['username'] = username
            session['user_id'] = user[2]
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    if request.method == 'POST':
        portfolio_name = request.form['portfolio_name']
        if portfolio_name:
            create_portfolio(session['user_id'], portfolio_name)

    data = portfolio_data( session['user_id'])
    return render_template('portfolio.html', portfolio=data, user_name=session['username'], for_year=datetime.now().year)

@app.route('/delete_portfolio/<int:portfolioid>')
def delete_user_portfolio(portfolioid):
    delete_portfolio(session['user_id'], portfolioid )
    return redirect(url_for('portfolio'))


@app.route('/quotes/<int:portfolioid>')
@app.route('/quotes/<int:portfolioid>/<int:calcyear>', methods=['GET'])
def quotes(portfolioid, calcyear=None):
    data = portfolio_quotes(portfolioid, calcyear)
    if calcyear is None:
        for_year = datetime.now().year
    else:
        for_year = calcyear

    #print(data)
    err = request.args.get('err') or ''
    return render_template('quotes.html', quotes=data, symbols = symbols_as_array(data), user_name=session['username'], portfolioid=portfolioid, for_year=for_year, err=err)

@app.route('/addquote', methods=['POST'] )
def addquote_to_portfolio():
    print("POST Data:", request.form)
    portfolio_id = validate_int(request.form['portfolioid'])
    symbol = validate_string(request.form['symbol'])
    price = validate_numeric(request.form['price'])
    quotes_count = validate_int(request.form['quantity'])

    from_year = validate_int(request.form['from_year'])
    from_month = validate_int(request.form['from_month'])
    to_year = validate_int(request.form['to_year'])
    if to_year == 0:
        to_year = None
    to_month = validate_int(request.form['to_month'])
    if to_month == 0:
        to_month = None

    err=''
    if (portfolio_id > 0) and ( price > 0) and (quotes_count >0 ) and (symbol != ''):
        add_quote(portfolio_id, symbol.upper(), price, quotes_count, from_year, from_month, to_year, to_month)
    else:
        err = "Invalid quotes parameters"


    return redirect(url_for('quotes', portfolioid=portfolio_id, calcyear=from_year, err=err))

@app.route('/deletequote/<int:portfolioid>/<int:quoteid>', methods=['GET'] )
def delete_quote_to_portfolio(portfolioid, quoteid):
    delete_protfolio_quote(portfolioid, quoteid)

    return redirect(url_for('quotes', portfolioid=portfolioid))

@app.route('/editquote', methods=['POST'] )
def edit_quote_to_portfolio():
    portfolio_id = request.form['portfolioid']
    quote_id = request.form['quoteid']
    price = request.form['price']
    quotes_count = request.form['quantity']

    from_year = validate_int(request.form['from_year'])
    from_month = validate_int(request.form['from_month'])
    to_year = validate_int(request.form['to_year'])
    if to_year == 0:
        to_year = None
    to_month = validate_int(request.form['to_month'])
    if to_month == 0:
        to_month = None


    edit_quote( portfolio_id, quote_id, price, quotes_count, from_year, from_month, to_year, to_month)
    return redirect(url_for('quotes', portfolioid=portfolio_id, calcyear=from_year))

@app.route('/quotedividents', methods=['GET'])
@app.route('/quotedividents/<string:quote_symbol>', methods=['GET'])
def quotedividents(quote_symbol=None):
    if quote_symbol:
        # Handle specific quote
        data = all_dividents(quote_symbol)
    else:
        # Handle general case
        data = all_dividents()
    #print(data)
    return render_template('dividents.html', data = data, single_quote = (quote_symbol is not None), quote_symbol = quote_symbol)

@app.route('/adddiv', methods=['POST'] )
def adddiv():
    print("POST Data:", request.form)

    symbol = validate_string(request.form['symbol'])
    div_price = validate_numeric(request.form['divprice'])
    div_year = validate_int(request.form['divyear'])
    div_month = validate_int(request.form['divmonth'])

    #print(symbol, div_price, div_year, div_month)

    err=''
    if ( div_price > 0) and (div_year >0  and div_month > 0) and (symbol != ''):
        add_div(symbol.upper(), div_price, div_year, div_month)
    else:
        err = "Invalid quotes parameters"

    return redirect(url_for('quotedividents', quote_symbol=symbol))


@app.route('/editquotediv/<string:value>/<int:id>', methods=['GET'])
def editquotediv(id, value):
    try:
        new_value = float(value)
        edit_div(int(id), value)
    except (TypeError, ValueError):
        return 'Invalid parameters'

    return 'successfully'

@app.route('/addyeardiv/<string:quote_symbol>/<int:foryear>', methods=['GET'])
def add_full_year_divs(quote_symbol, foryear):
    add_full_year_div(quote_symbol, foryear, True)
    return redirect(url_for('quotedividents', quote_symbol=quote_symbol))

@app.route('/deletediv/<string:quote_symbol>/<int:divid>', methods=['GET'])
def deletediv(quote_symbol, divid):
    delete_div(divid, quote_symbol)
    return redirect(url_for('quotedividents', quote_symbol=quote_symbol))

@app.route('/importquotedividents/<string:quote_symbol>', methods=['GET'])
def importquotedividents(quote_symbol):

    import_quote(quote_symbol, '2025-01-01', '2025-05-01')
    return redirect(url_for('quotedividents', quote_symbol=quote_symbol))

@app.route('/getquotedivs/<string:quote_symbol>/<int:foryear>/<int:frommonth>/<int:tomonth>', methods=['GET'])
def getquotedivs(quote_symbol,foryear, frommonth, tomonth):
    data = div_for_quote_and_year(quote_symbol,foryear, frommonth, tomonth)
    return jsonify(data)

@app.route('/symbols', methods=['GET'])
def symbols():
    symbols = all_symbols()
    return render_template('symbols.html', symbols=symbols)

@app.route('/deletesymbol/<string:symbol>', methods=['GET'] )
def deletesymbol(symbol):
    delete_symbol(symbol)
    return render_template('symbols.html', symbols=all_symbols())
   # return redirect(url_for('quotes', portfolioid=portfolioid))

@app.route('/refresh_stocks', methods=['POST'] )
def refresh_stocks():
    refresh_quotes()
    return 'successfully'
    #return render_template('symbols.html', symbols=all_symbols())

if __name__ == '__main__':
    app.run(debug=True)
