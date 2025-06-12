# resultados.py
# Data: 13/05/2025 08:35
# Pagina de resultados - Dashboard
# rotina das Simulações, tabelas: forms_resultados


# type: ignore
# pylance: disable=reportMissingModuleSource

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
from datetime import date
import io
import tempfile
import matplotlib.pyplot as plt
import traceback
from paginas.monitor import registrar_acesso
from paginas.form_model_recalc import verificar_dados_usuario, calculate_formula, atualizar_formulas
import time

from config import DB_PATH  # Adicione esta importação

# Dicionário de títulos para cada tabela
TITULOS_TABELAS = {
    "forms_resultados": "Análise: Avaliação de Perfis",
    "forms_result_sea": "Simulador da Pegada de Carbono"
}

# Dicionário de subtítulos para cada tabela
SUBTITULOS_TABELAS = {
    "forms_resultados": "Avaliação de Perfis",
    "forms_result_sea": "Simulações da Empresa"
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
        
        # Define a cor das barras
        cor = section if section else '#1f77b4'  # azul padrão se não houver cor definida
        cores = [cor] * len(valores)  # aplica a mesma cor para todas as barras
        
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
        
        # Cria o gráfico usando plotly express
        fig = px.bar(
            x=labels,
            y=valores,
            title=None,  # Remove título do plotly pois já usamos markdown
            color_discrete_sequence=cores
        )
        
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
                tickfont=dict(size=16),  # aumentado em 30%
            ),
            # Configuração do eixo Y
            yaxis=dict(
                tickfont=dict(size=18),  # aumentado em 30%
                tickformat=",.",  # formato dos números
                separatethousands=True  # separador de milhar
            ),
            # Desativa o hover (tooltip ao passar o mouse)
            hovermode=False
        )
        
        # Exibe o gráfico no Streamlit
        # config={'displayModeBar': False} remove a barra de ferramentas do Plotly
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
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
        cor = section if section else '#1f77b4'
        cores = [cor] * len(valores)
        # Ajustar base_width para ocupar mais da largura da página A4
        base_width = 250
        base_height = 180
        # largura dos gráficos igual à tabela (usando width_pct)
        adj_width = int(base_width * 2.2 * 0.8 * (width_pct / 100)) + 20  # aumenta 20 na largura
        adj_height = int(base_height * (height_pct / 100)) - 25           # reduz 25 na altura
        fig = px.bar(
            x=labels,
            y=valores,
            title=None,
            color_discrete_sequence=cores
        )
        fig.update_layout(
            showlegend=False,
            height=adj_height,
            width=adj_width,
            margin=dict(t=30, b=50),
            xaxis=dict(
                title=None,
                tickfont=dict(size=16)  # aumentado em 30%
            ),
            yaxis=dict(
                title=None,
                tickfont=dict(size=18),  # aumentado em 30%
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
    Função específica para gerar o conteúdo do PDF usando uma conexão dedicada
    Novo layout: título, subtítulo, tabela centralizada, 4 gráficos em 2 linhas (2x2)
    """
    try:
        # Configurações de dimensões (em percentual)
        TABLE_HEIGHT_PCT = 25
        TABLE_WIDTH_PCT = 60
        GRAPH_HEIGHT_PCT = 100
        GRAPH_WIDTH_PCT = 100
        base_width = 250  # largura individual de cada gráfico/tabela
        base_height = 180 # altura individual de cada gráfico
        table_width = base_width * 2.2 * 0.8  # reduz 20% da largura da tabela
        table_height = base_height * (TABLE_HEIGHT_PCT / 100)
        graph_width = table_width  # gráficos agora têm a mesma largura da tabela
        graph_height = base_height

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

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=26,
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=26,
                spaceBefore=15,
                spaceAfter=20,
                borderRadius=5,
                backColor=colors.white,
                borderPadding=10
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=20,
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=24,
                spaceBefore=10,
                spaceAfter=15
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
                ('BOTTOMPADDING', (0, 0), (-1, 0), 16),  # cabeçalho
                ('TOPPADDING', (0, 1), (-1, -1), 12),    # corpo
                ('BOTTOMPADDING', (0, 1), (-1, -1), 12), # corpo
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROUNDEDCORNERS', [3, 3, 3, 3]),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
            ])

            # Estilo para títulos dos gráficos (aumentado em 30%)
            graphic_title_style = ParagraphStyle(
                'GraphicTitle',
                parent=styles['Heading2'],
                fontSize=18,  # aumentado em 30%
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=16,
                spaceBefore=6,
                spaceAfter=8
            )

            titulo_principal = TITULOS_TABELAS.get(tabela_escolhida, "Análise")
            subtitulo_principal = SUBTITULOS_TABELAS.get(tabela_escolhida, "Análises")
            elements.append(Paragraph(titulo_principal, title_style))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(subtitulo_principal, subtitle_style))
            elements.append(Spacer(1, 20))

            # Buscar elementos da tabela e gráficos
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

            # Pega a primeira tabela e até 4 gráficos
            tabela = next((e for e in elementos if e[1] == 'tabela'), None)
            graficos = [e for e in elementos if e[1] == 'grafico'][:4]

            # --- ORGANIZAÇÃO DAS PÁGINAS DO PDF ---
            # Identificar os gráficos pelos títulos
            graficos_dict = {}
            for grafico in graficos:
                # Por padrão, altura 160 (será ajustada por página)
                dados_grafico = gerar_dados_grafico(pdf_cursor, grafico, tabela_escolhida, height_pct=160, width_pct=100)
                if dados_grafico:
                    graficos_dict[dados_grafico['title']] = Table(
                        [[Paragraph(dados_grafico['title'], graphic_title_style)], [dados_grafico['image']]],
                        colWidths=[graph_width],
                        style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                    )

            # --- DIFERENCIAÇÃO DE LAYOUT POR TABELA ---
            if tabela_escolhida in ["forms_resultados", "forms_result_sea"]:
                # Layout padrão: Tabela + gráficos
                if tabela:
                    dados_tabela = gerar_dados_tabela(pdf_cursor, tabela, height_pct=TABLE_HEIGHT_PCT, width_pct=TABLE_WIDTH_PCT)
                    if dados_tabela:
                        t = Table(dados_tabela['data'], colWidths=[table_width * 0.6, table_width * 0.4])
                        t.setStyle(table_style)
                        elements.append(Table([[t]], colWidths=[table_width], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                        for _ in range(5):
                            elements.append(Spacer(1, 12))
                # Gráfico Demanda de Água com altura reduzida em 25%
                if 'Demanda de Água (m³/1000kg de café)' in graficos_dict:
                    grafico_agua = next((g for g in graficos if 'Demanda de Água' in g[3]), None)
                    if grafico_agua:
                        dados_grafico_agua = gerar_dados_grafico(pdf_cursor, grafico_agua, tabela_escolhida, height_pct=120, width_pct=100)
                        elements.append(Table(
                            [[Paragraph(dados_grafico_agua['title'], graphic_title_style)], [dados_grafico_agua['image']]],
                            colWidths=[graph_width],
                            style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                        ))
                elements.append(PageBreak())

                # Página 2: Demanda de Água, Pegada de Carbono e Resíduos Sólidos (todos juntos, altura reduzida)
                titulos_graficos_p2 = [
                    'Demanda de Água (litros / 1000kg de café)',
                    'Pegada de Carbono (kg CO2eq/1000 kg de café)'
                ]
                residuos_key = next((k for k in graficos_dict if 'resíduo' in k.lower()), None)
                if residuos_key:
                    titulos_graficos_p2.append(residuos_key)
                for titulo in titulos_graficos_p2:
                    grafico = next((g for g in graficos if titulo in g[3]), None)
                    if grafico:
                        dados_grafico = gerar_dados_grafico(pdf_cursor, grafico, tabela_escolhida, height_pct=120, width_pct=100)
                        elements.append(Table(
                            [[Paragraph(dados_grafico['title'], graphic_title_style)], [dados_grafico['image']]],
                            colWidths=[graph_width],
                            style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                        ))
                        elements.append(Spacer(1, 10))
            else:
                # Layout setorial: só gráficos, 2 por página
                # Página 1: Demanda de Água
                palavras_chave_p1 = ["água"]
                graficos_p1 = []
                for palavra in palavras_chave_p1:
                    grafico = next((g for g in graficos if palavra in g[3].lower()), None)
                    if grafico:
                        dados_grafico = gerar_dados_grafico(pdf_cursor, grafico, tabela_escolhida, height_pct=120, width_pct=100)
                        graficos_p1.append(Table(
                            [[Paragraph(dados_grafico['title'], graphic_title_style)], [dados_grafico['image']]],
                            colWidths=[graph_width],
                            style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                        ))
                        graficos_p1.append(Spacer(1, 10))
                for g in graficos_p1:
                    elements.append(g)
                elements.append(PageBreak())
                # Página 2: Pegada de Carbono e Resíduos Sólidos
                palavras_chave_p2 = ["carbono", "resíduo"]
                graficos_p2 = []
                for palavra in palavras_chave_p2:
                    grafico = next((g for g in graficos if palavra in g[3].lower()), None)
                    if grafico:
                        dados_grafico = gerar_dados_grafico(pdf_cursor, grafico, tabela_escolhida, height_pct=120, width_pct=100)
                        graficos_p2.append(Table(
                            [[Paragraph(dados_grafico['title'], graphic_title_style)], [dados_grafico['image']]],
                            colWidths=[graph_width],
                            style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                        ))
                        graficos_p2.append(Spacer(1, 10))
                for g in graficos_p2:
                    elements.append(g)

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
            
        # 1. Verifica se usuário tem dados em forms_tab
        verificar_dados_usuario(cursor, user_id)
        
        # 2. Atualiza todas as fórmulas e verifica o resultado
        if not atualizar_formulas(cursor, user_id):
            st.error("Erro ao atualizar fórmulas!")
            return

        # 3. Verifica/inicializa dados na tabela escolhida
        new_user(cursor, user_id, tabela_escolhida)
        conn.commit()
        
        # 4. Registra acesso à página
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
        with st.expander("Clique aqui para ver sua Análise de Perfil DISC Completa", expanded=False):
            st.markdown("---")
            analise_texto = analisar_perfil_disc(cursor, user_id)
            st.markdown(analise_texto, unsafe_allow_html=True)
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

def analisar_perfil_disc(cursor, user_id):
    """
    Realiza uma análise completa do perfil DISC do usuário, buscando dinamicamente
    os dados a partir da configuração do gráfico de resultados.

    Args:
        cursor: Cursor do banco de dados.
        user_id (int): ID do usuário.

    Returns:
        str: Uma string formatada em Markdown com a análise completa.
    """
    try:
        # 1. Encontrar o gráfico de resultados DISC para obter os name_elements corretos
        tabela = st.session_state.tabela_escolhida
        cursor.execute(f"""
            SELECT select_element, str_element
            FROM {tabela}
            WHERE user_id = ? AND type_element = 'grafico' AND msg_element LIKE '%PESQUISA COMPORTAMENTAL%'
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()

        if not result or not result[0] or not result[1]:
            return "Análise não disponível: A configuração do gráfico 'PESQUISA COMPORTAMENTAL' não foi encontrada no banco de dados."

        name_elements_str, labels_str = result
        name_elements = [name.strip() for name in name_elements_str.split('|')]
        labels = [label.strip() for label in labels_str.split('|')]

        # 2. Mapear os name_elements para as letras do perfil (D, I, S, C)
        profile_map = {name: label[0].upper() for name, label in zip(name_elements, labels)}

        # 3. Obter os valores DISC do usuário usando os name_elements encontrados
        placeholders = ','.join('?' for _ in name_elements)
        cursor.execute(f"""
            SELECT name_element, value_element
            FROM {tabela}
            WHERE user_id = ? AND name_element IN ({placeholders})
        """, (user_id, *name_elements))
        
        resultados_disc_raw = cursor.fetchall()

        if not resultados_disc_raw:
            return "Não foram encontrados resultados DISC para este usuário."

        # 4. Construir o dicionário de perfil (e.g., {'D': 12.0, 'I': 9.0, ...})
        perfil = {}
        for name, value in resultados_disc_raw:
            if name in profile_map:
                profile_letter = profile_map[name]
                perfil[profile_letter] = float(value) if value is not None else 0.0
        
        if len(perfil) < 4:
            return "Dados para a análise DISC estão incompletos."

        # 5. Ler a base de conhecimento
        try:
            with open('base_conhecimento_disc.md', 'r', encoding='utf-8') as f:
                base_conhecimento = f.read()
        except FileNotFoundError:
            return "Arquivo 'base_conhecimento_disc.md' não encontrado. Análise não pode ser gerada."

        # 6. Gerar a análise com base no perfil e na base de conhecimento
        perfil_ordenado = sorted(perfil.items(), key=lambda item: item[1], reverse=True)
        perfil_primario, _ = perfil_ordenado[0]
        perfil_secundario, _ = perfil_ordenado[1]

        analise = f"## Análise Comportamental DISC\n\n"
        analise += f"### Seu Perfil: **{perfil_primario}/{perfil_secundario}**\n\n"

        # Extrai a descrição do perfil combinado
        perfil_combinado_key = f"### {perfil_primario}/{perfil_secundario} - "
        perfil_combinado_key_alt = f"### {perfil_secundario}/{perfil_primario} - "

        inicio_desc = base_conhecimento.find(perfil_combinado_key)
        if inicio_desc == -1:
            inicio_desc = base_conhecimento.find(perfil_combinado_key_alt)

        if inicio_desc != -1:
            fim_desc = base_conhecimento.find('###', inicio_desc + len(perfil_combinado_key))
            if fim_desc == -1: # if not found, find next major section
                fim_desc = base_conhecimento.find('##', inicio_desc + len(perfil_combinado_key))
            if fim_desc == -1: # if still not found, go to end of file
                fim_desc = len(base_conhecimento)
            
            secao_completa = base_conhecimento[inicio_desc:fim_desc].strip()
            descricao = secao_completa.split('\n', 1)[1] if '\n' in secao_completa else ''
            analise += f"{descricao}\n\n"
        else:
            # Fallback for individual profile
            inicio_desc_individual = base_conhecimento.find(f"### Perfil {perfil_primario} - ")
            if inicio_desc_individual != -1:
                fim_desc_individual = base_conhecimento.find('###', inicio_desc_individual + 1)
                secao_completa = base_conhecimento[inicio_desc_individual:fim_desc_individual].strip()
                descricao = secao_completa.split('\n', 1)[1] if '\n' in secao_completa else ''
                analise += f"**Perfil Principal: {perfil_primario}**\n{descricao}\n\n"

        # Adicionar pontos fortes e limitações do perfil primário
        inicio_secao_primario = base_conhecimento.find(f"### Perfil {perfil_primario} - ")
        if inicio_secao_primario != -1:
            fim_secao_primario = base_conhecimento.find('###', inicio_secao_primario + 1)
            if fim_secao_primario == -1:
                 fim_secao_primario = len(base_conhecimento)
            secao_primario_texto = base_conhecimento[inicio_secao_primario:fim_secao_primario]

            # Pontos Fortes
            inicio_fortes = secao_primario_texto.find(f'- **Pontos Fortes:**')
            if inicio_fortes != -1:
                fim_fortes = secao_primario_texto.find('- **Limitações:**', inicio_fortes)
                fortes_raw = secao_primario_texto[inicio_fortes:fim_fortes].replace("- **Pontos Fortes:**", "").strip()
                fortes_lista = [f"<li>{item.strip()}</li>" for item in fortes_raw.split(',') if item.strip()]
                analise += f"#### Pontos Fortes do seu perfil principal ({perfil_primario}):\n"
                analise += f"<ul>{''.join(fortes_lista)}</ul>\n"

            # Limitações
            inicio_limit = secao_primario_texto.find(f'- **Limitações:**')
            if inicio_limit != -1:
                limitacoes_raw = secao_primario_texto[inicio_limit:].replace("- **Limitações:**", "").strip()
                limitacoes_lista = [f"<li>{item.strip()}</li>" for item in limitacoes_raw.split(',') if item.strip()]
                analise += f"#### Limitações a observar ({perfil_primario}):\n"
                analise += f"<ul>{''.join(limitacoes_lista)}</ul>\n"
        
        return analise

    except Exception as e:
        traceback.print_exc() # Printar traceback no terminal para debug
        return f"Ocorreu um erro inesperado ao gerar a análise DISC: {str(e)}"

if __name__ == "__main__":
    show_results()

