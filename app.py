import os
import time
import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO

# Supondo que seus arquivos estão em uma pasta 'utils'
from utils.serp_client import SerpAPIClient
from utils.data_enrichment import DataEnricher 

# Nota: O arquivo minin_data.py parece ser um duplicado de data_enrichment.py
# Se for o caso, pode ser removido para simplificar o projeto.
from utils.mining_data import MINING_SEARCH_TERMS

# ==================== CONFIGURAÇÃO DA PÁGINA ====================

st.set_page_config(
    page_title="Prospector de Mineradoras - Pará",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== INICIALIZAÇÃO ====================

def initialize_session_state():
    """Inicializa o estado da sessão"""
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "enriched_results" not in st.session_state:
        st.session_state.enriched_results = []
    if "search_history" not in st.session_state:
        st.session_state.search_history = []

initialize_session_state()

# ==================== INTERFACE PRINCIPAL ====================

def main():
    # Header
    st.title("⛏️ Prospector de Mineradoras - Pará")
    st.markdown("""
    ### 🎯 Ferramenta especializada para prospecção de empresas de mineração no Pará
    **Foco:** Clientes potenciais para peças de freio de caminhão e equipamentos de mineração
    """)
    
    # Sidebar - Configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        serp_api_key = st.text_input(
            "🔑 SERP API Key:",
            type="password",
            help="Sua chave da API do SERP API",
            value=os.getenv("SERP_API_KEY", "")
        )
        
        st.divider()
        
        st.subheader("🔍 Parâmetros de Busca")
        
        search_terms = st.multiselect(
            "Termos de busca:",
            options=list(MINING_SEARCH_TERMS.keys()),
            default=list(MINING_SEARCH_TERMS.keys())[:3],
            format_func=lambda x: f"{x} ({MINING_SEARCH_TERMS[x]['description']})"
        )
        
        num_results = st.slider(
            "Máximo de resultados por termo:",
            min_value=10,
            max_value=100,
            value=20,
            step=10
        )
        
        st.divider()
        
        st.subheader("📊 Enriquecimento de Dados")
        
        enrich_data = st.checkbox("Enriquecer dados via APIs públicas", value=True)
        include_cnpj = st.checkbox("Buscar dados de CNPJ", value=True)
        include_contacts = st.checkbox("Buscar contatos e redes sociais", value=True)
        
        st.divider()
        
        st.subheader("🔧 Configurações Avançadas")
        
        delay_between_requests = st.slider(
            "Delay entre requisições (segundos):",
            min_value=1,
            max_value=10,
            value=3,
            help="Ajuda a evitar bloqueios da API"
        )
        
        enable_filters = st.checkbox("Aplicar filtros específicos de mineração", value=True)

    # ==================== ÁREA PRINCIPAL ====================
    
    if not serp_api_key:
        st.error("🔑 Por favor, insira sua chave da API do SERP API na barra lateral")
        st.info("""
        **Como obter uma chave da SERP API:**
        1. Acesse https://serpapi.com
        2. Crie uma conta gratuita
        3. Copie sua API key do dashboard
        4. Cole a chave na barra lateral
        """)
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🚀 Iniciar Prospecção", type="primary", disabled=not search_terms):
            perform_search(serp_api_key, search_terms, num_results, delay_between_requests, 
                         enrich_data, include_cnpj, include_contacts, enable_filters)
    
    with col2:
        if st.session_state.enriched_results:
            if st.button("🔄 Recarregar Dados"): # Nome mais claro
                st.rerun()
    
    with col3:
        if st.session_state.enriched_results:
            if st.button("🗑️ Limpar Resultados"):
                st.session_state.search_results = []
                st.session_state.enriched_results = []
                st.rerun()
    
    # ==================== EXIBIÇÃO DOS RESULTADOS ====================
    
    if st.session_state.enriched_results:
        st.success(f"✅ Prospecção concluída! {len(st.session_state.enriched_results)} empresas encontradas")
        
        tab1, tab2, tab3 = st.tabs(["📋 Lista de Empresas", "📊 Análise", "📥 Exportar"])
        
        with tab1:
            display_results_table()
        
        with tab2:
            display_analytics()
        
        with tab3:
            display_export_options()
    
    elif st.session_state.search_results:
        st.info("🔄 Dados básicos coletados. Iniciando enriquecimento...")
    
    if st.session_state.search_history:
        with st.expander("📜 Histórico de Buscas"):
            for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
                st.text(f"{search['timestamp']} - {search['terms_count']} termos - {search['results_count']} resultados")

