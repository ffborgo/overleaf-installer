import os
import sys
import subprocess
import secrets
import shutil
import re
import time
import webbrowser
import socket

# ============================================
# 🎨 COLORES Y FORMATO
# ============================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def print_step(msg):
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}🚀 {msg}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")

    @staticmethod
    def print_success(msg):
        print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")

    @staticmethod
    def print_error(msg):
        print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

    @staticmethod
    def print_info(msg):
        print(f"{Colors.BLUE}ℹ️  {msg}{Colors.ENDC}")

    @staticmethod
    def print_warning(msg):
        print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")

# ============================================
# ⚙️ CONFIGURACIÓN
# ============================================
REPO_URL = "https://github.com/overleaf/toolkit.git"
DIR_NAME = "overleaf-toolkit"
DEFAULT_PORT = 8080

# ============================================
# 🛠️ FUNCIONES DE UTILIDAD
# ============================================

def check_command(command):
    return shutil.which(command) is not None

def check_docker_running():
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

def get_docker_compose_cmd():
    try:
        subprocess.run(["docker", "compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ["docker", "compose"]
    except Exception:
        pass
    
    if check_command("docker-compose"):
        return ["docker-compose"]
    return None

def validate_input(input_str):
    """
    Validación Robusta (Mejora de Seguridad):
    1. Separa el puerto si existe.
    2. Verifica si es una IPv4 válida estrictamente.
    3. O verifica si es un Hostname válido (RFC 1123) para dominios/MagicDNS.
    """
    # Separar puerto
    host_part = input_str
    if ":" in input_str:
        host_part, port_part = input_str.split(":", 1)
        if not port_part.isdigit() or not (1 <= int(port_part) <= 65535):
            return None
    
    # 1. Regex estricta para IPv4
    ipv4_regex = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if re.match(ipv4_regex, host_part):
        return input_str

    # 2. Regex estricta para Hostnames (letras, números, guiones, puntos)
    # Permite 'mi-pc', 'localhost', 'server.tailscale.net'
    hostname_regex = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])$"
    if re.match(hostname_regex, host_part):
        return input_str
        
    return None

def check_port_availability(port):
    """Verifica si un puerto está disponible."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) != 0

def get_port():
    """Solicita al usuario un puerto y lo valida."""
    while True:
        port_str = input(f"👉 Introduce el puerto a usar (Enter para {DEFAULT_PORT}): ").strip()
        if not port_str:
            return DEFAULT_PORT
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                return port
            else:
                Colors.print_warning("El puerto debe estar entre 1 y 65535.")
        except ValueError:
            Colors.print_warning("Por favor, introduce un número válido.")

def get_tailscale_ip():
    """Intenta obtener la IP de Tailscale en Linux."""
    if not sys.platform.startswith("linux"):
        return ""
    try:
        # Ejecuta 'tailscale ip -4' y captura la salida
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Si el comando falla o no se encuentra, no hace nada
        return ""

# ============================================
# 🌐 GESTIÓN DE TAILSCALE
# ============================================

def handle_tailscale_linux():
    Colors.print_info("Linux detectado. Iniciando instalación segura...")
    url = "https://tailscale.com/install.sh"
    local_script = "/tmp/tailscale_install.sh"

    try:
        subprocess.run(["curl", "-fsSL", "-o", local_script, url], check=True)
        os.chmod(local_script, 0o700)
        subprocess.run([local_script], check=True)
        
        Colors.print_success("Tailscale instalado.")
        Colors.print_warning("ACCIÓN REQUERIDA: Ejecuta 'sudo tailscale up' en otra terminal.")
        input(f"{Colors.BOLD}Presiona ENTER cuando estés conectado y tengas tu IP...{Colors.ENDC}")
    except subprocess.CalledProcessError:
        Colors.print_error("Falló la instalación automática.")

def handle_tailscale_windows():
    Colors.print_info("Windows detectado.")
    print("\n👉 Abriendo página de descarga...")
    time.sleep(1)
    webbrowser.open("https://tailscale.com/download/windows")
    input(f"\n{Colors.BOLD}Presiona ENTER cuando tengas Tailscale listo y conectado...{Colors.ENDC}")

# ============================================
# 📦 CLONADO Y SEGURIDAD
# ============================================

def git_clone_and_verify():
    if not os.path.exists(DIR_NAME):
        Colors.print_step("Clonando Overleaf Toolkit...")
        try:
            subprocess.run(["git", "clone", REPO_URL, DIR_NAME], check=True)
        except subprocess.CalledProcessError:
            Colors.print_error("No se pudo clonar el repositorio. Revisa tu internet.")
            sys.exit(1)
    else:
        Colors.print_info(f"La carpeta '{DIR_NAME}' ya existe. Usando versión actual.")

    os.chdir(DIR_NAME)

# ============================================
# 📝 CONFIGURACIÓN DEL ENTORNO
# ============================================

def create_env_file(domain_url):
    if os.path.exists("overleaf.env"):
        Colors.print_info("El archivo .env ya existe. No se sobrescribirá.")
        return

    Colors.print_step("Generando secretos criptográficos (.env)")

    session_secret = secrets.token_hex(32)
    jwt_secret = secrets.token_hex(32)

    content = f"""# Generado automáticamente
