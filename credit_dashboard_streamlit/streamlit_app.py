import os
import json

import streamlit as st
import pandas as pd
import numpy as np
import requests




API_URL = "https://credit-scoring-api-p5ym.onrender.com/predict"
DATA_PATH = "data/"
OPTIMAL_THRESHOLD_SCORE = 63.36

APPLICATION_TEST_COLS_NEEDED = [
    # IDs
    'SK_ID_CURR',
    # Direct features from pipeline_input_columns.txt (or used for them)
    'EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3', 'AMT_CREDIT', 
    'DAYS_BIRTH', 'AMT_ANNUITY', 'AMT_GOODS_PRICE', 'DAYS_EMPLOYED', 
    'OWN_CAR_AGE', 'CODE_GENDER', # Used for CODE_GENDER_F, CODE_GENDER_M
    'NAME_EDUCATION_TYPE', # Used for NAME_EDUCATION_TYPE_Higher_education, etc.
    'DAYS_ID_PUBLISH', 'NAME_FAMILY_STATUS', # Used for NAME_FAMILY_STATUS_Married, etc.
    'NAME_CONTRACT_TYPE', # Is a direct feature and also likely used for display
    'REGION_RATING_CLIENT_W_CITY', 'FLAG_DOCUMENT_3', 'DEF_60_CNT_SOCIAL_CIRCLE',
    'REG_CITY_NOT_LIVE_CITY', 'NAME_INCOME_TYPE', # Used for NAME_INCOME_TYPE_Working, etc.
    'DAYS_LAST_PHONE_CHANGE', 'DAYS_REGISTRATION', 'AMT_REQ_CREDIT_BUREAU_QRT',
    'DEF_30_CNT_SOCIAL_CIRCLE', 'OCCUPATION_TYPE', # Used for OCCUPATION_TYPE_Core_staff, etc.
    'ORGANIZATION_TYPE', # Used for ORGANIZATION_TYPE_Self_employed, etc.
    'YEARS_BEGINEXPLUATATION_MODE', 'FLOORSMAX_AVG', 'APARTMENTS_MEDI', 
    'AMT_INCOME_TOTAL', 'LIVINGAREA_MEDI', 'FLOORSMAX_MEDI', 
    'NONLIVINGAPARTMENTS_MEDI', 'OBS_60_CNT_SOCIAL_CIRCLE', 'LIVINGAREA_MODE', 
    'REGION_POPULATION_RELATIVE', 'FLAG_DOCUMENT_18', 'APARTMENTS_MODE',
    'WALLSMATERIAL_MODE', # Used for WALLSMATERIAL_MODE_Monolithic
    'NONLIVINGAPARTMENTS_AVG', 'LANDAREA_MEDI', 'YEARS_BEGINEXPLUATATION_MEDI',
    'BASEMENTAREA_MEDI', 'NONLIVINGAREA_MODE', 'TOTALAREA_MODE', 
    'YEARS_BUILD_MODE', 'YEARS_BUILD_MEDI', 'ENTRANCES_MODE', 
    'REGION_RATING_CLIENT', 'FLAG_WORK_PHONE',
    # Columns used by initial LabelEncoder or get_dummies in prepare_input_data for current_app:
    # Add any other 'object' columns from application_test.csv that are processed by
    # current_app = pd.get_dummies(current_app, ...) or the LabelEncoder loop
    # My script identified these as object types from your list:
    'NAME_TYPE_SUITE', 'NAME_HOUSING_TYPE', 'WEEKDAY_APPR_PROCESS_START', 
    'FONDKAPREMONT_MODE', 'HOUSETYPE_MODE', 'EMERGENCYSTATE_MODE',
    # Other flags/numeric columns often used for display or basic features
    'FLAG_OWN_CAR', 'FLAG_OWN_REALTY', 'CNT_CHILDREN', 'CNT_FAM_MEMBERS',
    'HOUR_APPR_PROCESS_START', # Though features are from prev_app, this might be for display
    # Other FLAG_DOCUMENT_... if any are directly used and in pipeline_input_columns.txt
    'FLAG_MOBIL', 'FLAG_EMP_PHONE', 'FLAG_CONT_MOBILE', 'FLAG_PHONE', 'FLAG_EMAIL',
    'REG_REGION_NOT_LIVE_REGION', 'REG_REGION_NOT_WORK_REGION', 'LIVE_REGION_NOT_WORK_REGION',
    'REG_CITY_NOT_WORK_CITY', 'LIVE_CITY_NOT_WORK_CITY',
    'APARTMENTS_AVG', 'BASEMENTAREA_AVG', 'YEARS_BEGINEXPLUATATION_AVG', 'YEARS_BUILD_AVG', 
    'COMMONAREA_AVG', 'ELEVATORS_AVG', 'ENTRANCES_AVG', 'FLOORSMIN_AVG', 'LANDAREA_AVG', 
    'LIVINGAPARTMENTS_AVG', 'LIVINGAREA_AVG', 'NONLIVINGAPARTMENTS_AVG', 
    'COMMONAREA_MODE', 'ELEVATORS_MODE', 'FLOORSMIN_MODE', 'LANDAREA_MODE', 
    'LIVINGAPARTMENTS_MODE', 'COMMONAREA_MEDI', 'ELEVATORS_MEDI', 'FLOORSMIN_MEDI', 
    'LIVINGAPARTMENTS_MEDI', 'OBS_30_CNT_SOCIAL_CIRCLE',
    'FLAG_DOCUMENT_2', 'FLAG_DOCUMENT_4', 'FLAG_DOCUMENT_5', 'FLAG_DOCUMENT_6', 'FLAG_DOCUMENT_7', 
    'FLAG_DOCUMENT_8', 'FLAG_DOCUMENT_9', 'FLAG_DOCUMENT_10', 'FLAG_DOCUMENT_11', 'FLAG_DOCUMENT_12', 
    'FLAG_DOCUMENT_13', 'FLAG_DOCUMENT_14', 'FLAG_DOCUMENT_15', 'FLAG_DOCUMENT_16', 'FLAG_DOCUMENT_17',
    'FLAG_DOCUMENT_19', 'FLAG_DOCUMENT_20', 'FLAG_DOCUMENT_21',
    'AMT_REQ_CREDIT_BUREAU_HOUR', 'AMT_REQ_CREDIT_BUREAU_DAY', 'AMT_REQ_CREDIT_BUREAU_WEEK',
    'AMT_REQ_CREDIT_BUREAU_MON', 'AMT_REQ_CREDIT_BUREAU_YEAR'
]
APPLICATION_TEST_COLS_NEEDED = sorted(list(set(APPLICATION_TEST_COLS_NEEDED))) # Unique and sorted

