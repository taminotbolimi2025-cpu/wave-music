#!/bin/bash
set -e

echo "=========================================================="
echo ">> УСТАНОВКА И ЗАПУСК WAVE MUSIC НА VPS (24/7)"
echo "=========================================================="

apt update && apt install -y python3 python3-pip python3-venv ffmpeg git curl

cd /opt
if [ -d "wave-music" ]; then
    echo ">> Обновление репозитория..."
    cd wave-music && git pull origin main
else
    echo ">> Клонирование репозитория..."
    git clone https://github.com/taminotbolimi2025-cpu/wave-music.git
    cd wave-music
fi

if [ ! -d ".venv" ]; then
    echo ">> Создание виртуального окружения..."
    python3 -m venv .venv
fi

echo ">> Установка зависимостей..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Установка Cloudflared для Linux если не установлен
if ! command -v cloudflared &> /dev/null; then
    echo ">> Установка Cloudflared для HTTPS..."
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i /tmp/cloudflared.deb || apt --fix-broken install -y
    rm -f /tmp/cloudflared.deb
fi

# Настройка автозапуска через systemd
echo ">> Настройка службы systemd (wave-music.service)..."
cat << 'EOF' > /etc/systemd/system/wave-music.service
[Unit]
Description=Wave Music Telegram MiniApp Daemon 24/7
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wave-music
ExecStart=/opt/wave-music/.venv/bin/python run_app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wave-music
systemctl restart wave-music

echo "=========================================================="
echo ">> ГОТОВО! Wave Music работает на VPS 24/7!"
echo ">> Проверить статус: systemctl status wave-music"
echo ">> Посмотреть логи:  journalctl -u wave-music -f"
echo "=========================================================="
