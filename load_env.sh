#!/bin/bash
# Script para cargar variables de entorno desde archivo .env

# Comprobar si existe archivo .env
if [ -f .env ]; then
    echo "Cargando variables de entorno desde .env..."
    
    # Cargar cada línea del archivo .env que no sea un comentario
    while read -r line; do
        # Ignorar líneas vacías o comentarios
        if [[ ! $line =~ ^#.*$ ]] && [[ ! -z $line ]]; then
            export $line
            # echo "Exportada: $line"
        fi
    done < .env
    
    echo "Variables de entorno cargadas correctamente."
    
    # Mostrar estado de las API keys (ocultar valor real)
    if [ -n "$FOOTBALL_DATA_API_KEY" ]; then
        echo "FOOTBALL_DATA_API_KEY: Configurada"
    else
        echo "FOOTBALL_DATA_API_KEY: No configurada"
    fi
    
    if [ -n "$API_FOOTBALL_KEY" ]; then
        echo "API_FOOTBALL_KEY: Configurada"
    else
        echo "API_FOOTBALL_KEY: No configurada"
    fi
else
    echo "Archivo .env no encontrado."
    echo "Por favor, crea un archivo .env basado en .env.example"
fi
