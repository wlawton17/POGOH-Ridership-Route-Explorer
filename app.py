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
    file_id = "1InKv_47z8tVBmqT8TBbv4xfAukGwHl2y"
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    # 1) initial request — might get a warning page
    r = session.get(URL, params={"id": file_id}, stream=True)

    # 2) look for the "download_warning" cookie
    token = next((v for k, v in r.cookies.items() if k.startswith("download_warning")), None)

    # 3) if there is a token, re‑request with confirm=token
    if token:
        r = session.get(URL, params={"id": file_id, "confirm": token}, stream=True)

    # 4) now r.content is the raw CSV
    df = pd.read_csv(BytesIO(r.content))
    
    # Debug column names
    st.write("Original columns:", df.columns.tolist())
    
    # Rename columns to lowercase with underscores
    # Map the actual column names to the expected column names
    column_mapping = {
        'Start Station Neighborhood': 'start_station_neighborhood',
        'End Station Neighborhood': 'end_station_neighborhood'
    }
    
    # Apply the mapping for specific columns
    df = df.rename(columns=column_mapping)
    
    # For the remaining columns, apply the standard transformation
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r'[\s\(\)\-]+', '_', regex=True)
          .str.replace(r'[^a-z0-9_]', '', regex=True)
    )
    
    st.write("Cleaned columns:", df.columns.tolist())
    
    return df

df = load_data()

# Sidebar filters
with st.sidebar:
    st.header('🔍 Filters')
    
    # Handle potential missing columns
    if 'start_station_name' in df.columns:
        start_station = st.selectbox('Start Station', 
                                   ['All'] + sorted(df['start_station_name'].dropna().unique()))
    else:
        st.error("Column 'start_station_name' not found.")
        start_station = 'All'
    
    if 'end_station_name' in df.columns:
        end_station = st.selectbox('End Station', 
                                 ['All'] + sorted(df['end_station_name'].dropna().unique()))
    else:
        st.error("Column 'end_station_name' not found.")
        end_station = 'All'
    
    if 'start_station_neighborhood' in df.columns:
        start_neighborhood = st.selectbox('Start Station Neighborhood',
                                       ['All'] + sorted(df['start_station_neighborhood'].dropna().unique()))
    else:
        st.error("Column 'start_station_neighborhood' not found.")
        start_neighborhood = 'All'
    
    if 'end_station_neighborhood' in df.columns:
        end_neighborhood = st.selectbox('End Station Neighborhood',
                                     ['All'] + sorted(df['end_station_neighborhood'].dropna().unique()))
    else:
        st.error("Column 'end_station_neighborhood' not found.")
        end_neighborhood = 'All'
    
    if 'product_name' in df.columns:
        membership_types = st.multiselect('Membership Types',
                                        sorted(df['product_name'].dropna().unique()))
    else:
        st.error("Column 'product_name' not found.")
        membership_types = []
    
    if 'year' in df.columns:
        selected_years = st.multiselect('Year(s)',
                                      sorted(df['year'].dropna().unique()))
    else:
        st.error("Column 'year' not found.")
        selected_years = []
    
    if 'month' in df.columns:
        selected_months = st.multiselect('Month(s)',
                                       sorted(df['month'].dropna().unique()))
    else:
        st.error("Column 'month' not found.")
        selected_months = []
    
    if 'is_pitt_rider' in df.columns:
        pitt_filter = st.radio('Include Pitt Riders',
                             ['All', 'Only Pitt Riders', 'Exclude Pitt Riders'])
    else:
        st.error("Column 'is_pitt_rider' not found.")
        pitt_filter = 'All'
    
    if st.button('Clear Filters'):
        st.experimental_rerun()

# Apply filters
filtered = df.copy()
if start_station != 'All' and 'start_station_name' in df.columns:
    filtered = filtered[filtered['start_station_name']==start_station]
if end_station != 'All' and 'end_station_name' in df.columns:
    filtered = filtered[filtered['end_station_name']==end_station]
if start_neighborhood != 'All' and 'start_station_neighborhood' in df.columns:
    filtered = filtered[filtered['start_station_neighborhood']==start_neighborhood]
if end_neighborhood != 'All' and 'end_station_neighborhood' in df.columns:
    filtered = filtered[filtered['end_station_neighborhood']==end_neighborhood]
