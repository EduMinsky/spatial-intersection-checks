import geopandas as gpd
from pathlib import Path
import numpy as np
import logging
import folium
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def _ensure_spatial_obj_(obj1,obj2) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    if isinstance(obj1, gpd.GeoDataFrame) and isinstance(obj2, gpd.GeoDataFrame):
        return obj1, obj2

    if isinstance(obj1, (str, Path)) and isinstance(obj2, (str, Path)):
        path1 = Path(obj1)
        path2 = Path(obj2)
        if not (path1.exists() or not  (path2.exists())):
            raise FileNotFoundError(f"File not found")
        else:
            logger.info("Path to spatial file provided. Reading spatial data")
            return gpd.read_file(path1), gpd.read_file(path2)


    raise TypeError(
        "Input must be a GeoDataFrame or a path-like object"
    )


def _check_crs_ (obj1:gpd.GeoDataFrame,obj2:gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame ]:
    if obj1.crs is None or obj2.crs is None:
        raise ValueError("Object CRS is empty. Set a proper CRS")
    if obj1.crs.is_projected==False or obj2.crs.is_projected==False:
        raise ValueError("Object's CRS is not in meters. Spatial operations are not possible.")

    else:
        return obj1,obj2



def _equal_crs_(obj1:gpd.GeoDataFrame,obj2:gpd.GeoDataFrame)-> tuple [gpd.GeoDataFrame, gpd.GeoDataFrame]:
    if obj1.crs == obj2.crs:
        return obj1,obj2
    else:

        logger.warning("Geopandas don't have the same CRS.\n Considering the CRS from first object as the Reference CRS")

        obj2.set_crs(obj1.crs,inplace=True,allow_override=True)
        return obj1,obj2

def intersection_exploration(intersection_shapefile:gpd.GeoDataFrame,r_num:int) -> folium.folium.Map :
    """
    Performs an exploration using folium to check the result of the intersection

    Parameters
    ----------
    intersection_shapefile: Geopandas Dataframe created by the spatial_intersection_checks function
    r_num: number indicating an index of the Geopandas Dataframe
    folium Map with both polygons and its intersection
    """
    r = intersection_shapefile.iloc[[r_num,]]
    m = r.explore(
    color="red",
    style_kwds={"weight":2, "fillOpacity":0},
    name="geometry_left",
    tooltip=False,
    popup=False
                )
    r.set_geometry("geometry_right").explore(
    m=m,
    color="blue",
    style_kwds={"weight":3, "fillOpacity":0, "dashArray":"5,5"},
    name="geometry_right",
    tooltip=False,
    popup=False
)
    r.set_geometry("intersection_geom").explore(
    m=m,
    color="pink",
    style_kwds={"weight":3, "fillOpacity":0, "dashArray":"5,5"},
    name="intersection_geom",
    tooltip=False,
    popup=False
)
    folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='© OpenStreetMap contributors',
    name='Google Satellite'
    ).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def spatial_intersection_checks(shp_1: gpd.GeoDataFrame,
                                shp_2: gpd.GeoDataFrame,
                                d :float = 10.0,
                                min_area:float = 10_000.0) -> gpd.GeoDataFrame:
    """
    Perform robust spatial intersection checks between two GeoDataFrames.

    This function identifies true spatial intersections between two polygon
    datasets by combining spatial predicates, area-based filtering, and a
    morphological opening operation. The approach is designed to exclude
    false-positive intersections such as boundary touches or very thin overlaps.

    Parameters
    ----------
    shp_1 : geopandas.GeoDataFrame
    Left GeoDataFrame containing polygon geometries. The GeoDataFrame must
    have a valid, projected CRS with linear units in meters.
    shp_2 : geopandas.GeoDataFrame
    Right GeoDataFrame containing polygon geometries. The GeoDataFrame must
    have a valid, projected CRS with linear units in meters.
    d : float, default=10.0
    Distance (in meters) used to perform the morphological opening
    (erosion followed by dilation). This parameter controls the minimum
    spatial thickness required for an intersection to be considered
    structurally meaningful.
    min_area : float, default=10000.0
    Minimum intersection area (in square meters) required for an
    intersection to be considered a candidate of a true spatial overlap.
    The default value corresponds approximately to 1 hectare.

    Returns
    -------
    geopandas.GeoDataFrame
    A GeoDataFrame containing attributes from both `shp_1` and `shp_2`,
    along with additional geometry and diagnostic columns:

    - ``geometry_right`` : geometry
        Geometry from `shp_2` corresponding to each matched feature.
    - ``intersection_geom`` : geometry
        Geometry representing the spatial intersection between `shp_1`
        and `shp_2`.
    - ``intersection_geom_open`` : geometry
        Result of the morphological opening applied to the intersection
        geometry.
    - ``intersection_area`` : float
        Area of the intersection geometry, expressed in square meters.
    - ``is_valid_intersection`` : bool
        Boolean flag indicating whether the intersection satisfies the
        minimum area and morphological opening criteria. ``True`` indicates
        a valid intersection, while ``False`` indicates a likely
        false-positive (e.g., touches or thin overlaps).

    Notes
    -----
    - Both input GeoDataFrames must use a projected CRS with linear units in meters.
    - The morphological opening operation is used to remove narrow or spurious
    intersections that may arise from boundary contacts or geometric artifacts.
    - The function does not drop invalid intersections; instead, it flags them
    using the ``is_valid_intersection`` column to allow downstream filtering.

"""
    #Check if files are geopandas
    spat_obj = _ensure_spatial_obj_(obj1 = shp_1,obj2 = shp_2)
    #Check if objects have CRS:
    checkers = _check_crs_(obj1 = spat_obj[0],obj2 = spat_obj[1])
    #Check if objects have same CRS:
    same_ = _equal_crs_(obj1 = checkers[0],obj2 = checkers[1])
    shape_1 = same_[0]
    shape_2 = same_[1]
    #Calculating the true intersection
    joined = gpd.sjoin(
    shape_1,
    shape_2,
    how="inner",
    predicate="intersects"
        )
    joined["geometry_right"] = shape_2.loc[joined["index_right"], "geometry"].values
    joined["intersection_geom"] = joined.geometry.intersection(joined["geometry_right"])
    joined["intersection_geom_open"] = joined["intersection_geom"].buffer(-d).buffer(d)
    joined["intersection_area"] = joined["intersection_geom"].area
    joined["Is_valid_intersection"] = np.where(
        (~joined["intersection_geom_open"].is_empty) & (joined["intersection_area"] >= min_area),
        True,
        False
    )
    return joined



