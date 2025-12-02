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

# INSTALACIÓN EN CARPETA DE USUARIO (Ej: /home/juan/overleaf-server)
# Esto mantiene limpio el directorio donde descargaste el script.
INSTALL_DIR = Path.home() / "overleaf-server"
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
#  TRADUCCIONES / TRANSLATIONS (SIN EMOJIS)
# =====================================================

LANG = "en" 

TEXTS = {
    "es": {
        "title": "Instalador Overleaf - Community Edition",
        "mode_label": "Modo de instalación:",
        "mode_local": "[LOCAL] Solo mi PC / Wi-Fi",
        "mode_remote": "[REMOTO] Compartir vía Tailscale",
        "tailscale_check": "Instalar Tailscale automáticamente (Solo Linux)",
        "host_label": "Dirección IP (Solo para modo Remoto):",
        "host_placeholder": "Ej: 100.85.x.x (Dejar vacío para localhost en Local)",
        "btn_install": ">>> INSTALAR / REPARAR",
        "control_panel": "Panel de Control",
        "btn_start": "Iniciar Servidor",
        "btn_stop": "Detener Servidor",
        "log_label": "Registro de operaciones:",
        "err_git": "Git no está instalado.",
        "err_docker_compose": "No se encontró docker-compose.",
        "err_docker_run": "Docker no responde. Verifica permisos.",
        "msg_tailscale_linux": "Se instaló Tailscale. Ejecuta 'sudo tailscale up' en una terminal aparte.\nLuego dale OK.",
        "msg_tailscale_win": "Instálalo, conéctate y luego presiona OK.",
        "err_ip": "IP o Dominio inválido.",
        "warn_port": "El puerto {} parece ocupado.\n¿Continuar de todos modos?",
        "log_init": "Iniciando configuración...",
        "log_dl": "... Descargando ~1.5 GB (TeX Live). Paciencia ...",
        "log_success": "\n[OK] INSTALACION COMPLETADA",
        "log_access": "URL Acceso:",
        "log_auto": "[INFO] El servidor iniciará con la PC.",
        "msg_final_title": "Finalizado",
        "msg_final_body": "El servidor está arrancando.\nPuede tardar 2-3 minutos la primera vez.",
        "server_stop": "[OK] Servidor DETENIDO.",
        "server_start": "[OK] Servidor INICIADO.",
        "not_installed": "[ERROR] Carpeta no encontrada. Instala primero.",
        "select_lang": "Select Language / Seleccione Idioma"
    },
    "en": {
        "title": "Overleaf Installer - Community Edition",
        "mode_label": "Installation Mode:",
        "mode_local": "[LOCAL] Only my PC / Wi-Fi",
        "mode_remote": "[REMOTE] Share via Tailscale",
        "tailscale_check": "Auto-install Tailscale (Linux only)",
        "host_label": "IP Address (Remote mode only):",
        "host_placeholder": "Ex: 100.85.x.x (Leave empty for localhost)",
        "btn_install": ">>> INSTALL / REPAIR",
        "control_panel": "Control Panel",
        "btn_start": "Start Server",
        "btn_stop": "Stop Server",
        "log_label": "Operation Log:",
        "err_git": "Git is not installed.",
        "err_docker_compose": "docker-compose not found.",
        "err_docker_run": "Docker is not responding. Check permissions.",
        "msg_tailscale_linux": "Tailscale installed. Run 'sudo tailscale up' externally.\nClick OK when ready.",
        "msg_tailscale_win": "Install it, connect, and then press OK.",
        "err_ip": "Invalid IP or Domain.",
        "warn_port": "Port {} seems busy.\nContinue anyway?",
        "log_init": "Starting configuration...",
        "log_dl": "... Downloading ~1.5 GB (TeX Live). Please wait ...",
        "log_success": "\n[OK] INSTALLATION COMPLETED",
        "log_access": "Access URL:",
        "log_auto": "[INFO] Server will auto-start with PC.",
        "msg_final_title": "Finished",
        "msg_final_body": "Server is starting up.\nIt may take 2-3 minutes to be ready.",
        "server_stop": "[OK] Server STOPPED.",
        "server_start": "[OK] Server STARTED.",
        "not_installed": "[ERROR] Folder not found. Install first.",
        "select_lang": "Select Language / Seleccione Idioma"
    }
}

