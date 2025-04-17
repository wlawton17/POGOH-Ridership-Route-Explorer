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
        
        # Check if request was successful
        if r.status_code != 200:
            st.error(f"Failed to fetch data: Status code {r.status_code}")
            return pd.DataFrame()  # Return empty DataFrame
            
        # Handle large file download (with confirm token)
        token = next((v for k, v in r.cookies.items() if k.startswith("download_warning")), None)
        if token:
            r = session.get(URL, params={"id": file_id, "confirm": token}, stream=True)
        
        # Read CSV
        try:
            df = pd.read_csv(BytesIO(r.content))
            st.success(f"Data loaded successfully with {df.shape[0]} rows and {df.shape[1]} columns")
            
            # Display column names for debugging
            st.write("Available columns:", df.columns.tolist())
            
            # Clean column names
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
                .str.replace(r'[\s\(\)\-]+', '_', regex=True)
                .str.replace(r'[^a-z0-9_]', '', regex=True)
            )
            
            # Display cleaned column names
            st.write("Cleaned columns:", df.columns.tolist())
            
            return df
            
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
            # Try to show the first part of the content for debugging
            st.text("First 1000 bytes of content:")
            st.text(r.content[:1000])
            return pd.DataFrame()  # Return empty DataFrame
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame

# Load data
df = load_data()

# Check if data loaded successfully
if df.empty:
    st.error("Failed to load data. Please check the data source.")
    st.stop()  # Stop execution

# Expected column names after cleaning
expected_columns = [
    'start_station_name', 
    'end_station_name', 
    'start_station_neighborhood', 
    'end_station_neighborhood',
    'product_name',
    'year',
    'month',
    'is_pitt_rider',
    'start_lat',
    'start_lon',
    'end_lat',
    'end_lon',
    'rider_id'
]

# Check for missing columns
missing_columns = [col for col in expected_columns if col not in df.columns]
if missing_columns:
    st.error(f"Missing expected columns: {', '.join(missing_columns)}")
    
    # Try to handle common column naming issues
    if 'start_station_name' not in df.columns and 'start_station_id' in df.columns:
        st.info("Using start_station_id as start_station_name")
        df['start_station_name'] = df['start_station_id']
    
    if 'end_station_name' not in df.columns and 'end_station_id' in df.columns:
        st.info("Using end_station_id as end_station_name")
        df['end_station_name'] = df['end_station_id']
    
    # Create placeholder columns for any still missing
    for col in missing_columns:
        if col not in df.columns:
            st.info(f"Creating placeholder for {col}")
            df[col] = "Unknown" if col.endswith('name') else 0

# Sidebar filters
with st.sidebar:
    st.header('🔍 Filters')
    
    start_station = st.selectbox('Start Station', 
                              ['All'] + sorted(df['start_station_name'].dropna().unique().tolist()))
    
    end_station = st.selectbox('End Station', 
                            ['All'] + sorted(df['end_station_name'].dropna().unique().tolist()))
    
    start_neighborhood = st.selectbox('Start Station Neighborhood',
                                   ['All'] + sorted(df['start_station_neighborhood'].dropna().unique().tolist()))
    
    end_neighborhood = st.selectbox('End Station Neighborhood',
                                 ['All'] + sorted(df['end_station_neighborhood'].dropna().unique().tolist()))
    
    membership_types = st.multiselect('Membership Types',
                                    sorted(df['product_name'].dropna().unique().tolist()))
    
    selected_years = st.multiselect('Year(s)',
                                  sorted(df['year'].dropna().unique().tolist()))
    
    selected_months = st.multiselect('Month(s)',
                                   sorted(df['month'].dropna().unique().tolist()))
    
    pitt_filter = st.radio('Include Pitt Riders',
                         ['All', 'Only Pitt Riders', 'Exclude Pitt Riders'])
    
    if st.button('Clear Filters'):
        st.experimental_rerun()

# Apply filters
filtered = df.copy()
if start_station != 'All':
    filtered = filtered[filtered['start_station_name'] == start_station]
if end_station != 'All':
    filtered = filtered[filtered['end_station_name'] == end_station]
