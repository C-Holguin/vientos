from import_vientos_v4 import *


#Archivo local
path = '/volumen/files/'


#### DESCARGA DE DATOS ####
#Obtener fecha actual UTC
fecha = datetime.datetime.now()

# Extraer fecha de archivo deseado
year = 2024#fecha.year
month = 10#fecha.month
day = 31#fecha.day
hour = 0#(6*((fecha.hour-3)//6) - 6) % 24 #redondear a ultima hora Arg con datos (00, 06, 12 o 18)
forecast = 0

# Crear el objeto datetime con los datos extraídos
INIT_DATE = datetime.datetime(year, month, day, hour)

# Imprimir la fecha inicial
print(f"Fecha inicial extraída del archivo: {INIT_DATE}")


# Descargar archivo del SMN y Abrir archivo descargado
#smn_nc = datos_met_x_fecha(year= year, month= month, day= day, hour= hour, forecast= forecast, local_path = path)
#ds = xr.open_dataset(smn_nc, decode_coords = 'all', engine = 'h5netcdf')
file = '/volumen/files/Almacenamiento/Aggregated_Data_compressed9.nc'
ds = xr.open_dataset(file, decode_coords = 'all', engine = 'h5netcdf')

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

#guardar archivo
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
##Cambiar dimensiones a latitude y longitude para funcion fuera de engine
ds = ds.rename({"x": "longitude", "y": "latitude"})

# Asegúrate de que las coordenadas sean correctas y estén alineadas
ds = ds.assign_coords({"longitude": ds.lon.mean(dim='latitude'), "latitude": ds.lat.mean(dim='longitude')})


#guardar archivo
ds.to_netcdf('ds.nc')



#### CONECTAR A GEE ####
##Eliminado



#### VISUALIZACION EN MAPA INTERACTIVO ####

## Cargar mapa base de ipyleaflet
m = Map(center=(-37.5, -62), zoom=5, layout= Layout(height ='100vh'), layer_ctrl=True, basemap=basemaps.CartoDB.DarkMatter)

##Codigo geemap para cargar datos .nc (https://geemap.org/geemap/?h=add_velocity#geemap.geemap.Map.add_velocity)


ds = ds.sel(time=INIT_DATE).squeeze()###ELIMINAR

##Eliminar dimension time para que funcione codigo
#if "time" in list(ds.coords.keys()):
#    ds = ds.isel(time=INIT_DATE, drop=True)


# Normalizar para colormap [0, 1]
norm = Normalize(vmin = 0, vmax = 50, clip = True)

#Mapa de color
#colores = ["#5e5a77", "#5b5b9d", "#4285ba", "#51ac92", "#4dc14a", "#90cb4d", "#cbd73f", "#d9c03e", "#d89d46", "#d4774b", "#cb4a73", "#a3355b", "#901c4f", "#631a1b", "#2b0001", "#000000", "#000000", "#000000", "#000000"]
#cmap = ListedColormap(colores)

# Crear mapa de fondo desde magnitud del viento
fig, ax = plt.subplots(figsize=(8, 6))
mesh = ax.pcolormesh(ds['lon'].values, ds['lat'].values, norm(ds['magViento10'].values), cmap = "viridis", shading='auto')
ax.axis('off')  

# Exportar como .png
img_name = "fondo_viento.png"
plt.savefig(path + img_name, format="png", bbox_inches='tight', pad_inches=0)
plt.close(fig)


# 2. Cargar .png a mapa ipyleaflef con coordenadas limite
m.add_layer(ImageOverlay(url=img_name, bounds=[[lat_min, lon_min], [lat_max, lon_max]], opacity=0.6)) 

##Generar mapa de velocidad de viento
m.add(Velocity(data = ds, zonal_speed = "u_wind",  meridional_speed='v_wind', velocity_scale = 0.005, color_scale = "white")) #velocity_scale cambia largo de lineas graficadas

##Exportar mapa a html
archivo = path + f'vientos_smn_{INIT_DATE.date()}_{INIT_DATE.hour}.html'
m.save(archivo, title='Mapa de Vientos - IGN')
