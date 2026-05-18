# rag_system

# Paso 1
Descargar Ollama https://ollama.com/download/windows

Para este proyecto se usó un modelo ligero por cuestiones de memoria y falta de un hardware más sofisticado. El modelo siempre puede cambiar según las capacidades del hardware, pero para cuestiones de este proyecto el modelo llama3 resultó bastante útil.

Posterior a la instalación de ollama, configurarlo como una variable de ambiente para que funcione directo desde la terminal.

Una vez terminada la configuración, ejecutar el siguiente comando.

ollama pull llama3

# Paso 2
Ejecutar el install.bat en una terminal para instalar todas las dependencias y crear un ambiente virtual.

# Paso 3
Ejecutar el start.bat para empezar a correr el programa de instalación y configurar todo lo necesario

# Paso 4
La base de datos y los pesos para los modelos de embedding ya están descargados al clonar este proyecto. 
Si se desea reiniciar todo desde cero, borrar la carpeta data y model_cache

