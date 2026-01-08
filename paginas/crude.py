# Arquivo: crude.py
# Data: 14/12/2025 
# IDE Cursor - Auto Agent
# Adaptação para o sistema de múltiplos assessments
# Download o banco de dados: calcrh2.db 

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

from config import DB_PATH  # Adicione esta importação
from paginas.monitor import registrar_acesso  # Importação para auditoria

def format_br_number(value):
    """Formata um número para o padrão brasileiro."""
    try:
        if pd.isna(value) or value == '':
            return ''
        return f"{float(str(value).replace(',', '.')):.2f}".replace('.', ',')
    except:
        return ''

def get_available_tables():
    """Obtém lista de tabelas disponíveis no banco de dados."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return tables
    except Exception as e:
        st.error(f"Erro ao buscar tabelas: {str(e)}")
        return []

def get_assessment_tables():
    """Obtém tabelas relacionadas aos assessments numerados."""
    tables = get_available_tables()
    assessment_tables = {
        'forms_tab': [t for t in tables if t.startswith('forms_tab_')],
        'forms_resultados': [t for t in tables if t.startswith('forms_resultados_')]
    }
    return assessment_tables

def get_assessment_info():
    """Obtém informações dos assessments disponíveis."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT assessment_id, MIN(assessment_name) as assessment_name 
            FROM assessments 
            GROUP BY assessment_id
            ORDER BY assessment_id
        """)
        
        assessments = cursor.fetchall()
        conn.close()
        
        return {assessment_id: name for assessment_id, name in assessments}
    except Exception as e:
        st.warning(f"Erro ao buscar informações dos assessments: {str(e)}")
        return {}

def check_numbered_tables():
    """Verifica se as tabelas numeradas existem."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar tabelas forms_tab_XX
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'forms_tab_%'")
        forms_tab_tables = [row[0] for row in cursor.fetchall()]
        
        # Verificar tabelas forms_resultados_XX
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'forms_resultados_%'")
        forms_resultados_tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'forms_tab_count': len(forms_tab_tables),
            'forms_resultados_count': len(forms_resultados_tables),
            'forms_tab_tables': forms_tab_tables,
            'forms_resultados_tables': forms_resultados_tables
        }
    except Exception as e:
        st.error(f"Erro ao verificar tabelas numeradas: {str(e)}")
        return {'forms_tab_count': 0, 'forms_resultados_count': 0, 'forms_tab_tables': [], 'forms_resultados_tables': []}

def manage_assessment_permissions():
    """
    Interface para gerenciar permissões de assessments
    """
    st.markdown("### 🔐 Gerenciamento de Permissões de Assessments")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar todos os usuários
        cursor.execute("""
            SELECT user_id, nome, email, perfil 
            FROM usuarios 
            ORDER BY perfil, email
        """)
        users = cursor.fetchall()
        
        # Buscar todos os assessments
        cursor.execute("""
            SELECT assessment_id, MIN(assessment_name) as assessment_name 
            FROM assessments 
            GROUP BY assessment_id
            ORDER BY assessment_id
        """)
        assessments = cursor.fetchall()
        
        if not users or not assessments:
            st.warning("Nenhum usuário ou assessment encontrado.")
            return
        
        # Seletor de usuário
        user_options = {f"{user[2]} ({user[3]})": user[0] for user in users}
        selected_user_name = st.selectbox("Selecione o usuário:", list(user_options.keys()))
        selected_user_id = user_options[selected_user_name]
        
        # Mostrar perfil do usuário
        user_profile = next(user[3] for user in users if user[0] == selected_user_id)
        st.info(f"**Perfil:** {user_profile}")
        
        # Verificar se é master ou adm
        if user_profile.lower() in ["master", "adm"]:
            st.success("✅ **Usuário Master/Admin:** Acesso total a todos os assessments")
            st.info("💡 **Nota:** Usuários Master e Admin têm acesso automático a todos os assessments, independente das permissões na tabela.")
            return
        
        # Mostrar permissões atuais
        st.markdown("#### 📋 Permissões Atuais")
        
        cursor.execute("""
            SELECT assessment_id, assessment_name, access_granted
            FROM assessments 
            WHERE user_id = ?
            ORDER BY assessment_id
        """, (selected_user_id,))
        
        current_permissions = cursor.fetchall()
        
        if current_permissions:
            # Criar DataFrame para edição
            df_data = []
            for assessment_id, assessment_name, access_granted in current_permissions:
                df_data.append({
                    'assessment_id': assessment_id,
                    'assessment_name': assessment_name,
                    'access_granted': bool(access_granted)
                })
            
            df = pd.DataFrame(df_data)
            
            # Editor de permissões
            edited_df = st.data_editor(
                df,
                column_config={
                    "assessment_id": st.column_config.TextColumn("ID", disabled=True),
                    "assessment_name": st.column_config.TextColumn("Nome do Assessment", disabled=True),
                    "access_granted": st.column_config.CheckboxColumn("Acesso Concedido")
                },
                hide_index=True,
                use_container_width=True,
                key=f"permissions_editor_{selected_user_id}"
            )
            
            # Botão para salvar alterações
            if st.button("💾 Salvar Permissões", type="primary"):
                try:
                    for _, row in edited_df.iterrows():
                        cursor.execute("""
                            UPDATE assessments 
                            SET access_granted = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = ? AND assessment_id = ?
                        """, (int(row['access_granted']), selected_user_id, row['assessment_id']))
                    
                    conn.commit()
                    st.success("✅ Permissões atualizadas com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar permissões: {str(e)}")
        else:
            st.warning("Nenhuma permissão encontrada para este usuário.")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Erro ao gerenciar permissões: {str(e)}")

def get_table_analysis(cursor, table_name):
    """Analisa a estrutura e dados da tabela."""
    # Análise da estrutura
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    
    # Contagem de registros
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    record_count = cursor.fetchone()[0]
    
    # Data da última atualização (assumindo que existe uma coluna 'data' ou similar)
    try:
        cursor.execute(f"SELECT MAX(data) FROM {table_name}")
        last_update = cursor.fetchone()[0]
    except:
        last_update = "N/A"
    
    # Maior user_id
    try:
        cursor.execute(f"SELECT MAX(user_id) FROM {table_name}")
        max_user_id = cursor.fetchone()[0]
    except:
        max_user_id = "N/A"
    
    return {
        "columns": columns_info,
        "record_count": record_count,
        "last_update": last_update,
        "max_user_id": max_user_id
    }

