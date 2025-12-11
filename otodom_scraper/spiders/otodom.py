import scrapy
from otodom_scraper.items import OtodomScraperItem
import json
from bs4 import BeautifulSoup

class OtodomSpider(scrapy.Spider):
    name = "otodom"
    allowed_domains = ["otodom.pl"]
    start_urls = [
        "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie,rynek-wtorny/malopolskie/krakow/krakow/krakow?limit=36&ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing&page=1"
    ]
    flat_counter = 0  # licznik ogłoszeń


    def parse(self, response):
        flats = response.css('article[data-cy="listing-item"]')
        #flats = flats[:10]  # Limit do testów
        current_page = int(response.url.split("page=")[-1])
        print(f" **** Znaleziono {len(flats)} mieszkań na stronie {current_page} **** ")

        if not flats:
            self.logger.info(f"Zatrzymano scraper – brak mieszkań na stronie {current_page}")
            return

        for flat in flats:
            flat_url = flat.css('a::attr(href)').get()
            yield response.follow(flat_url, callback=self.parse_flat_page)

        next_page = current_page + 1
        base_url = response.url.split("page=")[0]
        next_page_url = f"{base_url}page={next_page}"

        yield response.follow(next_page_url, callback=self.parse)

    def parse_flat_page(self, response):
        self.flat_counter += 1
        print(f"\n=== PRZETWARZANIE {self.flat_counter}. MIESZKANIA ===")
        item = OtodomScraperItem()
        item['url'] = response.url
        item['title'] = response.css('h1::text').get(default='').strip()
        item['price'] = response.css('[data-cy="adPageHeaderPrice"]::text').get(default='').strip()
        item['price_per_m2'] = response.css('[aria-label="Cena za metr kwadratowy"]::text').get(default='').strip()

        soup = BeautifulSoup(response.text, "html.parser")

        def extract_all_attributes():
            attributes = {}
            for grid in soup.select("div.css-1xw0jqp"):
                ps = grid.find_all("p")
                if len(ps) >= 2:
                    key = ps[0].get_text(strip=True).rstrip(":")
                    value = ps[1].get_text(strip=True)
                    attributes[key] = value
            return attributes

        attributes = extract_all_attributes()

        def get_from_json(ad, *keys, default=None):
            for key in keys:
                ad = ad.get(key, {})
            return ad or default

        try:
            json_script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
            data = json.loads(json_script)
            ad = data.get('props', {}).get('pageProps', {}).get('ad', {})
        except Exception as e:
            self.logger.warning(f"Nie udało się sparsować __NEXT_DATA__: {e}")
            ad = {}

        item['area'] = ad.get('area') or attributes.get('Powierzchnia')
        item['rooms'] = ad.get('rooms_num') or attributes.get('Liczba pokoi')
        item['floor'] = ad.get('floor') or attributes.get('Piętro')
        item['rent'] = get_from_json(ad, 'monthly_costs', 'rent', 'value') or attributes.get('Czynsz')
        item['heating'] = ad.get('heating') or attributes.get('Ogrzewanie')
        item['finish'] = ad.get('construction_status') or attributes.get('Stan wykończenia')
        item['market'] = ad.get('market') or attributes.get('Rynek')
        item['ownership'] = ad.get('building_ownership') or attributes.get('Forma własności')
        item['available_from'] = ad.get('free_from') or attributes.get('Dostępne od')
        item['advertiser_type'] = ad.get('advertiser_type') or attributes.get('Typ ogłoszeniodawcy')
        item['build_year'] = ad.get('build_year') or attributes.get('Rok budowy')
        item['building_type'] = ad.get('building', {}).get('type') or attributes.get('Rodzaj zabudowy')
        item['windows'] = ad.get('windows_type') or attributes.get('Okna')
        item['material'] = ad.get('building_material') or attributes.get('Materiał budynku')
        item['lift'] = 'Tak' if ad.get('has_elevator') else attributes.get('Winda', 'Nie')

        location = response.css('[data-testid="address-link"]::text').get()
        if not location:
            location = response.css('a[href^="#map"]::text').get()
        item['location'] = location.strip() if location else ''

        raw_description = ad.get('description') if ad else None
        if raw_description:
            clean_description = BeautifulSoup(raw_description, "html.parser").get_text(separator="\n", strip=True)
        else:
            paragraph_tags = response.css('[data-testid="ad-description"] p::text').getall()
            if paragraph_tags:
                clean_description = "\n".join([p.strip() for p in paragraph_tags if p.strip()])
            else:
                text_parts = response.css('[data-testid="ad-description"] *::text').getall()
                clean_description = " ".join([part.strip() for part in text_parts if part.strip()])
        item['description'] = clean_description

        def join_list(value):
            return ', '.join(value) if isinstance(value, list) else value

        item['security'] = join_list(ad.get('security_types', [])) or attributes.get('Bezpieczeństwo', '')
        item['media'] = join_list(ad.get('media_types', [])) or attributes.get('Media', '')
        item['equipment'] = join_list(ad.get('equipment_types', [])) or ', '.join(attributes.get('Wyposażenie', '').split())
        item['extras'] = join_list(ad.get('extras_types', [])) or ', '.join(attributes.get('Informacje dodatkowe', '').split())

        yield item
