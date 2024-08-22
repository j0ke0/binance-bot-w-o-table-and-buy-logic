from tkinter.ttk import Treeview
import tkinter as tk
from tkinter import messagebox
import psycopg2
import os

def fetch_and_print_top_gainers(root):
    """Fetches top gainers from PostgreSQL and displays them in a new window using Treeview."""
    # Create a new Toplevel window
    sub_root = tk.Toplevel(root)
    sub_root.title("Top Gainers Data")
    sub_root.iconbitmap('C:/Users/joanm/Desktop/Noly/trading/icon.ico')
    sub_root.grab_set()

    # Create a Treeview widget
    tree = Treeview(sub_root, columns=("Coin", "Days 60 High", "Vol Ave 60 days"), show='headings')
    tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Define columns and headings
    tree.heading("Coin", text="Coin")
    tree.heading("Days 60 High", text="Days 60 High")
    tree.heading("Vol Ave 60 days", text="Vol Ave 60 days")
    
    # Configure column widths and alignment
    tree.column("Coin", width=200, anchor=tk.CENTER)
    tree.column("Days 60 High", width=150, anchor=tk.CENTER)
    tree.column("Vol Ave 60 days", width=150, anchor=tk.CENTER)

    # Add buttons to the window
    button_frame = tk.Frame(sub_root)
    button_frame.pack(pady=10)

    # Delete Button
    def delete_selected_rows():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "No rows selected for deletion.")
            return
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected rows?"):
            for item in selected_items:
                # Get the coin name from the selected row
                coin_name = tree.item(item, 'values')[0]
                try:
                    # Connect to PostgreSQL database
                    with psycopg2.connect(
                        user="postgres",
                        password=os.getenv('DATABASE_PASSWORD'),
                        host="localhost",
                        port="5432",
                        database="trading"
                    ) as connection:
                        with connection.cursor() as cursor:
                            # Execute SQL query to delete the record
                            cursor.execute("""
                                DELETE FROM top_gainers
                                WHERE coin = %s;
                            """, (coin_name,))
                            connection.commit()
                            
                    # Delete the row from the Treeview
                    tree.delete(item)
                except psycopg2.Error as error:
                    messagebox.showerror("Database Error", f"Error while deleting data from PostgreSQL: {error}")

    delete_button = tk.Button(button_frame, text="Delete", command=delete_selected_rows, width=12)
    delete_button.pack(side=tk.LEFT, padx=15)

    # Close Button
    close_button = tk.Button(button_frame, text="Close", command=sub_root.destroy, width=12)
    close_button.pack(side=tk.LEFT, padx=15)

    try:
        # Connect to PostgreSQL database
        with psycopg2.connect(
            user="postgres",
            password=os.getenv('DATABASE_PASSWORD'),
            host="localhost",
            port="5432",
            database="trading"
        ) as connection:
            with connection.cursor() as cursor:
                # Execute SQL query
                cursor.execute("""
                    SELECT coin, days_60_high, volume_60_days
                    FROM top_gainers;
                """)

                # Fetch and insert data into Treeview
                rows = cursor.fetchall()
                for row in rows:
                    tree.insert("", tk.END, values=row)
    except psycopg2.Error as error:
        messagebox.showerror("Database Error", f"Error while fetching data from PostgreSQL: {error}")
