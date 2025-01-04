# Utiliser Python 3.11 slim comme image de base
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV SECRET_KEY="django-insecure-temporary-key-for-collect-static" 

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
   # Dépendances essentielles
   build-essential \
   pkg-config \
   # Pour mysqlclient
   default-libmysqlclient-dev \
   python3-dev \
   default-mysql-client \
   # Pour Pillow et le traitement d'images
   libjpeg-dev \
   zlib1g-dev \
   libpq-dev \
   # Pour PDF et documents
   poppler-utils \
   # Autres outils nécessaires
   gcc \
   netcat-traditional \
   curl \
   # Nettoyage
   && apt-get clean \
   && rm -rf /var/lib/apt/lists/*

# Création du répertoire de travail
WORKDIR /app

# Configuration pour mysqlclient
ENV MYSQLCLIENT_CFLAGS="-I/usr/include/mysql"
ENV MYSQLCLIENT_LDFLAGS="-L/usr/lib/x86_64-linux-gnu -lmysqlclient"

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
   pip install --no-cache-dir wheel && \
   pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Collection des fichiers statiques avec une SECRET_KEY temporaire
RUN python manage.py collectstatic --noinput

# Port d'exposition
EXPOSE 8000

# Création et configuration du script de démarrage
COPY start.sh .
RUN chmod +x start.sh

# Commande par défaut
CMD ["./start.sh"]