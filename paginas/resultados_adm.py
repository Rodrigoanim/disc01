# resultados_adm.py
# Módulo de administração para visualização de análises de usuários
# Data: 29/07/2025 - Hora: 29:00

import streamlit as st
import sqlite3
import pandas as pd
from config import DB_PATH
from paginas.monitor import registrar_acesso
# from paginas.resultados import show_results  # Removido - usando redirecionamento

def show_resultados_adm():
    """
    Módulo administrativo para visualização de análises de usuários.
    Permite que perfis 'master' e 'adm' selecionem usuários e visualizem suas análises.
    """
    
    # Verificar se o usuário tem perfil master ou adm
    user_profile = st.session_state.get("user_profile", "").lower()
    if user_profile not in ["master", "adm"]:
        st.error("❌ **Acesso não autorizado.** Esta página é restrita para usuários Master e Administradores.")
        return
    
    # Registrar acesso
    registrar_acesso(
        user_id=st.session_state.get("user_id"),
        programa="resultados_adm.py",
        acao="acesso_modulo_admin"
    )
    
    # Título da página
    st.markdown("""
        <p style='text-align: center; font-size: 30px; font-weight: bold;'>
            📊 Administração - Análises de Usuários
        </p>
    """, unsafe_allow_html=True)
    
    # Informações da sessão admin
    st.markdown(f"""
        <div style='background-color:#e8f4f8;padding:15px;border-radius:5px;margin-bottom:20px;'>
            <p style='font-size:14px;color:#333;'>
                <strong>👤 Administrador:</strong> {st.session_state.get('user_name')}<br>
                <strong>🔑 Perfil:</strong> {st.session_state.get('user_profile')}<br>
                <strong>📋 Função:</strong> Visualizar análises de usuários cadastrados
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Verificar se o banco existe
    if not DB_PATH.exists():
        st.error(f"❌ **Banco de dados não encontrado:** {DB_PATH}")
        return
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar usuários cadastrados
        cursor.execute("""
            SELECT user_id, nome, email, perfil, empresa 
            FROM usuarios 
            WHERE perfil = 'usuario'
            ORDER BY nome
        """)
        usuarios = cursor.fetchall()
        
        if not usuarios:
            st.warning("⚠️ **Nenhum usuário encontrado** na base de dados.")
            return
        
        # Criar DataFrame para melhor manipulação
        df_usuarios = pd.DataFrame(usuarios, columns=['User ID', 'Nome', 'Email', 'Perfil', 'Empresa'])
        
        # Exibir estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Usuários", len(usuarios))
        with col2:
            empresas_unicas = len(df_usuarios['Empresa'].dropna().unique())
            st.metric("Empresas Cadastradas", empresas_unicas)
        with col3:
            # Verificar quantos usuários têm análises
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM forms_resultados 
                WHERE user_id IN (SELECT user_id FROM usuarios WHERE perfil = 'usuario')
            """)
            usuarios_com_analises = cursor.fetchone()[0]
            st.metric("Usuários com Análises", usuarios_com_analises)
        
        st.markdown("---")
        
        # Interface de pesquisa e seleção
        st.markdown("### 🔍 Pesquisar e Selecionar Usuário")
        
        # Campo de pesquisa
        pesquisa = st.text_input(
            "Digite nome ou email para pesquisar:",
            placeholder="Ex: João Silva ou joao@empresa.com",
            key="pesquisa_usuario"
        )
        
        # Filtrar usuários baseado na pesquisa
        if pesquisa:
            mascara = (
                df_usuarios['Nome'].str.contains(pesquisa, case=False, na=False) |
                df_usuarios['Email'].str.contains(pesquisa, case=False, na=False)
            )
            df_filtrado = df_usuarios[mascara]
        else:
            df_filtrado = df_usuarios
        
        if len(df_filtrado) == 0:
            st.warning("🔍 **Nenhum usuário encontrado** com os critérios de pesquisa.")
            return
        
        # Exibir tabela de usuários filtrados
        st.markdown(f"**Usuários encontrados:** {len(df_filtrado)}")
        
        # Criar lista para seleção
        opcoes_usuarios = []
        for _, usuario in df_filtrado.iterrows():
            opcao = f"{usuario['Nome']} ({usuario['Email']}) - ID: {usuario['User ID']}"
            opcoes_usuarios.append((opcao, usuario['User ID']))
        
        # Seletor de usuário
        if opcoes_usuarios:
            opcao_selecionada = st.selectbox(
                "📋 **Selecione o usuário que deseja analisar:**",
                options=[opcao[0] for opcao in opcoes_usuarios],
                index=None,
                placeholder="Escolha um usuário da lista...",
                key="usuario_selecionado"
            )
            
            if opcao_selecionada:
                # Encontrar o user_id correspondente
                user_id_selecionado = None
                for opcao, user_id in opcoes_usuarios:
                    if opcao == opcao_selecionada:
                        user_id_selecionado = user_id
                        break
                
                if user_id_selecionado:
                    # Exibir informações do usuário selecionado
                    usuario_info = df_filtrado[df_filtrado['User ID'] == user_id_selecionado].iloc[0]
                    
                    st.success(f"✅ **Usuário selecionado:** {usuario_info['Nome']}")
                    
                    # Verificar se o usuário tem análises
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM forms_resultados 
                        WHERE user_id = ?
                    """, (user_id_selecionado,))
                    tem_analises = cursor.fetchone()[0] > 0
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown(f"""
                            **📋 Informações do Usuário:**
                            - **Nome:** {usuario_info['Nome']}
                            - **Email:** {usuario_info['Email']}
                            - **ID:** {usuario_info['User ID']}
                            - **Empresa:** {usuario_info['Empresa'] or 'Não informada'}
                        """)
                    
                    with col2:
                        if tem_analises:
                            st.success("✅ **Status:** Usuário possui análises DISC")
                            
                            # Botão para visualizar análises
                            if st.button("🔍 **Visualizar Análises DISC**", use_container_width=True, type="primary"):
                                # Registrar acesso à análise
                                registrar_acesso(
                                    user_id=st.session_state.get("user_id"),
                                    programa="resultados_adm.py",
                                    acao=f"visualizar_analise_usuario_{user_id_selecionado}"
                                )
                                
                                # Armazenar dados para redirecionamento
                                st.session_state["admin_view_user_id"] = user_id_selecionado
                                st.session_state["admin_view_user_name"] = usuario_info['Nome']
                                st.session_state["redirect_to_analysis"] = True
                                
                                # Redirecionar para a página de análises
                                st.rerun()
                        else:
                            st.warning("⚠️ **Status:** Usuário ainda não realizou análises DISC")
                            st.info("💡 **Orientação:** Este usuário precisa completar as avaliações de Âncoras P1 e P2 primeiro.")
        
        # Tabela resumo (opcional, pode ser colocada em um expander)
        with st.expander("📋 **Ver todos os usuários cadastrados**", expanded=False):
            st.dataframe(
                df_filtrado,
                use_container_width=True,
                hide_index=True
            )
    
    except sqlite3.Error as e:
        st.error(f"❌ **Erro de banco de dados:** {str(e)}")
    except Exception as e:
        st.error(f"❌ **Erro inesperado:** {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close() 