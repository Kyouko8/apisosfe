from providers import SOSFEApiServiceProvider

# Inicializar el servicio de SOFSE
sofse_api = SOSFEApiServiceProvider()

# Buscar estaciones (el token se genera y se autentica automáticamente)
response = sofse_api.buscar_estaciones(nombre="San Miguel")
print(response)
