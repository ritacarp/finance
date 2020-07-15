import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session, Markup, url_for
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.urls import url_parse
from app import app, db
from app.models import Users, Orders
from app.forms import LoginForm, RegistrationForm



from app.helpers import apology, login_required, lookup, usd, create_connection, checkEmail, checkPhone, messageAlert, checkPassword, stringSlice



@app.route("/", methods=["GET"])
@login_required
def index():
    """Show portfolio of stocks"""
    # create a database connection
    conn = create_connection(db)
    conn.row_factory = sqlite3.Row

    with conn:

        cur = conn.cursor()
        # Query database for username
        cur.execute("SELECT id, username, hash, cash, mobile,comments FROM users WHERE id = ?",
                     (session["user_id"],))
        
        rows = cur.fetchall()
        
        # Ensure record exists
        if len(rows) != 1:
            return messageAlert(Markup.escape("Portfolio Error: User does not exist"), 500, "error.png", "login")

        cash = rows[0]["cash"]
        accountTotal = cash


        cur = conn.cursor()
        cur.execute("SELECT symbol, sum(shares) as shares from orders \
                     WHERE user_id = ? \
                     group by symbol \
                     having sum(shares) > 0 \
                     order by symbol", \
                     (session["user_id"],))

        rows = cur.fetchall()
        
        idx=-1
        allStocks = []
        for row in rows:
            
            idx += 1
            # shares = rows[idx]["shares"]
            stockDict = lookup(rows[idx]["symbol"])

            if not stockDict:
                return messageAlert(Markup.escape("Portfolio Error: Invalid stock symbol " + str(idx) + " " + rows[idx]["symbol"]), 500, "error.png", "quote")


            # The tuple is constructed as (Symbol, company_name, Shares, Price, TOTAL)
            stockTuple = ()
            stockSymbol = stockDict["symbol"]
            stockCompanyName = stockDict["companyName"]
            
            shares = rows[idx]["shares"]
            
            stockLatestPrice = stockDict["latestPrice"]
            formattedLatestPrice = "${:,.2f}".format(stockLatestPrice)
            
            stockTotalPrice = stockLatestPrice * shares
            formattedTotalPrice = "${:,.2f}".format(stockTotalPrice)
            
            stockTuple = (stockSymbol, stockCompanyName, shares,formattedLatestPrice, formattedTotalPrice)
            allStocks.append(stockTuple)
            
            accountTotal = accountTotal + stockTotalPrice
            


        return render_template("portfolio.html",
                               title="Portfolio",
                               cash = cash,
                               allStocks=allStocks,
                               accountTotal = accountTotal
                               )




@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password',"danger")
            return redirect(url_for('login'))
        login_user(user)
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(username=form.username.data, mobile=form.mobile.data, comments=form.password.data, cash=10000)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!<br>Please Log In.', "success")
        return redirect(url_for('login'))

    form.submit.label.text = 'Register'
    print(f"register:  This is 6 - calling register.html")
    return render_template('register.html', title='Register', form=form)








@app.route("/buy", methods=["GET", "POST"])
@app.route("/buy/<args>", methods=["GET", "POST"])
@login_required
def buy(args=""):
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buyShares.html",title="Buy Shares",symbol=args,action="buy")
        
    symbol = request.form.get("symbol")
    shares = request.form.get("shares")
        
    if not symbol:
        return messageAlert(Markup.escape("Stock symbol is required"), 403, "error.png", "buy")

    if not shares:
        return messageAlert(Markup.escape("Number of shares is required"), 403, "error.png", "buy", symbol)

    try:
        int(shares)
        shares = int(shares)
        isValidShares = True
    except ValueError:
        isValidShares = False

    if not isValidShares:
        return messageAlert(Markup.escape("Number of shares is an integer"), 403, "error.png", "buy", symbol)

    stockDict = lookup(symbol)
    if not stockDict:
        message = "You have requested an invalid stock symbol " + symbol + ".<br>Please try again."
        return messageAlert(Markup.escape(message), 403, "error.png", "buy", symbol)
    
    stockSymbol = stockDict["symbol"]
    stockCompanyName = stockDict["companyName"]
    stockLatestPrice = stockDict["latestPrice"]
    title = "Buy:  Stock Symbol " + stockSymbol
    extendedPrice = stockLatestPrice * shares
    
    # create a database connection
    conn = create_connection(db)
    conn.row_factory = sqlite3.Row

    with conn:

        cur = conn.cursor()
        # Query database for username
        cur.execute("SELECT id, username, hash, cash, mobile,comments FROM users WHERE id = ?",
                     (session["user_id"],))
        
        rows = cur.fetchall()
        
        # Ensure record exists
        if len(rows) != 1:
            return messageAlert(Markup.escape("Portfolio Error: User does not exist"), 500, "error.png", "login")

        cash = rows[0]["cash"]
        
        if cash < extendedPrice:
           message = "You do not have sufficient funds (" + "${:,.2f}".format(cash) + ")<br>to buy " + \
                     str(shares) + " shares of " + stockCompanyName + "(" + stockSymbol + ") at " + \
                     "${:,.2f}".format(stockLatestPrice) + " a share<br>for a net price of " + "${:,.2f}".format(extendedPrice) + "."
           return messageAlert(Markup.escape(message), 403, "error.png", "buy", symbol)
           

        values = (session["user_id"], 
                  "Buy",
                  stockSymbol, 
                  stockCompanyName,
                  shares,
                  stockLatestPrice,
                  extendedPrice)


        sql = ''' INSERT INTO orders(user_id, transaction_type, symbol, company_name, shares, price, extendedPrice) VALUES(?,?,?,?,?,?,?) '''

        cur = conn.cursor()
        cur.execute(sql, values)
        id = cur.lastrowid
        
        cur = conn.cursor()
        cur.execute("Update users Set cash = cash - ? Where id=?",
        (extendedPrice,session["user_id"]))

    # Redirect user to home page
    return redirect("/")



