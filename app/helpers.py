import os
#import requests
import urllib.parse
#import sqlite3
#from sqlite3 import Error
import re 
from flask import Markup

from flask import redirect, render_template, request, session
from functools import wraps
    
def messageAlert(message, code=400, image="", route="", args=""):
    s = message
    return render_template("messageAlert.html", message=s, code=code, image=image, route=route, args=args), code


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code



def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("IEXAPI_KEY")
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "companyName": quote["companyName"],
            "latestPrice": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def stringSlice(source,charater,position):
    """ Return some part of a string."""
    """ Example: stringSlice(".", 0, 1) """
    value = source.split(charater)[position]
    return f"{value}"


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
        :param db_file: database file
        :return: Connection object or None
        """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def checkEmail(email):  
  
    # pass the regular expression 
    # and the string in search() method 
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if(re.search(regex,email)):  
        return True
    else:  
        return False
        
def checkPhone(phone):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    regex = '^(1\s*[-\/\.]?)?(\((\d{3})\)|(\d{3}))\s*[-\/\.]?\s*(\d{3})\s*[-\/\.]?\s*(\d{4})\s*(([xX]|[eE][xX][tT])\.?\s*(\d+))*$'
    if(re.search(regex,phone)):  
        return True
    else:  
        return False


# Password validation in Python 
# using naive method 
  
# Function to validate the password 
def checkPassword(passwd): 
      
    SpecialSym =['$', '!', '#', '%', '_', '~'] 
    val = True
    message=""
      
    if len(passwd) < 6: 
        message = message + 'Password length should be at least 6 characters.<br>'
        val = False
                    
    if not any(char.isdigit() for char in passwd): 
        message = message + 'Password should have at least one numeral.<br>' 
        val = False
          
    if not any(char.isupper() for char in passwd): 
        message = message + 'Password should have at least one uppercase letter<br>' 
        val = False
          
    if not any(char.islower() for char in passwd): 
        message = message + 'Password should have at least one lowercase letter<br>' 
        val = False
          
    if not any(char in SpecialSym for char in passwd): 
        message = message + 'Password should have at least one of the symbols ($ ! # % _~)<br> '
        val = False

    
    return (Markup.escape(message))
  