from sell_logic_delete_handling import update_prepar_times_posted, update_band_times_posted
from pre_ma_volume_top_gainers import fetch_and_update_coin_metrics
from sell_get_data_actual_sell import sell_actual_oco_transaction
from pre_delete_unwanted_coin import fetch_and_print_top_gainers
from buy_all_position_holding import insert_positions_into_db
from buy_handling_timer import get_all_open_orders_with_usdt
from tkinter import scrolledtext, Entry, messagebox, Button
from pre_buy_add_on_rsi import fetch_and_update_coin_rsi
from sell_recheck_position import recheck_port_positions
from sell_from_prepar_to_tpsl import update_sell_table
from buy_actual_placing_order import price_buy_placer
from pre_save_top_gainer import get_top_gainers_usdt
from pre_cal_vol_price_ma_pushbuy import fetch_data
from buy_tp_sl_calculations import calculate_tp_sl
from buy_check_24hrs_high import check_24hrs_range
from pre_blacklist_coins import fetch_blacklist
import tkinter as tk
import requests
import sys
import os
import psycopg2
from psycopg2 import Error
import time
from main_input_text_number_limit import (
    validate_entry_buy_timer,
    validate_timer_ban_after_sell,
    validate_ma25_period,
    validate_ma50_period,
    validate_highest_price_period,
    validate_gain_level,
    validate_sl_loss_level,
    validate_avg_volume_period,
    validate_volume_threshold_millions,
    validate_tp_gain_level,
    print_buy_assets_table,
    reset_process,
    update_button_state,
    validate_ma15_period,
    print_dots
)


loop_button = None
start_button = None
blacklist_button2 = None
check_button = None
reset_button = None
stop_button = None
is_looping = False
max_buy_usdt_size = print_buy_assets_table()

def validate_buy_usdt_size(value):
    if value == "":  # Allow empty input
        return True
    if value.isdigit() and 1 <= int(value) <= max_buy_usdt_size:
        return True
    return False

def start_process():
    output_text.delete(1.0, tk.END)
    # Check if all required fields are filled
    if any(not entry.get().strip() for entry in [
        entry_ma_size, entry_ma_25, entry_ma_50, entry_avg_volume_period,
        entry_volume_threshold, entry_gain_level, entry_highest_price_period,
        tp_gain_level, sl_loss_level, entry_ma_15, entry_buy_timer, timer_ban_after_sell]):
        messagebox.showerror("Input Error", "Error: All fields must be filled out.")
        return

    try:
        volume_threshold_millions = int(entry_volume_threshold.get().strip())
        gain_level = int(entry_gain_level.get().strip())
        highest_price_period = entry_highest_price_period.get().strip()       
        
        get_top_gainers_usdt(output_text, volume_threshold_millions, gain_level)
        root.after(5000, continue_process)
        root.after(11000, lambda: fetch_and_update_coin_rsi(output_text, rsi_period=14))
        root.after(22000, lambda: fetch_data(output_text, highest_price_period))
        root.after(27500, lambda: check_24hrs_range(output_text))
        root.after(35000, lambda: calculate_tp_sl(output_text, tp_gain_level, sl_loss_level))
        root.after(45000, lambda: insert_positions_into_db(output_text))
        root.after(55000, lambda: price_buy_placer(output_text, entry_ma_size))
        root.after(56000, lambda: get_all_open_orders_with_usdt(entry_buy_timer, output_text))
        root.after(66000, lambda: recheck_port_positions(output_text))
        root.after(76000, lambda: update_sell_table(output_text))
        root.after(77000, lambda: sell_actual_oco_transaction(output_text))
        root.after(81000, lambda: update_prepar_times_posted(entry_buy_timer, output_text))
        root.after(86000, lambda: fetch_data(output_text, highest_price_period))
        root.after(89000, lambda: (update_band_times_posted(timer_ban_after_sell, output_text), print_dots(44, 6000, output_text)))
    except ValueError as e:
        output_text.insert(tk.END, f"Value Error: {e}\n")
    except Exception as e:
        output_text.insert(tk.END, f"An unexpected error occurred: {e}\n")
    
    # Schedule next execution if looping
    if is_looping:
        root.after(360000, start_process)  # Loop after 60 seconds

def continue_process():
    # Retrieve the MA periods from the entry fields with default values
    ma_25_days = int(entry_ma_25.get()) if entry_ma_25.get().strip().isdigit() else 25
    ma_50_days = int(entry_ma_50.get()) if entry_ma_50.get().strip().isdigit() else 50
    ma_15_days = int(entry_ma_15.get()) if entry_ma_15.get().strip().isdigit() else 15  # New entry for MA_15
    highest_price_period = int(entry_highest_price_period.get()) if entry_highest_price_period.get().strip().isdigit() else 60
    avg_volume_period = int(entry_avg_volume_period.get()) if entry_avg_volume_period.get().strip().isdigit() else 30   
    # Fetch and update coin metrics including the MA_15
    fetch_and_update_coin_metrics(output_text, ma_25_days, ma_50_days, ma_15_days, highest_price_period, avg_volume_period)

