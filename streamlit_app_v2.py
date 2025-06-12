import os
import json

import streamlit as st
from streamlit_navigation_bar import st_navbar
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests

from utils import load_available_client_ids, get_data_for_client, call_prediction_api, create_gauge_chart, load_all_clients_data, COMPARISON_COLS

# Notes avant de commencer 
# Lorsqu'un utilisateur intéragit avec un widget streamlit et c'est une particularité de la librairie :
# Le script tout entier est relancé du début à la fin
# Dans notre cas, si l'on change l'ID dans le selectbox ou que l'on sélectionne une nouvelle variable de comparaison, le script est immédiatement relancé.
# Cette nouvelle exécution permet de mettre à jour la valeur de st.session_state.selected_client_id grâce à la ligne d'assignation qui est st.session_state.selected_client_id =
# Le script utilise ensuite cette nouvelle valeur pour afficher les bonnes informations.
# Pendant ce temps, les fonctions marquées avec @st.cache_data ne sont pas ré-exécutées si leurs arguments n'ont pas changé, ce qui permet de garder l'application rapide.



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

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", 
                   page_title="Dashboard Scoring Crédit P8", 
                   initial_sidebar_state="expanded", 
                   menu_items={ 
                       'About': "This app was made to calculate a prediction on the probability of a client repaying a loan they are applying for and whether or not this application is accepted. Please select the application id on the sidebar's dropdown list to see the the application result"
                        }
                    )


# --- 3. HOME PAGE APPLICATION LAYOUT AND LOGIC ---

