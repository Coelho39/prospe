import requests
import time
import random
from typing import List, Dict, Optional

class SerpAPIClient:
    """Cliente para interagir com a SERP API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_local_businesses(
        self, 
        query: str, 
        location: str = "Pará, Brasil",
        num_results: int = 20,
        enable_filters: bool = True
    ) -> List[Dict]:
        """
        Busca empresas locais usando Google Maps via SERP API
        """
        # Melhor query específica para mineradoras no Pará
        enhanced_query = f"{query} Pará Brasil"
        
        params = {
            "engine": "google_maps",
            "q": enhanced_query,
            "ll": "@-3.731862,-52.325249,12z",  # Coordenadas do centro do Pará com zoom mais focado
            "type": "search",
            "api_key": self.api_key,
            "num": min(num_results, 100),  # Limite da API
            "hl": "pt",
            "gl": "br"
        }
        
        # Remove parâmetros None
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                raise Exception(f"SERP API Error: {data['error']}")
            
            local_results = data.get('local_results', [])
            
            # Processa e filtra resultados
            processed_results = []
            for result in local_results:
                processed_result = self._process_local_result(result, enable_filters)
                if processed_result:
                    processed_results.append(processed_result)
            
            return processed_results
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro de conexão com SERP API: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro ao processar resposta da SERP API: {str(e)}")
    
    def _process_local_result(self, result: Dict, enable_filters: bool = True) -> Optional[Dict]:
        """Processa um resultado individual do Google Maps"""
        
        # Extrai dados básicos
        name = result.get('title', '').strip()
        address = result.get('address', '').strip()
        phone = result.get('phone', '').strip()
        website = result.get('website', '').strip()
        rating = result.get('rating')
        reviews = result.get('reviews')
        
        # Filtros específicos para mineração (se habilitado)
        if enable_filters and name:
            mining_keywords = [
                # Principais termos de mineração
                'mineração', 'mineradora', 'minério', 'extração', 'mina', 'lavra',
                'garimpo', 'garimpeira', 'cooperativa', 'associação',
                
                # Minerais específicos do Pará
                'ferro', 'bauxita', 'ouro', 'cobre', 'alumínio', 'manganês', 
                'níquel', 'estanho', 'cassiterita', 'caulim', 'calcário',
                'granito', 'quartzito', 'gemas', 'diamante', 'esmeralda',
                
                # Agregados e materiais de construção
                'pedreira', 'areia', 'brita', 'cascalho', 'argila', 'saibro',
                'britagem', 'peneiramento', 'beneficiamento',
                
                # Atividades de apoio
                'equipamentos mineração', 'perfuração', 'desmonte', 
                'terraplanagem', 'dragagem', 'consultoria mineral',
                'explosivos', 'pelotização', 'concentração', 'flotação'
            ]
            
            name_lower = name.lower()
            description_lower = result.get('snippet', '').lower()
            type_lower = result.get('type', '').lower()
            address_lower = address.lower() if address else ''
            
            # Verifica se contém palavras-chave de mineração
            has_mining_keyword = any(
                keyword in name_lower or 
                keyword in description_lower or 
                keyword in type_lower or
                keyword in address_lower
                for keyword in mining_keywords
            )
            
            # Filtros de exclusão mais rigorosos
            exclude_keywords = [
                'restaurante', 'lanchonete', 'bar', 'hotel', 'pousada', 'motel',
                'supermercado', 'farmácia', 'posto', 'oficina', 'loja', 'shopping',
                'escola', 'hospital', 'clínica', 'banco', 'agência', 'cartório',
                'advocacia', 'escritório', 'contabilidade', 'imobiliária',
                'igreja', 'templo', 'salão', 'barbearia', 'academia', 'veterinária'
            ]
            
            has_exclude_keyword = any(
                keyword in name_lower or keyword in description_lower
                for keyword in exclude_keywords
            )
            
            # Verifica se está no estado do Pará
            para_indicators = ['pará', 'pa', 'belém', 'marabá', 'santarém', 'altamira', 'parauapebas', 'carajás']
            is_in_para = any(
                indicator in address_lower or indicator in description_lower
                for indicator in para_indicators
            )
            
            # Se não tem palavra-chave de mineração OU tem palavra de exclusão OU não está no Pará, pula
            if not has_mining_keyword or has_exclude_keyword or not is_in_para:
                return None
        
        # Retorna apenas se tiver nome válido
        if not name:
            return None
        
        return {
            'name': name,
            'address': address,
            'phone': phone,
            'website': website,
            'rating': rating,
            'reviews': reviews,
            'type': result.get('type', ''),
            'snippet': result.get('snippet', ''),
            'place_id': result.get('place_id', ''),
            'coordinates': {
                'lat': result.get('gps_coordinates', {}).get('latitude'),
                'lng': result.get('gps_coordinates', {}).get('longitude')
            }
        }
    
    def search_web(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Busca web geral (fallback)
        """
        params = {
            "engine": "google",
            "q": f"{query} site:gov.br OR site:com.br OR site:org.br",
            "api_key": self.api_key,
            "num": min(num_results, 100),
            "hl": "pt",
            "gl": "br"
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                raise Exception(f"SERP API Error: {data['error']}")
            
            organic_results = data.get('organic_results', [])
            
            processed_results = []
            for result in organic_results:
                processed_results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'source': 'web_search'
                })
            
            return processed_results
            
        except Exception as e:
            raise Exception(f"Erro na busca web: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """Valida se a API key está funcionando"""
        try:
            params = {
                "engine": "google",
                "q": "test",
                "api_key": self.api_key,
                "num": 1
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            return 'error' not in data
            
        except Exception:
            return False