BUREAU_COLS_NEEDED = [
    # IDs
    'SK_ID_CURR', 'SK_ID_BUREAU',
    # Columns used in manual feature engineering for final_bureau_features:
    'CREDIT_ACTIVE', 'CREDIT_TYPE', 'AMT_CREDIT_MAX_OVERDUE', 
    'AMT_CREDIT_SUM_OVERDUE', 'CNT_CREDIT_PROLONG', 'AMT_CREDIT_SUM_DEBT', 
    'AMT_CREDIT_SUM', 'DAYS_CREDIT_ENDDATE', 'CREDIT_DAY_OVERDUE',
    # Columns processed by agg_numeric (df_name='bureau') contributing to pipeline_input_columns.txt
    'DAYS_CREDIT', 'AMT_ANNUITY', # Note: AMT_ANNUITY from bureau is used for bureau_AMT_ANNUITY_max
    # 'AMT_CREDIT_SUM_LIMIT' (used for bureau_AMT_CREDIT_SUM_LIMIT_mean, bureau_AMT_CREDIT_SUM_LIMIT_count)
    'AMT_CREDIT_SUM_LIMIT', 
    # 'DAYS_CREDIT_UPDATE' (used for bureau_DAYS_CREDIT_UPDATE_mean, etc.)
    'DAYS_CREDIT_UPDATE',
    # Columns processed by count_categorical (df_name='bureau') contributing to pipeline_input_columns.txt
    # (CREDIT_ACTIVE and CREDIT_TYPE are already listed from manual part)
    'CREDIT_CURRENCY' # If it's an object type and generates features. Let's assume it might.
]
BUREAU_COLS_NEEDED = sorted(list(set(BUREAU_COLS_NEEDED)))

