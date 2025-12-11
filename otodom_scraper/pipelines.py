# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re

# Zestaw opcji z Otodom do rozpoznawania i czyszczenia
EQUIPMENT_OPTIONS = [
    "meble", "zmywarka", "kuchenka", "telewizor",
    "pralka", "lodówka", "piekarnik"
]

SECURITY_OPTIONS = [
    "rolety antywłamaniowe", "drzwi / okna antywłamaniowe",
    "domofon / wideofon", "monitoring / ochrona",
    "system alarmowy", "teren zamknięty"
]

EXTRAS_OPTIONS = [
    "balkon", "garaż/miejsce parkingowe", "ogród", "winda",
    "oddzielna kuchnia", "pom. użytkowe", "piwnica", "taras",
    "dwupoziomowe", "klimatyzacja"
]

MEDIA_OPTIONS = [
    "internet", "telefon", "telewizja kablowa"
]

def match_keywords(text, options):
    found = []
    for option in options:
        pattern = option.lower().replace(" / ", "|").replace(" ", "[\\s-]?")
        if re.search(pattern, text.lower()):
            found.append(option)
    return found

class OtodomScraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # --- price ---
        if adapter.get('price'):
            price_clean = re.sub(r"[^\d]", "", adapter['price'])
            adapter['price'] = float(price_clean) if price_clean else None

        # --- price_per_m2 ---
        if adapter.get('price_per_m2'):
            ppm_clean = re.sub(r"[^\d]", "", adapter['price_per_m2'])
            adapter['price_per_m2'] = float(ppm_clean) if ppm_clean else None

        # --- area ---
        if adapter.get('area'):
            area_clean = adapter['area'].replace(",", ".")
            area_clean = re.sub(r"[^\d.]", "", area_clean)
            adapter['area'] = float(area_clean) if area_clean else None

        # --- rent ---
        if adapter.get('rent'):
            rent_clean = re.sub(r"[^\d]", "", str(adapter['rent']))
            adapter['rent'] = float(rent_clean) if rent_clean else None

        # --- floor: split into floor_number and total_floors ---
        if adapter.get('floor') and "/" in adapter['floor']:
            floor_str = adapter['floor'].split("/")
            try:
                adapter['floor_number'] = int(re.sub(r"[^\d]", "", floor_str[0]))
                adapter['total_floors'] = int(re.sub(r"[^\d]", "", floor_str[1]))
            except ValueError:
                adapter['floor_number'] = None
                adapter['total_floors'] = None

                # --- location: split into street, district, city, region ---
        if adapter.get('location'):
            parts = [part.strip() for part in adapter['location'].split(",")]

            def is_street(text):
                return text.lower().startswith(("ul.", "pl.", "al.", "os.", "ulica", "plac", "aleja"))

            if parts and is_street(parts[0]):
                adapter['street'] = parts[0]
                # pozostałe pola zgodnie z kolejnością
                if len(parts) >= 5:
                    adapter['neighbourhood'] = parts[1]
                    adapter['district'] = parts[2]
                    adapter['city'] = parts[3]
                    adapter['region'] = parts[4]
            else:
                adapter['street'] = None
                # traktuj pierwszy element jako osiedle
                if len(parts) >= 4:
                    adapter['neighbourhood'] = parts[0]
                    adapter['district'] = parts[1]
                    adapter['city'] = parts[2]
                    adapter['region'] = parts[3]
                elif len(parts) >= 3:
                    adapter['neighbourhood'] = None
                    adapter['district'] = parts[0]
                    adapter['city'] = parts[1]
                    adapter['region'] = parts[2]

        # --- convert comma/space-separated fields to lists ---
        list_fields = ['equipment', 'extras', 'media', 'security']
        # --- dopasowanie do list zdefiniowanych opcji ---
        if adapter.get('equipment'):
            adapter['equipment'] = match_keywords(adapter['equipment'], EQUIPMENT_OPTIONS)
        if adapter.get('extras'):
            adapter['extras'] = match_keywords(adapter['extras'], EXTRAS_OPTIONS)
        if adapter.get('security'):
            adapter['security'] = match_keywords(adapter['security'], SECURITY_OPTIONS)
        if adapter.get('media'):
            adapter['media'] = match_keywords(adapter['media'], MEDIA_OPTIONS)

        return item