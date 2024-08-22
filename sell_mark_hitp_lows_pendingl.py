import requests
import time
import hmac
import hashlib
import psycopg2
import os
from urllib.parse import urlencode
from buy_keys_dont_del import yawi_api_key, yawi_secret_key

# Binance API base URL and credentials
base_url = 'https://api.binance.com'
api_key = yawi_api_key()  # Replace with your Binance API key
api_secret = yawi_secret_key()  # Replace with your Binance API secret

# Database credentials
db_host = 'localhost'
db_name = 'trading'
db_user = 'postgres'
db_password = os.getenv('DATABASE_PASSWORD')

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password
    )

def signed_request(endpoint, params={}):

    query_string = urlencode(params)
    timestamp = int(time.time() * 1000)
    params['timestamp'] = timestamp
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    headers = {
        'X-MBX-APIKEY': api_key
    }

    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Binance API request failed with status code {response.status_code}: {response.text}")

    return response.json()

def all_positions():

    endpoint = '/api/v3/account'
    params = {'timestamp': int(time.time() * 1000)}
    response = signed_request(endpoint, params)
    return response.get('balances', [])

def get_12hr_high_low(symbol):

    endpoint = '/api/v3/klines'
    interval = '1h'
    end_time = int(time.time() * 1000)
    start_time = end_time - (48 * 60 * 60 * 1000)  # 12 hours ago
    
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time
    }
    
    response = requests.get(f"{base_url}{endpoint}", params=params)
    
    if response.status_code != 200:
        raise Exception(f"Binance API request failed with status code {response.status_code}: {response.text}")
    
    data = response.json()
    
    high_prices = [float(candle[2]) for candle in data]  # High prices from each candlestick
    low_prices = [float(candle[3]) for candle in data]   # Low prices from each candlestick
    
    return max(high_prices, default=0), min(low_prices, default=0)

def update_db(symbol_with_usdt, high_price, low_price):

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the symbol exists in the table
            cursor.execute("SELECT EXISTS (SELECT 1 FROM sell_table_tpsl WHERE coin_name = %s)", (symbol_with_usdt,))
            exists = cursor.fetchone()[0]
            
            if exists:
                # Update the existing record
                cursor.execute("""
                    UPDATE sell_table_tpsl
                    SET base_hi = %s, base_low = %s
                    WHERE coin_name = %s
                """, (high_price, low_price, symbol_with_usdt))
                conn.commit()
                return True  # Indicate that an update occurred
            else:
                # If the record does not exist, do nothing
                print(f"Record for {symbol_with_usdt} does not exist. Skipping update.")
                return False  # Indicate that no update occurred
    finally:
        conn.close()

def recheck_port_positions():
    """
    Check all positions and update the database with 12-hour high and low prices.
    """
    positions = all_positions()
    excluded_symbols = ['EON', 'ADD', 'MEETONE', 'ATD', 'EOP', 'ETHW', 'FLR', 'BNB', 'USDT']
    
    any_update_occurred = False
    
    for position in positions:
        symbol = position['asset']
        free_balance = float(position['free'])
        
        if symbol not in excluded_symbols and free_balance != 0.0:
            symbol_with_usdt = f"{symbol}USDT"
            high_price, low_price = get_12hr_high_low(symbol_with_usdt)
            print(f"Detected {symbol_with_usdt} with quantity {free_balance}. 12h High: {high_price}, 12h Low: {low_price}.")
            update_occurred = update_db(symbol_with_usdt, high_price, low_price)
            any_update_occurred = any_update_occurred or update_occurred
    
    if not any_update_occurred:
        print("No records were updated in the database.")
    else:
        print("Finished processing positions with updates.")

# Example usage
if __name__ == "__main__":
    recheck_port_positions()
