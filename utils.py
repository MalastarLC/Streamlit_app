# credit_dashboard_streamlit/utils.py

import streamlit as st # Still needed for @st.cache_data and st.error
import pandas as pd
import numpy as np
import requests
import os
import plotly.graph_objects as go
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
# For simplicity of this example, let's assume they are defined here for now
# ... and so on for all _COLS_NEEDED lists

APPLICATION_TEST_COLS_NEEDED = [
    'AMT_ANNUITY', 'AMT_CREDIT', 'AMT_GOODS_PRICE', 'AMT_INCOME_TOTAL', 
    'AMT_REQ_CREDIT_BUREAU_DAY', 'AMT_REQ_CREDIT_BUREAU_HOUR', 'AMT_REQ_CREDIT_BUREAU_MON',
    'AMT_REQ_CREDIT_BUREAU_QRT', 'AMT_REQ_CREDIT_BUREAU_WEEK', 'AMT_REQ_CREDIT_BUREAU_YEAR',
    'APARTMENTS_AVG', 'APARTMENTS_MEDI', 'APARTMENTS_MODE', 'BASEMENTAREA_AVG',
    'BASEMENTAREA_MEDI', 'BASEMENTAREA_MODE', 'CODE_GENDER', 'COMMONAREA_AVG',
    'COMMONAREA_MEDI', 'COMMONAREA_MODE', 'CNT_CHILDREN', 'CNT_FAM_MEMBERS',
    'DAYS_BIRTH', 'DAYS_EMPLOYED', 'DAYS_ID_PUBLISH', 'DAYS_LAST_PHONE_CHANGE',
    'DAYS_REGISTRATION', 'DEF_30_CNT_SOCIAL_CIRCLE', 'DEF_60_CNT_SOCIAL_CIRCLE',
    'ELEVATORS_AVG', 'ELEVATORS_MEDI', 'ELEVATORS_MODE', 'EMERGENCYSTATE_MODE',
    'ENTRANCES_AVG', 'ENTRANCES_MEDI', 'ENTRANCES_MODE', 'EXT_SOURCE_1',
    'EXT_SOURCE_2', 'EXT_SOURCE_3', 'FLAG_CONT_MOBILE', 'FLAG_DOCUMENT_10',
    'FLAG_DOCUMENT_11', 'FLAG_DOCUMENT_12', 'FLAG_DOCUMENT_13', 'FLAG_DOCUMENT_14',
    'FLAG_DOCUMENT_15', 'FLAG_DOCUMENT_16', 'FLAG_DOCUMENT_17', 'FLAG_DOCUMENT_18',
    'FLAG_DOCUMENT_19', 'FLAG_DOCUMENT_2', 'FLAG_DOCUMENT_20', 'FLAG_DOCUMENT_21',
    'FLAG_DOCUMENT_3', 'FLAG_DOCUMENT_4', 'FLAG_DOCUMENT_5', 'FLAG_DOCUMENT_6',
    'FLAG_DOCUMENT_7', 'FLAG_DOCUMENT_8', 'FLAG_DOCUMENT_9', 'FLAG_EMAIL',
    'FLAG_EMP_PHONE', 'FLAG_MOBIL', 'FLAG_OWN_CAR', 'FLAG_OWN_REALTY',
    'FLAG_PHONE', 'FLAG_WORK_PHONE', 'FLOORSMAX_AVG', 'FLOORSMAX_MEDI',
    'FLOORSMAX_MODE', 'FLOORSMIN_AVG', 'FLOORSMIN_MEDI', 'FLOORSMIN_MODE',
    'FONDKAPREMONT_MODE', 'HOUR_APPR_PROCESS_START', 'HOUSETYPE_MODE',
    'LANDAREA_AVG', 'LANDAREA_MEDI', 'LANDAREA_MODE', 'LIVE_CITY_NOT_WORK_CITY',
    'LIVE_REGION_NOT_WORK_REGION', 'LIVINGAPARTMENTS_AVG', 'LIVINGAPARTMENTS_MEDI',
    'LIVINGAPARTMENTS_MODE', 'LIVINGAREA_AVG', 'LIVINGAREA_MEDI', 'LIVINGAREA_MODE',
    'NAME_CONTRACT_TYPE', 'NAME_EDUCATION_TYPE', 'NAME_FAMILY_STATUS',
    'NAME_HOUSING_TYPE', 'NAME_INCOME_TYPE', 'NAME_TYPE_SUITE',
    'NONLIVINGAPARTMENTS_AVG', 'NONLIVINGAPARTMENTS_MEDI', 'NONLIVINGAPARTMENTS_MODE',
    'NONLIVINGAREA_AVG', 'NONLIVINGAREA_MEDI', 'NONLIVINGAREA_MODE',
    'OBS_30_CNT_SOCIAL_CIRCLE', 'OBS_60_CNT_SOCIAL_CIRCLE', 'OCCUPATION_TYPE',
    'ORGANIZATION_TYPE', 'OWN_CAR_AGE', 'REG_CITY_NOT_LIVE_CITY',
    'REG_CITY_NOT_WORK_CITY', 'REG_REGION_NOT_LIVE_REGION', 'REG_REGION_NOT_WORK_REGION',
    'REGION_POPULATION_RELATIVE', 'REGION_RATING_CLIENT', 'REGION_RATING_CLIENT_W_CITY',
    'SK_ID_CURR', 'TOTALAREA_MODE', 'WALLSMATERIAL_MODE', 'WEEKDAY_APPR_PROCESS_START',
    'YEARS_BEGINEXPLUATATION_AVG', 'YEARS_BEGINEXPLUATATION_MEDI',
    'YEARS_BEGINEXPLUATATION_MODE', 'YEARS_BUILD_AVG', 'YEARS_BUILD_MEDI',
    'YEARS_BUILD_MODE'
]

