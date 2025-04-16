import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    # Direct‑download link to your Dropbox CSV (dl=1 forces download)
    url = "https://www.dropbox.com/scl/fi/9rcp9278pcbugfuh53h86/prepared_ridership_data.csv?dl=1"
    # Read it straight into pandas
    df = pd.read_csv(url)
    # Normalize column names
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r'[\s\(\)\-]+', '_', regex=True)
          .str.replace(r'[^a-z0-9_]', '', regex=True)
    )
    return df

# Replace your old local‑file call with this
df = load_data()


