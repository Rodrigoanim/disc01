# resultados.py
# Data: 01/08/2025 - 22h00
# Pagina de resultados e Analises - Dashboard.
# Tabela: forms_resultados

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
from paginas.monitor import registrar_acesso
import time

from config import DB_PATH  # Adicione esta importação

# Dicionário de títulos para cada tabela
TITULOS_TABELAS = {
    "forms_resultados": "Análise: Âncoras de Carreira"
}

# Dicionário de subtítulos para cada tabela
SUBTITULOS_TABELAS = {
    "forms_resultados": "Avaliação de Âncoras de Carreira"
}

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
    Busca dados na tabela forms_tab e atualiza o value_element do registro atual.
    
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
                FROM forms_tab 
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
                st.warning(f"Valor não encontrado na tabela forms_tab para {str_value} (user_id: {user_id})")
                
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
    
    Configurações do Gráfico:
        - Título do gráfico usando msg_element
        - Barras verticais sem hover (tooltip)
        - Altura fixa de 400px
        - Largura responsiva
        - Sem legenda e títulos dos eixos
        - Fonte tamanho 14px
        - Valores no eixo Y formatados com separador de milhar
        - Cor das barras definida pela coluna 'section'
        - Sem barra de ferramentas do Plotly
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
        
        # Sistema exclusivo para Âncoras de Carreira - Cores do prisma/espectro
        cores_ancoras = {
            'C31': '#FF0000',  # Vermelho - Competência Técnica
            'C32': '#FF8C00',  # Laranja - Gestão Geral  
            'C33': '#FFD700',  # Amarelo - Autonomia
            'C34': '#00FF00',  # Verde - Segurança
            'D31': '#0080FF',  # Azul - Criatividade
            'D32': '#4B0082',  # Índigo - Serviço
            'D33': '#8A2BE2',  # Violeta - Estilo de Vida
            'D34': '#FF1493'   # Rosa - Desafio
        }
        
        # Mapear códigos das âncoras para cores
        cores = []
        cores_prisma = ['#FF0000', '#FF8C00', '#FFD700', '#00FF00', '#0080FF', '#4B0082', '#8A2BE2', '#FF1493']
        
        for i, type_name in enumerate(type_names):
            codigo = type_name.strip()
            if codigo in cores_ancoras:
                cores.append(cores_ancoras[codigo])
            else:
                # Fallback: usar índice nas cores do prisma
                cores.append(cores_prisma[i % len(cores_prisma)])

        # Adiciona o título antes do gráfico usando markdown
        if msg:
            st.markdown(f"""
                <p style='
                    text-align: center;
                    font-size: 31px;
                    font-weight: bold;
                    color: #1E1E1E;
                    margin: 15px 0;
                    padding: 10px;
                '>{msg}</p>
            """, unsafe_allow_html=True)
        
        # Cria o gráfico usando Graph Objects para controle total das cores
        fig = go.Figure(data=[
            go.Bar(
                x=labels,
                y=valores,
                marker=dict(color=cores),  # Define cores diretamente
                showlegend=False
            )
        ])
        
        # Configura o layout do gráfico
        fig.update_layout(
            # Remove títulos dos eixos
            xaxis_title=None,
            yaxis_title=None,
            # Remove legenda
            showlegend=False,
            # Define dimensões
            height=400,
            width=None,  # largura responsiva
            # Configuração do eixo X
            xaxis=dict(
                tickfont=dict(size=16),  # mantido tamanho original para web
            ),
            # Configuração do eixo Y
            yaxis=dict(
                tickfont=dict(size=18),  # mantido tamanho original para web
                tickformat=",.",  # formato dos números
                separatethousands=True  # separador de milhar
            ),
            # Desativa o hover (tooltip ao passar o mouse)
            hovermode=False
        )
        
        # Exibe o gráfico no Streamlit com chave única para evitar conflitos de ID
        # config={'displayModeBar': False} remove a barra de ferramentas do Plotly
        name_element = element[0]  # Usa o name_element como chave única
        graph_key = f"grafico_{name_element}_{user_id}"  # Chave única baseada no elemento e usuário
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=graph_key)
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")

