from pydantic import BaseModel
from datetime import date

class FidelidadeCreate(BaseModel):
    id_cliente: int
    status: str
    data_exclusao: date | None = None
