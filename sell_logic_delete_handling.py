import psycopg2
import os
import tkinter as tk

def update_prepar_times_posted(entry_buy_timer, output_text):
    # Retrieve the database password from environment variables
    password = os.getenv('DATABASE_PASSWORD')
    if not password:
        output_text.insert(tk.END, "DATABASE_PASSWORD environment variable not set\n")
        return

    dbname = "trading"
    user = "postgres"
    host = "localhost"
    port = "5432"

    # Try to parse the threshold value from the entry widget
    try:
        threshold = int(entry_buy_timer.get().strip())
    except ValueError:
        output_text.insert(tk.END, "Invalid threshold value in entry_buy_timer.\n")
        return

    # Establish a connection to the database
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = conn.cursor()

        # Print cycle_band values and count rows before deletion
        output_text.insert(tk.END, "\nRows before deletion: ")
        cursor.execute("SELECT times_posted FROM buy_prepar;")
        rows_before = cursor.fetchall()
        output_text.insert(tk.END, f"Total rows before deletion: {len(rows_before)}")


        # Update null column values
        update_query = "UPDATE buy_prepar SET times_posted = 1 WHERE times_posted IS NULL;"
        cursor.execute(update_query)
        conn.commit()

        # Delete rows where column value is greater than or equal to the threshold
        delete_query = "DELETE FROM buy_prepar WHERE times_posted >= %s;"
        cursor.execute(delete_query, (threshold,))
        conn.commit()

        # Print cycle_band values and count rows after deletion
        output_text.insert(tk.END, "\nRows after deletion: ")
        cursor.execute("SELECT times_posted FROM buy_prepar;")
        rows_after = cursor.fetchall()
        output_text.insert(tk.END, f"Total rows after deletion: {len(rows_after)}\n")
        for row in rows_after:
            output_text.insert(tk.END, f"\nCycle band: {row[0]}")

        output_text.insert(tk.END, f"\nCycle limit is {threshold}.\n\n")
        output_text.yview_pickplace("end")

    except psycopg2.DatabaseError as e:
        output_text.insert(tk.END, f"Database error: {e}\n")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def update_band_times_posted(timer_ban_after_sell, output_text):
    # Fetch database password from environment variable
    password = os.getenv('DATABASE_PASSWORD')
    if not password:
        output_text.insert(tk.END, "DATABASE_PASSWORD environment variable not set\n")
        return

    # Database connection parameters
    dbname = "trading"
    user = "postgres"
    host = "localhost"
    port = "5432"

    try:
        # Attempt to convert the threshold value from the input to an integer
        threshold_sell = int(timer_ban_after_sell.get().strip())
    except ValueError:
        # Insert error message into the output_text widget if conversion fails
        output_text.insert(tk.END, "Invalid threshold value in timer_ban_after_sell.\n")
        return

    # Initialize database connection and cursor variables
    conn = None
    cursor = None

    try:
        # Establish a connection to the database
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = conn.cursor()

        # Print cycle_band values and count rows before deletion
        output_text.insert(tk.END, "\nRows before deletion: ")
        cursor.execute("SELECT cycle_band FROM sell_temp_band;")
        rows_before = cursor.fetchall()
        output_text.insert(tk.END, f"Total rows before deletion: {len(rows_before)}")

        # Increment cycle_band values by 1
        increment_query = "UPDATE sell_temp_band SET cycle_band = cycle_band + 1;"
        cursor.execute(increment_query)
        conn.commit()

        # Update rows where 'cycle_band' is NULL
        update_query = "UPDATE sell_temp_band SET cycle_band = 1 WHERE cycle_band IS NULL;"
        cursor.execute(update_query)
        conn.commit()

        # Delete rows where 'cycle_band' is greater than or equal to the threshold
        delete_query = "DELETE FROM sell_temp_band WHERE cycle_band >= %s;"
        cursor.execute(delete_query, (threshold_sell,))
        conn.commit()

        # Print cycle_band values and count rows after deletion
        output_text.insert(tk.END, "\nRows after deletion:")
        cursor.execute("SELECT cycle_band FROM sell_temp_band;")
        rows_after = cursor.fetchall()
        output_text.insert(tk.END, f" Total rows after deletion: {len(rows_after)}\n")
        for row in rows_after:
            output_text.insert(tk.END, f"\nCycle band: {row[0]}\n")

        output_text.insert(tk.END, f"Cycle limit is {threshold_sell}.\n\n")
        output_text.yview_pickplace("end")

    except psycopg2.DatabaseError as e:
        output_text.insert(tk.END, f"Database error: {e}\n")
    finally:
        # Ensure resources are closed properly
        if cursor:
            cursor.close()
        if conn:
            conn.close()