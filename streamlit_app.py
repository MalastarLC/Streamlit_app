import os
import json

import streamlit as st
import pandas as pd
import numpy as np
import requests

from utils import load_available_client_ids, get_data_for_client, call_prediction_api



API_URL = "https://credit-scoring-api-p5ym.onrender.com/predict"
DATA_PATH = "data/"
OPTIMAL_THRESHOLD_SCORE = 63.36

# --- 1. DEFINING NEEDED COLUMNS TO MINIMIZE RAM USAGE ---

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
    'AMT_INST_MIN_REGULARITY', 'AMT_INSTALMENT', 'AMT_PAYMENT', 'AMT_PAYMENT_CURRENT',
    'AMT_PAYMENT_TOTAL_CURRENT', 'AMT_RECEIVABLE_PRINCIPAL', 'AMT_RECIVABLE',
    'AMT_TOTAL_RECEIVABLE', 'CNT_DRAWINGS_ATM_CURRENT', 'CNT_DRAWINGS_CURRENT',
    'CNT_DRAWINGS_OTHER_CURRENT', 'CNT_DRAWINGS_POS_CURRENT',
    'CNT_INSTALMENT_MATURE_CUM', 'DAYS_ENTRY_PAYMENT', 'DAYS_INSTALMENT',
    'MONTHS_BALANCE', 'NAME_CONTRACT_STATUS', 'NUM_INSTALMENT_NUMBER',
    'NUM_INSTALMENT_VERSION', 'SK_DPD', 'SK_DPD_DEF', 'SK_ID_CURR', 'SK_ID_PREV'
]
# --- END OF _COLS_NEEDED LISTS ---

# --- 2. MAIN APPLICATION LAYOUT AND LOGIC ---
st.set_page_config(layout="wide", page_title="Dashboard Scoring Crédit P7")
st.title("🏦 Dashboard Interactif de Scoring Crédit")
st.markdown("---") 

st.sidebar.header("👨‍💼 Sélection du Client")
available_ids = load_available_client_ids() 

if not available_ids:
    st.error("Impossible de charger la liste des IDs clients. L'application ne peut pas continuer. Vérifiez la configuration des données et les logs.")
    st.stop() 

selected_client_id = int(st.sidebar.selectbox(
    label="Choisissez un ID Client:",  
    options=available_ids,            
    index=0                           
))

if selected_client_id:
    st.header(f"🔍 Analyse Détaillée du Client ID: {selected_client_id}")
    with st.spinner(f"Chargement et préparation des données pour le client {selected_client_id}... (Merci de patienter)"):
        client_api_payload, client_main_info_df = get_data_for_client(selected_client_id)

    if client_api_payload is None or client_main_info_df is None:
        st.warning("Les informations ne peuvent pas être affichées car les données du client n'ont pas pu être chargées. Veuillez vérifier les messages d'erreur ci-dessus.")
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
        st.write("Aucune information descriptive principale trouvée pour ce client dans application_test.csv.")
    st.markdown("---") 

    st.subheader("📊 Score de Crédit et Décision du Modèle")
    try:
        payload_size_bytes = len(json.dumps(client_api_payload).encode('utf-8'))
        payload_size_mb = payload_size_bytes / (1024 * 1024) 
        st.info(f"Taille estimée du payload de données envoyé à l'API: {payload_size_mb:.3f} MB")
    except Exception as e_payload_size: 
        st.warning(f"Impossible d'estimer la taille du payload : {e_payload_size}")

    with st.spinner("Calcul du score via l'API... (Cette opération peut prendre quelques instants)"):
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
                    st.caption(f"Barre de progression: Probabilité de remboursement. Le seuil de décision pour 'Crédit Accordé' implique une probabilité de remboursement > {((100-OPTIMAL_THRESHOLD_SCORE)/100):.0%}.")
                    st.markdown("#### Interprétation Simplifiée pour le Chargé de Relation Client:")
                    if decision == "Crédit Accordé": 
                        st.write(
                            f"Le modèle a attribué un score de **{raw_score_from_api:.2f}** à ce client. "
                            f"Ce score est **inférieur** au seuil de refus de {OPTIMAL_THRESHOLD_SCORE:.2f}. "
                            f"Cela correspond à une probabilité de remboursement estimée à **{probability_repayment:.0%}**. "
                            "Sur la base de ces éléments, la demande de crédit est **acceptée**."
                        )
                    else: 
                        st.write(
                            f"Le modèle a attribué un score de **{raw_score_from_api:.2f}** à ce client. "
                            f"Ce score est **supérieur ou égal** au seuil de refus de {OPTIMAL_THRESHOLD_SCORE:.2f}. "
                            f"Cela correspond à une probabilité de défaut estimée à **{probability_default:.0%}** (ou une probabilité de remboursement de seulement {probability_repayment:.0%}). "
                            "Sur la base de ces éléments, la demande de crédit est **refusée**."
                        )
                else: 
                    st.error("La clé 'SCORE' est manquante ou nulle dans la section 'client_with_scores' de la réponse de l'API.")
                    st.json(api_response_data) 
            else: 
                st.error("La section 'client_with_scores' est absente, mal formatée, ou vide dans la réponse de l'API.")
                st.json(api_response_data) 
        except Exception as e: 
            st.error(f"Une erreur est survenue lors du traitement de la réponse de l'API: {e}")
            st.json(api_response_data) 
    else: 
        st.warning("Aucune réponse (ou une erreur) n'a été reçue de l'API pour le calcul du score. Vérifiez les messages d'erreur précédents et l'état de l'API.")
else:
    st.info("Veuillez sélectionner un ID client dans la barre latérale pour afficher les détails.")