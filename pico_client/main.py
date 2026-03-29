import network
import time
import requests # V MicroPythonu to funguje podobně jako v běžném Pythonu
import secrets # Custom secrets module with WiFi credentials

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Nastavení power managementu pro lepší stabilitu (Pico W specifikum)
    wlan.config(pm=0xa11140) 
    
    wlan.connect(secrets.SSID, secrets.PASSWORD)
    
    print("Pripojovani k WiFi...")
    max_wait = 15
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("Cekam...")
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('Pripojeni k WiFi selhalo!')
    else:
        status = wlan.ifconfig()
        print('Pripojeno k WiFi! IP adresa:', status[0])

def fetch_and_print_image():
    print(f"\nStahuji data z {secrets.SERVER_URL} ...")
    
    try:
        # HTTP GET request
        response = requests.get(secrets.SERVER_URL)
        
        if response.status_code == 200:
            # Přečteme binární payload do paměti (Pico W má 264KB RAM, 19.2KB se vejde hravě)
            data = response.content
            print(f"Uspesne stazeno {len(data)} bytu!\n")
            
            # --- Vykreslení do terminálu ---
            width = 480
            height = 320
            step_x = 4 # Vykreslíme každý 4. pixel (aby se to vešlo na šířku monitoru)
            step_y = 8 # Vykreslíme každý 8. pixel (terminálové znaky jsou vysoké)
            
            print('+' + '-' * (width // step_x) + '+')
            
            for y in range(0, height, step_y):
                line_str = '|'
                for x in range(0, width, step_x):
                    # Zjištění, ve kterém bytu a bitu se pixel nachází (stejná matematika jako v JS)
                    bit_index = y * width + x
                    byte_index = bit_index // 8
                    bit_in_byte = 7 - (bit_index % 8)
                    
                    # Logický AND pro zjištění hodnoty bitu (zda je černý)
                    is_black = data[byte_index] & (1 << bit_in_byte)
                    
                    if is_black:
                        line_str += '█' # Znak pro černý pixel
                    else:
                        line_str += ' ' # Mezera pro bílý pixel
                        
                line_str += '|'
                print(line_str)
                
            print('+' + '-' * (width // step_x) + '+')
            print("\nVykreslovani dokonceno. Cekam na dalsi cyklus...")
            
        else:
            print(f"Chyba serveru: Status {response.status_code}")
            
    except Exception as e:
        print(f"Chyba pri stahovani: {e}")
    finally:
        # Je dobré zavřít spojení, abychom nevyčerpali paměť (sockets)
        if 'response' in locals():
            response.close()

# --- HLAVNÍ SMYČKA ---
try:
    connect_wifi()
    
    # Zatím to necháme běžet v nekonečné smyčce, ať vidíme, že to žije
    while True:
        fetch_and_print_image()
        time.sleep(10) # Počká 10 vteřin a stáhne to znovu

except KeyboardInterrupt:
    print("\nProgram ukoncen uzivatelem.")
except Exception as e:
    print(f"\nKriticka chyba: {e}")