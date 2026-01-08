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
        
        
        # Interface de seleção de usuário (sem pesquisa)
        st.markdown("### 👥 Selecionar Usuário para Análise")
        
        # Usar todos os usuários (sem filtro de pesquisa)
        df_filtrado = df_usuarios
        
        if len(df_filtrado) == 0:
            st.warning("⚠️ **Nenhum usuário encontrado** na base de dados.")
            return
        
        # Exibir total de usuários
        st.markdown(f"**Usuários disponíveis:** {len(df_filtrado)}")
        
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
                    
                    # Verificar quais assessments o usuário tem dados
                    assessments_disponiveis = []
                    
                    for assessment_id in ["01", "02", "03", "04", "05"]:
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM forms_resultados_{assessment_id} 
                            WHERE user_id = ?
                        """, (user_id_selecionado,))
                        
                        if cursor.fetchone()[0] > 0:
                            # Buscar nome do assessment
                            cursor.execute("""
                                SELECT assessment_name FROM assessments 
                                WHERE assessment_id = ? LIMIT 1
                            """, (assessment_id,))
                            result = cursor.fetchone()
                            assessment_name = result[0] if result else f"Assessment {assessment_id}"
                            
                            assessments_disponiveis.append((assessment_id, assessment_name))
                    
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
                        if assessments_disponiveis:
                            st.success(f"✅ **Status:** Usuário possui {len(assessments_disponiveis)} análise(s) disponível(is)")
                            
                            st.markdown("### 🎯 Análises Disponíveis")
                            st.info("💡 **Clique no botão do assessment que deseja visualizar:**")
                            
                            # Criar botões para cada assessment disponível
                            for assessment_id, assessment_name in assessments_disponiveis:
                                if st.button(f"📊 **{assessment_name}**", use_container_width=True, key=f"btn_assessment_{assessment_id}"):
                                    # Registrar acesso à análise
                                    registrar_acesso(
                                        user_id=st.session_state.get("user_id"),
                                        programa="resultados_adm.py",
                                        acao=f"visualizar_analise_usuario_{user_id_selecionado}_{assessment_id}"
                                    )
                                    
                                    # Armazenar dados para redirecionamento
                                    st.session_state["admin_view_user_id"] = user_id_selecionado
                                    st.session_state["admin_view_user_name"] = usuario_info['Nome']
                                    st.session_state["admin_selected_assessment"] = assessment_id
                                    st.session_state["redirect_to_analysis"] = True
                                    
                                    # Redirecionar para a página de análises
                                    st.rerun()
                        else:
                            st.warning("⚠️ **Status:** Usuário ainda não possui análises disponíveis")
                            st.info("💡 **Orientação:** Este usuário precisa completar pelo menos um assessment primeiro.")
        
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