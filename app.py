import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import base64
import uuid
from transform_utils import transform_gpkg, transform_coordinates


st.set_page_config(page_title="HS2 Snake Grid (9300) and British National Grid (27700) Transformer", layout="wide")
# Ensure data/input and data/output directories exist
os.makedirs('data/input', exist_ok=True)
os.makedirs('data/output', exist_ok=True)

st.title("HS2 Snake Grid (9300) and British National Grid (27700) Transformer")

# Sidebar for input
st.sidebar.header("Input Options")
operation = st.sidebar.radio("Choose an operation:", ['Transform GeoPackage', 'Transform Coordinates'])
source_epsg = st.sidebar.selectbox("Select Source EPSG Code", [27700, 9300])
dest_epsg = st.sidebar.selectbox("Select Destination EPSG Code", [27700, 9300])

def save_uploadedfile(uploadedfile):
    with open(os.path.join('data/input', uploadedfile.name), "wb") as f:
        f.write(uploadedfile.getbuffer())
    return os.path.join('data/input', uploadedfile.name)


def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="transformed_coordinates.csv">Download CSV File</a>'
    return href

def get_file_download_link(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/gpkg;base64,{b64}" download="{os.path.basename(file_path)}">Download File</a>'
    return href

def read_geopackage(uploaded_file):
    gdf = gpd.read_file(uploaded_file)
    return gdf


if operation == 'Transform GeoPackage':
    uploaded_file = st.file_uploader("Upload a GeoPackage file", type=['gpkg'])
    if uploaded_file is not None:
        # Save uploaded file to data/input directory
        saved_path = save_uploadedfile(uploaded_file)
        gdf = gpd.read_file(saved_path)
        if st.button("Transform GeoPackage"):
            transformed_gdf = transform_gpkg(gdf, source_epsg, dest_epsg)
            st.write(transformed_gdf)

            # Generate a unique filename in the data/output directory
            unique_filename = f"data/output/transformed_{uuid.uuid4().hex}.gpkg"
            transformed_gdf.to_file(unique_filename, driver='GPKG')
            st.markdown(get_file_download_link(unique_filename), unsafe_allow_html=True)

elif operation == 'Transform Coordinates':
    coords_text = st.text_area("Enter coordinates (x, y per line, separated by commas):")
    if coords_text and st.button("Transform Coordinates"):
        # Parsing the input text to DataFrame
        data = pd.DataFrame([x.split(',') for x in coords_text.strip().split('\n')], columns=['x', 'y'])
        data = data.apply(pd.to_numeric, errors='coerce')
        transformed_data = transform_coordinates(data, source_epsg, dest_epsg)
        
        # Format and display the DataFrame
        transformed_data['transformed_x'] = transformed_data['transformed_x'].map('{:.4f}'.format)  # Adjust format as needed
        transformed_data['transformed_y'] = transformed_data['transformed_y'].map('{:.4f}'.format)
        st.write(transformed_data)
        
        # Provide download link for the transformed coordinates
        st.markdown(get_table_download_link(transformed_data), unsafe_allow_html=True)