def show_home_dashboard():
    """
    This function contains all the logic the home dashboard page.
    """

    st.title('Prêt à dépenser : Outil de "scoring crédit"')
    st.markdown("---") 


    selected_client_id = st.session_state.selected_client_id

    if selected_client_id:
        st.header(f"Prédiction pour l'application ID : {selected_client_id}")
        #st.header(f"🔍 Analyse Détaillée du Client ID: {selected_client_id}")
        with st.spinner(f"Chargement des informations liées à l'ID : {selected_client_id}... (Merci de patienter)"):
            client_api_payload, client_main_info_df = get_data_for_client(selected_client_id)

        with st.spinner("Calcul du score via l'API... (Cette opération peut prendre quelques instants)"):
            api_response_data = call_prediction_api(client_api_payload, API_URL)
            if api_response_data:
                try:
                    client_score_details_list = api_response_data.get('client_with_scores')
                    if client_score_details_list and isinstance(client_score_details_list, list) and len(client_score_details_list) > 0:
                        score_data_dict = client_score_details_list[0]
                        raw_score_from_api = score_data_dict.get('SCORE')
                        if raw_score_from_api is not None: 
                            probabilite_de_remboursement = 100 - raw_score_from_api
                            #probability_default = raw_score_from_api / 100.0
                            probabilite_de_defaut = raw_score_from_api
                            #probability_repayment = 1.0 - probability_default
                            seuil_de_remboursement = 100 - OPTIMAL_THRESHOLD_SCORE
                            decision = "Crédit Accordé" if probabilite_de_remboursement > (100 - 63.36) else "Crédit Refusé"
                            col1, col2, col3 = st.columns(3)
                            with col2: 
                                st.metric(label="Score Client (selon API)", value=f"{raw_score_from_api:.2f}")
                                st.caption(f"Seuil de refus (score >) : {OPTIMAL_THRESHOLD_SCORE:.2f}")
                            with col1: 
                                st.metric(label="Probabilité de Remboursement", value=f"{round(probabilite_de_remboursement, 2)}%")
                            with col3: 
                                if decision == "Crédit Accordé":
                                    st.success(f"{decision}")
                                else:
                                    st.error(f"{decision}")
                            
                            #Middle part
                            st.markdown("---")
                            col1, col2 = st.columns(2)                           
                            #Gauge plot
                            with col1:
                                gauge_graph = create_gauge_chart(raw_score_from_api, OPTIMAL_THRESHOLD_SCORE)
                                st.plotly_chart(gauge_graph, use_container_width=True)
                                # st.progress(probabilite_de_remboursement/100)                                                      
                            with col2:
                                st.markdown(
                                    "Explication du score :  \n"
                                    "  \n"
                                    "  \n"
                                    "  \n"
                                    "Pour une demande donnée l'application prédit un score de risque.  \n"
                                    "Ce score représente la probabilité sur 100 d'un risque de défaut.  \n"
                                    "  \n"
                                    "Le graphique à gauche permet de situer le score attribué au client  \n"
                                    "au seuil de risque limite accepté pour une demande de prêt.  \n"
                                )                            


                            #Lower part
                            st.markdown("---") 
                            #st.caption(f"Probabilité de remboursement Le seuil de décision pour 'Crédit Accordé' implique une probabilité de remboursement > {((100-OPTIMAL_THRESHOLD_SCORE)/100):.2%}.")
                            st.markdown("#### Interprétation du score:")
                            if decision == "Crédit Accordé": 
                                st.write(
                                    f"Le score du client est de **{raw_score_from_api:.2f}** pour cette application. "
                                    f"Ce score est **inférieur** au seuil de refus de {OPTIMAL_THRESHOLD_SCORE:.2f}. "
                                    f"Cela correspond à une probabilité de remboursement estimée à **{probabilite_de_remboursement/100:.2%}**. "
                                    "Sur la base de ces éléments, la demande de crédit est **acceptée**."
                                )
                            else: 
                                st.write(
                                    f"Le score du client est de **{raw_score_from_api:.2f}** pour cette application. "
                                    f"Ce score est **supérieur ou égal** au seuil de refus de {OPTIMAL_THRESHOLD_SCORE:.2f}. "
                                    f"Cela correspond à une probabilité de défaut estimée à **{raw_score_from_api:.2f}**%. "
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

def show_informations_relatives_au_client():

    st.title("Informations relatives au client")
    st.markdown("---") 

    selected_client_id = st.session_state.selected_client_id

    if selected_client_id:
        st.header(f"Analyse Détaillée du Client ID: {selected_client_id}")
        #st.header(f"🔍 Analyse Détaillée du Client ID: {selected_client_id}")
        with st.spinner(f"Chargement et préparation des données pour le client {selected_client_id}... (Merci de patienter)"):
            client_api_payload, client_main_info_df = get_data_for_client(selected_client_id)

        if client_api_payload is None or client_main_info_df is None:
            st.warning("Les informations ne peuvent pas être affichées car les données du client n'ont pas pu être chargées. Veuillez vérifier les messages d'erreur ci-dessus.")
            st.stop() 

        st.subheader("Informations Descriptives Générales du Client")
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

def show_graphiques_informations_relatives_au_client():


    # --- PARTIE 1 : Initialisation de la Page ---
    st.title("Graphiques de Comparaison Client")
    st.markdown("Comparez les informations du client sélectionné à celles d'autres groupes de clients.")
    st.markdown("---") 

    # --- PARTIE 2 : La sélection du client est faite par la sidebar centralisée
   
    selected_client_id = st.session_state.selected_client_id

    # --- Chargement des Données ---
    with st.spinner(f"Chargement des données pour le client {selected_client_id} et l'ensemble des applications"):
        # Données spécifiques au client sélectionné
        _, client_main_info_df = get_data_for_client(selected_client_id) # _ sert a stocker notre api_payload dans une variable "poubelle" car on n'en a besoin que pour la page home ou la prédiction est faite
        # Données de tous les clients pour la comparaison (rapide grâce au cache)
        all_clients_df = load_all_clients_data()

    if client_main_info_df is None or all_clients_df.empty:
        st.warning("Les données n'ont pas pu être chargées. Les graphiques ne peuvent pas être affichés.")
        st.stop()

    st.header(f"Analyse comparative pour le Client ID: {selected_client_id}")

    # --- PARTIE 4 : Interface de Sélection pour la Comparaison ---
    col1, col2 = st.columns(2)
    with col1:
        # L'utilisateur choisit la variable à visualiser
        selected_variable_label = st.selectbox(
            "Choisir une variable à comparer :",
            options=list(COMPARISON_COLS.keys()) # Utilise les noms lisibles
        )
        # On récupère le vrai nom de la colonne
        variable_to_compare = COMPARISON_COLS[selected_variable_label]
    
    with col2:
        # L'utilisateur choisit le groupe de comparaison
        comparison_group_label = st.radio(
            "Comparer à :",
            options=["L'ensemble des clients", "Clients avec un statut familial similaire", "Clients du même genre"],
            key="comparison_group"
        )
    
    # --- PARTIE 5 : Logique de Filtrage du Groupe de Comparaison ---
    client_series = all_clients_df[all_clients_df['SK_ID_CURR'] == selected_client_id].iloc[0] #when you select a single row, Pandas "pivots" that row. The original column names become the new index of the Series. Si on vait mis [[0]] à la place on aurait eu un DataFrame
                                                #its "easier" to use as a series because you can use it like a dictionnary with a key and a vlaue and not have to deal with the constraints of using a DatAFrame
    comparison_df = all_clients_df.copy() # Copie du DataFrame avec les colonnes de comparaison pour tout les clients de application_test

    if comparison_group_label == "Clients avec un statut familial similaire":
        client_status = client_series.get('NAME_FAMILY_STATUS')
        if client_status:
            comparison_df = all_clients_df[all_clients_df['NAME_FAMILY_STATUS'] == client_status]
            st.info(f"Filtre appliqué : comparaison avec les {len(comparison_df)} clients dont le statut est '{client_status}'.")

    elif comparison_group_label == "Clients du même genre":
        client_gender = client_series.get('CODE_GENDER')
        if client_gender and client_gender != 'XNA':
            comparison_df = all_clients_df[all_clients_df['CODE_GENDER'] == client_gender]
            st.info(f"Filtre appliqué : comparaison avec les {len(comparison_df)} clients de genre '{client_gender}'.")

    # --- PARTIE 6 : Génération et Affichage du Graphique ---
    st.subheader(f"Distribution de : {selected_variable_label}")
    
    # Obtenir la valeur spécifique du client sélectionné pour la variable choisie
    client_value = client_series.get(variable_to_compare)

    # Détecter si la variable est numérique ou catégorielle pour choisir le bon graphique
    if pd.api.types.is_numeric_dtype(comparison_df[variable_to_compare]): #vérifie si la colonne que l'utilisateur a choisi de comparer contient des nombres ou du texte. En fonction du résultat, elle choisit le bon type de graphique.
        # --- Graphique pour Variable NUMÉRIQUE (Histogramme) ---
        fig = go.Figure()

        # Trace 1: L'histogramme de la distribution du groupe
        fig.add_trace(go.Histogram(
            x=comparison_df[variable_to_compare].dropna(), # .dropna() est une sécurité
            name='Distribution du groupe',
            marker_color='#1f77b4', # Bleu
            opacity=0.75
        ))

        # Trace 2: La ligne verticale pour le client sélectionné
        if pd.notna(client_value):
            fig.add_vline(
                x=client_value,
                line_width=3,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Client {selected_client_id}",
                annotation_position="top right"
            )
        
        fig.update_layout(
            title_text=f"Distribution de '{selected_variable_label}'",
            xaxis_title=selected_variable_label,
            yaxis_title="Nombre de clients",
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)
        if pd.isna(client_value):
            st.warning(f"La valeur pour '{selected_variable_label}' n'est pas disponible pour ce client.")
        if pd.notna(client_value):
            # Format the value for better readability.
            # Use f-string formatting to handle decimals for floats and no decimals for integers.
            if isinstance(client_value, float):
                formatted_value = f"{client_value:,.2f}" # e.g., 150,000.00
            else:
                formatted_value = f"{client_value:,}" # e.g., 150,000

            # Use st.markdown for rich text formatting
            st.markdown(
                f"La valeur du client **{selected_client_id}** pour la variable **'{selected_variable_label}'** est de **<span style='color:red; font-weight:bold;'>{formatted_value}</span>**.",
                unsafe_allow_html=True
            )

    else:
        # --- Graphique pour Variable CATÉGORIELLE (Diagramme en barres) ---
        counts = comparison_df[variable_to_compare].value_counts()
        
        # Mettre en évidence la barre du client en rouge
        colors = ['red' if cat == client_value else '#1f77b4' for cat in counts.index]

        fig = go.Figure(go.Bar(
            x=counts.index,
            y=counts.values,
            marker_color=colors,
            text=counts.values,
            textposition='outside'
        ))

        fig.update_layout(
            title_text=f"Répartition par '{selected_variable_label}'",
            xaxis_title=selected_variable_label,
            yaxis_title="Nombre de clients",
            template="plotly_dark",
            xaxis={'categoryorder':'total descending'} # Ordonner les barres par taille
        )
        st.plotly_chart(fig, use_container_width=True)
        if pd.notna(client_value):
            st.markdown(f"Le client **{selected_client_id}** appartient à la catégorie **<span style='color:red; font-weight:bold;'>{client_value}</span>**.", unsafe_allow_html=True)
        else:
            st.warning(f"La catégorie pour '{selected_variable_label}' n'est pas disponible pour ce client.")

 

def show_documentation_page():
    st.title("Documentation")
    st.write("Cette page contient les instructions pour utiliser l'application.")
    st.markdown("""
    ### Comment utiliser le tableau de bord (Home)
    1.  Allez sur la page **Home**.
    2.  Utilisez le menu déroulant dans la barre latérale gauche pour sélectionner un `ID` de client.
    3.  L'application contactera l'API pour récupérer le score de crédit.
    4.  Les résultats, y compris la probabilité de remboursement et la décision finale, seront affichés.
                
    ### Comment utiliser la page Informations client
    1.  Allez sur la page **Informations client**.
    2.  Utilisez le menu déroulant dans la barre latérale gauche pour sélectionner un `ID` de client.
    3.  L'application contactera l'API pour récupérer le score de crédit.
    4.  L'application contactera l'API pour récupérer le score de crédit qui pourra être consulté sur la page **Home**
    5.  La page affichera ensuite les informations du clients.
                
    ### Comment utiliser la page Graphiques client
    1.  Allez sur la page **Graphiques client**.
    2.  Utilisez le menu déroulant dans la barre latérale gauche pour sélectionner un `ID` de client.
    3.  L'application contactera l'API pour récupérer le score de crédit qui pourra être consulté sur la page **Home**           
    4.  Utilisez le menu déroulant pour choisir une variable à comparer.
    5.  Le graphique représentant la variable sélectionnée pour le client choisi sera affichée.
    6.  Utilisez les boutons radio pour choisir à quel population de clients comparer le client.            
    7.  Le graphique sera mis à jour si une population différente est sélectionnée.
    
    ### Signification des termes
    - **Score Client (risque)** : Un score calculé par le modèle. Plus le score est élevé, plus le risque de défaut de paiement est grand.
    - **Seuil de refus** : La valeur de score au-delà de laquelle une demande de crédit est automatiquement refusée.
    - **Probabilité de Remboursement** : L'estimation de la chance que le client rembourse son prêt. C'est l'inverse du score de risque.
    """)

def show_about_page():
    st.title("À Propos de l'outil")
    st.write("Le script utilisé pour créer ce dashboard ainsi que les fonctions utilisées sont accessibles dans le repository suivant :")
    st.write("*https://github.com/MalastarLC/Streamlit_app*")
    st.markdown("---")
    st.write("Le modèle utilisé ainsi que les fichiers nécessaires pour deployer l'API sont accessibles dans le repository suivant :")
    st.write("*https://github.com/MalastarLC/Home_Credit_Project_Ver2*")

# --- 4. MAIN APP LOGIC WITH NAVIGATION ---

# Define the navigation bar
page = st_navbar(["Home", "Informations client", "Graphiques client", "Documentation", "About"])

# Création d'une sidebar centralisée ici plutot que de l'avoir dans chaque fonction pour pas qu'elle ne soit récrée et reset l'id sélectionné a chaque changement de page

st.sidebar.header("Sélection de l'ID de la demande de crédit")
available_ids = load_available_client_ids()
if not available_ids:
    st.error("Impossible de charger les IDs. L'application ne peut pas continuer.")
    st.stop()
# 1. Initialize the session state key if it's not already present.
#    This happens only on the very first run.
if 'selected_client_id' not in st.session_state:
    st.session_state.selected_client_id = available_ids[0]
# 2. Find the index of the currently "remembered" client ID.
#    This is crucial for telling the selectbox what to display.
# 3. Define the callback function.
#    This function will be called immediately when the selectbox value changes. Nous permet de pas avoir a selectionner l'id deux fois a chaque fois
def update_client_id():
    """
    Copies the value from the widget's temporary state
    to our application's master state.
    """
    st.session_state.selected_client_id = st.session_state.sidebar_selector

# How the callback works :

# User selects a new ID.
# st.session_state.sidebar_selector is updated. This is an internal Streamlit mechanism. Because the widget has a key, its value is automatically reflected in st.session_state.
# The on_change callback is executed. the update_client_id function runs before the main script rerun. This is the crucial part. It's during this callback that the line st.session_state.selected_client_id = st.session_state.sidebar_selector is executed.
# And then the full script rerun is triggered.
# Otherwise there's an issue everytime everytime we try to select an id we have to do it a second time 

# This is what happens without the callback : If we had 100002 selected and we select a new ID (100003).
# This triggers a script rerun.
# During the rerun, the selectbox code is executed. It is created using index=current_index. At this exact moment, current_index is still based on the old session state (100002).
# The assignment st.session_state.selected_client_id = ... happens, and the state is updated to 100003.
# However, for that same rerun, the selectbox widget has already been sent to the browser with instructions to display the old value.
# The rest of your script (the if page == "Home" part) correctly uses the new ID 100003, so the page content updates. But the selectbox itself visually lags behind.
# Now, on your second click, the session state is already correct (100003), so current_index is calculated correctly, and everything syncs up.



try:
    current_index = available_ids.index(st.session_state.selected_client_id) #récupere la position/index de l'id de la session state premiere position si premiere initialisation
except ValueError:
    current_index = 0  # Fallback in case the saved ID is invalid
# 4. Create the ONE and ONLY selectbox for the entire application.
#    When the user chooses a new value, we immediately assign it
#    back to our session state key, updating the "memory".
st.session_state.selected_client_id = st.sidebar.selectbox( #Ici on définit l'id
    label="Choisissez un ID:",
    options=available_ids,
    index=current_index,
    key='sidebar_selector',  # This gives the widget its own temporary key in session_state.
    on_change=update_client_id # This tells Streamlit to run our function when a change is made.  
)

# Page selection
if page == "Home":
    show_home_dashboard()
elif page == "Graphiques client":
    show_graphiques_informations_relatives_au_client()
elif page == "Informations client":
    show_informations_relatives_au_client()
elif page == "Documentation":
    show_documentation_page()
elif page == "About":
    show_about_page()
