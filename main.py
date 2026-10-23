from providers import SOFSEApiServiceProvider

# Inicializar el servicio de SOFSE
sofse = SOFSEApiServiceProvider()

# Buscar estaciones (el token se genera y se autentica automáticamente)
response = sofse.buscar_estaciones(nombre="San Miguel")
print(response)