BUREAU_BALANCE_COLS_NEEDED = [
    # IDs
    'SK_ID_BUREAU',
    # Columns used in manual feature engineering for final_bureau_balance_features:
    'MONTHS_BALANCE', 'STATUS'
    # No direct call to agg_numeric/count_categorical on raw bureau_balance that generates
    # features in pipeline_input_columns.txt with 'bureau_balance_' prefix.
    # The 'client_bureau_balance_...' features are from aggregating 'final_bureau_balance_features_with_curr'.
]
BUREAU_BALANCE_COLS_NEEDED = sorted(list(set(BUREAU_BALANCE_COLS_NEEDED)))

PREVIOUS_APPLICATION_COLS_NEEDED = [
    # IDs
    'SK_ID_CURR', 'SK_ID_PREV',
    # Columns processed by agg_numeric (df_name='previous_application') contributing to pipeline_input_columns.txt
    'CNT_PAYMENT', 'AMT_DOWN_PAYMENT', 'DAYS_LAST_DUE_1ST_VERSION', 'AMT_ANNUITY',
    'DAYS_FIRST_DRAWING', 'RATE_DOWN_PAYMENT', 'HOUR_APPR_PROCESS_START',
    'SELLERPLACE_AREA', 'DAYS_FIRST_DUE', 'DAYS_LAST_DUE', 'DAYS_DECISION',
    'DAYS_TERMINATION', 'AMT_GOODS_PRICE', 'AMT_APPLICATION', 'AMT_CREDIT',
    # Columns processed by count_categorical (df_name='previous_application') contributing to pipeline_input_columns.txt
    'NAME_CONTRACT_STATUS', 'NAME_YIELD_GROUP', 'PRODUCT_COMBINATION',
    'NAME_GOODS_CATEGORY', 'CODE_REJECT_REASON', 'NAME_PRODUCT_TYPE',
    'NAME_PAYMENT_TYPE', 'NAME_CASH_LOAN_PURPOSE', 'NAME_CONTRACT_TYPE', # Also a direct feature
    'CHANNEL_TYPE', 'NAME_PORTFOLIO', 'WEEKDAY_APPR_PROCESS_START', 
    'NAME_TYPE_SUITE', 'NAME_CLIENT_TYPE', 'NAME_SELLER_INDUSTRY',
    # Other raw columns from previous_application that might be used:
    'FLAG_LAST_APPL_PER_CONTRACT', 'NFLAG_LAST_APPL_IN_DAY', 
    'RATE_INTEREST_PRIMARY', 'RATE_INTEREST_PRIVILEGED', 
    'NFLAG_INSURED_ON_APPROVAL'
]
PREVIOUS_APPLICATION_COLS_NEEDED = sorted(list(set(PREVIOUS_APPLICATION_COLS_NEEDED)))

POS_CASH_BALANCE_COLS_NEEDED = [
    # IDs
    'SK_ID_CURR', 'SK_ID_PREV',
    # Columns processed by agg_numeric (df_name='POS_CASH_balance') contributing to pipeline_input_columns.txt
    'CNT_INSTALMENT_FUTURE', 'SK_DPD_DEF', 'MONTHS_BALANCE', 'CNT_INSTALMENT', 'SK_DPD',
    # Columns processed by count_categorical (df_name='POS_CASH_balance') contributing to pipeline_input_columns.txt
    'NAME_CONTRACT_STATUS'
]
POS_CASH_BALANCE_COLS_NEEDED = sorted(list(set(POS_CASH_BALANCE_COLS_NEEDED)))

