# credit_dashboard_streamlit/utils.py

import streamlit as st # Still needed for @st.cache_data and st.error
import pandas as pd
import numpy as np
import requests
import os
# import json # Not directly used by these functions but by app.py for payload size

# --- CONFIGURATION & CONSTANTS (that these functions depend on) ---
# It's often better to pass these as arguments to the functions if they might change,
# or ensure app.py passes them if they are truly global settings.
# For now, to keep it simple, we can redefine them here or import from a config file.
# Let's assume DATA_PATH and API_URL are needed by these utils.
# The _COLS_NEEDED lists would also need to be accessible here.

# OPTION A: Redefine constants needed by utils.py within utils.py
# (This can lead to duplication if app.py also needs them for other things)
DATA_PATH = "data/" 
# API_URL is used by call_prediction_api - better to pass it as an argument from app.py

# The _COLS_NEEDED lists are heavily used by get_data_for_client
# It's best if get_data_for_client can access these.
# They could be defined here, or app.py could pass them as arguments.
# For simplicity of this example, let's assume they are defined here for now:
APPLICATION_TEST_COLS_NEEDED = [ ... ] # Copy from app.py
BUREAU_COLS_NEEDED = [ ... ]           # Copy from app.py
# ... and so on for all _COLS_NEEDED lists

# --- HELPER FUNCTION DEFINITIONS ---

@st.cache_data 
def load_available_client_ids(app_file_name: str = "application_test.csv") -> list:
    """
    Loads unique SK_ID_CURR values from the specified application CSV file.

    This function is cached by Streamlit, meaning it only executes the file
    reading and processing once for a given `app_file_name`, reusing the
    result on subsequent calls within the same session or if inputs don't change.
    It reads only the 'SK_ID_CURR' column to minimize memory usage.

    Args:
        app_file_name (str, optional): The name of the CSV file (e.g., 
            "application_test.csv" or "application_train.csv") located in the 
            `DATA_PATH` directory. Defaults to "application_test.csv".

    Returns:
        list: A sorted list of unique client IDs (SK_ID_CURR). Returns an
              empty list if the file is not found, is empty, the 'SK_ID_CURR'
              column is missing, or any other error occurs during loading.
    """
    # (Function code remains the same, but ensure DATA_PATH is accessible)
    try:
        file_path = os.path.join(DATA_PATH, app_file_name) # Uses DATA_PATH from this file
        # ... rest of the function
        df = pd.read_csv(file_path, usecols=['SK_ID_CURR'])
        client_ids = sorted(df['SK_ID_CURR'].unique().tolist())
        if not client_ids: 
            st.error(f"No client IDs found in '{file_path}'.") # st.error still works
            return [] 
        return client_ids
    except FileNotFoundError:
        st.error(f"Data file '{file_path}' not found.")
        return []
    except ValueError as ve: 
        st.error(f"Error reading '{file_path}': {ve}")
        return []
    except Exception as e: 
        st.error(f"Unexpected error loading client IDs: {e}")
        return []


def prepare_df_for_json(df_orig: pd.DataFrame) -> list:
    """
    Prepares a Pandas DataFrame for safe JSON serialization.

    This function handles common data cleaning tasks required before converting
    a DataFrame to a JSON-compatible format (list of dictionaries):
    1. Replaces string representations of NaN/Infinity (e.g., "NaN", "inf") 
       in object columns with `np.nan`.
    2. Replaces Python's `np.inf` and `-np.inf` in numeric columns with `np.nan`.
    3. Converts all `np.nan` values to Python's `None`, as `None` is serialized 
       to `null` in JSON, while `np.nan` is not directly JSON serializable.

    Args:
        df_orig (pd.DataFrame): The input DataFrame to prepare. Can be None or empty.

    Returns:
        list: A list of dictionaries, where each dictionary represents a row from
              the prepared DataFrame. Returns an empty list if `df_orig` is None
              or empty.
    """
    # (Function code remains the same)
    if df_orig is None or df_orig.empty:
        return [] 
    df = df_orig.copy() 
    for col in df.select_dtypes(include=['object']).columns:
        try:
            df[col] = df[col].astype(str).replace(
                ['inf', '-inf', 'Infinity', '-Infinity', 'NaN', 'nan', 'None', 'null', 'NA', '<NA>'],
                np.nan, regex=False 
            )
        except Exception: pass
    numeric_cols = df.select_dtypes(include=np.number).columns
    if not numeric_cols.empty: 
        df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
    return df.astype(object).where(pd.notnull(df), None).to_dict(orient='records')

