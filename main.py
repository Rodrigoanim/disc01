# Data: 09/06/2025 - Hora: 10:00
# IDE Cursor - gemini 2.5 pro
# comando: streamlit run main.py
# Adaptação para Mobile e novo conteudo


import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import time
import sys
from config import DB_PATH, DATA_DIR
import os
import streamlit.components.v1 as components

from paginas.form_model import process_forms_tab
from paginas.monitor import registrar_acesso, main as show_monitor
from paginas.crude import show_crud
from paginas.diagnostico import show_diagnostics
from paginas.resultados import show_results


# Adicione esta linha logo no início do arquivo, após os imports
# os.environ['RENDER'] = 'true'

# Configuração da página - deve ser a primeira chamada do Streamlit
st.set_page_config(
    page_title="Assessment DISC",  # Título simplificado
    page_icon="📊",
    layout="centered",
    menu_items={
        'About': """
        ### Sobre o Sistema - Assessment DISC
        
        Versão: 3.0 - 06/06/2025
        
        Este sistema foi desenvolvido para realizar avaliações comportamentais 
        utilizando a metodologia DISC.
        
        © 2025 Todos os direitos reservados.
        """,
        'Get Help': None,
        'Report a bug': None
    },
    initial_sidebar_state="collapsed"
)

# Adicionar verificação e carregamento do logo
import os

# Obtém o caminho absoluto do diretório atual
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "Logo_2a.jpg")

# --- CSS Global ---
# Adiciona CSS para ocultar o botão de fullscreen das imagens globalmente
st.markdown("""
    <style>
        /* Oculta o botão baseado no aria-label identificado na inspeção */
        button[aria-label="Fullscreen"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)
# --- Fim CSS Global ---

def authenticate_user():
    """Autentica o usuário e verifica seu perfil no banco de dados."""
    # Adicionar CSS para a página de login
    if not st.session_state.get("logged_in", False):
        st.markdown("""
            <style>
                /* Oculta a barra lateral na página de login */
                [data-testid="stSidebar"] {
                    display: none;
                }
                /* Estilo para a página de login */
                [data-testid="stAppViewContainer"] {
                    background-color: #cbe7f5;
                }
                
                /* Remove a faixa branca superior */
                [data-testid="stHeader"] {
                    background-color: #cbe7f5;
                }
                
                /* Ajuste da cor do texto para melhor contraste */
                [data-testid="stAppViewContainer"] p {
                    color: black;
                }
            </style>
        """, unsafe_allow_html=True)
    
    # Verifica se o banco existe
    if not DB_PATH.exists():
        st.error(f"Banco de dados não encontrado em {DB_PATH}")
        return False, None
        
    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = None

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None

    if not st.session_state["logged_in"]:
        # Imagem de capa - Tela abertura
        st.image("webinar1.jpg", use_container_width=True)
            
        st.markdown("""
            <p style='text-align: center; font-size: 35px;'>Faça login para acessar o sistema</p>
        """, unsafe_allow_html=True)
        
        # Formulário de login na área principal
        with st.form("login_form"):
            email = st.text_input("E-mail", key="email")
            password = st.text_input("Senha", type="password", key="password")

            aceite_termos = st.checkbox(
                'Declaro que li e aceito os [termos de uso da ferramenta](https://ag93eventos.com.br/ear/Termos_Uso_DISC.pdf)',
                key='aceite_termos'
            )

            login_button = st.form_submit_button("Entrar", use_container_width=True)
        
            if login_button:
                if not aceite_termos:
                    st.warning("Você deve aceitar os termos de uso para continuar.")
                else:
                    clean_email = email.strip()

                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, user_id, perfil, nome FROM usuarios WHERE LOWER(email) = LOWER(?) AND senha = ?
                    """, (clean_email, password))
                    user = cursor.fetchone()
                    conn.close()

                    if user:
                        st.session_state["logged_in"] = True
                        st.session_state["user_profile"] = user[2]
                        st.session_state["user_id"] = user[1]
                        st.session_state["user_name"] = user[3]
                        
                        # Registrar o acesso bem-sucedido
                        registrar_acesso(
                            user_id=user[1],
                            programa="main.py",
                            acao="login"
                        )
                        st.rerun()
                    else:
                        st.error("E-mail ou senha inválidos. Por favor, verifique seus dados e tente novamente.")

    return st.session_state.get("logged_in", False), st.session_state.get("user_profile", None)

def get_timezone_offset():
    """
    Determina se é necessário aplicar offset de timezone baseado no ambiente
    """
    is_production = os.getenv('RENDER') is not None
    
    if is_production:
        # Se estiver no Render, ajusta 3 horas para trás
        return datetime.now() - timedelta(hours=3)
    return datetime.now()  # Se local, usa hora atual

