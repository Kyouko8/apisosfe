import datetime
from pprint import pprint

from providers import SOFSEApiServiceProvider, format_date, format_time, to_argtz

# Inicializar el servicio de SOFSE
sofse = SOFSEApiServiceProvider()


# Buscar estaciones y sus arribos (el token se genera y se autentica automáticamente)
def test_arrivos_estacion(nombre: str):
    estaciones = sofse.buscar_estaciones(nombre=nombre)
    # hoy = format_date(datetime.datetime.now())

    # Recorrer el listado de estaciones encontradas
    for estacion in estaciones:
        print(estacion.nombre)
        arribos = sofse.obtener_arribos(estacion.id_estacion)  # , fecha=hoy)

        # Preguntar si hay arribos para dicha estación
        if arribos.total == 0:
            print("\tNo hay arribos próximos.")
            return

        # Mostrar los arribos con sus tiempos.
        print("\tArribos\n")
        for ar in arribos.results:
            llegada = ar.arribo.llegada

            diff = llegada.diferencia_programada_estimada()
            faltante = llegada.tiempo_faltante()

            programada = format_time(to_argtz(llegada.programada))
            if programada:
                print(f"\t\tProgramado para: {programada}")

            estimada = format_time(to_argtz(llegada.estimada))
            if estimada:
                print(f"\t\tEstimado para:   {estimada}")

            if diff:
                print(f"\t\tRetrsado:        {diff}")

            if faltante:
                print(f"\t\tFaltante:        {faltante}")


if __name__ == '__main__':
    test_arrivos_estacion("San Miguel")