INSTALLMENTS_PAYMENTS_COLS_NEEDED = [
    # IDs
    'SK_ID_CURR', 'SK_ID_PREV',
    # df_name was 'credit_card_balance' for this one in your script, which is confusing.
    # Assuming it processes numeric cols from installments_payments and these might be relevant if fixed:
    'NUM_INSTALMENT_VERSION', 'NUM_INSTALMENT_NUMBER', 'DAYS_INSTALMENT', 
    'DAYS_ENTRY_PAYMENT', 'AMT_INSTALMENT', 'AMT_PAYMENT'
    # If no features from installments_payments are actually in pipeline_input_columns.txt
    # (even with a misapplied 'credit_card_balance_' prefix), then this list could potentially be
    # just ['SK_ID_CURR', 'SK_ID_PREV'] if your API needs the DataFrame structure but not its content.
    # However, your call_api_script.py sends data for it, and agg_numeric IS called on it.
    # The `credit_card_balance_NUM_INSTALMENT_VERSION_mean` and `_sum` etc. are likely from `credit_card_balance` not `installments_payments`.
    # But your pipeline_input_columns.txt has `credit_card_balance_DAYS_ENTRY_PAYMENT_min` etc.
    # This needs care. For now, I will assume the numeric columns are needed because agg_numeric is called.
]
INSTALLMENTS_PAYMENTS_COLS_NEEDED = sorted(list(set(INSTALLMENTS_PAYMENTS_COLS_NEEDED)))


CREDIT_CARD_BALANCE_COLS_NEEDED = [
    # IDs
    'SK_ID_CURR', 'SK_ID_PREV',
    # Columns processed by agg_numeric (df_name='credit_card_balance') contributing to pipeline_input_columns.txt
    'AMT_PAYMENT', 'CNT_DRAWINGS_ATM_CURRENT', 'DAYS_ENTRY_PAYMENT', 
    'CNT_DRAWINGS_CURRENT', 'NUM_INSTALMENT_VERSION', 'AMT_INSTALMENT', # (This AMT_INSTALMENT is from CCB)
    'AMT_CREDIT_LIMIT_ACTUAL', 'AMT_BALANCE', 'AMT_RECIVABLE', 
    'AMT_DRAWINGS_CURRENT', # (already listed as CNT_DRAWINGS_CURRENT implies AMT_DRAWINGS_CURRENT)
    'DAYS_INSTALMENT', # (This DAYS_INSTALMENT is from CCB)
    'NUM_INSTALMENT_NUMBER', # (This NUM_INSTALMENT_NUMBER is from CCB)
    'AMT_RECEIVABLE_PRINCIPAL', 'MONTHS_BALANCE', 'AMT_TOTAL_RECEIVABLE',
    'CNT_INSTALMENT_MATURE_CUM', 'CNT_DRAWINGS_POS_CURRENT', 'SK_DPD',
    'AMT_PAYMENT_CURRENT', # (Used for credit_card_balance_AMT_PAYMENT_CURRENT_sum)
    # Columns processed by count_categorical (df_name='credit_card_balance') contributing to pipeline_input_columns.txt
    'NAME_CONTRACT_STATUS',
    # Other numeric columns from credit_card_balance.csv (as agg_numeric processes all numeric):
    'AMT_DRAWINGS_ATM_CURRENT', # Already covered if used in a feature
    'AMT_DRAWINGS_OTHER_CURRENT', 'AMT_INST_MIN_REGULARITY', 
    'AMT_PAYMENT_TOTAL_CURRENT', 'SK_DPD_DEF',
    # Other object columns from credit_card_balance.csv (as count_categorical processes all object):
    # (NAME_CONTRACT_STATUS is the only object column in your raw list for credit_card_balance.csv)
    'CNT_DRAWINGS_OTHER_CURRENT' # This is numeric
]
CREDIT_CARD_BALANCE_COLS_NEEDED = sorted(list(set(CREDIT_CARD_BALANCE_COLS_NEEDED)))