def perform_search(api_key, search_terms, num_results, delay, enrich_data, include_cnpj, include_contacts, enable_filters):
    """Executa a busca principal"""
    try:
        st.session_state.search_results = []
        st.session_state.enriched_results = []
        
        serp_client = SerpAPIClient(api_key)
        
        progress_bar = st.progress(0, text="Iniciando busca...")
        status_text = st.empty()
        
        all_results = []
        
        for i, term in enumerate(search_terms):
            status_text.text(f"🔍 Buscando: {term}...")
            
            search_query = MINING_SEARCH_TERMS[term]['query']
            
            results = serp_client.search_local_businesses(
                query=search_query,
                location="Pará, Brasil",
                num_results=num_results,
                enable_filters=enable_filters
            )
            
            if results:
                for result in results:
                    result['search_term'] = term
                    result['search_timestamp'] = datetime.now().isoformat()
                
                all_results.extend(results)
                st.session_state.search_results.extend(results)
            
            progress_bar.progress((i + 1) / len(search_terms) * 0.5, text=f"Buscando: {term}")
            
            if i < len(search_terms) - 1:
                time.sleep(delay)
        
        unique_results = remove_duplicates(all_results)
        st.session_state.search_results = unique_results
        
        status_text.text(f"✅ Busca concluída: {len(unique_results)} empresas únicas encontradas.")
        
        if enrich_data and unique_results:
            status_text.text("📊 Enriquecendo dados...")
            
            enricher = DataEnricher()
            enriched = enricher.enrich_companies(
                unique_results,
                include_cnpj=include_cnpj,
                include_contacts=include_contacts,
                progress_callback=lambda p: progress_bar.progress(0.5 + p * 0.5, text=f"Enriquecendo... {int(p*100)}%")
            )
            
            st.session_state.enriched_results = enriched
        else:
            st.session_state.enriched_results = unique_results
        
        st.session_state.search_history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'terms_count': len(search_terms),
            'results_count': len(unique_results)
        })
        
        progress_bar.empty()
        status_text.empty()
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro durante a busca: {str(e)}")

def remove_duplicates(results):
    """Remove empresas duplicadas baseado em nome e endereço"""
    seen = set()
    unique_results = []
    
    for result in results:
        name = result.get('name', '').strip().lower()
        # Usa os primeiros 15 caracteres do endereço para evitar pequenas variações
        address = result.get('address', '').strip().lower()[:15]
        key = f"{name}|{address}"
        
        if key not in seen and name:
            seen.add(key)
            unique_results.append(result)
    
    return unique_results

def display_results_table():
    """Exibe a tabela de resultados"""
    if not st.session_state.enriched_results:
        return
    
    df = pd.DataFrame(st.session_state.enriched_results)
    
    display_columns = [
        'name', 'address', 'phone', 'website', 'rating', 'reviews',
        'cnpj', 'razao_social', 'email_oficial', 'social_media'
    ]
    
    available_columns = [col for col in display_columns if col in df.columns]
    
    if available_columns:
        column_names = {
            'name': 'Nome', 'address': 'Endereço', 'phone': 'Telefone',
            'website': 'Website', 'rating': 'Avaliação', 'reviews': 'Nº Avaliações',
            'cnpj': 'CNPJ', 'razao_social': 'Razão Social', 
            'email_oficial': 'Email', 'social_media': 'Redes Sociais'
        }
        
        display_df = df[available_columns].copy()
        display_df = display_df.rename(columns=column_names)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Website": st.column_config.LinkColumn("Website", display_text="Acessar"),
                "Avaliação": st.column_config.NumberColumn(format="%.1f ⭐"),
                "Redes Sociais": st.column_config.TextColumn(width="medium")
            }
        )
    else:
        st.warning("Nenhum dado disponível para exibição")

def display_analytics():
    """Exibe análises dos dados coletados"""
    if not st.session_state.enriched_results:
        return
    
    df = pd.DataFrame(st.session_state.enriched_results)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de Empresas", len(df))
        
        phone_series = df.get('phone', pd.Series(dtype='object'))
        with_phone = len(df[phone_series.notna() & (phone_series != '')])
        st.metric("Com Telefone", with_phone, f"{with_phone/len(df)*100:.1f}%")
        
        website_series = df.get('website', pd.Series(dtype='object'))
        with_website = len(df[website_series.notna() & (website_series != '')])
        st.metric("Com Website", with_website, f"{with_website/len(df)*100:.1f}%")
    
    with col2:
        if 'search_term' in df.columns:
            st.subheader("Distribuição por Termo de Busca")
            term_counts = df['search_term'].value_counts()
            st.bar_chart(term_counts)
        
        if 'rating' in df.columns and len(df[df['rating'].notna()]) > 0:
            avg_rating = df['rating'].mean()
            st.metric("Avaliação Média", f"{avg_rating:.1f} ⭐")

def display_export_options():
    """Exibe opções de exportação"""
    if not st.session_state.enriched_results:
        return
    
    st.subheader("📥 Exportar Dados")
    
    df = pd.DataFrame(st.session_state.enriched_results)
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📄 Baixar CSV",
            data=csv_data,
            file_name=f"mineradoras_para_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        excel_buffer = BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Mineradoras')
            
            # --- CORREÇÃO APLICADA AQUI ---
            phone_series = df.get('phone', pd.Series(dtype='object'))
            website_series = df.get('website', pd.Series(dtype='object'))
            
            summary_data = {
                'Métrica': ['Total de Empresas', 'Com Telefone', 'Com Website', 'Com Email'],
                'Valor': [
                    len(df),
                    len(df[phone_series.notna() & (phone_series != '')]),
                    len(df[website_series.notna() & (website_series != '')]),
                    len(df[df.get('email_oficial', pd.Series(dtype='object')).notna() & (df.get('email_oficial', pd.Series(dtype='object')) != '')])
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, index=False, sheet_name='Resumo')
        
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="📊 Baixar Excel",
            data=excel_data,
            file_name=f"mineradoras_para_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()