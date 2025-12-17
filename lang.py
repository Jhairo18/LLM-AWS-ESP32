from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import initialize_agent, Tool
from dotenv import load_dotenv
from matplotlib import pyplot as plt
from datos_dynamo import datos_limpios

# Cargar variables de entorno desde archivo .env (contiene API keys)
load_dotenv()

# Obtener datos limpios y ordenados desde DynamoDB
df = datos_limpios()
info_df = df.info()
# Inicializar el modelo de lenguaje OpenAI
llm = ChatOpenAI(
    temperature=0.3, 
    model_name="gpt-4o-mini", 
    verbose=True,
    streaming=True
)

# Crear agente especializado en análisis de DataFrames de pandas
agent = create_pandas_dataframe_agent(
    llm, 
    df, 
    agent_type="openai-functions",
    verbose=False, 
    allow_dangerous_code=True,
    handle_parsing_errors=True
)


def analizar_datos(prompt):

    return agent.invoke(prompt)


def graficar_datos(prompt):

    # Prompt específico que fuerza al modelo a generar solo código
    respuesta = agent.invoke(
        f"Genera SOLO código matplotlib en Python, no generes otro texto mas es estricto para: {prompt} "
        f"haz que se vea ordenado, no generes solamente dame el codigo"
        f"Tendras una columna llamada fecha que tiene el formato %Y-%m-%d %H:%M:%S, asegúrate de usarla correctamente en el eje x y filtrar la fecha de acuerdo al prompt"
        f"Si te pido dos graficas (menciono temperatura y humedad), haz subplots, en caso contrario haz un solo plot."
    )
    
    # Extraer el código de la respuesta (puede venir en diferentes formatos)
    if isinstance(respuesta, dict) and "output" in respuesta:
        codigo = respuesta["output"]
    else:
        codigo = str(respuesta)
    
    # Limpiar el código: remover markdown de bloques de código
    codigo = codigo.replace("```python", "").replace("```", "").strip()
    
    # Retornar código con marcadores especiales para identificación
    # Esto permite al sistema principal distinguir entre análisis y gráficos
    return f"CODIGO_MATPLOTLIB_START\n{codigo}\nCODIGO_MATPLOTLIB_END"


# Definir herramientas disponibles para el agente principal
tools = [
    Tool(
        name="Analizador de Datos",
        func=analizar_datos,
        description="Utiliza esto para responder preguntas estadísticas, cálculos, medias, sumas, conteos, etc. sobre los datos."
    ),
    Tool(
        name="Graficador de Datos",
        func=graficar_datos,
        description="Utiliza esto SOLO cuando el usuario pida explícitamente un gráfico, visualización, plot o comparación visual."
    )
]   


def respuesta_agente(prompt):

    # Inicializar agente principal con estrategia "zero-shot-react-description"
    # Esta estrategia permite al agente razonar y seleccionar herramientas dinámicamente
    agente_principal = initialize_agent(
        tools, 
        llm, 
        agent="zero-shot-react-description",  
        verbose=True,  
        return_intermediate_steps=True, 
        hasattr_parsing_errors=True  
    )
    
    # Ejecutar el prompt y obtener resultado con pasos intermedios
    resultado = agente_principal.invoke(prompt)
    
    # Extraer los pasos intermedios (acciones y observaciones del agente)
    steps = resultado.get('intermediate_steps', [])
    
    # Iterar sobre cada paso para buscar código de gráfico
    for action, observation in steps:
        # Convertir observación a string para búsqueda
        obs_str = str(observation)
        
        # Verificar si se generó código matplotlib (mediante el marcador)
        if 'CODIGO_MATPLOTLIB_START' in obs_str:
            # Extraer el código entre los marcadores especiales
            codigo = obs_str.split('CODIGO_MATPLOTLIB_START')[1].split('CODIGO_MATPLOTLIB_END')[0].strip()
            
            # Retornar formato para gráfico
            return {
                'tipo': 'grafico',
                'codigo': codigo,  # Código matplotlib listo para ejecutar
                'explicacion': resultado.get('output', 'Gráfico generado'),
                'input': prompt  # Pregunta original del usuario
            }
    
    # Si no se encontró código de gráfico, es un análisis estadístico
    return {
        'tipo': 'analisis',
        'respuesta': resultado.get('output', ''),  # Respuesta textual del análisis
        'input': prompt  # Pregunta original del usuario
    }

 
if __name__ == "__main__":
    # resultado = respuesta_agente("dame un grafico q compara la temperatura con la hora") 
    print(df.tail())