@st.cache_data 
def get_data_for_client(client_id: int):
    data_frames_for_payload = {}
    client_main_descriptive_df = pd.DataFrame()
    try:
        # --- 1. current_app (from application_test.csv) ---
        df_app_test_full = pd.read_csv(
            os.path.join(DATA_PATH, "application_test.csv"), 
            usecols=APPLICATION_TEST_COLS_NEEDED 
        )
        client_main_descriptive_df = df_app_test_full[df_app_test_full['SK_ID_CURR'] == client_id]
        if client_main_descriptive_df.empty:
            st.error(f"Client ID {client_id} not found in application_test.csv (or columns missing).")
            return None, None 
        data_frames_for_payload["current_app"] = client_main_descriptive_df

        # --- 2. bureau.csv ---
        df_bureau_full = pd.read_csv(
            os.path.join(DATA_PATH, "bureau.csv"), 
            usecols=BUREAU_COLS_NEEDED
        )
        client_bureau_df = df_bureau_full[df_bureau_full['SK_ID_CURR'] == client_id]
        data_frames_for_payload["bureau"] = client_bureau_df
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
            data_frames_for_payload["bureau_balance"] = client_bureau_balance_df
        else:
            data_frames_for_payload["bureau_balance"] = pd.DataFrame(columns=BUREAU_BALANCE_COLS_NEEDED)

        # --- 4. previous_application.csv ---
        df_prev_app_full = pd.read_csv(
            os.path.join(DATA_PATH, "previous_application.csv"), 
            usecols=PREVIOUS_APPLICATION_COLS_NEEDED
        )
        client_prev_app_df = df_prev_app_full[df_prev_app_full['SK_ID_CURR'] == client_id]
        data_frames_for_payload["previous_application"] = client_prev_app_df
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
        data_frames_for_payload["POS_CASH_balance"] = client_pos_cash_df
        
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
        data_frames_for_payload["installments_payments"] = client_installments_df

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
        data_frames_for_payload["credit_card_balance"] = client_credit_card_df

        api_payload = {}
        for df_name, df_content in data_frames_for_payload.items():
            api_payload[df_name] = prepare_df_for_json(df_content)
        return api_payload, client_main_descriptive_df

    except FileNotFoundError as e:
        st.error(f"Data file not found for client {client_id}: {e}.")
        return None, None 
    except ValueError as ve: 
        st.error(f"ValueError during data loading for client {client_id} (check 'usecols'): {ve}")
        return None, None
    except Exception as e: 
        st.error(f"Unexpected error in get_data_for_client (ID {client_id}): {e}")
        import traceback 
        st.error(traceback.format_exc()) 
        return None, None

def call_prediction_api(payload_dict: dict):
    if not API_URL or API_URL == "YOUR_API_ENDPOINT_URL_HERE": 
        st.error("API_URL not configured.")
        return None
    try:
        response = requests.post(API_URL, json=payload_dict, timeout=300) 
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error(f"API request to {API_URL} timed out.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Failed to connect to API at {API_URL}.")
        return None
    except requests.exceptions.HTTPError as http_err: 
        st.error(f"API HTTP error: {http_err.response.status_code} {http_err.response.reason}.")
        st.error(f"API Response (first 500 chars): {http_err.response.text[:500]}...")
        return None
    except requests.exceptions.RequestException as req_err: 
        st.error(f"API request error: {req_err}")
        return None
    except ValueError as json_err: 
        st.error(f"Error decoding JSON from API: {json_err}")
        st.error(f"Raw API response (first 200 chars): {response.text[:200]}...") 
        return None

# --- 3. MAIN APPLICATION LAYOUT AND LOGIC ---
st.set_page_config(layout="wide", page_title="Dashboard Scoring Crédit P7")
st.title("🏦 Dashboard Interactif de Scoring Crédit")
st.markdown("---") 

st.sidebar.header("👨‍💼 Sélection du Client")
available_ids = load_available_client_ids() 

if not available_ids:
    st.error("Cannot load client IDs. App cannot continue.")
    st.stop() 

selected_client_id = int(st.sidebar.selectbox(
    label="Choisissez un ID Client:",  
    options=available_ids,            
    index=0                           
))

