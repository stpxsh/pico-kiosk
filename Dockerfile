# Použijeme Node image založený na Debianu
FROM node:18-bookworm-slim

# Nainstalujeme Chromium a fonty, které Puppeteer potřebuje k renderování HTML
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Nastavíme environment proměnné, aby Puppeteer nestahoval vlastní Chrome,
# ale použil ten, co jsme právě nainstalovali přes apt-get.
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Vytvoření složky aplikace
WORKDIR /usr/src/app

# Zkopírování package.json a instalace Node modulů
COPY package*.json ./
RUN npm install

# Zkopírování zbytku kódu (server.js a public/ složky)
COPY . .

# Vystavení portu
EXPOSE 3000

# Spuštění serveru
CMD [ "npm", "start" ]
