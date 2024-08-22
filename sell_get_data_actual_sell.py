import psycopg2
import tkinter as tk
import os
import requests
import time
import hmac
import hashlib
from buy_keys_dont_del import yawi_api_key, yawi_secret_key, save_base_url

# API credentials and endpoints
base_url = save_base_url()
api_key = yawi_api_key()
api_secret = yawi_secret_key()

# Database credentials
dbname = "trading"
user = "postgres"
password = os.getenv('DATABASE_PASSWORD')  # Ensure you have this environment variable set
host = "localhost"
port = "5432"

headers = {
    'X-MBX-APIKEY': api_key
}

def generate_signature(params):
    """
    Generate HMAC SHA256 signature for API request parameters.
    """
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature

def sell_actual_oco_transaction(output_text):
    """
    Fetch coin details from the database and place OCO orders. 
    After placing an order, save the coin_name to sell_temp_band and then delete it from sell_table_tpsl.
    """
    try:
        with psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        ) as conn:
            with conn.cursor() as cursor:
                query = "SELECT coin_name, qty, tp, sl, stop_trigger FROM sell_table_tpsl"
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    coin_name, qty, tp, sl, stop_trigger = row
                    
                    # Skip if coin_name exists in sell_temp_band
                    if coin_exists_in_temp_band(coin_name, conn):
                        output_text.insert(tk.END, f"\nCoin Name '{coin_name}' already exists in sell_temp_band. Skipping...\n")
                        output_text.yview_pickplace("end")
                        continue
                    
                    try:
                        qty = float(qty)
                        tp = float(tp)
                        sl = float(sl)
                        stop_trigger = float(stop_trigger)
                    except (ValueError, TypeError):
                        qty, tp, sl, stop_trigger = 0.0, 0.0, 0.0, 0.0
                    
                    # Print coin details along with sl and stop_trigger
                    output_text.insert(tk.END, f"\nCoin Name: {coin_name}, Quantity: {qty}, TP: {tp}, SL: {sl}, Stop Trigger: {stop_trigger}\n")
                    output_text.yview_pickplace("end")
                    
                    # Place the OCO order for each coin
                    if place_oco_order(coin_name, qty, sl, tp, stop_trigger, output_text):
                        # If order is successfully placed, save to sell_temp_band and then delete the row
                        if save_to_temp_band(coin_name, conn, output_text):
                            delete_row_by_coin_name(coin_name, conn, output_text)
                
    except Exception as e:
        output_text.insert(tk.END, f"\nAn error occurred: {e}\n")
        output_text.yview_pickplace("end")

def coin_exists_in_temp_band(coin_name, conn):
    """
    Check if the coin_name already exists in the sell_temp_band table.
    """
    try:
        with conn.cursor() as cursor:
            query = "SELECT EXISTS (SELECT 1 FROM sell_temp_band WHERE coin_name = %s)"
            cursor.execute(query, (coin_name,))
            exists = cursor.fetchone()[0]
            return exists
    except Exception as e:
        print(f"An error occurred on the sell transaction: {e}")
        return False

def place_oco_order(symbol, quantity, stop_price, limit_price, stop_limit_price, output_text):
    """
    Place an OCO (One-Cancels-the-Other) order via the trading API.
    """
    endpoint = '/order/oco'
    params = {
        'symbol': symbol,
        'side': 'SELL',
        'quantity': quantity,
        'stopPrice': stop_price,
        'price': limit_price,
        'stopLimitPrice': stop_limit_price,
        'stopLimitTimeInForce': 'GTC',
        'timestamp': int(time.time() * 1000)
    }
    params['signature'] = generate_signature(params)
    
    try:
        response = requests.post(base_url + endpoint, headers=headers, params=params)
        response.raise_for_status()
        output_text.insert(tk.END, f"OCO Order placed successfully: {response.json()}\n")
        return True
    except requests.exceptions.HTTPError as err:
        output_text.insert(tk.END, f"HTTP error occurred: {err}\n")
        output_text.insert(tk.END, f"Response status code: {response.status_code}\n")
        output_text.insert(tk.END, f"Response text: {response.text}\n")
    except Exception as err:
        output_text.insert(tk.END, f"Other error occurred: {err}\n")
    return False

def save_to_temp_band(coin_name, conn, output_text):
    """
    Save the coin_name and a constant value '1' to the sell_temp_band table.
    """
    try:
        with conn.cursor() as cursor:
            insert_query = """
            INSERT INTO sell_temp_band (coin_name, cycle_band) 
            VALUES (%s, %s)
            """
            cursor.execute(insert_query, (coin_name, 0))
            conn.commit()
            output_text.insert(tk.END, f"Coin Name '{coin_name}' place a OCO successfully.\n")
            output_text.yview_pickplace("end")
            return True
    except Exception as e:
        output_text.insert(tk.END, f"An error occurred while saving to sell_temp_band: {e}\n")
    return False

def delete_row_by_coin_name(coin_name, conn, output_text):
    """
    Delete a row from the database by its coin_name.
    """
    try:
        with conn.cursor() as cursor:
            delete_query = "DELETE FROM sell_table_tpsl WHERE coin_name = %s"
            cursor.execute(delete_query, (coin_name,))
            conn.commit()
            output_text.insert(tk.END, f"Coin_name '{coin_name}' ban for a few minutes for any transaction.\n")
            output_text.yview_pickplace("end")
    except Exception as e:
        output_text.insert(tk.END, f"An error occurred while deleting the row: {e}\n")