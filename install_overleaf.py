import os
import sys
import subprocess
import secrets
import shutil
import re
import time
import webbrowser
import socket
import threading
from tkinter import *
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

# =====================================================
#  CONFIGURACIÓN GLOBAL
# =====================================================

REPO_URL = "https://github.com/overleaf/toolkit.git"
DIR_NAME = "overleaf-toolkit"
DEFAULT_PORT = 8080

# Regex para validar Hostnames y Direcciones IP
ipv4_regex = re.compile(
    r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)

hostname_regex = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9]"
    r"([A-Za-z0-9\-]{0,61}[A-Za-z0-9])?"
    r"(\.(?!-)[A-Za-z0-9]([A-Za-z0-9\-]{0,61}[A-Za-z0-9])?)*$"
)


# =====================================================
#  UTILIDADES Y HELPERS
# =====================================================

def log(msg):
    """Escribe en la caja de texto de la GUI."""
    output_box.config(state="normal")
    output_box.insert(END, msg + "\n")
    output_box.see(END)
    output_box.config(state="disabled")


def check_command(cmd):
    return shutil.which(cmd) is not None


def check_docker_running():
    try:
        subprocess.run(["docker", "info"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
        return True
    except:
        return False


def is_port_in_use(port):
    """Devuelve True si el puerto está ocupado."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def sanitize_host_port(raw):
    """Valida y limpia la entrada de Host/IP."""
    if ":" in raw:
        host, port_str = raw.rsplit(":", 1)
    else:
        host, port_str = raw, str(DEFAULT_PORT)

    if not port_str.isdigit():
        return None
    port = int(port_str)
    if not (1 <= port <= 65535):
        return None

    if ipv4_regex.match(host) or hostname_regex.match(host):
        return f"{host}:{port}"

    return None


def get_compose_cmd():
    """Detecta si usar 'docker compose' o 'docker-compose'."""
    try:
        subprocess.run(["docker", "compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ["docker", "compose"]
    except:
        pass

    if check_command("docker-compose"):
        return ["docker-compose"]

    return None


# =====================================================
#  GESTIÓN DE RED Y TAILSCALE
# =====================================================

def install_tailscale_linux():
    log("Intentando instalación nativa de Tailscale...")

    # Intentar gestores de paquetes comunes
    if check_command("pacman") and Path("/etc/arch-release").exists():
        subprocess.run(["sudo", "pacman", "-Sy", "--noconfirm", "tailscale"])
        return True

    if check_command("apt"):
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "-y", "tailscale"])
        return True

    if check_command("dnf"):
        subprocess.run(["sudo", "dnf", "install", "-y", "tailscale"])
        return True

    # Fallback manual
    messagebox.showinfo("Instalación Manual",
                        "No se detectó un gestor compatible automático.\n"
                        "Se abrirá la web para instalar Tailscale manualmente.")
    webbrowser.open("https://tailscale.com/download/linux")
    return False


# =====================================================
#  GESTIÓN DE ARCHIVOS Y CONFIGURACIÓN
# =====================================================

def git_clone():
    if not os.path.exists(DIR_NAME):
        log("Clonando repositorio Overleaf Toolkit...")
        subprocess.run(["git", "clone", REPO_URL, DIR_NAME], check=True)
    else:
        log("Directorio del proyecto encontrado. Usando versión existente.")

    os.chdir(DIR_NAME)


def create_env(domain, port):
    """Genera overleaf.env y docker-compose.yml con la configuración v5.0."""
    
    # 1. Archivo de Variables (.env)
    if os.path.exists("overleaf.env"):
        log("Archivo .env existente. No se sobrescribirá (mantiene tus datos).")
    else:
        session = secrets.token_hex(32)
        jwt = secrets.token_hex(32)

        # Variables actualizadas para Overleaf 5.0 (Prefijo OVERLEAF_)
        data = f"""# Generado por Overleaf Installer
OVERLEAF_APP_NAME=Overleaf Community
OVERLEAF_SITE_URL=http://{domain}
OVERLEAF_SESSION_SECRET={session}
OVERLEAF_JWT_SECRET={jwt}
OVERLEAF_MONGO_URL=mongodb://mongo/sharelatex
OVERLEAF_REDIS_HOST=redis
REDIS_HOST=redis
REDIS_PORT=6379
OVERLEAF_PORT={port}
"""
        with open("overleaf.env", "w") as f:
            f.write(data)
            # Permisos seguros solo en Linux/Mac
            if hasattr(os, "fchmod"):
                os.fchmod(f.fileno(), 0o600)
        log("Archivo .env creado con éxito.")

    # 2. Archivo Docker Compose (Infraestructura)
    # Configuración para Mongo 8.0, Redis 7.0 y Rutas Nuevas
    compose_content = f"""services:
  sharelatex:
    image: sharelatex/sharelatex:latest
    container_name: sharelatex
    restart: unless-stopped
    depends_on:
      - mongo
      - redis
    ports:
      - "{port}:80"
    links:
      - mongo
      - redis
    volumes:
      - ./data/sharelatex:/var/lib/overleaf
      - ./data/logs:/var/log/overleaf
    environment:
      OVERLEAF_MONGO_URL: mongodb://mongo/sharelatex
      OVERLEAF_REDIS_HOST: redis
      REDIS_HOST: redis
    env_file:
      - overleaf.env

  mongo:
    image: mongo:8.0
    container_name: mongo
    restart: unless-stopped
    command: "--replSet overleaf" 
    volumes:
      - ./data/mongo:/data/db

  redis:
    image: redis:7
    container_name: redis
    restart: unless-stopped
    volumes:
      - ./data/redis:/data
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    log("Configuración de Docker (compose) actualizada.")


def init_mongo_replica():
    """Inicializa el Replica Set requerido por Mongo 8.0."""
    log("Inicializando base de datos (Mongo Replica Set)...")
    log("Esperando 10 segundos para asegurar arranque...")
    time.sleep(10) 
    
    try:
        cmd = ["docker", "exec", "mongo", "mongosh", "--eval", "rs.initiate()"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if "ok" in result.stdout or "already initialized" in result.stdout:
            log("✅ Base de datos inicializada correctamente.")
        else:
            log(f"⚠️ Alerta Mongo: {result.stdout}")
            
    except Exception as e:
        log(f"No se pudo inicializar Mongo (¿Quizás ya estaba listo?): {e}")


# =====================================================
#  FUNCIONES DE CONTROL (THREADS)
# =====================================================

def start_install_thread():
    t = threading.Thread(target=run_install)
    t.daemon = True
    t.start()

def stop_server_thread():
    t = threading.Thread(target=stop_server)
    t.daemon = True
    t.start()

def start_server_thread():
    t = threading.Thread(target=only_start_server)
    t.daemon = True
    t.start()

# --- Lógica de Control ---

def stop_server():
    compose = get_compose_cmd()
    if not compose:
        messagebox.showerror("Error", "No se encontró docker-compose.")
        return
    
    if os.path.exists(DIR_NAME):
        os.chdir(DIR_NAME)
        log("🛑 Deteniendo servidor...")
        subprocess.run(compose + ["stop"], check=True)
        log("✅ Servidor DETENIDO. (Recursos liberados)")
    else:
        log("❌ No se encontró la carpeta de instalación.")

def only_start_server():
    compose = get_compose_cmd()
    if not compose:
        messagebox.showerror("Error", "No se encontró docker-compose.")
        return
    
    if os.path.exists(DIR_NAME):
        os.chdir(DIR_NAME)
        log("▶️ Iniciando servidor...")
        subprocess.run(compose + ["start"], check=True)
        log("✅ Servidor INICIADO en segundo plano.")
        messagebox.showinfo("Servidor", "El servidor se ha iniciado.")
    else:
        log("❌ Primero debes instalar Overleaf.")

def run_install():
    try:
        # 1. Validaciones Iniciales
        mode = mode_var.get()
        host = host_entry.get().strip()
        domain = f"localhost:{DEFAULT_PORT}"

        if not check_command("git"):
            messagebox.showerror("Error", "Git no está instalado.")
            return

        compose = get_compose_cmd()
        if not compose:
            messagebox.showerror("Error", "No se encontró docker-compose.")
            return

        if not check_docker_running():
            messagebox.showerror("Error", "Docker no responde. Verifica que esté corriendo y tengas permisos.")
            return

        # 2. Configuración de Red (Tailscale / Local)
        if mode == 2: # Remoto
            log("Modo Remoto seleccionado.")
            if sys.platform.startswith("linux"):
                if tailscale_var.get():
                    if not check_command("tailscale"):
                        install_tailscale_linux()
                        messagebox.showinfo("Atención", 
                                            "Se instaló Tailscale. Ejecuta 'sudo tailscale up' en una terminal aparte para loguearte.\n\nDale OK cuando estés listo.")
                    else:
                        log("Tailscale ya está instalado.")
                        
            elif sys.platform == "win32":
                webbrowser.open("https://tailscale.com/download/windows")
                messagebox.showinfo("Tailscale", "Instálalo, conéctate y luego presiona OK.")

            if host:
                clean = sanitize_host_port(host)
                if not clean:
                    messagebox.showerror("Error", "IP o Dominio inválido.")
                    return
                domain = clean

        # 3. Validación de Puerto
        try:
            port = int(domain.split(":")[1])
        except IndexError:
            port = DEFAULT_PORT

        if is_port_in_use(port):
            log(f"⚠️ El puerto {port} parece ocupado. Si es una reinstalación, ignora esto.")
            if not messagebox.askyesno("Puerto en uso", f"El puerto {port} está ocupado.\n¿Continuar de todos modos?"):
                return

        # 4. Proceso de Instalación
        log("📥 Iniciando descarga y configuración...")
        git_clone()
        create_env(domain, port)

        log(f"🐳 Levantando contenedores en puerto {port}...")
        log("⏳ Descargando ~1.5 GB de imágenes (TeX Live). Paciencia...")
        
        # Reset para asegurar configuración limpia
        subprocess.run(compose + ["down"], check=True)
        subprocess.run(compose + ["up", "-d"], check=True)
        
        # Inicializar DB
        init_mongo_replica()

        url = f"http://{domain}"
        log(f"\n✅ ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!")
        log(f"🔗 Acceso: {url}")
        log(f"ℹ️  El servidor se iniciará automáticamente con la PC (si no lo detienes manualmnete).")
        
        messagebox.showwarning("Finalizado", 
                            "El servidor está arrancando.\n\n"
                            "⚠️ IMPORTANTE: Puede tardar 2-3 minutos en estar listo la primera vez.\n"
                            "Si ves un error de conexión, espera un poco y recarga la página.")
        
        webbrowser.open(url)
        
    except Exception as e:
        messagebox.showerror("Error Crítico", f"Ocurrió un error:\n{str(e)}")
        log(f"❌ ERROR: {str(e)}")


# =====================================================
#  INTERFAZ GRÁFICA (GUI)
# =====================================================

root = Tk()
root.title("Instalador Overleaf – Community Edition")
root.geometry("750x650")

# Estilo
style = ttk.Style()
style.configure("TButton", font=("Helvetica", 10))
style.configure("TLabel", font=("Helvetica", 11))

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

# Encabezado
ttk.Label(frame, text="Configuración de Instalación", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(0, 10))

# Selección de modo
mode_frame = ttk.LabelFrame(frame, text="1. Elige el modo de uso", padding=10)
mode_frame.pack(fill="x", pady=5)

mode_var = IntVar(value=1)
ttk.Radiobutton(mode_frame, text="🏠 Local (Solo mi PC / Wi-Fi)", variable=mode_var, value=1).pack(anchor="w")
ttk.Radiobutton(mode_frame, text="🌍 Remoto (Compartir vía Tailscale)", variable=mode_var, value=2).pack(anchor="w")

tailscale_var = IntVar(value=1)
ttk.Checkbutton(mode_frame, text="Instalar Tailscale automáticamente (Solo Linux)", variable=tailscale_var).pack(anchor="w", padx=20)

# Host/IP
host_frame = ttk.LabelFrame(frame, text="2. Dirección IP (Solo para modo Remoto)", padding=10)
host_frame.pack(fill="x", pady=10)

host_entry = ttk.Entry(host_frame)
host_entry.pack(fill="x", pady=5)
ttk.Label(host_frame, text="Ej: 100.85.x.x  (Dejar vacío para localhost:8080 en modo Local)", font=("Helvetica", 9, "italic")).pack(anchor="w")

# Botones de Acción
action_frame = ttk.Frame(frame)
action_frame.pack(fill="x", pady=20)

btn_install = ttk.Button(action_frame, text="INSTALAR / REPARAR", command=start_install_thread)
btn_install.pack(fill="x", ipady=5)

# Panel de Control
control_frame = ttk.LabelFrame(frame, text="Panel de Control (Post-Instalación)", padding=10)
control_frame.pack(fill="x", pady=10)

btn_start = ttk.Button(control_frame, text="Iniciar", command=start_server_thread)
btn_start.pack(side="left", expand=True, fill="x", padx=5)

btn_stop = ttk.Button(control_frame, text="Detener (Ahorrar RAM)", command=stop_server_thread)
btn_stop.pack(side="right", expand=True, fill="x", padx=5)

# Log
ttk.Label(frame, text="Registro de operaciones:", font=("Helvetica", 10, "bold")).pack(anchor="w")
output_box = scrolledtext.ScrolledText(frame, height=12, state="disabled", font=("Consolas", 9))
output_box.pack(fill="both", expand=True)

root.mainloop()