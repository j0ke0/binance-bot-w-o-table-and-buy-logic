import psycopg2
import os
import tkinter as tk
import requests
from binance.client import Client
from tabulate import tabulate
from buy_keys_dont_del import yawi_api_key, yawi_secret_key

def init_binance_client():
    """Initialize the Binance client with your API keys."""
    api_key = yawi_api_key()
    api_secret = yawi_secret_key()
    return Client(api_key, api_secret)

def fetch_current_price_binance(coin, client, output_text):
    """Fetch the current price of the coin from Binance API."""
    try:
        symbol = coin.upper()
        ticker = client.get_symbol_ticker(symbol=symbol)
        return ticker.get('price', 'N/A')
    except requests.exceptions.RequestException as e:
        output_text.insert(tk.END, f"Network error fetching price for {coin}: {e}\n")
    except Exception as e:
        output_text.insert(tk.END, f"Error fetching price for {coin}: {e}\n")
    return 'N/A'

def connect_to_db(output_text):
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname="trading",
            user="postgres",
            password=os.getenv('DATABASE_PASSWORD'),
            host="localhost",
            port="5432"
        )
        return conn
    except psycopg2.OperationalError as e:
        output_text.insert(tk.END, f"Operational error connecting to the database: {e}\n")
    except Exception as e:
        output_text.insert(tk.END, f"Error connecting to the database: {e}\n")
    return None

def insert_into_buy_prepar(conn, coin_name, buy_price, rsi, output_text):
    """Insert the coin name, buy price, and RSI into the buy_prepar table if it is not in sell_temp_band."""
    try:
        with conn.cursor() as cursor:
            # Check if the coin_name exists in the sell_temp_band table
            check_query_sell_temp_band = "SELECT 1 FROM sell_temp_band WHERE coin_name = %s;"
            cursor.execute(check_query_sell_temp_band, (coin_name,))
            exists_in_sell_temp_band = cursor.fetchone()
            
            if exists_in_sell_temp_band:
                output_text.insert(tk.END, f"Coin {coin_name} This coin has recently been sold, and it is currently frozen. Skipping insertion into buy_prepar.\n")
                return
            
            # Check if the coin_name already exists in the buy_prepar table
            check_query_buy_prepar = "SELECT 1 FROM buy_prepar WHERE coin_name = %s;"
            cursor.execute(check_query_buy_prepar, (coin_name,))
            exists_in_buy_prepar = cursor.fetchone()
            
            if exists_in_buy_prepar:
                output_text.insert(tk.END, f"Coin {coin_name} already exists in buy_prepar. Skipping insertion.\n")
                return
            
            # Insert the new coin_name into the buy_prepar table if it does not exist
            insert_query = """
            INSERT INTO buy_prepar (coin_name, buy_price, rsi) 
            VALUES (%s, %s, %s);
            """
            cursor.execute(insert_query, (coin_name, buy_price, rsi))
            conn.commit()
            output_text.insert(tk.END, f"Inserted {coin_name} into buy_prepar.\n")
    except psycopg2.Error as e:
        output_text.insert(tk.END, f"Error inserting into buy_prepar: {e}\n")

def format_number(value):
    """Format large numbers into a more readable format (e.g., 1.2M, 3.4B)."""
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        else:
            return f"{value:.0f}"
    except ValueError:
        return "N/A"

def apply_tags(output_text, line):
    """Apply 'buy' tag to 'Buy' keywords, leaving 'Sell' as normal color."""
    start_index = len(output_text.get("1.0", tk.END))  # Start position for tag
    for keyword, tag in [('Buy', 'buy')]:  # Only define a tag for 'Buy'
        index = line.find(keyword)
        while index != -1:
            output_text.insert(tk.END, line[:index])
            end_index = index + len(keyword)
            output_text.insert(tk.END, line[index:end_index], tag)
            line = line[end_index:]
            index = line.find(keyword)
    output_text.insert(tk.END, line + "\n")

