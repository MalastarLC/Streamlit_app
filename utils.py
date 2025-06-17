# credit_dashboard_streamlit/utils.py

import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
import plotly.graph_objects as go
import traceback # Added for better error logging

# --- CONFIGURATION & CONSTANTS ---

# This is the S3 bucket where your NEW Parquet data is stored.
S3_BUCKET_NAME = "streamlit-credit-data-bucket-2"

# These lists of columns are still relevant, as they describe the columns
# that will be present in the data we read from the Parquet files.
APPLICATION_TEST_COLS_NEEDED = [
    'AMT_ANNUITY', 'AMT_CREDIT', 'AMT_GOODS_PRICE', 'AMT_INCOME_TOTAL', 'AMT_REQ_CREDIT_BUREAU_DAY', 
    'AMT_REQ_CREDIT_BUREAU_HOUR', 'AMT_REQ_CREDIT_BUREAU_MON', 'AMT_REQ_CREDIT_BUREAU_QRT', 
    'AMT_REQ_CREDIT_BUREAU_WEEK', 'AMT_REQ_CREDIT_BUREAU_YEAR', 'APARTMENTS_AVG', 'APARTMENTS_MEDI', 
    'APARTMENTS_MODE', 'BASEMENTAREA_AVG', 'BASEMENTAREA_MEDI', 'BASEMENTAREA_MODE', 'CODE_GENDER', 
    'COMMONAREA_AVG', 'COMMONAREA_MEDI', 'COMMONAREA_MODE', 'CNT_CHILDREN', 'CNT_FAM_MEMBERS', 
    'DAYS_BIRTH', 'DAYS_EMPLOYED', 'DAYS_ID_PUBLISH', 'DAYS_LAST_PHONE_CHANGE', 'DAYS_REGISTRATION', 
    'DEF_30_CNT_SOCIAL_CIRCLE', 'DEF_60_CNT_SOCIAL_CIRCLE', 'ELEVATORS_AVG', 'ELEVATORS_MEDI', 
    'ELEVATORS_MODE', 'EMERGENCYSTATE_MODE', 'ENTRANCES_AVG', 'ENTRANCES_MEDI', 'ENTRANCES_MODE', 
    'EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3', 'FLAG_CONT_MOBILE', 'FLAG_DOCUMENT_10', 
    'FLAG_DOCUMENT_11', 'FLAG_DOCUMENT_12', 'FLAG_DOCUMENT_13', 'FLAG_DOCUMENT_14', 'FLAG_DOCUMENT_15', 
    'FLAG_DOCUMENT_16', 'FLAG_DOCUMENT_17', 'FLAG_DOCUMENT_18', 'FLAG_DOCUMENT_19', 'FLAG_DOCUMENT_2', 
    'FLAG_DOCUMENT_20', 'FLAG_DOCUMENT_21', 'FLAG_DOCUMENT_3', 'FLAG_DOCUMENT_4', 'FLAG_DOCUMENT_5', 
    'FLAG_DOCUMENT_6', 'FLAG_DOCUMENT_7', 'FLAG_DOCUMENT_8', 'FLAG_DOCUMENT_9', 'FLAG_EMAIL', 
    'FLAG_EMP_PHONE', 'FLAG_MOBIL', 'FLAG_OWN_CAR', 'FLAG_OWN_REALTY', 'FLAG_PHONE', 'FLAG_WORK_PHONE', 
    'FLOORSMAX_AVG', 'FLOORSMAX_MEDI', 'FLOORSMAX_MODE', 'FLOORSMIN_AVG', 'FLOORSMIN_MEDI', 'FLOORSMIN_MODE', 
    'FONDKAPREMONT_MODE', 'HOUR_APPR_PROCESS_START', 'HOUSETYPE_MODE', 'LANDAREA_AVG', 'LANDAREA_MEDI', 
    'LANDAREA_MODE', 'LIVE_CITY_NOT_WORK_CITY', 'LIVE_REGION_NOT_WORK_REGION', 'LIVINGAPARTMENTS_AVG', 
    'LIVINGAPARTMENTS_MEDI', 'LIVINGAPARTMENTS_MODE', 'LIVINGAREA_AVG', 'LIVINGAREA_MEDI', 'LIVINGAREA_MODE', 
    'NAME_CONTRACT_TYPE', 'NAME_EDUCATION_TYPE', 'NAME_FAMILY_STATUS', 'NAME_HOUSING_TYPE', 'NAME_INCOME_TYPE', 
    'NAME_TYPE_SUITE', 'NONLIVINGAPARTMENTS_AVG', 'NONLIVINGAPARTMENTS_MEDI', 'NONLIVINGAPARTMENTS_MODE', 
    'NONLIVINGAREA_AVG', 'NONLIVINGAREA_MEDI', 'NONLIVINGAREA_MODE', 'OBS_30_CNT_SOCIAL_CIRCLE', 
    'OBS_60_CNT_SOCIAL_CIRCLE', 'OCCUPATION_TYPE', 'ORGANIZATION_TYPE', 'OWN_CAR_AGE', 
    'REG_CITY_NOT_LIVE_CITY', 'REG_CITY_NOT_WORK_CITY', 'REG_REGION_NOT_LIVE_REGION', 
    'REG_REGION_NOT_WORK_REGION', 'REGION_POPULATION_RELATIVE', 'REGION_RATING_CLIENT', 
    'REGION_RATING_CLIENT_W_CITY', 'SK_ID_CURR', 'TOTALAREA_MODE', 'WALLSMATERIAL_MODE', 
    'WEEKDAY_APPR_PROCESS_START', 'YEARS_BEGINEXPLUATATION_AVG', 'YEARS_BEGINEXPLUATATION_MEDI', 
    'YEARS_BEGINEXPLUATATION_MODE', 'YEARS_BUILD_AVG', 'YEARS_BUILD_MEDI', 'YEARS_BUILD_MODE'
]
# ... (The other _COLS_NEEDED lists can remain as they are, but are not strictly necessary for this file anymore) ...