def tabela_dados(cursor, element):
    """
    Cria uma tabela estilizada com dados da tabela forms_resultados.
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
            cursor.execute("""
                SELECT value_element 
                FROM forms_resultados 
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = format_br_number(result[0]) if result and result[0] is not None else '0,00'
            valores.append(valor)
        
        # Criar DataFrame com os dados
        df = pd.DataFrame({
            'Indicador': rotulos,
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
            
            # Criar HTML da tabela com estilos inline
            html_table = f"""
            <div style='font-size: 20px; width: 80%;'>
                <table style='width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 0 8px rgba(0,0,0,0.1);'>
                    <thead>
                        <tr>
                            <th style='text-align: left; padding: 10px; background-color: #e8f5e9; border-bottom: 2px solid #dee2e6;'>Indicador</th>
                            <th style='text-align: right; padding: 10px; background-color: #e8f5e9; border-bottom: 2px solid #dee2e6;'>Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f"<tr><td style='padding: 8px 10px; border-bottom: 1px solid #dee2e6;'>{row['Indicador']}</td><td style='text-align: right; padding: 8px 10px; border-bottom: 1px solid #dee2e6;'>{row['Valor']}</td></tr>" for _, row in df.iterrows())}
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
            valor = format_br_number(result[1]) if result and result[1] is not None else '0,00'
            valores.append(valor)
        
        # Retornar dados formatados para a tabela
        return {
            'title': msg if msg else "Tabela de Dados",
            'data': [['Indicador', 'Valor']] + list(zip(labels, valores)),
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
        
        # Sistema exclusivo para Âncoras de Carreira - Cores do prisma/espectro
        cores_ancoras = {
            'C31': '#FF0000',  # Vermelho - Competência Técnica
            'C32': '#FF8C00',  # Laranja - Gestão Geral  
            'C33': '#FFD700',  # Amarelo - Autonomia
            'C34': '#00FF00',  # Verde - Segurança
            'D31': '#0080FF',  # Azul - Criatividade
            'D32': '#4B0082',  # Índigo - Serviço
            'D33': '#8A2BE2',  # Violeta - Estilo de Vida
            'D34': '#FF1493'   # Rosa - Desafio
        }
        
        # Mapear códigos das âncoras para cores
        cores = []
        cores_prisma = ['#FF0000', '#FF8C00', '#FFD700', '#00FF00', '#0080FF', '#4B0082', '#8A2BE2', '#FF1493']
        
        for i, type_name in enumerate(type_names):
            codigo = type_name.strip()
            if codigo in cores_ancoras:
                cores.append(cores_ancoras[codigo])
            else:
                # Fallback: usar índice nas cores do prisma
                cores.append(cores_prisma[i % len(cores_prisma)])
        # Ajustar base_width para ocupar mais da largura da página A4
        base_width = 250
        base_height = 180
        # largura dos gráficos igual à tabela (usando width_pct)
        adj_width = int(base_width * 2.2 * 0.8 * (width_pct / 100)) + 20  # aumenta 20 na largura
        adj_height = int(base_height * (height_pct / 100)) - 25           # reduz 25 na altura
        fig = go.Figure(data=[
            go.Bar(
                x=labels,
                y=valores,
                marker=dict(color=cores),  # Define cores diretamente
                showlegend=False
            )
        ])
        fig.update_layout(
            showlegend=False,
            height=int(adj_height * 1.5),  # aumentado 50% na altura
            width=adj_width,
            margin=dict(t=30, b=50),
            xaxis=dict(
                title=None,
                tickfont=dict(size=8)  # reduzido 50% (de 16 para 8)
            ),
            yaxis=dict(
                title=None,
                tickfont=dict(size=9),  # reduzido 50% (de 18 para 9)
                tickformat=",.",
                separatethousands=True
            )
        )
        img_bytes = fig.to_image(format="png", scale=3)
        return {
            'title': msg,
            'image': Image(io.BytesIO(img_bytes), 
                         width=adj_width,
                         height=adj_height)
        }
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")
        return None

def subtitulo(titulo_pagina: str):
    """
    Exibe o subtítulo da página e o botão de gerar PDF (temporariamente desabilitado)
    """
    try:
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown(f"""
                <p style='
                    text-align: Left;
                    font-size: 36px;
                    color: #000000;
                    margin-top: 10px;
                    margin-bottom: 30px;
                    font-family: sans-serif;
                    font-weight: 500;
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
                            file_name="Ancoras_de_Carreira.pdf",
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

def convert_markdown_to_html(text):
    """
    Converte markdown básico para HTML que o ReportLab pode interpretar
    Versão SIMPLIFICADA que evita HTML complexo
    """
    import re
    
    # Processar linha por linha para evitar conflitos
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        if not line.strip():
            processed_lines.append(line)
            continue
            
        processed_line = line
        
        # Processar apenas dentro da linha atual
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            # Converter para item de lista SEM HTML
            item_text = line.strip()[2:]  # Remove '- ' ou '* '
            # Remover formatações markdown mas manter texto
            item_text = re.sub(r'\*\*(.*?)\*\*', r'\1', item_text)  # Negrito → texto normal
            item_text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)', r'\1', item_text)  # Itálico → texto normal
            processed_line = f'• {item_text}'
            
        elif line.strip().startswith('> '):
            # Converter citação SEM HTML
            quote_text = line.strip()[2:]  # Remove '> '
            # Remover formatações markdown mas manter texto
            quote_text = re.sub(r'\*\*(.*?)\*\*', r'\1', quote_text)
            quote_text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)', r'\1', quote_text)
            processed_line = f'"{quote_text}"'
            
        else:
            # Linha normal - REMOVER formatações markdown ao invés de converter para HTML
            # Remover negrito **texto** → texto
            processed_line = re.sub(r'\*\*(.*?)\*\*', r'\1', processed_line)
            # Remover itálico *texto* → texto
            processed_line = re.sub(r'(?<!\*)\*(?!\*)([^*<>]+?)\*(?!\*)', r'\1', processed_line)
        
        processed_lines.append(processed_line)
    
    return '\n'.join(processed_lines)

