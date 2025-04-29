# Importamos las librerías necesarias

import xarray as xr
import h5netcdf
import datetime
import xesmf as xe #conda es necesario para esta linea
import numpy as np

#descarga datos
import s3fs
import os
#Reemplazar Engine y geemap
from ipyleaflet.velocity import Velocity
from ipyleaflet import Map, basemaps, ImageOverlay
from ipywidgets import Layout
from matplotlib.colors import Normalize, ListedColormap
from PIL import Image
import matplotlib.pyplot as plt
import netCDF4 as nc


# Define the function to download data based on date input
def datos_met_x_fecha(year, month, day, hour="00", frequency="01H", forecast="000", local_path=None):
    """
    Descarga datos WRF del Servicio Meteorologico Nacional desde la fecha y hora, la frecuencia de captura, y la hora del pronostico.

    Parámetros:
        year (int): Año de captura de los datos
        month (int): Mes de captura de los datos
        day (int): Día de captura de los datos
        hour (str): Hora de captura de los datos (00, 06, 12 o 18)
        frequency (str): Frecuencia de actualizacion del archivo (10M, 01H, 24H)
        forecast (str): Período Pronosticado en horas (000 - ).
        local_path (str): Local directory to save the downloaded file (default is current working directory).

    Returns:
        str: Local path of the downloaded file, or an error message if the download fails.
    """
    # Formatear con cantidad adecuada de digitos (rellenar 0 izquierda)
    year = str(year).zfill(4)
    month = str(month).zfill(2)
    day = str(day).zfill(2)
    hour = str(hour).zfill(2)
    forecast = str(forecast).zfill(3)
    
    # Habilitar valores validos de frecuencia
    if frequency not in ["10M", "01H", "24H"]:
        frequency = "01H"
    
    # Nombre del archivo
    file_name = f"WRFDETAR_{frequency}_{year}{month}{day}_{hour}_{forecast}.nc"
    print("Descargando archivo " + file_name)
    
    # Definir carpeta de descarga
    if local_path is None:
        local_path = os.getcwd()

    # Ubicacion base
    local_file_path = os.path.join(local_path, file_name)

    # Checkear si ya se descargo el archivo
    if not os.path.exists(local_file_path):
        # Generar link de descarga
        s3_link = f"s3://smn-ar-wrf/DATA/WRF/DET/{year}/{month}/{day}/{hour}/{file_name}"

        # Iniciar complemento S3 y Descargar archivo segun datos indicados
        s3 = s3fs.S3FileSystem(anon=True)
        try:
            s3.get(s3_link, local_file_path)
            print(f"El archivo se descargó correctamente: {local_file_path}")
            
        except Exception as e:
            print(f"Error: {e} \n En la descarga del archivo {s3_link}")
    # Devolver archivo de fecha indicada
    return local_file_path