def show_welcome():
    """Exibe a tela de boas-vindas com informações do usuário"""
    st.markdown("""
        <p style='text-align: left; font-size: 40px; font-weight: bold;'>Bem-vindo à Pesquisa Comportamental</p>
    """, unsafe_allow_html=True)
    
    # Buscar dados do usuário
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, empresa 
        FROM usuarios 
        WHERE user_id = ?
    """, (st.session_state.get('user_id'),))
    user_info = cursor.fetchone()
    
    # Removemos a consulta de contagem de formulários
    conn.close()
    
    empresa = user_info[1] if user_info[1] is not None else "Não informada"
    
    # Layout em colunas usando st.columns
    col1, col2, col3 = st.columns(3)
    
    # Coluna 1: Seus Dados
    with col1:
        st.markdown(f"""
            <div style="background-color: #007a7d; padding: 20px; border-radius: 8px;">
                <p style="color: #ffffff; font-size: 24px; font-weight: bold;">Seus Dados</p>
                <div style="color: #ffffff; font-size: 16px;">
                    <p>ID: {st.session_state.get('user_id')}</p>
                    <p>Nome: {st.session_state.get('user_name')}</p>
                    <p>E-mail: {user_info[0]}</p>
                    <p>Empresa: {empresa}</p>
                    <p>Perfil: {st.session_state.get('user_profile')}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Coluna 2: Suuas Atividades
    with col2:
        current_time = get_timezone_offset()
        ambiente = "Produção" if os.getenv('RENDER') else "Local"
        
        st.markdown(f"""
            <div style="background-color: #53a7a9; padding: 20px; border-radius: 8px;">
                <p style="color: #ffffff; font-size: 24px; font-weight: bold;">Suas Atividades</p>
                <div style="color: #ffffff; font-size: 16px;">
                    <p>Data Atual: {current_time.strftime('%d/%m/%Y')}</p>
                    <p>Hora Atual: {current_time.strftime('%H:%M:%S')}</p>
                    <p>Ambiente: {ambiente}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Coluna 3: Módulos Disponíveis
    with col3:
        modulos_html = """
            <div style="background-color: #8eb0ae; padding: 20px; border-radius: 8px;">
                <p style="color: #ffffff; font-size: 24px; font-weight: bold;">Módulos Disponíveis</p>
                <div style="color: #ffffff; font-size: 16px;">
                    <p>Entrada de Dados - Perfil DISC</p>
                    <p>Entrada de Dados - Comportamento DISC</p>                    
                    <p>Simulações DISC</p>                    
                </div>
            </div>
        """
        
        st.markdown(modulos_html, unsafe_allow_html=True)

def zerar_value_element():
    """Função para zerar todos os value_element do usuário logado na tabela forms_tab onde type_element é input, formula ou formulaH"""
    # Inicializa o estado do checkbox se não existir
    if 'confirma_zeragem' not in st.session_state:
        st.session_state.confirma_zeragem = False
    
    # Checkbox para confirmação
    confirma = st.checkbox("Confirmar zeragem dos valores?", 
                                 value=st.session_state.confirma_zeragem,
                                 key='confirma_zeragem')
    
    if st.button("Zerar Valores"):
        if confirma:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Atualiza value_element para 0.0 para os tipos especificados
                cursor.execute("""
                    UPDATE forms_tab 
                    SET value_element = 0.0 
                    WHERE user_id = ? 
                    AND value_element IS NOT NULL
                    AND type_element IN ('input', 'formula', 'formulaH')
                """, (st.session_state["user_id"],))
                
                registros_afetados = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                # Registra a ação no monitor
                registrar_acesso(
                    user_id=st.session_state["user_id"],
                    programa="main.py",
                    acao="zerar_valores"
                )
                
                st.success(f"Valores zerados com sucesso! ({registros_afetados} registros atualizados)")
                
                # Força a atualização da página após 1 segundo
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao zerar valores: {str(e)}")
                if 'conn' in locals():
                    conn.close()
        else:
            st.warning("Confirme a operação para prosseguir")

def main():
    """Gerencia a navegação entre as páginas do sistema."""
    # Verifica se o diretório data existe
    if not DATA_DIR.exists():
        st.error(f"Pasta '{DATA_DIR}' não encontrada. O programa não pode continuar.")
        st.stop()
        
    # Verifica se o banco existe
    if not DB_PATH.exists():
        st.error(f"Banco de dados '{DB_PATH}' não encontrado. O programa não pode continuar.")
        st.stop()
        
    logged_in, user_profile = authenticate_user()
    
    if not logged_in:
        st.stop()
    
    # Armazenar página anterior para comparação
    if "previous_page" not in st.session_state:
        st.session_state["previous_page"] = None

    # --- HEADER ---
    col1, col2 = st.columns([1, 4])
    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
    
    with col2:
        st.markdown("""
            <p style='text-align: left; font-size: 44px; font-weight: bold;'>
                Assessment DISC
            </p>
        """, unsafe_allow_html=True)
        with st.expander("Informações do Usuário / Logout", expanded=False):
            st.markdown(f"""
                **Usuário:** {st.session_state.get('user_name')}  
                **ID:** {st.session_state.get('user_id')}  
                **Perfil:** {st.session_state.get('user_profile')}
            """)
            if st.button("Logout"):
                if "user_id" in st.session_state:
                    registrar_acesso(
                        user_id=st.session_state["user_id"],
                        programa="main.py",
                        acao="logout"
                    )
                for key in ['logged_in', 'user_profile', 'user_id', 'user_name']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # --- NAVEGAÇÃO ---
    
    # Mapeamento de páginas para suas funções de handler
    page_handlers = {
        "Bem-vindo": show_welcome,
        "Avaliação de Perfis": lambda: process_forms_tab("perfil"),
        "Avaliação de Comportamento": lambda: process_forms_tab("comportamento"),
        "Avaliação Híbrida": lambda: process_forms_tab("hibrido"),
        "do Perfil": lambda: show_results(tabela_escolhida="forms_resultados", titulo_pagina="Análise: Avaliação de Perfis", user_id=st.session_state.user_id),
        "Info Tabelas (CRUD)": show_crud,
        "Monitor de Uso": show_monitor,
        "Diagnóstico": show_diagnostics,
        "Zerar Valores": zerar_value_element,
    }
    
    # Criando grupos de menu
    menu_groups = {
        "Abertura": ["Bem-vindo"],
        "Avaliação Comportamental": [
            "Avaliação de Perfis",
            "Avaliação de Comportamento",
            "Avaliação Híbrida"
        ],
        "Análise": [
            "do Perfil",
        ],
        "Administração": []  # Iniciando vazio para adicionar itens na ordem correta
    }
    
    # Adicionar opções administrativas na ordem desejada
    if user_profile and user_profile.lower() == "master":
        menu_groups["Administração"].append("Info Tabelas (CRUD)")
    if user_profile and user_profile.lower() == "master":
        menu_groups["Administração"].append("Diagnóstico")
    if user_profile and user_profile.lower() in ["adm", "master"]:
        menu_groups["Administração"].append("Monitor de Uso")
    # Adicionar Zerar Valores por último
    menu_groups["Administração"].append("Zerar Valores")
    
    # Se não houver opções de administração, remover o grupo
    if not menu_groups["Administração"]:
        menu_groups.pop("Administração")
    
    # Criar seletores de navegação na página principal
    nav_cols = st.columns(2)
    with nav_cols[0]:
        selected_group = st.selectbox(
            "Selecione o módulo:",
            options=list(menu_groups.keys()),
            key="group_selection"
        )
    
    with nav_cols[1]:
        section = st.radio(
            "Selecione a página:",
            menu_groups[selected_group],
            key="menu_selection",
            horizontal=True
        )

    # Verificar se houve mudança de página
    if st.session_state.get("previous_page") != section:
        save_current_form_data()
        st.session_state["previous_page"] = section

    # Processa a seção selecionada usando o dicionário de handlers
    handler = page_handlers.get(section)
    if handler:
        handler()
    else:
        st.error("Página não encontrada.")

    # --- FOOTER ---
    st.markdown("<br>" * 1, unsafe_allow_html=True)
    
    # Logo do rodapé
    footer_logo_path = os.path.join(current_dir, "Logo_1b.jpg")
    if os.path.exists(footer_logo_path):
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image(
                footer_logo_path,
                width=100, 
                use_container_width=False
            )

def save_current_form_data():
    """Salva os dados do formulário atual quando houver mudança de página"""
    if "form_data" in st.session_state and st.session_state["form_data"]:
        with st.spinner('Salvando dados...'):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            previous_page = st.session_state.get("previous_page", "")
            
            if "Tipo do Café" in previous_page:
                tipo_cafe = st.session_state.get("form_data", {}).get("tipo_cafe")
                quantidade = st.session_state.get("form_data", {}).get("quantidade")
                
                if tipo_cafe and quantidade is not None:  # Verifica se os dados existem
                    cursor.execute("""
                        INSERT OR REPLACE INTO form_cafe 
                        (user_id, data_input, tipo_cafe, quantidade)
                        VALUES (?, datetime('now'), ?, ?)
                    """, (
                        st.session_state["user_id"],
                        tipo_cafe,
                        quantidade
                    ))
            
            elif "Torrefação e Moagem" in previous_page:
                cursor.execute("""
                    INSERT OR REPLACE INTO form_moagem 
                    (user_id, data_input, tipo_moagem, temperatura)
                    VALUES (?, datetime('now'), ?, ?)
                """, (
                    st.session_state["user_id"],
                    st.session_state.get("form_data", {}).get("tipo_moagem"),
                    st.session_state.get("form_data", {}).get("temperatura")
                ))
            
            elif "Embalagem" in previous_page:
                cursor.execute("""
                    INSERT OR REPLACE INTO form_embalagem 
                    (user_id, data_input, tipo_embalagem, peso)
                    VALUES (?, datetime('now'), ?, ?)
                """, (
                    st.session_state["user_id"],
                    st.session_state.get("form_data", {}).get("tipo_embalagem"),
                    st.session_state.get("form_data", {}).get("peso")
                ))
            
            conn.commit()
            conn.close()
            # Limpar os dados do formulário após salvar
            st.session_state["form_data"] = {}
            time.sleep(0.5)  # Pequeno delay para feedback visual
        st.success('Dados salvos com sucesso!')

if __name__ == "__main__":
    main()
