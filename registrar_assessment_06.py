# Arquivo: registrar_assessment_06.py
# Data: 14/12/2025
# Objetivo: Registrar o Assessment 06 na tabela assessments do banco de dados

import sqlite3
from datetime import datetime
from config import DB_PATH

def registrar_assessment_06():
    """
    Registra o Assessment 06 na tabela assessments.
    Cria um registro com user_id = 0 (template) para que o assessment apareça no sistema.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o Assessment 06 já existe
        cursor.execute("""
            SELECT COUNT(*) FROM assessments 
            WHERE assessment_id = '06'
        """)
        
        existe = cursor.fetchone()[0] > 0
        
        if existe:
            print("[AVISO] Assessment 06 ja esta registrado no banco de dados.")
            resposta = input("Deseja atualizar o nome? (s/n): ").strip().lower()
            
            if resposta == 's':
                cursor.execute("""
                    UPDATE assessments 
                    SET assessment_name = 'Inventario Vocacional e Profissional',
                        updated_at = ?
                    WHERE assessment_id = '06'
                """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
                conn.commit()
                print("[OK] Nome do Assessment 06 atualizado com sucesso!")
            else:
                print("Operacao cancelada.")
                conn.close()
                return False
        else:
            # Inserir Assessment 06 com user_id = 0 (template)
            agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO assessments (
                    user_id, 
                    assessment_id, 
                    assessment_name, 
                    access_granted,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                0,  # user_id = 0 (template/global)
                '06',
                'Inventario Vocacional e Profissional',
                1,  # access_granted = 1 (permitido)
                agora,
                agora
            ))
            
            conn.commit()
            print("[OK] Assessment 06 registrado com sucesso!")
            print(f"   ID: 06")
            print(f"   Nome: Inventario Vocacional e Profissional")
            print(f"   Data: {agora}")
        
        # Verificar registros
        cursor.execute("""
            SELECT assessment_id, assessment_name, COUNT(*) as total_registros
            FROM assessments 
            WHERE assessment_id = '06'
            GROUP BY assessment_id, assessment_name
        """)
        
        resultado = cursor.fetchone()
        if resultado:
            print(f"\n[INFO] Estatisticas do Assessment 06:")
            print(f"   Total de registros: {resultado[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao registrar Assessment 06: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("REGISTRO DO ASSESSMENT 06 NO BANCO DE DADOS")
    print("=" * 60)
    print()
    
    if registrar_assessment_06():
        print("\n[OK] Processo concluido com sucesso!")
        print("[INFO] O Assessment 06 agora deve aparecer no menu principal.")
    else:
        print("\n[ERRO] Processo falhou. Verifique os erros acima.")
