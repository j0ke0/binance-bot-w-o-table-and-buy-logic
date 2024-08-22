from binance.client import Client
from binance.exceptions import BinanceAPIException
from buy_keys_dont_del import yawi_api_key, yawi_secret_key
import psycopg2
import os
import tkinter as tk

# Replace these with your own API key and secret
API_KEY = yawi_api_key()
API_SECRET = yawi_secret_key()

# Database connection parameters
DATABASE_NAME = "trading"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_HOST = "localhost"
DATABASE_PORT = "5432"

def get_symbols_from_db(output_text):
    """Fetch all symbols from the PostgreSQL database."""
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT
        )
        cur = conn.cursor()
        
        # Execute SQL query to get all symbols
        cur.execute("SELECT coin FROM top_gainers;")
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Extract symbols from the query results
        symbols = [result[0] for result in results]
        
        if symbols:
            return symbols
        else:
            output_text.insert(tk.END, "No symbols found in the database.\n")
            return []

    except Exception as e:
        output_text.insert(tk.END, f"An error occurred while fetching symbols from the database: {e}\n")
        return []
    
def get_high_price(symbol, output_text):
    """Fetch the high price of a given symbol from Binance."""
    client = Client(API_KEY, API_SECRET)

    try:
        # Fetch the 24-hour ticker price change statistics
        ticker = client.get_ticker(symbol=symbol)
        
        # Extract the high price from the ticker information
        high_price_str = ticker['highPrice']
        high_price = float(high_price_str)
        formatted_high_price = f"{high_price:.8f}".rstrip('0').rstrip('.')

        return formatted_high_price

    except BinanceAPIException as e:
        output_text.insert(tk.END, f"An error occurred while fetching the high price for {symbol}: {e}\n")
        return None

def calculate_5_percent_less(price_str, output_text):
    """Calculate 5% less than the given price and format it properly."""
    try:
        # Convert the price to float
        price_float = float(price_str)
        
        # Calculate 5% less
        reduced_price = price_float * 0.94 #tail math
        
        # Determine the number of decimal places in the original price
        decimal_places = len(price_str.split('.')[1]) if '.' in price_str else 0
        
        # Format the reduced price with the same number of decimal places
        formatted_reduced_price = f"{reduced_price:.{decimal_places}f}".rstrip('0').rstrip('.')
        
        return formatted_reduced_price
    
    except ValueError as e:
        output_text.insert(tk.END, f"An error occurred in price calculation: {e}\n")
        return None

def update_check_24hrs(symbol, reduced_price, output_text):
    """Update the check_24hrs column in the PostgreSQL database for the given symbol."""
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT
        )
        cur = conn.cursor()
        
        # Update the check_24hrs column for the given symbol
        cur.execute("""
            UPDATE top_gainers
            SET check_24hrs = %s
            WHERE coin = %s;
        """, (reduced_price, symbol))
        
        conn.commit()
        cur.close()
        conn.close()
        
    
    except Exception as e:
        output_text.insert(tk.END, f"An error occurred while updating check_24hrs for {symbol}: {e}\n")

def check_24hrs_range(output_text):
    """Main function to coordinate fetching data, calculations, and updates for all symbols."""
    symbols = get_symbols_from_db(output_text)  # Pass output_text here
    if symbols:
        for symbol in symbols:
            high_price = get_high_price(symbol, output_text)
            if high_price:
                reduced_price = calculate_5_percent_less(high_price, output_text)
                if reduced_price:
                    update_check_24hrs(symbol, reduced_price, output_text)
                else:
                    output_text.insert(tk.END, "Failed to calculate 5% less price.\n")
            else:
                output_text.insert(tk.END, "Failed to retrieve high price.\n")
    else:
        output_text.insert(tk.END, "No symbols to process.\n")


