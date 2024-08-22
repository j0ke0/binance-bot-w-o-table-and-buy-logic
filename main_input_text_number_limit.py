from psycopg2 import Error
import os
import psycopg2
import sys
import tkinter as tk

def restart_application():
    """Restart the current application."""
    python = sys.executable
    os.execl(python, python, *sys.argv)

def reset_process(root, output_text, insert_positions_into_db):
    try:
        # Insert positions into the database
        insert_positions_into_db(output_text)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, "Database reset completed. Restarting application...\n")
        
        # Close the current Tkinter application
        root.quit()
        
        # Restart the application
        restart_application()
        
    except Exception as e:
        output_text.insert(tk.END, f"Error during reset: {e}\n")


def print_buy_assets_table():
    dbname = "trading"
    user = "postgres"
    password = os.getenv('DATABASE_PASSWORD')  # Ensure you have this environment variable set
    host = "localhost"
    port = "5432"
    
    quantities = []  # List to store quantities without decimal places
    
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        cursor = connection.cursor()

        # Execute the query to get coin and qty from buy_assets table
        query = "SELECT coin, qty FROM buy_assets WHERE coin LIKE '%USDT%';"
        cursor.execute(query)

        # Fetch all rows from the executed query
        rows = cursor.fetchall()

        # Save the results to the quantities list, removing decimal places
        for row in rows:
            # Convert quantity to integer if it has a decimal place
            qty = int(row[1]) if row[1] is not None else 0
            quantities.append(qty)

    except (Exception, Error) as error:
        print(f"Error fetching data from PostgreSQL table: {error}")
    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()

    # Determine the maximum quantity as the limit
    max_limit = max(quantities) if quantities else 21  # Default to 75 if no quantities found

    return max_limit  # Return the maximum quantity as the limit

def validate_ma25_period(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 50:  # Validate if value is a digit between 1 and 50
        return True
    return False

def validate_ma50_period(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 2 <= int(value) <= 100:  # Validate if value is a digit between 1 and 100
        return True
    return False

def validate_highest_price_period(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 110:  # Validate if value is a digit between 1 and 110
        return True
    return False

def validate_avg_volume_period(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 90:  # Validate if value is a digit between 1 and 90
        return True
    return False

def validate_volume_threshold_millions(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 100:  # Validate if value is between 1 and 100
        return True
    return False

def validate_gain_level(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 50:  # Validate if value is between 1 and 50
        return True
    return False

def validate_tp_gain_level(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 200:  # Validate if value is a digit between 1 and 200
        return True
    return False

def validate_sl_loss_level(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 99:  # Validate if value is a digit between 1 and 99
        return True
    return False

def validate_timer_ban_after_sell(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 240:  # Validate if value is a digit between 1 and 240
        return True
    return False

def validate_entry_buy_timer(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 240:  # Validate if value is a digit between 1 and 240
        return True
    return False

def validate_ma15_period(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= 35:  # Validate if value is a digit between 1 and 35
        return True
    return False

def update_button_state(state, buttons):
    """Update the state of all buttons."""
    loop_button, start_button, blacklist_button2, check_button, reset_button, stop_button = buttons
    
    if state == 'disabled':
        loop_button.config(state='disabled')
        start_button.config(state='disabled')
        blacklist_button2.config(state='disabled')
        check_button.config(state='disabled')
        reset_button.config(state='disabled')
    elif state == 'normal':
        loop_button.config(state='normal')
        start_button.config(state='normal')
        blacklist_button2.config(state='normal')
        check_button.config(state='normal')
        reset_button.config(state='normal')
    stop_button.config(state='normal')  # Always keep the stop button enabled


def print_dots(dot_count, interval=6000, output_text=None):
    """Print a dot every `interval` milliseconds for `dot_count` times."""
    if dot_count > 0:
        output_text.insert(tk.END, ' .')
        output_text.update()  # Ensure the output_text widget is updated immediately
        output_text.after(interval, print_dots, dot_count - 1, interval, output_text)
