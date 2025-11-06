# api_tool.py

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import uvicorn
from db_calendar import get_calendar_by_text, get_calendar_by_month

# Inicializar la base de datos (se asegura de que la tabla exista)
# Nota: La inicialización se hace ahora dentro de db_calendar.py al importarse.

app = FastAPI(
    title="F1 Calendar API Tool",
    description="API para consultar el calendario de la Fórmula 1 2026 por GP o por mes. Diseñada para LLMs.",
    version="1.0.0"
)


# --- Definición de Pydantic para la respuesta (Schema) ---
class CalendarEntry(BaseModel):
    gp: str = Field(..., example="Gran Premio de España - Madrid")
    circuito: str = Field(..., example="Circuito urbano de Madrid (Madring)")
    desde: str = Field(..., example="11/09/2026")
    hasta: str = Field(..., example="13/09/2026")


# --- Definición de la función Tool para el LLM ---
@app.get(
    "/calendar/query",
    response_model=list[CalendarEntry],
    summary="Obtiene el calendario de F1 2026, filtrando por GP, Circuito o Mes."
)
def query_f1_calendar(
    # --- CORRECCIÓN AQUÍ: Usar Query(default=None, description=...) ---
    gp_name: str | None = Query(
        None,
        description="El nombre parcial del Gran Premio a buscar (ej: 'Barcelona')."
    ),
    circuit_name: str | None = Query(
        None, 
        description="El nombre parcial del circuito a buscar (ej: 'Monza')."
    ),
    month_name: str | None = Query(
        None,
        description="El nombre completo del mes (ej: 'junio')."
    )
):
    """
    Busca GPs por nombre de Gran Premio, circuito o mes.
    La prioridad es: GP > Circuito > Mes.
    Si todos los parametros son nulos, devuelve todo el calendario.

    :return: Una lista de objetos JSON con la información del calendario.
    """

    if gp_name:
        # Prioridad 1: Búsqueda por nombre de GP
        results = get_calendar_by_text(gp_name, 'gp')
    elif circuit_name:
        # Prioridad 2: Búsqueda por nombre de Circuito
        results = get_calendar_by_text(circuit_name, 'circuito')
    elif month_name:
        # Prioridad 3: Búsqueda por mes
        results = get_calendar_by_month(month_name)
    else:
        # Sin filtros, devolver todo (usando un query vacío de GP para retornar todo)
        results = get_calendar_by_text(search_text='', column_name='gp')

    if not results:
        # Retorna una estructura vacía si no se encuentra nada
        raise HTTPException(
            status_code=404,
            detail="No se encontró ningún Gran Premio que coincida con el nombre, circuito o mes especificado."
        )

    return results


# --- Ejecución ---
if __name__ == "__main__":
    print(f"API iniciada. Accede a la documentación en: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
