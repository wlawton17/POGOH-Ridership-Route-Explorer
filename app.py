import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap, MarkerCluster

st.set_page_config(page_title='POGOH Dashboard', layout='wide')
st.title('📍 POGOH Ridership Route Explorer')

@st.cache_data
def load_data():
    df = pd.read_csv('prepared_ridership_data.csv')
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r'[\\s\\(\\)\\-]+', '_', regex=True)
          .str.replace(r'[^a-z0-9_]', '', regex=True)
    )
    return df

df = load_data()

# Sidebar filters
with st.sidebar:
    st.header('🔍 Filters')
    start_station = st.selectbox('Start Station',
        ['All'] + sorted(df['start_station_name'].dropna().unique()))
    end_station = st.selectbox('End Station',
        ['All'] + sorted(df['end_station_name'].dropna().unique()))
    start_neighborhood = st.selectbox('Start Station Neighborhood',
        ['All'] + sorted(df['start_station_neighborhood'].dropna().unique()))
    end_neighborhood = st.selectbox('End Station Neighborhood',
        ['All'] + sorted(df['end_station_neighborhood'].dropna().unique()))
    membership_types = st.multiselect('Membership Types',
        sorted(df['product_name'].dropna().unique()))
    selected_years = st.multiselect('Year(s)',
        sorted(df['year'].dropna().unique()))
    selected_months = st.multiselect('Month(s)',
        sorted(df['month'].dropna().unique()))
    pitt_filter = st.radio('Include Pitt Riders',
        ['All','Only Pitt Riders','Exclude Pitt Riders'])
    if st.button('Clear Filters'):
        st.experimental_rerun()

# Apply filters
filtered = df.copy()
if start_station != 'All':
    filtered = filtered[filtered['start_station_name']==start_station]
if end_station != 'All':
    filtered = filtered[filtered['end_station_name']==end_station]
if start_neighborhood != 'All':
    filtered = filtered[filtered['start_station_neighborhood']==start_neighborhood]
if end_neighborhood != 'All':
    filtered = filtered[filtered['end_station_neighborhood']==end_neighborhood]
if membership_types:
    filtered = filtered[filtered['product_name'].isin(membership_types)]
if selected_years:
    filtered = filtered[filtered['year'].isin(selected_years)]
if selected_months:
    filtered = filtered[filtered['month'].isin(selected_months)]
if pitt_filter == 'Only Pitt Riders':
    filtered = filtered[filtered['is_pitt_rider']==True]
elif pitt_filter == 'Exclude Pitt Riders':
    filtered = filtered[filtered['is_pitt_rider']==False]

# Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Rides", f"{df.shape[0]:,}")
with col2:
    st.metric("Filtered Rides", f"{filtered.shape[0]:,}")

# Build detail_table
breakdown_cols = ['start_station_name','end_station_name','product_name','is_pitt_rider']
if selected_months and len(selected_months)>1:
    filtered['period'] = filtered['month'].astype(str).str.zfill(2) + '-' + filtered['year'].astype(str)
    group_on = ['period']
else:
    group_on = ['year']

if not filtered.empty:
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
if not filtered.empty:
    mid_lat, mid_lon = filtered['start_lat'].mean(), filtered['start_lon'].mean()
else:
    mid_lat, mid_lon = 40.4406, -79.9959

m = folium.Map(location=[mid_lat, mid_lon], zoom_start=13)
route_counts = filtered.groupby(
    ['start_station_name','end_station_name','start_lat','start_lon','end_lat','end_lon']
).size().reset_index(name='count').sort_values('count', ascending=False).head(200)
unique_stations = {}

for _, row in route_counts.iterrows():
    # draw route lines
    folium.PolyLine(
        locations=[[row['start_lat'],row['start_lon']],[row['end_lat'],row['end_lon']]],
        color='blue', weight=1+4*(row['count']-route_counts['count'].min())/(route_counts['count'].max()-route_counts['count'].min()),
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
    last_col = detail_table.columns[-1]
    st.dataframe(detail_table.sort_values(by=last_col, ascending=False).reset_index(drop=True))
