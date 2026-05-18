# client_finder

Encontra CNPJs e endereços de **empresas de médio e grande porte** num raio geográfico a partir de qualquer endereço.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### Busca rápida (modo `quick`)

Usa OpenStreetMap/Overpass. **Não requer setup**, mas cobertura é parcial.

```bash
python main.py search "Av. Paulista, 1000, São Paulo, SP"
python main.py search "Rua XV de Novembro, Curitiba" --radius 3
python main.py search "Praça da Sé, São Paulo" --output json --save resultado.json
```

### Busca completa (modo `full`) — RECOMENDADO

Usa os **dados abertos da Receita Federal** (todos os CNPJs do Brasil).

#### Passo 1 — Import único (~30-60 min, ~10 GB disco)

```bash
python main.py import
```

#### Passo 2 (opcional, acelera buscas) — Pré-geocodificar CEPs do estado

```bash
python main.py geocode-ceps SP --batch 500
```

#### Passo 3 — Buscar

```bash
python main.py search "Av. Paulista, 1000, São Paulo" --mode full
python main.py search "Rua das Flores, 200, Porto Alegre" --mode full --radius 3
python main.py search "SCN Qd 2, Brasília" --mode full --output csv --save empresas.csv
```

## Opções

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `--radius` / `-r` | Raio em km | `5.0` |
| `--mode` / `-m` | `quick` ou `full` | `quick` |
| `--output` / `-o` | `table`, `json`, `csv` | `table` |
| `--limit` / `-l` | Máx. resultados | `500` |
| `--save` / `-s` | Salvar em arquivo | — |

## Comandos

```
python main.py search   ENDEREÇO [opções]   # Busca por raio
python main.py import  [--year YYYY] [--month MM]  # Importa dados RF
python main.py geocode-ceps UF [--batch N]          # Pré-geocodifica CEPs
python main.py status                               # Status do banco
```

## Como funciona

### Porte das empresas

A Receita Federal classifica as empresas em:

| Código | Classificação |
|--------|--------------|
| ME | Micro Empresa (receita ≤ R$ 360k/ano) |
| EPP | Empresa de Pequeno Porte (≤ R$ 4,8M/ano) |
| **DEMAIS** | **Médio e Grande porte** — target desta busca |

### Fontes de dados

| Modo | Fonte | Cobertura |
|------|-------|-----------|
| `quick` | OpenStreetMap via Overpass API | Parcial (dados voluntários) |
| `full` | Receita Federal — Dados Abertos CNPJ | 100% (todos CNPJs ativos) |

### Dados armazenados

```
~/.client_finder/
├── data.db       # SQLite: empresas + estabelecimentos + cache de CEPs
└── raw/          # ZIPs da Receita Federal (podem ser removidos após import)
```

## Campos retornados

- CNPJ (formatado e bruto)
- Razão Social e Nome Fantasia
- Porte
- Endereço completo (logradouro, número, bairro, CEP, município, UF)
- Telefone e e-mail
- Distância em km do ponto de busca
- Fonte dos dados (`RF` ou `OSM`)
