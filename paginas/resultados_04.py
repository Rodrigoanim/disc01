# resultados_04.py
# Data: 08/01/2026 
# Pagina de resultados e Analises - Dashboard
# Tabela: forms_resultados_04

try:
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        KeepTogether,
        PageBreak
    )
except ImportError as e:
    print(f"Erro ao importar ReportLab: {e}")

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import io
import tempfile
import matplotlib.pyplot as plt
import traceback
import re
import os
from paginas.monitor import registrar_acesso
import time

from config import DB_PATH  # Adicione esta importação


def format_br_number(value):
    """
    Formata um número para o padrão brasileiro
    
    Args:
        value: Número a ser formatado
        
    Returns:
        str: Número formatado como string
        
    Notas:
        - Valores >= 1: sem casas decimais
        - Valores < 1: 3 casas decimais
        - Usa vírgula como separador decimal
        - Usa ponto como separador de milhar
        - Retorna "0" para valores None ou inválidos
    """
    try:
        if value is None:
            return "0"
        
        float_value = float(value)
        if abs(float_value) >= 1:
            return f"{float_value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')  # Duas casas decimais com separador de milhar
        else:
            return f"{float_value:.3f}".replace('.', ',')  # 3 casas decimais
    except:
        return "0"

def format_br_integer(value):
    """
    Formata um número como inteiro no padrão brasileiro
    
    Args:
        value: Número a ser formatado
        
    Returns:
        str: Número inteiro formatado como string
        
    Notas:
        - Sempre retorna número inteiro (sem casas decimais)
        - Usa ponto como separador de milhar
        - Retorna "0" para valores None ou inválidos
    """
    try:
        if value is None:
            return "0"
        
        float_value = float(value)
        int_value = int(round(float_value))  # Arredonda para o inteiro mais próximo
        return f"{int_value:,}".replace(',', '.')  # Formata com separador de milhar
    except:
        return "0"

def parse_br_number(value):
    """
    Converte um valor em formato brasileiro (vírgula decimal) para float
    
    Args:
        value: Valor a ser convertido (string, float ou int)
        
    Returns:
        float: Valor convertido para float
        
    Notas:
        - Se valor já for float ou int, retorna diretamente
        - Se for string, trata formato brasileiro (vírgula como decimal)
        - Remove pontos de milhar e converte vírgula para ponto
        - Retorna 0.0 para valores inválidos
    """
    try:
        if value is None:
            return 0.0
        
        # Se já for float ou int, retorna diretamente
        if isinstance(value, (float, int)):
            return float(value)
        
        # Converte para string e remove espaços
        str_value = str(value).strip()
        
        # Se string vazia
        if not str_value:
            return 0.0
        
        # Remove pontos de milhar e substitui vírgula por ponto decimal
        str_value = str_value.replace('.', '').replace(',', '.')
        
        # Converte para float
        return float(str_value)
        
    except Exception as e:
        print(f"# Debug: Erro ao converter valor brasileiro '{value}': {str(e)}")
        return 0.0

