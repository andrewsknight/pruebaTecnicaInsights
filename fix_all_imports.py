#!/usr/bin/env python3
"""Script para arreglar TODAS las importaciones de una vez"""

import os
import re

def fix_imports_in_file(filepath):
    """Arregla las importaciones en un archivo"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Backup
    with open(filepath + '.bak', 'w') as f:
        f.write(content)
    
    # Patterns de importaciones relativas a arreglar
    patterns = [
        # Tres puntos
        (r'from \.\.\.infrastructure\.', 'from infrastructure.'),
        (r'from \.\.\.domain\.', 'from domain.'),
        (r'from \.\.\.application\.', 'from application.'),
        (r'from \.\.\.config\.', 'from config.'),
        
        # Dos puntos  
        (r'from \.\.infrastructure\.', 'from infrastructure.'),
        (r'from \.\.domain\.', 'from domain.'),
        (r'from \.\.application\.', 'from application.'),
        (r'from \.\.config\.', 'from config.'),
        (r'from \.\.entities\.', 'from domain.entities.'),
        (r'from \.\.services\.', 'from domain.services.'),
        (r'from \.\.repositories\.', 'from domain.repositories.'),
        
        # Un punto (dentro de domain/)
        (r'from \.entities\.', 'from domain.entities.'),
        (r'from \.services\.', 'from domain.services.'),
        (r'from \.repositories\.', 'from domain.repositories.'),
    ]
    
    # Aplicar todas las transformaciones
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Escribir el archivo arreglado
    with open(filepath, 'w') as f:
        f.write(content)
    
    return True

def create_simple_init_files():
    """Crear __init__.py files simples sin importaciones circulares"""
    
    init_files = {
        'src/__init__.py': '',
        'src/config/__init__.py': '',
        'src/domain/__init__.py': '',
        'src/domain/entities/__init__.py': '',
        'src/domain/services/__init__.py': '',
        'src/domain/repositories/__init__.py': '',
        'src/infrastructure/__init__.py': '',
        'src/infrastructure/database/__init__.py': '',
        'src/infrastructure/cache/__init__.py': '',
        'src/infrastructure/api/__init__.py': '',
        'src/application/__init__.py': '',
        'tests/__init__.py': '',
    }
    
    for filepath, content in init_files.items():
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Creado: {filepath}")
        except Exception as e:
            print(f"❌ Error creando {filepath}: {e}")

def main():
    print("🔧 Arreglando TODAS las importaciones...")
    
    # 1. Arreglar importaciones en todos los archivos .py
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                filepath = os.path.join(root, file)
                try:
                    fix_imports_in_file(filepath)
                    print(f"✅ Arreglado: {filepath}")
                except Exception as e:
                    print(f"❌ Error en {filepath}: {e}")
    
    # 2. Crear __init__.py files simples
    print("\n🔧 Creando __init__.py files simples...")
    create_simple_init_files()
    
    print("\n✅ ¡Todas las importaciones arregladas!")
    print("\nEjecuta: docker-compose restart api")

if __name__ == "__main__":
    main()