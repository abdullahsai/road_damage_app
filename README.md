
# Road Damage Reporter

A tiny self‑hosted web app that lets a single user log damaged signboards or guardrails from a phone and later download a formatted report.

## Features
* **No login required** – open the site, press one button.
* **GPS accuracy check** – indicator turns green when < 5 m horizontal accuracy.
* **Camera capture** – take a photo right inside the browser (`input type=file` capture).
* **Damage type selector** – choose *guardrail* or *signboard*.
* **Offline-friendly** – everything runs in your container, no external APIs.
* **Report generator** – view `/report` or download `/report/pdf`.
* **One‑click deploy** – Docker Compose builds backend (FastAPI) + frontend (NGINX).

## Quick start on a fresh Ubuntu (e.g. Linode)

```bash
# 1. install docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# 2. download and unzip
curl -L -o road_damage_app.zip <URL_TO_ZIP>
unzip road_damage_app.zip
cd road_damage_app

# 3. build & run
docker compose up -d --build
```

Now open `http://YOUR_SERVER_IP` on your phone.

## Customizations
* Change accuracy threshold: edit `frontend/app.js`.
* If you disable PDF, remove `weasyprint` from requirements to speed up build.