def titulo(cursor, element):
    """
    Exibe títulos formatados na interface com base nos valores do banco de dados.
    """
    try:
        name = element[0]        # name_element
        type_elem = element[1]   # type_element
        msg = element[3]         # msg_element
        value = element[4]       # value_element (já é REAL do SQLite)
        str_value = element[6]   # str_element
        col = element[7]         # e_col
        row = element[8]         # e_row
        
        # Verifica se a coluna é válida
        if col > 6:
            st.error(f"Posição de coluna inválida para o título {name}: {col}. Deve ser entre 1 e 6.")
            return
        
        # Se for do tipo 'titulo', usa o str_element do próprio registro
        if type_elem == 'titulo':
            if str_value:
                # Se houver um valor numérico para exibir
                if value is not None:
                    # Formata o valor para o padrão brasileiro
                    value_br = format_br_number(value)
                    # Substitui {value} no str_value pelo valor formatado
                    str_value = str_value.replace('{value}', value_br)
                st.markdown(str_value, unsafe_allow_html=True)
            else:
                st.markdown(msg, unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Erro ao processar título: {str(e)}")

def pula_linha(cursor, element):
    """
    Adiciona uma linha em branco na interface quando o type_element é 'pula linha'
    """
    try:
        type_elem = element[1]  # type_element
        
        if type_elem == 'pula linha':
            st.markdown("<br>", unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Erro ao processar pula linha: {str(e)}")

def new_user(cursor, user_id: int, tabela: str):
    """
    Cria registros iniciais para um novo usuário na tabela especificada,
    copiando os dados do template (user_id = 0)
    
    Args:
        cursor: Cursor do banco de dados
        user_id: ID do usuário
        tabela: Nome da tabela para criar os registros
    """
    try:
        # Verifica se já existem registros para o usuário
        cursor.execute(f"""
            SELECT COUNT(*) FROM {tabela} 
            WHERE user_id = ?
        """, (user_id,))
        
        if cursor.fetchone()[0] == 0:
            # Copia dados do template (user_id = 0) para o novo usuário
            cursor.execute(f"""
                INSERT INTO {tabela} (
                    user_id, name_element, type_element, math_element,
                    msg_element, value_element, select_element, str_element,
                    e_col, e_row, section
                )
                SELECT 
                    ?, name_element, type_element, math_element,
                    msg_element, value_element, select_element, str_element,
                    e_col, e_row, section
                FROM {tabela}
                WHERE user_id = 0
            """, (user_id,))
            
            cursor.connection.commit()
            st.success("Dados iniciais criados com sucesso!")
            
    except Exception as e:
        st.error(f"Erro ao criar dados do usuário: {str(e)}")

def call_dados(cursor, element, tabela_destino: str):
    """
    Busca dados na tabela forms_tab_04 e atualiza o value_element do registro atual.
    
    Args:
        cursor: Cursor do banco de dados
        element: Tupla com dados do elemento
        tabela_destino: Nome da tabela onde o valor será atualizado
    """
    try:
        name = element[0]        # name_element
        type_elem = element[1]   # type_element
        str_value = element[6]   # str_element
        user_id = element[10]    # user_id
        
        if type_elem == 'call_dados':
            # Busca o valor com CAST para garantir precisão decimal
            cursor.execute("""
                SELECT CAST(value_element AS DECIMAL(20, 8))
                FROM forms_tab_04 
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (str_value, user_id))
            
            result = cursor.fetchone()
            
            if result:
                value = float(result[0]) if result[0] is not None else 0.0
                
                # Atualiza usando a tabela passada como parâmetro
                cursor.execute(f"""
                    UPDATE {tabela_destino}
                    SET value_element = CAST(? AS DECIMAL(20, 8))
                    WHERE name_element = ? 
                    AND user_id = ?
                """, (value, name, user_id))
                
                cursor.connection.commit()
            else:
                st.warning(f"Valor não encontrado na tabela forms_tab_04 para {str_value} (user_id: {user_id})")
                
    except Exception as e:
        st.error(f"Erro ao processar call_dados: {str(e)}")

def grafico_barra(cursor, element):
    """
    Cria um gráfico de barras verticais com dados da tabela específica.
    
    Args:
        cursor: Cursor do banco de dados SQLite
        element: Tupla contendo os dados do elemento tipo 'grafico'
            [0] name_element: Nome do elemento
            [1] type_element: Tipo do elemento (deve ser 'grafico')
            [3] msg_element: Título/mensagem do gráfico
            [5] select_element: Lista de type_names separados por '|'
            [6] str_element: Lista de rótulos separados por '|'
            [9] section: Cor do gráfico (formato hex)
            [10] user_id: ID do usuário
    

    """
    try:
        # Extrai informações do elemento
        type_elem = element[1]   # type_element
        msg = element[3]         # msg_element (título do gráfico)
        select = element[5]      # select_element
        rotulos = element[6]     # str_element
        section = element[9]     # section (cor do gráfico)
        user_id = element[10]    # user_id
        
        # Validação do tipo e dados necessários
        if type_elem != 'grafico':
            return
            
        if not select or not rotulos:
            st.error("Configuração incompleta do gráfico: select ou rótulos vazios")
            return
            
        # Processa as listas de type_names e rótulos
        type_names = select.split('|')
        labels = rotulos.split('|')
        
        # Lista para armazenar os valores
        valores = []
        
        # Busca os valores para cada type_name no banco
        for type_name in type_names:
            tabela = st.session_state.tabela_escolhida
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = result[0] if result and result[0] is not None else 0.0
            valores.append(valor)
        
        # Define paleta de cores corporativas com bom contraste
        # Paleta expandida para suportar até 7 armadilhas com cores distintas
        cores_corporativas = [
            '#C62828',  # Vermelho corporativo (A)
            '#F57C00',  # Laranja/Âmbar corporativo (B)
            '#2E7D32',  # Verde corporativo (C)
            '#1565C0',  # Azul corporativo (D)
            '#6A1B9A',  # Roxo/Violeta corporativo (E)
            '#00838F',  # Teal/Ciano corporativo (F)
            '#D84315'   # Vermelho-alaranjado corporativo (G)
        ]
        
        # Aplica as cores pela posição (ordem das barras)
        cores = []
        for i in range(len(labels)):
            if i < len(cores_corporativas):
                cores.append(cores_corporativas[i])
            else:
                # Se houver mais de 7, usa tons alternados
                cores.append('#5C6BC0')  # Índigo como cor adicional
        
        # Cria labels curtos para o eixo X (letras ou números)
        labels_curtos = [chr(65 + i) if i < 26 else f"A{i-25}" for i in range(len(labels))]  # A, B, C, D...
        
        # Adiciona o título antes do gráfico usando HTML direto
        if msg:
            st.markdown(f"""
                <h2 style="text-align: center; font-size: 36px; font-weight: 60; color: #2c3e50; margin: 5px 0; padding: 3px; letter-spacing: 0.5px;">{msg}</h2>
            """, unsafe_allow_html=True)
        
        # Cria o gráfico usando Graph Objects com design moderno
        fig = go.Figure(data=[
            go.Bar(
                x=labels_curtos,  # Usa labels curtos no eixo X
                y=valores,
                marker=dict(
                    color=cores,
                    line=dict(width=1.5, color='rgba(255,255,255,0.8)'),  # Borda sutil nas barras
                    opacity=0.9
                ),
                showlegend=False,
                text=valores,  # Mostra valores nas barras
                textposition='outside',
                textfont=dict(size=14, color='#2c3e50', family='Arial')
            )
        ])
        
        # Configura o layout do gráfico com design moderno
        fig.update_layout(
            # Remove títulos dos eixos
            xaxis_title=None,
            yaxis_title=None,
            # Remove legenda
            showlegend=False,
            # Define dimensões
            height=450,
            width=None,  # largura responsiva
            # Background e margens
            plot_bgcolor='rgba(255,255,255,1)',
            paper_bgcolor='rgba(255,255,255,1)',
            margin=dict(l=40, r=40, t=20, b=60),  # Margem top reduzida já que não há mais tabela antes do gráfico
            # Configuração do eixo X
            xaxis=dict(
                tickfont=dict(size=16, color='#2c3e50', family='Arial'),
                gridcolor='rgba(0,0,0,0.05)',
                linecolor='rgba(0,0,0,0.1)',
                showgrid=False
            ),
            # Configuração do eixo Y
            yaxis=dict(
                tickfont=dict(size=16, color='#2c3e50', family='Arial'),
                tickformat=",.",  # formato dos números
                separatethousands=True,  # separador de milhar
                gridcolor='rgba(0,0,0,0.08)',
                linecolor='rgba(0,0,0,0.1)',
                showgrid=True,
                zeroline=False,
                range=[0, None]  # Permite que o eixo Y se ajuste automaticamente para mostrar todos os valores
            ),
            # Hover melhorado
            hovermode='closest',
            hoverlabel=dict(
                bgcolor='rgba(255,255,255,0.95)',
                bordercolor='rgba(0,0,0,0.1)',
                font_size=14,
                font_family='Arial'
            )
        )
        
        # Exibe o gráfico no Streamlit com chave única para evitar conflitos de ID
        name_element = element[0]  # Usa o name_element como chave única
        graph_key = f"grafico_{name_element}_{user_id}"  # Chave única baseada no elemento e usuário
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=graph_key)
        
        # Criar tabela de legenda moderna abaixo do gráfico
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Preparar dados da legenda
        dados_legenda = []
        for i, (label_curto, label_completo, cor) in enumerate(zip(labels_curtos, labels, cores)):
            dados_legenda.append({
                'Indicador': label_curto,
                'Armadilha': label_completo,
                'Cor': cor
            })
        
        # Criar HTML da tabela de legenda com estilos modernos
        linhas_legenda = []
        for idx, item in enumerate(dados_legenda):
            bg_color = '#ffffff' if idx % 2 == 0 else '#f8f9fa'
            # Círculo colorido para representar a cor da barra
            circulo_cor = f"<span style='display: inline-block; width: 20px; height: 20px; background-color: {item['Cor']}; border-radius: 50%; border: 2px solid rgba(0,0,0,0.1); margin-right: 8px; vertical-align: middle;'></span>"
            linhas_legenda.append(
                f"<tr style='background-color: {bg_color}; transition: all 0.2s ease;'>"
                f"<td style='padding: 12px 14px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-size: 18px; font-weight: 600; text-align: center; width: 10%;'>{item['Indicador']}</td>"
                f"<td style='padding: 12px 14px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-size: 18px;'>{circulo_cor}{item['Armadilha']}</td>"
                f"</tr>"
            )
        
        html_legenda = f"""
        <style>
            .legend-table-container {{
                font-size: 18px;
                width: 85%;
                margin: 20px auto;
            }}
            .legend-table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                border-radius: 12px;
                overflow: hidden;
                background-color: #FFFFFF;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.05);
            }}
            .legend-table thead tr {{
                background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
            }}
            .legend-table th {{
                text-align: left;
                padding: 14px;
                background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
                border-bottom: 3px solid #c8e6c9;
                color: #2c3e50;
                font-size: 18px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
            .legend-table th:first-child {{
                text-align: center;
                width: 10%;
            }}
            .legend-table tbody tr {{
                transition: all 0.2s ease;
            }}
            .legend-table tbody tr:hover {{
                background-color: #f0f7f2 !important;
                transform: scale(1.01);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }}
            .legend-table tbody td {{
                padding: 12px 14px;
                border-bottom: 1px solid #e0e0e0;
                color: #2c3e50;
                font-size: 18px;
            }}
            .legend-table tbody tr:last-child td {{
                border-bottom: none;
            }}
        </style>
        <div class="legend-table-container">
            <table class="legend-table">
                <thead>
                    <tr>
                        <th>Indicador</th>
                        <th>Armadilha</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(linhas_legenda)}
                </tbody>
            </table>
        </div>
        """
        
        # Exibe a tabela de legenda
        st.markdown(html_legenda, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")

def tabela_dados(cursor, element):
    """
    Cria uma tabela estilizada com dados da tabela forms_resultados_04.
    Tabela transposta (vertical) com valores em vez de nomes.
    
    Args:
        cursor: Conexão com o banco de dados
        element: Tupla com os dados do elemento tipo 'tabela'
        
    Configurações do elemento:
        type_element: 'tabela'
        msg_element: título da tabela
        math_element: número de colunas da tabela
        select_element: type_names separados por | (ex: 'N24|N25|N26')
        str_element: rótulos separados por | (ex: 'Energia|Água|GEE')
        
    Nota: 
        - Layout usando três colunas do Streamlit para centralização
        - Proporção de colunas: [1, 8, 1] (10% vazio, 80% tabela, 10% vazio)
        - Valores formatados no padrão brasileiro
        - Tabela transposta (vertical) para melhor leitura
        - Coluna 'Valor' com largura aumentada em 25%
    """
    try:
        # Extrai informações do elemento
        type_elem = element[1]   # type_element
        msg = element[3]         # msg_element (título da tabela)
        select = element[5]      # select_element (type_names separados por |)
        rotulos = element[6]     # str_element (rótulos separados por |)
        user_id = element[10]    # user_id
        
        if type_elem != 'tabela':
            return
            
        # Validações iniciais
        if not select or not rotulos:
            st.error("Configuração incompleta da tabela: select ou rótulos vazios")
            return
            
        # Separa os type_names e rótulos
        type_names = select.split('|')
        rotulos = rotulos.split('|')
        
        # Valida se quantidade de rótulos corresponde aos type_names
        if len(type_names) != len(rotulos):
            st.error("Número de rótulos diferente do número de valores")
            return
            
        # Lista para armazenar os valores
        valores = []
        
        # Busca os valores para cada type_name
        for type_name in type_names:
            tabela = st.session_state.tabela_escolhida  # Pega a tabela da sessão
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = format_br_integer(result[0]) if result and result[0] is not None else '0'
            valores.append(valor)
        
        # Criar DataFrame com os dados
        df = pd.DataFrame({
            'Armadilhas': rotulos,
            'Valor': valores
        })
        
        # Criar três colunas, usando a do meio para a tabela
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col2:
            # Espaçamento fixo definido no código
            spacing = 20  # valor em pixels ajustado conforme solicitado
            
            # Adiciona quebras de linha antes do título
            num_breaks = spacing // 20
            for _ in range(num_breaks):
                st.markdown("<br>", unsafe_allow_html=True)
            
            # Exibe o título da tabela a esquerda
            st.markdown(f"<h4 style='text-align: left;'>{msg}</h4>", unsafe_allow_html=True)
            
            # Criar HTML da tabela com estilos modernos e profissionais
            # Gerar linhas do corpo com hover effect e cores alternadas
            linhas_tbody = []
            for idx, (_, row) in enumerate(df.iterrows()):
                bg_color = '#ffffff' if idx % 2 == 0 else '#f8f9fa'
                linhas_tbody.append(
                    f"<tr style='background-color: {bg_color}; transition: all 0.2s ease;'>"
                    f"<td style='padding: 12px 14px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-size: 18px;'>{row['Armadilhas']}</td>"
                    f"<td style='text-align: center; padding: 12px 14px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-size: 18px; font-weight: 600;'>{row['Valor']}</td>"
                    f"</tr>"
                )
            
            html_table = f"""
            <style>
                .modern-table-container {{
                    font-size: 18px;
                    width: 85%;
                    margin: 0 auto;
                }}
                .modern-table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    border-radius: 12px;
                    overflow: hidden;
                    background-color: #FFFFFF;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.05);
                }}
                .modern-table thead tr {{
                    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
                }}
                .modern-table th {{
                    text-align: left;
                    padding: 14px;
                    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
                    border-bottom: 3px solid #c8e6c9;
                    color: #2c3e50;
                    font-size: 18px;
                    font-weight: 600;
                    letter-spacing: 0.3px;
                }}
                .modern-table th:first-child,
                .modern-table td:first-child {{
                    width: 75%;
                    white-space: nowrap;
                }}
                .modern-table th:last-child,
                .modern-table td:last-child {{
                    text-align: center;
                    width: 25%;
                }}
                .modern-table tbody tr {{
                    transition: all 0.2s ease;
                }}
                .modern-table tbody tr:hover {{
                    background-color: #f0f7f2 !important;
                    transform: scale(1.01);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                }}
                .modern-table tbody td {{
                    padding: 12px 14px;
                    border-bottom: 1px solid #e0e0e0;
                    color: #2c3e50;
                    font-size: 18px;
                }}
                .modern-table tbody tr:last-child td {{
                    border-bottom: none;
                }}
            </style>
            <div class="modern-table-container">
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>Armadilhas</th>
                            <th>Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(linhas_tbody)}
                    </tbody>
                </table>
            </div>
            """
            
            # Exibe a tabela HTML
            st.markdown(html_table, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao criar tabela: {str(e)}")

def gerar_dados_tabela(cursor, elemento, height_pct=100, width_pct=100):
    """
    Função auxiliar para gerar dados da tabela para o PDF
    """
    try:
        msg = elemento[3]         # msg_element
        select = elemento[5]      # select_element
        rotulos = elemento[6]     # str_element
        user_id = elemento[10]    # user_id
        
        if not select or not rotulos:
            st.error("Configuração incompleta da tabela: select ou rótulos vazios")
            return None
            
        # Separa os type_names e rótulos
        type_names = str(select).split('|')
        labels = str(rotulos).split('|')
        valores = []
        
        # Busca os valores para cada type_name
        for type_name in type_names:
            cursor.execute(f"""
                SELECT name_element, value_element 
                FROM {st.session_state.tabela_escolhida}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = format_br_integer(result[1]) if result and result[1] is not None else '0'
            valores.append(valor)
        
        # Retornar dados formatados para a tabela
        return {
            'title': msg if msg else "Tabela de Dados",
            'data': [['Armadilhas', 'Valor']] + list(zip(labels, valores)),
            'height_pct': height_pct,
            'width_pct': width_pct
        }
        
    except Exception as e:
        st.error(f"Erro ao gerar dados da tabela: {str(e)}")
        return None

