import psycopg2
import tkinter as tk
from psycopg2 import Error
import os

def calculate_tp_sl(output_text, tp_gain_level, sl_loss_level):
    # Database connection parameters
    dbname = "trading"
    user = "postgres"
    password = os.getenv('DATABASE_PASSWORD')  # Ensure you have this environment variable set
    host = "localhost"
    port = "5432"

    # Check if password is set
    if not password:
        output_text.insert(tk.END, "Error: DATABASE_PASSWORD environment variable not set.\n")
        return

    conn = None
    rows_updated = False  # Flag to track if any rows are updated
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        # Create a cursor object
        with conn.cursor() as cur:
            # Define the SQL query to fetch data from the table
            query = "SELECT coin_name, buy_price FROM buy_prepar;"

            try:
                # Execute the query
                cur.execute(query)

                # Fetch all rows from the executed query
                rows = cur.fetchall()

                # Get the take profit and stop loss percentages from the entry widgets
                tp_percentage = float(tp_gain_level.get().strip()) if tp_gain_level.get().strip() else 10
                sl_percentage = float(sl_loss_level.get().strip()) if sl_loss_level.get().strip() else 10

                # Print the column names
                output_text.insert(tk.END, f"\n{'coin name':<20} {'buy price':<18} TP (+{tp_percentage}% value)       SL (-{sl_percentage}% value)\n")
                output_text.insert(tk.END, "-" * 100 + "\n")

                # Print each row of the result with formatted buy_price, price with TP percentage increase, and price minus SL percentage decrease
                for row in rows:
                    coin_name, buy_price = row

                    # Format buy_price to remove trailing zeros
                    formatted_buy_price = f"{float(buy_price):g}" if buy_price is not None else "N/A"

                    # Calculate the new price with TP percentage increase and SL percentage decrease
                    if buy_price is not None:
                        buy_price_float = float(buy_price)
                        price_with_tp_increase = buy_price_float * (1 + tp_percentage / 100)
                        price_with_sl_decrease = buy_price_float * (1 - sl_percentage / 100)
                        
                        # Format the calculated prices
                        formatted_price_with_tp_increase = f"{price_with_tp_increase:g}"
                        formatted_price_with_sl_decrease = f"{price_with_sl_decrease:g}"
                    else:
                        formatted_price_with_tp_increase = "N/A"
                        formatted_price_with_sl_decrease = "N/A"

                    # Calculate the length of formatted_buy_price
                    formatted_buy_price_length = len(formatted_buy_price)

                    # Truncate or pad formatted_price_with_tp_increase to match the length of formatted_buy_price
                    if len(formatted_price_with_tp_increase) > formatted_buy_price_length:
                        formatted_price_with_tp_increase = formatted_price_with_tp_increase[:formatted_buy_price_length]
                    else:
                        formatted_price_with_tp_increase = formatted_price_with_tp_increase.ljust(formatted_buy_price_length)

                    # Truncate or pad formatted_price_with_sl_decrease to match the length of formatted_buy_price
                    if len(formatted_price_with_sl_decrease) > formatted_buy_price_length:
                        formatted_price_with_sl_decrease = formatted_price_with_sl_decrease[:formatted_buy_price_length]
                    else:
                        formatted_price_with_sl_decrease = formatted_price_with_sl_decrease.ljust(formatted_buy_price_length)

                    # Print the results
                    output_text.insert(tk.END, f"{coin_name:<20} {formatted_buy_price:<18} {formatted_price_with_tp_increase:<23} {formatted_price_with_sl_decrease:<10}\n")

                    # Update the database with the new TP price and cut price
                    update_query = """
                    UPDATE buy_prepar
                    SET tp_price = %s, cut_price = %s
                    WHERE coin_name = %s;
                    """
                    cur.execute(update_query, (formatted_price_with_tp_increase, formatted_price_with_sl_decrease, coin_name))

                    # Set flag if any row is updated
                    rows_updated = True

                # Commit the changes to the database
                conn.commit()

                # Provide feedback based on the update result
                if rows_updated:
                    output_text.insert(tk.END, "\nTP and Cut Prices were successfully updated in the database.\n\n")
                    output_text.yview_pickplace("end")
                else:
                    output_text.insert(tk.END, "\nNo TP or SL needs update. No cryptocurrency meets the requirements.\n\n")
                    output_text.yview_pickplace("end")

            except Exception as e:
                output_text.insert(tk.END, f"Error executing the query: {e}\n")

    except Exception as e:
        output_text.insert(tk.END, f"Error connecting to the database: {e}\n")

    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()
