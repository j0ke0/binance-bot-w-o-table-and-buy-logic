import tkinter as tk
import os
import psycopg2
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

# Replace with your own API key and secret
def get_binance_client():
    from buy_keys_dont_del import yawi_api_key, yawi_secret_key
    api_key = yawi_api_key()
    api_secret = yawi_secret_key()
    return Client(api_key, api_secret)

client = get_binance_client()

# Database connection parameters
db_params = {
    'dbname': 'trading',
    'user': 'postgres',
    'password': os.getenv('DATABASE_PASSWORD'),  # Ensure you have this environment variable set
    'host': 'localhost',
    'port': '5432'
}

def write_to_output(output_text, message):
    """Helper function to write messages to the output_text widget."""
    output_text.insert(tk.END, f"{message}\n")
    output_text.yview(tk.END)  # Scroll to the end to show the latest output

def get_spot_symbols():
    """Fetch all spot trading pairs from Binance."""
    try:
        exchange_info = client.get_exchange_info()
        spot_symbols = [
            s['symbol'] for s in exchange_info['symbols']
            if s['quoteAsset'] == 'USDT' and s['symbol'].endswith('USDT')
        ]
        return spot_symbols
    except BinanceAPIException as e:
        write_to_output(f"Binance API Exception while fetching symbols: {e}")
    except Exception as e:
        write_to_output(f"An error occurred while fetching symbols: {e}")
    return []

def symbol_in_database(symbol):
    """Check if the symbol exists in the PostgreSQL table 'buy_prepar'."""
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                query = "SELECT EXISTS (SELECT 1 FROM buy_prepar WHERE coin_name = %s)"
                cursor.execute(query, (symbol,))
                exists = cursor.fetchone()[0]
                return exists
    except psycopg2.Error as e:
        write_to_output(f"PostgreSQL error: {e}")
        return False

def update_times_posted(symbol, output_text):
    """Update the 'times_posted' column to increment the value by 1 for the given symbol and return the updated value."""
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                update_query = """
                UPDATE buy_prepar
                SET times_posted = times_posted + 1
                WHERE coin_name = %s
                RETURNING times_posted
                """
                cursor.execute(update_query, (symbol,))
                
                if cursor.rowcount > 0:
                    updated_value = cursor.fetchone()[0]
                    conn.commit()
                    write_to_output(output_text, f"\nSuccessfully updated 'times_posted' for {symbol}. New value: {updated_value}\n")
                    return updated_value
                else:
                    write_to_output(output_text, f"\nNo rows were updated for {symbol}.\n")
                    return None
    except psycopg2.Error as e:
        write_to_output(output_text, f"\nPostgreSQL error while updating times_posted: {e}\n")
        return None

def get_open_orders(symbol, entry_buy_timer, output_text):
    """Fetch and print open buy orders for a specific symbol, only if there are open orders and times_posted reaches the specified value."""
    try:
        if symbol_in_database(symbol):
            # Update times_posted and get the updated value
            times_posted = update_times_posted(symbol, output_text)
            
            try:
                timer_value = int(entry_buy_timer.get().strip())
            except ValueError:
                timer_value = 12

            if times_posted == timer_value:
                orders = client.get_open_orders(symbol=symbol)
                if orders:
                    write_to_output(output_text, f"Open buy orders for {symbol}:")
                    for order in orders:
                        order_id = order.get('orderId', 'No Order ID')
                        side = order.get('side', 'Unknown Side')
                        
                        if side == 'BUY':
                            write_to_output(output_text, f"Order ID: {order_id}")
                            write_to_output(output_text, f"Order details: {order}")

                            try:
                                response = client.cancel_order(
                                    symbol=symbol,
                                    orderId=order_id
                                )
                                write_to_output(output_text, "\nOrder cancelled successfully\n")
                                write_to_output(output_text, response)
                            except BinanceOrderException as e:
                                write_to_output(output_text, f"Binance Order Exception while cancelling order: {e}")
                            except Exception as e:
                                write_to_output(output_text, f"An error occurred while cancelling the order: {e}")
                        else:
                            write_to_output(output_text, f"Skipped sell order with Order ID: {order_id}")
                    
                    try:
                        with psycopg2.connect(**db_params) as conn:
                            with conn.cursor() as cursor:
                                delete_query = "DELETE FROM buy_prepar WHERE coin_name = %s"
                                cursor.execute(delete_query, (symbol,))
                                delete_prepar = "DELETE FROM top_gainers WHERE coin = %s"
                                cursor.execute(delete_prepar, (symbol,))
                                insert_blacklist = "INSERT INTO blacklist (coin_name) VALUES (%s)"
                                cursor.execute(insert_blacklist, (symbol,))
                                conn.commit()
                                write_to_output(output_text, f"\n!!!Successfully deleted the row for {symbol}!!!")
                    except psycopg2.Error as e:
                        write_to_output(output_text, f"PostgreSQL error while deleting row: {e}")
                else:
                    write_to_output(output_text, f"No open orders found for {symbol}.")
            # No message if `times_posted` does not match `timer_value`
        # No message if symbol is not in the database
    except BinanceAPIException as e:
        write_to_output(output_text, f"Binance API Exception for {symbol}: {e}")
    except Exception as e:
        write_to_output(output_text, f"An error occurred for {symbol}: {e}")

def get_all_open_orders_with_usdt(entry_buy_timer, output_text):
    """Fetch and print open orders for all spot symbols ending with 'USDT'."""
    spot_symbols = get_spot_symbols()
    if not spot_symbols:
        write_to_output(output_text, "No spot symbols ending with 'USDT' found.")
        return

    for symbol in spot_symbols:
        get_open_orders(symbol, entry_buy_timer, output_text)
