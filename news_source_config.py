import pytz

# Define UTC for scraper comparisons
UTC = pytz.timezone('UTC')
# ISO 8601 con Z
ISO_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# -------------------------------------------------------------------
# MAPA DE CONFIGURACIÓN DE FUENTES (F1_SOURCE_CONFIG)
# lógica de extracción de fecha para cada sitio web.
# -------------------------------------------------------------------
F1_SOURCE_CONFIG = {    
    "https://es.motorsport.com/f1/news/": {
        "source": "MotorSport F1",
        "driver": "F1 News",
        "date_selector": 'time.ms-date-with-timezone',  # Selector CSS para el tag time
        "date_attribute": "datetime",                   # Atributo que contiene la fecha 'datetime'
        "date_format": ISO_FORMAT,                      # Formato de fecha ISO: '2025-11-06T19:56:12Z'        
    }
}
'''
"https://www.caranddriver.com/es/formula-1/": {
        "source": "Car and Driver F1",
        "driver": "F1 News",
        "date_selector": 'meta[name="sailthru.date"]',  # Selector CSS para el tag meta
        "date_attribute": "content",                    # Atributo del tag que contiene la fecha
        "date_format": '%Y-%m-%d %H:%M:%S',             # Formato de fecha esperado: '2025-11-06 20:00:00'
    },
'''
# -------------------------------------------------------------------
# LISTA DE FUENTES (F1_SOURCES)
# Se genera a partir del mapa de configuración para la iteración del scraper.
# -------------------------------------------------------------------
F1_SOURCES = [{"url": url, **config} for url, config in F1_SOURCE_CONFIG.items()]

# -------------------------------------------------------------------
# PALABRAS CLAVE (F1_KEYWORDS)
# Usadas para determinar la relevancia de los artículos.
# -------------------------------------------------------------------
F1_KEYWORDS = ['f1', 'fórmula 1', 'formula 1', 'verstappen', 'hamilton', 'alonso', 'sainz', 'wolff',
               'leclerc', 'red bull', 'mercedes', 'ferrari', 'gp', 'gran premio', 'aston martin'
               'mclaren', 'alpine', 'pit stop', 'parrilla', 'carrera', 'colapinto']

# -------------------------------------------------------------------
# VARIABLES GLOBALES
# Se exportan para uso en otros módulos si es necesario.
# -------------------------------------------------------------------
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
]
