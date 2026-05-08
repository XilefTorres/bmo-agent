import requests
from bs4 import BeautifulSoup
from modules.base_command import BaseCommand
from modules.tts_speaker import speak

class PriceSearchCommand(BaseCommand):
    def __init__(self, face, bmo_brain):
        super().__init__(face, bmo_brain)
        self._keywords = ["busca precio", "cuánto cuesta", "mejor precio", "compara", "que precio tiene"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    @property
    def keywords(self): return self._keywords

    @property
    def threaded(self): return True

    def execute(self, text, actions_manager):
        producto = text.lower()
        for kw in self._keywords:
            producto = producto.replace(kw, "")
        producto = producto.strip()

        if not producto:
            speak("¿Qué producto quieres que analice, Xilef?")
            return

        self.face.set_state("pensando")
        print(f">>> BMO recolectando datos para análisis: {producto}")
        
        datos_encontrados = {}
        
        # 1. Recolección de datos crudos
        ml = self.scrape_mercadolibre(producto)
        amz = self.scrape_amazon(producto)
        lvp = self.scrape_liverpool(producto)

        if ml: datos_encontrados['Mercado Libre'] = ml
        if amz: datos_encontrados['Amazon'] = amz
        if lvp: datos_encontrados['Liverpool'] = lvp

        if not datos_encontrados:
            self.face.set_state("triste")
            speak("Mis sensores no detectan ese producto en las tiendas, Xilef. ¡Tal vez no existe!")
            return

        # 2. BMO lista lo que encontró (Voz y Consola)
        self.face.set_state("hablando")
        reporte_inicial = f"¡Encontré información de {producto}! Aquí está la lista:\n"
        print(f"\n>>> [BMO REPORT] {producto.upper()}")
        
        for tienda, info in datos_encontrados.items():
            linea = f"- En {tienda}: {info['precio']} pesos."
            reporte_inicial += linea + "\n"
            print(f"[{tienda}] {info['nombre'][:50]}... | Precio: ${info['precio']}")
        
        speak(reporte_inicial)

        # 3. Preparar contexto para el LLM
        contexto_para_llm = ""
        for tienda, info in datos_encontrados.items():
            contexto_para_llm += f"Tienda: {tienda}. Producto: {info['nombre']}. Precio: {info['precio']}. "
            if 'entrega' in info: contexto_para_llm += f"Entrega: {info['entrega']}. "
            if 'rating' in info: contexto_para_llm += f"Reseñas: {info['rating']}. "
            contexto_para_llm += "\n"

        prompt_bmo = (
            f"Xilef encontró estos precios para '{producto}':\n{contexto_para_llm}\n"
            "Dime cuál recomiendas comprar basándote en el precio más bajo, la rapidez de entrega y las reseñas. "
            "Responde como BMO de hora de aventura. Se breve, tierno y entusiasta."
        )

        # 4. Recomendación final del Cerebro
        print(">>> BMO procesando recomendación...")
        self.face.set_state("pensando")
        recomendacion = self.bmo_brain.ask(prompt_bmo)
        
        self.face.set_state("hablando")
        print(f"BMO (Recomendación): {recomendacion}")
        speak(recomendacion)
        
        self.face.set_state("esperando")

    # --- SCRAPERS MEJORADOS ---

    def scrape_mercadolibre(self, producto):
        try:
            url = f"https://lista.mercadolibre.com.mx/{producto.replace(' ', '-')}"
            res = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            item = soup.select_one(".ui-search-result__content-wrapper")
            if item:
                nombre = item.select_one(".ui-search-item__title").text
                precio = item.select_one(".poly-price__current .andes-money-amount__fraction").text
                entrega = "Full (Mañana mismo)" if "full" in res.text.lower() else "Estándar"
                return {"nombre": nombre, "precio": precio, "entrega": entrega}
        except: return None

    def scrape_amazon(self, producto):
        try:
            url = f"https://www.amazon.com.mx/s?k={producto.replace(' ', '+')}"
            res = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            card = soup.select_one('div[data-component-type="s-search-result"]')
            if card:
                nombre = card.select_one("h2 span").text
                precio = card.select_one(".a-price-whole").text
                rating = card.select_one(".a-icon-alt").text if card.select_one(".a-icon-alt") else "Sin reseñas"
                entrega = "Prime (Rápido)" if "prime" in card.text.lower() else "3-5 días"
                return {"nombre": nombre, "precio": precio, "rating": rating, "entrega": entrega}
        except: return None

    def scrape_liverpool(self, producto):
        try:
            url = f"https://www.liverpool.com.mx/tienda?s={producto.replace(' ', '+')}"
            res = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            card = soup.select_one(".m-product__card")
            if card:
                nombre = card.select_one("h5").text
                precio_raw = card.select_one(".a-card-discountPrice").text
                return {"nombre": nombre, "precio": precio_raw}
        except: return None