def t(key):
    return TEXTS[LANG].get(key, key)

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
    log("Tailscale native install...")

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
    messagebox.showinfo("Manual Install",
                        "No package manager found.\nOpening browser for manual install.")
    webbrowser.open("https://tailscale.com/download/linux")
    return False


# =====================================================
#  GESTIÓN DE ARCHIVOS Y CONFIGURACIÓN
# =====================================================

def git_clone():
    # Usamos INSTALL_DIR (ruta absoluta) en lugar de relativa
    if not INSTALL_DIR.exists():
        log(f"Cloning repo to {INSTALL_DIR}...")
        subprocess.run(["git", "clone", REPO_URL, str(INSTALL_DIR)], check=True)
    else:
        log("Folder found. Using existing version.")

    os.chdir(INSTALL_DIR)


def create_env(domain, port):
    """Genera overleaf.env y docker-compose.yml con la configuración v5.0."""
    
    # 1. Archivo de Variables (.env)
    if os.path.exists("overleaf.env"):
        log(".env exists. Keeping config.")
    else:
        session = secrets.token_hex(32)
        jwt = secrets.token_hex(32)

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
        log(".env created.")

    # 2. Archivo Docker Compose (Infraestructura)
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
    log("docker-compose.yml updated.")


def init_mongo_replica():
    """Inicializa el Replica Set requerido por Mongo 8.0."""
    log("Init Mongo (Wait 10s)...")
    time.sleep(10) 
    
    try:
        cmd = ["docker", "exec", "mongo", "mongosh", "--eval", "rs.initiate()"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if "ok" in result.stdout or "already initialized" in result.stdout:
            log("[OK] Mongo Replica Set Ready.")
        else:
            log(f"[!] Mongo Warning: {result.stdout}")
            
    except Exception as e:
        log(f"Mongo Init Error: {e}")


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
        messagebox.showerror("Error", t("err_docker_compose"))
        return
    
    if INSTALL_DIR.exists():
        os.chdir(INSTALL_DIR)
        log("Stopping...")
        subprocess.run(compose + ["stop"], check=True)
        log(t("server_stop"))
    else:
        log(t("not_installed"))

def only_start_server():
    compose = get_compose_cmd()
    if not compose:
        messagebox.showerror("Error", t("err_docker_compose"))
        return
    
    if INSTALL_DIR.exists():
        os.chdir(INSTALL_DIR)
        log("Starting...")
        subprocess.run(compose + ["start"], check=True)
        log(t("server_start"))
        messagebox.showinfo("Server", t("server_start"))
    else:
        log(t("not_installed"))

def run_install():
    try:
        # 1. Validaciones Iniciales
        mode = mode_var.get()
        host = host_entry.get().strip()
        domain = f"localhost:{DEFAULT_PORT}"

        if not check_command("git"):
            messagebox.showerror("Error", t("err_git"))
            return

        compose = get_compose_cmd()
        if not compose:
            messagebox.showerror("Error", t("err_docker_compose"))
            return

        if not check_docker_running():
            messagebox.showerror("Error", t("err_docker_run"))
            return

        # 2. Configuración de Red (Tailscale / Local)
        if mode == 2: # Remoto
            log("Remote Mode selected.")
            if sys.platform.startswith("linux"):
                if tailscale_var.get():
                    if not check_command("tailscale"):
                        install_tailscale_linux()
                        messagebox.showinfo("Action Required", t("msg_tailscale_linux"))
                    else:
                        log("Tailscale installed.")
                        
            elif sys.platform == "win32":
                webbrowser.open("https://tailscale.com/download/windows")
                messagebox.showinfo("Tailscale", t("msg_tailscale_win"))

            if host:
                clean = sanitize_host_port(host)
                if not clean:
                    messagebox.showerror("Error", t("err_ip"))
                    return
                domain = clean

        # 3. Validación de Puerto
        try:
            port = int(domain.split(":")[1])
        except IndexError:
            port = DEFAULT_PORT

        if is_port_in_use(port):
            log(f"[!] Port {port} busy.")
            if not messagebox.askyesno("Port Busy", t("warn_port").format(port)):
                return

        # 4. Proceso de Instalación
        log(t("log_init"))
        
        # Clonamos en la nueva ubicación (HOME/overleaf-server)
        git_clone()
        
        create_env(domain, port)

        log(f"Docker Up ({port})...")
        log(t("log_dl"))
        
        subprocess.run(compose + ["down"], check=True)
        subprocess.run(compose + ["up", "-d"], check=True)
        
        init_mongo_replica()

        url = f"http://{domain}"
        log(t("log_success"))
        log(f"{t('log_access')} {url}")
        log(t("log_auto"))
        
        messagebox.showwarning(t("msg_final_title"), t("msg_final_body"))
        
        webbrowser.open(url)
        
    except Exception as e:
        messagebox.showerror("Critical Error", f"{str(e)}")
        log(f"[ERROR] {str(e)}")


# =====================================================
#  LÓGICA DE SELECCIÓN DE IDIOMA
# =====================================================

def set_lang(language):
    global LANG
    LANG = language
    lang_window.destroy()
    launch_main_gui()

def launch_lang_selector():
    global lang_window
    lang_window = Tk()
    lang_window.title("Language")
    lang_window.geometry("300x150")
    
    ttk.Label(lang_window, text="Select Language / Seleccione Idioma", font=("Arial", 10)).pack(pady=20)
    
    btn_frame = ttk.Frame(lang_window)
    btn_frame.pack(fill="x", padx=20)
    
    ttk.Button(btn_frame, text="English", command=lambda: set_lang("en")).pack(side="left", expand=True, padx=5)
    ttk.Button(btn_frame, text="Español", command=lambda: set_lang("es")).pack(side="right", expand=True, padx=5)
    
    lang_window.mainloop()

# =====================================================
#  INTERFAZ PRINCIPAL (GUI)
# =====================================================

def launch_main_gui():
    global root, mode_var, tailscale_var, host_entry, output_box
    
    root = Tk()
    root.title(t("title"))
    root.geometry("750x650")

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=t("title"), font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(0, 10))

    # Selección de modo
    mode_frame = ttk.LabelFrame(frame, text=f"1. {t('mode_label')}", padding=10)
    mode_frame.pack(fill="x", pady=5)

    mode_var = IntVar(value=1)
    ttk.Radiobutton(mode_frame, text=t("mode_local"), variable=mode_var, value=1).pack(anchor="w")
    ttk.Radiobutton(mode_frame, text=t("mode_remote"), variable=mode_var, value=2).pack(anchor="w")

    tailscale_var = IntVar(value=1)
    ttk.Checkbutton(mode_frame, text=t("tailscale_check"), variable=tailscale_var).pack(anchor="w", padx=20)

    # Host/IP
    host_frame = ttk.LabelFrame(frame, text=f"2. {t('host_label')}", padding=10)
    host_frame.pack(fill="x", pady=10)

    host_entry = ttk.Entry(host_frame)
    host_entry.pack(fill="x", pady=5)
    ttk.Label(host_frame, text=t("host_placeholder"), font=("Helvetica", 9, "italic")).pack(anchor="w")

    # Botones de Acción
    action_frame = ttk.Frame(frame)
    action_frame.pack(fill="x", pady=20)

    btn_install_w = ttk.Button(action_frame, text=t("btn_install"), command=start_install_thread)
    btn_install_w.pack(fill="x", ipady=5)

    # Panel de Control
    control_frame = ttk.LabelFrame(frame, text=t("control_panel"), padding=10)
    control_frame.pack(fill="x", pady=10)

    ttk.Button(control_frame, text=t("btn_start"), command=start_server_thread).pack(side="left", expand=True, fill="x", padx=5)
    ttk.Button(control_frame, text=t("btn_stop"), command=stop_server_thread).pack(side="right", expand=True, fill="x", padx=5)

    # Log
    ttk.Label(frame, text=t("log_label"), font=("Helvetica", 10, "bold")).pack(anchor="w")
    output_box = scrolledtext.ScrolledText(frame, height=12, state="disabled", font=("Consolas", 9))
    output_box.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    launch_lang_selector()