BUREAU_COLS_NEEDED = [
    'AMT_ANNUITY', 'AMT_CREDIT_MAX_OVERDUE', 'AMT_CREDIT_SUM', 
    'AMT_CREDIT_SUM_DEBT', 'AMT_CREDIT_SUM_LIMIT', 'AMT_CREDIT_SUM_OVERDUE',
    'CNT_CREDIT_PROLONG', 'CREDIT_ACTIVE', 'CREDIT_CURRENCY', 'CREDIT_DAY_OVERDUE',
    'CREDIT_TYPE', 'DAYS_CREDIT', 'DAYS_CREDIT_ENDDATE', 'DAYS_CREDIT_UPDATE',
    'DAYS_ENDDATE_FACT', 'SK_ID_BUREAU', 'SK_ID_CURR'
]

BUREAU_BALANCE_COLS_NEEDED = [
    'MONTHS_BALANCE', 'SK_ID_BUREAU', 'STATUS'
]

PREVIOUS_APPLICATION_COLS_NEEDED = [
    'AMT_ANNUITY', 'AMT_APPLICATION', 'AMT_CREDIT', 'AMT_DOWN_PAYMENT',
    'AMT_GOODS_PRICE', 'CHANNEL_TYPE', 'CNT_PAYMENT', 'CODE_REJECT_REASON',
    'DAYS_DECISION', 'DAYS_FIRST_DRAWING', 'DAYS_FIRST_DUE', 'DAYS_LAST_DUE',
    'DAYS_LAST_DUE_1ST_VERSION', 'DAYS_TERMINATION', 'FLAG_LAST_APPL_PER_CONTRACT',
    'HOUR_APPR_PROCESS_START', 'NAME_CASH_LOAN_PURPOSE', 'NAME_CLIENT_TYPE',
    'NAME_CONTRACT_STATUS', 'NAME_CONTRACT_TYPE', 'NAME_GOODS_CATEGORY',
    'NAME_PAYMENT_TYPE', 'NAME_PORTFOLIO', 'NAME_PRODUCT_TYPE',
    'NAME_SELLER_INDUSTRY', 'NAME_TYPE_SUITE', 'NAME_YIELD_GROUP',
    'NFLAG_INSURED_ON_APPROVAL', 'NFLAG_LAST_APPL_IN_DAY', 'PRODUCT_COMBINATION',
    'RATE_DOWN_PAYMENT', 'RATE_INTEREST_PRIMARY', 'RATE_INTEREST_PRIVILEGED',
    'SELLERPLACE_AREA', 'SK_ID_CURR', 'SK_ID_PREV', 'WEEKDAY_APPR_PROCESS_START'
]

POS_CASH_BALANCE_COLS_NEEDED = [
    'CNT_INSTALMENT', 'CNT_INSTALMENT_FUTURE', 'MONTHS_BALANCE',
    'NAME_CONTRACT_STATUS', 'SK_DPD', 'SK_DPD_DEF', 'SK_ID_CURR', 'SK_ID_PREV'
]

