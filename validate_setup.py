#!/usr/bin/env python3
"""
Script de validación del setup.
Verifica que todas las dependencias y configuraciones estén correctas.
Ejecutar con: python validate_setup.py
"""

import os
import sys
import subprocess
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_check(message, passed):
    status = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
    print(f"{status} {message}")
    return passed

def check_python_dependencies():
    """Verifica que las dependencias Python estén instaladas."""
    print_header("Verificando Dependencias Python")
    
    required = [
        "flask",
        "flask_sqlalchemy",
        "flask_login",
        "flask_cors",
        "dotenv",
        "werkzeug"
    ]
    
    all_installed = True
    for package in required:
        try:
            __import__(package.replace('_', '-').replace('-', '_'))
            print_check(f"Módulo '{package}'", True)
        except ImportError:
            print_check(f"Módulo '{package}'", False)
            all_installed = False
    
    return all_installed

def check_node_dependencies():
    """Verifica que las dependencias Node.js estén instaladas."""
    print_header("Verificando Dependencias Node.js")
    
    frontend_path = Path("frontend")
    node_modules_path = frontend_path / "node_modules"
    package_json_path = frontend_path / "package.json"
    
    if not package_json_path.exists():
        print_check("package.json existe", False)
        return False
    else:
        print_check("package.json existe", True)
    
    if node_modules_path.exists():
        print_check("node_modules instalado", True)
        return True
    else:
        print_check("node_modules instalado", False)
        print(f"\n{Colors.YELLOW}💡 Consejo: Ejecuta 'npm install' en frontend/{Colors.RESET}")
        return False

def check_backend_structure():
    """Verifica la estructura del backend."""
    print_header("Verificando Estructura del Backend")
    
    backend_files = {
        "backend/app.py": "Servidor Flask",
        "backend/models.py": "Modelos SQLAlchemy",
        "backend/seed.py": "Script de datos de prueba",
        "backend/requirements.txt": "Dependencias Python",
        ".env": "Variables de entorno",
    }
    
    all_exist = True
    for file_path, description in backend_files.items():
        exists = Path(file_path).exists()
        print_check(f"{description} ({file_path})", exists)
        if not exists:
            all_exist = False
    
    return all_exist

def check_frontend_structure():
    """Verifica la estructura del frontend."""
    print_header("Verificando Estructura del Frontend")
    
    frontend_files = {
        "frontend/package.json": "Configuración NPM",
        "frontend/vite.config.js": "Configuración Vite",
        "frontend/index.html": "HTML principal",
        "frontend/src/main.js": "Entry point",
        "frontend/src/App.vue": "Componente raíz",
        "frontend/src/router/index.js": "Router",
    }
    
    all_exist = True
    for file_path, description in frontend_files.items():
        exists = Path(file_path).exists()
        print_check(f"{description} ({file_path})", exists)
        if not exists:
            all_exist = False
    
    return all_exist

def check_database():
    """Verifica que la base de datos esté creada."""
    print_header("Verificando Base de Datos")
    
    db_path = Path("backend/app.db")
    if db_path.exists():
        print_check("Base de datos (app.db) existe", True)
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"  └─ Tamaño: {size_mb:.2f} MB")
        return True
    else:
        print_check("Base de datos (app.db) existe", False)
        print(f"\n{Colors.YELLOW}💡 Consejo: Ejecuta 'python backend/seed.py'{Colors.RESET}")
        return False

def check_ports():
    """Verifica que los puertos estén disponibles."""
    print_header("Verificando Puertos Disponibles")
    
    try:
        import socket
        
        ports = {
            5000: "Backend (Flask)",
            5173: "Frontend (Vite)",
        }
        
        all_available = True
        for port, service in ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            
            available = result != 0
            print_check(f"Puerto {port} disponible ({service})", available)
            if not available:
                all_available = False
        
        return all_available
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ No se pudo verificar puertos: {e}{Colors.RESET}")
        return True

def run_validation():
    """Ejecuta todas las validaciones."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "="*58 + "╗")
    print("║" + " VALIDACIÓN DE SETUP - INGE2-APP ".center(58) + "║")
    print("╚" + "="*58 + "╝")
    print(f"{Colors.RESET}")
    
    results = {
        "Estructura Backend": check_backend_structure(),
        "Estructura Frontend": check_frontend_structure(),
        "Dependencias Python": check_python_dependencies(),
        "Dependencias Node.js": check_node_dependencies(),
        "Base de Datos": check_database(),
        "Puertos Disponibles": check_ports(),
    }
    
    print_header("Resumen de Validación")
    
    all_passed = True
    for check_name, passed in results.items():
        status = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ TODO ESTÁ CORRECTAMENTE CONFIGURADO{Colors.RESET}")
        print("\n" + Colors.GREEN + "Próximos pasos:" + Colors.RESET)
        print("  1. cd frontend && npm run dev")
        print("  2. En otra terminal: cd backend && python app.py")
        print("  3. Abre http://localhost:5173")
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠ PROBLEMAS DETECTADOS{Colors.RESET}")
        print("\n" + Colors.YELLOW + "Soluciones:" + Colors.RESET)
        
        if not results.get("Dependencias Python"):
            print("  • Ejecuta: pip install -r requirements.txt")
        
        if not results.get("Dependencias Node.js"):
            print("  • Ejecuta: cd frontend && npm install")
        
        if not results.get("Base de Datos"):
            print("  • Ejecuta: python backend/seed.py")
        
        print(f"\n• Ve a README.md para más detalles")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = run_validation()
    sys.exit(exit_code)