def start_loop():
    """Start the loop by setting the global flag and calling start_process."""
    global is_looping
    is_looping = True
    update_button_state('disabled', [loop_button, start_button, blacklist_button2, check_button, reset_button, stop_button])
    start_process()

def stop_loop():
    """Stop the loop by clearing the global flag."""
    global is_looping
    is_looping = False
    update_button_state('normal', [loop_button, start_button, blacklist_button2, check_button, reset_button, stop_button])

location = 'C:/Users/joanm/Desktop/Noly/trading/icon.ico'
root = tk.Tk()
root.title("Crypto Trading Bot Binance")
root.iconbitmap(location)

output_text = scrolledtext.ScrolledText(root, width=155, height=31, wrap=tk.WORD)
output_text.grid(row=0, column=0, columnspan=6, padx=5, pady=3)

label_ma_50 = tk.Label(root, text="(30 to 99 days) Slow MA:") # Entry widget for MA above 50 days
label_ma_50.grid(row=1, column=0, padx=2, pady=2, sticky=tk.E)
entry_ma_50 = Entry(root)
entry_ma_50.insert(tk.END, "99")
entry_ma_50.grid(row=1, column=1, padx=2, pady=2, sticky=tk.W)

label_ma_25 = tk.Label(root, text="(1 to 50 days) Mid MA:") # Entry widget for MA below 50 days
label_ma_25.grid(row=2, column=0, padx=2, pady=2, sticky=tk.E)
entry_ma_25 = Entry(root)
entry_ma_25.insert(tk.END, "45")
entry_ma_25.grid(row=2, column=1, padx=2, pady=2, sticky=tk.W)

label_ma_15 = tk.Label(root, text="(1 to 35 days) Fast MA:")
label_ma_15.grid(row=3, column=0, padx=2, pady=2, sticky=tk.E)
entry_ma_15 = Entry(root)
entry_ma_15.insert(tk.END, "15")
entry_ma_15.grid(row=3, column=1, padx=2, pady=2, sticky=tk.W)

label_avg_volume_period = tk.Label(root, text="(1 to 90 days) Avg Vol:") # Entry widget for average volume period
label_avg_volume_period.grid(row=4, column=0, padx=2, pady=2, sticky=tk.E)
entry_avg_volume_period = Entry(root)
entry_avg_volume_period.insert(tk.END, "30")
entry_avg_volume_period.grid(row=4, column=1, padx=2, pady=2, sticky=tk.W)

label_volume_threshold = tk.Label(root, text="Vol in Millions (24hrs):") # Entry widget for volume threshold
label_volume_threshold.grid(row=1, column=2, padx=2, pady=2, sticky=tk.E)
entry_volume_threshold = Entry(root)
entry_volume_threshold.insert(tk.END, "26")
entry_volume_threshold.grid(row=1, column=3, padx=2, pady=2, sticky=tk.W)

label_gain_level = tk.Label(root, text="Gain in % (24hrs):") # Entry widget for gain level
label_gain_level.grid(row=2, column=2, padx=2, pady=2, sticky=tk.E)
entry_gain_level = Entry(root)
entry_gain_level.insert(tk.END, "26")
entry_gain_level.grid(row=2, column=3, padx=2, pady=2, sticky=tk.W)

take_profit_level = tk.Label(root, text="Take Profit %:")
take_profit_level.grid(row=3, column=2, padx=2, pady=2, sticky=tk.E)
tp_gain_level = Entry(root)
tp_gain_level.insert(tk.END, "17")
tp_gain_level.grid(row=3, column=3, padx=2, pady=2, sticky=tk.W)

cut_loss_level = tk.Label(root, text="Cut Loss % :")
cut_loss_level.grid(row=4, column=2, padx=2, pady=2, sticky=tk.E)
sl_loss_level = Entry(root)
sl_loss_level.insert(tk.END, "10")
sl_loss_level.grid(row=4, column=3, padx=2, pady=2, sticky=tk.W)

buy_usdt_size = tk.Label(root, text="Allocation per buy USDT:")
buy_usdt_size.grid(row=1, column=4, padx=2, pady=2, sticky=tk.E)
entry_ma_size = Entry(root)
entry_ma_size.insert(tk.END, f"{max_buy_usdt_size}")
entry_ma_size.grid(row=1, column=5, padx=2, pady=2, sticky=tk.W)

