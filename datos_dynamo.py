import pandas as pd
import boto3

# Crear recurso de DynamoDB para interactuar con AWS
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-2'  # Región de AWS donde está la tabla (ajustar según necesidad)
)

# Obtener referencia a la tabla de DynamoDB
table = dynamodb.Table('DatosSensorMqtt')  # Nombre de la tabla en DynamoDB


def obtener_datos():
    """
    Obtiene todos los registros de la tabla DynamoDB mediante un scan.
    
    Returns:
        list: Lista de diccionarios con los items de la tabla
    
    Nota: scan() puede ser costoso en tablas grandes, considera usar query() 
    con índices si la tabla crece mucho.
    """
    response = table.scan()
    return response["Items"]


def datos_limpios():
    """
    Obtiene los datos de DynamoDB, los limpia y los estructura en un DataFrame.
    
    Proceso:
    1. Obtiene datos crudos de DynamoDB
    2. Transforma cada registro a un formato estandarizado
    3. Convierte a DataFrame de pandas
    4. Parsea las fechas al formato datetime
    5. Ordena por fecha de forma ascendente
    
    Returns:
        pd.DataFrame: DataFrame con columnas 'fecha', 'temperatura' y 'humedad',
                      ordenado cronológicamente
    """
    # Obtener datos crudos de DynamoDB
    data = obtener_datos()
    
    # Limpiar y estructurar los datos en una lista de diccionarios
    data_limpia = [
        {
            "fecha": d["id"],  # El id contiene la fecha en formato string
            "temperatura": float(d["temperatura"]),  # Convertir a float
            "humedad": float(d["humedad"])  # Convertir a float
        }
        for d in data
    ]
    
    # Crear DataFrame de pandas
    df = pd.DataFrame(data_limpia)
    
    # Convertir columna 'fecha' de string a datetime
    # format: especifica el formato de entrada
    # errors='coerce': convierte valores inválidos a NaT (Not a Time)
    df["fecha"] = pd.to_datetime(
        df["fecha"],
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce"
    )

    # Ordenar DataFrame por fecha de forma ascendente y resetear el índice
    df = df.sort_values(by="fecha").reset_index(drop=True)
    df["diff"] = df["temperatura"].diff().abs()
    df = df[df["diff"] < 2]
    df = df.drop(columns=["diff"]).reset_index(drop=True)

    df["diff"] = df["humedad"].diff().abs()
    df = df[df["diff"] < 5]
    df = df.drop(columns=["diff"]).reset_index(drop=True)
    return df


# Bloque que se ejecuta solo cuando el script corre directamente (no al importar)
if __name__ == "__main__":
    # Obtener datos limpios y ordenados
    df = datos_limpios()
    df.to_csv("datos_limpios.csv", index=False)
    # Mostrar los últimos 5 registros para verificación
    print(df.tail())