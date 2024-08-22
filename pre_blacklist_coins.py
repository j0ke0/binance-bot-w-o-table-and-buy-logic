import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Treeview
import psycopg2
import os

location = 'C:/Users/joanm/Desktop/Noly/trading/icon.ico'

def validate_blacklist_period(value):
    """Validate the input value for the coin entry."""
    if value == "":  # Allow empty input
        return True
    if len(value) <= 6:  # Check if length is up to 6 characters
        return True
    return False

def fetch_blacklist(root):
    """Fetches coins and their timestamps from PostgreSQL and displays them in a new window using Treeview."""
    # Create a new Toplevel window
    sub_root = tk.Toplevel(root)
    sub_root.title("Blacklisted Coins")
    sub_root.iconbitmap(location)  # Make sure 'location' is defined somewhere
    sub_root.grab_set()

    # Create a Treeview widget
    tree = Treeview(sub_root, columns=("Coin", "Timestamp"), show='headings')
    tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Define columns and headings
    tree.heading("Coin", text="Coin")
    tree.heading("Timestamp", text="Timestamp")
    
    # Configure column widths and alignment
    tree.column("Coin", width=200, anchor=tk.CENTER)
    tree.column("Timestamp", width=200, anchor=tk.CENTER)

    # Add buttons and input field to the window
    button_frame = tk.Frame(sub_root)
    button_frame.pack(pady=10)

    # Register the validation function
    validate_command = sub_root.register(validate_blacklist_period)
    
    # Add Coin Entry
    tk.Label(button_frame, text="Add Coin:").pack(side=tk.LEFT, padx=5)
    coin_entry = tk.Entry(button_frame, validate="key", validatecommand=(validate_command, "%P"))
    coin_entry.pack(side=tk.LEFT, padx=5)

    # Function to add a new coin to the blacklist
    def add_coin():
        coin_name = coin_entry.get().strip().upper()  # Convert to uppercase
        if not coin_name:
            messagebox.showwarning("Input Error", "Coin name cannot be empty.")
            return
        
        coin_name_with_suffix = f"{coin_name}USDT"  # Append 'USDT'
        
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
                    # Check if the coin already exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 
                            FROM blacklist 
                            WHERE coin_name = %s
                        );
                    """, (coin_name_with_suffix,))
                    exists = cursor.fetchone()[0]
                    
                    if exists:
                        messagebox.showwarning("Input Error", "Coin already exists in the blacklist.")
                        return
                    
                    # Execute SQL query to insert the new record
                    cursor.execute("""
                        INSERT INTO blacklist (coin_name, timestamp)
                        VALUES (%s, NOW());
                    """, (coin_name_with_suffix,))
                    connection.commit()
                    
                    # Insert the new row into the Treeview
                    tree.insert("", tk.END, values=(coin_name_with_suffix, "N/A"))  # Assuming "N/A" for the timestamp initially
                    
            coin_entry.delete(0, tk.END)  # Clear the entry field
        except psycopg2.Error as error:
            messagebox.showerror("Database Error", f"Error while adding data to PostgreSQL: {error}")


    # Add Coin Button
    add_coin_button = tk.Button(button_frame, text="Add Coin", command=add_coin, width=12)
    add_coin_button.pack(side=tk.LEFT, padx=15)

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
                                DELETE FROM blacklist
                                WHERE coin_name = %s;
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
                # Execute SQL query to fetch coin and timestamp columns
                cursor.execute("""
                    SELECT coin_name, timestamp
                    FROM blacklist;
                """)

                # Fetch and insert data into Treeview
                rows = cursor.fetchall()
                for row in rows:
                    tree.insert("", tk.END, values=row)
    except psycopg2.Error as error:
        messagebox.showerror("Database Error", f"Error while fetching data from PostgreSQL: {error}")
