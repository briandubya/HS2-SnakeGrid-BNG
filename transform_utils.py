from pyproj import Transformer, CRS
from shapely.geometry import Point, LineString, Polygon, MultiLineString
#import geopandas as gpd

def create_transformer(source_epsg, dest_epsg):
    """
    Creates a Pyproj Transformer object for the given source and destination EPSG codes.
    .gsb files are located in a 'gsb_files' directory.
    """
    # Define custom CRS with EPSG parameters and NTV2 grid files
    if source_epsg == 27700:
        source_crs = CRS.from_proj4("+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 "
                                    "+x_0=400000 +y_0=-100000 +ellps=airy "
                                    "+nadgrids=./gsb_files/OSTN15_NTv2_OSGBtoETRS.gsb +units=m +no_defs")
    elif source_epsg == 9300:
        source_crs = CRS.from_proj4("+proj=tmerc +lat_0=52.3 +lon_0=-1.5 +k=1 "
                                    "+x_0=198873.0046 +y_0=375064.3871 +ellps=GRS80 "
                                    "+nadgrids=./gsb_files/HS2TN15_NTv2.gsb +units=m +no_defs")

    if dest_epsg == 27700:
        dest_crs = CRS.from_proj4("+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 "
                                  "+x_0=400000 +y_0=-100000 +ellps=airy "
                                  "+nadgrids=./gsb_files/OSTN15_NTv2_OSGBtoETRS.gsb +units=m +no_defs")
    elif dest_epsg == 9300:
        dest_crs = CRS.from_proj4("+proj=tmerc +lat_0=52.3 +lon_0=-1.5 +k=1 "
                                  "+x_0=198873.0046 +y_0=375064.3871 +ellps=GRS80 "
                                  "+nadgrids=./gsb_files/HS2TN15_NTv2.gsb +units=m +no_defs")

    return Transformer.from_crs(source_crs, dest_crs, always_xy=True)

def transform_coordinates(data, source_epsg, dest_epsg):
    """
    Transforms coordinates in a DataFrame from source EPSG to destination EPSG.
    """
    transformer = create_transformer(source_epsg, dest_epsg)
    transformed_data = data.apply(lambda row: transformer.transform(row['x'], row['y']), axis=1, result_type='expand')
    transformed_data.columns = ['transformed_x', 'transformed_y']
    
    # Convert to float
    transformed_data['transformed_x'] = transformed_data['transformed_x'].astype(float)
    transformed_data['transformed_y'] = transformed_data['transformed_y'].astype(float)
    
    return transformed_data

def transform_gpkg(input_gdf, source_epsg, dest_epsg):
    transformer = create_transformer(source_epsg, dest_epsg)
    input_gdf['geometry'] = input_gdf['geometry'].apply(lambda geom: transform_geom(geom, transformer))
    return input_gdf

def transform_geom(geometry, transformer):
    """
    Applies a transformation to a single geometry object.
    """
    if geometry.is_empty:
        return geometry
    elif isinstance(geometry, Point):
        return transform_point(geometry, transformer)
    elif isinstance(geometry, LineString):
        return transform_linestring(geometry, transformer)
    elif isinstance(geometry, Polygon):
        return transform_polygon(geometry, transformer)
    elif isinstance(geometry, MultiLineString):
        return MultiLineString([transform_linestring(line, transformer) for line in geometry.geoms])
    else:
        raise ValueError(f"Unsupported geometry type: {type(geometry)}")

def transform_point(point, transformer):
    x, y = transformer.transform(point.x, point.y)
    return Point(x, y)

def transform_linestring(linestring, transformer):
    transformed_points = [transformer.transform(*point) for point in linestring.coords]
    return LineString(transformed_points)

def transform_polygon(polygon, transformer):
    exterior = transform_linestring(polygon.exterior, transformer)
    interiors = [transform_linestring(ring, transformer) for ring in polygon.interiors]
    return Polygon(exterior, interiors)