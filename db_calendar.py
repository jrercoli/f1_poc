# db_calendar.py

import sqlite3
import json
from datetime import datetime

DB_NAME = "f1_data.db"
TABLE_NAME = "calendario_2026"

CALENDAR_DATA = [
  {"desde": "06/03/2026", "hasta": "08/03/2026", "GP": "Australia", "circuito": "Albert Park"},
  {"desde": "13/03/2026", "hasta": "15/03/2026", "GP": "China", "circuito": "Internacional de Shanghái"},
  {"desde": "27/03/2026", "hasta": "29/03/2026", "GP": "Japón", "circuito": "Suzuka"},
  {"desde": "10/04/2026", "hasta": "12/04/2026", "GP": "Baréin", "circuito": "Internacional de Baréin (Sakhir)"},
  {"desde": "17/04/2026", "hasta": "19/04/2026", "GP": "Arabia Saudí", "circuito": "Jeddah Corniche"},
  {"desde": "01/05/2026", "hasta": "03/05/2026", "GP": "Miami", "circuito": "Autódromo Internacional de Miami"},
  {"desde": "22/05/2026", "hasta": "24/05/2026", "GP": "Canadá", "circuito": "Gilles Villeneuve"},
  {"desde": "05/06/2026", "hasta": "07/06/2026", "GP": "Mónaco", "circuito": "Mónaco"},
  {"desde": "12/06/2026", "hasta": "14/06/2026", "GP": "España - Barcelona", "circuito": "Barcelona-Catalunya"},
  {"desde": "26/06/2026", "hasta": "28/06/2026", "GP": "Austria", "circuito": "Red Bull Ring"},
  {"desde": "03/07/2026", "hasta": "05/07/2026", "GP": "Gran Bretaña", "circuito": "Silverstone"},
  {"desde": "17/07/2026", "hasta": "19/07/2026", "GP": "Bélgica", "circuito": "Spa-Francorchamps"},
  {"desde": "24/07/2026", "hasta": "26/07/2026", "GP": "Hungría", "circuito": "Hungaroring"},
  {"desde": "21/08/2026", "hasta": "23/08/2026", "GP": "Países Bajos", "circuito": "Zandvoort"},
  {"desde": "04/09/2026", "hasta": "06/09/2026", "GP": "Italia", "circuito": "Autodromo Nazionale Monza"},
  {"desde": "11/09/2026", "hasta": "13/09/2026", "GP": "España - Madrid", "circuito": "Circuito urbano de Madrid (Madring)"},
  {"desde": "25/09/2026", "hasta": "27/09/2026", "GP": "Azerbaiyán", "circuito": "Circuito urbano de Bakú"},
  {"desde": "09/10/2026", "hasta": "11/10/2026", "GP": "Singapur", "circuito": "Circuito urbano de Marina Bay"},
  {"desde": "23/10/2026", "hasta": "25/10/2026", "GP": "Estados Unidos", "circuito": "Circuito de las Américas (Austin)"},
  {"desde": "30/10/2026", "hasta": "01/11/2026", "GP": "México", "circuito": "Autódromo Hermanos Rodríguez"},
  {"desde": "06/11/2026", "hasta": "08/11/2026", "GP": "Brasil", "circuito": "Autódromo José Carlos Pace (Interlagos)"},
  {"desde": "19/11/2026", "hasta": "21/11/2026", "GP": "Las Vegas", "circuito": "Circuito urbano de Las Vegas"},
  {"desde": "27/11/2026", "hasta": "29/11/2026", "GP": "Catar", "circuito": "Internacional de Lusail"},
  {"desde": "04/12/2026", "hasta": "06/12/2026", "GP": "Abu Dabi", "circuito": "Yas Marina"}
]


def _format_results(cursor):
    """Format the query results as a list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _get_month_number(month_name: str) -> str | None:
    """Translate the name of the month to its 2-digit number."""
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04", 
        "may": "05", "june": "06", "july": "07", "august": "08", 
        "september": "09", "october": "10", "november": "11", "december": "12"
    }
    return month_map.get(month_name.lower(), None)


def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Crete table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY,
            gp TEXT NOT NULL,
            circuito TEXT NOT NULL,
            desde TEXT NOT NULL,
            hasta TEXT NOT NULL
        )
    """)
    conn.commit()

    # 2. Insert data if empty
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    if cursor.fetchone()[0] == 0:
        # print("Tabla del calendario vacía. Insertando 24 GPs.") # Usar print o logger fuera de Streamlit
        for item in CALENDAR_DATA:
            cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (gp, circuito, desde, hasta)
                VALUES (?, ?, ?, ?)
            """, (item['GP'], item['circuito'], item['desde'], item['hasta']))
        conn.commit()
    # else:
        # print("Tabla del calendario ya tiene datos.")

    conn.close()


# --- Consulta por nombre de GP (se mantiene igual) ---
def get_calendar_by_text(search_text: str, column_name: str):
    """
    Check the calendar for partial text in the GP or circuit name.

    :param search_text: The partial text to search for (e.g., 'Barcelona' or 'Spain').
    :param column_name: 'gp' or 'circuito'.
    """
    if column_name not in ['gp', 'circuito']:
        return []

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Usamos la columna especificada y LIKE para búsqueda parcial.
    query = f"SELECT gp, circuito, desde, hasta FROM {TABLE_NAME} WHERE {column_name} LIKE ?"
    cursor.execute(query, ('%' + search_text + '%',))

    results = _format_results(cursor)
    conn.close()
    return results


def get_calendar_by_month(month_name: str):
    """
    Search for GPs whose 'from' or 'to' field falls within the specified month.
    """
    month_num = _get_month_number(month_name)
    if not month_num:
        return []

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    month_pattern = f'%/{month_num}/%'
    query = f"""
        SELECT gp, circuito, desde, hasta 
        FROM {TABLE_NAME} 
        WHERE desde LIKE ? OR hasta LIKE ?
    """
    cursor.execute(query, (month_pattern, month_pattern))

    results = _format_results(cursor)
    conn.close()
    return results


initialize_db()