def gerar_dados_grafico(cursor, elemento, tabela_escolhida: str, height_pct=100, width_pct=100):
    try:
        msg = elemento[3]         # msg_element
        select = elemento[5]      # select_element
        rotulos = elemento[6]     # str_element
        section = elemento[9]     # section (cor do gráfico)
        user_id = elemento[10]    # user_id
        if not select or not rotulos:
            return None
        type_names = str(select).split('|')
        labels = str(rotulos).split('|')
        valores = []
        # Busca os valores para cada type_name
        for type_name in type_names:
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela_escolhida}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            result = cursor.fetchone()
            valor = float(result[0]) if result and result[0] is not None else 0.0
            valores.append(valor)
        # Define paleta de cores corporativas com bom contraste
        # Paleta expandida para suportar até 7 armadilhas com cores distintas
        cores_corporativas = [
            '#C62828',  # Vermelho corporativo (A)
            '#F57C00',  # Laranja/Âmbar corporativo (B)
            '#2E7D32',  # Verde corporativo (C)
            '#1565C0',  # Azul corporativo (D)
            '#6A1B9A',  # Roxo/Violeta corporativo (E)
            '#00838F',  # Teal/Ciano corporativo (F)
            '#D84315'   # Vermelho-alaranjado corporativo (G)
        ]
        
        # Aplica as cores pela posição (ordem das barras)
        cores = []
        for i in range(len(labels)):
            if i < len(cores_corporativas):
                cores.append(cores_corporativas[i])
            else:
                # Se houver mais de 7, usa tons alternados
                cores.append('#5C6BC0')  # Índigo como cor adicional
        
        # Cria labels curtos para o eixo X (letras ou números) - mesma lógica da tela web
        labels_curtos = [chr(65 + i) if i < 26 else f"A{i-25}" for i in range(len(labels))]  # A, B, C, D...
        
        # Ajustar base_width para ocupar mais da largura da página A4
        base_width = 250
        base_height = 270  # Aumentado 50% na altura: 180 * 1.5 = 270
        # largura dos gráficos igual à tabela (usando width_pct)
        adj_width = int(base_width * 2.2 * 0.8 * (width_pct / 100)) + 20  # aumenta 20 na largura
        adj_height = int(base_height * (height_pct / 100)) - 25           # reduz 25 na altura
        
        # Calcular valor máximo para ajustar o range do eixo Y com padding
        max_valor = max(valores) if valores else 6
        y_max = max_valor * 1.2  # Adiciona 20% de padding no topo para evitar corte dos valores
        
        # Criar gráfico com labels curtos e design moderno
        fig = go.Figure(data=[
            go.Bar(
                x=labels_curtos,  # Usa labels curtos no eixo X
                y=valores,
                marker=dict(
                    color=cores,
                    line=dict(width=1.5, color='rgba(255,255,255,0.8)'),  # Borda sutil nas barras
                    opacity=0.9
                ),
                showlegend=False,
                text=valores,  # Mostra valores nas barras
                textposition='outside',
                textfont=dict(size=10, color='#2c3e50', family='Arial')
            )
        ])
        fig.update_layout(
            showlegend=False,
            height=int(adj_height * 2),  # Aumentado 
            width=adj_width,
            margin=dict(t=20, b=50, l=40, r=40),  # Margem top reduzida já que não há mais tabela antes do gráfico
            plot_bgcolor='rgba(255,255,255,1)',
            paper_bgcolor='rgba(255,255,255,1)',
            xaxis=dict(
                title=None,
                tickfont=dict(size=10, color='#2c3e50', family='Arial'),
                gridcolor='rgba(0,0,0,0.05)',
                linecolor='rgba(0,0,0,0.1)',
                showgrid=False
            ),
            yaxis=dict(
                title=None,
                tickfont=dict(size=10, color='#2c3e50', family='Arial'),
                tickformat=",.1f",  # Formato com 1 casa decimal
                separatethousands=True,
                gridcolor='rgba(0,0,0,0.08)',
                linecolor='rgba(0,0,0,0.1)',
                showgrid=True,
                zeroline=False,
                range=[0, y_max]  # Range fixo com padding de 20% no topo para evitar corte
            )
        )
        img_bytes = fig.to_image(format="png", scale=3)
        
        # Preparar dados da legenda para o PDF
        dados_legenda = []
        for i, (label_curto, label_completo, cor) in enumerate(zip(labels_curtos, labels, cores)):
            dados_legenda.append({
                'Indicador': label_curto,
                'Armadilha': label_completo,
                'Cor': cor
            })
        
        return {
            'title': msg,
            'image': Image(io.BytesIO(img_bytes), 
                         width=adj_width,
                         height=adj_height),
            'legenda': dados_legenda  # Adiciona dados da legenda
        }
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")
        return None