if selected_client_id:
    st.header(f"🔍 Analyse Détaillée du Client ID: {selected_client_id}")
    with st.spinner(f"Chargement des données pour client {selected_client_id}..."):
        client_api_payload, client_main_info_df = get_data_for_client(selected_client_id)

    if client_api_payload is None or client_main_info_df is None:
        st.warning("Cannot display info: client data failed to load.")
        st.stop() 

    st.subheader("📋 Informations Descriptives Générales du Client")
    if not client_main_info_df.empty:
        display_series = client_main_info_df.iloc[0].copy()
        if 'DAYS_BIRTH' in display_series and pd.notna(display_series['DAYS_BIRTH']):
            display_series['AGE_ANNÉES'] = abs(int(display_series['DAYS_BIRTH'] // 365))
        if 'DAYS_EMPLOYED' in display_series and pd.notna(display_series['DAYS_EMPLOYED']):
            if display_series['DAYS_EMPLOYED'] < 200000: 
                display_series['ANNÉES_EMPLOI'] = abs(int(display_series['DAYS_EMPLOYED'] // 365))
            else:
                display_series['ANNÉES_EMPLOI'] = "N/A (ou Erreur Donnée)"
        st.dataframe(
            pd.DataFrame(display_series).rename(columns={display_series.name: "Valeur"}).astype(str),
            use_container_width=True 
        )
    else:
        st.write("No main descriptive info for this client in application_test.csv.")
    st.markdown("---") 

    st.subheader("📊 Score de Crédit et Décision du Modèle")
    try:
        payload_size_bytes = len(json.dumps(client_api_payload).encode('utf-8'))
        payload_size_mb = payload_size_bytes / (1024 * 1024) 
        st.info(f"Taille estimée du payload envoyé à l'API: {payload_size_mb:.3f} MB")
    except Exception as e_payload_size: 
        st.warning(f"Cannot estimate payload size: {e_payload_size}")

    with st.spinner("Calcul du score via l'API..."):
        api_response_data = call_prediction_api(client_api_payload)

    if api_response_data:
        try:
            client_score_details_list = api_response_data.get('client_with_scores')
            if client_score_details_list and isinstance(client_score_details_list, list) and len(client_score_details_list) > 0:
                score_data_dict = client_score_details_list[0]
                raw_score_from_api = score_data_dict.get('SCORE')
                if raw_score_from_api is not None: 
                    probability_default = raw_score_from_api / 100.0
                    probability_repayment = 1.0 - probability_default
                    decision = "Crédit Accordé" if raw_score_from_api < OPTIMAL_THRESHOLD_SCORE else "Crédit Refusé"
                    col1, col2, col3 = st.columns(3)
                    with col1: 
                        st.metric(label="Score Client (selon API)", value=f"{raw_score_from_api:.2f}")
                        st.caption(f"Seuil de refus (score >) : {OPTIMAL_THRESHOLD_SCORE:.2f}")
                    with col2: 
                        st.metric(label="Probabilité de Remboursement", value=f"{probability_repayment:.2%}")
                    with col3: 
                        if decision == "Crédit Accordé":
                            st.success(f"Décision: {decision} 🎉")
                        else:
                            st.error(f"Décision: {decision} 😥")
                    st.progress(probability_repayment)
                    st.caption(f"Barre de progression: Prob. remboursement. Seuil implicite > {((100-OPTIMAL_THRESHOLD_SCORE)/100):.0%}.")
                    st.markdown("#### Interprétation Simplifiée pour le Chargé de Relation Client:")
                    if decision == "Crédit Accordé": # Corrected typo from "CrédIT"
                        st.write(
                            f"Score client: **{raw_score_from_api:.2f}**. "
                            f"Ce score est **inférieur** au seuil de refus ({OPTIMAL_THRESHOLD_SCORE:.2f}), "
                            f"correspondant à une prob. de remboursement de **{probability_repayment:.0%}**. "
                            "Demande **acceptée**."
                        )
                    else: 
                        st.write(
                            f"Score client: **{raw_score_from_api:.2f}**. "
                            f"Ce score est **supérieur ou égal** au seuil de refus ({OPTIMAL_THRESHOLD_SCORE:.2f}), "
                            f"correspondant à une prob. de défaut de **{probability_default:.0%}** (remb. {probability_repayment:.0%}). "
                            "Demande **refusée**."
                        )
                else: 
                    st.error("Clé 'SCORE' manquante/nulle dans 'client_with_scores' de l'API.")
                    st.json(api_response_data) 
            else: 
                st.error("'client_with_scores' absente/mal formatée/vide dans la réponse API.")
                st.json(api_response_data) 
        except Exception as e: 
            st.error(f"Erreur traitement réponse API: {e}")
            st.json(api_response_data) 
    else: 
        st.warning("Aucune réponse/erreur de l'API pour le score.")
else:
    st.info("Veuillez sélectionner un ID client.")

# --- 4. FOOTER (Optional) ---
st.markdown("---")
st.caption("P7: Implémentez un modèle de scoring - Dashboard Client @ OpenClassrooms")