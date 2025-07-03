# Script PowerShell para cargar variables de entorno desde archivo .env

# Comprobar si existe archivo .env
if (Test-Path -Path ".env") {
    Write-Host "Cargando variables de entorno desde .env..."
    
    # Leer el archivo .env
    $envVars = Get-Content -Path ".env"
    
    # Procesar cada línea
    foreach ($line in $envVars) {
        # Ignorar líneas vacías o comentarios
        if ($line -notmatch "^#" -and $line.Trim() -ne "") {
            # Dividir en nombre y valor
            $keyValue = $line.Split("=", 2)
            
            if ($keyValue.Length -eq 2) {
                $name = $keyValue[0].Trim()
                $value = $keyValue[1].Trim()
                
                # Eliminar comillas si existen
                if ($value -match '^"(.*)"$' -or $value -match "^'(.*)'$") {
                    $value = $Matches[1]
                }
                
                # Establecer la variable de entorno para la sesión actual
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
                # Write-Host "Exportada: $name=$value"
            }
        }
    }
    
    Write-Host "Variables de entorno cargadas correctamente."
    
    # Mostrar estado de las API keys (ocultar valor real)
    if ([string]::IsNullOrEmpty($env:FOOTBALL_DATA_API_KEY)) {
        Write-Host "FOOTBALL_DATA_API_KEY: No configurada"
    } else {
        Write-Host "FOOTBALL_DATA_API_KEY: Configurada"
    }
    
    if ([string]::IsNullOrEmpty($env:API_FOOTBALL_KEY)) {
        Write-Host "API_FOOTBALL_KEY: No configurada"
    } else {
        Write-Host "API_FOOTBALL_KEY: Configurada"
    }
} else {
    Write-Host "Archivo .env no encontrado."
    Write-Host "Por favor, crea un archivo .env basado en .env.example"
}
