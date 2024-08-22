import requests
import time
import os
import hmac
import hashlib
from urllib.parse import urlencode
import tkinter as tk
import psycopg2
from buy_keys_dont_del import yawi_api_key, yawi_secret_key

# code to view all the current positions

# Binance API endpoints
base_url = 'https://api.binance.com'
api_key = yawi_api_key()  # Replace with your Binance API key
api_secret = yawi_secret_key()  # Replace with your Binance API secret

# PostgreSQL connection parameters
db_host = 'localhost'
db_name = 'trading'
db_user = 'postgres'
db_password = os.getenv('DATABASE_PASSWORD')

# Function to create a signed request
def signed_request(endpoint, params={}):
    query_string = urlencode(params)
    timestamp = int(time.time() * 1000)
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    headers = {
        'X-MBX-APIKEY': api_key
    }

    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    response = requests.get(url, headers=headers)
    return response.json()

# Function to truncate the assets table
def assets_table():
    try:
        conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()

        # Truncate the assets table
        truncate_query = "TRUNCATE TABLE sell_table_tpsl;"
        cursor.execute(truncate_query)
        conn.commit()

    except (Exception, psycopg2.Error) as error:
        # Log error if necessary
        pass

    finally:
        if conn:
            cursor.close()
            conn.close()

def recheck_port_positions(output_text):
    assets_table()  # Truncate the table before inserting new data
    positions = all_positions()
    excluded_assets = ['EON', 'ADD', 'MEETONE', 'ATD', 'EOP', 'ETHW', 'FLR', 'BNB', 'USDT']  # Updated list of assets to exclude
    
    inserted_any = False  # Flag to track if any record is inserted

    try:
        conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()

        output_text.tag_configure('blue', foreground='blue')
        
        for position in positions:
            asset = position['asset']
            free_balance = float(position['free'])
            
            # Create the full coin name by appending 'USDT' to the asset
            coin_name = f"{asset}USDT"
            
            # Check if the asset is not in the excluded list and has a non-zero balance
            if asset not in excluded_assets and free_balance != 0.0:
                insert_query = "INSERT INTO sell_table_tpsl (coin_name, qty) VALUES (%s, %s);"
                cursor.execute(insert_query, (coin_name, free_balance))
                output_text.insert(tk.END, f"Inserted {coin_name} with quantity {free_balance}. \n", 'blue')
                inserted_any = True
        
        conn.commit()
        if inserted_any:
            output_text.insert(tk.END, "Successfully copied from port to database.\n")
            output_text.yview_pickplace("end")
        else:
            output_text.insert(tk.END, "No assets were inserted into the database.\n")
            output_text.yview_pickplace("end")
    
    except (Exception, psycopg2.Error) as error:
        output_text.insert(tk.END, f"Database error: {error}\n")
    
    finally:
        if conn:
            cursor.close()
            conn.close()

# Function to get all positions from Binance API
def all_positions():
    endpoint = '/api/v3/account'
    params = {
        'timestamp': int(time.time() * 1000)
    }
    response = signed_request(endpoint, params)
    return response.get('balances', [])