def compare_price_with_check_24hrs(conn, coin, current_price):
    """Compare the current price with the value in the check_24hrs column and return 'Buy' or 'Sell'."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT check_24hrs FROM top_gainers WHERE coin = %s;", (coin,))
            result = cursor.fetchone()
            if result:
                check_24hrs_value = result[0]
                if current_price is None or check_24hrs_value is None:
                    return 'N/A'
                try:
                    current_price_float = float(current_price)
                    check_24hrs_value_float = float(check_24hrs_value)
                    return "Buy" if current_price_float > check_24hrs_value_float else "Sell"
                except ValueError:
                    return 'N/A'
            else:
                return 'N/A'
    except psycopg2.Error as e:
        return f"Error fetching check_24hrs value: {e}"

def update_delta_ma_price(conn, coin, ma_15_days, output_text):
    """Update the delta_ma_price column in the top_gainers table with ma_15_days multiplied by 3."""
    try:
        # Calculate delta_ma_price
        delta_ma_price = ma_15_days * 3

        # Update the top_gainers table
        with conn.cursor() as cursor:
            update_query = """
            UPDATE top_gainers
            SET delta_ma_price = %s
            WHERE coin = %s;
            """
            cursor.execute(update_query, (delta_ma_price, coin))
            conn.commit()
    except psycopg2.Error as e:
        output_text.insert(tk.END, f"Error updating delta_ma_price for {coin}: {e}\n")


def fetch_data(output_text, highest_price_period):
    """Fetch data from the database, process it, and print it in a formatted table."""
    conn = connect_to_db(output_text)
    if conn is None:
        output_text.insert(tk.END, "Error: Unable to connect to the database.\n")
        return

    client = init_binance_client()
    

    # Define the tag for Buy with blue color
    output_text.tag_configure('buy', foreground='blue')
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM top_gainers WHERE ma_50_below = 0;")
            conn.commit()

            cursor.execute("""
            SELECT coin, ma_50_up, ma_50_below, ma_15_days, volume_60_days, volume_24, days_60_high, delta_ma_price, rsi
            FROM top_gainers;
            """)
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]

            table_data = []
            for row in rows:
                coin, ma_50_up, ma_50_below, ma_15_days, volume_60_days, volume_24, days_60_high, delta_ma_price, rsi = row
                current_price = fetch_current_price_binance(coin, client, output_text)
                update_delta_ma_price(conn, coin, ma_15_days, output_text)

                # Compare current price with check_24hrs
                price_health_comparison = compare_price_with_check_24hrs(conn, coin, current_price)
                
                volume_60_days_formatted = format_number(volume_60_days)
                volume_24_formatted = format_number(volume_24)

                combined_ma = f"Slow: {ma_50_up}\nMid : {ma_50_below}\nFast: {ma_15_days}"
                combined_volume = f"{highest_price_period}Days Vol: {volume_60_days_formatted}\n24 hrs Vol: {volume_24_formatted}"
                combined_high_price = f"High : {days_60_high}\nPrice: {current_price}"

                ma_comparison_result = "Sell" if ma_50_below <= ma_50_up else "Buy"
                ma_15_days_comparison_result = "Sell" if ma_15_days <= ma_50_below else "Buy"
                volume_comparison_result = "Sell" if volume_60_days >= volume_24 else "Buy"
                high_price_comparison_result = "Sell" if float(current_price) <= days_60_high else "Buy"

                ma_ti_combined = f"Mid vs Slow: {ma_comparison_result}\nFast vs Mid: {ma_15_days_comparison_result}"

                rsi_status = "N/A" if rsi is None else "Buy" if rsi >= 66 else "Sell"

                vol_rsi_combined = f"Vol TA: {volume_comparison_result}\nRSI TA: {rsi_status}"

                price_ti_combined = f"Past H: {high_price_comparison_result}"
                if delta_ma_price is not None and current_price is not None:
                    delta_ma_price = float(delta_ma_price)
                    current_price = float(current_price)
                    gap_ma_price = "Buy" if delta_ma_price > current_price else "Sell"
                else:
                    gap_ma_price = "N/A"

                # Combine price_ti_combined with price_health_comparison
                price_health_combined = f"{price_ti_combined}\nTail H: {price_health_comparison}\nMA Gap: {gap_ma_price}"
            
                table_data.append((coin, combined_ma, combined_volume, combined_high_price, price_health_combined, ma_ti_combined, vol_rsi_combined))

                if (ma_comparison_result == "Buy" and 
                    volume_comparison_result == "Buy" and 
                    high_price_comparison_result == "Buy" and 
                    ma_15_days_comparison_result == "Buy" and
                    price_health_comparison == "Buy" and 
                    gap_ma_price == "Buy" and #monitor if its works
                    rsi is not None and rsi >= 66):
                    insert_into_buy_prepar(conn, coin, days_60_high, rsi, output_text)

            if table_data:
                colnames = ["Coin", "MA Details", "Volume", "High & Price", "Price Health", "MA TA", "Vol & RSI TA"]
                table_str = tabulate(table_data, headers=colnames, tablefmt='grid')

                for line in table_str.splitlines():
                    apply_tags(output_text, line)
                   
                output_text.yview_pickplace("end")
            else:
                output_text.insert(tk.END, "No data found.\n")
    except psycopg2.Error as e:
        output_text.insert(tk.END, f"Database query error: {e}\n")
    finally:
        conn.close()

