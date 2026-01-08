# resultados_01.py
# Data: 05/12/2025
# Pagina de resultados e Analises - Dashboard.
# Tabela: forms_resultados_01
# Assessment: DISC Essencial

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
from paginas.monitor import registrar_acesso
import time

from config import DB_PATH  # Adicione esta importação

# Dicionário de títulos para cada tabela
TITULOS_TABELAS = {
    "forms_resultados_01": "Análise: DISC Essencial"
}

# Dicionário de subtítulos para cada tabela
SUBTITULOS_TABELAS = {
    "forms_resultados_01": "Análise: DISC Essencial"
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
    Busca dados na tabela forms_tab_01 e atualiza o value_element do registro atual.
    
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
            # Usar a tabela de origem baseada na tabela de destino
            tabela_origem = tabela_destino.replace("forms_resultados", "forms_tab")
            
            
            cursor.execute(f"""
                SELECT CAST(value_element AS DECIMAL(20, 8))
                FROM {tabela_origem} 
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
                st.warning(f"Valor não encontrado na tabela {tabela_origem} para {str_value} (user_id: {user_id})")
                
    except Exception as e:
        st.error(f"Erro ao processar call_dados: {str(e)}")

def grafico_barra(cursor, element):
    """
    Cria um gráfico de pizza (pie/donut) com dados da tabela específica.
    
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
        - Gráfico de pizza (donut chart) com hole=0.3
        - Altura fixa de 400px
        - Largura responsiva
        - Sem legenda (rótulos e percentuais no gráfico)
        - Fonte tamanho 14px para rótulos
        - Cores DISC definidas automaticamente
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
        
        # Cria o gráfico de pizza usando Graph Objects para controle total das cores
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=valores,
                marker=dict(colors=cores),  # Define cores diretamente
                textinfo='label+percent',  # Mostra rótulo e percentual
                textfont=dict(size=14),  # Tamanho da fonte dos rótulos
                hole=0.3  # Cria um gráfico de rosca (donut chart) - pode ser 0 para pizza completa
            )
        ])
        
        # Configura o layout do gráfico
        fig.update_layout(
            # Remove legenda (os rótulos já aparecem no gráfico)
            showlegend=False,
            # Define dimensões
            height=400,
            width=None,  # largura responsiva
            # Centraliza o gráfico
            margin=dict(l=20, r=20, t=20, b=20),
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
    Cria uma tabela estilizada com dados da tabela forms_resultados_01.
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
                FROM forms_resultados_01 
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
        
        # Aumentar tamanho do gráfico em 50% + 30% (total 95% maior) para PDF
        adj_width = int(adj_width * 1.5 * 1.3)
        adj_height = int(adj_height * 1.5 * 1.3)
        
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=valores,
                marker=dict(colors=cores),  # Define cores diretamente
                textinfo='label+percent',  # Mostra rótulo e percentual
                textfont=dict(size=14),  # Tamanho da fonte dos rótulos para PDF (aumentado proporcionalmente ao gráfico)
                hole=0.3  # Cria um gráfico de rosca (donut chart) - pode ser 0 para pizza completa
            )
        ])
        fig.update_layout(
            showlegend=False,
            height=adj_height,  # altura já ajustada com aumento de 95% (50% + 30%)
            width=adj_width,   # largura já ajustada com aumento de 95% (50% + 30%)
            margin=dict(t=30, b=50, l=20, r=20),
            # Não precisa configurar eixos para gráfico de pizza
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
                            file_name="DISC_Essencial_Analise.pdf",
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
            rightMargin=50,
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
                    elements.append(Spacer(1, 20))

            # 5. ANÁLISE DETALHADA DO ASSESSMENT
            try:
                analise_texto = analisar_perfil_disc(pdf_cursor, user_id, tabela_escolhida)
                # Verificar se a análise retornou conteúdo válido (não apenas mensagem de erro)
                if analise_texto and not analise_texto.startswith("Análise não disponível"):
                    # Adicionar título da seção
                    elements.append(PageBreak())
                    elements.append(Paragraph("Análise Detalhada do Assessment", title_style))
                    elements.append(Spacer(1, 20))
                    
                    # Converter HTML/Markdown para texto simples para o PDF
                    # Remove tags HTML mas preserva estrutura básica
                    texto_limpo = analise_texto
                    # Remove tags HTML complexas mas preserva quebras de linha
                    texto_limpo = re.sub(r'<br\s*/?>', '\n', texto_limpo, flags=re.IGNORECASE)
                    texto_limpo = re.sub(r'</p>', '\n\n', texto_limpo, flags=re.IGNORECASE)
                    texto_limpo = re.sub(r'</div>', '\n', texto_limpo, flags=re.IGNORECASE)
                    texto_limpo = re.sub(r'<[^>]+>', '', texto_limpo)
                    # Remove emojis mas preserva pontuação básica
                    texto_limpo = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\/\n\r\'\"]', '', texto_limpo)
                    # Normaliza quebras de linha
                    texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
                    texto_limpo = texto_limpo.strip()
                    
                    # Dividir em parágrafos e adicionar ao PDF
                    paragrafos = [p.strip() for p in texto_limpo.split('\n\n') if p.strip() and len(p.strip()) > 10]
                    
                    # Estilos para diferentes níveis de texto
                    analise_style = ParagraphStyle(
                        'AnaliseStyle',
                        parent=styles['Normal'],
                        fontSize=10,
                        alignment=0,  # Justificado à esquerda
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica',
                        leading=12,
                        spaceBefore=6,
                        spaceAfter=6
                    )
                    
                    titulo_secao_style = ParagraphStyle(
                        'TituloSecaoStyle',
                        parent=styles['Heading2'],
                        fontSize=14,
                        alignment=0,
                        textColor=colors.HexColor('#1E1E1E'),
                        fontName='Helvetica-Bold',
                        leading=16,
                        spaceBefore=12,
                        spaceAfter=8
                    )
                    
                    for paragrafo in paragrafos:
                        if paragrafo:
                            # Identificar títulos (linhas curtas ou que começam com ##)
                            if paragrafo.startswith('##') or (len(paragrafo) < 80 and paragrafo.isupper()):
                                # É um título
                                titulo_limpo = paragrafo.replace('##', '').strip()
                                if titulo_limpo:
                                    elements.append(Paragraph(titulo_limpo, titulo_secao_style))
                                    elements.append(Spacer(1, 8))
                            else:
                                # É um parágrafo normal
                                # Limitar tamanho do parágrafo para evitar problemas
                                if len(paragrafo) > 800:
                                    # Dividir parágrafos muito longos em frases
                                    frases = re.split(r'[.!?]\s+', paragrafo)
                                    for frase in frases:
                                        if frase.strip():
                                            elements.append(Paragraph(frase.strip() + '.', analise_style))
                                            elements.append(Spacer(1, 4))
                                else:
                                    elements.append(Paragraph(paragrafo, analise_style))
                                    elements.append(Spacer(1, 6))
            except Exception as e:
                # Se houver erro ao gerar a análise, continua sem ela
                print(f"Erro ao adicionar análise ao PDF: {str(e)}")
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
        with st.expander("Análise Detalhada do Assessment", expanded=True):
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

        # ===== PASSO 3: ANÁLISE DE PERFIL (ÚNICO, HÍBRIDO OU TRÍPLICE) - REGRA DOS 25 PONTOS =====
        
        st.markdown("---")
        st.markdown("### 🔍 Análise Comportamental Detalhada")
        
        # REGRA DOS 25 PONTOS: Contar dimensões com valor híbrido >= 25
        LIMITE_FORTE = 25.0
        dimensoes_fortes = [v for v in variaveis_hibridas if v['valor_hibrido'] >= LIMITE_FORTE]
        num_dimensoes_fortes = len(dimensoes_fortes)
        
        # Ordenar dimensões fortes por valor (maior para menor)
        dimensoes_fortes_ordenadas = sorted(dimensoes_fortes, key=lambda x: x['valor_hibrido'], reverse=True)
        
        # Determinar tipo de perfil baseado no número de dimensões fortes
        if num_dimensoes_fortes == 1:
            # PERFIL ÚNICO: Apenas uma dimensão possui 25 pontos ou mais
            tipo_perfil = "ÚNICO"
            primario = dimensoes_fortes_ordenadas[0]
            letra_primaria = primario['letra']
            
            # Mapear arquivo baseado no perfil primário
            arquivos_unicos = {
                'D': 'Conteudo/01/1_D_Dominancia.md',
                'I': 'Conteudo/01/1_I_Influencia.md', 
                'S': 'Conteudo/01/1_S_Estabilidade.md',
                'C': 'Conteudo/01/1_C_Conformidade.md'
            }
            
            arquivo_analise = arquivos_unicos.get(letra_primaria)
            titulo_analise = f"Perfil {tipo_perfil}: {primario['dimensao']}"
            
        elif num_dimensoes_fortes == 2:
            # PERFIL HÍBRIDO (DUPLO): Exatamente duas dimensões possuem 25 pontos ou mais
            tipo_perfil = "HÍBRIDO"
            primario = dimensoes_fortes_ordenadas[0]
            secundario = dimensoes_fortes_ordenadas[1]
            letra_primaria = primario['letra']
            letra_secundaria = secundario['letra']
            combinacao = f"{letra_primaria}{letra_secundaria}"
            
            # Mapear arquivo baseado na combinação
            arquivos_combinados = {
                'DC': 'Conteudo/01/21_DC_DOMINANCIA_CONFORMIDADE.md',
                'DI': 'Conteudo/01/22_DI_DOMINANCIA_INFLUENCIA.md',
                'ID': 'Conteudo/01/23_ID_INFLUENCIA_DOMINANCIA.md',
                'IS': 'Conteudo/01/24_IS_INFLUENCIA_ESTABILIDADE.md',
                'SI': 'Conteudo/01/25_SI_ESTABILIDADE_INFLUENCIA.md',
                'SC': 'Conteudo/01/26_SC_ESTABILIDADE_CONFORMIDADE.md',
                'CD': 'Conteudo/01/27_CD_CONFORMIDADE_DOMINANCIA.md',
                'CS': 'Conteudo/01/28_CS_CONFORMIDADE_ESTABILIDADE.md',
                'DS': 'Conteudo/01/29_DS_DOMINANCIA_ESTABILIDADE.md',
                'SD': 'Conteudo/01/30_SD_ESTABILIDADE_DOMINANCIA.md',
                'IC': 'Conteudo/01/31_IC_INFLUENCIA_CONFORMIDADE.md',
                'CI': 'Conteudo/01/32_CI_CONFORMIDADE_INFLUENCIA.md'
            }
            
            arquivo_analise = arquivos_combinados.get(combinacao)
            titulo_analise = f"Perfil {tipo_perfil}: {primario['dimensao']} + {secundario['dimensao']}"
            
        elif num_dimensoes_fortes == 3:
            # PERFIL TRÍPLICE: Três dimensões possuem 25 pontos ou mais
            tipo_perfil = "TRÍPLICE"
            primario = dimensoes_fortes_ordenadas[0]
            secundario = dimensoes_fortes_ordenadas[1]
            terciario = dimensoes_fortes_ordenadas[2]
            letra_primaria = primario['letra']
            letra_secundaria = secundario['letra']
            letra_terciaria = terciario['letra']
            
            # Criar combinação tríplice ordenada (P₁P₂P₃)
            combinacao_triplice = f"{letra_primaria}{letra_secundaria}{letra_terciaria}"
            
            # Mapear arquivo baseado na combinação tríplice
            arquivos_triplices = {
                'DSC': 'Conteudo/01/41_DSC_DOMINANCIA_ESTABILIDADE_CONFORMIDADE.md',
                'DIS': 'Conteudo/01/42_DIS_DOMINANCIA_INFLUENCIA_ESTABILIDADE.md',
                'ISC': 'Conteudo/01/43_ISC_INFLUENCIA_ESTABILIDADE_CONFORMIDADE.md',
                'DIC': 'Conteudo/01/44_DIC_DOMINANCIA_INFLUENCIA_CONFORMIDADE.md'
            }
            
            arquivo_analise = arquivos_triplices.get(combinacao_triplice)
            titulo_analise = f"Perfil {tipo_perfil}: {primario['dimensao']} + {secundario['dimensao']} + {terciario['dimensao']}"
        else:
            # Caso não haja dimensões fortes ou dados insuficientes
            tipo_perfil = "INDETERMINADO"
            arquivo_analise = None
            titulo_analise = "Dados insuficientes para análise"
            st.error("❌ **Dados insuficientes:** Não há dimensões com 25 pontos ou mais para análise comportamental.")
        
        # Exibir informações do tipo de perfil
        criterio_texto = ""
        if tipo_perfil == "ÚNICO":
            criterio_texto = "1 dimensão forte (≥ 25 pontos) = Perfil Único"
        elif tipo_perfil == "HÍBRIDO":
            criterio_texto = "2 dimensões fortes (≥ 25 pontos) = Perfil Híbrido"
        elif tipo_perfil == "TRÍPLICE":
            criterio_texto = "3 dimensões fortes (≥ 25 pontos) = Perfil Tríplice"
        else:
            criterio_texto = "Dados insuficientes"
        
        # Listar dimensões fortes para exibição
        dimensoes_fortes_texto = ", ".join([f"{d['letra']} ({d['valor_hibrido']:.1f})" for d in dimensoes_fortes_ordenadas])
        
        info_perfil_html = f"""
        <div style='background-color: #fff3cd; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #ffc107;'>
            <p style='margin: 0; font-size: 16px; color: #856404;'>
                    <strong>📊 Tipo de Perfil:</strong> {tipo_perfil}<br>
                    <strong>📈 Dimensões Fortes (≥ 25 pontos):</strong> {num_dimensoes_fortes}<br>
                    <strong>📋 Dimensões:</strong> {dimensoes_fortes_texto if dimensoes_fortes_texto else 'Nenhuma'}<br>
                    <strong>📋 Critério:</strong> {criterio_texto}
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
                # Warning específico para perfis tríplices
                if tipo_perfil == "TRÍPLICE":
                    # Usar as dimensões fortes ordenadas
                    if num_dimensoes_fortes >= 3:
                        combinacao_triplice = f"{dimensoes_fortes_ordenadas[0]['letra']}{dimensoes_fortes_ordenadas[1]['letra']}{dimensoes_fortes_ordenadas[2]['letra']}"
                    else:
                        combinacao_triplice = "N/A"
                    st.error("⚠️ **AVISO CRÍTICO PARA ADMINISTRADOR DA PLATAFORMA**")
                    st.error(f"❌ **Arquivo de perfil tríplice não encontrado:** {arquivo_analise}")
                    st.error(f"**Combinação detectada:** {combinacao_triplice}")
                    st.error("**AÇÃO NECESSÁRIA:** Criar o arquivo de conteúdo para este perfil tríplice na pasta 'Conteudo/01/' do projeto.")
                    st.error("**Impacto:** O usuário não receberá a análise completa do perfil tríplice até que o arquivo seja criado.")
                else:
                    st.error(f"❌ **Arquivo não encontrado:** {arquivo_analise}")
                    st.error("Verifique se o arquivo existe na pasta 'Conteudo' do projeto.")
            
            except Exception as e:
                st.error(f"❌ **Erro ao ler arquivo:** {str(e)}")
        else:
            # Combinação não encontrada
            if tipo_perfil == "TRÍPLICE":
                # Usar as dimensões fortes ordenadas
                if num_dimensoes_fortes >= 3:
                    combinacao_triplice = f"{dimensoes_fortes_ordenadas[0]['letra']}{dimensoes_fortes_ordenadas[1]['letra']}{dimensoes_fortes_ordenadas[2]['letra']}"
                else:
                    combinacao_triplice = "N/A"
                st.error("⚠️ **AVISO CRÍTICO PARA ADMINISTRADOR DA PLATAFORMA**")
                st.error(f"❌ **PERFIL TRÍPLICE NÃO MAPEADO - AVISAR O ADMINISTRADOR**")
                st.error(f"**Combinação tríplice detectada:** {combinacao_triplice}")
                st.error("**AÇÃO NECESSÁRIA:** Adicionar mapeamento e criar arquivo de conteúdo para este perfil tríplice.")
                st.error("**Impacto:** O usuário não receberá a análise completa do perfil tríplice até que seja implementado.")
            elif tipo_perfil == "HÍBRIDO":
                st.error("❌ **COMBINAÇÃO DE PERFIL HÍBRIDO INDEFINIDO - AVISAR O CONSULTOR DO PROJETO**")
                if num_dimensoes_fortes >= 2:
                    st.error(f"Combinação não mapeada: {dimensoes_fortes_ordenadas[0]['letra']}/{dimensoes_fortes_ordenadas[1]['letra']}")
            else:
                st.error("❌ **PERFIL INDEFINIDO - AVISAR O CONSULTOR DO PROJETO**")
        
        # ===== FIM DO PASSO 3 =====

    except Exception as e:
        st.error(f"Erro na análise DISC: {str(e)}")

def analisar_perfil_disc(cursor, user_id, tabela_escolhida=None):
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
        tabela_escolhida (str, optional): Nome da tabela. Se não fornecido, usa session_state.

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
        # Usa tabela_escolhida como parâmetro se fornecido, senão usa session_state
        if tabela_escolhida:
            tabela = tabela_escolhida
        else:
            tabela = st.session_state.get('tabela_escolhida', 'forms_resultados_01')
        
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

        # 4. Calcular variáveis híbridas (mesma lógica da função streamlit)
        import os
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
                try:
                    valor_str = str(result[0]).replace(',', '.')
                    valor_convertido = float(valor_str)
                    # Aplicar correção se valor estiver multiplicado por 1000
                    if valor_convertido >= 1000:
                        valores_elementos[elemento] = valor_convertido / 1000
                    else:
                        valores_elementos[elemento] = valor_convertido
                except:
                    valores_elementos[elemento] = 0.0
            else:
                valores_elementos[elemento] = 0.0
        
        # Calcular variáveis híbridas
        variaveis_hibridas = []
        dominancia_hibrida = (valores_elementos.get('C31', 0) + valores_elementos.get('D31', 0)) / 2
        influencia_hibrida = (valores_elementos.get('C32', 0) + valores_elementos.get('D32', 0)) / 2
        estabilidade_hibrida = (valores_elementos.get('C33', 0) + valores_elementos.get('D33', 0)) / 2
        conformidade_hibrida = (valores_elementos.get('C34', 0) + valores_elementos.get('D34', 0)) / 2
        
        variaveis_hibridas = [
            {'dimensao': 'Dominância', 'letra': 'D', 'valor_hibrido': dominancia_hibrida},
            {'dimensao': 'Influência', 'letra': 'I', 'valor_hibrido': influencia_hibrida},
            {'dimensao': 'Estabilidade', 'letra': 'S', 'valor_hibrido': estabilidade_hibrida},
            {'dimensao': 'Conformidade', 'letra': 'C', 'valor_hibrido': conformidade_hibrida}
        ]
        variaveis_hibridas.sort(key=lambda x: x['valor_hibrido'], reverse=True)
        
        if len(variaveis_hibridas) < 2:
            return "Análise não disponível: dados insuficientes para análise."
        
        # REGRA DOS 25 PONTOS: Contar dimensões com valor híbrido >= 25
        LIMITE_FORTE = 25.0
        dimensoes_fortes = [v for v in variaveis_hibridas if v['valor_hibrido'] >= LIMITE_FORTE]
        num_dimensoes_fortes = len(dimensoes_fortes)
        
        # Ordenar dimensões fortes por valor (maior para menor)
        dimensoes_fortes_ordenadas = sorted(dimensoes_fortes, key=lambda x: x['valor_hibrido'], reverse=True)
        
        # Determinar tipo de perfil baseado no número de dimensões fortes
        if num_dimensoes_fortes == 1:
            # PERFIL ÚNICO: Apenas uma dimensão possui 25 pontos ou mais
            primario = dimensoes_fortes_ordenadas[0]
            letra_primaria = primario['letra']
            arquivos_unicos = {
                'D': 'Conteudo/01/1_D_Dominancia.md',
                'I': 'Conteudo/01/1_I_Influencia.md', 
                'S': 'Conteudo/01/1_S_Estabilidade.md',
                'C': 'Conteudo/01/1_C_Conformidade.md'
            }
            arquivo_analise = arquivos_unicos.get(letra_primaria)
            titulo_analise = f"Perfil ÚNICO: {primario['dimensao']}"
        elif num_dimensoes_fortes == 2:
            # PERFIL HÍBRIDO (DUPLO): Exatamente duas dimensões possuem 25 pontos ou mais
            primario = dimensoes_fortes_ordenadas[0]
            secundario = dimensoes_fortes_ordenadas[1]
            letra_primaria = primario['letra']
            letra_secundaria = secundario['letra']
            combinacao = f"{letra_primaria}{letra_secundaria}"
            arquivos_combinados = {
                'DC': 'Conteudo/01/21_DC_DOMINANCIA_CONFORMIDADE.md',
                'DI': 'Conteudo/01/22_DI_DOMINANCIA_INFLUENCIA.md',
                'ID': 'Conteudo/01/23_ID_INFLUENCIA_DOMINANCIA.md',
                'IS': 'Conteudo/01/24_IS_INFLUENCIA_ESTABILIDADE.md',
                'SI': 'Conteudo/01/25_SI_ESTABILIDADE_INFLUENCIA.md',
                'SC': 'Conteudo/01/26_SC_ESTABILIDADE_CONFORMIDADE.md',
                'CD': 'Conteudo/01/27_CD_CONFORMIDADE_DOMINANCIA.md',
                'CS': 'Conteudo/01/28_CS_CONFORMIDADE_ESTABILIDADE.md',
                'DS': 'Conteudo/01/29_DS_DOMINANCIA_ESTABILIDADE.md',
                'SD': 'Conteudo/01/30_SD_ESTABILIDADE_DOMINANCIA.md',
                'IC': 'Conteudo/01/31_IC_INFLUENCIA_CONFORMIDADE.md',
                'CI': 'Conteudo/01/32_CI_CONFORMIDADE_INFLUENCIA.md'
            }
            arquivo_analise = arquivos_combinados.get(combinacao)
            titulo_analise = f"Perfil HÍBRIDO: {primario['dimensao']} + {secundario['dimensao']}"
        elif num_dimensoes_fortes == 3:
            # PERFIL TRÍPLICE: Três dimensões possuem 25 pontos ou mais
            primario = dimensoes_fortes_ordenadas[0]
            secundario = dimensoes_fortes_ordenadas[1]
            terciario = dimensoes_fortes_ordenadas[2]
            letra_primaria = primario['letra']
            letra_secundaria = secundario['letra']
            letra_terciaria = terciario['letra']
            
            # Criar combinação tríplice ordenada (P₁P₂P₃)
            combinacao_triplice = f"{letra_primaria}{letra_secundaria}{letra_terciaria}"
            
            # Mapear arquivo baseado na combinação tríplice
            arquivos_triplices = {
                'DSC': 'Conteudo/01/41_DSC_DOMINANCIA_ESTABILIDADE_CONFORMIDADE.md',
                'DIS': 'Conteudo/01/42_DIS_DOMINANCIA_INFLUENCIA_ESTABILIDADE.md',
                'ISC': 'Conteudo/01/43_ISC_INFLUENCIA_ESTABILIDADE_CONFORMIDADE.md',
                'DIC': 'Conteudo/01/44_DIC_DOMINANCIA_INFLUENCIA_CONFORMIDADE.md'
            }
            
            arquivo_analise = arquivos_triplices.get(combinacao_triplice)
            titulo_analise = f"Perfil TRÍPLICE: {primario['dimensao']} + {secundario['dimensao']} + {terciario['dimensao']}"
        else:
            # Caso não haja dimensões fortes ou dados insuficientes
            return "Análise não disponível: nenhuma dimensão com 25 pontos ou mais encontrada."
        
        # Ler arquivo de análise
        if not arquivo_analise:
            # Verificar se é perfil tríplice para mensagem específica
            if num_dimensoes_fortes == 3:
                combinacao_triplice = f"{dimensoes_fortes_ordenadas[0]['letra']}{dimensoes_fortes_ordenadas[1]['letra']}{dimensoes_fortes_ordenadas[2]['letra']}"
                return f"""## ⚠️ AVISO CRÍTICO PARA ADMINISTRADOR DA PLATAFORMA

