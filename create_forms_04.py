# Arquivo: create_forms_04.py
# Data: 05/01/2026
# Importação: forms_tab_04 (Armadilhas do Empresário)
# Programa para importar dados do arquivo TXT para formato multi-assessment
# Rodar pelo terminal: python create_forms_04.py


import sqlite3
import os
import pandas as pd
from tkinter import filedialog, messagebox
import tkinter as tk
import sys
from pathlib import Path
from config import DB_PATH

def clean_string(value):
    """Limpa strings de aspas e apóstrofos extras."""
    if isinstance(value, str):
        return value.replace("'", "").replace('"', "").strip()
    return value

def check_database():
    """Verifica se o banco de dados existe."""
    if not DB_PATH.exists():
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        print("Execute primeiro o programa principal para criar o banco.")
        return False
    return True

def select_import_file(file_type="forms_tab"):
    """Seleciona o arquivo TXT para importação."""
    root = tk.Tk()
    root.withdraw()
    
    title = f"Selecione o arquivo {file_type}.txt"
    file_path = filedialog.askopenfilename(
        title=title,
        filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    
    if not file_path:
        print("❌ Nenhum arquivo selecionado.")
        return None
    
    # Verificar se o arquivo tem o nome esperado
    file_name = os.path.basename(file_path)
    if file_type not in file_name.lower():
        print(f"⚠️  Aviso: Arquivo selecionado não parece ser {file_type}.txt: {file_name}")
        if not messagebox.askyesno("Confirmação", 
            f"O arquivo selecionado é '{file_name}'. Deseja continuar mesmo assim?"):
            return None
    
    return file_path

def confirm_file_selection(txt_file, table_name):
    """Confirma com o usuário se o arquivo selecionado está correto."""
    root = tk.Tk()
    root.withdraw()
    
    file_name = os.path.basename(txt_file)
    
    message = f"""
    ATENÇÃO! Confirme os dados da importação:

    Tabela de destino: {table_name}
    Arquivo selecionado: {file_name}
    Caminho completo: {txt_file}

    Deseja prosseguir com a importação?
    """
    
    return messagebox.askyesno("Confirmação de Importação", message)

def validate_selectbox_data(row_dict):
    """Valida dados de selectbox para evitar erros de inserção."""
    try:
        # Verifica se select_element contém dados válidos
        if 'select_element' in row_dict and pd.notna(row_dict['select_element']):
            select_data = str(row_dict['select_element']).strip()
            if select_data and len(select_data) > 0:
                # Limpa dados problemáticos
                row_dict['select_element'] = clean_string(select_data)
        
        return True, row_dict
    except Exception as e:
        print(f"⚠️  Erro na validação de selectbox: {str(e)}")
        return False, row_dict

def import_forms_tab_04():
    """
    Importa dados do arquivo forms_tab.txt para a tabela forms_tab_04
    """
    if not check_database():
        return False
    
    # 1. Selecionar arquivo TXT
    print("📁 Selecionando arquivo forms_tab.txt...")
    txt_file = select_import_file()
    if not txt_file:
        return False
    
    # 2. Confirmar seleção
    if not confirm_file_selection(txt_file, "forms_tab_04"):
        print("❌ Importação cancelada pelo usuário.")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🔄 Iniciando importação: forms_tab.txt → forms_tab_04")
        
        # 3. Verificar se forms_tab_04 já existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forms_tab_04'
        """)
        
        if cursor.fetchone():
            print("⚠️  Tabela forms_tab_04 já existe!")
            root = tk.Tk()
            root.withdraw()
            if not messagebox.askyesno("Confirmação", 
                "A tabela forms_tab_04 já existe. Deseja apagá-la e recriar?"):
                print("Operação cancelada pelo usuário.")
                return False
            
            # Apagar tabela existente
            cursor.execute("DROP TABLE IF EXISTS forms_tab_04")
            conn.commit()
            print("🗑️  Tabela forms_tab_04 removida para recriação.")
        
        # 4. Criar tabela forms_tab_04
        print("📋 Criando tabela forms_tab_04...")
        cursor.execute("""
            CREATE TABLE forms_tab_04 (
                ID_element INTEGER PRIMARY KEY AUTOINCREMENT,
                name_element TEXT NOT NULL,
                type_element TEXT NOT NULL,
                math_element TEXT,
                msg_element TEXT,
                value_element REAL,
                select_element TEXT,
                str_element TEXT,
                e_col INTEGER,
                e_row INTEGER,
                user_id INTEGER,
                section TEXT,
                col_len TEXT
            );
        """)
        
        # 5. Ler arquivo TXT
        print("📊 Lendo arquivo forms_tab.txt...")
        try:
            df = pd.read_csv(
                txt_file,
                encoding='cp1252',
                sep='\t',
                quoting=3,
                na_filter=False,
                decimal=','
            )
            print(f"✅ Arquivo lido com sucesso: {len(df)} linhas encontradas")
            
            # Verificar colunas
            print("\nColunas encontradas no arquivo:")
            print(df.columns.tolist())
            
            # Verificar se col_len existe
            if 'col_len' not in df.columns:
                print("⚠️  Aviso: Coluna 'col_len' não encontrada no arquivo.")
                df['col_len'] = ''  # Adiciona coluna vazia se não existir
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {str(e)}")
            return False
        
        # 6. Confirmar importação
        if not messagebox.askyesno("Confirmação Final",
            f"Foram encontradas {len(df)} linhas para importar.\n"
            "Deseja iniciar a importação?"):
            print("❌ Importação cancelada pelo usuário.")
            return False
        
        # 7. Importar dados
        print("📥 Importando dados...")
        imported_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Preparar dados da linha
                row_dict = row.to_dict()
                
                # Validar dados de selectbox
                is_valid, row_dict = validate_selectbox_data(row_dict)
                if not is_valid:
                    error_count += 1
                    continue
                
                # Inserir registro
                cursor.execute("""
                    INSERT INTO forms_tab_04 (
                        name_element, type_element, math_element, msg_element,
                        value_element, select_element, str_element, e_col, e_row,
                        user_id, section, col_len
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    clean_string(str(row_dict.get('name_element', ''))),
                    clean_string(str(row_dict.get('type_element', ''))),
                    clean_string(str(row_dict.get('math_element', ''))),
                    clean_string(str(row_dict.get('msg_element', ''))),
                    row_dict.get('value_element', 0.0),
                    clean_string(str(row_dict.get('select_element', ''))),
                    clean_string(str(row_dict.get('str_element', ''))),
                    int(row_dict.get('e_col', 0)) if pd.notna(row_dict.get('e_col')) else 0,
                    int(row_dict.get('e_row', 0)) if pd.notna(row_dict.get('e_row')) else 0,
                    int(row_dict.get('user_id', 0)) if pd.notna(row_dict.get('user_id')) else 0,
                    clean_string(str(row_dict.get('section', ''))),
                    clean_string(str(row_dict.get('col_len', '')))
                ))
                
                imported_count += 1
                
                # Progresso a cada 100 registros
                if imported_count % 100 == 0:
                    print(f"📊 Importados: {imported_count} registros...")
                    
            except Exception as e:
                error_count += 1
                print(f"⚠️  Erro na linha {index + 1}: {str(e)}")
                continue
        
        conn.commit()
        
        print(f"\n✅ Importação concluída!")
        print(f"📊 Registros importados: {imported_count}")
        print(f"⚠️  Erros encontrados: {error_count}")
        
        # 8. Mostrar estatísticas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registros,
                COUNT(DISTINCT user_id) as usuarios_unicos,
                COUNT(DISTINCT section) as secoes_unicas
            FROM forms_tab_04
        """)
        
        stats = cursor.fetchone()
        print(f"\n📈 Estatísticas da tabela forms_tab_04:")
        print(f"   Total de registros: {stats[0]}")
        print(f"   Usuários únicos: {stats[1]}")
        print(f"   Seções únicas: {stats[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def import_forms_resultados_04():
    """
    Importa dados do arquivo forms_resultados.txt para a tabela forms_resultados_04
    """
    if not check_database():
        return False
    
    # 1. Selecionar arquivo TXT
    print("📁 Selecionando arquivo forms_resultados.txt...")
    txt_file = select_import_file("forms_resultados")
    if not txt_file:
        return False
    
    # 2. Confirmar seleção
    if not confirm_file_selection(txt_file, "forms_resultados_04"):
        print("❌ Importação cancelada pelo usuário.")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🔄 Iniciando importação: forms_resultados.txt → forms_resultados_04")
        
        # 3. Verificar se forms_resultados_04 já existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forms_resultados_04'
        """)
        
        if cursor.fetchone():
            print("⚠️  Tabela forms_resultados_04 já existe!")
            root = tk.Tk()
            root.withdraw()
            if not messagebox.askyesno("Confirmação", 
                "A tabela forms_resultados_04 já existe. Deseja apagá-la e recriar?"):
                print("Operação cancelada pelo usuário.")
                return False
            
            # Apagar tabela existente
            cursor.execute("DROP TABLE IF EXISTS forms_resultados_04")
            conn.commit()
            print("🗑️  Tabela forms_resultados_04 removida para recriação.")
        
        # 4. Criar tabela forms_resultados_04
        print("📋 Criando tabela forms_resultados_04...")
        cursor.execute("""
            CREATE TABLE forms_resultados_04 (
                ID_element INTEGER PRIMARY KEY AUTOINCREMENT,
                name_element TEXT NOT NULL,
                type_element TEXT NOT NULL,
                math_element TEXT,
                msg_element TEXT,
                value_element REAL,
                select_element TEXT,
                str_element TEXT,
                e_col INTEGER,
                e_row INTEGER,
                section TEXT,
                user_id INTEGER
            );
        """)
        
        # 5. Ler arquivo TXT
        print("📊 Lendo arquivo forms_resultados.txt...")
        try:
            df = pd.read_csv(
                txt_file,
                encoding='cp1252',
                sep='\t',
                quoting=3,
                na_filter=False,
                decimal=','
            )
            print(f"✅ Arquivo lido com sucesso: {len(df)} linhas encontradas")
            
            # Verificar colunas
            print("\nColunas encontradas no arquivo:")
            print(df.columns.tolist())
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {str(e)}")
            return False
        
        # 6. Confirmar importação
        if not messagebox.askyesno("Confirmação Final",
            f"Foram encontradas {len(df)} linhas para importar.\n"
            "Deseja iniciar a importação?"):
            print("❌ Importação cancelada pelo usuário.")
            return False
        
        # 7. Criar mapeamento de seções baseado na forms_tab_04
        print("🔗 Criando mapeamento de seções...")
        cursor.execute("""
            SELECT name_element, section 
            FROM forms_tab_04 
            WHERE user_id = 0
        """)
        section_mapping = dict(cursor.fetchall())
        print(f"✅ Mapeamento criado: {len(section_mapping)} elementos")
        
        # 8. Importar dados
        print("📥 Importando dados...")
        imported_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Preparar dados da linha
                row_dict = row.to_dict()
                
                # Validar dados de selectbox
                is_valid, row_dict = validate_selectbox_data(row_dict)
                if not is_valid:
                    error_count += 1
                    continue
                
                # Determinar seção baseada no mapeamento
                name_element = clean_string(str(row_dict.get('name_element', '')))
                section = section_mapping.get(name_element, 'resultado')  # Default para 'resultado'
                
                # Inserir registro
                cursor.execute("""
                    INSERT INTO forms_resultados_04 (
                        name_element, type_element, math_element, msg_element,
                        value_element, select_element, str_element, e_col, e_row,
                        section, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name_element,
                    clean_string(str(row_dict.get('type_element', ''))),
                    clean_string(str(row_dict.get('math_element', ''))),
                    clean_string(str(row_dict.get('msg_element', ''))),
                    row_dict.get('value_element', 0.0),
                    clean_string(str(row_dict.get('select_element', ''))),
                    clean_string(str(row_dict.get('str_element', ''))),
                    int(row_dict.get('e_col', 0)) if pd.notna(row_dict.get('e_col')) else 0,
                    int(row_dict.get('e_row', 0)) if pd.notna(row_dict.get('e_row')) else 0,
                    section,
                    int(row_dict.get('user_id', 0)) if pd.notna(row_dict.get('user_id')) else 0
                ))
                
                imported_count += 1
                
                # Progresso a cada 100 registros
                if imported_count % 100 == 0:
                    print(f"📊 Importados: {imported_count} registros...")
                    
            except Exception as e:
                error_count += 1
                print(f"⚠️  Erro na linha {index + 1}: {str(e)}")
                continue
        
        conn.commit()
        
        print(f"\n✅ Importação concluída!")
        print(f"📊 Registros importados: {imported_count}")
        print(f"⚠️  Erros encontrados: {error_count}")
        
        # 8. Mostrar estatísticas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registros,
                COUNT(DISTINCT user_id) as usuarios_unicos
            FROM forms_resultados_04
        """)
        
        stats = cursor.fetchone()
        print(f"\n📈 Estatísticas da tabela forms_resultados_04:")
        print(f"   Total de registros: {stats[0]}")
        print(f"   Usuários únicos: {stats[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verify_import():
    """Verifica se as importações foram bem-sucedidas."""
    if not check_database():
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n🔍 Verificando importações...")
        
        # Verificar forms_tab_04
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forms_tab_04'
        """)
        
        forms_tab_exists = cursor.fetchone() is not None
        
        # Verificar forms_resultados_04
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forms_resultados_04'
        """)
        
        forms_resultados_exists = cursor.fetchone() is not None
        
        print(f"📊 forms_tab_04: {'✅ Existe' if forms_tab_exists else '❌ Não encontrada'}")
        print(f"📊 forms_resultados_04: {'✅ Existe' if forms_resultados_exists else '❌ Não encontrada'}")
        
        if forms_tab_exists:
            cursor.execute("SELECT COUNT(*) FROM forms_tab_04")
            count_tab = cursor.fetchone()[0]
            print(f"   Registros: {count_tab}")
        
        if forms_resultados_exists:
            cursor.execute("SELECT COUNT(*) FROM forms_resultados_04")
            count_resultados = cursor.fetchone()[0]
            print(f"   Registros: {count_resultados}")
        
        if forms_tab_exists and forms_resultados_exists:
            print("✅ Ambas as importações verificadas com sucesso!")
            return True
        else:
            print("⚠️  Aviso: Algumas tabelas não foram encontradas!")
            return False
            
    except Exception as e:
        print(f"❌ Erro na verificação: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def show_table_statistics():
    """Mostra estatísticas das tabelas."""
    if not check_database():
        return
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n📈 ESTATÍSTICAS DAS TABELAS ARMADILHAS DO EMPRESÁRIO:")
        print("-" * 60)
        
        # Verificar forms_tab_04
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forms_tab_04'
        """)
        
        if cursor.fetchone():
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT user_id) as usuarios_unicos,
                    COUNT(DISTINCT section) as secoes_unicas
                FROM forms_tab_04
            """)
            
            stats = cursor.fetchone()
            print(f"\n📊 forms_tab_04:")
            print(f"   Total de registros: {stats[0]}")
            print(f"   Usuários únicos: {stats[1]}")
            print(f"   Seções únicas: {stats[2]}")
            
            # Mostrar seções encontradas
            cursor.execute("""
                SELECT DISTINCT section, COUNT(*) as count
                FROM forms_tab_04 
                WHERE section IS NOT NULL AND section != ''
                GROUP BY section
                ORDER BY section
            """)
            sections = cursor.fetchall()
            if sections:
                print(f"   Seções encontradas:")
                for section, count in sections:
                    print(f"     - {section}: {count} registros")
        else:
            print("\n📊 forms_tab_04: ❌ Não encontrada")
        
        # Verificar forms_resultados_04
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forms_resultados_04'
        """)
        
        if cursor.fetchone():
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT user_id) as usuarios_unicos
                FROM forms_resultados_04
            """)
            
            stats = cursor.fetchone()
            print(f"\n📊 forms_resultados_04:")
            print(f"   Total de registros: {stats[0]}")
            print(f"   Usuários únicos: {stats[1]}")
        else:
            print("\n📊 forms_resultados_04: ❌ Não encontrada")
            
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {str(e)}")
    finally:
        if conn:
            conn.close()

