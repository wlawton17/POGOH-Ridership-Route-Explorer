# at the top of app.py, add:
import gdown
import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    # 1) Google Drive “file” share link, not folder.
    #    Grab your FILE_ID from a link like:
    #    https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    drive_file_id = "1dCQWnJjUFme-cpcmcUvoyXDyofbXTDHb"

    # 2) Construct the “direct download” URL
    url = f"https://drive.google.com/uc?export=download&id={drive_file_id}"

    # 3) Download to a local file in the container
    output = "prepared_ridership_data.csv"
    gdown.download(url, output, quiet=False)

    # 4) Load it into pandas
    df = pd.read_csv(output)

    # 5) Normalize your column names as before
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r'[\s\(\)\-]+', '_', regex=True)
          .str.replace(r'[^a-z0-9_]', '', regex=True)
    )
    return df

df = load_data()
