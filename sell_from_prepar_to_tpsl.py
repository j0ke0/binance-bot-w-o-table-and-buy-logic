# update_sell_table.py
import psycopg2
import psycopg2.extras
import os
import tkinter as tk

def update_sell_table(output_text):
    """Update the sell_table_tpsl based on the data from buy_prepar."""

    # PostgreSQL connection parameters
    db_host = 'localhost'
    db_name = 'trading'
    db_user = 'postgres'
    db_password = os.getenv('DATABASE_PASSWORD')

    # Check if the database password is set
    if db_password is None:
        raise ValueError("The DATABASE_PASSWORD environment variable is not set.")

    def format_number(value, decimals=None):
        """Format a number to remove trailing zeros and match the specified decimal places."""
        if value is None:
            return None
        str_value = f"{value:.{decimals}f}" if decimals is not None else str(value)
        if '.' in str_value:
            str_value = str_value.rstrip('0').rstrip('.')
        return str_value

    def calculate_percentage(value, percentage):
        """Calculate a percentage of the given value."""
        if value is None:
            return None
        return value * (percentage / 100.0)

    def get_decimal_places(value):
        """Return the number of decimal places in a number."""
        if '.' in str(value):
            return len(str(value).split('.')[1])
        return 0

    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Fetch coin names, buy prices, cut prices, and tp prices from buy_prepar
        cursor.execute("SELECT coin_name, buy_price, cut_price, tp_price FROM buy_prepar")
        buy_data = {row['coin_name']: (row['buy_price'], row['cut_price'], row['tp_price']) for row in cursor.fetchall()}

        updated_rows = []

        # Update the sell_table_tpsl table with corresponding buy_price, cut_price, and tp_price
        for coin_name, (buy_price, cut_price, tp_price) in buy_data.items():
            cursor.execute("""
                UPDATE sell_table_tpsl
                SET b_price = %s, sl = %s, tp = %s
                WHERE coin_name = %s
                RETURNING coin_name, b_price, sl, tp
            """, (buy_price, cut_price, tp_price, coin_name))
            
            updated_row = cursor.fetchone()
            if updated_row:
                formatted_sl = format_number(updated_row['sl'])
                sl_value = float(formatted_sl)  # Convert formatted string back to float
                sl_percentage = calculate_percentage(sl_value, 1)  # Calculate 1% of sl
                new_sl_value = sl_value - sl_percentage  # Subtract 1% from the original value
                
                # Determine the number of decimal places in the original formatted_sl
                decimal_places = get_decimal_places(formatted_sl)
                formatted_new_sl_value = format_number(new_sl_value, decimals=decimal_places)  # Format the result
                
                # Update the sl_trigger column with the new value
                cursor.execute("""
                    UPDATE sell_table_tpsl
                    SET stop_trigger = %s
                    WHERE coin_name = %s
                """, (formatted_new_sl_value, coin_name))
                
                updated_row['new_stop_trigger'] = formatted_new_sl_value
                updated_rows.append(updated_row)

        # Commit the changes
        conn.commit()

        # Print the updated rows and specifically the 'sl' value and 'tp_price'
        if updated_rows:
            for row in updated_rows:
                formatted_sl = format_number(row['sl'])
                sl_value = float(formatted_sl)  # Convert formatted string back to float
                sl_percentage = calculate_percentage(sl_value, 1)  # Calculate 1% of sl
                new_sl_value = sl_value - sl_percentage  # Subtract 1% from the original value
                
                # Determine the number of decimal places in the original formatted_sl
                decimal_places = get_decimal_places(formatted_sl)
                formatted_new_sl_value = format_number(new_sl_value, decimals=decimal_places)  # Format the result

                output_text.insert(tk.END, f"\nSL & TP value for: {row['coin_name']} limit: {formatted_sl} stop: {formatted_new_sl_value}, TP Price: {row['tp']}\n")
                output_text.yview_pickplace("end")
        else:
            # Add visual appeal to the "Nothing to sell" message
            output_text.insert(tk.END, "\n" + "="*50 + "\n")
            output_text.insert(tk.END, "    Nothing to sell. No rows were updated.\n")
            output_text.insert(tk.END, "="*50 + "\n")
            output_text.yview_pickplace("end")

    except Exception as e:
        output_text.insert(tk.END, f"An error occurred: {e}\n")
        output_text.yview_pickplace("end")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
