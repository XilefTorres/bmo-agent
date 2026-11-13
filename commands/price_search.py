from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from modules.base_command import BaseCommand
from modules.tts_speaker import speak, speak_stream
from modules.text_utils import remove_phrases, parse_price

class PriceSearchCommand(BaseCommand):
    def __init__(self, face, bmo_brain):
        super().__init__(face, bmo_brain)
        self._keywords = ["busca precio de", "busca precio", "cuánto cuesta", "mejor precio de", "mejor precio",
                          "compara", "qué precio tiene"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    @property
    def keywords(self): return self._keywords

    @property
    def threaded(self): return True

    def execute(self, text, actions_manager):
        producto = remove_phrases(text.lower(), self._keywords)

        if not producto:
            speak("¿Qué producto quieres que analice, Xilef?")
            return

        print(f">>> BMO recolectando datos para análisis: {producto}")

        # 1. Recolección de datos: las tres tiendas en paralelo
        tiendas = {
            "Mercado Libre": self.scrape_mercadolibre,
            "Amazon": self.scrape_amazon,
            "Liverpool": self.scrape_liverpool,
        }
        datos_encontrados = {}
        with self.face.estado("pensando"):
            with ThreadPoolExecutor(max_workers=len(tiendas)) as pool:
                futuros = {tienda: pool.submit(self._safe_scrape, tienda, fn, producto)
                           for tienda, fn in tiendas.items()}
            for tienda, futuro in futuros.items():
                info = futuro.result()
                if info:
                    datos_encontrados[tienda] = info

        if not datos_encontrados:
            self.face.show_expression("sad", 4000)
            speak("Mis sensores no detectan ese producto en las tiendas, Xilef. ¡Tal vez no existe!")
            return

        # 2. BMO lista lo que encontró (Voz y Consola)
        reporte_inicial = f"¡Encontré información de {producto}! Aquí está la lista:\n"
        print(f"\n>>> [BMO REPORT] {producto.upper()}")

        for tienda, info in datos_encontrados.items():
            reporte_inicial += f"- En {tienda}: {info['precio']} pesos.\n"
            print(f"[{tienda}] {info['nombre'][:50]}... | Precio: ${info['precio']}")

        speak(reporte_inicial)

        # 3. El precio más bajo se calcula en código; el LLM solo redacta la recomendación
        con_precio = {t: i for t, i in datos_encontrados.items() if i.get("valor") is not None}
        contexto_para_llm = ""
        for tienda, info in datos_encontrados.items():
            contexto_para_llm += f"Tienda: {tienda}. Producto: {info['nombre']}. Precio: {info['precio']} pesos. "
            if 'entrega' in info: contexto_para_llm += f"Entrega: {info['entrega']}. "
            if 'rating' in info: contexto_para_llm += f"Reseñas: {info['rating']}. "
            contexto_para_llm += "\n"

        if con_precio:
            mas_barata = min(con_precio, key=lambda t: con_precio[t]["valor"])
            dato_clave = (f"El precio más bajo ya está calculado: {mas_barata}, "
                          f"con {con_precio[mas_barata]['precio']} pesos. No hagas cuentas tú. ")
        else:
            dato_clave = ""

        prompt_bmo = (
            f"Xilef encontró estos precios para '{producto}':\n{contexto_para_llm}\n"
            f"{dato_clave}"
            "Dile a Xilef cuál recomiendas comprar tomando en cuenta ese precio más bajo, la rapidez de entrega y las reseñas. "
            "Responde como BMO de hora de aventura. Se breve, tierno y entusiasta."
        )

        # 4. Recomendación final del Cerebro
        print(">>> BMO procesando recomendación...")
        with self.face.estado("pensando"):
            recomendacion = speak_stream(self.bmo_brain.ask_stream(prompt_bmo))

        print(f"BMO (Recomendación): {recomendacion}")

    # --- SCRAPERS ---

    def _safe_scrape(self, tienda, scraper, producto):
        """Ejecuta un scraper dejando registro de por qué falló (bloqueo, timeout, cambio de HTML...)."""
        try:
            info = scraper(producto)
        except requests.RequestException as e:
            print(f"[!] {tienda}: error de red: {e}")
            return None
        except AttributeError:
            # select_one devolvió None: la tienda cambió su HTML o nos mostró un captcha
            print(f"[!] {tienda}: no encontré nombre o precio en el primer resultado.")
            return None
        if info is None:
            print(f"[!] {tienda}: sin resultados (¿producto inexistente o bloqueo?).")
            return None
        info["nombre"] = info["nombre"].strip()
        info["precio"] = info["precio"].strip()
        info["valor"] = parse_price(info["precio"])
        return info

    def _get(self, tienda, url, params=None):
        res = requests.get(url, params=params, headers=self.headers, timeout=5)
        if res.status_code != 200:
            print(f"[!] {tienda}: respondió HTTP {res.status_code}")
        return BeautifulSoup(res.text, 'html.parser')

    def scrape_mercadolibre(self, producto):
        soup = self._get("Mercado Libre", f"https://lista.mercadolibre.com.mx/{producto.replace(' ', '-')}")
        item = soup.select_one(".ui-search-result__content-wrapper")
        if not item:
            return None
        nombre = item.select_one(".ui-search-item__title").text
        precio = item.select_one(".poly-price__current .andes-money-amount__fraction").text
        # Solo miramos este resultado, no toda la página (que siempre menciona "full")
        entrega = "Full (Mañana mismo)" if "full" in str(item).lower() else "Estándar"
        return {"nombre": nombre, "precio": precio, "entrega": entrega}

    def scrape_amazon(self, producto):
        soup = self._get("Amazon", "https://www.amazon.com.mx/s", params={"k": producto})
        card = soup.select_one('div[data-component-type="s-search-result"]')
        if not card:
            return None
        nombre = card.select_one("h2 span").text
        precio = card.select_one(".a-price-whole").text
        rating = card.select_one(".a-icon-alt").text if card.select_one(".a-icon-alt") else "Sin reseñas"
        entrega = "Prime (Rápido)" if "prime" in card.text.lower() else "3-5 días"
        return {"nombre": nombre, "precio": precio, "rating": rating, "entrega": entrega}

    def scrape_liverpool(self, producto):
        soup = self._get("Liverpool", "https://www.liverpool.com.mx/tienda", params={"s": producto})
        card = soup.select_one(".m-product__card")
        if not card:
            return None
        nombre = card.select_one("h5").text
        precio_raw = card.select_one(".a-card-discountPrice").text
        return {"nombre": nombre, "precio": precio_raw}
