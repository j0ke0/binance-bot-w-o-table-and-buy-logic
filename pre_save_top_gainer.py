import requests
import psycopg2
from psycopg2 import Error
import os
import tkinter as tk

def output_to_text(message, output_widget):
    """Append message to the output_text widget."""
    output_widget.insert(tk.END, message + "\n")
    output_widget.yview(tk.END)  # Auto-scroll to the end

def fetch_blacklisted_coins(output_widget):
    """Fetch blacklisted coins from the database."""
    try:
        # Connect to PostgreSQL database
        with psycopg2.connect(
            user="postgres",
            password=os.getenv('DATABASE_PASSWORD'),
            host="localhost",
            port="5432",
            database="trading"
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT coin_name FROM blacklist')
                blacklisted_coins = {row[0] for row in cursor.fetchall()}
        return blacklisted_coins
    except psycopg2.Error as error:
        output_to_text(f"Error while connecting to PostgreSQL: {error}", output_widget)
        return set()

def output_to_text(message, output_widget):
    """Append message to the output_text widget."""
    output_widget.insert(tk.END, message + "\n")
    output_widget.yview(tk.END)  # Auto-scroll to the end

def no_coins_match(output_widget):
    """Output a formatted message when no coins match the criteria."""
    message = (
        "No coins match the criteria.\n"
        "===========================\n"
        "          EMPTY LIST       \n"
        "===========================\n"
    )
    output_to_text(message, output_widget)


def get_top_gainers_usdt(output_widget, volume_threshold_millions, gain_level):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    
    # Convert volume threshold from millions to absolute value
    volume_threshold = volume_threshold_millions * 1000000

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors
        tickers = response.json()

        # Fetch blacklisted coins
        blacklisted_coins = fetch_blacklisted_coins(output_widget)

        # Filter tickers to include only those traded against USDT and sort by percentage change
        tickers_usdt = [ticker for ticker in tickers if ticker['symbol'].endswith('USDT')]
        tickers_sorted = sorted(tickers_usdt, key=lambda x: float(x['priceChangePercent']), reverse=True)
        
        # Output top gainers with percentage change above the gain level and volume above the threshold
        top_gainers = []
        for ticker in tickers_sorted:
            if (float(ticker['priceChangePercent']) > gain_level and 
                float(ticker['quoteVolume']) > volume_threshold):
                if ticker['symbol'] in blacklisted_coins:
                    message = f"{ticker['symbol']} is blacklisted. Skipping this coin."
                    output_to_text(message, output_widget)
                    continue
                volume_int = int(float(ticker['quoteVolume']))
                top_gainers.append((ticker['symbol'], ticker['priceChangePercent']))
                message = f"{ticker['symbol']}: {ticker['priceChangePercent']}% | Volume: {volume_int}"
                output_to_text(message, output_widget)
        
        if not top_gainers:
            no_coins_match(output_widget)  # Use the new formatted message function
        else:
            # Save top gainers data to PostgreSQL database
            save_to_database(top_gainers, output_widget)
    
    except requests.exceptions.RequestException as e:
        output_to_text(f"Error fetching data from Binance API: {e}", output_widget)


def save_to_database(top_gainers, output_widget):
    try:
        # Connect to PostgreSQL database
        with psycopg2.connect(
            user="postgres",
            password=os.getenv('DATABASE_PASSWORD'),
            host="localhost",
            port="5432",
            database="trading"
        ) as connection:
            with connection.cursor() as cursor:
                # Check if coin already exists in the database
                existing_coins = set()
                cursor.execute('SELECT coin FROM top_gainers')
                existing_coins.update(row[0] for row in cursor.fetchall())
                
                # Prepare list of new entries to insert
                new_entries = []
                already_saved = []

                for coin, gain in top_gainers:
                    if coin not in existing_coins:
                        new_entries.append((coin, gain))
                    else:
                        already_saved.append(coin)
                
                # Insert new data into the table with timestamp (if not already present)
                if new_entries:
                    insert_query = '''
                        INSERT INTO top_gainers (coin, gain, timestamp)
                        VALUES (%s, %s, CURRENT_TIMESTAMP);
                    '''
                    cursor.executemany(insert_query, new_entries)
                    connection.commit()
                    output_to_text(f"New coins saved to database: {', '.join([coin for coin, _ in new_entries])}.", output_widget)
                
                # Log already saved coins
                if already_saved:
                    output_to_text(f"Already saved in the database: {', '.join(already_saved)}", output_widget)
                    
    except psycopg2.Error as error:
        output_to_text(f"Error while connecting to PostgreSQL: {error}", output_widget)
    finally:
        # Improved message formatting
        message = (
            "==============================\n"
            " Database connection is closed \n"
            "==============================\n"
        )
        output_to_text(message, output_widget)
