# 🍃 Overleaf Community Installer (Self-Hosted)

Un instalador automatizado, seguro y multiplataforma para desplegar tu propio servidor de **Overleaf Community Edition**.

Este script simplifica la configuración de Docker, la generación de secretos criptográficos y la conectividad remota (vía Tailscale), permitiéndote tener tu propio editor de LaTeX colaborativo sin límites de usuarios y bajo tu control.

## ✨ Características

  * **🚀 Multiplataforma:** Detecta y se adapta automáticamente a **Arch Linux**, **Debian/Ubuntu**, **Windows** y **macOS**.
  * **🔒 Seguridad Primero:**
      * Generación automática de `SESSION_SECRET` y `JWT_SECRET` seguros.
      * Validación estricta de IPs y Hostnames (evita inyección de comandos).
      * Descarga segura de dependencias (verifica permisos en Linux).
  * **🌐 Soporte Remoto (Tailscale):** Integración nativa para instalar y configurar Tailscale en Linux (con auto-detección de IP), facilitando la colaboración remota segura.
  * **🐳 Docker Inteligente:** Detecta y utiliza automáticamente `docker compose` (V2) o `docker-compose` (V1).
  * **🛡️ Verificaciones de Salud:** Comprueba si Docker está corriendo y si el puerto elegido está libre antes de iniciar.
  * **⚙️ Puerto Configurable:** Permite elegir el puerto de la aplicación, con `8080` como valor por defecto.

## 📋 Requisitos Previos

Antes de ejecutar el script, asegúrate de tener instalado:

1.  **Python 3** (Preinstalado en Linux/macOS. En Windows descargar de la Store o python.org).
2.  **Git**.
3.  **Docker Desktop** (Windows/macOS) o **Docker Engine** (Linux).

## 🚀 Uso Rápido

1.  Descarga el archivo `install_overleaf.py`:

2.  Ejecuta el instalador:

    ```bash
    python install_overleaf.py
    ```

3.  Sigue las instrucciones en pantalla:

      * Selecciona **[1] Local** si solo lo usarás en tu red Wi-Fi.
      * Selecciona **[2] Remoto** si quieres colaborar con amigos a través de internet (usando Tailscale).

## 🛠️ ¿Qué hace este script?

El script automatiza los siguientes pasos manuales y tediosos:

1.  **Verificación:** Comprueba que Git y Docker estén listos.
2.  **Clonado:** Descarga el repositorio oficial `overleaf/toolkit`.
3.  **Configuración:** Crea el archivo `overleaf.env` inyectando claves criptográficas aleatorias (hex 32 bytes) y configurando la URL base.
4.  **Permisos:** En Linux/macOS, aplica `chmod 600` al archivo de configuración por seguridad.
5.  **Despliegue:** Ejecuta `docker compose up -d` para descargar las imágenes (incluyendo el sistema TeX Live completo) y levantar los servicios.

## ⚠️ Notas Importantes

  * **Tamaño de Descarga:** La primera vez que corras el instalador, Docker descargará cerca de **4GB** de datos (debido a la instalación completa de LaTeX). Ten paciencia.
  * **Windows:** Si usas Windows, el script abrirá el navegador para que instales Tailscale manualmente si eliges el modo remoto.
  * **Puerto:** El script te permitirá elegir el puerto. Por defecto, utiliza el `8080`. Si está ocupado, te avisará.

## 🤝 Contribuciones

Las contribuciones son bienvenidas, si encuentras un bug o queres mejorar la detección de distros, sentite libre de abrir un Pull Request.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - eres libre de usarlo y modificarlo.
*Overleaf es una marca registrada de Digital Science UK Limited. Este instalador es un proyecto comunitario no oficial.*


