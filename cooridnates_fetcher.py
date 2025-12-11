import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tqdm import tqdm
import time

# === USTAWIENIA GŁÓWNE ===
INPUT_FILE = "mieszkania_otodom.csv"
BATCH_SIZE = 500
driver_path = "chromedriver.exe"

# === Konfiguracja Chrome ===
options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
service = ChromeService(executable_path=driver_path)


def smooth_scroll(driver, pixels=3000, step=100, delay=0.1):
    for i in range(0, pixels, step):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(delay)

def process_batch(df_batch, batch_number):
    driver = webdriver.Chrome(service=service, options=options)

    coords = []
    coord_type = []
    success = 0

    for idx, row in tqdm(df_batch.iterrows(), total=len(df_batch), desc=f"Batch {batch_number}"):
        url = row['url']
        lat, lng = None, None
        typ = "brak"

        for attempt in range(2): 
            try:
                driver.get(url)

                try:
                    accept_btn = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Akceptuję")]'))
                    )
                    accept_btn.click()
                    time.sleep(1)
                except:
                    pass

                smooth_scroll(driver)
                time.sleep(1)

                WebDriverWait(driver, [10, 20][attempt]).until(
                    EC.presence_of_element_located((By.TAG_NAME, "gmp-advanced-marker"))
                )

                soup = BeautifulSoup(driver.page_source, "html.parser")
                marker = soup.find("gmp-advanced-marker")

                if marker and marker.has_attr("position"):
                    lat, lng = marker["position"].split(",")
                    typ = "dokładne"
                    success += 1
                else:
                    typ = "przybliżone"

                break  

            except:
                if attempt == 1:
                    typ = "brak"
                time.sleep(1)

        coords.append((lat, lng))
        coord_type.append(typ)

    driver.quit()

    df_batch["latitude"], df_batch["longitude"] = zip(*coords)
    df_batch["coord_type"] = coord_type

    output_file = f"mieszkania_z_koordynatami_batch_{batch_number}.csv"
    df_batch.to_csv(output_file, index=False)
    print(f"Zapisano: {output_file} (dokładne: {success})")

# Wczytanie danych i batch processing 
df_all = pd.read_csv(INPUT_FILE)

# Przetwórz w partiach
for start in range(0, len(df_all), BATCH_SIZE):
    end = min(start + BATCH_SIZE, len(df_all))
    batch_number = start // BATCH_SIZE + 1
    df_batch = df_all.iloc[start:end].copy()

    output_file = f"mieszkania_z_koordynatami_batch_{batch_number}.csv"
    if os.path.exists(output_file):
        print(f"Pomijam batch {batch_number} (plik już istnieje)")
        continue

    process_batch(df_batch, batch_number)