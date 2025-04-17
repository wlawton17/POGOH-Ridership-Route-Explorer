import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap, MarkerCluster

st.set_page_config(page_title='POGOH Dashboard', layout='wide')
st.title('📍 POGOH Ridership Route Explorer')

@st.cache_data
def load_data():
    try:
        file_id = "1InKv_47z8tVBmqT8TBbv4xfAukGwHl2y"
        URL = "https://docs.google.com/uc?export=download"
        
        st.info("Loading data from Google Drive...")
        
        session = requests.Session()
        r = session.get(URL, params={"id": file_id}, stream=True)
        
        if r.status_code != 200:
            st.error(f"Failed to fetch data: Status code {r.status_code}")
            return None
            
        token = next((v for k, v in r.cookies.items() if k.startswith("download_warning")), None)
        if token:
            r = session.get(URL, params={"id": file_id, "confirm": token}, stream=True)
        
        try:
            df = pd.read_csv(BytesIO(r.content))
            return df
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
            return None
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Load data - no column manipulation yet
df = load_data()

# Check if data loaded
if df is None:
    st.error("Failed to load data. Please check the data source.")
    st.stop()
else:
    st.success(f"Data loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    
# Show column names for debugging
st.write("Available columns:", list(df.columns))

# Simple placeholder map for initial testing
st.subheader("🗺️ POGOH Station Map")
m = folium.Map(location=[40.4406, -79.9959], zoom_start=13)
st_folium(m, width=1000, height=600)

# Show a sample of the data 
st.subheader("📊 Data Sample")
st.dataframe(df.head(10))
