#Script to get the column needed for the streamlit app because we won't be reusing every single column and we'll try to trim down a little the input data to try and avoid memory issues

import pandas as pd

# --- Replace with the actual paths to your CSV files ---
path_to_data = "data/" # Or wherever your full CSVs are

try:
    print("--- application_test.csv ---")
    df_app_test = pd.read_csv(f"{path_to_data}application_test.csv", nrows=0) # nrows=0 reads only headers
    print(df_app_test.columns.tolist())
    print("\n")

    print("--- bureau.csv ---")
    df_bureau = pd.read_csv(f"{path_to_data}bureau.csv", nrows=0)
    print(df_bureau.columns.tolist())
    print("\n")

    print("--- bureau_balance.csv ---")
    df_bureau_balance = pd.read_csv(f"{path_to_data}bureau_balance.csv", nrows=0)
    print(df_bureau_balance.columns.tolist())
    print("\n")

    print("--- previous_application.csv ---")
    df_prev_app = pd.read_csv(f"{path_to_data}previous_application.csv", nrows=0)
    print(df_prev_app.columns.tolist())
    print("\n")

    print("--- POS_CASH_balance.csv ---")
    df_pos = pd.read_csv(f"{path_to_data}POS_CASH_balance.csv", nrows=0)
    print(df_pos.columns.tolist())
    print("\n")

    print("--- installments_payments.csv ---")
    df_install = pd.read_csv(f"{path_to_data}installments_payments.csv", nrows=0)
    print(df_install.columns.tolist())
    print("\n")

    print("--- credit_card_balance.csv ---")
    df_cc = pd.read_csv(f"{path_to_data}credit_card_balance.csv", nrows=0)
    print(df_cc.columns.tolist())
    print("\n")

except FileNotFoundError as e:
    print(f"ERROR: Could not find a CSV file. Please check paths. {e}")
except Exception as e:
    print(f"An error occurred: {e}")