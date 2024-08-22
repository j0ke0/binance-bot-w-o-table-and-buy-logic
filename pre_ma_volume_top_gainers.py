import tkinter as tk
import requests
from datetime import datetime, timedelta
import psycopg2
import os

def fetch_and_update_coin_metrics(output_text, ma_25_days, ma_50_days, ma_15_days, highest_price_period, avg_volume_period):
    # Function to connect to PostgreSQL database
    def connect_to_db():
        try:
            conn = psycopg2.connect(
                dbname="trading",
                user="postgres",
                password=os.getenv('DATABASE_PASSWORD'),
                host="localhost",
                port="5432"
            )
            return conn
        except psycopg2.Error as e:
            output_text.insert(tk.END, f"Error connecting to PostgreSQL database: {e}\n")
            return None
    
    # Function to fetch coin symbols from the database
    def get_coin_symbols(output_text):
        conn = connect_to_db()
        if conn is not None:
            try:
                cur = conn.cursor()
                cur.execute("SELECT coin FROM top_gainers")
                coins = cur.fetchall()
                symbols = [coin[0] for coin in coins]
                output_text.insert(tk.END, f"{len(symbols)} coins was detected on watch list.\n\n")
                return symbols
            except psycopg2.Error as e:
                output_text.insert(tk.END, f"Error fetching data from PostgreSQL: {e}\n")
            finally:
                conn.close()
        return []

    def fetch_highest_price_and_ma(symbol, output_text, ma_25_days, ma_50_days, ma_15_days, highest_price_period, avg_volume_period):
        """Fetch highest price, moving averages, and volume data for a coin."""
        base_url = 'https://api.binance.com/api/v3/klines'
        interval = '1d'
        now = datetime.utcnow()
        start_of_today = datetime(now.year, now.month, now.day)
        end_date = start_of_today - timedelta(milliseconds=1)
        start_date = end_date - timedelta(days=highest_price_period)
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_timestamp,
            'endTime': end_timestamp
        }
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            close_prices = [float(entry[4]) for entry in data]
            ma_25 = calculate_ma(close_prices, ma_25_days)
            ma_50 = calculate_ma(close_prices, ma_50_days)
            ma_15 = calculate_ma(close_prices, ma_15_days)
            high_prices = [float(entry[2]) for entry in data]
            highest_price = max(high_prices) if high_prices else 0
            quote_volumes = [float(entry[7]) for entry in data]
            avg_volume_30_days = sum(quote_volumes[-avg_volume_period:]) / avg_volume_period if len(quote_volumes) >= avg_volume_period else 0
            volume_24_hours = quote_volumes[-1] if len(quote_volumes) >= 1 else 0

            return highest_price, ma_25, ma_50, ma_15, avg_volume_30_days, volume_24_hours
        else:
            output_text.insert(tk.END, f"Failed to retrieve data for {symbol}. Status code: {response.status_code}\n")
            return None, None, None, None, None, None

    def update_60_days_high(symbol, highest_price, ma_25, ma_50, ma_15, avg_volume_30_days, volume_24_hours, output_text):
        """Update the database with the latest metrics."""
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                highest_price_str = format(highest_price, '.8f')
                ma_25_str = format(ma_25, '.8f') if ma_25 is not None else None
                ma_50_str = format(ma_50, '.8f') if ma_50 is not None else None
                ma_15_str = format(ma_15, '.8f') if ma_15 is not None else None
                avg_volume_30_days_adjusted = avg_volume_30_days * 1.5
                avg_volume_30_days_str = format(avg_volume_30_days_adjusted, '.8f')
                volume_24_hours_str = format(volume_24_hours, '.8f')
                cur.execute(
                    "UPDATE top_gainers SET days_60_high = %s, ma_50_up = %s, ma_50_below = %s, ma_15_days = %s, volume_60_days = %s, volume_24 = %s WHERE coin = %s",
                    (highest_price_str, ma_50_str, ma_25_str, ma_15_str, avg_volume_30_days_str, volume_24_hours_str, symbol)
                )
                conn.commit()
                output_text.insert(tk.END, "Actual Data from Binance:\n")
                output_text.insert(tk.END, f"{'=' * 30}\n")
                output_text.insert(tk.END, f"Coin: {symbol}\n")
                output_text.insert(tk.END, f"Highest Price: {highest_price_str}\n")
                output_text.insert(tk.END, f"MA Slow: {ma_25_str}\n")
                output_text.insert(tk.END, f"MA Mid : {ma_50_str}\n")
                output_text.insert(tk.END, f"MA Fast: {ma_15_str}\n")
                output_text.insert(tk.END, f"Avg Volume 30 Days (adjusted): {avg_volume_30_days_str}\n")
                output_text.insert(tk.END, f"Volume 24 Hours: {volume_24_hours_str}\n")
                output_text.insert(tk.END, f"{'=' * 30}\n")
            except psycopg2.Error as e:
                output_text.insert(tk.END, f"Error updating data for {symbol}: {e}\n")
            finally:
                conn.close()
                output_text.insert(tk.END, "" + "="*30 + "\n")
                output_text.insert(tk.END, "Database connection is closed.\n")
                output_text.insert(tk.END, "="*30 + "\n\n")


    # Calculate moving average based on given days
    def calculate_ma(close_prices, days):
        if len(close_prices) >= days:
            return sum(close_prices[-days:]) / days
        else:
            return 0  # Default to 0 if less than given days of data
    
    # Main function to fetch data for each coin symbol and update the database
    coin_symbols = get_coin_symbols(output_text)

    for symbol in coin_symbols:
        highest_price, ma_25, ma_50, ma_15, avg_volume_30_days, volume_24_hours = fetch_highest_price_and_ma(
            symbol, output_text, ma_25_days, ma_50_days, ma_15_days, highest_price_period, avg_volume_period
        )
        if all(v is not None for v in [highest_price, ma_25, ma_50, ma_15, avg_volume_30_days, volume_24_hours]):
            update_60_days_high(
                symbol, highest_price, ma_25, ma_50, ma_15, avg_volume_30_days, volume_24_hours, output_text
            )
        else:
            output_text.insert(tk.END, f"Failed to fetch data for {symbol}.\n")