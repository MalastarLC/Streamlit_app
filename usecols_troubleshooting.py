import pandas as pd

try:
    df_check = pd.read_csv("data/installments_payments.csv", nrows=0)
    print("--- Headers from installments_payments.csv as seen by Pandas ---")
    print(df_check.columns.tolist())
    print("\n--- Your COLS_NEEDED list for installments_payments ---")
    # Copy your INSTALLMENTS_PAYMENTS_COLS_NEEDED list here
    INSTALLMENTS_PAYMENTS_COLS_NEEDED = [ 
        'AMT_INSTALMENT', 'AMT_PAYMENT', 'DAYS_ENTRY_PAYMENT', 'DAYS_INSTALMENT',
        'NUM_INSTALMENT_NUMBER', 'NUM_INSTALMENT_VERSION', 'SK_ID_CURR', 'SK_ID_PREV'
    ]
    print(INSTALLMENTS_PAYMENTS_COLS_NEEDED)

    # Check for differences
    missing_in_csv = [col for col in INSTALLMENTS_PAYMENTS_COLS_NEEDED if col not in df_check.columns]
    if missing_in_csv:
        print(f"\nERROR: Columns in COLS_NEEDED but NOT in CSV: {missing_in_csv}")
    
    extra_in_csv = [col for col in df_check.columns if col not in INSTALLMENTS_PAYMENTS_COLS_NEEDED]
    if extra_in_csv:
        print(f"\nINFO: Columns in CSV but NOT in COLS_NEEDED (this is usually fine): {extra_in_csv}")

except Exception as e:
    print(f"Error reading installments_payments.csv: {e}")