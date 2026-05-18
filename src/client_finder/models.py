from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Empresa:
    cnpj: str
    razao_social: str
    nome_fantasia: str
    porte: str
    porte_desc: str
    logradouro: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    municipio: str
    uf: str
    telefone: str
    email: str
    distancia_km: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    fonte: str = "rf"

    @property
    def cnpj_formatado(self) -> str:
        c = self.cnpj.zfill(14)
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"

    @property
    def endereco_completo(self) -> str:
        partes = [
            f"{self.logradouro}, {self.numero}".strip(", "),
            self.complemento,
            self.bairro,
            self.municipio,
            self.uf,
            self.cep,
        ]
        return " — ".join(p for p in partes if p and p.strip())


@dataclass
class SearchResult:
    endereco_buscado: str
    lat_centro: float
    lng_centro: float
    raio_km: float
    total: int
    empresas: list[Empresa] = field(default_factory=list)
