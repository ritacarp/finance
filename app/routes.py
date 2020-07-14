import os

#from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, Markup
#from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
#import sqlite3
#from sqlite3 import Error


from flask import render_template, flash, redirect, url_for, request, Markup
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.models import Users,Orders




from app.helpers import apology, login_required, lookup, usd, create_connection, checkEmail, checkPhone, messageAlert, checkPassword, stringSlice

# Configure application
# app = Flask(__name__)
# app = Flask(__name__.split('.')[0])
#app = Flask('Finance', instance_relative_config=True)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters['stringSlice'] = stringSlice

# Check for environment variable
if not os.getenv("IEXAPI_KEY"):
    raise RuntimeError("IEXAPI_KEY is not set")



# Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"

# app.config.from_pyfile looks for a config file (in this case development.py) in an instance folder
# app.config.from_pyfile('development.py', silent=True)

#This call loads the config file that is set in the batch script C:\FlaskRoot\Finance\envs\etc\conda\activate.d\env_vars.bat
#app.config.from_envvar('APP_CONFIG_FILE')
# os.environ["IEXAPI_KEY"] = app.config["IEXAPI_KEY"]

#Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")
# db = r"/home/ubuntu/finance/finance.db"
# db =  r"C:\FlaskRoot\Finance\finance.db"

# Make sure API key is set
#if not os.getenv('API_KEY'):
#    raise RuntimeError("API_KEY not set")

#if not  app.config["IEXAPI_KEY"]:
#    raise RuntimeError("IEXAPI_KEY not set")


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
                     WHERE userID = ? \
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


            # The tuple is constructed as (Symbol, Name, Shares, Price, TOTAL)
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


        sql = ''' INSERT INTO orders(userID, type, symbol, name, shares, price, extendedPrice) VALUES(?,?,?,?,?,?,?) '''

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
        cur.execute("Select ID, UserID, Type, Symbol, Name, Shares, Price, orderDate From Orders Where userID=?",
            (session["user_id"],))
            
        rows = cur.fetchall()
        
        idx=-1
        allStocks = []
        for row in rows:
            
            idx += 1

            # The tuple is constructed as (Type, Symbol, Name, Shares, Price, Order Date)
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




@app.route("/login", methods=["GET", "POST"])
@app.route("/login/<args>", methods=["GET", "POST"])
def login(args=""):
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
    

        # Ensure username was submitted
        if not request.form.get("username"):
            return messageAlert(Markup.escape("Username is required"), 403, "error.png", "login")

        
        # Ensure password was submitted
        elif not request.form.get("password"):
            return messageAlert(Markup.escape("Password is required"), 403, "error.png", "login", request.form.get("username"))

        # create a database connection
        conn = create_connection(db)
        conn.row_factory = sqlite3.Row

        with conn:

            cur = conn.cursor()
            # Query database for username
            cur.execute("SELECT id, username, hash, cash, mobile,comments FROM users WHERE username = ?",
                         (request.form.get("username"),))


            rows = cur.fetchall()

            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                return messageAlert(Markup.escape("Invalid username and/or password"), 403, "error.png", "login", request.form.get("username"))

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html",username=args)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


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
    
    


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    
    # print("In register, method =",request.method)
    
    if request.method == "GET":
        return render_template("register.html")

    # Ensure username was submitted
    if not request.form.get("username"):
        return messageAlert(Markup.escape("Username is required"), 403, "error.png", "register")

    # Ensure password was submitted
    elif not request.form.get("password"):
        return messageAlert(Markup.escape("Password is required"), 403, "error.png", "register")

    # Ensure mobile number was submitted
    elif not request.form.get("mobile"):
        return messageAlert(Markup.escape("Phone Number is required"), 403, "error.png", "register")

    elif request.form.get("password") != request.form.get("verifyPassword"):
       return messageAlert(Markup.escape("Password and Verification Password do not match"), 402, "error.png", "register")

    isValidEmail = checkEmail(request.form.get("username"))
    if not isValidEmail:
        return messageAlert(Markup.escape("Email address is not valid.  Please provide a valid email address for username"), 403, "error.png", "register")

    isValidPhone = checkPhone(request.form.get("mobile"))
    if not isValidPhone:
        return messageAlert(Markup.escape("Phone number is not valid.  Please provide a valid mobile phone number"), 403, "error.png", "register")

    passwordMessage = checkPassword(request.form.get("password"))
    if passwordMessage:
        return messageAlert(passwordMessage, 403, "error.png", "register")

    # create a database connection
    conn = create_connection(db)

    with conn:

        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?",
                         (request.form.get("username"),))


        rows = cur.fetchall()
        if len(rows) == 0:
            values = (request.form.get("username"), 
                      generate_password_hash(request.form.get("password")), 
                      '10000',
                      request.form.get("mobile"),
                      request.form.get("password"))
                      
            sql = ''' INSERT INTO users(username,hash,cash,mobile,comments) VALUES(?,?,?,?,?) '''


            cur = conn.cursor()
            cur.execute(sql, values)
            id = cur.lastrowid
            return messageAlert("You have successfully registered", 200, "information.png", "login")
        else:
            return messageAlert(Markup.escape("That username already exists, please try another"), 403, "error.png", "register")




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
                     Where userid=? \
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


        sql = ''' INSERT INTO orders(userID, type, symbol, name, shares, price, extendedPrice) VALUES(?,?,?,?,?,?,?) '''

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