if membership_types and 'product_name' in df.columns:
    filtered = filtered[filtered['product_name'].isin(membership_types)]
if selected_years and 'year' in df.columns:
    filtered = filtered[filtered['year'].isin(selected_years)]
if selected_months and 'month' in df.columns:
    filtered = filtered[filtered['month'].isin(selected_months)]
if pitt_filter == 'Only Pitt Riders' and 'is_pitt_rider' in df.columns:
    filtered = filtered[filtered['is_pitt_rider']==True]
elif pitt_filter == 'Exclude Pitt Riders' and 'is_pitt_rider' in df.columns:
    filtered = filtered[filtered['is_pitt_rider']==False]

# Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Rides", f"{df.shape[0]:,}")
with col2:
    st.metric("Filtered Rides", f"{filtered.shape[0]:,}")

# Build detail_table
breakdown_cols = [col for col in ['start_station_name', 'end_station_name', 'product_name', 'is_pitt_rider'] if col in df.columns]
if not breakdown_cols:
    st.error("Required columns for breakdown not found.")
    detail_table = pd.DataFrame()
else:
    if selected_months and len(selected_months)>1 and 'month' in df.columns and 'year' in df.columns:
        filtered['period'] = filtered['month'].astype(str).str.zfill(2) + '-' + filtered['year'].astype(str)
        group_on = ['period']
    else:
        group_on = ['year'] if 'year' in df.columns else []

    if not filtered.empty and group_on:
        pivot = filtered.groupby(breakdown_cols+group_on).agg(ride_count=('rider_id','count')).reset_index()
        detail_table = pivot.pivot_table(
            index=breakdown_cols,
            columns=group_on,
            values='ride_count',
            fill_value=0
        ).reset_index()
    else:
        detail_table = pd.DataFrame()

# Map
st.subheader('🗺️ Route Map')
if not filtered.empty and all(col in filtered.columns for col in ['start_lat', 'start_lon', 'end_lat', 'end_lon']):
    mid_lat, mid_lon = filtered['start_lat'].mean(), filtered['start_lon'].mean()
else:
    mid_lat, mid_lon = 40.4406, -79.9959

m = folium.Map(location=[mid_lat, mid_lon], zoom_start=13)

# Only create routes if we have all needed columns
if not filtered.empty and all(col in filtered.columns for col in ['start_station_name', 'end_station_name', 'start_lat', 'start_lon', 'end_lat', 'end_lon']):
    route_counts = filtered.groupby(
        ['start_station_name','end_station_name','start_lat','start_lon','end_lat','end_lon']
    ).size().reset_index(name='count').sort_values('count', ascending=False).head(200)
    
    unique_stations = {}

    for _, row in route_counts.iterrows():
        # draw route lines
        folium.PolyLine(
            locations=[[row['start_lat'],row['start_lon']],[row['end_lat'],row['end_lon']]],
            color='blue', 
            weight=1+4*(row['count']-route_counts['count'].min())/(route_counts['count'].max()-route_counts['count'].min() or 1),
            opacity=0.6,
            tooltip=f"{row['start_station_name']} ➝ {row['end_station_name']} ({row['count']} trips)"
        ).add_to(m)
        unique_stations[row['start_station_name']] = (row['start_lat'],row['start_lon'])
        unique_stations[row['end_station_name']] = (row['end_lat'],row['end_lon'])

    marker_cluster = MarkerCluster().add_to(m)
    for name,(lat,lon) in unique_stations.items():
        st_count = filtered[filtered['start_station_name']==name].shape[0]
        en_count = filtered[filtered['end_station_name']==name].shape[0]
        folium.Marker([lat,lon],
            popup=f"<b>{name}</b><br>Starts: {st_count}<br>Ends: {en_count}",
            tooltip=name,
            icon=folium.Icon(icon='bicycle', prefix='fa', color='green')
        ).add_to(marker_cluster)

st_folium(m, width=1000, height=600)

# Table
st.subheader('📊 Detailed Ride Breakdown')
if detail_table.empty:
    st.write("No rides match your filter selection.")
else:
    if len(detail_table.columns) > 1:  # Make sure there's at least one data column
        last_col = detail_table.columns[-1]
        st.dataframe(
            detail_table
            .sort_values(by=last_col, ascending=False)
            .reset_index(drop=True)
        )
    else:
        st.write("No data available for table view.")
