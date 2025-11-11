# api_tool.py

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import uvicorn
from db_calendar import get_calendar_by_text, get_calendar_by_month

# Inicializar la base de datos (se asegura de que la tabla exista)
# Nota: La inicialización se hace ahora dentro de db_calendar.py al importarse.

app = FastAPI(
    title="F1 Calendar API Tool",
    description="API to query the 2026 Formula 1 calendar by GP or month. Designed for LLMs",
    version="1.0.0"
)


# --- Definición de Pydantic para la respuesta (Schema) ---
class CalendarEntry(BaseModel):
    gp: str = Field(..., example="Gran Premio de España - Madrid")
    circuito: str = Field(..., example="Circuito urbano de Madrid (Madring)")
    desde: str = Field(..., example="11/09/2026")
    hasta: str = Field(..., example="13/09/2026")


# --- API definition for LLM Tool function ---
@app.get(
    "/calendar/query",
    response_model=list[CalendarEntry],
    summary="Get the 2026 F1 calendar, filtering by GP, Circuit or Month."
)
def query_f1_calendar(
    # --- CORRECCIÓN AQUÍ: Usar Query(default=None, description=...) ---
    gp_name: str | None = Query(
        None,
        description="The partial name of the Grand Prix to search for ('Barcelona')."
    ),
    circuit_name: str | None = Query(
        None, 
        description="The partial name of the circuit to search for ('Monza')."
    ),
    month_name: str | None = Query(
        None,
        description="The full name of the month ('June')."
    )
):
    """
    Search for Grand Prix races by Grand Prix name, circuit, or month.
    Priority: GP > Circuit > Month.
    If all parameters are null, return the entire calendar.

    :return: A list of JSON objects containing the calendar information.
    """

    if gp_name:        
        results = get_calendar_by_text(gp_name, 'gp')
    elif circuit_name:        
        results = get_calendar_by_text(circuit_name, 'circuito')
    elif month_name:        
        results = get_calendar_by_month(month_name)
    else:
        # Without filters, return everything (using an empty GP query to return everything)
        results = get_calendar_by_text(search_text='', column_name='gp')

    if not results:
        # Retorna una estructura vacía si no se encuentra nada
        raise HTTPException(
            status_code=404,
            detail="No Grand Prix was found that matches the specified name, circuit, or month."
        )

    return results


if __name__ == "__main__":
    print(f"API launched. Access the documentation at: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
