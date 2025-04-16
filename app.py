import gdown
import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    # 1) direct‐download URL for your file
    file_id = "1InKv_47z8tVBmqT8TBbv4xfAukGwHl2y"  # ← make sure this matches your Drive file
    url = f"https://drive.google.com/file/d/1InKv_47z8tVBmqT8TBbv4xfAukGwHl2y/view?usp=drive_link"

    # 2) download to local
    output = "prepared_ridership_data.csv"
    # fuzzy=True helps gdown pick up confirmation tokens for large files
    gdown.download(url, output, quiet=False, fuzzy=True)

    # 3) load into pandas
    df = pd.read_csv(output)

    # 4) normalize columns as before
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r'[\s\(\)\-]+','_', regex=True)
          .str.replace(r'[^a-z0-9_]','', regex=True)
    )
    return df

