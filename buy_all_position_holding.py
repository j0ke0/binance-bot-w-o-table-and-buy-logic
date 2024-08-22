import requests
import time
import os
import hmac
import hashlib
from urllib.parse import urlencode
import tkinter as tk
import psycopg2
from buy_keys_dont_del import yawi_api_key, yawi_secret_key
from tabulate import tabulate

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
def create_signed_request(endpoint, params={}):
    timestamp = int(time.time() * 1000)
    params['timestamp'] = timestamp
    query_string = urlencode(params)
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    headers = {
        'X-MBX-APIKEY': api_key
    }

    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an HTTPError for bad responses
    return response.json()

# Function to truncate the assets table
def truncate_assets_table(output_text):
    try:
        with psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password) as conn:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE buy_assets;")
                conn.commit()
    except (Exception, psycopg2.Error) as error:
        output_text.insert(tk.END, f"Error truncating table: {error}\n")
        return False
    return True

def insert_positions_into_db(output_text):
    if not truncate_assets_table(output_text):
        return

    positions = get_all_positions()
    excluded_assets = ['EON', 'ADD', 'MEETONE', 'ATD', 'EOP', 'ETHW', 'FLR']
    
    table_data = []

    try:
        with psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password) as conn:
            with conn.cursor() as cursor:
                for position in positions:
                    asset = position['asset']
                    free_balance = float(position['free'])
                    locked_balance = float(position['locked'])

                    if asset not in excluded_assets:
                        if free_balance != 0.0:
                            cursor.execute("INSERT INTO buy_assets (coin, qty) VALUES (%s, %s);", (asset, free_balance))
                            table_data.append([asset, free_balance])
                        
                        if locked_balance != 0.0:
                            cursor.execute("INSERT INTO buy_assets (coin, qty) VALUES (%s, %s);", (asset, locked_balance))
                            table_data.append([asset, locked_balance])

                conn.commit()
                if table_data:
                    # Use tabulate to format the data
                    header = ["Asset", "Quantity"]
                    formatted_table = tabulate(table_data, headers=header, tablefmt='grid')
                    output_text.insert(tk.END, f"Successfully copied port. Looping to your wallet.\n\n{formatted_table}\n")
                else:
                    output_text.insert(tk.END, "No assets were inserted into the database.\n")

                output_text.yview_pickplace("end")
    except (Exception, psycopg2.Error) as error:
        output_text.insert(tk.END, f"Database error: {error}\n")

# Function to get all positions from Binance API
def get_all_positions():
    endpoint = '/api/v3/account'
    params = {
        'timestamp': int(time.time() * 1000)
    }
    response = create_signed_request(endpoint, params)
    return response.get('balances', [])
