# Data: 26/08/2025 - Hora: 20:30
# IDE Cursor - claude-4-sonnet
# comando: uv run streamlit run main.py
# Ancoras de Carreira
# Troca senha do usuário - OK
# Multi-lingua - Seletor de idioma na tela de login

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import time
import sys
from config import DB_PATH, DATA_DIR
import os
import streamlit.components.v1 as components
from texto_manager import get_texto, set_user_language

from paginas.form_model import process_forms_tab
from paginas.monitor import registrar_acesso, main as show_monitor
from paginas.crude import show_crud
from paginas.diagnostico import show_diagnostics
from paginas.resultados import show_results
from paginas.resultados_adm import show_resultados_adm


# Adicione esta linha logo no início do arquivo, após os imports
# os.environ['RENDER'] = 'true'

# Configuração da página - deve ser a primeira chamada do Streamlit
st.set_page_config(
    page_title="Ancoras de Carreira - v1.0b",  # Título na Aba do Navegador
    page_icon="⚓",
    layout="centered",
    menu_items={
        'About': """
        ### Sistema de Assessment de Âncoras de Carreira
        
        Versão 1.0b - 26/08/2025
        
        © 2025 Todos os direitos reservados.
        """,
        'Get Help': None,
        'Report a bug': None
    },
    initial_sidebar_state="collapsed"
)

