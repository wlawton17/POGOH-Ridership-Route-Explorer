import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap, MarkerCluster

st.set_page_config(page_title='POGOH Dashboard', layout='wide')
st.title('📍 POGOH Ridership Route Explorer')

# Debug data loading step by step
st.write("Starting data load process...")

try:
    file_id = "1InKv_47z8tVBmqT8TBbv4xfAukGwHl2y"
    URL = "https://docs.google.com/uc?export=download"
    
    st.write(f"Request URL: {URL}?id={file_id}")
    
    session = requests.Session()
    
    # Initial request
    st.write("Making initial request...")
    r = session.get(URL, params={"id": file_id}, stream=True)
    st.write(f"Initial response status code: {r.status_code}")
    
    # Check for download warning cookie
    cookies = r.cookies.items()
    st.write(f"Cookies received: {list(cookies)}")
    
    token = next((v for k, v in cookies if k.startswith("download_warning")), None)
    st.write(f"Download token: {token}")
    
    # If token exists, make a second request
    if token:
        st.write("Making confirmed request with token...")
        r = session.get(URL, params={"id": file_id, "confirm": token}, stream=True)
        st.write(f"Confirmed response status code: {r.status_code}")
    
    # Try to read the content
    st.write(f"Response content type: {r.headers.get('Content-Type')}")
    st.write(f"Response content length: {r.headers.get('Content-Length')}")
    
    # Try to read as CSV
    st.write("Attempting to read as CSV...")
    df = pd.read_csv(BytesIO(r.content))
    
    # Check the DataFrame
    st.write(f"DataFrame loaded with shape: {df.shape}")
    
    if not df.empty:
        st.write("First few rows:")
        st.write(df.head())
        
        st.write("Columns:")
        st.write(df.columns.tolist())
    else:
        st.error("DataFrame is empty!")
        
except Exception as e:
    st.error(f"Error during data loading: {str(e)}")
    import traceback
    st.code(traceback.format_exc())

# Rest of the app will only run if data is loaded
if 'df' in locals() and not df.empty:
    st.success("Data successfully loaded!")
    
    # Just show a simple display of the data
    st.subheader("Data Preview")
    st.dataframe(df.head(10))
else:
    st.error("Cannot proceed with app - data not loaded properly.")