### ❌ Perfil Tríplice Não Mapeado

**Combinação tríplice detectada:** {combinacao_triplice}

**AÇÃO NECESSÁRIA:** Adicionar mapeamento e criar arquivo de conteúdo para este perfil tríplice.

**Impacto:** O usuário não receberá a análise completa do perfil tríplice até que seja implementado.

**Arquivo esperado:** Conteudo/01/XX_{combinacao_triplice}_[NOME_DO_PERFIL].md
"""
            return "Análise não disponível: perfil não mapeado."
        
        # Tentar diferentes caminhos possíveis para o arquivo
        caminhos_possiveis = [
            arquivo_analise,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), arquivo_analise),
            os.path.join(os.path.dirname(__file__), arquivo_analise),
        ]
        
        conteudo_analise = None
        for caminho in caminhos_possiveis:
            try:
                if os.path.exists(caminho):
                    with open(caminho, 'r', encoding='utf-8') as f:
                        conteudo_analise = f.read()
                        break
            except Exception:
                continue
        
        if not conteudo_analise:
            # Verificar se é perfil tríplice para mensagem específica
            if num_dimensoes_fortes == 3:
                combinacao_triplice = f"{dimensoes_fortes_ordenadas[0]['letra']}{dimensoes_fortes_ordenadas[1]['letra']}{dimensoes_fortes_ordenadas[2]['letra']}"
                return f"""## ⚠️ AVISO CRÍTICO PARA ADMINISTRADOR DA PLATAFORMA

### ❌ Arquivo de Perfil Tríplice Não Encontrado

**Arquivo esperado:** {arquivo_analise}

**Combinação detectada:** {combinacao_triplice}

**AÇÃO NECESSÁRIA:** Criar o arquivo de conteúdo para este perfil tríplice na pasta 'Conteudo/01/' do projeto.

**Impacto:** O usuário não receberá a análise completa do perfil tríplice até que o arquivo seja criado.

**Caminhos verificados:**
{chr(10).join([f"- {caminho}" for caminho in caminhos_possiveis])}
"""
            return f"Análise não disponível: arquivo {arquivo_analise} não encontrado."

        # Retornar análise formatada com título e conteúdo
        analise = f"## {titulo_analise}\n\n"
        analise += conteudo_analise
        
        return analise
        
    except Exception as e:
        traceback.print_exc()
        return f"Ocorreu um erro inesperado ao gerar a análise DISC: {str(e)}"

if __name__ == "__main__":
    show_results()

