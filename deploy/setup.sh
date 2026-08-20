#!/usr/bin/env bash
# Falak Bot — VPS'ni ilk marta sozlash skripti.
# Ishlatish: loyiha papkasi ichidan  ->  bash deploy/setup.sh
#
# Bu skript:
#   1. Kerakli tizim paketlarini o'rnatadi (python3-venv, nginx, certbot)
#   2. Python virtual muhit yaratadi va requirements.txt'ni o'rnatadi
#   3. .env fayli yo'q bo'lsa, .env.example'dan nusxa oladi
#   4. systemd xizmatini o'rnatadi (lekin avtomatik ishga tushirmaydi —
#      avval .env'ni to'ldirishingiz kerak)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo ">> 1/4  Tizim paketlari o'rnatilmoqda..."
sudo apt update -y
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx git

echo ">> 2/4  Python virtual muhit yaratilmoqda..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate

echo ">> 3/4  .env fayli tekshirilmoqda..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   .env yaratildi — ENDI UNI TO'LDIRING:"
    echo "   nano .env"
    echo "   (kamida BOT_TOKEN, WEBHOOK_BASE_URL, WEBHOOK_SECRET shart)"
else
    echo "   .env allaqachon mavjud, o'zgartirilmadi."
fi

echo ">> 4/4  systemd xizmati o'rnatilmoqda..."
SERVICE_PATH="/etc/systemd/system/falak-bot.service"
sudo cp deploy/falak-bot.service "$SERVICE_PATH"
sudo sed -i "s#/home/falak/falak-bot#${PROJECT_DIR}#g" "$SERVICE_PATH"
sudo systemctl daemon-reload

echo ""
echo "=================================================================="
echo " Tayyor. Keyingi qadamlar:"
echo "   1. nano .env               — tokenlarni to'ldiring"
echo "   2. sudo nano ${SERVICE_PATH}   — WorkingDirectory/ExecStart to'g'riligini tekshiring"
echo "   3. Domenni serverga yo'naltiring (A-record) va:"
echo "      sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/falak-bot"
echo "      sudo ln -s /etc/nginx/sites-available/falak-bot /etc/nginx/sites-enabled/"
echo "      sudo nginx -t && sudo systemctl reload nginx"
echo "      sudo certbot --nginx -d SIZNING_DOMENINGIZ"
echo "   4. sudo systemctl enable --now falak-bot"
echo "   5. sudo systemctl status falak-bot"
echo "=================================================================="