def subtitulo(titulo_pagina: str):
    
    try:
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown(f"""
                <p style='
                    text-align: Left;
                    font-size: 30px;
                    color: #000000;
                    margin-top: 15px;
                    margin-bottom: 15px;
                    font-family: sans-serif;
                    font-weight: 50;
                '>{titulo_pagina}</p>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("Gerar PDF", type="primary", key="btn_gerar_pdf"):
                try:
                    msg_placeholder = st.empty()
                    msg_placeholder.info("Gerando PDF... Por favor, aguarde.")
                    
                    for _ in range(3):
                        try:
                            conn = sqlite3.connect(DB_PATH, timeout=20)
                            cursor = conn.cursor()
                            break
                        except sqlite3.OperationalError as e:
                            if "database is locked" in str(e):
                                time.sleep(1)
                                continue
                            raise e
                    else:
                        st.error("Não foi possível conectar ao banco de dados. Tente novamente.")
                        return
                    
                    buffer = generate_pdf_content(
                        cursor, 
                        st.session_state.user_id,
                        st.session_state.tabela_escolhida
                    )
                    
                    if buffer:
                        conn.close()
                        msg_placeholder.success("PDF gerado com sucesso!")
                        st.download_button(
                            label="Baixar PDF",
                            data=buffer.getvalue(),
                            file_name="Armadilhas_Empresario_Analise.pdf",
                            mime="application/pdf",
                        )
                    
                except Exception as e:
                    msg_placeholder.error(f"Erro ao gerar PDF: {str(e)}")
                    st.write("Debug: Stack trace completo:", traceback.format_exc())
                finally:
                    if 'conn' in locals() and conn:
                        conn.close()
                    
    except Exception as e:
        st.error(f"Erro ao gerar interface: {str(e)}")

def generate_pdf_content(cursor, user_id: int, tabela_escolhida: str):
    """
    Função para gerar PDF com layout específico: 
    Gráfico Perfil → Análise Detalhada
    (Tabela foi removida - o gráfico com legenda é suficiente)
    """
    try:
        # Configurações de dimensões
        base_width = 400  # largura base para tabelas e gráficos
        base_height = 200 # altura base
        table_width = base_width * 0.8  # largura da tabela
        graph_width = base_width        # largura do gráfico

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=72,
            topMargin=36,
            bottomMargin=36
        )

        with sqlite3.connect(DB_PATH, timeout=20) as pdf_conn:
            pdf_cursor = pdf_conn.cursor()
            elements = []
            styles = getSampleStyleSheet()

            # Estilos para o PDF
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20, 
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=16,  # Reduzido proporcionalmente
                spaceBefore=15,
                spaceAfter=20
            )
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 18),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 18),  # Aumentado 50% do valor original (14): 14 * 1.5 = 21, mas usando 18 para melhor legibilidade
                ('BOTTOMPADDING', (0, 0), (-1, 0), 16),
                ('TOPPADDING', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
            ])
            
            graphic_title_style = ParagraphStyle(
                'GraphicTitle',
                parent=styles['Heading2'],
                fontSize=16,  # Aumentado 
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=14,  # Aumentado proporcionalmente
                spaceBefore=6,
                spaceAfter=8
            )

            # Título principal - PDF
            elements.append(Paragraph("Relatório de Devolutiva do Assessment", title_style))
            elements.append(Paragraph("As 7 Armadilhas do Empresário", title_style))
            elements.append(Spacer(1, 20))

            # Adicionar Informações do Usuário no topo do PDF
            pdf_cursor.execute("""
                SELECT u.nome, u.email, u.empresa 
                FROM usuarios u 
                WHERE u.user_id = ?
            """, (user_id,))
            usuario_info_pdf = pdf_cursor.fetchone()
            
            if usuario_info_pdf:
                # Estilo para o título da seção de informações do usuário
                info_usuario_title_style = ParagraphStyle(
                    'InfoUsuarioTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    alignment=0,  # Alinhado à esquerda
                    textColor=colors.HexColor('#1E1E1E'),
                    fontName='Helvetica-Bold',
                    leading=16,
                    spaceBefore=0,
                    spaceAfter=10
                )
                
                # Estilo para os dados do usuário
                info_usuario_style = ParagraphStyle(
                    'InfoUsuario',
                    parent=styles['Normal'],
                    fontSize=11,
                    alignment=0,  # Alinhado à esquerda
                    textColor=colors.HexColor('#1E1E1E'),
                    fontName='Helvetica',
                    leading=13,
                    spaceBefore=2,
                    spaceAfter=2
                )
                
                elements.append(Paragraph("👤 Informações do Usuário", info_usuario_title_style))
                elements.append(Paragraph(f"<b>👤 Nome:</b> {usuario_info_pdf[0] or 'Não informado'}", info_usuario_style))
                elements.append(Paragraph(f"<b>📧 E-mail:</b> {usuario_info_pdf[1] or 'Não informado'}", info_usuario_style))
                elements.append(Paragraph(f"<b>🏢 Empresa:</b> {usuario_info_pdf[2] or 'Não informado'}", info_usuario_style))
                elements.append(Spacer(1, 15))

            # Buscar todos os elementos (tabelas e gráficos)
            pdf_cursor.execute(f"""
                SELECT name_element, type_element, math_element, msg_element,
                       value_element, select_element, str_element, e_col, e_row,
                       section, user_id
                FROM {tabela_escolhida}
                WHERE (type_element = 'tabela' OR type_element = 'grafico')
                AND user_id = ?
                ORDER BY e_row, e_col
            """, (user_id,))
            elementos = pdf_cursor.fetchall()

            # Separar tabelas e gráficos
            tabelas = [e for e in elementos if e[1] == 'tabela']
            graficos = [e for e in elementos if e[1] == 'grafico']

            # Layout específico: Gráfico Perfil → Análise Detalhada
            # (Tabela foi removida - não é mais necessária, o gráfico com legenda é suficiente)
            
            # 1. GRÁFICO PERFIL (primeiro gráfico encontrado)
            if len(graficos) > 0:
                grafico_perfil = graficos[0]
                dados_grafico_perfil = gerar_dados_grafico(pdf_cursor, grafico_perfil, tabela_escolhida, height_pct=100, width_pct=100)
                if dados_grafico_perfil:
                    # Usa o título do próprio gráfico ou padrão
                    titulo_grafico = dados_grafico_perfil['title'] or "RESULTADOS DE PERFIS"
                    elements.append(Paragraph(titulo_grafico, graphic_title_style))
                    elements.append(Spacer(1, 10))
                    elements.append(Table(
                        [[dados_grafico_perfil['image']]],
                        colWidths=[graph_width],
                        style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                    ))
                    elements.append(Spacer(1, 15))
                    
                    # Adicionar tabela de legenda após o gráfico
                    if 'legenda' in dados_grafico_perfil and dados_grafico_perfil['legenda']:
                        # Estilo para tabela de legenda (similar à tabela de ranking)
                        legenda_table_style = TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Coluna Indicador centralizada
                            ('ALIGN', (1, 0), (1, 0), 'CENTER'),   # Cabeçalho Armadilha centralizado
                            ('ALIGN', (1, 1), (1, -1), 'CENTER'),   # Dados Armadilha centralizados
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (0, 0), 11),       # Tamanho normal para Indicador
                            ('FONTSIZE', (1, 0), (1, 0), 15),       # 40% maior: 11 * 1.4 = 15.4 ≈ 15
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 15),  # Aumentado 50%: 10 * 1.5 = 15
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('TOPPADDING', (0, 1), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                            ('LEFTPADDING', (0, 0), (-1, -1), 8),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('BOX', (0, 0), (-1, -1), 2, colors.black),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Alinhamento vertical no meio
                        ])
                        
                        # Estilo para texto da legenda - Indicador (centralizado, sem quebra)
                        legenda_indicador_style = ParagraphStyle(
                            'LegendaIndicadorStyle',
                            parent=styles['Normal'],
                            fontSize=6,  # Reduzido 40%: 10 * 0.6 = 6
                            alignment=1,  # Centralizado
                            textColor=colors.HexColor('#1E1E1E'),
                            fontName='Helvetica-Bold',
                            leading=7,  # Reduzido proporcionalmente
                            spaceBefore=0,
                            spaceAfter=0
                        )
                        
                        # Estilo para cabeçalho Armadilha (centralizado, reduzido 40%)
                        legenda_armadilha_header_style = ParagraphStyle(
                            'LegendaArmadilhaHeaderStyle',
                            parent=styles['Normal'],
                            fontSize=9,  # Reduzido 40%: 15 * 0.6 = 9
                            alignment=1,  # Centralizado
                            textColor=colors.HexColor('#1E1E1E'),
                            fontName='Helvetica-Bold',
                            leading=11,  # Reduzido proporcionalmente
                            spaceBefore=0,
                            spaceAfter=0
                        )
                        
                        # Estilo para texto da legenda - Armadilha (centralizado)
                        legenda_armadilha_style = ParagraphStyle(
                            'LegendaArmadilhaStyle',
                            parent=styles['Normal'],
                            fontSize=11,  # Reduzido 30%: 15 * 0.7 = 10.5 ≈ 11
                            alignment=1,  # Centralizado
                            textColor=colors.HexColor('#1E1E1E'),
                            fontName='Helvetica',
                            leading=13,  # Reduzido proporcionalmente
                            spaceBefore=0,
                            spaceAfter=0
                        )
                        
                        # Preparar dados da tabela de legenda
                        dados_tabela_legenda = []
                        dados_tabela_legenda.append([
                            Paragraph("Indicador", legenda_indicador_style),
                            Paragraph("Armadilha", legenda_armadilha_header_style)  # Usa estilo maior e centralizado
                        ])
                        
                        for item in dados_grafico_perfil['legenda']:
                            indicador_para = Paragraph(item['Indicador'], legenda_indicador_style)
                            armadilha_para = Paragraph(item['Armadilha'], legenda_armadilha_style)
                            dados_tabela_legenda.append([
                                indicador_para,
                                armadilha_para
                            ])
                        
                        # Criar tabela de legenda
                        t_legenda = Table(dados_tabela_legenda, colWidths=[table_width * 0.15, table_width * 0.85])
                        t_legenda.setStyle(legenda_table_style)
                        elements.append(Table([[t_legenda]], colWidths=[table_width], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                    
                    elements.append(Spacer(1, 30))

            # 5. ADICIONAR ARQUIVO 00_Abertura.md (após gráfico, antes do ranking)
            try:
                import os
                current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                arquivo_abertura = os.path.join(current_dir, "Conteudo", "04", "00_Abertura.md")
                
                if os.path.exists(arquivo_abertura):
                    # Estilos para o conteúdo
                    abertura_style = ParagraphStyle(
                        'AberturaStyle',
                        parent=styles['Normal'],
                        fontSize=11,
                        alignment=0,
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica',
                        leading=13,
                        spaceBefore=8,
                        spaceAfter=8
                    )
                    
                    titulo_abertura_style = ParagraphStyle(
                        'TituloAberturaStyle',
                        parent=styles['Heading2'],
                        fontSize=12,
                        alignment=0,
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica-Bold',
                        leading=14,
                        spaceBefore=14,
                        spaceAfter=10
                    )
                    
                    with open(arquivo_abertura, 'r', encoding='utf-8') as file:
                        conteudo_abertura = file.read()
                    
                    processar_e_adicionar_markdown_pdf(conteudo_abertura, elements, abertura_style, titulo_abertura_style)
                    elements.append(Spacer(1, 20))
                    
            except Exception as e:
                print(f"Erro ao adicionar 00_Abertura.md ao PDF: {str(e)}")
                pass

            # 6. ADICIONAR RANKING DAS ARMADILHAS
            try:
                # Obter dados do ranking
                dados_ranking = obter_dados_ranking_pdf(pdf_cursor, user_id, tabela_escolhida)
                
                if dados_ranking:
                    # Estilo específico para tabela do ranking (30% menor)
                    ranking_table_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Primeira coluna centralizada
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # Segunda coluna centralizada
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (0, 0), 11),       # Tamanho normal para Indicador
                            ('FONTSIZE', (1, 0), (1, 0), 15),       # 40% maior: 11 * 1.4 = 15.4 ≈ 15  # 16 * 0.7 = 11.2 ≈ 11
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 15),  # Aumentado 50%: 10 * 1.5 = 15
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('TOPPADDING', (0, 1), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP')  # Alinhamento vertical no topo
                    ])
                    
                    # Estilo para texto da coluna Armadilhas (permite quebra de linha)
                    ranking_text_style = ParagraphStyle(
                        'RankingTextStyle',
                        parent=styles['Normal'],
                        fontSize=11,  # Reduzido 30%: 15 * 0.7 = 10.5 ≈ 11
                        alignment=1,  # Centralizado
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica',
                        leading=13,  # Reduzido proporcionalmente
                        spaceBefore=0,
                        spaceAfter=0
                    )
                    
                    # Estilo para valores (não precisa quebrar linha)
                    ranking_value_style = ParagraphStyle(
                        'RankingValueStyle',
                        parent=styles['Normal'],
                        fontSize=11,  # Reduzido 30%: 15 * 0.7 = 10.5 ≈ 11
                        alignment=1,  # Centralizado
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica',
                        leading=13,  # Reduzido proporcionalmente
                        spaceBefore=0,
                        spaceAfter=0
                    )
                    
                    # Adicionar título do ranking
                    elements.append(Spacer(1, 20))
                    elements.append(Paragraph("Ranking das Armadilhas - TOP 3", graphic_title_style))
                    elements.append(Spacer(1, 10))
                    
                    # Preparar dados da tabela com Paragraph para permitir quebra de linha
                    dados_tabela_ranking = []
                    
                    # Cabeçalho
                    dados_tabela_ranking.append([
                        Paragraph("Armadilhas", ranking_text_style),
                        Paragraph("Risco", ranking_value_style)
                    ])
                    
                    # Dados com quebra de linha automática para nomes longos
                    for armadilha, nivel_risco in dados_ranking:
                        # Usar Paragraph para permitir quebra de linha
                        # Limitar largura aproximada para forçar quebra (ajustar conforme necessário)
                        armadilha_para = Paragraph(armadilha, ranking_text_style)
                        nivel_risco_para = Paragraph(nivel_risco, ranking_value_style)
                        dados_tabela_ranking.append([armadilha_para, nivel_risco_para])
                    
                    # Criar tabela do ranking com larguras ajustadas
                    # Proporção: 3/4 (75%) para primeira coluna e 1/4 (25%) para segunda coluna
                    t_ranking = Table(dados_tabela_ranking, colWidths=[table_width * 0.75, table_width * 0.25])
                    t_ranking.setStyle(ranking_table_style)
                    elements.append(Table([[t_ranking]], colWidths=[table_width], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                    elements.append(Spacer(1, 20))
            except Exception as e:
                print(f"Erro ao adicionar ranking ao PDF: {str(e)}")
                pass

            # 7. ADICIONAR ARQUIVO 00_Devolutiva.md (após ranking, antes do relatório detalhado)
            try:
                import os
                current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                arquivo_devolutiva = os.path.join(current_dir, "Conteudo", "04", "00_Devolutiva.md")
                
                if os.path.exists(arquivo_devolutiva):
                    # Estilos para o conteúdo
                    devolutiva_style = ParagraphStyle(
                        'DevolutivaStyle',
                        parent=styles['Normal'],
                        fontSize=11,
                        alignment=0,
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica',
                        leading=13,
                        spaceBefore=8,
                        spaceAfter=8
                    )
                    
                    titulo_devolutiva_style = ParagraphStyle(
                        'TituloDevolutivaStyle',
                        parent=styles['Heading2'],
                        fontSize=12,
                        alignment=0,
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica-Bold',
                        leading=14,
                        spaceBefore=14,
                        spaceAfter=10
                    )
                    
                    with open(arquivo_devolutiva, 'r', encoding='utf-8') as file:
                        conteudo_devolutiva = file.read()
                    
                    processar_e_adicionar_markdown_pdf(conteudo_devolutiva, elements, devolutiva_style, titulo_devolutiva_style)
                    elements.append(Spacer(1, 20))
                    
            except Exception as e:
                print(f"Erro ao adicionar 00_Devolutiva.md ao PDF: {str(e)}")
                pass

            # 8. ADICIONAR RELATÓRIO DETALHADO DAS ARMADILHAS
            try:
                # Obter as 3 primeiras armadilhas do ranking
                top_3_armadilhas = obter_top_3_armadilhas_pdf(pdf_cursor, user_id, tabela_escolhida)
                
                if top_3_armadilhas:
                    # Adicionar quebra de página
                    elements.append(PageBreak())
                    elements.append(Paragraph("Relatório Detalhado das Armadilhas", title_style))
                    elements.append(Spacer(1, 15))
                    
                    # Estilos para o relatório (reduzido 40%)
                    relatorio_style = ParagraphStyle(
                        'RelatorioStyle',
                        parent=styles['Normal'],
                        fontSize=11,  # Reduzido 40%: 18 * 0.6 = 10.8 ≈ 11
                        alignment=0,
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica',
                        leading=13,  # Reduzido proporcionalmente
                        spaceBefore=8,
                        spaceAfter=8
                    )
                    
                    # Estilo para títulos de seção no relatório
                    titulo_relatorio_style = ParagraphStyle(
                        'TituloRelatorioStyle',
                        parent=styles['Heading2'],
                        fontSize=12,  # Reduzido 40%: 20 * 0.6 = 12
                        alignment=0,
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica-Bold',
                        leading=14,  # Reduzido proporcionalmente
                        spaceBefore=16,
                        spaceAfter=10
                    )
                    
                    # Adicionar arquivos das 3 armadilhas com sufixos de classificação
                    import os
                    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    
                    # Verificar se é formato antigo (lista) ou novo (dicionário)
                    if isinstance(top_3_armadilhas, list):
                        # Compatibilidade com formato antigo
                        top_3_nomes = top_3_armadilhas
                        sufixos = {}
                    else:
                        # Novo formato
                        top_3_nomes = top_3_armadilhas.get('armadilhas', [])
                        sufixos = top_3_armadilhas.get('sufixos', {})
                    
                    for nome_armadilha in top_3_nomes:
                        if nome_armadilha:
                            # Obter sufixo se disponível
                            sufixo = sufixos.get(nome_armadilha, "")
                            arquivo_armadilha = mapear_armadilha_para_arquivo(nome_armadilha, sufixo)
                            
                            if arquivo_armadilha:
                                caminho_arquivo = os.path.join(current_dir, "Conteudo", "04", arquivo_armadilha)
                                
                                if os.path.exists(caminho_arquivo):
                                    elements.append(Spacer(1, 12))
                                    with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                                        conteudo_armadilha = file.read()
                                    
                                    # Processar markdown para PDF com identificação de títulos
                                    processar_e_adicionar_markdown_pdf(conteudo_armadilha, elements, relatorio_style, titulo_relatorio_style)
                                else:
                                    # Fallback: tentar arquivo sem sufixo
                                    arquivo_base = mapear_armadilha_para_arquivo(nome_armadilha, "")
                                    if arquivo_base:
                                        caminho_base = os.path.join(current_dir, "Conteudo", "04", arquivo_base)
                                        if os.path.exists(caminho_base):
                                            elements.append(Spacer(1, 12))
                                            with open(caminho_base, 'r', encoding='utf-8') as file:
                                                conteudo_armadilha = file.read()
                                            processar_e_adicionar_markdown_pdf(conteudo_armadilha, elements, relatorio_style, titulo_relatorio_style)
            except Exception as e:
                # Se houver erro, continua sem o relatório detalhado
                print(f"Erro ao adicionar relatório detalhado ao PDF: {str(e)}")
                pass

            # 8. ADICIONAR CRÉDITOS DO DESENVOLVEDOR E PROGRAMADOR
            try:
                # Estilo para o título dos créditos
                creditos_titulo_style = ParagraphStyle(
                    'CreditosTituloStyle',
                    parent=styles['Heading3'],
                    fontSize=12,  # Tamanho similar ao título de seção
                    alignment=0,  # Alinhado à esquerda
                    textColor=colors.HexColor('#1E1E1E'),
                    fontName='Helvetica-Bold',
                    leading=14,
                    spaceBefore=20,
                    spaceAfter=10
                )
                
                # Estilo para o texto dos créditos
                creditos_texto_style = ParagraphStyle(
                    'CreditosTextoStyle',
                    parent=styles['Normal'],
                    fontSize=10,  # Tamanho menor para créditos
                    alignment=0,  # Alinhado à esquerda
                    textColor=colors.HexColor('#1E1E1E'),
                    fontName='Helvetica',
                    leading=12,
                    spaceBefore=4,
                    spaceAfter=4
                )
                
                # Adicionar espaçamento antes dos créditos (2 linhas adicionais)
                elements.append(Spacer(1, 20))
                elements.append(Spacer(1, 24))  # Adiciona 2 linhas de espaço extra
                
                # Adicionar título dos créditos
                elements.append(Paragraph("Agende sua Reunião Estratégica", creditos_titulo_style))
                
                # Adicionar créditos com formatação em negrito usando HTML
                elements.append(Paragraph("Caso o diagnóstico indique áreas críticas, estou à disposição para uma conversa estratégica. Analisaremos o cenário atual e definiremos ações iniciais para fortalecer a gestão. Agende a reunião e avance com clareza e segurança.Caso o diagnóstico indique áreas críticas, estou à disposição para uma conversa estratégica. Analisaremos o cenário atual e definiremos ações iniciais para fortalecer a gestão. Agende a reunião e avance com clareza e segurança.", creditos_texto_style))
                elements.append(Paragraph("E-mail: erika7rossi@gmail.com - WhatsApp: (11) 99506-6778", creditos_texto_style))
                
                # Adicionar espaçamento antes dos créditos finais
                elements.append(Spacer(1, 30))
                
                # Adicionar créditos de criação e programação (centralizados)
                creditos_finais_style = ParagraphStyle(
                    'CreditosFinaisStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    alignment=1,  # Centralizado
                    textColor=colors.HexColor('#1E1E1E'),
                    fontName='Helvetica',
                    leading=12,
                    spaceBefore=10,
                    spaceAfter=10
                )
                
                elements.append(Paragraph("Criação: Erika Rossi - EAR Consultoria", creditos_finais_style))
                elements.append(Paragraph("Programação: Nagano - AnimGrafs", creditos_finais_style))
                
                # Adicionar espaçamento antes dos logos
                elements.append(Spacer(1, 15))
                
                # Adicionar logos (Logo_1b.jpg contém ambos os logos)
                try:
                    # Caminho do logo - subir dois níveis da pasta paginas para a raiz
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    logo_path = os.path.join(os.path.dirname(current_dir), "Logo_1b.jpg")
                    if os.path.exists(logo_path):
                        # Carregar imagem com tamanho proporcional
                        logo_img = Image(logo_path, width=200, height=60)  # Tamanho ajustado para o PDF
                        # Centralizar o logo usando Table
                        logo_table = Table([[logo_img]], colWidths=[graph_width])
                        logo_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        elements.append(logo_table)
                except Exception as logo_error:
                    print(f"Erro ao adicionar logo ao PDF: {str(logo_error)}")
                    pass
                
            except Exception as e:
                # Se houver erro, continua sem os créditos
                print(f"Erro ao adicionar créditos ao PDF: {str(e)}")
                pass

            doc.build(elements)
            return buffer
    except Exception as e:
        st.error(f"Erro ao gerar conteúdo do PDF: {str(e)}")
        return None

def show_results(tabela_escolhida: str, titulo_pagina: str, user_id: int):
    """
    Função principal para exibir a interface web
    """
    try:
        if not user_id:
            st.error("Usuário não está logado!")
            return
            
        # Armazena a tabela na sessão para uso em outras funções
        st.session_state.tabela_escolhida = tabela_escolhida
        
        # Adiciona o subtítulo antes do conteúdo principal
        subtitulo(titulo_pagina)
        
        # Estabelece conexão com retry
        for _ in range(3):
            try:
                conn = sqlite3.connect(DB_PATH, timeout=20)
                cursor = conn.cursor()
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    time.sleep(1)
                    continue
                raise e
        else:
            st.error("Não foi possível conectar ao banco de dados. Tente novamente.")
            return
            
        # 1. Verifica/inicializa dados na tabela escolhida
        new_user(cursor, user_id, tabela_escolhida)
        conn.commit()
        
        # 2. Exibir Informações do Participante no topo da tela
        cursor.execute("""
            SELECT u.nome, u.email, u.empresa 
            FROM usuarios u 
            WHERE u.user_id = ?
        """, (user_id,))
        usuario_info = cursor.fetchone()
        
        if usuario_info:
            st.markdown("### 👤 Informações do Usuário")
            st.markdown(f"**👤 Nome:** {usuario_info[0] or 'Não informado'}")  
            st.markdown(f"**📧 E-mail:** {usuario_info[1] or 'Não informado'}")
            st.markdown(f"**🏢 Empresa:** {usuario_info[2] or 'Não informado'}")
            st.markdown("---")  # Linha separadora
        
        # 3. Registra acesso à página
        registrar_acesso(
            user_id,
            "resultados",
            f"Acesso na simulação {titulo_pagina}"
        )

        # Configuração para esconder elementos durante a impressão e controlar quebra de página
        hide_streamlit_style = """
            <style>
                @media print {
                    [data-testid="stSidebar"] {
                        display: none !important;
                    }
                    .stApp {
                        margin: 0;
                        padding: 0;
                    }
                    #MainMenu {
                        display: none !important;
                    }
                    .page-break {
                        page-break-before: always !important;
                    }
                }
            </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)
        
        # Buscar todos os elementos ordenados por row e col
        cursor.execute(f"""
            SELECT name_element, type_element, math_element, msg_element,
                   value_element, select_element, str_element, e_col, e_row,
                   section, user_id
            FROM {tabela_escolhida}
            WHERE (type_element = 'titulo' OR type_element = 'pula linha' 
                  OR type_element = 'call_dados' OR type_element = 'grafico'
                  OR type_element = 'tabela')
            AND user_id = ?
            ORDER BY e_row, e_col
        """, (user_id,))
        
        elements = cursor.fetchall()
        
        # Contador para gráficos
        grafico_count = 0
        
        # Agrupar elementos por e_row
        row_elements = {}
        for element in elements:
            e_row = element[8]  # e_row do elemento
            if e_row not in row_elements:
                row_elements[e_row] = []
            row_elements[e_row].append(element)
        
        # Processar elementos por linha
        for e_row in sorted(row_elements.keys()):
            row_data = row_elements[e_row]
            
            # Processar gráficos (tabelas foram removidas - não são mais necessárias)
            # Depois processar outros elementos em duas colunas
            graficos_na_linha = [elem for elem in row_data if elem[1] == 'grafico']
            for grafico in graficos_na_linha:
                grafico_count += 1
                grafico_barra(cursor, grafico)
                if grafico_count == 2:
                    st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

            outros_elementos = [elem for elem in row_data if elem[1] not in ('tabela', 'grafico')]
            if outros_elementos:
                with st.container():
                    col1, col2 = st.columns(2)
                    
                    # Processar elementos não-tabela e não-gráfico
                    for element in outros_elementos:
                        e_col = element[7]  # e_col do elemento
                        
                        if e_col <= 3:
                            with col1:
                                if element[1] == 'titulo':
                                    titulo(cursor, element)
                                elif element[1] == 'pula linha':
                                    pula_linha(cursor, element)
                                elif element[1] == 'call_dados':
                                    call_dados(cursor, element, tabela_escolhida)
                        else:
                            with col2:
                                if element[1] == 'titulo':
                                    titulo(cursor, element)
                                elif element[1] == 'pula linha':
                                    pula_linha(cursor, element)
                                elif element[1] == 'call_dados':
                                    call_dados(cursor, element, tabela_escolhida)
        
        # 5. Gerar e exibir a análise 7 Armadilhas (sem expander, conteúdo direto)
        analisar_vulnerabilidade_7armadilhas_streamlit(cursor, user_id)

    except Exception as e:
        st.error(f"Erro ao carregar resultados: {str(e)}")
    finally:
        if conn:
            conn.close()