if start_neighborhood != 'All':
    filtered = filtered[filtered['start_station_neighborhood'] == start_neighborhood]
if end_neighborhood != 'All':
    filtered = filtered[filtered['end_station_neighborhood'] == end_neighborhood]
if membership_types:
    filtered = filtered[filtered['product_name'].isin(membership_types)]
if selected_years:
    filtered = filtered[filtered['year'].isin(selected_years)]
if selected_months:
    filtered = filtered[filtered['month'].isin(selected_months)]
if pitt_filter == 'Only Pitt Riders':
    filtered = filtered[filtered['is_pitt_rider'] == True]
elif pitt_filter == 'Exclude Pitt Riders':
    filtered = filtered[filtered['is_pitt_rider'] == False]

# Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Rides", f"{df.shape[0]:,}")
with col2:
    st.metric("Filtered Rides", f"{filtered.shape[0]:,}")

# Build detail_table
breakdown_cols = [col for col in ['start_station_name', 'end_station_name', 'product_name', 'is_pitt_rider'] 
                 if col in df.columns]

if not breakdown_cols:
    st.warning("Missing columns required for breakdown table")
    detail_table = pd.DataFrame()
else:
    if selected_months and len(selected_months)>1 and 'month' in df.columns and 'year' in df.columns:
        filtered['period'] = filtered['month'].astype(str).str.zfill(2) + '-' + filtered['year'].astype(str)
        group_on = ['period']
    else:
        group_on = ['year'] if 'year' in df.columns else []

    if not filtered.empty and group_on:
        try:
            pivot = filtered.groupby(breakdown_cols+group_on).agg(ride_count=('rider_id','count')).reset_index()
            detail_table = pivot.pivot_table(
                index=breakdown_cols,
                columns=group_on,
                values='ride_count',
                fill_value=0
            ).reset_index()
        except Exception as e:
            st.error(f"Error creating breakdown table: {str(e)}")
            detail_table = pd.DataFrame()
    else:
        detail_table = pd.DataFrame()

# Map
st.subheader('🗺️ Route Map')
if not filtered.empty and all(col in filtered.columns for col in ['start_lat', 'start_lon', 'end_lat', 'end_lon']):
    mid_lat, mid_lon = filtered['start_lat'].mean(), filtered['start_lon'].mean()
else:
    mid_lat, mid_lon = 40.4406, -79.9959  # Default Pittsburgh coordinates

m = folium.Map(location=[mid_lat, mid_lon], zoom_start=13)

# Only create routes if we have all needed columns and data
if not filtered.empty and all(col in filtered.columns for col in 
                             ['start_station_name', 'end_station_name', 'start_lat', 'start_lon', 'end_lat', 'end_lon']):
    try:
        route_counts = filtered.groupby(
            ['start_station_name','end_station_name','start_lat','start_lon','end_lat','end_lon']
        ).size().reset_index(name='count').sort_values('count', ascending=False).head(200)
        
        unique_stations = {}

        for _, row in route_counts.iterrows():
            # Calculate route line weight (avoid division by zero)
            min_count = route_counts['count'].min()
            max_count = route_counts['count'].max()
            weight_factor = 1
            if max_count > min_count:
                weight_factor = 1 + 4 * (row['count'] - min_count) / (max_count - min_count)
            
            # Draw route lines
            folium.PolyLine(
                locations=[[row['start_lat'],row['start_lon']],[row['end_lat'],row['end_lon']]],
                color='blue',
                weight=weight_factor,
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
    except Exception as e:
        st.error(f"Error creating map: {str(e)}")
else:
    st.warning("Missing required location data for map visualization")

st_folium(m, width=1000, height=600)

# Table
st.subheader('📊 Detailed Ride Breakdown')
if detail_table.empty:
    st.write("No rides match your filter selection or data is missing required columns.")
else:
    try:
        if len(detail_table.columns) > 1:  # Make sure there's at least one data column
            last_col = detail_table.columns[-1]
            st.dataframe(
                detail_table
                .sort_values(by=last_col, ascending=False)
                .reset_index(drop=True)
            )
        else:
            st.write("Insufficient data for detailed breakdown.")
    except Exception as e:
        st.error(f"Error displaying table: {str(e)}")