# --- HELPER FUNCTION DEFINITIONS ---

# UPDATED to read from the efficient application_test.parquet file
@st.cache_data
def load_available_client_ids(app_file_name: str = "application_test.parquet") -> list:
    """
    Loads unique SK_ID_CURR values from the small application_test.parquet file for very fast startup.
    """
    try:
        s3_path = f"s3://{S3_BUCKET_NAME}/data_parquet/{app_file_name}"
        print(f"Loading available client IDs from: {s3_path}")
        # Read only the single column we need for maximum efficiency
        df = pd.read_parquet(s3_path, columns=['SK_ID_CURR'])
        client_ids = sorted(df['SK_ID_CURR'].unique().tolist())
        if not client_ids: 
            st.error(f"No client IDs found in '{s3_path}'.")
            return []
        print("Client IDs loaded successfully.")
        return client_ids
    except Exception as e: 
        st.error(f"FATAL: Could not load client IDs from {s3_path}. The application cannot start.")
        st.error(traceback.format_exc())
        return []


# UNCHANGED: This function is generic and works perfectly as is.
def prepare_df_for_json(df_orig: pd.DataFrame) -> list:
    """
    Prepares a Pandas DataFrame for safe JSON serialization.
    """
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


# COMPLETELY REWRITTEN to be fast and efficient using Parquet
@st.cache_data
def get_data_for_client(client_id: int) -> tuple[dict | None, pd.DataFrame | None]:
    """
    Loads data for a single client efficiently from schema-aware, partitioned Parquet files on S3.
    """
    S3_DATA_FOLDER = f"s3://{S3_BUCKET_NAME}/data_parquet"
    
    print(f"--- DÉBUT: get_data_for_client (SCHEMA-AWARE PARQUET) pour client ID: {client_id} ---")

    try:
        # Define the primary filter for most tables, which will be used for fast lookups.
        id_filter = [('SK_ID_CURR', '=', client_id)]

        # --- 1. current_app (read from the single parquet file) ---
        # It's small and efficient to read the whole thing once and filter in memory.
        @st.cache_data
        def load_app_test_data_parquet():
            print("Loading application_test.parquet...")
            return pd.read_parquet(f"{S3_DATA_FOLDER}/application_test.parquet")
        
        df_app_test_full = load_app_test_data_parquet()
        client_main_descriptive_df = df_app_test_full[df_app_test_full['SK_ID_CURR'] == client_id]

        if client_main_descriptive_df.empty:
            st.error(f"Client ID {client_id} not found in application_test.parquet.")
            return None, None

        # --- 2. Bureau (Partitioned by SK_ID_CURR) ---
        print("Reading partitioned bureau data...")
        client_bureau_df = pd.read_parquet(f"{S3_DATA_FOLDER}/bureau.parquet", filters=id_filter)
        
        # --- 3. Bureau Balance (Partitioned by SK_ID_BUREAU) ---
        # This is the crucial two-step lookup based on your data schema.
        print("Reading partitioned bureau_balance data...")
        if not client_bureau_df.empty and 'SK_ID_BUREAU' in client_bureau_df.columns:
            bureau_ids = client_bureau_df['SK_ID_BUREAU'].unique().tolist()
            bureau_id_filter = [('SK_ID_BUREAU', 'in', bureau_ids)]
            client_bureau_balance_df = pd.read_parquet(f"{S3_DATA_FOLDER}/bureau_balance.parquet", filters=bureau_id_filter)
        else:
            # If the client has no loans in the bureau file, they won't have bureau_balance records.
            client_bureau_balance_df = pd.DataFrame() 

        # --- 4-7. Read all other related tables (All Partitioned by SK_ID_CURR) ---
        print("Reading other partitioned data files...")
        client_prev_app_df = pd.read_parquet(f"{S3_DATA_FOLDER}/previous_application.parquet", filters=id_filter)
        client_pos_cash_df = pd.read_parquet(f"{S3_DATA_FOLDER}/POS_CASH_balance.parquet", filters=id_filter)
        client_installments_df = pd.read_parquet(f"{S3_DATA_FOLDER}/installments_payments.parquet", filters=id_filter)
        client_credit_card_df = pd.read_parquet(f"{S3_DATA_FOLDER}/credit_card_balance.parquet", filters=id_filter)

        # --- Prepare the final API payload ---
        api_payload = {
            "current_app": prepare_df_for_json(client_main_descriptive_df),
            "bureau": prepare_df_for_json(client_bureau_df),
            "bureau_balance": prepare_df_for_json(client_bureau_balance_df),
            "previous_application": prepare_df_for_json(client_prev_app_df),
            "POS_CASH_balance": prepare_df_for_json(client_pos_cash_df),
            "installments_payments": prepare_df_for_json(client_installments_df),
            "credit_card_balance": prepare_df_for_json(client_credit_card_df)
        }
        
        print("--- FIN: get_data_for_client (SCHEMA-AWARE PARQUET) ---")
        return api_payload, client_main_descriptive_df

    except Exception as e:
        st.error(f"An error occurred in get_data_for_client (Parquet version): {e}")
        st.error(traceback.format_exc())
        return None, None


