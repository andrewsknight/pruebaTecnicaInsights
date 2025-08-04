#!/bin/bash
# Script para arreglar todas las importaciones relativas a absolutas

echo "🔧 Arreglando importaciones relativas..."

# Buscar todos los archivos .py en src/
find src -name "*.py" -type f | while read file; do
    echo "Procesando: $file"
    
    # Crear backup
    cp "$file" "$file.bak"
    
    # Arreglar importaciones relativas
    sed -i \
        -e 's/from \.\.\.infrastructure\./from infrastructure\./g' \
        -e 's/from \.\.\.domain\./from domain\./g' \
        -e 's/from \.\.\.application\./from application\./g' \
        -e 's/from \.\.\.config\./from config\./g' \
        -e 's/from \.\.infrastructure\./from infrastructure\./g' \
        -e 's/from \.\.domain\./from domain\./g' \
        -e 's/from \.\.application\./from application\./g' \
        -e 's/from \.\.config\./from config\./g' \
        -e 's/from \.\.entities\./from domain\.entities\./g' \
        -e 's/from \.\.services\./from domain\.services\./g' \
        -e 's/from \.\.repositories\./from domain\.repositories\./g' \
        -e 's/from \.entities\./from domain\.entities\./g' \
        -e 's/from \.services\./from domain\.services\./g' \
        -e 's/from \.repositories\./from domain\.repositories\./g' \
        "$file"
done

echo "✅ Importaciones arregladas!"

# Reiniciar servicio API
echo "🔄 Reiniciando servicio API..."
docker-compose restart api

echo "⏳ Esperando que el servicio inicie..."
sleep 5

# Verificar health check
echo "🏥 Verificando health check..."
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ API no responde"

echo "✅ Script completado!"