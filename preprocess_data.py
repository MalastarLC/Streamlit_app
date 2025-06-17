# Current issue with the app :

"""
The Real Problem: Application Timeout on Interaction
Here is the new, correct sequence of events:
Fast Startup: The app starts, calls load_available_client_ids(), reads the small 26MB application_test.csv, populates the sidebar, and becomes "healthy". This is fast, so the health check passes.
User Interaction: You select a client ID from the sidebar.
Massive Data Load: This triggers the get_data_for_client() function. This function then tries to load all the other large CSV files (totaling over 2 GB) into the container's memory to find the few rows related to your selected client.
Request Timeout: This massive I/O and filtering operation on a 1vCPU/2GB container takes a very long time—much longer than the standard web request timeout (typically 30-60 seconds) that App Runner's load balancer allows.
Connection Closed: Before your function can finish processing all that data and return a result, the load balancer gives up on the waiting connection from your browser and closes it. This results in the blank/error screen you see.

The issue is not a startup failure, but an application logic timeout. The app is too slow to respond to user actions because it's designed to read the entire dataset for every single request.
The Solution: Pre-process Your Data for Efficient Lookups
The only robust, scalable, and correct solution is to stop reading gigabytes of data on the fly. We need to convert the data into a format that allows us to read only the specific rows we need for a single client.
The perfect format for this is Partitioned Parquet.
Parquet is a highly efficient, columnar data format.
Partitioning means we will structure the data on S3 into folders based on a key, like SK_ID_CURR.
When you ask for data for client_id = 100002, pandas will be smart enough to go directly to the SK_ID_CURR=100002 folder and read only the tiny file inside, instead of scanning a 700MB CSV. This will be nearly instantaneous.
"""

# En gros on va faire du partitionning pour que quand on sélectionne un id on ne "scan" pas l'entiereté de chaque dataset pour ce qui nous intéresse pour que pandas sache directement ou regarder 
# et permet à notre appli d'être beaucoup plus efficace et on va surement pouvoir passer les health checks avec ça 

# Basically partionning is like aggregating every client data in their own parition/folder and then when we select client 100003 pandas just has to go to the folder 100003 which contains all the information related to this SK_ID_CURR
# And  instead of loading entire dsatsets it loads bits of the datatset and it stops as soon as it has what it needs

"""
Réponse gemini :

Superpower #1: Partitioning (Finding the Right Folder)
This is what we just discussed. Instead of searching a single giant drawer (the huge CSV file), we go directly to the labeled folder for client 100003.
Result: We have already ignored 99.9% of the rows in the original dataset. We are now only concerned with the tiny file(s) inside that specific folder.
Superpower #2: Columnar Storage (Reading only the needed "bits")
This is where your new question comes in. Now that we're inside the correct folder for client 100003, what do we do with the little Parquet file inside?
A CSV file is like a traditional document. It's stored row by row. To get the "Amount" and "Status" for a transaction, you have to read the entire row: "SK_ID_CURR, Date, Amount, Status, Other_Column_1, Other_Column_2...". You can't just pick out the two words you need; you have to process the whole line.
A Parquet file is completely different. It's stored column by column. Imagine the file for client 100003 is like a special spreadsheet where all the AMT_PAYMENT values are physically stored together, all the DAYS_INSTALMENT values are stored together, and so on.
Now, when your code runs, it's even smarter than just loading the whole small file.
Your Code:
The preprocess_data.py script I provided is designed to only keep a subset of columns needed for the model:
cols_to_read = ['SK_ID_CURR', 'SK_ID_PREV', 'AMT_ANNUITY', 'NAME_CONTRACT_STATUS']
What Happens:
When pandas reads the Parquet file for client 100003, it says:
"I've found the right folder for client 100003."
"Now, from the file(s) inside, I don't need everything. The user's code only needs the data from the SK_ID_CURR, SK_ID_PREV, AMT_ANNUITY, and NAME_CONTRACT_STATUS columns."
"So, I will only read the physical "bits" on the disk (S3) that correspond to these four columns. I will completely ignore the data for all the other columns that might be in the file."

"""

import pandas as pd
import os
import traceback
import pyarrow.parquet as pq
import pyarrow as pa

# This is the definitive pre-processing script.

# --- Configuration ---
SOURCE_DATA_DIR = 'data_sample'
OUTPUT_PARQUET_DIR = 'data_parquet'