def tabela_dados_sem_titulo(cursor, element):
    """Versão da função tabela_dados sem o título"""
    try:
        type_elem = element[1]   # type_element
        select = element[5]      # select_element
        rotulos = element[6]     # str_element
        user_id = element[10]    # user_id
        
        if type_elem != 'tabela':
            return
            
        # Validações iniciais
        if not select or not rotulos:
            st.error("Configuração incompleta da tabela: select ou rótulos vazios")
            return
            
        # Separa os type_names e rótulos
        type_names = select.split('|')
        rotulos = rotulos.split('|')
        
        # Valida se quantidade de rótulos corresponde aos type_names
        if len(type_names) != len(rotulos):
            st.error("Número de rótulos diferente do número de valores")
            return
            
        # Lista para armazenar os valores
        valores = []
        
        # Busca os valores para cada type_name
        for type_name in type_names:
            tabela = st.session_state.tabela_escolhida  # Pega a tabela da sessão
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = format_br_integer(result[0]) if result and result[0] is not None else '0'
            valores.append(valor)
        
        # Criar DataFrame com os dados
        df = pd.DataFrame({
            'Armadilhas': rotulos,
            'Valor': valores
        })
        
        # Criar três colunas, usando a do meio para a tabela
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col2:
            # Criar HTML da tabela com estilos modernos e profissionais (sem título)
            # Gerar linhas do corpo com hover effect e cores alternadas
            linhas_tbody = []
            for idx, (_, row) in enumerate(df.iterrows()):
                bg_color = '#ffffff' if idx % 2 == 0 else '#f8f9fa'
                linhas_tbody.append(
                    f"<tr style='background-color: {bg_color}; transition: all 0.2s ease;'>"
                    f"<td style='padding: 12px 14px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-size: 18px;'>{row['Armadilhas']}</td>"
                    f"<td style='text-align: center; padding: 12px 14px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-size: 18px; font-weight: 600;'>{row['Valor']}</td>"
                    f"</tr>"
                )
            
            html_table = f"""
            <style>
                .modern-table-container {{
                    font-size: 18px;
                    width: 85%;
                    margin: 0 auto;
                }}
                .modern-table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    border-radius: 12px;
                    overflow: hidden;
                    background-color: #FFFFFF;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.05);
                }}
                .modern-table thead tr {{
                    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
                }}
                .modern-table th {{
                    text-align: left;
                    padding: 14px;
                    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
                    border-bottom: 3px solid #c8e6c9;
                    color: #2c3e50;
                    font-size: 18px;
                    font-weight: 600;
                    letter-spacing: 0.3px;
                }}
                .modern-table th:first-child,
                .modern-table td:first-child {{
                    width: 75%;
                    white-space: nowrap;
                }}
                .modern-table th:last-child,
                .modern-table td:last-child {{
                    text-align: center;
                    width: 25%;
                }}
                .modern-table tbody tr {{
                    transition: all 0.2s ease;
                }}
                .modern-table tbody tr:hover {{
                    background-color: #f0f7f2 !important;
                    transform: scale(1.01);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                }}
                .modern-table tbody td {{
                    padding: 12px 14px;
                    border-bottom: 1px solid #e0e0e0;
                    color: #2c3e50;
                    font-size: 18px;
                }}
                .modern-table tbody tr:last-child td {{
                    border-bottom: none;
                }}
            </style>
            <div class="modern-table-container">
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>Armadilhas</th>
                            <th>Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(linhas_tbody)}
                    </tbody>
                </table>
            </div>
            """
            
            # Exibe a tabela HTML
            st.markdown(html_table, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao criar tabela: {str(e)}")

def exibir_ranking_armadilhas(cursor, user_id):
    """
    Exibe o ranking das armadilhas ordenado por valor (do maior para o menor).
    Busca os dados da primeira tabela do tipo 'tabela' encontrada.
    Retorna as 3 primeiras armadilhas do ranking.
    """
    try:
        tabela_escolhida = st.session_state.tabela_escolhida
        
        # Buscar a primeira tabela do tipo 'tabela'
        cursor.execute(f"""
            SELECT name_element, type_element, math_element, msg_element,
                   value_element, select_element, str_element, e_col, e_row,
                   section, user_id
            FROM {tabela_escolhida}
            WHERE type_element = 'tabela'
            AND user_id = ?
            ORDER BY e_row, e_col
            LIMIT 1
        """, (user_id,))
        
        tabela_element = cursor.fetchone()
        
        if not tabela_element:
            # Se não encontrou tabela, não exibe nada
            return None
        
        # Extrai informações do elemento
        select = tabela_element[5]      # select_element (type_names separados por |)
        rotulos = tabela_element[6]    # str_element (rótulos separados por |)
        
        if not select or not rotulos:
            return None
        
        # Separa os type_names e rótulos
        type_names = select.split('|')
        rotulos_list = rotulos.split('|')
        
        # Valida se quantidade de rótulos corresponde aos type_names
        if len(type_names) != len(rotulos_list):
            return None
        
        # Lista para armazenar os dados (indicador, valor numérico, valor formatado)
        dados_armadilhas = []
        
        # Busca os valores para cada type_name
        for i, type_name in enumerate(type_names):
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela_escolhida}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor_numerico = float(result[0]) if result and result[0] is not None else 0.0
            valor_formatado = format_br_integer(result[0]) if result and result[0] is not None else '0'
            
            # Classificar risco da armadilha
            faixa_risco, sufixo, cor = classificar_risco_armadilha(valor_numerico)
            
            dados_armadilhas.append({
                'Armadilhas': rotulos_list[i].strip(),
                'Valor_Numerico': valor_numerico,
                'Valor': valor_formatado,
                'Nivel_Risco': faixa_risco
            })
        
        # Criar DataFrame e ordenar por valor numérico (decrescente)
        df = pd.DataFrame(dados_armadilhas)
        df_ordenado = df.sort_values('Valor_Numerico', ascending=False)
        
        # Remover colunas auxiliares para exibição, mantendo apenas Armadilhas e Nivel_Risco
        df_exibicao = df_ordenado.drop(['Valor_Numerico', 'Valor'], axis=1)
        
        # Exibir título e tabela
        st.markdown("")
        st.markdown("")
        st.markdown("### 🏆 Ranking das Armadilhas - TOP 3")
        
        # Criar três colunas, usando a do meio para a tabela
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col2:
            # Criar HTML da tabela com estilos modernos e profissionais
            # Gerar linhas do corpo com hover effect e cores alternadas
            linhas_tbody = []
            for idx, (_, row) in enumerate(df_exibicao.iterrows()):
                bg_color = '#ffffff' if idx % 2 == 0 else '#f8f9fa'
                linhas_tbody.append(
                    f"<tr style='background-color: {bg_color}; transition: all 0.2s ease;'>"
                    f"<td style='padding: 12px 14px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-size: 18px;'>{row['Armadilhas']}</td>"
                    f"<td style='text-align: center; padding: 12px 14px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-size: 18px; font-weight: 600;'>{row['Nivel_Risco']}</td>"
                    f"</tr>"
                )
            
            html_table = f"""
            <style>
                .modern-table-container {{
                    font-size: 18px;
                    width: 85%;
                    margin: 0 auto;
                }}
                .modern-table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    border-radius: 12px;
                    overflow: hidden;
                    background-color: #FFFFFF;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.05);
                }}
                .modern-table thead tr {{
                    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
                }}
                .modern-table th {{
                    text-align: left;
                    padding: 14px;
                    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
                    border-bottom: 3px solid #c8e6c9;
                    color: #2c3e50;
                    font-size: 18px;
                    font-weight: 600;
                    letter-spacing: 0.3px;
                }}
                .modern-table th:first-child,
                .modern-table td:first-child {{
                    width: 75%;
                    white-space: nowrap;
                }}
                .modern-table th:last-child,
                .modern-table td:last-child {{
                    text-align: center;
                    width: 25%;
                }}
                .modern-table tbody tr {{
                    transition: all 0.2s ease;
                }}
                .modern-table tbody tr:hover {{
                    background-color: #f0f7f2 !important;
                    transform: scale(1.01);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                }}
                .modern-table tbody td {{
                    padding: 12px 14px;
                    border-bottom: 1px solid #e0e0e0;
                    color: #2c3e50;
                    font-size: 18px;
                }}
                .modern-table tbody tr:last-child td {{
                    border-bottom: none;
                }}
            </style>
            <div class="modern-table-container">
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>Armadilhas</th>
                            <th>Risco</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(linhas_tbody)}
                    </tbody>
                </table>
            </div>
            """
            
            # Exibe a tabela HTML
            st.markdown(html_table, unsafe_allow_html=True)
        
        # Obter valores e classificações das armadilhas
        valores_armadilhas = obter_valores_armadilhas(cursor, user_id, tabela_escolhida)
        
        # Retornar as 3 primeiras armadilhas do ranking com informações completas
        top_3_df = df_ordenado.head(3)
        top_3_nomes = top_3_df['Armadilhas'].tolist()
        
        if len(top_3_nomes) < 3:
            return None
        
        # Construir dicionário de retorno com informações completas
        resultado = {
            'armadilhas': top_3_nomes,
            'valores': {},
            'classificacoes': {},
            'sufixos': {}
        }
        
        for nome in top_3_nomes:
            if nome in valores_armadilhas:
                resultado['valores'][nome] = valores_armadilhas[nome]['valor']
                resultado['classificacoes'][nome] = valores_armadilhas[nome]['classificacao']
                resultado['sufixos'][nome] = valores_armadilhas[nome]['sufixo']
            else:
                # Fallback se não encontrar na função obter_valores_armadilhas
                # Buscar valor do DataFrame
                valor = top_3_df[top_3_df['Armadilhas'] == nome]['Valor_Numerico'].iloc[0]
                faixa, sufixo, cor = classificar_risco_armadilha(valor)
                resultado['valores'][nome] = valor
                resultado['classificacoes'][nome] = faixa
                resultado['sufixos'][nome] = sufixo
        
        return resultado
            
    except Exception as e:
        # Se houver erro, não exibe nada (não quebra o fluxo)
        return None

