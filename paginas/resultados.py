# resultados.py
# Data: 28/06/2025 09:35
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
    "forms_resultados": "Análise: Avaliação DISC"
}

# Dicionário de subtítulos para cada tabela
SUBTITULOS_TABELAS = {
    "forms_resultados": "Avaliação de Perfis"
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
        
        # Define as cores fixas para cada posição DISC (D, I, S, C)
        cores_disc = ['#B22222', '#DAA520', '#2E8B57', '#4682B4']
        
        # Aplica as cores pela posição (ordem das barras)
        cores = []
        for i in range(len(labels)):
            if i < len(cores_disc):
                cores.append(cores_disc[i])
            else:
                cores.append('#1f77b4')  # cor padrão se houver mais de 4 barras
        

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
        # Define as cores fixas para cada posição DISC (D, I, S, C)
        cores_disc = ['#B22222', '#DAA520', '#2E8B57', '#4682B4']
        
        # Aplica as cores pela posição (ordem das barras)
        cores = []
        for i in range(len(labels)):
            if i < len(cores_disc):
                cores.append(cores_disc[i])
            else:
                cores.append('#1f77b4')  # cor padrão se houver mais de 4 barras
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
                            file_name="simulacoes.pdf",
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
    Tabela Perfil → Gráfico Perfil → Tabela Comportamento → Gráfico Comportamento
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
            titulo_principal = TITULOS_TABELAS.get(tabela_escolhida, "Análise DISC")
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

            # Layout específico: Tabela Perfil → Gráfico Perfil → Tabela Comportamento → Gráfico Comportamento
            
            # 1. TABELA PERFIL (primeira tabela encontrada)
            if len(tabelas) > 0:
                tabela_perfil = tabelas[0]
                dados_tabela_perfil = gerar_dados_tabela(pdf_cursor, tabela_perfil, height_pct=100, width_pct=100)
                if dados_tabela_perfil:
                    # Cria tabela com título "Resultados do Perfil"
                    elements.append(Paragraph("Resultados do Perfil", graphic_title_style))
                    elements.append(Spacer(1, 10))
                    t = Table(dados_tabela_perfil['data'], colWidths=[table_width * 0.6, table_width * 0.4])
                    t.setStyle(table_style)
                    elements.append(Table([[t]], colWidths=[table_width], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                    elements.append(Spacer(1, 20))

            # 2. GRÁFICO PERFIL (primeiro gráfico encontrado)
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
                    elements.append(Spacer(1, 30))

            # 3. TABELA COMPORTAMENTO (segunda tabela ou cópia da primeira)
            if len(tabelas) > 1:
                tabela_comportamento = tabelas[1]
            else:
                tabela_comportamento = tabelas[0] if tabelas else None
                
            if tabela_comportamento:
                dados_tabela_comportamento = gerar_dados_tabela(pdf_cursor, tabela_comportamento, height_pct=100, width_pct=100)
                if dados_tabela_comportamento:
                    # Cria tabela com título "Resultados do Comportamento"
                    elements.append(Paragraph("Resultados do Comportamento", graphic_title_style))
                    elements.append(Spacer(1, 10))
                    t = Table(dados_tabela_comportamento['data'], colWidths=[table_width * 0.6, table_width * 0.4])
                    t.setStyle(table_style)
                    elements.append(Table([[t]], colWidths=[table_width], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                    elements.append(Spacer(1, 20))

            # 4. GRÁFICO COMPORTAMENTO (segundo gráfico ou cópia do primeiro)
            if len(graficos) > 1:
                grafico_comportamento = graficos[1]
            else:
                grafico_comportamento = graficos[0] if graficos else None
                
            if grafico_comportamento:
                dados_grafico_comportamento = gerar_dados_grafico(pdf_cursor, grafico_comportamento, tabela_escolhida, height_pct=100, width_pct=100)
                if dados_grafico_comportamento:
                    # Força o título para "RESULTADOS DE COMPORTAMENTO"
                    elements.append(Paragraph("RESULTADOS DE COMPORTAMENTO", graphic_title_style))
                    elements.append(Spacer(1, 10))
                    elements.append(Table(
                        [[dados_grafico_comportamento['image']]],
                        colWidths=[graph_width],
                        style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                    ))

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
        
        # 5. Gerar e exibir a análise DISC
        with st.expander("Clique aqui para ver sua Análise DISC de PERFIL", expanded=False):
            st.markdown("---")
            
            # Chama a função que gera e exibe a análise diretamente
            analisar_perfil_disc_streamlit(cursor, user_id)
            
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

def analisar_perfil_disc_streamlit(cursor, user_id):
    """
    Gera análise comportamental DISC na interface Streamlit.
    FUNÇÃO LIMPA - Pronta para novas regras e conteúdo.
    """
    try:
        # 1. Buscar dados do usuário
        cursor.execute("""
            SELECT u.nome, u.email, u.empresa 
            FROM usuarios u 
            WHERE u.user_id = ?
        """, (user_id,))
        usuario_info = cursor.fetchone()
        
        # 2. Buscar gráfico DISC
        tabela = st.session_state.tabela_escolhida
        
        # Busca por títulos DISC
        titulos_busca = [
            '%RESULTADOS DE PERFIS%',
            '%PESQUISA COMPORTAMENTAL%', 
            '%COMPORTAMENTAL%',
            '%PERFIL%',
            '%DISC%'
        ]
        
        result = None
        titulo_grafico_usado = ""
        for titulo in titulos_busca:
            cursor.execute(f"""
                SELECT select_element, str_element, msg_element
                FROM {tabela}
                WHERE user_id = ? AND type_element = 'grafico' AND msg_element LIKE ?
                LIMIT 1
            """, (user_id, titulo))
            result = cursor.fetchone()
            if result and result[0] and result[1]:
                titulo_grafico_usado = titulo
                break
        
        # Fallback: busca qualquer gráfico com 4 elementos
        if not result or not result[0] or not result[1]:
            cursor.execute(f"""
                SELECT select_element, str_element, msg_element
                FROM {tabela}
                WHERE user_id = ? AND type_element = 'grafico'
                AND select_element IS NOT NULL 
                AND str_element IS NOT NULL
                AND LENGTH(select_element) - LENGTH(REPLACE(select_element, '|', '')) = 3
                LIMIT 1
            """, (user_id,))
            result = cursor.fetchone()
            titulo_grafico_usado = "Gráfico com 4 elementos encontrado"
        
        # Validação: se não encontrou dados DISC
        if not result or not result[0] or not result[1]:
            st.markdown("## ⚠️ Análise DISC não disponível")
            st.markdown("### 👤 Informações do Usuário:")
            if usuario_info:
                st.markdown(f"**Nome:** {usuario_info[0] or 'Não informado'}")
                st.markdown(f"**Email:** {usuario_info[1] or 'Não informado'}")
                st.markdown(f"**Empresa:** {usuario_info[2] or 'Não informado'}")
            st.markdown("**Problema:** Dados DISC não encontrados para este usuário.")
            return

        # 3. Processar elementos DISC
        name_elements = [name.strip() for name in result[0].split('|')]
        labels = [label.strip() for label in result[1].split('|')]
        titulo_grafico = result[2] if result[2] else "Gráfico DISC"
        
        # 4. Mapear perfis D,I,S,C
        profile_map = {}
        for name, label in zip(name_elements, labels):
            if '(' in label and ')' in label:
                letra_parenteses = label[label.find('(')+1:label.find(')')].upper()
                if letra_parenteses in ['D', 'I', 'S', 'C']:
                    profile_map[name] = letra_parenteses
            else:
                first_letter = label[0].upper() if label else ''
                if first_letter in ['D', 'I', 'S', 'C']:
                    profile_map[name] = first_letter

        # 5. Obter valores DISC do usuário
        placeholders = ','.join('?' for _ in name_elements)
        cursor.execute(f"""
            SELECT name_element, value_element
            FROM {tabela}
            WHERE user_id = ? AND name_element IN ({placeholders})
        """, (user_id, *name_elements))
        resultados_disc_raw = cursor.fetchall()
        
        if not resultados_disc_raw:
            st.markdown("## ⚠️ Dados DISC não encontrados")
            st.markdown("**Problema:** Valores DISC não calculados para este usuário.")
            return

        # 6. Construir perfil DISC
        perfil = {profile_map.get(name, name): float(value if value is not None else 0.0) 
                 for name, value in resultados_disc_raw}
        perfil = {k: v for k, v in perfil.items() if k}  # Remove chaves vazias

        if len(perfil) < 2:
            st.markdown("## ⚠️ Dados DISC insuficientes")
            st.markdown(f"**Problema:** Apenas {len(perfil)} perfis encontrados. Necessário pelo menos 2.")
            return

        # 7. Definir perfis primário e secundário
        perfil_ordenado = sorted(perfil.items(), key=lambda item: item[1], reverse=True)
        perfil_primario, valor_primario = perfil_ordenado[0]
        perfil_secundario, valor_secundario = perfil_ordenado[1] if len(perfil_ordenado) > 1 else ('', 0)

        # ===== PASSO 2: CÁLCULO DE VARIÁVEIS HÍBRIDAS =====
        
        st.markdown("## 📊 Análise Comportamental DISC")
        st.markdown("### 👤 Informações do Participante")
        
        # Exibir dados do usuário
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
        
        # Buscar valores para cálculo das variáveis híbridas
        elementos_busca = ['C31', 'D31', 'C32', 'D32', 'C33', 'D33', 'C34', 'D34']
        valores_elementos = {}
        
        for elemento in elementos_busca:
            cursor.execute(f"""
                SELECT value_element
                FROM {tabela}
                WHERE user_id = ? AND name_element = ?
                LIMIT 1
            """, (user_id, elemento))
            result = cursor.fetchone()
            if result and result[0] is not None:
                # Converter formato brasileiro para float
                valor_convertido = parse_br_number(result[0])
                
                # Aplicar correção se valor estiver multiplicado por 1000
                if valor_convertido >= 1000:
                    valores_elementos[elemento] = valor_convertido / 1000
                else:
                    valores_elementos[elemento] = valor_convertido
            else:
                valores_elementos[elemento] = 0.0
        
        # Calcular variáveis híbridas
        variaveis_hibridas = []
        
        # Dominância Híbrida = (C31 + D31) / 2
        dominancia_hibrida = (valores_elementos['C31'] + valores_elementos['D31']) / 2
        variaveis_hibridas.append({
            'dimensao': 'Dominância',
            'letra': 'D',
            'valor_hibrido': dominancia_hibrida,
            'perfil': valores_elementos['C31'],
            'comportamento': valores_elementos['D31']
        })
        
        # Influência Híbrida = (C32 + D32) / 2
        influencia_hibrida = (valores_elementos['C32'] + valores_elementos['D32']) / 2
        variaveis_hibridas.append({
            'dimensao': 'Influência',
            'letra': 'I',
            'valor_hibrido': influencia_hibrida,
            'perfil': valores_elementos['C32'],
            'comportamento': valores_elementos['D32']
        })
        
        # Estabilidade Híbrida = (C33 + D33) / 2
        estabilidade_hibrida = (valores_elementos['C33'] + valores_elementos['D33']) / 2
        variaveis_hibridas.append({
            'dimensao': 'Estabilidade',
            'letra': 'S',
            'valor_hibrido': estabilidade_hibrida,
            'perfil': valores_elementos['C33'],
            'comportamento': valores_elementos['D33']
        })
        
        # Conformidade Híbrida = (C34 + D34) / 2
        conformidade_hibrida = (valores_elementos['C34'] + valores_elementos['D34']) / 2
        variaveis_hibridas.append({
            'dimensao': 'Conformidade',
            'letra': 'C',
            'valor_hibrido': conformidade_hibrida,
            'perfil': valores_elementos['C34'],
            'comportamento': valores_elementos['D34']
        })
        
        # Ordenar por valor híbrido (maior para menor)
        variaveis_hibridas.sort(key=lambda x: x['valor_hibrido'], reverse=True)
        
        # Renderizar tabela de variáveis híbridas
        st.markdown("### 🔄 Variáveis Híbridas DISC")
        st.markdown("*Média balanceada entre Perfil e Comportamento*")
        
        # Preparar dados para DataFrame
        import pandas as pd
        
        dados_tabela = []
        for i, variavel in enumerate(variaveis_hibridas):
            posicao = f"{i+1}º"
            
            # Formatação brasileira com 1 casa decimal (valores já corrigidos na origem)
            valor_hibrido_br = f"{variavel['valor_hibrido']:.1f}".replace('.', ',')
            perfil_br = f"{variavel['perfil']:.1f}".replace('.', ',')
            comportamento_br = f"{variavel['comportamento']:.1f}".replace('.', ',')
            
            dados_tabela.append({
                'Posição': posicao,
                'Dimensão DISC': f"{variavel['letra']} - {variavel['dimensao']}",
                'Valor Híbrido': valor_hibrido_br,
                'Perfil': perfil_br,
                'Comportamento': comportamento_br
            })
        
        # Criar DataFrame
        df_hibridas = pd.DataFrame(dados_tabela)
        
        # Criar colunas para centralizar
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col2:
            # Exibir tabela usando Streamlit dataframe
            st.dataframe(
                df_hibridas,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Posição": st.column_config.TextColumn(
                        "Posição",
                        width="small",
                    ),
                    "Dimensão DISC": st.column_config.TextColumn(
                        "Dimensão DISC",
                        width="medium",
                    ),
                    "Valor Híbrido": st.column_config.TextColumn(
                        "Valor Híbrido",
                        width="small",
                    ),
                    "Perfil": st.column_config.TextColumn(
                        "Perfil", 
                        width="small",
                    ),
                    "Comportamento": st.column_config.TextColumn(
                        "Comportamento",
                        width="small",
                    ),
                }
            )
        

        
        # ===== FIM DO PASSO 2 =====

        # ===== PASSO 3: ANÁLISE DE PERFIL ÚNICO OU COMBINADO =====
        
        st.markdown("---")
        st.markdown("### 🔍 Análise Comportamental Detalhada")
        
        # Calcular diferença entre primário e secundário
        if len(variaveis_hibridas) >= 2:
            primario = variaveis_hibridas[0]
            secundario = variaveis_hibridas[1]
            diferenca = primario['valor_hibrido'] - secundario['valor_hibrido']
            
            # Determinar tipo de perfil e arquivo correspondente
            if diferenca > 5:
                # PERFIL ÚNICO
                tipo_perfil = "ÚNICO"
                letra_primaria = primario['letra']
                
                # Mapear arquivo baseado no perfil primário
                arquivos_unicos = {
                    'D': 'Conteudo/1_D_Dominancia.md',
                    'I': 'Conteudo/1_I_Influencia.md', 
                    'S': 'Conteudo/1_S_Estabilidade.md',
                    'C': 'Conteudo/1_C_Conformidade.md'
                }
                
                arquivo_analise = arquivos_unicos.get(letra_primaria)
                titulo_analise = f"Perfil {tipo_perfil}: {primario['dimensao']}"
                
            else:
                # PERFIL COMBINADO
                tipo_perfil = "COMBINADO"
                letra_primaria = primario['letra']
                letra_secundaria = secundario['letra']
                combinacao = f"{letra_primaria}{letra_secundaria}"
                
                # Mapear arquivo baseado na combinação
                arquivos_combinados = {
                    'DC': 'Conteudo/21_DC_DOMINANCIA_CONFORMIDADE.md',
                    'DI': 'Conteudo/22_DI_DOMINANCIA_INFLUENCIA.md',
                    'ID': 'Conteudo/23_ID_INFLUENCIA_DOMINANCIA.md',
                    'IS': 'Conteudo/24_IS_INFLUENCIA_ESTABILIDADE.md',
                    'SI': 'Conteudo/25_SI_ESTABILIDADE_INFLUENCIA.md',
                    'SC': 'Conteudo/26_SC_ESTABILIDADE_CONFORMIDADE.md',
                    'CD': 'Conteudo/27_CD_CONFORMIDADE_DOMINANCIA.md'
                }
                
                arquivo_analise = arquivos_combinados.get(combinacao)
                titulo_analise = f"Perfil {tipo_perfil}: {primario['dimensao']} + {secundario['dimensao']}"
            
            # Exibir informações do tipo de perfil
            info_perfil_html = f"""
            <div style='background-color: #fff3cd; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #ffc107;'>
                <p style='margin: 0; font-size: 16px; color: #856404;'>
                    <strong>📊 Tipo de Perfil:</strong> {tipo_perfil}<br>
                    <strong>📈 Diferença Primário-Secundário:</strong> {diferenca:.1f} pontos<br>
                    <strong>📋 Critério:</strong> {'Diferença > 5 pontos = Perfil Único' if diferenca > 5 else 'Diferença ≤ 5 pontos = Perfil Combinado'}
                </p>
            </div>
            """
            st.markdown(info_perfil_html, unsafe_allow_html=True)
            
            # Tentar ler e exibir o conteúdo do arquivo
            if arquivo_analise:
                try:
                    with open(arquivo_analise, 'r', encoding='utf-8') as f:
                        conteudo_analise = f.read()
                    
                    # Exibir título da análise
                    st.markdown(f"## 📖 {titulo_analise}")
                    
                    # Exibir todo o conteúdo do arquivo markdown
                    st.markdown(conteudo_analise, unsafe_allow_html=True)
                    
                except FileNotFoundError:
                    st.error(f"❌ **Arquivo não encontrado:** {arquivo_analise}")
                    st.error("Verifique se o arquivo existe na pasta 'Conteudo' do projeto.")
                    
                except Exception as e:
                    st.error(f"❌ **Erro ao ler arquivo:** {str(e)}")
            else:
                # Combinação não encontrada
                st.error("❌ **COMBINAÇÃO DE PERFIL INDEFINIDO - AVISAR O CONSULTOR DO PROJETO**")
                st.error(f"Combinação não mapeada: {letra_primaria}/{letra_secundaria}")
        else:
            st.error("❌ **Dados insuficientes:** Necessário pelo menos 2 variáveis híbridas para análise.")
        
        # ===== FIM DO PASSO 3 =====

    except Exception as e:
        st.error(f"Erro na análise DISC: {str(e)}")

def analisar_perfil_disc(cursor, user_id):
    """
    Realiza uma análise completa do perfil DISC do usuário dividida em 2 blocos:
    1. Análise do Perfil - características, pontos fortes e limitações
    2. Análise do Comportamento - manifestações práticas e desenvolvimento

    A base de conhecimento deve ser estruturada com as seguintes tags:
    - <Perfis_Individuais>...</Perfis_Individuais>
    - <Perfis_Combinados>...</Perfis_Combinados>
    - <Excesso_Pontos_Fortes>...</Excesso_Pontos_Fortes>
    - <Caminhos_Aperfeiçoamento>...</Caminhos_Aperfeiçoamento>

    Args:
        cursor: Cursor do banco de dados.
        user_id (int): ID do usuário.

    Returns:
        str: Uma string formatada em Markdown com a análise completa.
    """
    try:
        # 1. Buscar dados do usuário primeiro
        cursor.execute("""
            SELECT u.nome, u.email, u.empresa 
            FROM usuarios u 
            WHERE u.user_id = ?
        """, (user_id,))
        usuario_info = cursor.fetchone()
        
        # 2. Encontrar o gráfico de resultados DISC - busca mais ampla
        tabela = st.session_state.tabela_escolhida
        
        # Primeiro tenta buscar por diferentes títulos possíveis
        titulos_busca = [
            '%RESULTADOS DE PERFIS%',
            '%PESQUISA COMPORTAMENTAL%', 
            '%COMPORTAMENTAL%',
            '%PERFIL%',
            '%DISC%'
        ]
        
        result = None
        titulo_grafico_usado = ""
        for titulo in titulos_busca:
            cursor.execute(f"""
                SELECT select_element, str_element, msg_element
                FROM {tabela}
                WHERE user_id = ? AND type_element = 'grafico' AND msg_element LIKE ?
                LIMIT 1
            """, (user_id, titulo))
            result = cursor.fetchone()
            if result and result[0] and result[1]:
                titulo_grafico_usado = titulo
                break
        
        # Se não encontrou por título, busca qualquer gráfico com 4 elementos (D,I,S,C)
        if not result or not result[0] or not result[1]:
            cursor.execute(f"""
                SELECT select_element, str_element, msg_element
                FROM {tabela}
                WHERE user_id = ? AND type_element = 'grafico'
                AND select_element IS NOT NULL 
                AND str_element IS NOT NULL
                AND LENGTH(select_element) - LENGTH(REPLACE(select_element, '|', '')) = 3
                LIMIT 1
            """, (user_id,))
            result = cursor.fetchone()
            titulo_grafico_usado = "Gráfico com 4 elementos encontrado"
        
        if not result or not result[0] or not result[1]:
            # Se ainda não encontrou, busca todos os elementos disponíveis para debug
            cursor.execute(f"""
                SELECT name_element, value_element, msg_element
                FROM {tabela}
                WHERE user_id = ? AND value_element IS NOT NULL
                ORDER BY name_element
                LIMIT 10
            """, (user_id,))
            elementos_debug = cursor.fetchall()
            
            debug_info = "<br>".join([f"- {elem[0]}: {elem[1]} ({elem[2] or 'sem título'})" for elem in elementos_debug])
            
            return f"""
            ## ⚠️ Análise DISC não disponível
            
            ### 👤 Informações do Usuário:
            **Nome:** {usuario_info[0] if usuario_info and usuario_info[0] else 'Não informado'}<br>
            **Email:** {usuario_info[1] if usuario_info and usuario_info[1] else 'Não informado'}<br>
            **Empresa:** {usuario_info[2] if usuario_info and usuario_info[2] else 'Não informado'}
            
            ### 📊 Problema encontrado:
            Não foi possível localizar o gráfico DISC na tabela `{tabela}` para o usuário {user_id}.
            
            ### 🔍 Elementos encontrados na tabela:
            {debug_info if debug_info else "Nenhum elemento encontrado"}
            
            **Solução:** Verifique se os dados DISC foram calculados corretamente ou se a configuração do gráfico está presente na tabela `{tabela}`.
            """

        name_elements = [name.strip() for name in result[0].split('|')]
        labels = [label.strip() for label in result[1].split('|')]
        titulo_grafico = result[2] if result[2] else "Gráfico DISC"
        
        # Cria mapeamento baseado nos rótulos DISC
        profile_map = {}
        for name, label in zip(name_elements, labels):
            # Procura pela letra DISC nos parênteses primeiro
            if '(' in label and ')' in label:
                letra_parenteses = label[label.find('(')+1:label.find(')')].upper()
                if letra_parenteses in ['D', 'I', 'S', 'C']:
                    profile_map[name] = letra_parenteses
            else:
                # Fallback: primeira letra do label
                first_letter = label[0].upper() if label else ''
                if first_letter in ['D', 'I', 'S', 'C']:
                    profile_map[name] = first_letter

        # Debug temporário: Vamos ver o mapeamento atual
        st.write("🔍 **Debug - Mapeamento encontrado:**")
        st.write(f"name_elements: {name_elements}")
        st.write(f"labels: {labels}")
        st.write(f"profile_map: {profile_map}")
        st.write("---")

        # 3. Obter os valores DISC do usuário
        placeholders = ','.join('?' for _ in name_elements)
        cursor.execute(f"""
            SELECT name_element, value_element
            FROM {tabela}
            WHERE user_id = ? AND name_element IN ({placeholders})
        """, (user_id, *name_elements))
        resultados_disc_raw = cursor.fetchall()
        
        if not resultados_disc_raw:
            return f"""
            ## ⚠️ Dados DISC não encontrados
            
            ### 👤 Informações do Usuário:
            **Nome:** {usuario_info[0] if usuario_info and usuario_info[0] else 'Não informado'}<br>
            **Email:** {usuario_info[1] if usuario_info and usuario_info[1] else 'Não informado'}<br>
            **Empresa:** {usuario_info[2] if usuario_info and usuario_info[2] else 'Não informado'}
            
            ### 📊 Problema:
            Encontrado gráfico "{titulo_grafico}" mas não há valores calculados para os elementos: {', '.join(name_elements)}
            
            **Solução:** Complete a avaliação DISC para gerar os resultados.
            """

        perfil = {profile_map.get(name, name): float(value if value is not None else 0.0) for name, value in resultados_disc_raw}
        perfil = {k: v for k, v in perfil.items() if k}  # Remove chaves vazias

        if len(perfil) < 2:
            return f"""
            ## ⚠️ Dados DISC insuficientes
            
            ### 👤 Informações do Usuário:
            **Nome:** {usuario_info[0] if usuario_info and usuario_info[0] else 'Não informado'}<br>
            **Email:** {usuario_info[1] if usuario_info and usuario_info[1] else 'Não informado'}<br>
            **Empresa:** {usuario_info[2] if usuario_info and usuario_info[2] else 'Não informado'}
            
            ### 📊 Dados encontrados:
            {', '.join([f'{k}: {v}' for k, v in perfil.items()])}
            
            **Problema:** Apenas {len(perfil)} perfis encontrados. Necessário pelo menos 2 para análise.
            """

        # 4. Ler e parsear a base de conhecimento
        try:
            with open('base_conhecimento_disc.md', 'r', encoding='utf-8') as f:
                base_conhecimento = f.read()
        except FileNotFoundError:
            st.error("Arquivo 'base_conhecimento_disc.md' não encontrado.")
            return "Análise não disponível: arquivo de conhecimento ausente."

        secoes = {}
        tags = {
            "individuais": ("<Perfis_Individuais>", "</Perfis_Individuais>"),
            "combinados": ("<Perfis_Combinados>", "</Perfis_Combinados>"),
            "excesso": ("<Excesso_Pontos_Fortes>", "</Excesso_Pontos_Fortes>"),
            "aperfeicoamento": ("<Caminhos_Aperfeiçoamento>", "</Caminhos_Aperfeiçoamento>")
        }
        for nome, (inicio_tag, fim_tag) in tags.items():
            inicio = base_conhecimento.find(inicio_tag)
            fim = base_conhecimento.find(fim_tag, inicio)
            if inicio != -1 and fim != -1:
                secoes[nome] = base_conhecimento[inicio + len(inicio_tag):fim].strip()
            else:
                secoes[nome] = ""

        # 5. Definir perfis primário e secundário
        perfil_ordenado = sorted(perfil.items(), key=lambda item: item[1], reverse=True)
        perfil_primario, valor_primario = perfil_ordenado[0]
        perfil_secundario, valor_secundario = perfil_ordenado[1] if len(perfil_ordenado) > 1 else ('', 0)

        # 6. Helper para extrair conteúdo
        def extrair_conteudo(secao_texto, chaves_busca):
            for chave in chaves_busca:
                inicio = secao_texto.find(chave)
                if inicio != -1:
                    fim = secao_texto.find('###', inicio + len(chave))
                    conteudo_bloco = secao_texto[inicio:fim if fim != -1 else len(secao_texto)].strip()
                    # Retorna o conteúdo APÓS a linha de chave (ex: "### D")
                    return conteudo_bloco.split('\n', 1)[1].strip() if '\n' in conteudo_bloco else ""
            return ""

        def formatar_tabela_html(raw_text, title):
            """
            Formata um texto com estrutura de tabela (cabeçalho e linhas separadas
            por quebras de linha, colunas por '|') em uma tabela HTML estilizada.
            """
            if not raw_text or '|' not in raw_text:
                return f"<h4>{title}</h4><p>{raw_text}</p>" if raw_text else ""

            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            if not lines or len(lines) < 2:
                return f"<h4>{title}</h4><p>{raw_text}</p>"

            header_cols = [h.strip() for h in lines[0].split('|')]
            if not header_cols:
                return f"<h4>{title}</h4><p>{raw_text}</p>"

            html = f"<br><h4>{title}</h4>"
            html += "<div style='font-size: 16px; width: 95%; margin: 0 auto;'>"
            html += "<table style='width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 0 8px rgba(0,0,0,0.1);'>"
            
            html += "<thead><tr style='background-color: #e8f5e9;'>"
            for col_title in header_cols:
                html += f"<th style='text-align: left; padding: 12px; border-bottom: 2px solid #dee2e6;'>{col_title}</th>"
            html += "</tr></thead>"
            
            html += "<tbody>"
            row_data = lines[1:]
            for i, row_str in enumerate(row_data):
                cols = [c.strip() for c in row_str.split('|')]
                if len(cols) == len(header_cols):
                    bg_color_style = "background-color: #f8f9fa;" if i % 2 else "background-color: #ffffff;"
                    html += f"<tr style='{bg_color_style}'>"
                    for col_data in cols:
                        html += f"<td style='padding: 10px 12px; border-bottom: 1px solid #dee2e6;'>{col_data}</td>"
                    html += "</tr>"
            html += "</tbody></table></div>"
            return html

        # ===== INÍCIO DA MONTAGEM DA ANÁLISE =====
        
        # CABEÇALHO PRINCIPAL
        analise = f"## 📊 Análise Comportamental DISC\n\n"
        
        # DADOS DO USUÁRIO
        analise += f"### 👤 Informações do Participante\n\n"
        if usuario_info:
            analise += f"""
            <div style='background-color: #f0f8ff; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #0066cc;'>
                <p style='margin: 0; font-size: 16px;'>
                    <strong>👤 Nome:</strong> {usuario_info[0] or 'Não informado'}<br>
                    <strong>📧 Email:</strong> {usuario_info[1] or 'Não informado'}<br>
                    <strong>🏢 Empresa:</strong> {usuario_info[2] or 'Não informado'}
                </p>
            </div>
            """
        
        # DADOS DA AVALIAÇÃO - Tabela com pontuações
        analise += f"### 📈 Resultados da sua Avaliação DISC\n\n"
        analise += f"*Baseado no gráfico: {titulo_grafico}* | *Busca: {titulo_grafico_usado}*\n\n"
        
        # Criar tabela HTML com os resultados
        dados_avaliacao = f"""
        <div style='font-size: 16px; width: 90%; margin: 20px auto;'>
            <table style='width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 0 8px rgba(0,0,0,0.1);'>
                <thead>
                    <tr style='background-color: #e3f2fd;'>
                        <th style='text-align: center; padding: 12px; border-bottom: 2px solid #1976d2; color: #1976d2; font-weight: bold;'>Perfil DISC</th>
                        <th style='text-align: center; padding: 12px; border-bottom: 2px solid #1976d2; color: #1976d2; font-weight: bold;'>Pontuação</th>
                        <th style='text-align: center; padding: 12px; border-bottom: 2px solid #1976d2; color: #1976d2; font-weight: bold;'>Posição</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Adicionar linhas da tabela ordenadas por pontuação
        nomes_perfis = {'D': 'Dominante', 'I': 'Influente', 'S': 'Estável', 'C': 'Conforme'}
        for i, (letra, valor) in enumerate(perfil_ordenado):
            if i == 0:
                destaque = "background-color: #fff3e0; font-weight: bold; color: #f57c00;"
                posicao = "1º - Primário"
            elif i == 1:
                destaque = "background-color: #f3e5f5; font-weight: bold; color: #7b1fa2;"
                posicao = "2º - Secundário"
            else:
                destaque = "background-color: #f5f5f5;"
                posicao = f"{i+1}º"
            
            nome_completo = nomes_perfis.get(letra, letra)
            
            dados_avaliacao += f"""
                    <tr style='{destaque}'>
                        <td style='text-align: center; padding: 10px 12px; border-bottom: 1px solid #dee2e6;'>{letra} - {nome_completo}</td>
                        <td style='text-align: center; padding: 10px 12px; border-bottom: 1px solid #dee2e6;'>{valor:.1f}</td>
                        <td style='text-align: center; padding: 10px 12px; border-bottom: 1px solid #dee2e6;'>{posicao}</td>
                    </tr>
            """
        
        dados_avaliacao += """
                </tbody>
            </table>
        </div>
        """
        
        analise += dados_avaliacao
        
        # Resumo do perfil identificado
        analise += f"""
        <div style='background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 10px; border-left: 5px solid #007bff;'>
            <h4 style='color: #007bff; margin: 0 0 10px 0;'>🎯 Seu Perfil Identificado</h4>
            <p style='font-size: 18px; margin: 0; color: #495057;'>
                <strong>Perfil Principal:</strong> {perfil_primario} - {nomes_perfis.get(perfil_primario, perfil_primario)} ({valor_primario:.1f} pontos)<br>
                {f"<strong>Perfil Secundário:</strong> {perfil_secundario} - {nomes_perfis.get(perfil_secundario, perfil_secundario)} ({valor_secundario:.1f} pontos)<br>" if perfil_secundario else ""}
                <strong>Combinação:</strong> {perfil_primario}{f"/{perfil_secundario}" if perfil_secundario else ""}
            </p>
        </div>
        """
        
        analise += "\n---\n\n"
        
        # ===== BLOCO 1: ANÁLISE DO PERFIL =====
        analise += f"## 🔍 BLOCO 1 - Análise do Perfil\n\n"
        
        # Perfil Combinado
        if perfil_secundario:
            chaves_combinado = [f"### {perfil_primario}/{perfil_secundario} -", f"### {perfil_secundario}/{perfil_primario} -"]
            desc_combinado = extrair_conteudo(secoes.get("combinados", ""), chaves_combinado)

            if desc_combinado:
                analise += f"### 🤝 Perfil Combinado: {perfil_primario}/{perfil_secundario}\n\n"
                analise += f"{desc_combinado}\n\n"
        
        # Perfil Individual (com pontos fortes e limitações)
        conteudo_individual_raw = extrair_conteudo(secoes.get("individuais", ""), [f"### Perfil {perfil_primario} -"])
        desc_individual, pontos_fortes_html, limitacoes_html = "", "", ""
        
        if conteudo_individual_raw:
            # Extrair descrição principal
            inicio_fortes = conteudo_individual_raw.find('- **Pontos Fortes:**')
            desc_individual = conteudo_individual_raw[:inicio_fortes if inicio_fortes != -1 else len(conteudo_individual_raw)].strip()
            
            analise += f"### 👤 Características do seu Perfil Principal: {perfil_primario}\n\n"
            analise += f"{desc_individual}\n\n"
            
            # Extrair pontos fortes
            if inicio_fortes != -1:
                inicio_limit = conteudo_individual_raw.find('- **Limitações:**', inicio_fortes)
                fortes_raw = conteudo_individual_raw[inicio_fortes:inicio_limit if inicio_limit != -1 else len(conteudo_individual_raw)]
                fortes_raw = fortes_raw.replace('- **Pontos Fortes:**', '').strip()
                fortes_lista = [f"<li>{item.strip()}</li>" for item in fortes_raw.split(',') if item.strip()]
                pontos_fortes_html = f"<h4>✅ Pontos Fortes ({perfil_primario})</h4><ul>{''.join(fortes_lista)}</ul>"

            # Extrair limitações
            if inicio_limit != -1:
                limitacoes_raw = conteudo_individual_raw[inicio_limit:].replace('- **Limitações:**', '').strip()
                limitacoes_lista = [f"<li>{item.strip()}</li>" for item in limitacoes_raw.split(',') if item.strip()]
                limitacoes_html = f"<h4>⚠️ Limitações a observar ({perfil_primario})</h4><ul>{''.join(limitacoes_lista)}</ul>"

            # Adicionar pontos fortes e limitações
            if pontos_fortes_html:
                analise += f"{pontos_fortes_html}\n\n"

            if limitacoes_html:
                analise += f"{limitacoes_html}\n\n"
        
        analise += "\n---\n\n"
        
        # ===== BLOCO 2: ANÁLISE DO COMPORTAMENTO =====
        analise += f"## 🎭 BLOCO 2 - Análise do Comportamento\n\n"
        analise += f"*Esta seção será desenvolvida na próxima etapa...*\n\n"
        
        # Extrair e formatar seções de Excesso e Aperfeiçoamento (temporariamente comentado)
        # desc_excesso_raw = extrair_conteudo(secoes.get("excesso", ""), [f"### {perfil_primario}"])
        # desc_aperfeicoamento_raw = extrair_conteudo(secoes.get("aperfeicoamento", ""), [f"### {perfil_primario}"])
        # html_excesso = formatar_tabela_html(desc_excesso_raw, "Quando seus Pontos Fortes são usados em Excesso")
        # html_aperfeicoamento = formatar_tabela_html(desc_aperfeicoamento_raw, "Caminhos para o Aperfeiçoamento e Desenvolvimento")
        
        # if html_excesso:
        #     analise += f"{html_excesso}\n\n"
        # if html_aperfeicoamento:
        #     analise += f"{html_aperfeicoamento}\n\n"

        # Validação final
        if not any([desc_combinado if perfil_secundario else True, desc_individual]):
            analise += f"⚠️ **Observação:** Algumas seções da análise podem estar incompletas devido à estrutura do arquivo de conhecimento."

        return analise

    except Exception as e:
        traceback.print_exc()
        return f"Ocorreu um erro inesperado ao gerar a análise DISC: {str(e)}"

if __name__ == "__main__":
    show_results()

