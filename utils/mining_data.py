# utils/mining_data.py

# Dicionário com os termos de busca para a prospecção
MINING_SEARCH_TERMS = {
    "Extracao Ferro": {
        "description": "Busca por mineradoras de ferro",
        "query": "extração de minério de ferro"
    },
    "Extracao Bauxita": {
        "description": "Busca por mineradoras de bauxita/alumínio",
        "query": "extração de bauxita"
    },
    "Extracao Ouro": {
        "description": "Busca por extração de ouro e garimpos",
        "query": "mineração de ouro"
    },
    "Extracao Cobre": {
        "description": "Busca por mineradoras de cobre",
        "query": "mineração de cobre"
    },
    "Extracao Manganes": {
        "description": "Busca por mineradoras de manganês",
        "query": "extração de manganês"
    },
    "Pedreiras": {
        "description": "Busca por pedreiras (brita, areia, cascalho)",
        "query": "pedreira brita cascalho"
    },
    "Equipamentos Mineracao": {
        "description": "Fornecedores de equipamentos de mineração",
        "query": "equipamentos para mineração"
    },
    "Cooperativas Garimpeiros": {
        "description": "Busca por cooperativas de garimpeiros",
        "query": "cooperativa de garimpeiros"
    }
}

# Dicionário com CNAEs relevantes para mineração (pode ser usado no futuro)
MINING_CNAES = {
    "0710-3/01": "Extração de minério de ferro",
    "0721-9/01": "Extração de minério de alumínio",
    "0724-3/01": "Extração de minério de metais preciosos",
    "0729-4/04": "Extração de minérios de cobre, chumbo, zinco e outros",
    "0810-0/00": "Extração de pedra, areia e argila",
    "0990-4/01": "Atividades de apoio à extração de minério de ferro",
    "0990-4/02": "Atividades de apoio à extração de minerais metálicos não ferrosos",
    "0990-4/03": "Atividades de apoio à extração de minerais não metálicos"
}
