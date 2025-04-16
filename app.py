import streamlit as st
import pandas as pd
import requests, io

@st.cache_data
def load_data():
    # Original share link
    share_url = "https://cmu.box.com/s/fcgqintnvy2tp8wvkqor1jji611cyme1"
    share_id = share_url.rstrip("/").split("/")[-1]

    # Box’s direct‑download endpoint
    dl_url = (
        "https://cmu.box.com/index.php"
        "?rm=box_download_shared_file"
        f"&shared_name={share_id}"
    )

    # 1) Fetch (follows redirects to the real file)
    resp = requests.get(dl_url)
    if resp.status_code != 200:
        st.error(f"Failed to download CSV: HTTP {resp.status_code}")
        st.stop()

    # 2) Load into pandas
    df = pd.read_csv(io.StringIO(resp.text))

    # 3) Normalize column names (as before)
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r'[\s\(\)\-]+','_', regex=True)
          .str.replace(r'[^a-z0-9_]','', regex=True)
    )
    return df

# Use it
df = load_data()
st.write("🔍 Loaded data shape:", df.shape)