# --- Column and Partition Key definitions (Unchanged) ---
REQUIRED_COLUMNS = {
    'application_test.csv': None,
    'bureau.csv': ['SK_ID_CURR', 'SK_ID_BUREAU', 'CREDIT_ACTIVE', 'CREDIT_CURRENCY', 'DAYS_CREDIT', 'CREDIT_DAY_OVERDUE', 'DAYS_CREDIT_ENDDATE', 'DAYS_ENDDATE_FACT', 'AMT_CREDIT_MAX_OVERDUE', 'CNT_CREDIT_PROLONG', 'AMT_CREDIT_SUM', 'AMT_CREDIT_SUM_DEBT', 'AMT_CREDIT_SUM_LIMIT', 'AMT_CREDIT_SUM_OVERDUE', 'CREDIT_TYPE', 'DAYS_CREDIT_UPDATE', 'AMT_ANNUITY'],
    'bureau_balance.csv': ['SK_ID_BUREAU', 'MONTHS_BALANCE', 'STATUS'],
    'POS_CASH_balance.csv': ['SK_ID_PREV', 'SK_ID_CURR', 'MONTHS_BALANCE', 'CNT_INSTALMENT', 'CNT_INSTALMENT_FUTURE', 'NAME_CONTRACT_STATUS', 'SK_DPD', 'SK_DPD_DEF'],
    'installments_payments.csv': ['SK_ID_PREV', 'SK_ID_CURR', 'NUM_INSTALMENT_VERSION', 'NUM_INSTALMENT_NUMBER', 'DAYS_INSTALMENT', 'DAYS_ENTRY_PAYMENT', 'AMT_INSTALMENT', 'AMT_PAYMENT'],
    'previous_application.csv': ['SK_ID_PREV', 'SK_ID_CURR', 'NAME_CONTRACT_TYPE', 'AMT_ANNUITY', 'AMT_APPLICATION', 'AMT_CREDIT', 'AMT_DOWN_PAYMENT', 'AMT_GOODS_PRICE', 'WEEKDAY_APPR_PROCESS_START', 'HOUR_APPR_PROCESS_START', 'FLAG_LAST_APPL_PER_CONTRACT', 'NFLAG_LAST_APPL_IN_DAY', 'RATE_DOWN_PAYMENT', 'RATE_INTEREST_PRIMARY', 'RATE_INTEREST_PRIVILEGED', 'NAME_CASH_LOAN_PURPOSE', 'NAME_CONTRACT_STATUS', 'DAYS_DECISION', 'NAME_PAYMENT_TYPE', 'CODE_REJECT_REASON', 'NAME_TYPE_SUITE', 'NAME_CLIENT_TYPE', 'NAME_GOODS_CATEGORY', 'NAME_PORTFOLIO', 'NAME_PRODUCT_TYPE', 'CHANNEL_TYPE', 'SELLERPLACE_AREA', 'NAME_SELLER_INDUSTRY', 'CNT_PAYMENT', 'NAME_YIELD_GROUP', 'PRODUCT_COMBINATION', 'DAYS_FIRST_DRAWING', 'DAYS_FIRST_DUE', 'DAYS_LAST_DUE_1ST_VERSION', 'DAYS_LAST_DUE', 'DAYS_TERMINATION', 'NFLAG_INSURED_ON_APPROVAL'],
    'credit_card_balance.csv': ['SK_ID_PREV', 'SK_ID_CURR', 'MONTHS_BALANCE', 'AMT_BALANCE', 'AMT_CREDIT_LIMIT_ACTUAL', 'AMT_DRAWINGS_ATM_CURRENT', 'AMT_DRAWINGS_CURRENT', 'AMT_DRAWINGS_OTHER_CURRENT', 'AMT_DRAWINGS_POS_CURRENT', 'AMT_INST_MIN_REGULARITY', 'AMT_PAYMENT_CURRENT', 'AMT_PAYMENT_TOTAL_CURRENT', 'AMT_RECEIVABLE_PRINCIPAL', 'AMT_RECIVABLE', 'AMT_TOTAL_RECEIVABLE', 'CNT_DRAWINGS_ATM_CURRENT', 'CNT_DRAWINGS_CURRENT', 'CNT_DRAWINGS_OTHER_CURRENT', 'CNT_DRAWINGS_POS_CURRENT', 'CNT_INSTALMENT_MATURE_CUM', 'NAME_CONTRACT_STATUS', 'SK_DPD', 'SK_DPD_DEF']
}
PARTITION_KEYS = {
    'application_test.csv': None,
    'bureau.csv': 'SK_ID_CURR',
    'bureau_balance.csv': 'SK_ID_BUREAU',
    'previous_application.csv': 'SK_ID_CURR',
    'POS_CASH_balance.csv': 'SK_ID_CURR',
    'installments_payments.csv': 'SK_ID_CURR',
    'credit_card_balance.csv': 'SK_ID_CURR'
}

def create_parquet_files():
    """
    Reads large CSVs in chunks and writes them to partitioned Parquet format,
    providing progress updates and handling high partition counts.
    """
    if not os.path.exists(OUTPUT_PARQUET_DIR):
        os.makedirs(OUTPUT_PARQUET_DIR)
        print(f"Created output directory: {OUTPUT_PARQUET_DIR}")

    chunk_size = 500000
    # A generous limit high enough for our largest file (~31k partitions)
    partition_limit = 40000 

    for filename, cols_to_read in REQUIRED_COLUMNS.items():
        try:
            source_path = os.path.join(SOURCE_DATA_DIR, filename)
            partition_key = PARTITION_KEYS.get(filename)
            output_path = os.path.join(OUTPUT_PARQUET_DIR, filename.replace('.csv', '.parquet'))
            
            print(f"\n--- Processing {filename} ---")

            if partition_key:
                print(f"Reading {filename} in chunks of {chunk_size} rows...")
                
                csv_reader = pd.read_csv(source_path, usecols=cols_to_read, chunksize=chunk_size, low_memory=False)
                
                for i, chunk_df in enumerate(csv_reader):
                    print(f"  -> Processing chunk {i+1}...")
                    
                    table = pa.Table.from_pandas(chunk_df, preserve_index=False)
                    
                    # --- THIS IS THE KEY COMBINED SOLUTION ---
                    pq.write_to_dataset(
                        table,
                        root_path=output_path,
                        partition_cols=[partition_key],
                        max_partitions=partition_limit, # Add the limit override back in
                        use_legacy_dataset=False # Use the modern, more robust dataset writer
                    )
                    # --- END OF SOLUTION ---

                print(f"Finished processing all chunks for {filename}.")
            else:
                print(f"Reading full file for {filename}...")
                df = pd.read_csv(source_path, usecols=cols_to_read)
                df.to_parquet(output_path, engine='pyarrow', index=False)
                print(f"Successfully created single parquet file for {filename}")

        except Exception as e:
            print(f"  -> ERROR processing {filename}: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    print("--- Starting Data Pre-processing to Parquet (Final Chunked Version) ---")
    create_parquet_files()
    print("\n--- Pre-processing Complete ---")