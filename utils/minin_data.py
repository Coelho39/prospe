import requests
import time
import random
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import streamlit as st

class DataEnricher:
    """Classe para enriquecimento de dados das empresas"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def enrich_companies(
        self, 
        companies: List[Dict], 
        include_cnpj: bool = True,
        include_contacts: bool = True,
        progress_callback=None
    ) -> List[Dict]:
        """Enriquece dados das empresas"""
        
        enriched_companies = []
        total = len(companies)
        
        for i, company in enumerate(companies):
            try:
                enriched_company = company.copy()
                
                # Enriquecimento via CNPJ
                if include_cnpj:
                    cnpj_data = self._search_cnpj_data(company.get('name', ''))
                    if cnpj_data:
                        enriched_company.update(cnpj_data)
                
                # Enriquecimento de contatos
                if include_contacts:
                    website = company.get('website')
                    if website and isinstance(website, str):
                        contact_data = self._extract_contacts_from_website(website)
                        if contact_data:
                            enriched_company.update(contact_data)
                        
                        # Busca redes sociais
                        social_data = self._extract_social_media(website)
                        if social_data:
                            enriched_company['social_media'] = social_data
                
                enriched_companies.append(enriched_company)
                
                # Callback de progresso
                if progress_callback:
                    progress_callback((i + 1) / total)
                
                # Delay anti-bloqueio
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                # Em caso de erro, mantém os dados originais
                enriched_companies.append(company)
                continue
        
        return enriched_companies
    
    def _search_cnpj_data(self, company_name: str) -> Optional[Dict]:
        """Busca dados de CNPJ usando APIs públicas"""
        if not company_name:
            return None
        
        # Tenta encontrar CNPJ via cnpj.biz
        cnpj_data = self._search_cnpj_biz(company_name)
        if cnpj_data and cnpj_data.get('cnpj'):
            # Se encontrou CNPJ, busca mais detalhes nas APIs oficiais
            official_data = self._get_cnpj_official_data(cnpj_data['cnpj'])
            if official_data:
                cnpj_data.update(official_data)
        
        return cnpj_data
    
    def _search_cnpj_biz(self, company_name: str) -> Optional[Dict]:
        """Busca CNPJ no site cnpj.biz"""
        try:
            # Limpa o nome da empresa para busca
            query = re.sub(r'[^\w\s]', ' ', company_name).strip()
            query = re.sub(r'\s+', '+', query)
            
            url = f"https://cnpj.biz/search/{query}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Procura links para páginas de empresas
            empresa_links = []
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if "/cnpj/" in href:
                    from urllib.parse import urljoin
                    full_url = urljoin("https://cnpj.biz", href)
                    empresa_links.append(full_url)
            
            if not empresa_links:
                return None
            
            # Acessa a primeira empresa encontrada
            detail_response = self.session.get(empresa_links[0], timeout=15)
            detail_response.raise_for_status()
            
            detail_soup = BeautifulSoup(detail_response.text, "html.parser")
            page_text = detail_soup.get_text()
            
            # Extrai CNPJ
            cnpj_match = re.search(r'(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2})', page_text)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            
            # Extrai sócios
            socios_patterns = [
                r'Sócio[:\s]*([^\n\r]+)',
                r'Administrador[:\s]*([^\n\r]+)',
                r'Diretor[:\s]*([^\n\r]+)'
            ]
            socios = []
            for pattern in socios_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    match = match.strip()
                    if match and len(match) > 3:
                        socios.append(match)
            
            # Remove duplicatas
            socios = list(set(socios))
            
            # Extrai email
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
            email = email_match.group(0).lower() if email_match else None
            
            return {
                'cnpj': cnpj,
                'socios': ', '.join(socios) if socios else None,
                'email_cnpj': email
            }
            
        except Exception:
            return None
    
    def _get_cnpj_official_data(self, cnpj: str) -> Optional[Dict]:
        """Busca dados oficiais do CNPJ em APIs públicas"""
        if not cnpj:
            return None
        
        # Limpa CNPJ
        cnpj_limpo = re.sub(r'\D', '', cnpj)
        if len(cnpj_limpo) != 14:
            return None
        
        # Lista de APIs para tentar
        apis = [
            f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}",
            f"https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}",
            f"https://publica.cnpj.ws/cnpj/{cnpj_limpo}"
        ]
        
        for api_url in apis:
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # BrasilAPI format
                    if 'razao_social' in data:
                        return {
                            'razao_social': data.get('razao_social'),
                            'nome_fantasia': data.get('nome_fantasia'),
                            'situacao_cadastral': data.get('descricao_situacao_cadastral'),
                            'cnae_principal': f"{data.get('cnae_fiscal', '')} - {data.get('cnae_fiscal_descricao', '')}",
                            'telefone_oficial': self._format_phone(data.get('ddd_telefone_1'), data.get('telefone_1')),
                            'email_oficial': data.get('email', '').lower() if data.get('email') else None
                        }
                    
                    # ReceitaWS format
                    elif 'nome' in data and data.get('status') != 'ERROR':
                        cnae_principal = data.get('atividade_principal', [{}])[0]
                        return {
                            'razao_social': data.get('nome'),
                            'nome_fantasia': data.get('fantasia'),
                            'situacao_cadastral': data.get('situacao'),
                            'cnae_principal': f"{cnae_principal.get('code', '')} - {cnae_principal.get('text', '')}",
                            'telefone_oficial': data.get('telefone'),
                            'email_oficial': data.get('email', '').lower() if data.get('email') else None
                        }
                
                # Delay entre tentativas
                time.sleep(1)
                
            except Exception:
                continue
        
        return None
    
    def _format_phone(self, ddd, phone):
        """Formata telefone com DDD"""
        if ddd and phone:
            return f"({ddd}) {phone}"
        return None
    
    def _extract_contacts_from_website(self, website: str) -> Optional[Dict]:
        """Extrai contatos do website da empresa"""
        if not website or not website.startswith('http'):
            return None
        
        try:
            response = self.session.get(website, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = response.text
            
            contacts = {}
            
            # Busca emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_text)
            
            # Filtra emails válidos (remove imagens, etc.)
            valid_emails = []
            for email in emails:
                email_lower = email.lower()
                if not email_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    valid_emails.append(email_lower)
            
            if valid_emails:
                contacts['emails_website'] = ', '.join(list(set(valid_emails)))
            
            # Busca links mailto
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href", "")
                if href.startswith("mailto:"):
                    email = href.replace("mailto:", "").strip().lower()
                    if email:
                        if 'emails_website' in contacts:
                            contacts['emails_website'] += f", {email}"
                        else:
                            contacts['emails_website'] = email
            
            # Busca telefones adicionais
            phone_patterns = [
                r'\(\d{2}\)\s*\d{4,5}-?\d{4}',  # (11) 9999-9999
                r'\d{2}\s*\d{4,5}-?\d{4}',      # 11 9999-9999
                r'\+55\s*\d{2}\s*\d{4,5}-?\d{4}' # +55 11 9999-9999
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, page_text)
                if phones:
                    contacts['telefones_website'] = ', '.join(list(set(phones)))
                    break
            
            return contacts if contacts else None
            
        except Exception:
            return None
    
    def _extract_social_media(self, website: str) -> Optional[str]:
        """Extrai links de redes sociais do website"""
        if not website or not website.startswith('http'):
            return None
        
        try:
            response = self.session.get(website, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            social_links = {}
            
            for a_tag in soup.find_all("a", href=True):
                href_attr = a_tag.get("href", "")
                if href_attr:
                    href = href_attr.lower()
                    
                    if 'facebook.com' in href and not social_links.get('facebook'):
                        social_links['facebook'] = href_attr
                    elif 'instagram.com' in href and not social_links.get('instagram'):
                        social_links['instagram'] = href_attr
                    elif 'linkedin.com' in href and not social_links.get('linkedin'):
                        social_links['linkedin'] = href_attr
                    elif 'twitter.com' in href and not social_links.get('twitter'):
                        social_links['twitter'] = href_attr
                    elif 'youtube.com' in href and not social_links.get('youtube'):
                        social_links['youtube'] = href_attr
            
            if social_links:
                return ', '.join([f"{k.title()}: {v}" for k, v in social_links.items()])
            
            return None
            
        except Exception:
            return None