def clean_text_for_reportlab(text):
    """
    Limpa texto para evitar problemas de encoding no ReportLab
    Versão simplificada sem HTML
    """
    # Remover ou substituir caracteres problemáticos
    replacements = {
        '\u2014': '—',  # em dash
        '\u2013': '–',  # en dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\u2026': '...',  # ellipsis
        '\xa0': ' ',    # non-breaking space
        '\u00e7': 'ç',  # ç explícito
        '\u00e3': 'ã',  # ã explícito
        '\u00e1': 'á',  # á explícito
        '\u00e9': 'é',  # é explícito
        '\u00ed': 'í',  # í explícito
        '\u00f3': 'ó',  # ó explícito
        '\u00fa': 'ú',  # ú explícito
        '\u00e2': 'â',  # â explícito
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Remover qualquer tag HTML residual
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()

def split_long_paragraph(text, max_length=2000):
    """
    Divide parágrafos muito longos em partes menores, respeitando pontuação
    """
    if len(text) <= max_length:
        return [text]
    
    # Tentar quebrar em frases (por ponto final + espaço)
    sentences = []
    current = ""
    
    # Dividir por pontos finais, mas manter pontos em abreviações
    parts = text.split('. ')
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            part += '.'
        
        if len(current + part) <= max_length:
            current += part + " " if i < len(parts) - 1 else part
        else:
            if current:
                sentences.append(current.strip())
            current = part + " " if i < len(parts) - 1 else part
    
    if current:
        sentences.append(current.strip())
    
    return sentences

def generate_pdf_content(cursor, user_id: int, tabela_escolhida: str):
    """
    Função para gerar PDF com layout específico: 
                    Tabela Âncoras P1 → Gráfico Âncoras P1 → Tabela Âncoras P2 → Gráfico Âncoras P2
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
            rightMargin=36,
            leftMargin=36,
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
                fontSize=26,
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=26,
                spaceBefore=15,
                spaceAfter=20
            )
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
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
                fontSize=18,
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=16,
                spaceBefore=6,
                spaceAfter=8
            )

            # Título principal
            titulo_principal = TITULOS_TABELAS.get(tabela_escolhida, "Análise de Âncoras de Carreira")
            elements.append(Paragraph(titulo_principal, title_style))
            elements.append(Spacer(1, 20))

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

            # GERAR RANKING UNIFICADO DAS ÂNCORAS (como na versão da tela)
            
            # Buscar dados das âncoras para o ranking (códigos corretos)
            mapeamento_ancoras_pdf = {
                'C31': {'nome': 'Competência Técnica / Funcional', 'descricao': 'Desenvolvimento de expertise técnica e especialização profissional', 'arquivo': 'Conteudo/A1_Competencia_Tecnica.md'},
                'C32': {'nome': 'Gestão Geral', 'descricao': 'Liderança, coordenação e responsabilidade gerencial', 'arquivo': 'Conteudo/A2_Gestao_Geral.md'},
                'C33': {'nome': 'Autonomia / Independência', 'descricao': 'Liberdade para tomar decisões e trabalhar independentemente', 'arquivo': 'Conteudo/A3_Autonomia_Independencia.md'},
                'C34': {'nome': 'Segurança / Estabilidade', 'descricao': 'Estabilidade financeira e segurança no emprego', 'arquivo': 'Conteudo/A4_Seguranca_Estabilidade.md'},
                'D31': {'nome': 'Criatividade Empreendedora', 'descricao': 'Inovação, criação de novos produtos e empreendedorismo', 'arquivo': 'Conteudo/A5_Criatividade_Empreendedora.md'},
                'D32': {'nome': 'Serviço / Dedicação', 'descricao': 'Contribuição para a sociedade e ajuda aos outros', 'arquivo': 'Conteudo/A6_Servico_Dedicacao.md'},
                'D33': {'nome': 'Estilo de Vida', 'descricao': 'Equilíbrio entre vida pessoal e profissional', 'arquivo': 'Conteudo/A7_Estilo_Vida.md'},
                'D34': {'nome': 'Desafio Puro', 'descricao': 'Busca por desafios complexos e competição', 'arquivo': 'Conteudo/A8_Desafio_Puro.md'}
            }
            
            # Calcular ranking das âncoras
            ranking_ancoras_pdf = []
            for codigo in mapeamento_ancoras_pdf.keys():
                # Usar mesma lógica da função da tela que funciona
                pdf_cursor.execute("""
                    SELECT value_element 
                    FROM forms_resultados 
                    WHERE name_element = ? 
                    AND user_id = ?
                    ORDER BY ID_element DESC
                    LIMIT 1
                """, (codigo.strip(), user_id))
                
                result = pdf_cursor.fetchone()
                valor_total = parse_br_number(result[0]) if result and result[0] is not None else 0.0
                
                ranking_ancoras_pdf.append({
                    'codigo': codigo,
                    'nome': mapeamento_ancoras_pdf[codigo]['nome'],
                    'valor_total': valor_total,
                    'descricao': mapeamento_ancoras_pdf[codigo]['descricao'],
                    'arquivo': mapeamento_ancoras_pdf[codigo]['arquivo']
                })
            
            # Ordenar ranking
            ranking_ancoras_pdf.sort(key=lambda x: x['valor_total'], reverse=True)
            
            # Verificar se há dados suficientes
            valores_validos_pdf = [a for a in ranking_ancoras_pdf if a['valor_total'] > 0]
            if len(valores_validos_pdf) >= 3:
                # 1. TABELA RANKING UNIFICADO DAS ÂNCORAS
                elements.append(Paragraph("RANKING COMPLETO DAS ÂNCORAS DE CARREIRA", graphic_title_style))
                elements.append(Spacer(1, 5))
                
                # Criar dados da tabela de ranking
                dados_ranking_pdf = [['Posição', 'Âncora de Carreira', 'Valor Total', 'Descrição']]
                for i, ancora in enumerate(ranking_ancoras_pdf):
                    posicao = f"{i+1}º"
                    valor_total_br = f"{ancora['valor_total']:.1f}".replace('.', ',')
                    # Quebrar descrição longa para melhor formatação
                    descricao = ancora['descricao']
                    if len(descricao) > 60:
                        palavras = descricao.split(' ')
                        if len(palavras) > 8:
                            meio = len(palavras) // 2
                            descricao = ' '.join(palavras[:meio]) + '<br/>' + ' '.join(palavras[meio:])
                    
                    dados_ranking_pdf.append([
                        posicao,
                        ancora['nome'],
                        valor_total_br,
                        Paragraph(descricao, styles['Normal'])
                    ])
                
                # Estilo específico para tabela de ranking
                ranking_table_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Posição centralizada
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # Nome à esquerda
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Valor centralizado
                    ('ALIGN', (3, 0), (3, -1), 'LEFT'),    # Descrição à esquerda
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),   # Alinhamento vertical no topo
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 2, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
                ])
                
                # Ajustar larguras das colunas para melhor distribuição
                col_widths = [50, 140, 60, 200]  # Larguras fixas em pontos
                t_ranking = Table(dados_ranking_pdf, colWidths=col_widths)
                t_ranking.setStyle(ranking_table_style)
                
                # Adicionar tabela diretamente (sem wrapper)
                elements.append(t_ranking)
                elements.append(Spacer(1, 10))

                # 2. GRÁFICO DE BARRAS DO RANKING
                elements.append(Paragraph("GRÁFICO DO RANKING DAS ÂNCORAS", graphic_title_style))
                elements.append(Spacer(1, 5))
                
                # Preparar dados para o gráfico de barras
                labels_grafico = [ancora['nome'] for ancora in ranking_ancoras_pdf]
                valores_grafico = [ancora['valor_total'] for ancora in ranking_ancoras_pdf]
                
                # Cores do prisma/espectro para as 8 âncoras (mesmo padrão da tela)
                cores_ancoras_grafico = {
                    'C31': '#FF0000',  # Vermelho - Competência Técnica
                    'C32': '#FF8C00',  # Laranja - Gestão Geral  
                    'C33': '#FFD700',  # Amarelo - Autonomia
                    'C34': '#00FF00',  # Verde - Segurança
                    'D31': '#0080FF',  # Azul - Criatividade
                    'D32': '#4B0082',  # Índigo - Serviço
                    'D33': '#8A2BE2',  # Violeta - Estilo de Vida
                    'D34': '#FF1493'   # Rosa - Desafio
                }
                
                # Mapear cores por código
                cores_grafico = []
                for ancora in ranking_ancoras_pdf:
                    codigo = ancora['codigo']
                    if codigo in cores_ancoras_grafico:
                        cores_grafico.append(cores_ancoras_grafico[codigo])
                    else:
                        cores_grafico.append('#1f77b4')  # Cor padrão
                
                # Criar gráfico usando Plotly
                fig = go.Figure(data=[
                    go.Bar(
                        x=labels_grafico,
                        y=valores_grafico,
                        marker=dict(color=cores_grafico),
                        showlegend=False
                    )
                ])
                
                # Configurar layout do gráfico (reduzido para caber na página)
                fig.update_layout(
                    showlegend=False,
                    height=280,
                    width=450,
                    margin=dict(t=15, b=90, l=50, r=15),  # Aumentar margem inferior para textos
                    xaxis=dict(
                        title=None,
                        tickfont=dict(size=8),
                        tickangle=-45,  # Rotacionar rótulos para melhor legibilidade
                        tickmode='array',
                        tickvals=list(range(len(labels_grafico))),
                        ticktext=[label[:20] + '...' if len(label) > 20 else label for label in labels_grafico]  # Truncar nomes longos
                    ),
                    yaxis=dict(
                        title="Pontuação",
                        title_font=dict(size=10),
                        tickfont=dict(size=9),
                        tickformat=",.",
                        separatethousands=True
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                
                # Converter para imagem e adicionar ao PDF
                img_bytes = fig.to_image(format="png", scale=2)
                img = Image(io.BytesIO(img_bytes), width=450, height=280)
                elements.append(Table([[img]], colWidths=[450], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                elements.append(Spacer(1, 15))
                
            else:
                elements.append(Paragraph("Dados insuficientes para gerar ranking das âncoras", styles['Normal']))
                elements.append(Spacer(1, 20))

            # Adicionar análise textual das âncoras (A0_Abertura + Top 3)
            elements.append(PageBreak())
            elements.append(Paragraph("ANÁLISE DAS ÂNCORAS DE CARREIRA", title_style))
            elements.append(Spacer(1, 20))
            
            # Usar o ranking já calculado acima
            top_3 = ranking_ancoras_pdf[:3]
            
            # Verificar se há dados suficientes (reutilizar validação anterior)
            if len(valores_validos_pdf) >= 3:
                
                # 1. SEÇÃO "SUAS 3 ÂNCORAS PRINCIPAIS" (concentrada na página 2)
                elements.append(Paragraph("SUAS 3 ÂNCORAS PRINCIPAIS", graphic_title_style))
                elements.append(Spacer(1, 10))
                
                # Criar caixa em destaque com as top 3
                top3_dados = [
                    ['🏆 Suas Âncoras Mais Fortes:'],
                    [f'🥇 1º Lugar: {top_3[0]["nome"]} - {top_3[0]["valor_total"]:.1f} pontos'],
                    [f'🥈 2º Lugar: {top_3[1]["nome"]} - {top_3[1]["valor_total"]:.1f} pontos'],
                    [f'🥉 3º Lugar: {top_3[2]["nome"]} - {top_3[2]["valor_total"]:.1f} pontos']
                ]
                
                # Estilo da caixa destacada
                top3_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e8')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#155724')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#28a745')),
                    ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#28a745')),
                ])
                
                top3_table = Table(top3_dados, colWidths=[450])
                top3_table.setStyle(top3_style)
                elements.append(top3_table)
                elements.append(Spacer(1, 15))
                
                # 2. SEÇÃO "ÂNCORA DOMINANTE" (igual da tela)
                ancora_principal = top_3[0]
                segunda_ancora = top_3[1]
                terceira_ancora = top_3[2]
                
                # Calcular diferenças absolutas
                diferenca_1_2 = ancora_principal['valor_total'] - segunda_ancora['valor_total']
                diferenca_1_3 = ancora_principal['valor_total'] - terceira_ancora['valor_total']
                diferenca_2_3 = segunda_ancora['valor_total'] - terceira_ancora['valor_total']
                
                # Calcular diferenças percentuais
                perc_1_2 = (diferenca_1_2 / segunda_ancora['valor_total'] * 100) if segunda_ancora['valor_total'] > 0 else 0
                perc_1_3 = (diferenca_1_3 / terceira_ancora['valor_total'] * 100) if terceira_ancora['valor_total'] > 0 else 0
                
                # Determinar tipo de perfil conforme Analise Tipo de Perfil.md
                if ((diferenca_1_2 >= 20 or perc_1_2 >= 25) and 
                    (diferenca_1_3 >= 20 or perc_1_3 >= 25)):
                    tipo_perfil = "DOMINANTE"
                    criterio = f"1ª âncora: +{diferenca_1_2:.1f}pts ({perc_1_2:.1f}%) da 2ª e +{diferenca_1_3:.1f}pts ({perc_1_3:.1f}%) da 3ª"
                elif (diferenca_1_2 <= 15 and diferenca_1_3 <= 15 and diferenca_2_3 <= 15):
                    tipo_perfil = "EQUILIBRADO"
                    criterio = f"Diferenças pequenas entre top 3: {diferenca_1_2:.1f}pts, {diferenca_1_3:.1f}pts, {diferenca_2_3:.1f}pts"
                else:
                    tipo_perfil = "MODERADAMENTE DOMINANTE"
                    criterio = f"Perfil intermediário: +{diferenca_1_2:.1f}pts da 2ª, +{diferenca_1_3:.1f}pts da 3ª"
                
                # Criar caixa "Âncora Dominante"
                elements.append(Paragraph("ÂNCORA DOMINANTE", graphic_title_style))
                elements.append(Spacer(1, 10))
                
                ancora_dominante_dados = [
                    [f'🎯 Âncora Dominante: {ancora_principal["nome"]}'],
                    [f'📊 Pontuação: {ancora_principal["valor_total"]:.1f} pontos'],
                    [f'📈 Tipo de Perfil: {tipo_perfil}'],
                    [f'📋 Critério: {criterio}']
                ]
                
                # Estilo da caixa amarela
                ancora_dominante_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#856404')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#ffc107')),
                ])
                
                ancora_dominante_table = Table(ancora_dominante_dados, colWidths=[450])
                ancora_dominante_table.setStyle(ancora_dominante_style)
                elements.append(ancora_dominante_table)
                elements.append(Spacer(1, 15))
                
                # 3. SEMPRE CARREGAR ABERTURA PRIMEIRO
                try:
                    with open('Conteudo/A0_Abertura_Devolutiva.md', 'r', encoding='utf-8') as f:
                        conteudo_abertura = f.read()
                    # Converter markdown para PDF (com formatação completa)
                    conteudo_formatado = convert_markdown_to_html(conteudo_abertura)
                    linhas_abertura = conteudo_formatado.split('\n')
                    
                    paragrafo_atual = []
                    for linha in linhas_abertura:
                        if linha.strip():  # Linha com conteúdo
                            if linha.startswith('#'):
                                # Se há parágrafo acumulado, processar primeiro
                                if paragrafo_atual:
                                    paragrafo_texto = ' '.join(paragrafo_atual)
                                    # Dividir parágrafos longos para evitar erros do ReportLab
                                    paragrafos_divididos = split_long_paragraph(paragrafo_texto)
                                    for p in paragrafos_divididos:
                                        elements.append(Paragraph(p, styles['Normal']))
                                        elements.append(Spacer(1, 3))
                                    elements.append(Spacer(1, 3))
                                    paragrafo_atual = []
                                
                                # Títulos
                                titulo_clean = linha.replace('#', '').strip()
                                if linha.startswith('###'):
                                    elements.append(Paragraph(titulo_clean, styles['Heading3']))
                                elif linha.startswith('##'):
                                    elements.append(Paragraph(titulo_clean, styles['Heading2']))
                                else:
                                    elements.append(Paragraph(titulo_clean, graphic_title_style))
                                elements.append(Spacer(1, 10))
                            elif linha.strip() == '---':
                                # Linha divisória
                                if paragrafo_atual:
                                    paragrafo_texto = ' '.join(paragrafo_atual)
                                    # Dividir parágrafos longos para evitar erros do ReportLab
                                    paragrafos_divididos = split_long_paragraph(paragrafo_texto)
                                    for p in paragrafos_divididos:
                                        elements.append(Paragraph(p, styles['Normal']))
                                        elements.append(Spacer(1, 3))
                                    elements.append(Spacer(1, 3))
                                    paragrafo_atual = []
                                elements.append(Spacer(1, 12))
                            else:
                                # Acumular linha no parágrafo atual
                                paragrafo_atual.append(linha.strip())
                        else:  # Linha vazia - indica fim do parágrafo
                            if paragrafo_atual:
                                paragrafo_texto = ' '.join(paragrafo_atual)
                                # Dividir parágrafos longos para evitar erros do ReportLab
                                paragrafos_divididos = split_long_paragraph(paragrafo_texto)
                                for p in paragrafos_divididos:
                                    elements.append(Paragraph(p, styles['Normal']))
                                    elements.append(Spacer(1, 3))
                                elements.append(Spacer(1, 3))
                                paragrafo_atual = []
                    
                    # Processar último parágrafo se existir
                    if paragrafo_atual:
                        paragrafo_texto = ' '.join(paragrafo_atual)
                        # Dividir parágrafos longos para evitar erros do ReportLab
                        paragrafos_divididos = split_long_paragraph(paragrafo_texto)
                        for p in paragrafos_divididos:
                            elements.append(Paragraph(p, styles['Normal']))
                            elements.append(Spacer(1, 3))
                        elements.append(Spacer(1, 3))
                    elements.append(Spacer(1, 20))
                except Exception as e:
                    elements.append(Paragraph(f"Erro ao carregar abertura: {str(e)}", styles['Normal']))
                    
                # 4. CARREGAR ANÁLISE DAS TOP 3 ÂNCORAS
                posicoes = ["PRIMEIRA", "SEGUNDA", "TERCEIRA"]
                for i, ancora in enumerate(top_3):
                    elements.append(Paragraph(f"{posicoes[i]} ÂNCORA: {ancora['nome'].upper()}", graphic_title_style))
                    elements.append(Paragraph(f"Pontuação: {ancora['valor_total']:.1f} pontos", styles['Normal']))
                    elements.append(Spacer(1, 10))
                    
                    try:
                        with open(ancora['arquivo'], 'r', encoding='utf-8') as f:
                            conteudo_ancora = f.read()
                        # Converter markdown para PDF (com formatação completa)
                        try:
                            conteudo_formatado = convert_markdown_to_html(conteudo_ancora)
                        except Exception as e:
                            conteudo_formatado = conteudo_ancora  # usar original sem formatação
                        linhas_ancora = conteudo_formatado.split('\n')
                        
                        paragrafo_atual = []
                        for linha in linhas_ancora:
                            if linha.strip():  # Linha com conteúdo
                                if linha.startswith('#'):
                                    # Se há parágrafo acumulado, processar primeiro
                                    if paragrafo_atual:
                                        paragrafo_texto = ' '.join(paragrafo_atual)
                                        # Dividir parágrafos longos para evitar erros do ReportLab
                                        paragrafos_divididos = split_long_paragraph(paragrafo_texto)
                                        for p in paragrafos_divididos:
                                            try:
                                                # Limpar texto antes de criar Paragraph
                                                p_clean = clean_text_for_reportlab(p)
                                                elements.append(Paragraph(p_clean, styles['Normal']))
                                                elements.append(Spacer(1, 3))
                                            except Exception as e:
                                                # Usar versão simplificada sem formatação  
                                                p_simple = clean_text_for_reportlab(p)  # A função já remove HTML
                                                elements.append(Paragraph(p_simple, styles['Normal']))
                                                elements.append(Spacer(1, 3))
                                        elements.append(Spacer(1, 3))
                                        paragrafo_atual = []
                                    
                                    # Títulos
                                    titulo_clean = linha.replace('#', '').strip()
                                    if linha.startswith('###'):
                                        elements.append(Paragraph(titulo_clean, styles['Heading3']))
                                    elif linha.startswith('##'):
                                        elements.append(Paragraph(titulo_clean, styles['Heading2']))
                                    else:
                                        elements.append(Paragraph(titulo_clean, styles['Heading1']))
                                    elements.append(Spacer(1, 8))
                                elif linha.strip() == '---':
                                    # Linha divisória
                                    if paragrafo_atual:
                                        paragrafo_texto = ' '.join(paragrafo_atual)
                                        # Dividir parágrafos longos para evitar erros do ReportLab
                                        paragrafos_divididos = split_long_paragraph(paragrafo_texto)
                                        for p in paragrafos_divididos:
                                            try:
                                                # Limpar texto antes de criar Paragraph
                                                p_clean = clean_text_for_reportlab(p)
                                                elements.append(Paragraph(p_clean, styles['Normal']))
                                                elements.append(Spacer(1, 3))
                                            except Exception as e:
                                                # Usar versão simplificada sem formatação  
                                                p_simple = clean_text_for_reportlab(p)  # A função já remove HTML
                                                elements.append(Paragraph(p_simple, styles['Normal']))
                                                elements.append(Spacer(1, 3))
                                        elements.append(Spacer(1, 3))
                                        paragrafo_atual = []
                                    elements.append(Spacer(1, 12))
                                else:
                                    # Acumular linha no parágrafo atual
                                    paragrafo_atual.append(linha.strip())
                            else:  # Linha vazia - indica fim do parágrafo
                                if paragrafo_atual:
                                    paragrafo_texto = ' '.join(paragrafo_atual)
                                    # Dividir parágrafos longos para evitar erros do ReportLab
                                    paragrafos_divididos = split_long_paragraph(paragrafo_texto)
                                    for p in paragrafos_divididos:
                                        elements.append(Paragraph(p, styles['Normal']))
                                        elements.append(Spacer(1, 3))
                                        
                                    elements.append(Spacer(1, 3))
                                    paragrafo_atual = []
                        
                        # Processar último parágrafo se existir
                        if paragrafo_atual:
                            paragrafo_texto = ' '.join(paragrafo_atual)
                            # Dividir parágrafos longos para evitar erros do ReportLab
                            paragrafos_divididos = split_long_paragraph(paragrafo_texto)
                            for p in paragrafos_divididos:
                                elements.append(Paragraph(p, styles['Normal']))
                                elements.append(Spacer(1, 3))
                                
                            elements.append(Spacer(1, 3))
                        
                        elements.append(Spacer(1, 20))
                    except Exception as e:
                        elements.append(Paragraph(f"Erro ao carregar {ancora['nome']}: {str(e)}", styles['Normal']))
                        elements.append(Spacer(1, 10))
            else:
                elements.append(Paragraph("Dados insuficientes para análise completa das âncoras", styles['Normal']))

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
        
        # 2. Registra acesso à página
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
            
            # Primeiro processar tabelas em container separado
            tabelas = [elem for elem in row_data if elem[1] == 'tabela']
            for tabela in tabelas:
                with st.container():
                    # Centralizar a tabela usando colunas
                    col1, col2, col3 = st.columns([1, 8, 1])
                    with col2:
                        tabela_dados_sem_titulo(cursor, tabela)
            
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
        
        # 5. Gerar e exibir análise de Âncoras de Carreira
        with st.expander("Clique aqui para ver sua Análise de Âncoras de Carreira", expanded=False):
            st.markdown("---")
            
            # Chama a função que gera e exibe a análise de âncoras
            analisar_ancoras_carreira_streamlit(cursor, user_id)
            
            st.markdown("---")

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
            valor = format_br_number(result[0]) if result and result[0] is not None else '0,00'
            valores.append(valor)
        
        # Criar DataFrame com os dados
        df = pd.DataFrame({
            'Indicador': rotulos,
            'Valor': valores
        })
        
        # Criar três colunas, usando a do meio para a tabela
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col2:
            # Criar HTML da tabela com estilos inline (sem o título)
            html_table = f"""
            <div style='font-size: 20px; width: 80%;'>
                <table style='width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 0 8px rgba(0,0,0,0.1);'>
                    <thead>
                        <tr>
                            <th style='text-align: left; padding: 10px; background-color: #e8f5e9; border-bottom: 2px solid #dee2e6;'>Indicador</th>
                            <th style='text-align: right; padding: 10px; background-color: #e8f5e9; border-bottom: 2px solid #dee2e6;'>Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f"<tr><td style='padding: 8px 10px; border-bottom: 1px solid #dee2e6;'>{row['Indicador']}</td><td style='text-align: right; padding: 8px 10px; border-bottom: 1px solid #dee2e6;'>{row['Valor']}</td></tr>" for _, row in df.iterrows())}
                    </tbody>
                </table>
            </div>
            """
            
            # Exibe a tabela HTML
            st.markdown(html_table, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao criar tabela: {str(e)}")

# Função DISC removida - Sistema agora é exclusivo para Âncoras de Carreira

# FUNÇÕES DISC REMOVIDAS - Sistema agora exclusivo para Âncoras de Carreira
# As funções analisar_perfil_disc_streamlit() e analisar_perfil_disc() foram removidas
# def analisar_perfil_disc(cursor, user_id):  # FUNÇÃO REMOVIDA
    # FUNÇÃO DISC REMOVIDA - Sistema agora é exclusivo para Âncoras de Carreira
    pass

# ===============================================================
# FUNÇÕES DE ANÁLISE DE ÂNCORAS DE CARREIRA
# ===============================================================

def parse_br_number(value_str):
    """
    Converte string com formato brasileiro para float
    """
    if not value_str:
        return 0.0
    try:
        # Remover espaços
        clean_str = str(value_str).strip()
        # Trocar vírgula por ponto
        clean_str = clean_str.replace(',', '.')
        return float(clean_str)
    except:
        return 0.0

# Sistema refatorado - agora exclusivo para Âncoras de Carreira

def buscar_valor_ancora(cursor, user_id, name_element):
    """
    Busca valor específico de uma âncora na tabela forms_resultados
    """
    try:
        cursor.execute("""
            SELECT value_element FROM forms_resultados
            WHERE user_id = ? AND name_element = ?
            LIMIT 1
        """, (user_id, name_element))
        
        result = cursor.fetchone()
        if result and result[0] is not None:
            valor = parse_br_number(result[0])
            # Correção para valores multiplicados por 1000
            return valor / 1000 if valor >= 1000 else valor
        return 0.0
        
    except Exception:
        return 0.0

def analisar_ancoras_carreira_streamlit(cursor, user_id):
    """
    Análise de Âncoras de Carreira com RANKING UNIFICADO
    Combina valores P1 e P2 para criar ranking das 8 âncoras
    """
    try:
        # 1. Buscar dados do usuário
        cursor.execute("""
            SELECT u.nome, u.email, u.empresa 
            FROM usuarios u 
            WHERE u.user_id = ?
        """, (user_id,))
        usuario_info = cursor.fetchone()
        
        # 2. Definir mapeamento completo das âncoras (códigos corretos do banco)
        # Cores do prisma/espectro para as 8 âncoras
        mapeamento_ancoras = {
            'C31': {
                'nome': 'Competência Técnica / Funcional',
                'descricao': 'Desenvolvimento de expertise técnica e especialização profissional',
                'cor': '#FF0000',  # Vermelho
                'arquivo': 'Conteudo/A1_Competencia_Tecnica.md'
            },
            'C32': {
                'nome': 'Gestão Geral',
                'descricao': 'Liderança, coordenação e responsabilidade gerencial',
                'cor': '#FF8C00',  # Laranja
                'arquivo': 'Conteudo/A2_Gestao_Geral.md'
            },
            'C33': {
                'nome': 'Autonomia / Independência',
                'descricao': 'Liberdade para tomar decisões e trabalhar independentemente',
                'cor': '#FFD700',  # Amarelo
                'arquivo': 'Conteudo/A3_Autonomia_Independencia.md'
            },
            'C34': {
                'nome': 'Segurança / Estabilidade',
                'descricao': 'Estabilidade financeira e segurança no emprego',
                'cor': '#00FF00',  # Verde
                'arquivo': 'Conteudo/A4_Seguranca_Estabilidade.md'
            },
            'D31': {
                'nome': 'Criatividade Empreendedora',
                'descricao': 'Inovação, criação de novos produtos e empreendedorismo',
                'cor': '#0080FF',  # Azul
                'arquivo': 'Conteudo/A5_Criatividade_Empreendedora.md'
            },
            'D32': {
                'nome': 'Serviço / Dedicação',
                'descricao': 'Contribuição para a sociedade e ajuda aos outros',
                'cor': '#4B0082',  # Índigo
                'arquivo': 'Conteudo/A6_Servico_Dedicacao.md'
            },
            'D33': {
                'nome': 'Estilo de Vida',
                'descricao': 'Equilíbrio entre vida pessoal e profissional',
                'cor': '#8A2BE2',  # Violeta
                'arquivo': 'Conteudo/A7_Estilo_Vida.md'
            },
            'D34': {
                'nome': 'Desafio Puro',
                'descricao': 'Busca por desafios complexos e competição',
                'cor': '#FF1493',  # Rosa/Pink
                'arquivo': 'Conteudo/A8_Desafio_Puro.md'
            }
        }
        
        # 3. Buscar valores das âncoras para criar ranking
        # USAR TABELA ESPECÍFICA: forms_resultados
        tabela = 'forms_resultados'
        
        codigos_ancoras = list(mapeamento_ancoras.keys())
        ranking_ancoras = []
        
        for codigo in codigos_ancoras:
            # Usar a mesma lógica da função tabela_dados que funciona
            cursor.execute("""
                SELECT value_element 
                FROM forms_resultados 
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (codigo.strip(), user_id))
            
            result = cursor.fetchone()
            valor_total = parse_br_number(result[0]) if result and result[0] is not None else 0.0
            

            
            # Adicionar ao ranking
            ranking_ancoras.append({
                'codigo': codigo,
                'nome': mapeamento_ancoras[codigo]['nome'],
                'descricao': mapeamento_ancoras[codigo]['descricao'],
                'valor_total': valor_total,
                'cor': mapeamento_ancoras[codigo]['cor'],
                'arquivo': mapeamento_ancoras[codigo]['arquivo']
            })
        
        # 4. Ordenar ranking por valor total (maior para menor)
        ranking_ancoras.sort(key=lambda x: x['valor_total'], reverse=True)
        
        # 5. Validar se existem dados suficientes
        valores_validos = [a for a in ranking_ancoras if a['valor_total'] > 0]
        
        if len(valores_validos) < 3:
            st.markdown("## ⚠️ Análise de Âncoras de Carreira não disponível")
            st.markdown("### 👤 Informações do Usuário:")
            if usuario_info:
                st.markdown(f"**Nome:** {usuario_info[0] or 'Não informado'}")
                st.markdown(f"**Email:** {usuario_info[1] or 'Não informado'}")
                st.markdown(f"**Empresa:** {usuario_info[2] or 'Não informado'}")
            st.markdown(f"**Problema:** Dados insuficientes. Encontrados apenas {len(valores_validos)} âncoras com valores.")
            st.markdown("**Solução:** Complete as avaliações de Âncoras P1 e P2 para gerar os resultados.")
            st.markdown("---")
            st.info("💡 **Informação:** Este sistema analisa exclusivamente Âncoras de Carreira, oferecendo uma avaliação completa das suas motivações e valores profissionais.")
            return
        
        # 6. EXIBIR ANÁLISE COMPLETA
        st.markdown("## ⚓ Análise de Âncoras de Carreira")
        
        # Informações do usuário
        if usuario_info:
            info_html = f"""
            <div style='background-color: #f0f8ff; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #0066cc;'>
                <p style='margin: 0; font-size: 16px;'>
                    <strong>👤 Nome:</strong> {usuario_info[0] or 'Não informado'}<br>
                    <strong>📧 Email:</strong> {usuario_info[1] or 'Não informado'}<br>
                    <strong>🏢 Empresa:</strong> {usuario_info[2] or 'Não informado'}
                </p>
            </div>
            """
            st.markdown(info_html, unsafe_allow_html=True)
        
        # 7. RANKING COMPLETO DAS 8 ÂNCORAS
        st.markdown("### 🏆 Ranking Completo das Âncoras de Carreira")
        st.markdown("*Valores das âncoras de carreira*")
        
        # Preparar dados para tabela
        dados_ranking = []
        for i, ancora in enumerate(ranking_ancoras):
            posicao = f"{i+1}º"
            valor_total_br = f"{ancora['valor_total']:.1f}".replace('.', ',')
            
            dados_ranking.append({
                'Posição': posicao,
                'Âncora de Carreira': ancora['nome'],
                'Valor Total': valor_total_br,
                'Descrição': ancora['descricao']
            })
        
        # Criar DataFrame
        df_ranking = pd.DataFrame(dados_ranking)
        
        # Exibir tabela completa
        st.dataframe(
            df_ranking,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Posição": st.column_config.TextColumn(
                    "Posição",
                    width="small",
                ),
                "Âncora de Carreira": st.column_config.TextColumn(
                    "Âncora de Carreira",
                    width="medium",
                ),
                "Valor Total": st.column_config.TextColumn(
                    "Valor Total",
                    width="small",
                ),
                "Descrição": st.column_config.TextColumn(
                    "Descrição",
                    width="large",
                ),
            }
        )
        
        # 8. ANÁLISE DAS TOP 3 ÂNCORAS
        top_3 = ranking_ancoras[:3]
        
        st.markdown("### 🎯 Suas 3 Âncoras Principais")
        
        # Box com as top 3
        top_3_html = f"""
        <div style='background-color: #e8f5e8; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #28a745;'>
            <h4 style='margin-top: 0; color: #155724;'>🏆 Suas Âncoras Mais Fortes:</h4>
            <p style='margin: 5px 0; font-size: 16px; color: #155724;'>
                <strong>🥇 1ª Lugar:</strong> {top_3[0]['nome']} 
                <span style='background-color: #28a745; color: white; padding: 2px 8px; border-radius: 4px; font-size: 14px;'>
                    {top_3[0]['valor_total']:.1f} pontos
                </span>
            </p>
            <p style='margin: 5px 0; font-size: 16px; color: #155724;'>
                <strong>🥈 2ª Lugar:</strong> {top_3[1]['nome']} 
                <span style='background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 4px; font-size: 14px;'>
                    {top_3[1]['valor_total']:.1f} pontos
                </span>
            </p>
            <p style='margin: 5px 0; font-size: 16px; color: #155724;'>
                <strong>🥉 3ª Lugar:</strong> {top_3[2]['nome']} 
                <span style='background-color: #fd7e14; color: white; padding: 2px 8px; border-radius: 4px; font-size: 14px;'>
                    {top_3[2]['valor_total']:.1f} pontos
                </span>
            </p>
        </div>
        """
        st.markdown(top_3_html, unsafe_allow_html=True)
        
        # 9. ANÁLISE DETALHADA DA ÂNCORA PRINCIPAL (conforme Analise Tipo de Perfil.md)
        ancora_principal = top_3[0]
        segunda_ancora = top_3[1]
        terceira_ancora = top_3[2]
        
        # Calcular diferenças absolutas
        diferenca_1_2 = ancora_principal['valor_total'] - segunda_ancora['valor_total']
        diferenca_1_3 = ancora_principal['valor_total'] - terceira_ancora['valor_total']
        diferenca_2_3 = segunda_ancora['valor_total'] - terceira_ancora['valor_total']
        
        # Calcular diferenças percentuais
        perc_1_2 = (diferenca_1_2 / segunda_ancora['valor_total']) * 100 if segunda_ancora['valor_total'] > 0 else 0
        perc_1_3 = (diferenca_1_3 / terceira_ancora['valor_total']) * 100 if terceira_ancora['valor_total'] > 0 else 0
        
        # Determinar tipo de perfil conforme critérios do documento
        if ((perc_1_2 >= 15 and perc_1_3 >= 25) or 
            (diferenca_1_2 >= 30 and diferenca_1_3 >= 50)):
            tipo_perfil = "DOMINANTE"
            criterio = f"1ª âncora: +{diferenca_1_2:.1f}pts ({perc_1_2:.1f}%) da 2ª e +{diferenca_1_3:.1f}pts ({perc_1_3:.1f}%) da 3ª"
        elif (diferenca_1_2 <= 15 and diferenca_1_3 <= 15 and diferenca_2_3 <= 15):
            tipo_perfil = "EQUILIBRADO"
            criterio = f"Diferenças pequenas entre top 3: {diferenca_1_2:.1f}pts, {diferenca_1_3:.1f}pts, {diferenca_2_3:.1f}pts"
        else:
            tipo_perfil = "MODERADAMENTE DOMINANTE"
            criterio = f"Perfil intermediário: +{diferenca_1_2:.1f}pts da 2ª, +{diferenca_1_3:.1f}pts da 3ª"
        
        # Informações do perfil
        info_perfil_html = f"""
        <div style='background-color: #fff3cd; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #ffc107;'>
            <p style='margin: 0; font-size: 16px; color: #856404;'>
                <strong>🎯 Âncora Dominante:</strong> {ancora_principal['nome']}<br>
                <strong>📊 Pontuação:</strong> {ancora_principal['valor_total']:.1f} pontos<br>
                <strong>📈 Tipo de Perfil:</strong> {tipo_perfil}<br>
                <strong>📋 Critério:</strong> {criterio}
            </p>
        </div>
        """
        st.markdown(info_perfil_html, unsafe_allow_html=True)
        
        # 10. EXIBIR ANÁLISE DETALHADA - NOVA LÓGICA
        st.markdown("## 📖 Análise das suas Âncoras de Carreira")
        
        # 10.1 SEMPRE CARREGAR ABERTURA PRIMEIRO
        arquivo_abertura = 'Conteudo/A0_Abertura_Devolutiva.md'
        
        try:
            with open(arquivo_abertura, 'r', encoding='utf-8') as f:
                conteudo_abertura = f.read()
            st.markdown(conteudo_abertura, unsafe_allow_html=True)
            
        except FileNotFoundError:
            st.warning(f"📝 **Arquivo de abertura não encontrado:** {arquivo_abertura}")
            st.info("Iniciando análise das suas âncoras de carreira...")
            
        except Exception as e:
            st.error(f"❌ **Erro ao carregar abertura:** {str(e)}")
        
        # 10.2 CARREGAR ANÁLISE DAS TOP 3 ÂNCORAS
        posicoes = ["🥇 Primeira", "🥈 Segunda", "🥉 Terceira"]
        
        for i, ancora in enumerate(top_3):
            posicao = posicoes[i]
            arquivo_analise = ancora['arquivo']
            
            try:
                st.markdown(f"### {posicao} Âncora: {ancora['nome']}")
                st.markdown(f"**Pontuação:** {ancora['valor_total']:.1f} pontos")
                
                with open(arquivo_analise, 'r', encoding='utf-8') as f:
                    conteudo_analise = f.read()
                
                # Exibir conteúdo da âncora
                st.markdown(conteudo_analise, unsafe_allow_html=True)
                
                # Separador entre âncoras (exceto na última)
                if i < len(top_3) - 1:
                    st.markdown("---")
                
            except FileNotFoundError:
                st.warning(f"📝 **Arquivo não encontrado:** {arquivo_analise}")
                st.info(f"A análise detalhada de {ancora['nome']} será disponibilizada em breve.")
                
                # Análise básica como fallback
                st.markdown(f"**Descrição:** {ancora['descricao']}")
                st.markdown(f"**Sua pontuação:** {ancora['valor_total']:.1f} pontos")
                
            except Exception as e:
                st.error(f"❌ **Erro ao carregar análise de {ancora['nome']}:** {str(e)}")
        
        # 11. RESUMO EXECUTIVO (conforme Analise Tipo de Perfil.md)
        st.markdown("### 📋 Resumo do seu Perfil de Âncoras")
        
        # Identificar padrão das top 3
        nomes_top_3 = [a['nome'] for a in top_3]
        
        # Interpretação baseada no tipo de perfil
        if tipo_perfil == "DOMINANTE":
            interpretacao = f"""Com base na distribuição de pontos, observa-se um perfil **{tipo_perfil}**. 
            A âncora **{ancora_principal['nome']}** se destaca com {ancora_principal['valor_total']:.1f} pontos, 
            representando a principal motivação de carreira. A diferença de {diferenca_1_2:.1f} pontos para a segunda âncora 
            sugere uma motivação muito clara e bem definida."""
            
        elif tipo_perfil == "EQUILIBRADO":
            interpretacao = f"""Com base na distribuição de pontos, observa-se um perfil **{tipo_perfil}**. 
            As diferenças pequenas entre as âncoras apontam para um perfil **multifacetado e adaptável**, 
            indicando que você busca realizar-se por meio de uma combinação de fatores como {', '.join(nomes_top_3)}."""
            
        else:  # MODERADAMENTE DOMINANTE
            interpretacao = f"""Com base na distribuição de pontos, observa-se um perfil **{tipo_perfil}**. 
            A âncora **{ancora_principal['nome']}** mostra uma leve predominância com {ancora_principal['valor_total']:.1f} pontos, 
            mas as outras âncoras também têm peso significativo, sugerindo múltiplas motivações profissionais."""
        
        resumo_html = f"""
        <div style='background-color: #d1ecf1; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #bee5eb;'>
            <h5 style='margin-top: 0; color: #0c5460;'>🎯 Resumo Executivo</h5>
            <p style='margin: 5px 0; color: #0c5460; line-height: 1.6;'>
                {interpretacao}
            </p>
            <hr style='margin: 10px 0; border-color: #bee5eb;'>
            <p style='margin: 5px 0; color: #0c5460; font-size: 14px;'>
                <strong>Top 3 Âncoras:</strong> {' | '.join([f"{i+1}º {a['nome']} ({a['valor_total']:.1f}pts)" for i, a in enumerate(top_3)])}<br>
                <strong>Critério de Classificação:</strong> {criterio}
            </p>
        </div>
        """
        st.markdown(resumo_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ **Erro na análise de Âncoras de Carreira:** {str(e)}")
        import traceback
        st.error(f"**Detalhes técnicos:** {traceback.format_exc()}")

if __name__ == "__main__":
    show_results()