@st.cache_data 
def get_data_for_client(client_id: int) -> tuple[dict | None, pd.DataFrame | None]:
    """
    Loads, filters, and prepares data from all 7 source CSV files for a single selected client.

    This function performs the crucial task of assembling the necessary raw data slices
    for the specified `client_id`. It uses predefined `_COLS_NEEDED` lists to load
    only the essential columns from each CSV, optimizing memory usage. The loaded
    and filtered data is then prepared into a dictionary format suitable for sending
    as a JSON payload to the prediction API.

    The function is cached by Streamlit, so for a given `client_id`, the expensive
    file I/O and filtering operations are performed only once per session or
    if the underlying data files were to change (which they don't in this context).

    Args:
        client_id (int): The `SK_ID_CURR` of the client for whom data needs to be fetched.

    Returns:
        tuple[dict | None, pd.DataFrame | None]: 
            - The first element is `api_payload` (dict): A dictionary where keys are
              the names of the 7 tables (e.g., "current_app", "bureau") and values
              are lists of records (dictionaries) representing the filtered data for
              that table, ready for JSON serialization. Returns `None` if a critical
              error occurs during data loading (e.g., a file is not found).
            - The second element is `client_main_descriptive_df` (pd.DataFrame):
              A DataFrame containing the raw row(s) for the `client_id` from the
              `application_test.csv` (or `application_train.csv`) file, used for
              displaying general descriptive information. Returns `None` if a
              critical error occurs.
    """
    # (Function code remains the same, but ensure DATA_PATH and _COLS_NEEDED lists are accessible)
    # This function now relies on the _COLS_NEEDED lists defined in this utils.py file
    data_frames_for_payload = {}
    client_main_descriptive_df = pd.DataFrame()
    try:
        # Example for current_app, repeat for others
        df_app_test_full = pd.read_csv(
            os.path.join(DATA_PATH, "application_test.csv"), 
            usecols=APPLICATION_TEST_COLS_NEEDED # Uses list from this file
        )
        # ... rest of get_data_for_client logic ...
        client_main_descriptive_df = df_app_test_full[df_app_test_full['SK_ID_CURR'] == client_id]
        if client_main_descriptive_df.empty: return None, None
        data_frames_for_payload["current_app"] = client_main_descriptive_df
        
        # ... (Full logic for all 7 DFs using _COLS_NEEDED from utils.py) ...

        api_payload = {}
        for df_name, df_content in data_frames_for_payload.items():
            api_payload[df_name] = prepare_df_for_json(df_content)
        return api_payload, client_main_descriptive_df

    except FileNotFoundError as e:
        st.error(f"Data file not found (utils.py): {e}.")
        return None, None 
    except ValueError as ve: 
        st.error(f"ValueError during data loading (utils.py): {ve}")
        return None, None
    except Exception as e: 
        st.error(f"Unexpected error in get_data_for_client (utils.py): {e}")
        import traceback; st.error(traceback.format_exc()) 
        return None, None

def call_prediction_api(payload_dict: dict, api_url_param: str) -> dict | None:
    """
    Sends the prepared data payload to the prediction API and returns the response.

    This function makes a POST request to the configured `API_URL` with the
    provided `payload_dict` (which should be a dictionary of table names to
    lists of records). It handles common HTTP request errors, connection issues,
    timeouts, and issues with JSON decoding of the API's response.

    Args:
        payload_dict (dict): The data payload to send to the API. This dictionary
                             is expected to be JSON serializable.

    Returns:
        dict | None: The parsed JSON response from the API if the request is
                      successful and the response is valid JSON. Returns `None`
                      if any error occurs during the API call (e.g., timeout,
                      connection error, HTTP error status, JSON decoding error).
    """
    # (Function code remains the same, but uses api_url_param)
    if not api_url_param: 
        st.error("API_URL parameter is missing or empty for call_prediction_api.")
        return None
    try:
        response = requests.post(api_url_param, json=payload_dict, timeout=300) 
        response.raise_for_status()
        return response.json()
    # ... (rest of error handling) ...
    except requests.exceptions.Timeout:
        st.error(f"API request to {api_url_param} timed out.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Failed to connect to API at {api_url_param}.")
        return None
    except requests.exceptions.HTTPError as http_err: 
        st.error(f"API HTTP error from {api_url_param}: {http_err.response.status_code} {http_err.response.reason}.")
        st.error(f"API Response (first 500 chars): {http_err.response.text[:500]}...")
        return None
    except requests.exceptions.RequestException as req_err: 
        st.error(f"API request error to {api_url_param}: {req_err}")
        return None
    except ValueError as json_err: 
        st.error(f"Error decoding JSON from {api_url_param}: {json_err}")
        st.error(f"Raw API response (first 200 chars): {response.text[:200]}...") 
        return None