SHARELATEX_CONFIG=config/overleaf.cfg
SHARELATEX_APP_NAME=Overleaf Community Edition
SHARELATEX_URL=http://{domain_url}
SHARELATEX_SESSION_SECRET={session_secret}
SHARELATEX_JWT_SECRET={jwt_secret}
MONGO_URL=mongodb://mongo/sharelatex
REDIS_HOST=redis
REDIS_PORT=6379
"""

    with open("overleaf.env", "w") as f:
        f.write(content)
        f.flush()
        
        if hasattr(os, 'fchmod'):
            os.fchmod(f.fileno(), 0o600)
            Colors.print_success("Permisos seguros (0600) aplicados.")
        else:
            Colors.print_info("Windows detectado: Omitiendo permisos UNIX.")

    Colors.print_success(f"Archivo de configuración creado para: {domain_url}")

# ============================================
# 🚀 MAIN
# ============================================

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.HEADER}{Colors.BOLD}   INSTALADOR DE OVERLEAF SERVER (Versión Segura){Colors.ENDC}")

    # 1. VERIFICACIONES
    if not check_command("git"):
        Colors.print_error("Git no está instalado.")
        sys.exit(1)

    compose_cmd = get_docker_compose_cmd()
    if not compose_cmd:
        Colors.print_error("No se encontró 'docker-compose'.")
        sys.exit(1)

    if not check_docker_running():
        Colors.print_error("Docker no está corriendo.")
        if sys.platform == "win32":
            Colors.print_info("👉 Abre Docker Desktop.")
        else:
            Colors.print_info("👉 Ejecuta: sudo systemctl start docker")
        sys.exit(1)

    # 2. MODO
    Colors.print_step("Modo de Instalación")
    print("   [1] 🏠 LOCAL (Solo accesible desde mi red/PC)")
    print("   [2] 🌍 REMOTO (Accesible vía Tailscale/VPN)")

    mode = input(f"\n👉 {Colors.BOLD}Elige una opción (1/2): {Colors.ENDC}").strip()
    
    # 3. CONFIGURACIÓN DE RED
    Colors.print_step("Configuración de Red")
    port = get_port()
    domain_url = f"localhost:{port}"

    if mode == "2":
        Colors.print_step("Configuración Remota (Tailscale)")
        if sys.platform.startswith("linux"):
            if check_command("tailscale"):
                Colors.print_info("Tailscale ya está instalado.")
            elif input("¿Instalar Tailscale automáticamente? (s/n): ").lower() == 's':
                handle_tailscale_linux()
        elif sys.platform == "win32":
            handle_tailscale_windows()
        
        # Mejora: intentar obtener la IP de Tailscale automáticamente
        suggested_ip = get_tailscale_ip()
        prompt_ip = f"👉 IP/Dominio (Enter para '{suggested_ip or 'localhost'}'): "
        
        print(f"\n{Colors.BLUE}Introduce tu IP de Tailscale o Hostname.{Colors.ENDC}")
        ip_raw = input(prompt_ip).strip()
        
        if not ip_raw:
            ip_raw = suggested_ip or "localhost"

        clean = validate_input(ip_raw)
        if not clean:
            Colors.print_error("Formato de IP o Hostname inválido por seguridad.")
            Colors.print_info("Solo se aceptan IPs válidas o nombres de dominio estándar.")
            sys.exit(1)
        
        # Añadir puerto si no está presente
        if ":" not in clean:
            domain_url = f"{clean}:{port}"
        else:
            domain_url = clean
    
    # 4. VERIFICACIÓN DE PUERTO
    try:
        target_port = int(domain_url.split(":")[-1])
        if not check_port_availability(target_port):
            Colors.print_warning(f"El puerto {target_port} ya está en uso.")
            if input("¿Intentar continuar de todos modos? (s/n): ").lower() != 's':
                sys.exit(1)
    except (ValueError, IndexError):
        Colors.print_error(f"No se pudo determinar el puerto desde '{domain_url}'.")
        sys.exit(1)

    # 5. EJECUCIÓN
    git_clone_and_verify()
    create_env_file(domain_url)

    Colors.print_step("Lanzando Docker Containers")
    Colors.print_info("Descargando imágenes (TeX Live es pesado)...")

    try:
        subprocess.run(compose_cmd + ["up", "-d"], check=True)
        
        Colors.print_step("¡INSTALACIÓN COMPLETADA!")
        final_url = f"http://{domain_url}"
        print(f"🌍 Accede aquí: {Colors.BOLD}{Colors.GREEN}{final_url}{Colors.ENDC}")
        print(f"📂 Carpeta: {os.path.abspath('.')}")
        print(f"🛑 Para detener: '{' '.join(compose_cmd)} down'")
        
        time.sleep(2)
        webbrowser.open(final_url)

    except subprocess.CalledProcessError:
        Colors.print_error("Error al ejecutar Docker Compose.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Cancelado por el usuario.{Colors.ENDC}")
        sys.exit(0)