INSTALLMENTS_PAYMENTS_COLS_NEEDED = [ 
    'AMT_INSTALMENT', 'AMT_PAYMENT', 'DAYS_ENTRY_PAYMENT', 'DAYS_INSTALMENT',
    'NUM_INSTALMENT_NUMBER', 'NUM_INSTALMENT_VERSION', 'SK_ID_CURR', 'SK_ID_PREV'
]

CREDIT_CARD_BALANCE_COLS_NEEDED = [
    'AMT_BALANCE', 'AMT_CREDIT_LIMIT_ACTUAL', 'AMT_DRAWINGS_ATM_CURRENT',
    'AMT_DRAWINGS_CURRENT', 'AMT_DRAWINGS_OTHER_CURRENT', 'AMT_DRAWINGS_POS_CURRENT',
    'AMT_INST_MIN_REGULARITY', 'AMT_PAYMENT_CURRENT',
    'AMT_PAYMENT_TOTAL_CURRENT', 'AMT_RECEIVABLE_PRINCIPAL', 'AMT_RECIVABLE',
    'AMT_TOTAL_RECEIVABLE', 'CNT_DRAWINGS_ATM_CURRENT', 'CNT_DRAWINGS_CURRENT',
    'CNT_DRAWINGS_OTHER_CURRENT', 'CNT_DRAWINGS_POS_CURRENT',
    'CNT_INSTALMENT_MATURE_CUM', 'MONTHS_BALANCE', 'NAME_CONTRACT_STATUS', 
    'SK_DPD', 'SK_DPD_DEF', 'SK_ID_CURR', 'SK_ID_PREV'
]


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
    data_frames_for_payload_preparation = {} # Use a temporary dict to store raw filtered DFs
    client_main_descriptive_df = pd.DataFrame() # This will be current_app

    try:
        # --- 1. current_app (from application_test.csv) ---
        df_app_test_full = pd.read_csv(
            os.path.join(DATA_PATH, "application_test.csv"), 
            usecols=APPLICATION_TEST_COLS_NEEDED 
        )
        client_main_descriptive_df = df_app_test_full[df_app_test_full['SK_ID_CURR'] == client_id]
        if client_main_descriptive_df.empty:
            st.error(f"Client ID {client_id} not found in application_test.csv (or required columns are missing for this ID).")
            return None, None 
        data_frames_for_payload_preparation["current_app"] = client_main_descriptive_df # Store the raw DF

        # --- 2. bureau.csv ---
        df_bureau_full = pd.read_csv(
            os.path.join(DATA_PATH, "bureau.csv"), 
            usecols=BUREAU_COLS_NEEDED
        )
        client_bureau_df = df_bureau_full[df_bureau_full['SK_ID_CURR'] == client_id]
        data_frames_for_payload_preparation["bureau"] = client_bureau_df # Store the raw DF
        
        client_sk_id_bureau_list = []
        if not client_bureau_df.empty and 'SK_ID_BUREAU' in client_bureau_df.columns:
            client_sk_id_bureau_list = client_bureau_df['SK_ID_BUREAU'].unique().tolist()

        # --- 3. bureau_balance.csv ---
        if client_sk_id_bureau_list: 
            df_bureau_balance_full = pd.read_csv(
                os.path.join(DATA_PATH, "bureau_balance.csv"), 
                usecols=BUREAU_BALANCE_COLS_NEEDED
            )
            client_bureau_balance_df = df_bureau_balance_full[
                df_bureau_balance_full['SK_ID_BUREAU'].isin(client_sk_id_bureau_list)
            ]
            data_frames_for_payload_preparation["bureau_balance"] = client_bureau_balance_df # Store
        else:
            data_frames_for_payload_preparation["bureau_balance"] = pd.DataFrame(columns=BUREAU_BALANCE_COLS_NEEDED)

        # --- 4. previous_application.csv ---
        df_prev_app_full = pd.read_csv(
            os.path.join(DATA_PATH, "previous_application.csv"), 
            usecols=PREVIOUS_APPLICATION_COLS_NEEDED
        )
        client_prev_app_df = df_prev_app_full[df_prev_app_full['SK_ID_CURR'] == client_id]
        data_frames_for_payload_preparation["previous_application"] = client_prev_app_df # Store
        
        client_sk_id_prev_list = []
        if not client_prev_app_df.empty and 'SK_ID_PREV' in client_prev_app_df.columns:
            client_sk_id_prev_list = client_prev_app_df['SK_ID_PREV'].unique().tolist()

        # --- 5. POS_CASH_balance.csv ---
        df_pos_cash_full = pd.read_csv(
            os.path.join(DATA_PATH, "POS_CASH_balance.csv"), 
            usecols=POS_CASH_BALANCE_COLS_NEEDED
        )
        filter_pos_by_curr = df_pos_cash_full['SK_ID_CURR'] == client_id
        filter_pos_by_prev = pd.Series([False] * len(df_pos_cash_full)) 
        if client_sk_id_prev_list and 'SK_ID_PREV' in df_pos_cash_full.columns:
            filter_pos_by_prev = df_pos_cash_full['SK_ID_PREV'].isin(client_sk_id_prev_list)
        client_pos_cash_df = df_pos_cash_full[filter_pos_by_curr | filter_pos_by_prev]
        data_frames_for_payload_preparation["POS_CASH_balance"] = client_pos_cash_df # Store
        
        # --- 6. installments_payments.csv ---
        df_installments_full = pd.read_csv(
            os.path.join(DATA_PATH, "installments_payments.csv"), 
            usecols=INSTALLMENTS_PAYMENTS_COLS_NEEDED
        )
        filter_install_by_curr = df_installments_full['SK_ID_CURR'] == client_id
        filter_install_by_prev = pd.Series([False] * len(df_installments_full))
        if client_sk_id_prev_list and 'SK_ID_PREV' in df_installments_full.columns:
            filter_install_by_prev = df_installments_full['SK_ID_PREV'].isin(client_sk_id_prev_list)
        client_installments_df = df_installments_full[filter_install_by_curr | filter_install_by_prev]
        data_frames_for_payload_preparation["installments_payments"] = client_installments_df # Store

        # --- 7. credit_card_balance.csv ---
        df_credit_card_full = pd.read_csv(
            os.path.join(DATA_PATH, "credit_card_balance.csv"), 
            usecols=CREDIT_CARD_BALANCE_COLS_NEEDED
        )
        filter_cc_by_curr = df_credit_card_full['SK_ID_CURR'] == client_id
        filter_cc_by_prev = pd.Series([False] * len(df_credit_card_full))
        if client_sk_id_prev_list and 'SK_ID_PREV' in df_credit_card_full.columns:
            filter_cc_by_prev = df_credit_card_full['SK_ID_PREV'].isin(client_sk_id_prev_list)
        client_credit_card_df = df_credit_card_full[filter_cc_by_curr | filter_cc_by_prev]
        data_frames_for_payload_preparation["credit_card_balance"] = client_credit_card_df # Store

        # --- Prepare the final API payload ---
        # Now, iterate through the populated `data_frames_for_payload_preparation` 
        # and apply `prepare_df_for_json` to each.
        api_payload = {}
        for df_name, df_content in data_frames_for_payload_preparation.items():
            api_payload[df_name] = prepare_df_for_json(df_content)
        
        # client_main_descriptive_df is essentially the current_app slice before JSON prep
        # which is data_frames_for_payload_preparation["current_app"]
        return api_payload, data_frames_for_payload_preparation["current_app"]

    except FileNotFoundError as e:
        st.error(f"Data file not found (utils.py): {e}.")
        return None, None 
    except ValueError as ve: 
        print("--- TRACEBACK FOR VALUEERROR IN GET_DATA_FOR_CLIENT ---") # Add this
        import traceback
        print(traceback.format_exc()) # Add this
        st.error(f"ValueError during data loading (utils.py - check 'usecols'): {ve}")
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


def create_gauge_chart(score, threshold):
    """Creates a gauge chart to visualize the client's score against the threshold."""
    
    # The score from the API is a risk score (higher is worse).
    # The gauge should visually represent this.
    # We define zones: Green (safe), Yellow (borderline), Red (denied)
    
    # Define the color zones based on the threshold
    # A little buffer (e.g., 10 points) for the yellow "borderline" zone
    #borderline_start = threshold - 10 
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        number = {'suffix': ' pts'},
        title = {'text': "Score de Risque du Client"},
        delta = {'reference': threshold, 'increasing': {'color': "Red"}, 'decreasing': {'color': "Green"}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black", 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, threshold], 'color': 'lightgreen'},
                #{'range': [0, borderline_start], 'color': 'lightgreen'},
                #{'range': [borderline_start, threshold], 'color': 'lightyellow'},
                {'range': [threshold, 100], 'color': 'lightcoral'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': threshold
            }
        }
    ))
    
    fig.update_layout(
        height=300, 
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig