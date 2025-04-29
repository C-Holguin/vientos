from import_vientos import *

#Archivo local
path = '/volumen/files/'
#filename = 'WRFDETAR_01H_20240816_06_000.nc' #modificar segun el nombre del archivo cargado en el entorno Colab.

# Extraer la parte del nombre correspondiente a la fecha y hora
#date_str = filename.split('_')[2]  # '20240816'
#hour_str = filename.split('_')[3]  # '06'




#### DESCARGA DE DATOS ####
#Obtener fecha actual UTC
fecha = datetime.datetime.now()

# Extraer fecha de archivo deseado
year = fecha.year
month = fecha.month
day = fecha.day
hour = (6*((fecha.hour-3)//6) - 6) % 24 #redondear a ultima hora Arg con datos (00, 06, 12 o 18)
forecast = 0

# Crear el objeto datetime con los datos extraídos
INIT_DATE = datetime.datetime(year, month, day, hour)

# Imprimir la fecha inicial
print(f"Fecha inicial extraída del archivo: {INIT_DATE}")


# Descargar archivo del SMN y Abrir archivo descargado
smn_nc = datos_met_x_fecha(year= year, month= month, day= day, hour= hour, forecast= forecast, local_path = path)
ds = xr.open_dataset(smn_nc, decode_coords = 'all', engine = 'h5netcdf')
print(ds)



#### CONFIGURACION DE GRILLA ####

resolution_lat = 0.1
resolution_lon = 0.1
lat_min = -56
lat_max = -19
lon_min = -76
lon_max = -48

new_grid = xe.util.grid_2d(lon_min - resolution_lon/2, lon_max, resolution_lon,
                           lat_min - resolution_lat/2, lat_max, resolution_lat)

regridder = xe.Regridder(ds, new_grid, 'bilinear')
ds_interpolated = regridder(ds, keep_attrs = True)
print(ds_interpolated)

print(ds_interpolated.head())

#guaradr archivo
ds_interpolated.to_netcdf('ds_interpolated.nc')



#### CORREGIR MAGNITUDES ####

# Abre el archivo .nc
ds = xr.open_dataset("ds_interpolated.nc")

# Asegúrate de que los datos estén en radianes
dir_rad = np.radians(ds['dirViento10'])  # Convertir grados a radianes

# Calcular componentes zonal y meridional
ds['u_wind'] = - ds['magViento10'] * np.sin(dir_rad)  # Componente Zonal (u_wind)
ds['v_wind'] = - ds['magViento10'] * np.cos(dir_rad)  # Componente Meridional (v_wind)



#### AJUSTE DIMENSIONES PARA VISUALIZACION ####

# Renombra las dimensiones de x e y a lat y lon
ds = ds.rename({"x": "longitude", "y": "latitude"})

# Asegúrate de que las coordenadas sean correctas y estén alineadas
ds = ds.assign_coords({"longitude": ds.lon.mean(dim='latitude'), "latitude": ds.lat.mean(dim='longitude')})


#guardar archivo
ds.to_netcdf('ds.nc')

#### CONECTAR A GEE ####



#### VISUALIZACION EN MAPA INTERACTIVO ####

# Ahora puedes utilizar m.add_velocity con los datos convertidos
m = Map(center=(-40, -64), zoom=4, layer_ctrl=True, basemap=basemaps.CartoDB.DarkMatter)
"""
#m.add_velocity(ds, zonal_speed='u_wind', meridional_speed='v_wind')
"""

#NUEVO
coords = list(ds.coords.keys())

m.add_layer(ds["magViento10"])
# Rasterio does not handle time or levels. So we must drop them (codigo geemap)
if "time" in coords:
    ds = ds.isel(time=0, drop=True)
m.add(Velocity(data = ds, zonal_speed = "u_wind",  meridional_speed='v_wind'))

m.save(path + f'vientos_smn_{INIT_DATE.date}.html', title='Mapa de Vientos - IGN')