def show_crud():
    """Exibe registros administrativos em formato de tabela."""
    
    # CSS para melhorar visualização das tabelas
    st.markdown("""
    <style>
    /* CSS para melhorar visualização das tabelas */
    .stDataFrame {
        max-width: none !important;
        width: 100% !important;
    }
    
    .stDataFrame table {
        width: 100% !important;
        min-width: 100% !important;
    }
    
    .stDataFrame th,
    .stDataFrame td {
        white-space: nowrap !important;
        padding: 8px 12px !important;
        font-size: 14px !important;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 6px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 6px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    /* Melhorar visualização em telas grandes */
    .main .block-container {
        max-width: 100% !important;
        padding: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Botões de controle de visualização
    st.markdown("### 🎯 Controles de Visualização")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📺 Modo Tela Cheia (F11)", help="Use F11 do navegador para tela cheia completa"):
            st.info("💡 **Dica:** Use F11 do navegador para ativar tela cheia completa!")
    
    with col2:
        if st.button("🔍 Zoom +", help="Aumentar zoom da página"):
            st.info("💡 **Dica:** Use Ctrl + + para aumentar o zoom da página!")
    
    with col3:
        if st.button("🔍 Zoom -", help="Diminuir zoom da página"):
            st.info("💡 **Dica:** Use Ctrl + - para diminuir o zoom da página!")
    
    # Informações sobre visualização
    with st.expander("ℹ️ Dicas para Melhor Visualização", expanded=False):
        st.markdown("""
        **🎯 Para Visualizar Tabelas Grandes:**
        
        **1. Tela Cheia do Navegador:**
        - Pressione **F11** para tela cheia completa
        - Pressione **F11** novamente para sair
        
        **2. Zoom da Página:**
        - **Ctrl + +** para aumentar zoom
        - **Ctrl + -** para diminuir zoom  
        - **Ctrl + 0** para resetar zoom
        
        **3. Scroll Horizontal:**
        - Use a **barra de rolagem horizontal** na parte inferior
        - Ou use **Shift + Scroll** do mouse
        
        **4. Navegação por Teclado:**
        - **Tab** para navegar entre células
        - **Setas** para mover entre campos
        - **Enter** para confirmar edições
        
        **5. Seleção de Dados:**
        - **Ctrl + A** para selecionar tudo
        - **Ctrl + C** para copiar
        - **Ctrl + V** para colar
        """)
    
    # Definição dos tamanhos de coluna por tabela
    COLUMN_WIDTHS = {
        'usuarios': {
            'id': 'small',
            'user_id': 'small',
            'nome': 'medium',
            'email': 'medium',
            'senha': 'small',
            'perfil': 'small',
            'empresa': 'medium',
            'idioma': 'small'
        },
        'assessments': {
            'id': 'small',
            'user_id': 'small',
            'assessment_id': 'small',
            'assessment_name': 'medium',
            'access_granted': 'small',
            'created_at': 'medium',
            'updated_at': 'medium'
        },
        'forms_tab': {
            'ID_element': 'small',
            'name_element': 'small',
            'type_element': 'small',
            'math_element': 'small',
            'msg_element': 'medium',
            'value_element': 'small',
            'select_element': 'small',
            'str_element': 'medium',
            'e_col': 'small',
            'e_row': 'small',
            'user_id': 'small',
            'section': 'small',
            'col_len': 'small'
        },
        'forms_insumos': {
            'ID_element': 'small',
            'name_element': 'medium',
            'type_element': 'small',
            'math_element': 'small',
            'msg_element': 'medium',
            'value_element': 'medium',
            'select_element': 'medium',
            'str_element': 'medium',
            'e_col': 'small',
            'e_row': 'small',
            'user_id': 'small'
        },
        'forms_resultados': {
            'ID_element': 'small',
            'name_element': 'medium',
            'type_element': 'small',
            'math_element': 'small',
            'msg_element': 'medium',
            'value_element': 'small',
            'select_element': 'medium',
            'str_element': 'medium',
            'e_col': 'small',
            'e_row': 'small',
            'user_id': 'small'
        },
        'forms_result_sea': {
            'ID_element': 'small',
            'name_element': 'medium',
            'type_element': 'small',
            'math_element': 'small',
            'msg_element': 'medium',
            'value_element': 'small',
            'select_element': 'medium',
            'str_element': 'medium',
            'e_col': 'small',
            'e_row': 'small',
            'user_id': 'small'
        },
        'log_acessos': {
            'id': 'small',
            'user_id': 'small',
            'data_acesso': 'small',
            'programa': 'medium',
            'acao': 'medium'
        }
    }

    st.title("Lista de Registros ADM")
    
    if st.button("Atualizar Dados"):
        st.rerun()

    # Botão para download do banco de dados
    with open(DB_PATH, "rb") as db_file:
        if st.download_button(
            label="Download DB",
            data=db_file,
            file_name="calcrh2.db",
            mime="application/octet-stream"
        ):
            # Registra o download na auditoria
            try:
                registrar_acesso(
                    user_id=st.session_state.get("user_id"),
                    programa="CRUD",
                    acao="DOWNLOAD_DB"
                )
                st.success("✅ Download registrado na auditoria!")
            except Exception as e:
                st.warning(f"⚠️ Download realizado, mas erro ao registrar auditoria: {str(e)}")

    # Obter informações dos assessments
    assessment_info = get_assessment_info()
    assessment_tables = get_assessment_tables()
    
    # Criar lista de tabelas disponíveis
    available_tables = get_available_tables()
    
    # Verificar tabelas numeradas
    numbered_tables_info = check_numbered_tables()
    
    # Separar tabelas por categoria
    basic_tables = ["", "usuarios", "assessments", "log_acessos"]
    
    # Verificar se tabelas originais ainda existem
    if "forms_tab" in available_tables:
        basic_tables.append("forms_tab")
    if "forms_resultados" in available_tables:
        basic_tables.append("forms_resultados")
    
    # Adicionar opção de gerenciamento de permissões
    basic_tables.append("🔐 Gerenciar Permissões de Assessments")
    
    forms_tab_tables = numbered_tables_info['forms_tab_tables']
    forms_resultados_tables = numbered_tables_info['forms_resultados_tables']
    
    # Interface de seleção
    st.markdown("### 📊 Seleção de Tabela")
    
    # Mostrar informações sobre tabelas disponíveis
    with st.expander("ℹ️ Informações sobre Tabelas", expanded=False):
        st.markdown("**Tabelas Básicas:**")
        st.write(f"- usuarios, assessments, log_acessos")
        if "forms_tab" in available_tables:
            st.write("- forms_tab (original)")
        if "forms_resultados" in available_tables:
            st.write("- forms_resultados (original)")
        
        if forms_tab_tables:
            st.markdown(f"**Forms Tab Numeradas:** {len(forms_tab_tables)} tabelas")
            st.write(f"- {', '.join(forms_tab_tables)}")
        else:
            st.warning("⚠️ Nenhuma tabela forms_tab_XX encontrada")
        
        if forms_resultados_tables:
            st.markdown(f"**Forms Resultados Numeradas:** {len(forms_resultados_tables)} tabelas")
            st.write(f"- {', '.join(forms_resultados_tables)}")
        else:
            st.warning("⚠️ Nenhuma tabela forms_resultados_XX encontrada")
        
        if not forms_tab_tables and not forms_resultados_tables:
            st.error("❌ **Tabelas numeradas não encontradas!**")
            st.info("💡 **Solução:** Execute o script `create_numbered_tables.py` para criar as tabelas numeradas.")
            
            if st.button("🔄 Verificar Novamente"):
                st.rerun()
    
    # Seletor de categoria
    category_options = ["Tabelas Básicas"]
    
    # Adicionar opções baseadas nas tabelas disponíveis
    if forms_tab_tables:
        category_options.append("Forms Tab (por Assessment)")
    if forms_resultados_tables:
        category_options.append("Forms Resultados (por Assessment)")
    
    category = st.radio(
        "Selecione a categoria:",
        category_options,
        horizontal=True
    )
    
    if category == "Tabelas Básicas":
        selected_table = st.selectbox("Selecione a tabela", basic_tables, key="table_selector")
        
        # Tratar opção especial de gerenciamento de permissões
        if selected_table == "🔐 Gerenciar Permissões de Assessments":
            manage_assessment_permissions()
            return
    elif category == "Forms Tab (por Assessment)":
        if forms_tab_tables:
            # Agrupar por assessment
            assessment_groups = {}
            for table in forms_tab_tables:
                assessment_id = table.split('_')[-1]
                if assessment_id not in assessment_groups:
                    assessment_groups[assessment_id] = []
                assessment_groups[assessment_id].append(table)
            
            # Seletor de assessment
            assessment_options = [f"{aid} - {assessment_info.get(aid, 'Assessment Desconhecido')}" for aid in sorted(assessment_groups.keys())]
            selected_assessment = st.selectbox("Selecione o Assessment:", assessment_options)
            
            if selected_assessment:
                assessment_id = selected_assessment.split(' - ')[0]
                table_options = [""] + assessment_groups[assessment_id]
                selected_table = st.selectbox("Selecione a tabela:", table_options, key="forms_tab_selector")
            else:
                selected_table = ""
        else:
            st.warning("Nenhuma tabela forms_tab_ encontrada")
            selected_table = ""
    elif category == "Forms Resultados (por Assessment)":
        if forms_resultados_tables:
            # Agrupar por assessment
            assessment_groups = {}
            for table in forms_resultados_tables:
                assessment_id = table.split('_')[-1]
                if assessment_id not in assessment_groups:
                    assessment_groups[assessment_id] = []
                assessment_groups[assessment_id].append(table)
            
            # Seletor de assessment
            assessment_options = [f"{aid} - {assessment_info.get(aid, 'Assessment Desconhecido')}" for aid in sorted(assessment_groups.keys())]
            selected_assessment = st.selectbox("Selecione o Assessment:", assessment_options)
            
            if selected_assessment:
                assessment_id = selected_assessment.split(' - ')[0]
                table_options = [""] + assessment_groups[assessment_id]
                selected_table = st.selectbox("Selecione a tabela:", table_options, key="forms_resultados_selector")
            else:
                selected_table = ""
        else:
            st.warning("Nenhuma tabela forms_resultados_ encontrada")
            selected_table = ""
    
    if selected_table:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Análise da tabela
            analysis = get_table_analysis(cursor, selected_table)
            
            # Obtém informações das colunas aqui, antes de usar
            cursor.execute(f"PRAGMA table_info({selected_table})")
            columns_info = cursor.fetchall()  # Define columns_info aqui
            
            # Exibe informações da tabela em um expander
            with st.expander("Informações da Tabela", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Registros", analysis["record_count"])
                with col2:
                    if selected_table == "log_acessos":
                        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM log_acessos")
                        unique_users = cursor.fetchone()[0]
                        st.metric("Usuários Únicos", unique_users)
                    elif selected_table == "assessments":
                        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM assessments")
                        unique_users = cursor.fetchone()[0]
                        st.metric("Usuários Únicos", unique_users)
                    elif selected_table.startswith("forms_tab_") or selected_table.startswith("forms_resultados_"):
                        # Para tabelas numeradas, mostrar assessment
                        assessment_id = selected_table.split('_')[-1]
                        assessment_name = assessment_info.get(assessment_id, f"Assessment {assessment_id}")
                        st.metric("Assessment", assessment_name)
                    else:
                        st.metric("Última Atualização", analysis["last_update"])
                with col3:
                    if selected_table == "log_acessos":
                        cursor.execute("SELECT COUNT(DISTINCT data_acesso) FROM log_acessos")
                        unique_dates = cursor.fetchone()[0]
                        st.metric("Dias com Registros", unique_dates)
                    elif selected_table == "assessments":
                        cursor.execute("SELECT COUNT(*) FROM assessments WHERE access_granted = 1")
                        active_assessments = cursor.fetchone()[0]
                        st.metric("Acessos Ativos", active_assessments)
                    elif selected_table.startswith("forms_tab_") or selected_table.startswith("forms_resultados_"):
                        # Para tabelas numeradas, mostrar usuários únicos
                        cursor.execute(f"SELECT COUNT(DISTINCT user_id) FROM {selected_table}")
                        unique_users = cursor.fetchone()[0]
                        st.metric("Usuários Únicos", unique_users)
                    else:
                        st.metric("Maior User ID", analysis["max_user_id"])
                
                # Exibe estrutura da tabela
                st.write("### Estrutura da Tabela")
                structure_df = pd.DataFrame(
                    analysis["columns"],
                    columns=["cid", "name", "type", "notnull", "dflt_value", "pk"]
                )
                st.dataframe(
                    structure_df[["name", "type", "notnull", "pk"]],
                    hide_index=True,
                    use_container_width=True
                )
            
            # Busca dados
            if selected_table == "log_acessos":
                # Ordenação específica para log_acessos
                cursor.execute("""
                    SELECT 
                        id as 'id',
                        user_id as 'user_id',
                        data_acesso as 'data_acesso',
                        programa as 'programa',
                        acao as 'acao',
                        time(hora_acesso) as 'hora_acesso'
                    FROM log_acessos 
                    ORDER BY data_acesso DESC, hora_acesso DESC, id DESC
                """)
            elif selected_table == "assessments":
                # Ordenação específica para assessments
                cursor.execute("""
                    SELECT 
                        a.id,
                        a.user_id,
                        a.assessment_id,
                        a.assessment_name,
                        a.access_granted,
                        a.created_at,
                        a.updated_at,
                        u.nome as user_name
                    FROM assessments a
                    LEFT JOIN usuarios u ON a.user_id = u.user_id
                    ORDER BY a.user_id, a.assessment_id
                """)
            elif selected_table.startswith("forms_tab_") or selected_table.startswith("forms_resultados_"):
                # Filtros para tabelas numeradas
                st.markdown("#### 🔍 Filtros")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    user_id_filter = st.number_input("Filtrar por User ID (0 para todos)", min_value=0, value=0)
                
                with col2:
                    section_filter = st.text_input("Filtrar por Section (deixe vazio para todos)", "")
                
                with col3:
                    type_filter = st.selectbox(
                        "Filtrar por Type Element",
                        ["", "input", "formula", "formulaH", "selectbox", "text", "button"],
                        index=0
                    )
                
                # Adiciona seleção de ordenação
                sort_column = st.selectbox(
                    "Ordenar por coluna",
                    ["ID_element", "name_element", "type_element", "e_col", "e_row", "user_id", "section"],
                    index=0
                )
                sort_order = st.selectbox("Ordem", ["ASC", "DESC"], index=0)
                
                # Construir query com filtros
                where_conditions = []
                if user_id_filter > 0:
                    where_conditions.append(f"user_id = {user_id_filter}")
                if section_filter:
                    where_conditions.append(f"section LIKE '%{section_filter}%'")
                if type_filter:
                    where_conditions.append(f"type_element = '{type_filter}'")
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                query = f"""
                    SELECT * FROM {selected_table}
                    {where_clause}
                    ORDER BY {sort_column} {sort_order}
                """
                cursor.execute(query)
            elif selected_table == "forms_tab":
                # Adiciona filtro por user_id para forms_tab
                user_id_filter = st.number_input("Filtrar por User ID (0 para mostrar todos)", min_value=0, value=0)
                
                # Adiciona seleção de ordenação
                sort_column = st.selectbox(
                    "Ordenar por coluna",
                    ["ID_element", "name_element", "type_element", "e_col", "e_row", "user_id", "section"],
                    index=0
                )
                sort_order = st.selectbox("Ordem", ["ASC", "DESC"], index=0)
                
                # Query com filtro e ordenação
                query = f"""
                    SELECT * FROM forms_tab
                    {f"WHERE user_id = {user_id_filter}" if user_id_filter > 0 else ""}
                    ORDER BY {sort_column} {sort_order}
                """
                cursor.execute(query)
            else:
                cursor.execute(f"SELECT * FROM {selected_table}")
            
            data = cursor.fetchall()
            
            # Busca nomes das colunas
            if selected_table == "assessments":
                # Para assessments, usar colunas específicas da consulta
                columns = ['id', 'user_id', 'assessment_id', 'assessment_name', 'access_granted', 'created_at', 'updated_at', 'user_name']
            elif selected_table == "log_acessos":
                # Para log_acessos, usar colunas específicas da consulta
                columns = ['id', 'user_id', 'data_acesso', 'programa', 'acao', 'hora_acesso']
            else:
                # Para outras tabelas, usar estrutura da tabela
                cursor.execute(f"PRAGMA table_info({selected_table})")
                columns = [col[1] for col in cursor.fetchall()]
            
            # Cria DataFrame
            df = pd.DataFrame(data, columns=columns)
            
            # Configuração específica para log_acessos
            if selected_table == "log_acessos":
                column_config = {
                    "id": st.column_config.NumberColumn(
                        "id",
                        width="small",
                        required=True,
                    ),
                    "user_id": st.column_config.NumberColumn(
                        "user_id",
                        width="small",
                        required=True,
                    ),
                    "data_acesso": st.column_config.TextColumn(
                        "data_acesso",
                        width="medium",
                        required=True,
                        help="Formato: YYYY-MM-DD"
                    ),
                    "programa": st.column_config.TextColumn(
                        "programa",
                        width="medium",
                        required=True,
                    ),
                    "acao": st.column_config.TextColumn(
                        "acao",
                        width="medium",
                        required=True,
                    ),
                    "hora_acesso": st.column_config.TextColumn(
                        "hora_acesso",
                        width="small",
                        required=False,
                        help="Formato: HH:MM:SS"
                    )
                }
            # Configuração específica para assessments
            elif selected_table == "assessments":
                column_config = {
                    "id": st.column_config.NumberColumn(
                        "id",
                        width="small",
                        required=False,
                        disabled=True,
                        help="ID automático (não editável)"
                    ),
                    "user_id": st.column_config.NumberColumn(
                        "user_id",
                        width="small",
                        required=True,
                    ),
                    "assessment_id": st.column_config.SelectboxColumn(
                        "assessment_id",
                        width="small",
                        required=True,
                        options=list(assessment_info.keys())
                    ),
                    "assessment_name": st.column_config.TextColumn(
                        "assessment_name",
                        width="medium",
                        required=True,
                    ),
                    "access_granted": st.column_config.CheckboxColumn(
                        "access_granted",
                        width="small",
                        required=True,
                    ),
                    "created_at": st.column_config.TextColumn(
                        "created_at",
                        width="medium",
                        required=False,
                        disabled=True,
                        help="Data de criação automática"
                    ),
                    "updated_at": st.column_config.TextColumn(
                        "updated_at",
                        width="medium",
                        required=False,
                        disabled=True,
                        help="Data de atualização automática"
                    ),
                    "user_name": st.column_config.TextColumn(
                        "user_name",
                        width="medium",
                        required=False,
                    )
                }
            else:
                # Configura o tipo de cada coluna baseado no tipo do SQLite
                column_config = {}
                for col_info in columns_info:  # Agora columns_info está definido
                    col_name = col_info[1]
                    col_type = col_info[2].upper()
                    
                    # Define a largura da coluna baseada no dicionário COLUMN_WIDTHS
                    # Para tabelas numeradas, usar configuração genérica
                    if selected_table.startswith('forms_tab_'):
                        table_key = 'forms_tab'
                    elif selected_table.startswith('forms_resultados_'):
                        table_key = 'forms_resultados'
                    else:
                        table_key = selected_table
                    
                    column_width = COLUMN_WIDTHS.get(table_key, {}).get(col_name, 'medium')
                    
                    # Configuração especial para a tabela de usuários
                    if selected_table == "usuarios":
                        if col_name == "perfil":
                            column_config[col_name] = st.column_config.SelectboxColumn(
                                "perfil",
                                width=column_width,
                                required=True,
                                options=["adm", "usuario", "Gestor", "master"]
                            )
                        elif col_name == "idioma":
                            column_config[col_name] = st.column_config.SelectboxColumn(
                                "idioma",
                                width=column_width,
                                required=True,
                                options=["pt", "en", "es"],
                                help="Idioma preferido do usuário: pt (Português), en (English), es (Español)"
                            )
                        elif col_name == "email":
                            column_config[col_name] = st.column_config.TextColumn(
                                "email",
                                width=column_width,
                                required=True
                            )
                        else:
                            if 'INTEGER' in col_type:
                                column_config[col_name] = st.column_config.NumberColumn(
                                    col_name,
                                    width=column_width,
                                    required=True,
                                )
                            else:
                                column_config[col_name] = st.column_config.TextColumn(
                                    col_name,
                                    width=column_width,
                                    required=True
                                )
                    # Configuração especial para a tabela assessments
                    elif selected_table == "assessments":
                        if col_name == "access_granted":
                            column_config[col_name] = st.column_config.CheckboxColumn(
                                "access_granted",
                                width=column_width,
                                required=True
                            )
                        elif col_name == "assessment_id":
                            # Criar opções baseadas nos assessments disponíveis
                            assessment_options = list(assessment_info.keys())
                            column_config[col_name] = st.column_config.SelectboxColumn(
                                "assessment_id",
                                width=column_width,
                                required=True,
                                options=assessment_options
                            )
                        elif col_name == "assessment_name":
                            column_config[col_name] = st.column_config.TextColumn(
                                "assessment_name",
                                width=column_width,
                                required=True
                            )
                        else:
                            if 'INTEGER' in col_type:
                                column_config[col_name] = st.column_config.NumberColumn(
                                    col_name,
                                    width=column_width,
                                    required=True,
                                )
                            else:
                                column_config[col_name] = st.column_config.TextColumn(
                                    col_name,
                                    width=column_width,
                                    required=True
                                )
                    else:
                        # Configuração padrão para outras tabelas
                        if 'INTEGER' in col_type:
                            column_config[col_name] = st.column_config.NumberColumn(
                                col_name,
                                width=column_width,
                                required=True,
                            )
                        elif 'REAL' in col_type:
                            column_config[col_name] = st.column_config.NumberColumn(
                                col_name,
                                width=column_width,
                                required=True,
                            )
                        else:
                            column_config[col_name] = st.column_config.TextColumn(
                                col_name,
                                width=column_width,
                                required=True
                            )
            
            # Configurações otimizadas para visualização
            table_config = {
                "use_container_width": True,
                "height": 600 if len(df) > 15 else 400 if len(df) > 5 else None,  # Altura adaptativa
                "column_config": column_config,
                "hide_index": False,
                "num_rows": "dynamic",
                "key": f"editor_{selected_table}"
            }
            
            # Adicionar informações sobre a tabela
            st.info(f"📊 **Tabela:** {selected_table} | **Registros:** {len(df)} | **Colunas:** {len(df.columns)}")
            
            # Controles adicionais para visualização
            col1, col2, col3 = st.columns(3)
            
            with col1:
                show_columns = st.multiselect(
                    "🔍 Filtrar Colunas:",
                    options=df.columns.tolist(),
                    default=df.columns.tolist(),
                    help="Selecione quais colunas exibir"
                )
            
            with col2:
                if len(df) > 0:
                    # Criar opções para o selectbox
                    row_options = [10, 25, 50, 100, 250, 500, 1000]
                    # Filtrar opções que não excedam o tamanho do DataFrame
                    available_options = [opt for opt in row_options if opt <= len(df)]
                    # Sempre adicionar opção "Todas as linhas"
                    available_options.append("Todas as linhas")
                    
                    # Valor padrão: 100 se disponível, senão o maior valor disponível
                    default_index = 0
                    if 100 in available_options:
                        default_index = available_options.index(100)
                    elif len(available_options) > 0:
                        default_index = len(available_options) - 1
                    
                    selected_option = st.selectbox(
                        "📏 Máximo de Linhas:",
                        options=available_options,
                        index=default_index,
                        help="Selecione quantas linhas exibir ou 'Todas as linhas' para mostrar tudo"
                    )
                    
                    # Converter seleção para número
                    if selected_option == "Todas as linhas":
                        max_rows = len(df)
                    else:
                        max_rows = int(selected_option)
                else:
                    max_rows = 10
            
            with col3:
                auto_refresh = st.checkbox(
                    "🔄 Auto-refresh",
                    value=False,
                    help="Atualizar automaticamente a visualização"
                )
            
            # Aplicar filtros
            if show_columns:
                filtered_df = df[show_columns].head(max_rows)
            else:
                filtered_df = df.head(max_rows)
            
            # Converte para formato editável
            edited_df = st.data_editor(
                filtered_df,
                **table_config
            )
            
            # Botão para salvar alterações
            if st.button("Salvar Alterações"):
                try:
                    # Primeiro, vamos verificar se há duplicatas no DataFrame editado
                    if selected_table == 'forms_tab' or selected_table.startswith('forms_tab_'):
                        duplicates = edited_df[edited_df['ID_element'].duplicated(keep=False)]
                        if not duplicates.empty:
                            st.error(f"⚠️ Encontradas duplicatas de ID_element no editor: {duplicates['ID_element'].tolist()}")
                            return

                    # Verificações específicas para tabela assessments
                    if selected_table == 'assessments':
                        # Verificar duplicatas de user_id + assessment_id
                        duplicates = edited_df[edited_df[['user_id', 'assessment_id']].duplicated(keep=False)]
                        if not duplicates.empty:
                            st.error(f"⚠️ Encontradas duplicatas de user_id + assessment_id no editor")
                            return

                    # Detecta registros novos comparando o tamanho dos DataFrames
                    if len(edited_df) > len(df):
                        # Processa novos registros
                        new_records = edited_df.iloc[len(df):]
                        for _, row in new_records.iterrows():
                            if selected_table == 'forms_tab' or selected_table.startswith('forms_tab_'):
                                # Debug: mostra o ID que está tentando inserir
                                st.write(f"Tentando inserir ID_element: {row['ID_element']}")
                                
                                cursor.execute(f"""
                                    SELECT ID_element, rowid 
                                    FROM {selected_table} 
                                    WHERE ID_element = ?
                                """, (row['ID_element'],))
                                existing = cursor.fetchone()
                                
                                if existing:
                                    st.error(f"⚠️ Não é possível adicionar: O ID_element '{row['ID_element']}' já existe na linha {existing[1]}")
                                    continue
                            elif selected_table == 'assessments':
                                # Verificar se já existe user_id + assessment_id
                                cursor.execute("""
                                    SELECT id FROM assessments 
                                    WHERE user_id = ? AND assessment_id = ?
                                """, (row['user_id'], row['assessment_id']))
                                existing = cursor.fetchone()
                                
                                if existing:
                                    st.error(f"⚠️ Não é possível adicionar: Já existe registro para user_id {row['user_id']} e assessment_id {row['assessment_id']}")
                                    continue

                            # Filtrar colunas que existem na tabela
                            if selected_table == "assessments":
                                # Para assessments, excluir user_name que é apenas para exibição
                                table_columns = ['user_id', 'assessment_id', 'assessment_name', 'access_granted']
                                row_values = [row[col] for col in table_columns if col in row]
                                insert_query = f"""
                                INSERT INTO {selected_table} ({', '.join(table_columns)})
                                VALUES ({', '.join(['?' for _ in table_columns])})
                                """
                            else:
                                row_values = [row[col] for col in columns]
                                insert_query = f"""
                                INSERT INTO {selected_table} ({', '.join(columns)})
                                VALUES ({', '.join(['?' for _ in columns])})
                                """
                            cursor.execute(insert_query, tuple(row_values))

                    # Atualiza registros existentes
                    for index, row in edited_df.iloc[:len(df)].iterrows():
                        if selected_table == 'forms_tab' or selected_table.startswith('forms_tab_'):
                            # Verifica duplicatas considerando o user_id
                            cursor.execute(f"""
                                SELECT ID_element, rowid 
                                FROM {selected_table} 
                                WHERE ID_element = ? 
                                    AND user_id = ?
                                    AND ID_element != (
                                        SELECT ID_element 
                                        FROM {selected_table} 
                                        WHERE ID_element = ?
                                        AND user_id = ?
                                    )
                            """, (row['ID_element'], row['user_id'], row['ID_element'], row['user_id']))
                            
                            existing = cursor.fetchone()
                            if existing:
                                st.error(f"⚠️ Não é possível atualizar: O ID_element '{row['ID_element']}' já está sendo usado em outro registro com o mesmo user_id")
                                continue

                        # Atualiza usando ID_element e user_id como identificadores
                        if selected_table == 'forms_tab' or selected_table.startswith('forms_tab_'):
                            update_query = f"""
                            UPDATE {selected_table}
                            SET {', '.join(f'{col} = ?' for col in columns)}
                            WHERE ID_element = ? AND user_id = ?
                            """
                            values = tuple(row) + (row['ID_element'], row['user_id'])
                        elif selected_table == 'assessments':
                            # Para assessments, usar apenas colunas que existem na tabela
                            table_columns = ['user_id', 'assessment_id', 'assessment_name', 'access_granted']
                            update_query = f"""
                            UPDATE {selected_table}
                            SET {', '.join(f'{col} = ?' for col in table_columns)}
                            WHERE user_id = ? AND assessment_id = ?
                            """
                            values = tuple(row[col] for col in table_columns) + (row['user_id'], row['assessment_id'])
                        else:
                            update_query = f"""
                            UPDATE {selected_table}
                            SET {', '.join(f'{col} = ?' for col in columns)}
                            WHERE rowid = {index + 1}
                            """
                            values = tuple(row)
                            
                        cursor.execute(update_query, values)
                    
                    conn.commit()
                    st.success("Alterações salvas com sucesso!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Erro ao salvar alterações: {str(e)}")
            
            # Botão de download - convertendo ponto para vírgula na coluna value
            if not df.empty:
                export_df = edited_df.copy()
                
                # Procura pela coluna que contém 'value' no nome
                value_columns = [col for col in export_df.columns if 'value' in col.lower()]
                
                # Converte os números para string e substitui ponto por vírgula
                for value_col in value_columns:
                    export_df[value_col] = export_df[value_col].apply(lambda x: str(x).replace('.', ',') if pd.notnull(x) else '')
                
                # Desativa a formatação automática do pandas para números
                txt_data = export_df.to_csv(sep='\t', index=False, encoding='cp1252', float_format=None)
                st.download_button(
                    label="Download TXT",
                    data=txt_data.encode('cp1252'),
                    file_name=f"{selected_table}.txt",
                    mime="text/plain"
                )
            
            # Seção de operações de deleção
            st.markdown("---")
            st.markdown("### 🗑️ Operações de Deleção")
            st.warning("⚠️ **ATENÇÃO:** As operações de deleção são irreversíveis!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Deletar Registro Específico", type="secondary", use_container_width=True):
                    st.session_state["delete_mode"] = "single"
                    st.session_state["selected_table"] = selected_table
                    st.rerun()
            
            with col2:
                if st.button("💥 Deletar TODOS os Registros", type="secondary", use_container_width=True):
                    st.session_state["delete_mode"] = "all"
                    st.session_state["selected_table"] = selected_table
                    st.rerun()
            
            # Interface para deleção de registro específico
            if st.session_state.get("delete_mode") == "single" and st.session_state.get("selected_table") == selected_table:
                st.markdown("#### 🎯 Deletar Registro Específico")
                
                if not df.empty:
                    st.write("**Selecione os registros para deletar:**")
                    
                    # Adicionar coluna de seleção ao DataFrame
                    df_with_selection = df.copy()
                    df_with_selection['Selecionar'] = False
                    
                    # Reordenar colunas para colocar 'Selecionar' no início
                    cols = ['Selecionar'] + [col for col in df_with_selection.columns if col != 'Selecionar']
                    df_with_selection = df_with_selection[cols]
                    
                    # Configuração da coluna de seleção
                    column_config = {
                        "Selecionar": st.column_config.CheckboxColumn(
                            "Selecionar",
                            width="small",
                            required=False,
                            help="Marque para deletar"
                        )
                    }
                    
                    # Adicionar configurações existentes
                    if selected_table == "assessments":
                        column_config.update({
                            "id": st.column_config.NumberColumn("id", width="small", required=False, disabled=True),
                            "user_id": st.column_config.NumberColumn("user_id", width="small", required=True),
                            "assessment_id": st.column_config.TextColumn("assessment_id", width="small", required=True),
                            "assessment_name": st.column_config.TextColumn("assessment_name", width="medium", required=True),
                            "access_granted": st.column_config.CheckboxColumn("access_granted", width="small", required=True),
                            "created_at": st.column_config.TextColumn("created_at", width="medium", required=False, disabled=True),
                            "updated_at": st.column_config.TextColumn("updated_at", width="medium", required=False, disabled=True),
                            "user_name": st.column_config.TextColumn("user_name", width="medium", required=False, disabled=True)
                        })
                    
                    # Exibir tabela editável
                    edited_df = st.data_editor(
                        df_with_selection,
                        column_config=column_config,
                        hide_index=True,
                        use_container_width=True,
                        key=f"delete_selection_{selected_table}"
                    )
                    
                    # Botões de ação
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        if st.button("🗑️ DELETAR SELECIONADOS", type="primary", use_container_width=True):
                            selected_records = edited_df[edited_df['Selecionar'] == True]
                            
                            if selected_records.empty:
                                st.warning("⚠️ Nenhum registro selecionado para deletar.")
                            else:
                                try:
                                    conn = sqlite3.connect(DB_PATH)
                                    cursor = conn.cursor()
                                    
                                    deleted_count = 0
                                    errors = []
                                    for idx, row in selected_records.iterrows():
                                        try:
                                            # Executar deleção baseada no tipo de tabela
                                            if selected_table == 'assessments':
                                                cursor.execute("DELETE FROM assessments WHERE user_id = ? AND assessment_id = ?", 
                                                             (row['user_id'], row['assessment_id']))
                                            elif selected_table.startswith('forms_tab') or selected_table.startswith('forms_resultados'):
                                                # Para tabelas forms_tab e forms_resultados, usar ID_element e user_id
                                                cursor.execute(f"DELETE FROM {selected_table} WHERE ID_element = ? AND user_id = ?", 
                                                             (row['ID_element'], row['user_id']))
                                            elif selected_table == 'usuarios':
                                                # Para usuarios, usar id (chave primária)
                                                if 'id' in row:
                                                    cursor.execute("DELETE FROM usuarios WHERE id = ?", (row['id'],))
                                                elif 'user_id' in row:
                                                    cursor.execute("DELETE FROM usuarios WHERE user_id = ?", (row['user_id'],))
                                                else:
                                                    errors.append(f"Linha {idx}: Não foi possível identificar a chave primária")
                                                    continue
                                            elif selected_table == 'log_acessos':
                                                # Para log_acessos, usar id (chave primária)
                                                if 'id' in row:
                                                    cursor.execute("DELETE FROM log_acessos WHERE id = ?", (row['id'],))
                                                else:
                                                    errors.append(f"Linha {idx}: Coluna 'id' não encontrada")
                                                    continue
                                            else:
                                                # Para outras tabelas, tentar usar 'id' se existir, senão usar rowid baseado no índice original
                                                if 'id' in row and pd.notna(row['id']):
                                                    cursor.execute(f"DELETE FROM {selected_table} WHERE id = ?", (int(row['id']),))
                                                else:
                                                    # Fallback: usar rowid, mas buscar o rowid correto do banco
                                                    # Primeiro, tentar encontrar o registro pelos dados da linha
                                                    st.warning(f"⚠️ Tabela '{selected_table}': Usando método de deleção por correspondência de dados. Verifique se a deleção foi bem-sucedida.")
                                                    # Construir WHERE clause baseado nos dados disponíveis
                                                    where_parts = []
                                                    where_values = []
                                                    for col in df.columns:
                                                        if col != 'Selecionar' and col in row and pd.notna(row[col]):
                                                            where_parts.append(f"{col} = ?")
                                                            where_values.append(row[col])
                                                    if where_parts:
                                                        where_clause = " AND ".join(where_parts)
                                                        cursor.execute(f"DELETE FROM {selected_table} WHERE {where_clause}", tuple(where_values))
                                                    else:
                                                        errors.append(f"Linha {idx}: Não foi possível identificar o registro para deletar")
                                                        continue
                                            
                                            deleted_count += 1
                                        except Exception as e:
                                            errors.append(f"Linha {idx}: {str(e)}")
                                            continue
                                    
                                    conn.commit()
                                    
                                    if errors:
                                        error_msg = f"⚠️ {deleted_count} registro(s) deletado(s), mas {len(errors)} erro(s) ocorreram:\n"
                                        for error in errors[:5]:  # Mostrar apenas os primeiros 5 erros
                                            error_msg += f"  - {error}\n"
                                        if len(errors) > 5:
                                            error_msg += f"  ... e mais {len(errors) - 5} erro(s)"
                                        st.warning(error_msg)
                                    else:
                                        st.success(f"✅ {deleted_count} registro(s) deletado(s) com sucesso!")
                                    
                                    conn.close()
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao deletar registros: {str(e)}")
                                    import traceback
                                    st.error(f"Detalhes: {traceback.format_exc()}")
                                    if 'conn' in locals():
                                        conn.close()
                    
                    with col2:
                        if st.button("❌ CANCELAR", use_container_width=True):
                            st.session_state.pop("delete_mode", None)
                            st.session_state.pop("selected_table", None)
                            st.rerun()
                    
                    with col3:
                        if st.button("🔄 ATUALIZAR", use_container_width=True):
                            st.rerun()
                else:
                    st.info("A tabela está vazia.")
            
            # Interface para deleção de todos os registros
            elif st.session_state.get("delete_mode") == "all" and st.session_state.get("selected_table") == selected_table:
                st.markdown("#### 💥 Deletar TODOS os Registros")
                delete_all_records(selected_table)
            
            # Botão para cancelar operação de deleção
            if st.session_state.get("delete_mode"):
                if st.button("❌ Cancelar Operação de Deleção", use_container_width=True):
                    st.session_state["delete_mode"] = None
                    st.session_state["selected_table"] = None
                    st.rerun()
        
        except Exception as e:
            st.error(f"Erro ao processar dados: {str(e)}")
        
        finally:
            conn.close()

def delete_single_record(table_name, record_id, user_id=None):
    """
    Deleta um registro específico da tabela com confirmação
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o registro existe
        if table_name == 'assessments':
            cursor.execute("SELECT * FROM assessments WHERE user_id = ? AND assessment_id = ?", (user_id, record_id))
        elif table_name.startswith('forms_tab'):
            cursor.execute("SELECT * FROM {} WHERE ID_element = ? AND user_id = ?".format(table_name), (record_id, user_id))
        else:
            cursor.execute("SELECT * FROM {} WHERE rowid = ?".format(table_name), (record_id,))
        
        record = cursor.fetchone()
        if not record:
            st.error("❌ Registro não encontrado!")
            return False
        
        # Mostrar warning de confirmação
        st.warning("⚠️ **ATENÇÃO: OPERAÇÃO IRREVERSÍVEL**")
        st.error("🚨 **Você está prestes a DELETAR um registro permanentemente!**")
        st.error("🚨 **Esta ação NÃO PODE ser desfeita!**")
        
        # Botão de confirmação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ CONFIRMAR DELETAR", type="primary", use_container_width=True):
                try:
                    # Executar deleção
                    if table_name == 'assessments':
                        cursor.execute("DELETE FROM assessments WHERE user_id = ? AND assessment_id = ?", (user_id, record_id))
                    elif table_name.startswith('forms_tab'):
                        cursor.execute("DELETE FROM {} WHERE ID_element = ? AND user_id = ?".format(table_name), (record_id, user_id))
                    else:
                        cursor.execute("DELETE FROM {} WHERE rowid = ?".format(table_name), (record_id,))
                    
                    conn.commit()
                    st.success("✅ Registro deletado com sucesso!")
                    st.rerun()
                    return True
                    
                except Exception as e:
                    st.error(f"❌ Erro ao deletar registro: {str(e)}")
                    return False
        
        with col2:
            if st.button("❌ CANCELAR", use_container_width=True):
                st.info("Operação cancelada.")
                return False
        
        conn.close()
        return False
        
    except Exception as e:
        st.error(f"❌ Erro ao deletar registro: {str(e)}")
        return False

def delete_all_records(table_name):
    """
    Deleta todos os registros da tabela com confirmação
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Contar registros existentes
        cursor.execute("SELECT COUNT(*) FROM {}".format(table_name))
        total_records = cursor.fetchone()[0]
        
        if total_records == 0:
            st.info("ℹ️ A tabela já está vazia.")
            return False
        
        # Mostrar warning de confirmação
        st.warning("⚠️ **ATENÇÃO: OPERAÇÃO IRREVERSÍVEL**")
        st.error(f"🚨 **Você está prestes a DELETAR TODOS os {total_records} registros da tabela '{table_name}'!**")
        st.error("🚨 **Esta ação NÃO PODE ser desfeita!**")
        st.error("🚨 **TODOS os dados serão perdidos permanentemente!**")
        
        # Botão de confirmação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ CONFIRMAR DELETAR TUDO", type="primary", use_container_width=True):
                try:
                    # Executar deleção de todos os registros
                    cursor.execute("DELETE FROM {}".format(table_name))
                    conn.commit()
                    st.success(f"✅ Todos os {total_records} registros foram deletados com sucesso!")
                    st.rerun()
                    return True
                    
                except Exception as e:
                    st.error(f"❌ Erro ao deletar registros: {str(e)}")
                    return False
        
        with col2:
            if st.button("❌ CANCELAR", use_container_width=True):
                st.info("Operação cancelada.")
                return False
        
        conn.close()
        return False
        
    except Exception as e:
        st.error(f"❌ Erro ao deletar registros: {str(e)}")
        return False

