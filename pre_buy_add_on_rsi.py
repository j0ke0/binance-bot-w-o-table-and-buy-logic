import tkinter as tk
import requests
from datetime import datetime, timedelta
import psycopg2
import os
from tabulate import tabulate

def connect_to_db(output_text):
    """Connects to the PostgreSQL database."""
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
        output_text.yview_pickplace("end")
        return None

def get_coin_symbols(output_text):
    """Fetches coin symbols from the database."""
    conn = connect_to_db(output_text)
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT coin FROM top_gainers")
                coins = cur.fetchall()
                symbols = [coin[0] for coin in coins]
                return symbols
        except psycopg2.Error as e:
            output_text.insert(tk.END, f"Error fetching data from PostgreSQL: {e}\n")
            output_text.yview_pickplace("end")
        finally:
            conn.close()
    return []

def calculate_rsi(prices, period=14):
    """Calculates the Relative Strength Index (RSI)."""
    if len(prices) < period:
        return None

    gains = []
    losses = []

    for i in range(1, period):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-change)

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    for i in range(period, len(prices)):
        change = prices[i] - prices[i - 1]
        gain = max(change, 0)
        loss = -min(change, 0)

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
        rsi = 100 - (100 / (1 + rs))

    return rsi

def fetch_rsi(symbol, output_text, rsi_period=14):
    """Fetches RSI data from Binance API and calculates RSI."""
    base_url = 'https://api.binance.com/api/v3/klines'
    interval = '1d'

    now = datetime.utcnow()
    start_of_today = datetime(now.year, now.month, now.day)
    end_date = start_of_today - timedelta(milliseconds=1)
    start_date = end_date - timedelta(days=rsi_period * 2)

    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': int(start_date.timestamp() * 1000),
        'endTime': int(end_date.timestamp() * 1000)
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()
        close_prices = [float(entry[4]) for entry in data]

        rsi = calculate_rsi(close_prices, rsi_period)

        return rsi
    except requests.RequestException as e:
        output_text.insert(tk.END, f"Failed to retrieve data for {symbol}. Error: {e}\n")
        output_text.yview_pickplace("end")
        return None

def update_rsi(symbol, rsi, output_text):
    """Updates the RSI value for a symbol in the database."""
    conn = connect_to_db(output_text)
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE top_gainers SET rsi = %s WHERE coin = %s",
                    (f"{rsi:.2f}" if rsi is not None else None, symbol)
                )
                conn.commit()
        except psycopg2.Error as e:
            output_text.insert(tk.END, f"Error updating data for {symbol}: {e}\n")
            output_text.yview_pickplace("end")
        finally:
            conn.close()

#non RSI relate just a print function for the table
def get_coin_data(output_text):
    """Fetches coin symbols and their check_24hrs values from the database."""
    conn = connect_to_db(output_text)
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT coin, check_24hrs FROM top_gainers")
                coins = cur.fetchall()
                return coins
        except psycopg2.Error as e:
            output_text.insert(tk.END, f"Error fetching data from PostgreSQL: {e}\n")
            output_text.yview_pickplace("end")
        finally:
            conn.close()
    return []

def fetch_and_update_coin_rsi(output_text, rsi_period=14):
    """Fetches and updates RSI for all coin symbols and includes check_24hrs."""
    coin_data = get_coin_data(output_text)
    results = []

    for symbol, check_24hrs in coin_data:
        rsi = fetch_rsi(symbol, output_text, rsi_period)
        if rsi is not None:
            update_rsi(symbol, rsi, output_text)
            results.append([symbol, f"{rsi_period}-day RSI", f"{rsi:.2f}", check_24hrs])
        else:
            results.append([symbol, f"{rsi_period}-day RSI", "Data insufficient", check_24hrs])

    # Format and insert table
    table = tabulate(results, headers=["Symbol", "Period", "RSI", "Buy Range"], tablefmt="grid")
    output_text.insert(tk.END, f"\n{table}\n")
    output_text.yview_pickplace("end")