def obter_dados_ranking_pdf(cursor, user_id, tabela_escolhida):
    """
    Obtém os dados do ranking das armadilhas ordenados para uso no PDF.
    Retorna lista de tuplas (armadilha, nivel_risco) ordenadas por valor decrescente.
    """
    try:
        # Buscar a primeira tabela do tipo 'tabela'
        cursor.execute(f"""
            SELECT select_element, str_element
            FROM {tabela_escolhida}
            WHERE type_element = 'tabela'
            AND user_id = ?
            ORDER BY e_row, e_col
            LIMIT 1
        """, (user_id,))
        
        tabela_element = cursor.fetchone()
        
        if not tabela_element:
            return None
        
        select = tabela_element[0]      # select_element
        rotulos = tabela_element[1]    # str_element
        
        if not select or not rotulos:
            return None
        
        type_names = select.split('|')
        rotulos_list = rotulos.split('|')
        
        if len(type_names) != len(rotulos_list):
            return None
        
        # Lista para armazenar os dados
        dados_armadilhas = []
        
        for i, type_name in enumerate(type_names):
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela_escolhida}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor_numerico = float(result[0]) if result and result[0] is not None else 0.0
            
            # Classificar risco da armadilha
            faixa_risco, sufixo, cor = classificar_risco_armadilha(valor_numerico)
            
            dados_armadilhas.append({
                'Armadilhas': rotulos_list[i].strip(),
                'Valor_Numerico': valor_numerico,
                'Nivel_Risco': faixa_risco
            })
        
        # Ordenar por valor numérico (decrescente)
        df = pd.DataFrame(dados_armadilhas)
        df_ordenado = df.sort_values('Valor_Numerico', ascending=False)
        
        # Retornar lista de tuplas (armadilha, nivel_risco)
        return [(row['Armadilhas'], row['Nivel_Risco']) for _, row in df_ordenado.iterrows()]
        
    except Exception as e:
        return None

