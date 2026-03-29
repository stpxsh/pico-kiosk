# E-ink Kiosk Backend (pro RPi Pico W)

Tento projekt slouží jako prostředník (backend) mezi responzivním HTML designem a mikrokontrolérem Raspberry Pi Pico W osazeným e-ink displejem.

## Co to dělá?
Server vezme běžnou HTML stránku (např. rozvrh hodin či informační panel uložený ve složce `public`), na pozadí spustí neviditelný prohlížeč Chrome pomocí knihovny Puppeteer a celou stránku vyfotí v přesném rozlišení displeje (480x320 pixelů).

Následně snímek převede do černobílé škály a zkomprimuje na binární úroveň tak, že 8 pixelů sbalí do 1 bytu. Výsledkem je super malý a optimalizovaný soubor o velikosti pouhých cca 19 KB. Tento hotový _payload_ si Pico už jen stáhne a rovnou metodou 1:1 vykreslí na e-ink displej, čímž ušetří maximum výkonu mikrokontroléru.

## Struktura projektu

```text
/
├── .gitignore         # Ignorované soubory (node_modules, bin_out/)
├── Dockerfile         # Konfigurace pro kontejnerizaci s připraveným m.j. Puppeteer/Chromium
├── package.json       # Závislosti projektu (express, puppeteer, sharp, atd.)
├── server.js          # Hlavní kód backend serveru a zpracování obrazu
├── test_client.js     # Testovací skript pro simulaci požadavku mikrokontroléru
├── bin_out/           # Složka pro generované testovací binárky (ignorováno v Gitu)
└── public/
    └── index.html     # HTML předloha (vzhled), kterou bude na Pico displeji vidět
```

## Jak začít (Lokální vývoj)

Pro spuštění v režimu lokálního vývojáře stačí stáhnout repozitář a provést instalaci závislostí. Očekává se nainstalovaný Node.js.

1.  Nainstalujte závislosti:
    ```bash
    npm install
    ```

2.  Spusťte server:
    ```bash
    npm start
    ```
    *(Tip: Běžně spouští `node server.js`)*

3.  **Kde vidím HTML:** Webový náhled aplikace najdete ve svém prohlížeči na adrese:
    [`http://localhost:3000`](http://localhost:3000)

4.  **Kde je API pro Pico:** Binární `.bin` payload pro samotný displej stahuje Pico na endpointu:
    [`http://localhost:3000/api/display`](http://localhost:3000/api/display)

## Jak to otestovat bez hw

Pokud na stole zrovna nemáte zapojené Pico W s displejem, využijte dodávaný testovací skript.

-   **Náhled v terminálu (Braillovo písmo)**
    Vyzvedne obraz a pokusí se ho simulovat v terminálu.
    ```bash
    node test_client.js
    ```

-   **Stažení hrubých (raw) dat**
    Vyzvedne obraz a uloží jej pod názvem `payload.bin` uvnitř adresáře `bin_out/`. Navíc do konzole vypíše prvních 32 bytů jako C pole (např. `0xFF, 0x00...` ), což ocení vývojáři hardwaru pro ladění struktury přímo v C/C++.
    ```bash
    node test_client.js --raw
    ```

## Jak to nasadit (Podman / Docker)

Projekt je plně připravený pro kontejnerizaci. Používá předvytvořený `Dockerfile`, který navíc rovnou instaluje systémový Chromium potřebný pro bezproblémové fungování Puppeteeru v sandboxovaném prostředí.

-   **Příkaz pro build (sestavení image):**
    ```bash
    podman build -t pico-kiosk-backend .
    ```
    *(Lze plně zaměnit za příkaz `docker build ...`)*

-   **Příkaz pro spuštění (rozběhnutí kontejneru):**
    ```bash
    podman run -d -p 3000:3000 --name pico-backend pico-kiosk-backend
    ```
    *(Tímto propojíte port 3000 kontejneru na port 3000 hostitelského stroje)*

## Důležité info pro úpravy

-   Vzhled obrazovky se kompletně definuje a upravuje ve složce **`public/index.html`** (následně lze napojit klidně i na CSS a JS z této složky).
-   Rozlišení výstupu je **napevno nastaveno na 480x320 pixelů**. Pokud v budoucnu zvolíte jiný displej (jiný počet pixelů či orientaci), musíte překalibrovat kódy v souboru **`server.js`** a adekvátně roztáhnout viewport.
