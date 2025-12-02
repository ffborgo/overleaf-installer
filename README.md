# 🍃 Overleaf Community Installer (Self-Hosted)

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

An automated, secure, and **GUI-based** installer to deploy your own **Overleaf Community Edition** server effortlessly.

This script handles Docker configuration, cryptographic secret generation, and remote connectivity (via Tailscale), allowing you to have your own real-time collaborative LaTeX editor without user limits and fully under your control.

## ✨ Features

* **🚀 Multi-platform:** Works on **Arch Linux**, **Debian/Ubuntu**, **Windows**, and **macOS**.
* **🖥️ GUI Control Panel:** User-friendly interface to install, start, and stop the server without complex CLI commands.
* **🔄 Up-to-date (v5.0):** Automatically configures **Overleaf 5.0** with **Mongo 8.0**, solving compatibility issues from older manual setups.
* **🔒 Security First:** Automated secure secret generation, 0600 permissions, and strict input validation.
* **🌐 Remote Support (Tailscale):** Native integration to install/detect Tailscale on Linux for secure remote collaboration.
* **⚡ Resource Control:** Includes buttons to **Stop** and **Start** the server easily to save RAM (~2GB) when not in use.

## 📋 Prerequisites

Before running the script, ensure you have:

1.  **Git** and **Docker** (Docker Desktop on Windows/Mac, Docker Engine on Linux).
2.  **Python 3**.
3.  **(Linux Only) Tkinter:**
    * Arch Linux: `sudo pacman -S tk`
    * Debian/Ubuntu: `sudo apt install python3-tk`

## 🚀 Quick Start

1.  Clone the repository:
    ```bash
    git clone [https://github.com/ffborgo/overleaf-installer.git](https://github.com/ffborgo/overleaf-installer.git)
    cd overleaf-installer
    ```

2.  Run the installer:
    ```bash
    python install_overleaf.py
    ```

3.  **Select your Language** (English/Spanish) and follow the GUI instructions:
    * Select **[1] Local** if you only use it on your Wi-Fi/PC.
    * Select **[2] Remote** if you want to collaborate with friends via Internet (using Tailscale).

## 🛠️ What does this script do?

It automates the "DevOps" work for you:

1.  **Cloning:** Downloads the official `overleaf/toolkit`.
2.  **Configuration:** Generates `overleaf.env` and `docker-compose.yml` with the correct configuration for v5.0 (fixed paths and ports).
3.  **Database:** Initializes the required MongoDB 8.0 *Replica Set*.
4.  **Auto-Start:** Configures containers to start automatically with your PC (unless manually stopped via the GUI).

## ⚠️ Important Notes

* **First Run:** The installation will download about **4GB** of data (Full TeX Live). Please be patient.
* **Initial Boot:** Once installed, Overleaf takes 2-3 minutes to start all services. If you see a "Connection Error", wait a bit and refresh the page.
* **Port:** Default is `8080`. If busy, the installer will alert you and let you change it.

## 🤝 Contributing

Contributions are welcome! If you find a bug or want to improve distro detection, feel free to open a Pull Request.

## 📄 License

This project is licensed under the MIT License.
*Overleaf is a registered trademark of Digital Science UK Limited. This installer is an unofficial community project.*