def obter_top_3_armadilhas_pdf(cursor, user_id, tabela_escolhida):
    """
    Obtém as 3 primeiras armadilhas do ranking para uso no PDF.
    Similar à função exibir_ranking_armadilhas mas retorna apenas os dados.
    """
    try:
        # Buscar a primeira tabela do tipo 'tabela'
        cursor.execute(f"""
            SELECT select_element, str_element
            FROM {tabela_escolhida}
            WHERE type_element = 'tabela'
            AND user_id = ?
            ORDER BY e_row, e_col
            LIMIT 1
        """, (user_id,))
        
        tabela_element = cursor.fetchone()
        
        if not tabela_element:
            return None
        
        select = tabela_element[0]      # select_element
        rotulos = tabela_element[1]    # str_element
        
        if not select or not rotulos:
            return None
        
        type_names = select.split('|')
        rotulos_list = rotulos.split('|')
        
        if len(type_names) != len(rotulos_list):
            return None
        
        # Lista para armazenar os dados
        dados_armadilhas = []
        
        for i, type_name in enumerate(type_names):
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela_escolhida}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor_numerico = float(result[0]) if result and result[0] is not None else 0.0
            faixa, sufixo, cor = classificar_risco_armadilha(valor_numerico)
            
            dados_armadilhas.append({
                'Armadilhas': rotulos_list[i].strip(),
                'Valor_Numerico': valor_numerico,
                'Sufixo': sufixo
            })
        
        # Ordenar e pegar as 3 primeiras
        df = pd.DataFrame(dados_armadilhas)
        df_ordenado = df.sort_values('Valor_Numerico', ascending=False)
        top_3_df = df_ordenado.head(3)
        
        if len(top_3_df) < 3:
            return None
        
        # Retornar dicionário com nomes e sufixos das 3 primeiras armadilhas
        resultado = {
            'armadilhas': top_3_df['Armadilhas'].tolist(),
            'sufixos': {row['Armadilhas']: row['Sufixo'] for _, row in top_3_df.iterrows()}
        }
        return resultado
        
    except Exception as e:
        return None

def processar_markdown_para_pdf(conteudo_markdown):
    """
    Processa conteúdo markdown e retorna lista de parágrafos para o PDF.
    Remove tags HTML, normaliza quebras de linha, etc.
    """
    try:
        # Remove tags HTML
        texto_limpo = re.sub(r'<[^>]+>', '', conteudo_markdown)
        # Converte quebras de linha markdown para quebras normais
        texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
        # NÃO remover emojis - preservar para o PDF
        texto_limpo = texto_limpo.strip()
        
        # Dividir em parágrafos
        paragrafos = [p.strip() for p in texto_limpo.split('\n\n') if p.strip() and len(p.strip()) > 5]
        
        return paragrafos
    except Exception as e:
        return [conteudo_markdown]  # Retorna o conteúdo original em caso de erro

def processar_e_adicionar_markdown_pdf(conteudo_markdown, elements, estilo_paragrafo, estilo_titulo):
    """
    Processa conteúdo markdown e adiciona diretamente aos elements do PDF,
    identificando títulos (##) e aplicando estilos apropriados.
    Preserva formatação markdown (negrito, itálico) convertendo para HTML do ReportLab.
    """
    try:
        # NÃO remover tags HTML primeiro - vamos processar markdown diretamente
        # Apenas normalizar quebras de linha
        texto_limpo = re.sub(r'\n{3,}', '\n\n', conteudo_markdown)
        texto_limpo = texto_limpo.strip()
        
        # Função auxiliar para processar itálico sem interferir com negrito
        def processar_italico_sem_negrito(texto):
            """Processa itálico (*texto*) sem interferir com tags <b> já criadas"""
            partes = re.split(r'(<b>.*?</b>)', texto)
            resultado = []
            for parte in partes:
                if parte.startswith('<b>') and parte.endswith('</b>'):
                    resultado.append(parte)
                else:
                    parte_processada = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', parte)
                    resultado.append(parte_processada)
            return ''.join(resultado)
        
        # Dividir em linhas para processar
        linhas = texto_limpo.split('\n')
        
        for linha in linhas:
            linha_original = linha
            linha = linha.strip()
            if not linha:
                elements.append(Spacer(1, 4))  # Espaço para linhas vazias
                continue
            
            # Verificar se é um título markdown (###, ##, #)
            if linha.startswith('###'):
                # Título nível 3
                titulo_limpo = re.sub(r'^###+\s*', '', linha).strip()
                # Converter **texto** para <b>texto</b> (preservar negrito)
                titulo_limpo = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', titulo_limpo)
                # Converter *texto* para <i>texto</i> (itálico) apenas se não for parte de **
                titulo_limpo = processar_italico_sem_negrito(titulo_limpo)
                if titulo_limpo:
                    elements.append(Paragraph(titulo_limpo, estilo_titulo))
                    elements.append(Spacer(1, 8))
            elif linha.startswith('##'):
                # Título nível 2
                titulo_limpo = re.sub(r'^##+\s*', '', linha).strip()
                # Converter **texto** para <b>texto</b> (preservar negrito)
                titulo_limpo = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', titulo_limpo)
                # Converter *texto* para <i>texto</i> (itálico) apenas se não for parte de **
                titulo_limpo = processar_italico_sem_negrito(titulo_limpo)
                if titulo_limpo:
                    elements.append(Paragraph(titulo_limpo, estilo_titulo))
                    elements.append(Spacer(1, 8))
            elif linha.startswith('#'):
                # Título nível 1
                titulo_limpo = re.sub(r'^#+\s*', '', linha).strip()
                # Converter **texto** para <b>texto</b> (preservar negrito)
                titulo_limpo = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', titulo_limpo)
                # Converter *texto* para <i>texto</i> (itálico) apenas se não for parte de **
                titulo_limpo = processar_italico_sem_negrito(titulo_limpo)
                if titulo_limpo:
                    elements.append(Paragraph(titulo_limpo, estilo_titulo))
                    elements.append(Spacer(1, 8))
            else:
                # É um parágrafo normal ou item de lista
                linha_processada = linha
                
                # Processar item de lista (começa com * ou -)
                if linha.startswith('* ') or linha.startswith('- '):
                    # Remover o marcador de lista, mas manter o espaço
                    linha_processada = re.sub(r'^[\*\-\+]\s+', '', linha_processada)
                
                # Converter **texto** para <b>texto</b> (negrito)
                # Usar substituição global para pegar todos os casos
                linha_processada = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', linha_processada)
                
                # Converter *texto* para <i>texto</i> (itálico) apenas se não for parte de **
                # Usar a função auxiliar já definida
                linha_processada = processar_italico_sem_negrito(linha_processada)
                
                # NÃO remover nenhum caractere - deixar o ReportLab processar
                # O ReportLab Paragraph aceita caracteres Unicode, então não precisa limpar
                
                if linha_processada.strip():
                    # Limitar tamanho do parágrafo
                    if len(linha_processada) > 800:
                        # Dividir parágrafos muito longos
                        frases = re.split(r'([.!?]\s+)', linha_processada)
                        frase_atual = ''
                        for parte in frases:
                            frase_atual += parte
                            if parte.strip().endswith(('.', '!', '?')):
                                if frase_atual.strip():
                                    elements.append(Paragraph(frase_atual.strip(), estilo_paragrafo))
                                    elements.append(Spacer(1, 4))
                                frase_atual = ''
                        if frase_atual.strip():
                            elements.append(Paragraph(frase_atual.strip(), estilo_paragrafo))
                            elements.append(Spacer(1, 4))
                    else:
                        elements.append(Paragraph(linha_processada.strip(), estilo_paragrafo))
                        elements.append(Spacer(1, 6))
    except Exception as e:
        # Em caso de erro, adiciona o conteúdo original processado de forma simples
        try:
            conteudo_simples = re.sub(r'\*\*([^*]+)\*\*', r'\1', conteudo_markdown[:500])
            elements.append(Paragraph(conteudo_simples, estilo_paragrafo))
        except:
            elements.append(Paragraph("Erro ao processar conteúdo", estilo_paragrafo))

def classificar_risco_armadilha(valor):
    """
    Classifica o risco de uma armadilha baseado no valor.
    
    Args:
        valor: Valor numérico da armadilha (0-6)
        
    Returns:
        tuple: (faixa_risco, sufixo_arquivo, cor)
    """
    if valor <= 1:
        return ("Baixo Risco", "_1", "#2E8B57")
    elif valor <= 3:
        return ("Atenção", "_2", "#DAA520")
    elif valor <= 5:
        return ("Alto Risco", "_3", "#FF8C00")
    else:  # valor == 6
        return ("Crítico", "_4", "#B22222")

