import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    # Use the dl.dropboxusercontent.com domain for raw file
    url = (
        "https://dl.dropboxusercontent.com/"
        "s/9rcp9278pcbugfuh53h86/prepared_ridership_data.csv"
    )
    df = pd.read_csv(url)
    # Normalize column names
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r'[\s\(\)\-]+','_', regex=True)
          .str.replace(r'[^a-z0-9_]','', regex=True)
    )
    return df

df = load_data()