buy_timer = tk.Label(root, text="after buy ban 6mins X")
buy_timer.grid(row=2, column=4, padx=2, pady=2, sticky=tk.E)
entry_buy_timer = Entry(root)
entry_buy_timer.insert(tk.END, "10")
entry_buy_timer.grid(row=2, column=5, padx=2, pady=2, sticky=tk.W)

ban_on_after_sell = tk.Label(root, text="After sell ban 6mins X")
ban_on_after_sell.grid(row=3, column=4, padx=2, pady=2, sticky=tk.E)
timer_ban_after_sell = Entry(root)
timer_ban_after_sell.insert(tk.END, "120")
timer_ban_after_sell.grid(row=3, column=5, padx=2, pady=2, sticky=tk.W)

label_highest_price_period = tk.Label(root, text="(1 to 110 days)Highest Price:")
label_highest_price_period.grid(row=4, column=4, padx=2, pady=2, sticky=tk.E)
entry_highest_price_period = Entry(root)
entry_highest_price_period.insert(tk.END, "100")
entry_highest_price_period.grid(row=4, column=5, padx=2, pady=2, sticky=tk.W)

# Register validation functions with tkinter
validate_ma25_period_cmd = root.register(validate_ma25_period)
validate_ma50_period_cmd = root.register(validate_ma50_period)
validate_highest_price_period_cmd = root.register(validate_highest_price_period)
validate_avg_volume_period_cmd = root.register(validate_avg_volume_period)
validate_volume_threshold_millions_cmd = root.register(validate_volume_threshold_millions)
validate_gain_level_cmd = root.register(validate_gain_level)
validate_tp_gain_level_cmd = root.register(validate_tp_gain_level)
validate_sl_loss_level_cmd = root.register(validate_sl_loss_level)
validate_buy_usdt_size_cmd = root.register(validate_buy_usdt_size)
validate_timer_ban_after_sell_cmd = root.register(validate_timer_ban_after_sell)
validate_entry_buy_timer_cmd = root.register(validate_entry_buy_timer)
validate_ma15_cmd = root.register(validate_ma15_period)


# Configure entry widgets to use validation commands
entry_ma_25.config(validate="key", validatecommand=(validate_ma25_period_cmd, "%P"))
entry_ma_50.config(validate="key", validatecommand=(validate_ma50_period_cmd, "%P"))
entry_highest_price_period.config(validate="key", validatecommand=(validate_highest_price_period_cmd, "%P"))
entry_avg_volume_period.config(validate="key", validatecommand=(validate_avg_volume_period_cmd, "%P"))
entry_volume_threshold.config(validate="key", validatecommand=(validate_volume_threshold_millions_cmd, "%P"))
entry_gain_level.config(validate="key", validatecommand=(validate_gain_level_cmd, "%P"))
tp_gain_level.config(validate="key", validatecommand=(validate_tp_gain_level_cmd, "%P"))
sl_loss_level.config(validate="key", validatecommand=(validate_sl_loss_level_cmd, "%P"))
entry_ma_size.config(validate="key", validatecommand=(validate_buy_usdt_size_cmd, "%P"))
timer_ban_after_sell.config(validate="key", validatecommand=(validate_timer_ban_after_sell_cmd, "%P"))
entry_buy_timer.config(validate="key", validatecommand=(validate_entry_buy_timer_cmd, "%P"))
entry_ma_15.config(validate="key", validatecommand=(validate_ma15_cmd, '%P'))


loop_button = tk.Button(root, text="Loop Trading", command=start_loop, width=12)
loop_button.grid(row=5, column=0, padx=8, pady=(5,6), sticky=tk.W)

start_button = tk.Button(root, text="Single Run Test", command=start_process, width=12)
start_button.grid(row=5, column=1, padx=8, pady=(5,6), sticky=tk.W)

blacklist_button2 = tk.Button(root, text="Blacklisted", command=lambda: fetch_blacklist(root), width=12)
blacklist_button2.grid(row=5, column=2, padx=8, pady=(5,6), sticky=tk.W)

check_button = tk.Button(root, text="Watch List", command=lambda: fetch_and_print_top_gainers(root), width=12)
check_button.grid(row=5, column=3, padx=8, pady=(5,6), sticky=tk.W)

reset_button = tk.Button(root, text="Reset", command=lambda: reset_process(root, output_text, insert_positions_into_db), width=12)
reset_button.grid(row=5, column=4, padx=8, pady=(5,6), sticky=tk.W)

stop_button = tk.Button(root, text="Stop Loop", command=stop_loop, width=12)
stop_button.grid(row=5, column=5, padx=8, pady=(5,6), sticky=tk.W)

root.mainloop()