# Inicializar sistema de textos após set_page_config
from texto_manager import inicializar_textos
inicializar_textos()

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
        st.error(get_texto('main_057', 'Banco de dados não encontrado').format(caminho=DB_PATH))
        return False, None
        
    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = None

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None

    if not st.session_state["logged_in"]:
        # Imagem de capa - Tela 
        st.image("webinar1.jpg", use_container_width=True)
            
        st.markdown(f"""
            <p style='text-align: center; font-size: 35px;'>{get_texto('main_001', 'Plataforma de Âncoras de Carreira')}</p>
        """, unsafe_allow_html=True)
        
        # Seletor de idioma
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            selected_language = st.selectbox(
                "🌐 Idioma / Language / Idioma",
                options=[
                    ("pt", "🇧🇷 Português"),
                    ("en", "🇺🇸 English"),
                    ("es", "🇪🇸 Español")
                ],
                format_func=lambda x: x[1],
                key="language_selector"
            )
            selected_language_code = selected_language[0]
        
        # Criar um usuário temporário para carregar textos no idioma selecionado
        temp_user_id = f"temp_{selected_language_code}"
        
        # Formulário de login na área principal
        with st.form("login_form"):
            email = st.text_input(get_texto('main_002', 'E-mail', user_id=temp_user_id), key="email")
            password = st.text_input(get_texto('main_003', 'Senha', user_id=temp_user_id), type="password", key="password")

            aceite_termos = st.checkbox(
                get_texto('main_004', 'Declaro que li e aceito os termos de uso', user_id=temp_user_id),
                key='aceite_termos'
            )

            login_button = st.form_submit_button(get_texto('main_005', 'Entrar', user_id=temp_user_id), use_container_width=True)
        
            if login_button:
                if not aceite_termos:
                    st.warning(get_texto('main_006', 'Você deve aceitar os termos de uso para continuar.', user_id=temp_user_id))
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
                        # Salvar idioma escolhido no banco
                        set_user_language(user[1], selected_language_code)
                        
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
                        st.error(get_texto('main_007', 'E-mail ou senha inválidos. Por favor, verifique seus dados e tente novamente.', user_id=temp_user_id))

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
    
    st.markdown(f"""
        <p style='text-align: center; font-size: 30px; font-weight: bold;'>{get_texto('main_008', 'Pesquisa Baseada na Metodologia de Âncoras de Carreira')}</p>
        
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
    
    # Coluna 1: Propósito
    with col1:
        st.markdown(f"""
            <div style="background-color: #007a7d; padding: 20px; border-radius: 8px; height: 100%;">
                <p style="color: #ffffff; font-size: 24px; font-weight: bold;">{get_texto('main_009', 'Propósito')}</p>
                <div style="color: #ffffff; font-size: 16px;">
                    <p>{get_texto('main_010', 'Este Web App tem como objetivo identificar suas âncoras de carreira predominantes.')}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Coluna 2: Identidade
    with col2:
        st.markdown(f"""
            <div style="background-color: #53a7a9; padding: 20px; border-radius: 8px; height: 100%;">
                <p style="color: #ffffff; font-size: 24px; font-weight: bold;"></p>
                <div style="color: #ffffff; font-size: 16px;">
                    <p>{get_texto('main_011', 'Ao identificar suas âncoras, você ativa uma jornada de autoconhecimento profissional aplicado.')}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Coluna 3: Funções
    with col3:
        modulos_html = f"""
            <div style="background-color: #8eb0ae; padding: 20px; border-radius: 8px; height: 100%;">
                <p style="color: #ffffff; font-size: 24px; font-weight: bold;"></p>
                <div style="color: #ffffff; font-size: 16px;">
                    <p>{get_texto('main_012', 'Mais do que um diagnóstico, é um ponto de partida para evoluir com propósito.')}</p>
                    <p></p>                    
                    <p></p>                    
                </div>
            </div>
        """
        
        st.markdown(modulos_html, unsafe_allow_html=True)

def trocar_senha():
    """Função para permitir que o usuário logado troque sua senha"""
    
    st.markdown(f"""
        <p style='text-align: center; font-size: 30px; font-weight: bold;'>
            {get_texto('main_019', 'Trocar Senha')}
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='background-color:#f0f0f0;padding:15px;border-radius:5px;margin-bottom:20px;'>
            <p style='font-size:16px;color:#333;'>
                {get_texto('main_020', 'Instruções para trocar senha')}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Formulário de troca de senha
    with st.form("trocar_senha_form"):
        senha_atual = st.text_input(get_texto('main_021', 'Senha Atual'), type="password", key="senha_atual")
        nova_senha = st.text_input(get_texto('main_022', 'Nova Senha'), type="password", key="nova_senha")
        confirmar_senha = st.text_input(get_texto('main_023', 'Confirmar Nova Senha'), type="password", key="confirmar_senha")
        
        submit_button = st.form_submit_button(get_texto('main_024', 'Alterar Senha'), use_container_width=True)
        
        if submit_button:
            # Validações
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.error(get_texto('main_025', 'Todos os campos são obrigatórios!'))
                return
            
            if nova_senha != confirmar_senha:
                st.error(get_texto('main_026', 'As senhas não coincidem! Digite a mesma senha nos dois campos.'))
                return
            
            if nova_senha == senha_atual:
                st.error(get_texto('main_027', 'A nova senha deve ser diferente da senha atual!'))
                return
            
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Verificar se a senha atual está correta
                cursor.execute("""
                    SELECT id FROM usuarios 
                    WHERE user_id = ? AND senha = ?
                """, (st.session_state["user_id"], senha_atual))
                
                if not cursor.fetchone():
                    st.error(get_texto('main_028', 'Senha atual incorreta! Verifique e tente novamente.'))
                    conn.close()
                    return
                
                # Atualizar a senha
                cursor.execute("""
                    UPDATE usuarios 
                    SET senha = ? 
                    WHERE user_id = ?
                """, (nova_senha, st.session_state["user_id"]))
                
                conn.commit()
                conn.close()
                
                # Registrar a ação no monitor
                registrar_acesso(
                    user_id=st.session_state["user_id"],
                    programa="main.py",
                    acao="trocar_senha"
                )
                
                st.success(get_texto('main_029', '✅ Senha alterada com sucesso!'))
                st.info(get_texto('main_030', 'A nova senha será válida no próximo login.'))
                
                # Limpar os campos do formulário
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(get_texto('main_031', 'Erro ao alterar senha: {erro}').format(erro=str(e)))
                if 'conn' in locals():
                    conn.close()

def show_analysis_with_admin_controls():
    """Wrapper para exibir análises com controles administrativos quando necessário"""
    
    # Verificar se é visualização administrativa
    admin_user_id = st.session_state.get("admin_view_user_id")
    admin_user_name = st.session_state.get("admin_view_user_name")
    current_user_id = st.session_state.get("user_id")
    
    if admin_user_id and admin_user_id != current_user_id:
        # É visualização administrativa
        st.markdown(f"""
            <div style='background-color:#fff3cd;padding:10px;border-radius:5px;margin-bottom:15px;border-left:4px solid #ffc107;'>
                <p style='margin:0;font-size:14px;'>
                    {get_texto('main_037', '🔍 **Modo Administrativo:** Visualizando análise de **{{usuario}}**').format(usuario=admin_user_name)}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Botão para voltar ao módulo administrativo
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(get_texto('main_038', '⬅️ **Voltar ao Módulo Administrativo**'), use_container_width=True, type="secondary"):
                # Limpar dados administrativos
                st.session_state.pop("admin_view_user_id", None)
                st.session_state.pop("admin_view_user_name", None)
                
                # Definir flag para retornar ao módulo administrativo
                st.session_state["return_to_admin"] = True
                st.rerun()
        
        st.markdown("---")
        
        # Exibir análise do usuário selecionado
        show_results(
            tabela_escolhida="forms_resultados", 
            titulo_pagina=get_texto('main_039', 'Análise Administrativa - {usuario}').format(usuario=admin_user_name), 
            user_id=admin_user_id
        )
    else:
        # Visualização normal do próprio usuário
        show_results(
            tabela_escolhida="forms_resultados", 
            titulo_pagina=get_texto('main_061', 'Análise das Avaliações'), 
            user_id=current_user_id
        )

def zerar_value_element():
    """Função para zerar todos os value_element do usuário logado na tabela forms_tab onde type_element é input, formula ou formulaH"""
    # Inicializa o estado do checkbox se não existir
    if 'confirma_zeragem' not in st.session_state:
        st.session_state.confirma_zeragem = False
    
    # Checkbox para confirmação
    confirma = st.checkbox(get_texto('main_032', 'Confirmar zeragem dos valores?'), 
                                 value=st.session_state.confirma_zeragem,
                                 key='confirma_zeragem')
    
    if st.button(get_texto('main_033', 'Zerar Valores')):
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
                    AND type_element IN ('input', 'formula', 'formulaH', 'selectbox')
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
                
                st.success(get_texto('main_035', 'Valores zerados com sucesso! ({registros} registros atualizados)').format(registros=registros_afetados))
                
                # Força a atualização da página após 1 segundo
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(get_texto('main_036', 'Erro ao zerar valores: {erro}').format(erro=str(e)))
                if 'conn' in locals():
                    conn.close()
        else:
            st.warning(get_texto('main_034', 'Confirme a operação para prosseguir'))

def main():
    """Gerencia a navegação entre as páginas do sistema."""
    # Verifica se o diretório data existe
    if not DATA_DIR.exists():
        st.error(get_texto('main_058', 'Pasta \'{pasta}\' não encontrada. O programa não pode continuar.').format(pasta=DATA_DIR))
        st.stop()
        
    # Verifica se o banco existe
    if not DB_PATH.exists():
        st.error(get_texto('main_059', 'Banco de dados \'{banco}\' não encontrado. O programa não pode continuar.').format(banco=DB_PATH))
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
        st.markdown(f"""
            <p style='text-align: center; font-size: 30px; font-weight: bold;'>
                {get_texto('main_013', 'Plataforma CHAVE - Desenvolvimento Humano, Automações com IA')}
            </p>
        """, unsafe_allow_html=True)
        with st.expander(get_texto('main_014', 'Informações do Usuário / Logout'), expanded=False):
            st.markdown(f"""
                {get_texto('main_015', '**Usuário:**')} {st.session_state.get('user_name')}  
                {get_texto('main_016', '**ID:**')} {st.session_state.get('user_id')}  
                {get_texto('main_017', '**Perfil:**')} {st.session_state.get('user_profile')}
            """)
            if st.button(get_texto('main_018', 'Logout')):
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
        get_texto('main_046', 'Bem-vindo'): show_welcome,
        get_texto('main_047', 'Âncoras P1'): lambda: process_forms_tab("ancoras_p1"),
        get_texto('main_048', 'Âncoras P2'): lambda: process_forms_tab("ancoras_p2"),
        get_texto('main_049', 'Resultados'): lambda: process_forms_tab("resultado"),
        get_texto('main_050', 'das Avaliações'): lambda: show_analysis_with_admin_controls(),
        get_texto('main_051', 'Info Tabelas (CRUD)'): show_crud,
        get_texto('main_052', 'Monitor de Uso'): show_monitor,
        get_texto('main_053', 'Diagnóstico'): show_diagnostics,
        get_texto('main_054', 'Análises de Usuários'): show_resultados_adm,
        get_texto('main_055', 'Trocar Senha'): trocar_senha,
        get_texto('main_056', 'Zerar Valores'): zerar_value_element,
    }
    
    # Criando grupos de menu
    menu_groups = {
        get_texto('main_042', 'Abertura'): [get_texto('main_046', 'Bem-vindo')],
        get_texto('main_043', 'Avaliação'): [
            get_texto('main_047', 'Âncoras P1'),
            get_texto('main_048', 'Âncoras P2'),
            get_texto('main_049', 'Resultados')
        ],
        get_texto('main_044', 'Análise'): [
            get_texto('main_050', 'das Avaliações'),
        ],
        get_texto('main_045', 'Administração'): []  # Iniciando vazio para adicionar itens na ordem correta
    }
    
    # Adicionar opções administrativas na ordem desejada
    admin_group_key = get_texto('main_045', 'Administração')
    if user_profile and user_profile.lower() in ["adm", "master"]:
        menu_groups[admin_group_key].append(get_texto('main_054', 'Análises de Usuários'))
    if user_profile and user_profile.lower() == "master":
        menu_groups[admin_group_key].append(get_texto('main_051', 'Info Tabelas (CRUD)'))
    if user_profile and user_profile.lower() == "master":
        menu_groups[admin_group_key].append(get_texto('main_053', 'Diagnóstico'))
    if user_profile and user_profile.lower() in ["adm", "master"]:
        menu_groups[admin_group_key].append(get_texto('main_052', 'Monitor de Uso'))
    # Adicionar Trocar Senha (disponível para todos os perfis)
    menu_groups[admin_group_key].append(get_texto('main_055', 'Trocar Senha'))
    # Adicionar Zerar Valores por último
    menu_groups[admin_group_key].append(get_texto('main_056', 'Zerar Valores'))
    
    # Se não houver opções de administração, remover o grupo
    if not menu_groups[admin_group_key]:
        menu_groups.pop(admin_group_key)
    
    # Criar seletores de navegação na página principal
    nav_cols = st.columns(2)
    with nav_cols[0]:
        selected_group = st.selectbox(
            get_texto('main_040', 'Selecione o Módulo:'),
            options=list(menu_groups.keys()),
            key="group_selection"
        )
    
    with nav_cols[1]:
        section = st.radio(
            get_texto('main_041', 'Selecione a Função:'),
            menu_groups[selected_group],
            key="menu_selection",
            horizontal=True
        )

    # Verificar se há retorno ao módulo administrativo
    if st.session_state.get("return_to_admin", False):
        st.session_state["return_to_admin"] = False
        # Exibir módulo administrativo diretamente
        show_resultados_adm()
        return
    
    # Verificar se houve mudança de página
    if st.session_state.get("previous_page") != section:
        st.session_state["previous_page"] = section

    # Verificar se há redirecionamento pendente de análise administrativa
    if st.session_state.get("redirect_to_analysis", False):
        # Limpar flag de redirecionamento
        st.session_state["redirect_to_analysis"] = False
        
        # Exibir análise administrativa diretamente sem modificar widgets
        show_analysis_with_admin_controls()
        return
    
    # Processa a seção selecionada usando o dicionário de handlers
    handler = page_handlers.get(section)
    if handler:
        handler()
    else:
        st.error(get_texto('main_060', 'Função não encontrada.'))

    # --- FOOTER ---
    st.markdown("<br>" * 1, unsafe_allow_html=True)
    
    # Logo do rodapé
    footer_logo_path = os.path.join(current_dir, "Logo_1b.jpg")
    if os.path.exists(footer_logo_path):
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image(
                footer_logo_path,
                width=200, 
                use_container_width=False
            )

if __name__ == "__main__":
    main()
