import pandas as pd
import os

# --- Configuration ---
SOURCE_DATA_DIR = 'data'
SAMPLE_OUTPUT_DIR = 'data_sample' # We'll create a new folder for our smaller files
SAMPLE_FRACTION = 0.10  # Use 10% of the clients

# --- Create the sample ---
print(f"--- Creating a {SAMPLE_FRACTION*100}% sample of the data ---")

# 1. Read the main application file
app_df = pd.read_csv(os.path.join(SOURCE_DATA_DIR, 'application_test.csv'))

# 2. Get a random sample of client IDs
sampled_app_df = app_df.sample(frac=SAMPLE_FRACTION, random_state=42) # random_state for reproducibility
sample_client_ids = set(sampled_app_df['SK_ID_CURR'])

print(f"Sampled {len(sample_client_ids)} client IDs.")

# 3. Create the new output directory
if not os.path.exists(SAMPLE_OUTPUT_DIR):
    os.makedirs(SAMPLE_OUTPUT_DIR)
    print(f"Created output directory: {SAMPLE_OUTPUT_DIR}")

# 4. Save the new, smaller application_test.csv
sampled_app_df.to_csv(os.path.join(SAMPLE_OUTPUT_DIR, 'application_test.csv'), index=False)
print("Saved sampled application_test.csv.")

# 5. Now, filter all other large CSVs based on these sampled IDs
files_to_filter = [
    'bureau.csv', 'previous_application.csv', 'POS_CASH_balance.csv',
    'installments_payments.csv', 'credit_card_balance.csv'
]

# Get all related SK_ID_BUREAU and SK_ID_PREV from the sampled clients
bureau_df = pd.read_csv(os.path.join(SOURCE_DATA_DIR, 'bureau.csv'))
prev_app_df = pd.read_csv(os.path.join(SOURCE_DATA_DIR, 'previous_application.csv'))

related_bureau_df = bureau_df[bureau_df['SK_ID_CURR'].isin(sample_client_ids)]
sample_bureau_ids = set(related_bureau_df['SK_ID_BUREAU'])
related_prev_app_df = prev_app_df[prev_app_df['SK_ID_CURR'].isin(sample_client_ids)]
sample_prev_ids = set(related_prev_app_df['SK_ID_PREV'])

# Save the sampled bureau.csv
related_bureau_df.to_csv(os.path.join(SAMPLE_OUTPUT_DIR, 'bureau.csv'), index=False)
print("Saved sampled bureau.csv.")

# Save the sampled previous_application.csv
related_prev_app_df.to_csv(os.path.join(SAMPLE_OUTPUT_DIR, 'previous_application.csv'), index=False)
print("Saved sampled previous_application.csv.")


# Filter and save the remaining files
for filename in files_to_filter[2:]: # We've already handled bureau and previous_app
    print(f"Filtering {filename}...")
    df = pd.read_csv(os.path.join(SOURCE_DATA_DIR, filename))
    # Keep rows if SK_ID_CURR is in our sample OR if SK_ID_PREV is in our sample
    sampled_df = df[
        df['SK_ID_CURR'].isin(sample_client_ids) |
        df['SK_ID_PREV'].isin(sample_prev_ids)
    ]
    sampled_df.to_csv(os.path.join(SAMPLE_OUTPUT_DIR, filename), index=False)
    print(f"Saved sampled {filename}.")

# Finally, filter bureau_balance.csv based on the bureau IDs we found
print("Filtering bureau_balance.csv...")
bureau_balance_df = pd.read_csv(os.path.join(SOURCE_DATA_DIR, 'bureau_balance.csv'))
sampled_bureau_balance_df = bureau_balance_df[bureau_balance_df['SK_ID_BUREAU'].isin(sample_bureau_ids)]
sampled_bureau_balance_df.to_csv(os.path.join(SAMPLE_OUTPUT_DIR, 'bureau_balance.csv'), index=False)
print("Saved sampled bureau_balance.csv.")

print("\n--- Sample creation complete! ---")
print(f"Your new, smaller dataset is in the '{SAMPLE_OUTPUT_DIR}' folder.")