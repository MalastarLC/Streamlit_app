import streamlit as st
import pandas as pd
import boto3
import traceback
from io import StringIO # Pour lire une chaîne de caractères comme un fichier

st.set_page_config(page_title="Debug S3 avec Boto3")
st.title("Test de Connexion S3 avec Boto3")

BUCKET_NAME = "p8-credit-dashboard-data-paris"
FILE_KEY = "data/application_test.csv"

try:
    st.write("Initialisation du client S3 avec Boto3...")
    print("DEBUG: Initialisation du client S3 avec Boto3...")
    s3_client = boto3.client('s3')
    st.success("Client S3 initialisé.")
    print("DEBUG: Client S3 initialisé.")

    st.write(f"Tentative de lecture de l'objet '{FILE_KEY}' depuis le bucket '{BUCKET_NAME}'...")
    print(f"DEBUG: Tentative de lecture de l'objet '{FILE_KEY}' depuis le bucket '{BUCKET_NAME}'...")
    
    # On lit l'objet S3 directement
    s3_object = s3_client.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
    
    st.success("s3_client.get_object() a réussi !")
    print("DEBUG: s3_client.get_object() a réussi !")

    # On lit le contenu du fichier
    file_content = s3_object['Body'].read().decode('utf-8')
    
    st.success("Lecture du contenu du fichier réussie !")
    print("DEBUG: Lecture du contenu du fichier réussie !")

    # On utilise pandas uniquement pour parser le texte déjà en mémoire
    df_sample = pd.read_csv(StringIO(file_content), nrows=5)
    
    st.success("Parsing avec Pandas réussi !")
    print("DEBUG: Parsing avec Pandas réussi !")
    st.write("Voici un échantillon des données :")
    st.dataframe(df_sample)

except Exception as e:
    st.error("Une erreur est survenue pendant l'opération S3 !")
    print("--- ERREUR CATCHÉE ---")
    print(f"Type de l'erreur: {type(e).__name__}")
    print(f"Message de l'erreur: {e}")
    print("Traceback complet:")
    traceback.print_exc()
    st.exception(e)