# UNCHANGED: This function is generic and works perfectly as is.
def call_prediction_api(payload_dict: dict, api_url_param: str) -> dict | None:
    """
    Sends the prepared data payload to the prediction API and returns the response.
    """
    if not api_url_param: 
        st.error("API_URL parameter is missing or empty for call_prediction_api.")
        return None
    try:
        response = requests.post(api_url_param, json=payload_dict, timeout=300) 
        response.raise_for_status()
        return response.json()
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
        # Raw response might not be available if the error is not from requests
        # st.error(f"Raw API response (first 200 chars): {response.text[:200]}...") 
        return None


# UNCHANGED: This function is for visualization and works perfectly as is.
def create_gauge_chart(score, threshold):
    """Creates a gauge chart to visualize the client's score against the threshold."""
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


# --- NEW CODE FOR COMPARISON CHARTS ---

# Dictionnaire associant des noms lisibles aux noms de colonnes techniques.
COMPARISON_COLS = {
    'Score externe 1': 'EXT_SOURCE_1', 'Score externe 2': 'EXT_SOURCE_2', 'Score externe 3': 'EXT_SOURCE_3',
    'Mensualité du prêt': 'AMT_ANNUITY', 'Revenu Total': 'AMT_INCOME_TOTAL', 'Montant du Crédit': 'AMT_CREDIT',
    'Prix du Bien': 'AMT_GOODS_PRICE', 'Âge du client': 'AGE_ANNÉES', 'Années d\'emploi': 'ANNÉES_EMPLOI',
    'Nombre d\'enfants': 'CNT_CHILDREN', 'Type de prêt' : 'NAME_CONTRACT_TYPE',
    'Niveau d\'éducation': 'NAME_EDUCATION_TYPE', 'Statut Familial': 'NAME_FAMILY_STATUS',
    'Possède une voiture': 'FLAG_OWN_CAR'
}

# UPDATED to read from the efficient application_test.parquet file
@st.cache_data
def load_all_clients_data(app_file_name: str = "application_test.parquet"):
    """
    Loads descriptive data for all clients from the efficient application_test.parquet file.
    Calculates age and employment years for comparison. Cached for performance.
    """
    try:
        # Define columns needed for comparison charts
        cols_to_load = list(set(COMPARISON_COLS.values()) - {'AGE_ANNÉES', 'ANNÉES_EMPLOI'})
        cols_to_load.extend(['DAYS_BIRTH', 'DAYS_EMPLOYED', 'SK_ID_CURR', 'NAME_FAMILY_STATUS', 'CODE_GENDER'])
        cols_to_load = list(set(cols_to_load))

        s3_path = f"s3://{S3_BUCKET_NAME}/data_parquet/{app_file_name}"
        print(f"Loading all clients data for charts from: {s3_path}")
        df_all = pd.read_parquet(s3_path, columns=cols_to_load)

        # --- Create simple features for comparison ---
        if 'DAYS_BIRTH' in df_all.columns:
            df_all['AGE_ANNÉES'] = df_all['DAYS_BIRTH'].abs() // 365
            df_all.loc[df_all['AGE_ANNÉES'] > 100, 'AGE_ANNÉES'] = np.nan

        if 'DAYS_EMPLOYED' in df_all.columns:
            df_all['ANNÉES_EMPLOI'] = df_all['DAYS_EMPLOYED'].abs() // 365
            df_all.loc[df_all['ANNÉES_EMPLOI'] > 80, 'ANNÉES_EMPLOI'] = np.nan

        print("All clients data loaded successfully.")
        return df_all

    except Exception as e:
        st.error(f"Error loading data for comparison charts from {s3_path}: {e}")
        st.error(traceback.format_exc())
        return pd.DataFrame()