@app.route("/history", methods=["GET"])
@login_required
def history():
    """Show history of transactions"""
    conn = create_connection(db)
    conn.row_factory = sqlite3.Row

    with conn:

        cur = conn.cursor()
        # Query database for username
        cur.execute("Select ID, user_id, transaction_type, Symbol, company_name, Shares, Price, orderDate From Orders Where user_id=?",
            (session["user_id"],))
            
        rows = cur.fetchall()
        
        idx=-1
        allStocks = []
        for row in rows:
            
            idx += 1

            # The tuple is constructed as (transaction_type, Symbol, company_name, Shares, Price, Order Date)
            stockTuple = ()
            stockType = rows[idx]["type"]
            stockSymbol = rows[idx]["symbol"]
            stockCompanyName =  rows[idx]["Name"]
            
            shares = rows[idx]["shares"]
            if stockType == "Sell":
               shares = shares * (-1)
    
            stockPrice = rows[idx]["Price"]
            formattedPrice = "${:,.2f}".format(stockPrice)
            
            orderDate = rows[idx]["orderDate"]
            
            
            stockTuple = (stockType, stockSymbol, stockCompanyName, shares,formattedPrice, orderDate)
            allStocks.append(stockTuple)
            
            


        return render_template("history.html",
                               title="History",
                               allStocks=allStocks
                               )






@app.route("/quote", methods=["GET", "POST"])
@app.route("/quote/<args>", methods=["GET", "POST"])
@login_required
def quote(args=""):
    """Get stock quote."""
    if request.method == "GET":
        return render_template("getStockQuote.html",symbol=args)
        
    symbol = request.form.get("symbol")
        
    if not symbol:
        return messageAlert(Markup.escape("Stock symbol is required"), 403, "error.png", "quote")


    stockDict = lookup(symbol)
    if not stockDict:
        message = "You have requested an invalid stock symbol " + symbol + ".<br>Please try again."
        return messageAlert(Markup.escape(message), 403, "error.png", "quote")
    
    stockSymbol = stockDict["symbol"]
    stockCompanyName = stockDict["companyName"]
    stockLatestPrice = stockDict["latestPrice"]
    title = "Quote: Stock Symbol " + stockSymbol

    return render_template('displayStockQuote.html',
                           symbol=stockSymbol,
                           stockSymbol=stockSymbol,
                           stockCompanyName=stockCompanyName,
                           stockLatestPrice=stockLatestPrice,
                           title=title
                           )
    
    




@app.route("/sell", methods=["GET", "POST"])
@app.route("/sell/<args>", methods=["GET", "POST"])
@login_required
def sell(args=""):
    """Sell shares of stock"""
    if request.method == "GET":
        return render_template("buyShares.html",title="Sell Shares",symbol=args,action="sell")
        
    symbol = request.form.get("symbol")
    shares = request.form.get("shares")
        
    if not symbol:
        return messageAlert(Markup.escape("Stock symbol is required"), 403, "error.png", "sell")

    if not shares:
        return messageAlert(Markup.escape("Number of shares is required"), 403, "error.png", "sell", symbol)

    try:
        int(shares)
        shares = int(shares)
        isValidShares = True
    except ValueError:
        isValidShares = False

    if not isValidShares:
        return messageAlert(Markup.escape("Number of shares is an integer"), 403, "error.png", "sell", symbol )
     

    stockDict = lookup(symbol)
    if not stockDict:
        message = "You have requested an invalid stock symbol " + symbol + ".<br>Please try again."
        return messageAlert(Markup.escape(message), 403, "error.png", "sell")
    
    stockSymbol = stockDict["symbol"]
    stockCompanyName = stockDict["companyName"]
    stockLatestPrice = stockDict["latestPrice"]
    title = "Buy:  Stock Symbol " + stockSymbol
    
    
    # create a database connection
    conn = create_connection(db)
    conn.row_factory = sqlite3.Row

    with conn:


        cur = conn.cursor()
        cur.execute("Select ifnull(sum(shares),0) as accountShares from orders \
                     Where user_id=? \
                     And   symbol = upper(?)", \
                     (session["user_id"],stockSymbol))

        rows = cur.fetchall()

        # Ensure record exists
        if len(rows) != 1:
            message = "You do not own any shares of " + stockCompanyName + " (" + stockSymbol + ").<br>Please try again."
            return messageAlert(Markup.escape(message), 403, "error.png", "sell", symbol)

        accountShares = rows[0]["accountShares"]

        
        if shares > accountShares:
            message = "You own " + \
                       str(accountShares) + " shares of " + stockCompanyName + " (" + stockSymbol + ").<br>" + \
                       "You may not sell more shares (" + str(shares) + ") than you currently own."
            return messageAlert(Markup.escape(message), 403, "error.png", "sell", symbol)

        shares = shares * (-1)
        extendedPrice = stockLatestPrice * shares

        values = (session["user_id"], 
                  "Sell",
                  stockSymbol, 
                  stockCompanyName,
                  shares,
                  stockLatestPrice,
                  extendedPrice)


        sql = ''' INSERT INTO orders(user_id, transaction_type, symbol, company_name, shares, price, extendedPrice) VALUES(?,?,?,?,?,?,?) '''

        cur = conn.cursor()
        cur.execute(sql, values)
        id = cur.lastrowid
        
        cur = conn.cursor()
        cur.execute("Update users Set cash = cash - ? Where id=?",
        (extendedPrice,session["user_id"]))

    # Redirect user to home page
    return redirect("/")





def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
