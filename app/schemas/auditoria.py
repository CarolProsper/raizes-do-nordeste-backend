from datetime import datetime

from pydantic import BaseModel


class AuditoriaCreate(BaseModel):
    id_funcionario: int
    tipo_ocorrencia: str
    objeto_ocorrencia: str
    registro_ocorrencia: str
    data_hora_ocorrencia: datetime