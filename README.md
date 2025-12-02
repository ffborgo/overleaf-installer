# 🍃 Overleaf Community Installer (Self-Hosted)

Un instalador automatizado, seguro y con **interfaz gráfica** para desplegar tu propio servidor de **Overleaf Community Edition**.

Este script simplifica la configuración de Docker, la generación de secretos criptográficos y la conectividad remota (vía Tailscale), permitiéndote tener tu propio editor de LaTeX colaborativo sin límites de usuarios y bajo tu control.

## ✨ Características

  * **🚀 Multiplataforma:** Funciona en **Arch Linux**, **Debian/Ubuntu**, **Windows** y **macOS**.
  * **🖥️ Interfaz Gráfica (GUI):** Panel de control visual para instalar y gestionar el servidor sin comandos complejos.
  * **🔄 Actualizado (v5.0):** Configura automáticamente **Overleaf 5.0** con **Mongo 8.0**, resolviendo los problemas de compatibilidad de versiones anteriores.
  * **🔒 Seguridad Primero:** Generación automática de secretos, permisos seguros (0600) y validación estricta de inputs.
  * **🌐 Soporte Remoto (Tailscale):** Integración nativa para instalar Tailscale en Linux, facilitando la colaboración remota segura.
  * **⚡ Control de Recursos:** Incluye botones para **Detener** e **Iniciar** el servidor fácilmente cuando no lo uses (ahorra \~2GB de RAM).

## 📋 Requisitos Previos

Antes de ejecutar el script, asegúrate de tener instalado:

1.  **Git** y **Docker** (Docker Desktop en Windows/Mac, Docker Engine en Linux).
2.  **Python 3**.
3.  **(Solo Linux) Librería Gráfica:**
      * Arch Linux: `sudo pacman -S tk`
      * Debian/Ubuntu: `sudo apt install python3-tk`

## 🚀 Uso Rápido

1.  Clona el repositorio o descarga `install_overleaf.py`:

    ```bash
    git clone https://github.com/ffborgo/overleaf-installer.git
    cd overleaf-installer
    ```

2.  Ejecuta el instalador:

    ```bash
    python install_overleaf.py
    ```

3.  **Se abrirá una ventana gráfica.** Sigue las instrucciones:

      * Selecciona **[1] Local** si solo lo usarás en tu red Wi-Fi.
      * Selecciona **[2] Remoto** si quieres colaborar con amigos a través de internet (usando Tailscale).

## 🛠️ ¿Qué hace este script?

El script automatiza todo el proceso de "DevOps" que normalmente harías a mano:

1.  **Clonado:** Descarga el repositorio oficial `overleaf/toolkit`.
2.  **Configuración:** Genera los archivos `overleaf.env` y `docker-compose.yml` con la configuración correcta para la versión 5.0 (rutas y puertos corregidos).
3.  **Base de Datos:** Inicializa el *Replica Set* de MongoDB 8.0 necesario para que Overleaf arranque.
4.  **Auto-Arranque:** Configura los contenedores para que inicien automáticamente con tu PC (a menos que los detengas manualmente).

## ⚠️ Notas Importantes

  * **Primera vez:** La instalación descargará cerca de **1GB** de datos (TeX Live completo). Ten paciencia, puede tardar unos minutos.
  * **Espera Inicial:** Una vez instalado, Overleaf tarda unos 2-3 minutos en arrancar todos sus servicios. Si ves "Error de conexión" en el navegador, espera un poco y recarga la página.
  * **Puerto:** Por defecto utiliza el `8080`. Si está ocupado, el instalador te avisará y te dejará cambiarlo.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si encuentras un bug o quieres mejorar la detección de distros, siéntete libre de abrir un Pull Request.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - eres libre de usarlo y modificarlo.
*Overleaf es una marca registrada de Digital Science UK Limited. Este instalador es un proyecto comunitario no oficial.*