def obter_valores_armadilhas(cursor, user_id, tabela_escolhida):
    """
    Obtém os valores das 7 armadilhas (M801-M807) e suas classificações.
    
    Args:
        cursor: Cursor do banco de dados
        user_id: ID do usuário
        tabela_escolhida: Nome da tabela a ser consultada
        
    Returns:
        dict: {nome_armadilha: {'valor': float, 'classificacao': str, 'sufixo': str, 'cor': str}}
    """
    # Mapeamento M80X -> nome armadilha
    mapeamento_m80x = {
        'M801': 'Sobrecarga e Solidão',
        'M802': 'Vida Pessoal x Profissional',
        'M803': 'Sem Backup / Falta de Sucessão',
        'M804': 'Crescimento no Improviso',
        'M805': 'Dependência Total do Dono',
        'M806': 'Dificuldade em Delegar e Formar Parcerias',
        'M807': 'Sem Tempo para o Futuro'
    }
    
    valores_armadilhas = {}
    for m80x, nome in mapeamento_m80x.items():
        cursor.execute(f"""
            SELECT value_element
            FROM {tabela_escolhida}
            WHERE user_id = ? AND str_element = ?
            LIMIT 1
        """, (user_id, m80x))
        result = cursor.fetchone()
        valor = float(result[0]) if result and result[0] is not None else 0.0
        faixa, sufixo, cor = classificar_risco_armadilha(valor)
        
        valores_armadilhas[nome] = {
            'valor': valor,
            'classificacao': faixa,
            'sufixo': sufixo,
            'cor': cor
        }
    
    return valores_armadilhas

def mapear_armadilha_para_arquivo(nome_armadilha, sufixo_risco=""):
    """
    Mapeia o nome do rótulo da armadilha para o arquivo .md correspondente.
    
    Args:
        nome_armadilha: Nome do rótulo da armadilha (ex: "Sobrecarga e Solidão")
        sufixo_risco: Sufixo baseado na classificação (_1, _2, _3, _4)
        
    Returns:
        str: Nome do arquivo .md correspondente com sufixo ou None se não encontrar
    """
    # Normalizar o nome (remover acentos, converter para minúsculas, remover espaços extras)
    nome_normalizado = nome_armadilha.lower().strip()
    
    # Mapeamento baseado em palavras-chave (estrutura fatorada: arquivo -> lista de palavras-chave)
    mapeamento_armadilhas = {
        '01_Sobrecarga_Solidao.md': ['sobrecarga', 'solidao'],
        '02_Pessoal_Profissional.md': ['pessoal', 'profissional'],
        '03_Backup_Sucessao.md': ['backup', 'sucessao'],
        '04_Crescimento_Improviso.md': ['crescimento', 'improviso'],
        '05_Dependencia_Dono.md': ['dependencia', 'dono'],
        '06_Dificuldade_parceiros.md': ['dificuldade', 'parceiros'],
        '07_Falta_Tempo.md': ['tempo', 'falta']
    }
    
    # Buscar correspondência por palavra-chave
    for arquivo, palavras_chave in mapeamento_armadilhas.items():
        if any(palavra in nome_normalizado for palavra in palavras_chave):
            # Adicionar sufixo se fornecido
            if sufixo_risco:
                return arquivo.replace('.md', f'{sufixo_risco}.md')
            return arquivo
    
    return None

def exibir_relatorio_detalhado_armadilhas(top_3_dados):
    """
    Exibe o relatório detalhado das 3 primeiras armadilhas.
    
    Args:
        top_3_dados: Dicionário com informações das top 3 armadilhas:
            - 'armadilhas': lista de nomes
            - 'sufixos': dicionário {nome: sufixo}
    """
    try:
        import os
        
        # Verificar se é o formato antigo (lista) ou novo (dicionário)
        if isinstance(top_3_dados, list):
            # Compatibilidade com formato antigo
            top_3_nomes = top_3_dados
            sufixos = {}
        else:
            # Novo formato
            top_3_nomes = top_3_dados.get('armadilhas', [])
            sufixos = top_3_dados.get('sufixos', {})
        
        if not top_3_nomes or len(top_3_nomes) < 3:
            return
        
        # Armazenar as 3 armadilhas nas variáveis
        armadilha01 = top_3_nomes[0]
        armadilha02 = top_3_nomes[1] if len(top_3_nomes) > 1 else None
        armadilha03 = top_3_nomes[2] if len(top_3_nomes) > 2 else None
        
        # Obter caminho da pasta Conteudo/04
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pasta_conteudo = os.path.join(current_dir, "Conteudo", "04")
        
        # Renderizar arquivos das 3 armadilhas
        armadilhas_selecionadas = [
            ("1ª", armadilha01),
            ("2ª", armadilha02),
            ("3ª", armadilha03)
        ]
        
        for posicao, nome_armadilha in armadilhas_selecionadas:
            if nome_armadilha:
                # Obter sufixo se disponível
                sufixo = sufixos.get(nome_armadilha, "")
                arquivo_armadilha = mapear_armadilha_para_arquivo(nome_armadilha, sufixo)
                
                if arquivo_armadilha:
                    caminho_arquivo = os.path.join(pasta_conteudo, arquivo_armadilha)
                    
                    if os.path.exists(caminho_arquivo):
                        st.markdown("---")
                        with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                            conteudo_armadilha = file.read()
                        st.markdown(conteudo_armadilha)
                    else:
                        # Fallback: tentar arquivo sem sufixo
                        arquivo_base = mapear_armadilha_para_arquivo(nome_armadilha, "")
                        if arquivo_base:
                            caminho_base = os.path.join(pasta_conteudo, arquivo_base)
                            if os.path.exists(caminho_base):
                                st.markdown("---")
                                with open(caminho_base, 'r', encoding='utf-8') as file:
                                    conteudo_armadilha = file.read()
                                st.markdown(conteudo_armadilha)
                            else:
                                st.warning(f"Arquivo não encontrado: {arquivo_armadilha} (Armadilha: {nome_armadilha})")
                        else:
                            st.warning(f"Arquivo não encontrado: {arquivo_armadilha} (Armadilha: {nome_armadilha})")
                else:
                    st.warning(f"Não foi possível mapear a armadilha '{nome_armadilha}' para um arquivo .md")
        
    except Exception as e:
        st.error(f"Erro ao exibir relatório detalhado: {str(e)}")
        import traceback
        st.error(f"Detalhes: {traceback.format_exc()}")

def analisar_vulnerabilidade_7armadilhas_streamlit(cursor, user_id):
    """
    Gera análise de vulnerabilidade das 7 Armadilhas do Eu Empresário na interface Streamlit.
    FUNÇÃO REFATORADA - Análise por armadilha usando M801-M807.
    """
    try:
        import os
        
        # 1. Adicionar CSS global para aumentar tamanho dos textos destacados para 18px
        st.markdown("""
        <style>
            /* Aumentar tamanho dos parágrafos de texto normal (não títulos) */
            .stMarkdown p {
                font-size: 18px !important;
                line-height: 1.6 !important;
            }
            /* Aumentar tamanho dos textos em negrito */
            .stMarkdown p strong {
                font-size: 18px !important;
            }
            /* Aumentar tamanho dos textos em listas */
            .stMarkdown ul li, .stMarkdown ol li {
                font-size: 18px !important;
                line-height: 1.6 !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Análise Vulnerabilidade - 7 Armadilhas do Empresário")
        
        # 2. Inserir arquivo 00_Abertura.md (entre gráfico e ranking)
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pasta_conteudo = os.path.join(current_dir, "Conteudo", "04")
        arquivo_abertura = os.path.join(pasta_conteudo, "00_Abertura.md")
        
        if os.path.exists(arquivo_abertura):
            st.markdown("---")
            with open(arquivo_abertura, 'r', encoding='utf-8') as file:
                conteudo_abertura = file.read()
            st.markdown(conteudo_abertura)
            st.markdown("---")
        else:
            st.warning(f"Arquivo não encontrado: 00_Abertura.md")
        
        # 3. Exibir Ranking das Armadilhas e obter as 3 primeiras com classificações
        top_3_dados = exibir_ranking_armadilhas(cursor, user_id)
        
        # 4. Inserir arquivo 00_Devolutiva.md (após ranking, antes do relatório detalhado)
        if top_3_dados:
            arquivo_devolutiva = os.path.join(pasta_conteudo, "00_Devolutiva.md")
            
            if os.path.exists(arquivo_devolutiva):
                st.markdown("---")
                with open(arquivo_devolutiva, 'r', encoding='utf-8') as file:
                    conteudo_devolutiva = file.read()
                st.markdown(conteudo_devolutiva)
                st.markdown("---")
            else:
                st.warning(f"Arquivo não encontrado: 00_Devolutiva.md")
            
            # 5. Exibir Relatório Detalhado das Armadilhas (com sufixos de classificação)
            exibir_relatorio_detalhado_armadilhas(top_3_dados)
        
        # 6. Informações adicionais sobre o assessment (sem moldura)
        # Adicionar 2 linhas de espaço antes dos créditos
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.markdown("### ℹ️ Agende sua Reunião Estratégica ")
        st.markdown("Caso o diagnóstico indique áreas críticas, estou à disposição para uma conversa estratégica. Analisaremos o cenário atual e definiremos ações iniciais para fortalecer a gestão. Agende a reunião e avance com clareza e segurança. ")
        st.markdown("E-mail: erika7rossi@gmail.com - WhatsApp: (11) 99506-6778")

    except Exception as e:
        st.error(f"Erro na análise de vulnerabilidade: {str(e)}")
        import traceback
        st.error(f"Detalhes do erro: {traceback.format_exc()}")

def analisar_vulnerabilidade_7armadilhas(cursor, user_id, tabela_escolhida=None):
    """
    DEPRECATED: Esta função está obsoleta e usa a lógica antiga baseada em M3000.
    Foi substituída por analisar_vulnerabilidade_7armadilhas_streamlit que usa análise por armadilha (M801-M807).
    
    Retorna análise de vulnerabilidade das 7 Armadilhas do Eu Empresário em formato texto.
    """
    try:
        # 1. Buscar dados do usuário
        cursor.execute("""
            SELECT u.nome, u.email, u.empresa 
            FROM usuarios u 
            WHERE u.user_id = ?
        """, (user_id,))
        usuario_info = cursor.fetchone()
        
        # 2. Buscar pontuação das perguntas diretas (M3000)
        if tabela_escolhida:
            tabela = tabela_escolhida
        else:
            tabela = st.session_state.get('tabela_escolhida', 'forms_resultados_04')
        
        cursor.execute(f"""
            SELECT value_element
            FROM {tabela}
            WHERE user_id = ? AND str_element = 'M3000'
            LIMIT 1
        """, (user_id,))
        result_diretas = cursor.fetchone()
        pontuacao = float(result_diretas[0]) if result_diretas and result_diretas[0] is not None else 0.0
        
        # 3. Validação: se não encontrou dados
        if not result_diretas:
            return "Análise não disponível: dados de vulnerabilidade não encontrados."
        
        # Função deprecada - lógica de faixas de risco e arquivos markdown removida
        # Use analisar_vulnerabilidade_7armadilhas_streamlit para análise atualizada
        return "Esta função está obsoleta. Use analisar_vulnerabilidade_7armadilhas_streamlit para análise atualizada."
        
    except Exception as e:
        traceback.print_exc()
        return f"Ocorreu um erro inesperado ao gerar a análise: {str(e)}"

# Função antiga removida - substituída por analisar_vulnerabilidade_7armadilhas_streamlit

if __name__ == "__main__":
    show_results()

