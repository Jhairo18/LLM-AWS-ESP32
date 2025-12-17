import streamlit as st
from datetime import datetime
from datos_dynamo import datos_limpios
from lang import respuesta_agente
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

# Cargar los datos limpios desde DynamoDB
df = datos_limpios()

# Crear input de texto para que el usuario ingrese su instrucción
texto_entry = st.text_input("Dame una instruccion")

# Crear botón para enviar la instrucción
boton = st.button("Enviar")

# Mostrar el dataframe con los datos cargados
st.dataframe(df)
st.set_page_config(page_title="Análisis y Visualización de Datos")

# Verificar si hay texto ingresado y si se presionó el botón
if texto_entry is not None and boton:
    # Enviar la instrucción al agente y obtener respuesta
    respuesta = respuesta_agente(texto_entry)
    
    # Verificar si la respuesta es de tipo gráfico
    if respuesta['tipo'] == 'grafico':
        # Mostrar mensaje de éxito
        st.success("✅ Gráfico generado exitosamente")
        
        # Crear dos columnas: una para explicación (1/3) y otra para gráfico (2/3)
        col1, col2 = st.columns([1, 2])        
        
        # Columna izquierda: mostrar explicación
        with col1:
            st.markdown("### 📝 Explicación")
            # Mostrar la explicación del gráfico o mensaje por defecto
            st.info(respuesta.get('explicacion', 'Gráfico generado'))
                    
            # # Crear un expander para mostrar el código generado
            # with st.expander("🔍 Ver código generado"):
            #     st.code(respuesta['codigo'], language='python')
        
        # Columna derecha: mostrar el gráfico
        with col2:
            st.markdown("### 📊 Visualización") 
            
            # Intentar ejecutar el código del gráfico
            try:
                # Limpiar el código: remover plt.show() que no es necesario en Streamlit
                codigo_limpio = respuesta['codigo'].replace("plt.show()", "")
                
                # Reemplazar conversión de fechas para manejar errores y formato específico
                codigo_limpio = codigo_limpio.replace(
                    "pd.to_datetime(df['fecha'])",
                    "pd.to_datetime(df['fecha'], format='%Y-%m-%d %H:%M:%S', errors='coerce')"
                )
                
                # Ejecutar el código de generación del gráfico
                exec(codigo_limpio) 
                
                # Obtener la figura actual de matplotlib
                fig = plt.gcf()
                
                # Ajustar el layout para mejor visualización
                plt.tight_layout()
                
                # Mostrar el gráfico en Streamlit
                st.pyplot(fig)
                
                # Cerrar la figura para liberar memoria
                plt.close(fig)
                        
            except Exception as e:
                # Si hay un error, mostrar mensaje y el código que falló
                st.error(f"❌ Error al generar el gráfico: {str(e)}")
                st.code(respuesta['codigo'], language='python')
        with st.expander("🔍 Ver código generado"):
            st.code(respuesta['codigo'], language='python')
    else:  # Si la respuesta es de tipo análisis estadístico
        # Mostrar mensaje de éxito
        st.success("✅ Análisis completado")
        
        # Título de la sección
        st.markdown("### 📈 Resultado del Análisis")
        
        # Mostrar la pregunta original del usuario
        st.markdown(f"**Pregunta:** {respuesta['input']}")
        
        # Mostrar la respuesta del análisis en un contenedor destacado
        st.info(respuesta['respuesta'])