def main():
    """Função principal do programa."""
    print("=" * 60)
    print("📥 IMPORTAÇÃO: ARMADILHAS DO EMPRESÁRIO (forms_tab + forms_resultados)")
    print("=" * 60)
    
    while True:
        print("\n📋 MENU DE OPÇÕES:")
        print("1 - Importar forms_tab.txt → forms_tab_04")
        print("2 - Importar forms_resultados.txt → forms_resultados_04")
        print("3 - Verificar importações")
        print("4 - Mostrar estatísticas das tabelas")
        print("0 - Sair")
        
        try:
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == "1":
                print("\n📥 Iniciando importação forms_tab...")
                if import_forms_tab_04():
                    print("✅ Importação forms_tab concluída com sucesso!")
                else:
                    print("❌ Importação forms_tab falhou!")
                    
            elif opcao == "2":
                print("\n📥 Iniciando importação forms_resultados...")
                if import_forms_resultados_04():
                    print("✅ Importação forms_resultados concluída com sucesso!")
                else:
                    print("❌ Importação forms_resultados falhou!")
                    
            elif opcao == "3":
                print("\n🔍 Verificando importações...")
                if verify_import():
                    print("✅ Verificação concluída com sucesso!")
                else:
                    print("❌ Verificação falhou!")
                    
            elif opcao == "4":
                show_table_statistics()
                
            elif opcao == "0":
                print("👋 Encerrando programa...")
                break
                
            else:
                print("❌ Opção inválida! Tente novamente.")
                
        except KeyboardInterrupt:
            print("\n👋 Programa interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")

if __name__ == "__main__":
    main()
