# 📋 Guia de Implementação de Assessments Multi-Assessment

**Data:** 09/11/2025  
**Versão:** 2.0  
**Objetivo:** Documentar o processo aprendido para implementar novos assessments no sistema multi-assessment

---

## 🎯 Visão Geral

Este guia documenta o processo aprendido com os assessments 01 (DISC Essencial), 02 (DISC Integral), 03 (Âncoras de Carreira), 04 (Armadilhas do Empresário) e 05 (Anamnese Completa) para implementar rapidamente novos assessments no sistema.

---

## 📊 Estrutura dos Assessments Implementados

### ✅ Assessment 01 - DISC Essencial
- **Tabela:** `forms_tab_01`
- **Seções:** `perfil`, `comportamento`, `resultado`
- **Status:** ✅ Funcionando
- **Função:** `process_forms_tab()` (nome especial para compatibilidade)
- **Correções:** ✅ Referências de tabela corrigidas, ✅ Análise comportamental detalhada funcionando, ✅ Caminhos de conteúdo corrigidos

### ✅ Assessment 02 - DISC Integral
- **Tabela:** `forms_tab_02`
- **Seções:** `perfil`, `comportamento`, `resultado`
- **Status:** ✅ Funcionando
- **Função:** `process_forms_tab_02()`
- **Correções:** ✅ Referências de tabela corrigidas, ✅ Caminhos de conteúdo corrigidos, ✅ Script de importação criado

### ✅ Assessment 03 - Âncoras de Carreira  
- **Tabela:** `forms_tab_03`
- **Seções:** `ancoras_p1`, `ancoras_p2`, `resultado`
- **Status:** ✅ Funcionando
- **Função:** `process_forms_tab_03()`

### ✅ Assessment 04 - Armadilhas do Empresário
- **Tabela:** `forms_tab_04`
- **Seções:** `armadilhas_p1`, `armadilhas_p2`, `resultado`
- **Status:** ✅ Funcionando
- **Função:** `process_forms_tab_04()`
- **Correções:** ✅ Referências de tabela corrigidas, ✅ Análises funcionando, ✅ Script de importação criado

### ✅ Assessment 05 - Anamnese Completa
- **Tabela:** `forms_tab_05`
- **Seções:** `anamnese_p1`, `anamnese_p2`, `resultado`
- **Status:** ✅ Funcionando
- **Função:** `process_forms_tab_05()`
- **Nota:** Usa o bloco `else` genérico no `show_assessment_execution()` (sem menu específico)

---

## 🔧 Arquitetura do Sistema Multi-Assessment

### **Sistema de Carregamento Dinâmico**

O sistema utiliza a função `load_assessment_module()` no `main.py` para carregar dinamicamente os módulos de cada assessment:

```python
def load_assessment_module(assessment_id):
    """
    Carrega dinamicamente o módulo do assessment selecionado
    """
    # Mapeamento de assessments para seus módulos
    assessment_modules = {
        "01": ("form_model_01", "resultados_01"),
        "02": ("form_model_02", "resultados_02"),
        "03": ("form_model_03", "resultados_03"),
        "04": ("form_model_04", "resultados_04"),
        "05": ("form_model_05", "resultados_05")
    }
    
    # Carregar módulo do formulário
    form_module = importlib.import_module(f"paginas.{form_module_name}")
    
    # Determinar o nome da função baseado no assessment_id
    if assessment_id == "01":
        function_name = "process_forms_tab"  # Nome especial para assessment 01
    else:
        function_name = f"process_forms_tab_{assessment_id}"  # process_forms_tab_02, etc.
    
    process_forms_tab = getattr(form_module, function_name, None)
    
    # Carregar módulo de resultados
    results_module = importlib.import_module(f"paginas.{results_module_name}")
    show_results = getattr(results_module, "show_results", None)
```

**⚠️ IMPORTANTE:** 
- Assessment 01 usa `process_forms_tab()` (sem sufixo numérico)
- Assessments 02-05 usam `process_forms_tab_XX()` (com sufixo numérico)

---

## 🔧 Correções Realizadas no DISC 01

### **Problema 1: Referências de Tabela Incorretas**
- **Erro:** `"cannot access local variable 'tipo_perfil'"`
- **Causa:** Variável não inicializada quando `len(variaveis_hibridas) < 2`
- **Solução:** Adicionado `else` para tratar dados insuficientes
- **Arquivo:** `paginas/resultados_01.py`

### **Problema 2: Caminhos de Arquivos de Conteúdo**
- **Erro:** `"Arquivo não encontrado: Conteudo/22_DI_DOMINANCIA_INFLUENCIA.md"`
- **Causa:** Arquivos estavam na subpasta `Conteudo/01/`
- **Solução:** Corrigidos todos os caminhos para incluir subpasta `01/`
- **Arquivos corrigidos:** 12 arquivos de conteúdo (únicos + combinados)

### **Problema 3: Indentação de Código**
- **Erro:** Estrutura `if/else` mal indentada
- **Causa:** Blocos `else` fora de alinhamento
- **Solução:** Corrigida indentação de todos os blocos condicionais

---

## 🔧 Correções Realizadas no Assessment 04

### **Problema 1: Referências de Tabela Duplicadas**
- **Erro:** `"no such table: forms_tab_04_04"`
- **Causa:** Substituição global incorreta criou nomes duplicados
- **Solução:** Corrigido para `forms_tab_04` em todas as referências
- **Arquivo:** `paginas/form_model_04.py`

### **Problema 2: Seções Incorretas na Tabela**
- **Erro:** Seções `fdireta`, `finvertida` em vez de `armadilhas_p1`, `armadilhas_p2`
- **Causa:** Dados importados com nomes de seção incorretos
- **Solução:** Script de correção para atualizar seções na tabela
- **Registros corrigidos:** 80 registros atualizados

### **Problema 3: Referências Incorretas em Análises**
- **Erro:** `"Valor não encontrado na tabela forms_tab"`
- **Causa:** `resultados_04.py` usando tabelas genéricas
- **Solução:** Corrigido para `forms_tab_04` e `forms_resultados_04`
- **Arquivo:** `paginas/resultados_04.py`

### **Problema 4: Dados Template Vazios**
- **Erro:** Tabela `forms_tab_04` existia mas estava vazia
- **Causa:** Falta de dados template (user_id = 0)
- **Solução:** Criado script `create_forms_04.py` para importação
- **Resultado:** 89 registros template criados

---

## 🔧 Processo de Implementação

### **Passo 1: Verificar/Criar Tabela do Assessment**

```python
# Script de verificação (exemplo para assessment XX)
import sqlite3
from config import DB_PATH

def check_forms_tab_XX():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar se a tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forms_tab_XX'")
    if cursor.fetchone():
        print('✅ Tabela forms_tab_XX existe')
        
        # Verificar seções
        cursor.execute("SELECT DISTINCT section FROM forms_tab_XX WHERE section IS NOT NULL ORDER BY section")
        sections = cursor.fetchall()
        print(f'📋 Seções: {[s[0] for s in sections]}')
        
        # Contar registros por seção
        for section in sections:
            cursor.execute("SELECT COUNT(*) FROM forms_tab_XX WHERE section = ?", (section[0],))
            count = cursor.fetchone()[0]
            print(f'  - {section[0]}: {count} registros')
        
        # Verificar dados template
        cursor.execute("SELECT COUNT(*) FROM forms_tab_XX WHERE user_id = 0")
        template_count = cursor.fetchone()[0]
        print(f'📦 Dados template (user_id=0): {template_count} registros')
    else:
        print('❌ Tabela forms_tab_XX não existe - precisa ser criada')
    
    conn.close()
```

### **Passo 2: Verificar/Criar Arquivo form_model_XX.py**

**⚠️ IMPORTANTE:** O nome da função depende do número do assessment:
- **Assessment 01:** `process_forms_tab()` (sem sufixo)
- **Assessments 02-99:** `process_forms_tab_XX()` (com sufixo)

**Estrutura necessária:**
```python
# paginas/form_model_XX.py

def new_user(cursor, user_id):
    """
    Inicializa registros para um novo usuário copiando dados do user_id 0.
    """
    try:
        # Verifica se já existem registros para o usuário
        cursor.execute("""
            SELECT COUNT(*) FROM forms_tab_XX WHERE user_id = ?
        """, (user_id,))
        
        if cursor.fetchone()[0] == 0:  # Se não existem registros
            # Copia todos os dados do user_id 0
            cursor.execute("""
                INSERT INTO forms_tab_XX (
                    name_element, type_element, math_element, msg_element,
                    value_element, select_element, str_element, e_col, e_row,
                    section, col_len, user_id
                )
                SELECT 
                    name_element, type_element, math_element, msg_element,
                    value_element, select_element, str_element, e_col, e_row,
                    section, col_len, ? as user_id
                FROM forms_tab_XX 
                WHERE user_id = 0
            """, (user_id,))
            
            st.success(f"Registros iniciais criados para o usuário {user_id}")
        
    except Exception as e:
        st.error(f"Erro ao criar registros para novo usuário: {str(e)}")
        raise

def process_forms_tab_XX(section='secao_padrao'):
    """
    Processa registros da tabela forms_tab_XX e exibe em layout de grade.
    
    Args:
        section: Nome da seção a ser processada (ex: 'secao_1', 'secao_2', 'resultado')
    """
    # ... implementação específica do assessment ...
    # Deve incluir lógica para:
    # - Conectar ao banco de dados
    # - Chamar new_user() se necessário
    # - Buscar elementos da seção
    # - Renderizar elementos na interface
    pass

# NOTA: Para assessment 01, a função deve se chamar process_forms_tab() (sem sufixo)
# Para outros assessments, use process_forms_tab_XX() (com sufixo)
```

### **Passo 3: Atualizar main.py**

**3.1. Adicionar ao mapeamento de assessments:**

```python
# No arquivo main.py, função load_assessment_module()
assessment_modules = {
    "01": ("form_model_01", "resultados_01"),
    "02": ("form_model_02", "resultados_02"),
    "03": ("form_model_03", "resultados_03"),
    "04": ("form_model_04", "resultados_04"),
    "05": ("form_model_05", "resultados_05"),
    "XX": ("form_model_XX", "resultados_XX")  # ← Adicionar novo assessment
}
```

**3.2. Adicionar lógica no `show_assessment_execution()` (OPCIONAL):**

**⚠️ NOTA:** Se o assessment não precisar de menu específico de seções, ele usará automaticamente o bloco `else` genérico que chama `process_forms_tab()` diretamente.

**Se precisar de menu específico (como assessments 01-04), adicionar:**

```python
# Para Assessment XX, usar seções específicas
elif assessment_id == "XX":
    # Mapeamento específico para Assessment XX
    st.markdown("#### 📋 Assessment XX - Selecione a Parte")
    
    # Usar radio buttons como no original
    section_options = {
        "📋 Parte 1": "secao_1",
        "✏️ Parte 2": "secao_2", 
        "📊 Resultados": "resultado"
    }
    
    # Verifica se há uma seção alvo definida pelo menu do final da página
    target_section = st.session_state.get("target_section_XX", None)
    section_to_process = None
    
    # Função callback para quando o menu principal mudar
    def on_main_menu_change():
        """Callback chamado quando o menu principal muda"""
        selected = st.session_state["assessment_XX_section_selector"]
        if selected:
            # Sincroniza com o menu do final da página
            st.session_state["assessment_XX_section_selector_bottom"] = selected
            # Limpa a variável auxiliar do menu do final para evitar conflito
            if "target_section_XX" in st.session_state:
                del st.session_state["target_section_XX"]
    
    # Prioridade 1: Se há target_section (do menu do final), usa ela
    if target_section:
        section_to_process = target_section
        # Encontra a opção correspondente à seção alvo
        target_option = None
        for option, value in section_options.items():
            if value == target_section:
                target_option = option
                break
        
        # Se encontrou, atualiza o session_state do menu principal ANTES de criar o widget
        if target_option:
            st.session_state["assessment_XX_section_selector"] = target_option
            # Limpa a variável auxiliar
            del st.session_state["target_section_XX"]
    
    selected_section = st.radio(
        "IMPORTANTE: Precisa responder tanto a Parte 1 quanto a Parte 2",
        options=list(section_options.keys()),
        key="assessment_XX_section_selector",  # Chave única para este assessment
        horizontal=True,
        on_change=on_main_menu_change  # Callback quando o menu principal mudar
    )
    
    # Sincroniza com o menu do final da página (se existir)
    if selected_section:
        st.session_state["assessment_XX_section_selector_bottom"] = selected_section
    
    # Executar a seção selecionada
    if not section_to_process and selected_section:
        section_to_process = section_options[selected_section]
    
    if section_to_process:
        process_forms_tab(section_to_process)
```

**⚠️ IMPORTANTE:** 
- Se o assessment não precisar de menu específico, ele funcionará automaticamente com o bloco `else` genérico
- O assessment 05 usa o bloco genérico (sem menu específico)
- Use menu específico apenas se precisar de controle de seções na interface

### **Passo 4: Verificar/Criar resultados_XX.py**

**Estrutura necessária:**
```python
# paginas/resultados_XX.py

def new_user(cursor, user_id: int, tabela: str):
    """
    Inicializa registros de resultados para um novo usuário.
    
    Args:
        cursor: Cursor do banco de dados
        user_id: ID do usuário
        tabela: Nome da tabela de resultados (ex: 'forms_resultados_XX')
    """
    # ... implementação específica ...
    pass

def show_results(tabela_escolhida: str, titulo_pagina: str, user_id: int):
    """
    Função principal para exibir a interface web de resultados.
    
    Args:
        tabela_escolhida: Nome da tabela de resultados (ex: 'forms_resultados_XX')
        titulo_pagina: Título a ser exibido na página
        user_id: ID do usuário
    """
    # ... implementação específica do assessment ...
    # Deve incluir:
    # - Conexão com banco de dados
    # - Chamada a new_user() se necessário
    # - Processamento e exibição dos resultados
    # - Gráficos, análises, etc.
    pass
```

### **Passo 5: Criar Script de Importação (se necessário)**

**⚠️ IMPORTANTE:** Se a tabela estiver vazia, criar script de importação baseado em `create_forms_04.py`:

```python
# create_forms_XX.py
# Script para importar dados do arquivo TXT para formato multi-assessment

import sqlite3
import os
import pandas as pd
from tkinter import filedialog, messagebox
import tkinter as tk
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

def import_forms_tab_XX():
    """
    Importa dados do arquivo forms_tab.txt para a tabela forms_tab_XX
    """
    if not check_database():
        return False
    
    # 1. Selecionar arquivo TXT
    print("📁 Selecionando arquivo forms_tab.txt...")
    txt_file = select_import_file()
    if not txt_file:
        return False
    
    # 2. Confirmar seleção
    if not confirm_file_selection(txt_file, "forms_tab_XX"):
        print("❌ Importação cancelada pelo usuário.")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🔄 Iniciando importação: forms_tab.txt → forms_tab_XX")
        
        # 3. Verificar se forms_tab_XX já existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forms_tab_XX'
        """)
        
        if cursor.fetchone():
            print("⚠️  Tabela forms_tab_XX já existe!")
            root = tk.Tk()
            root.withdraw()
            if not messagebox.askyesno("Confirmação", 
                "A tabela forms_tab_XX já existe. Deseja apagá-la e recriar?"):
                print("Operação cancelada pelo usuário.")
                return False
            
            # Apagar tabela existente
            cursor.execute("DROP TABLE IF EXISTS forms_tab_XX")
            conn.commit()
            print("🗑️  Tabela forms_tab_XX removida para recriação.")
        
        # 4. Criar tabela forms_tab_XX
        print("📋 Criando tabela forms_tab_XX...")
        cursor.execute("""
            CREATE TABLE forms_tab_XX (
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
        
        # 5. Ler e importar dados do arquivo TXT
        print("📥 Lendo arquivo TXT...")
        df = pd.read_csv(txt_file, encoding='cp1252', sep='\t', quoting=3, na_filter=False, decimal=',')
        
        print(f"📊 Total de registros no arquivo: {len(df)}")
        
        # 6. Importar dados
        print("💾 Importando dados...")
        for index, row in df.iterrows():
            cursor.execute("""
                INSERT INTO forms_tab_XX (
                    name_element, type_element, math_element, msg_element,
                    value_element, select_element, str_element, e_col, e_row,
                    user_id, section, col_len
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row.get('name_element', '')),
                str(row.get('type_element', '')),
                str(row.get('math_element', '')),
                str(row.get('msg_element', '')),
                row.get('value_element', 0.0),
                clean_string(str(row.get('select_element', ''))),
                str(row.get('str_element', '')),
                int(row.get('e_col', 0)) if pd.notna(row.get('e_col')) else 0,
                int(row.get('e_row', 0)) if pd.notna(row.get('e_row')) else 0,
                int(row.get('user_id', 0)) if pd.notna(row.get('user_id')) else 0,
                str(row.get('section', '')),
                str(row.get('col_len', ''))
            ))
        
        conn.commit()
        print(f"✅ Importação concluída: {len(df)} registros importados")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Função principal do programa."""
    print("=" * 60)
    print("📥 IMPORTAÇÃO: Assessment XX (forms_tab_XX)")
    print("=" * 60)
    
    if import_forms_tab_XX():
        print("✅ Importação concluída com sucesso!")
    else:
        print("❌ Importação falhou!")

if __name__ == "__main__":
    main()
```

### **Passo 6: Verificar Caminhos de Arquivos de Conteúdo**

**⚠️ IMPORTANTE:** Verificar se os arquivos de conteúdo estão na estrutura correta:

```
Conteudo/
├── 01/                          ← Subpasta específica do assessment
│   ├── 1_D_Dominancia.md
│   ├── 1_I_Influencia.md
│   ├── 1_S_Estabilidade.md
│   ├── 1_C_Conformidade.md
│   ├── 21_DC_DOMINANCIA_CONFORMIDADE.md
│   ├── 22_DI_DOMINANCIA_INFLUENCIA.md
│   └── ... (outros arquivos)
├── 02/                          ← Subpasta do assessment 02
├── 03/                          ← Subpasta do assessment 03
└── ...
```

**Código de verificação:**
```python
# Verificar se arquivos de conteúdo existem
import os

def check_content_files(assessment_id):
    content_path = f"Conteudo/{assessment_id}/"
    
    if not os.path.exists(content_path):
        print(f"❌ Pasta de conteúdo não encontrada: {content_path}")
        return False
    
    # Listar arquivos na pasta
    files = os.listdir(content_path)
    md_files = [f for f in files if f.endswith('.md')]
    
    print(f"✅ Pasta encontrada: {content_path}")
    print(f"📄 Arquivos .md encontrados: {len(md_files)}")
    
    for file in md_files:
        print(f"  - {file}")
    
    return True
```

---

## 📋 Checklist de Implementação

### ✅ **Pré-requisitos**
- [ ] Tabela `forms_tab_XX` existe com dados
- [ ] Seções definidas na tabela (ex: `secao_1`, `secao_2`, `resultado`)
- [ ] Dados template com `user_id = 0` (verificar com script de verificação)
- [ ] Tabela `forms_resultados_XX` existe (se necessário para resultados)

### ✅ **Arquivos a Verificar/Criar**
- [ ] `paginas/form_model_XX.py` com funções:
  - [ ] `new_user(cursor, user_id)` - copia dados do user_id 0
  - [ ] `process_forms_tab_XX(section)` - processa seção do assessment
  - [ ] **NOTA:** Assessment 01 usa `process_forms_tab()` (sem sufixo)
- [ ] `paginas/resultados_XX.py` com função:
  - [ ] `new_user(cursor, user_id, tabela)` - inicializa resultados
  - [ ] `show_results(tabela_escolhida, titulo_pagina, user_id)` - exibe resultados

### ✅ **Atualizações no main.py**
- [ ] Adicionar ao mapeamento `assessment_modules` em `load_assessment_module()`
- [ ] **OPCIONAL:** Adicionar `elif assessment_id == "XX":` no `show_assessment_execution()` se precisar de menu específico
- [ ] Se usar menu específico:
  - [ ] Definir `section_options` com mapeamento correto
  - [ ] Criar `st.radio()` com chave única (`assessment_XX_section_selector`)
  - [ ] Implementar lógica de execução com callbacks

### ✅ **Scripts de Importação**
- [ ] Criar `create_forms_XX.py` se tabela estiver vazia
- [ ] Testar importação de dados
- [ ] Verificar se dados template (user_id=0) foram criados

### ✅ **Testes**
- [ ] Seleção do assessment funciona no seletor
- [ ] Menu intermediário aparece (se implementado)
- [ ] Radio buttons funcionam (se implementado)
- [ ] Seções carregam corretamente
- [ ] Dados são copiados para novos usuários (testar com user_id novo)
- [ ] Resultados são exibidos corretamente
- [ ] Análises funcionam (se aplicável)

---

## 🚀 Implementação Rápida - Exemplos de Seções

### **Assessment 01 - DISC Essencial**
```python
# Seções esperadas: perfil, comportamento, resultado
section_options = {
    "📋 Parte 1": "perfil",
    "✏️ Parte 2": "comportamento", 
    "📊 Resultados": "resultado"
}
# Função: process_forms_tab() (sem sufixo)
```

### **Assessment 02 - DISC Integral**
```python
# Seções esperadas: perfil, comportamento, resultado
section_options = {
    "📋 Parte 1": "perfil",
    "✏️ Parte 2": "comportamento", 
    "📊 Resultados": "resultado"
}
# Função: process_forms_tab_02()
```

### **Assessment 03 - Âncoras de Carreira**
```python
# Seções esperadas: ancoras_p1, ancoras_p2, resultado
section_options = {
    "📋 Parte 1": "ancoras_p1",
    "✏️ Parte 2": "ancoras_p2", 
    "📊 Resultados": "resultado"
}
# Função: process_forms_tab_03()
```

### **Assessment 04 - Armadilhas do Empresário**
```python
# Seções esperadas: armadilhas_p1, armadilhas_p2, resultado
section_options = {
    "📋 Parte 1": "armadilhas_p1",
    "✏️ Parte 2": "armadilhas_p2", 
    "📊 Resultados": "resultado"
}
# Função: process_forms_tab_04()
```

### **Assessment 05 - Anamnese Completa**
```python
# Seções esperadas: anamnese_p1, anamnese_p2, resultado
# NOTA: Usa bloco else genérico (sem menu específico)
# Função: process_forms_tab_05()
```

---

## 🔍 Troubleshooting

### **Problema: "Não foi possível carregar o módulo do assessment"**
- ✅ Verificar se `form_model_XX.py` existe em `paginas/`
- ✅ Verificar se função existe:
  - Assessment 01: `process_forms_tab()` (sem sufixo)
  - Outros: `process_forms_tab_XX()` (com sufixo)
- ✅ Verificar se tabela `forms_tab_XX` existe
- ✅ Verificar se assessment está no mapeamento `assessment_modules` no `main.py`

### **Problema: "Nenhum elemento encontrado para a seção"**
- ✅ Verificar se dados existem na tabela com `user_id = 0`
- ✅ Verificar se função `new_user()` está sendo chamada
- ✅ Verificar se seções estão corretas no mapeamento
- ✅ Verificar se nome da seção na tabela corresponde ao mapeamento

### **Problema: Menu intermediário não aparece**
- ✅ Verificar se `assessment_id == "XX"` está correto no `show_assessment_execution()`
- ✅ Verificar se lógica está no `show_assessment_execution()`
- ✅ Verificar se chave do radio é única
- ✅ **NOTA:** Se não precisar de menu, o assessment funcionará com o bloco `else` genérico

### **Problema: "cannot access local variable 'tipo_perfil'"**
- ✅ Verificar se variável está inicializada em todos os caminhos
- ✅ Adicionar `else` para tratar casos de dados insuficientes
- ✅ Verificar indentação dos blocos `if/else`

### **Problema: "Arquivo não encontrado: Conteudo/XX_arquivo.md"**
- ✅ Verificar se arquivos estão na subpasta `Conteudo/XX/`
- ✅ Corrigir caminhos nos dicionários `arquivos_unicos` e `arquivos_combinados`
- ✅ Verificar se estrutura de pastas está correta

### **Problema: "Valor não encontrado na tabela forms_tab"**
- ✅ Verificar se referências estão usando `forms_tab_XX` (não `forms_tab`)
- ✅ Corrigir todas as consultas SQL para usar tabela numerada
- ✅ Verificar se dados existem na tabela correta

### **Problema: "no such table: forms_tab_XX_XX"**
- ✅ Verificar se substituição global não criou nomes duplicados
- ✅ Corrigir todas as referências para usar `forms_tab_XX` (não `forms_tab_XX_XX`)
- ✅ Verificar se tabela existe com nome correto

### **Problema: "Seções incorretas na tabela"**
- ✅ Verificar seções reais na tabela: `SELECT DISTINCT section FROM forms_tab_XX`
- ✅ Corrigir seções se necessário: `UPDATE forms_tab_XX SET section = 'nova_secao' WHERE section = 'secao_antiga'`
- ✅ Verificar se mapeamento no main.py está correto

### **Problema: "Tabela existe mas está vazia"**
- ✅ Verificar se há dados template (user_id = 0): `SELECT COUNT(*) FROM forms_tab_XX WHERE user_id = 0`
- ✅ Criar script de importação baseado em `create_forms_04.py`
- ✅ Importar dados do arquivo TXT para popular a tabela

### **Problema: "AttributeError: module has no attribute 'process_forms_tab_XX'"**
- ✅ Verificar se nome da função está correto:
  - Assessment 01: `process_forms_tab()` (sem sufixo)
  - Outros: `process_forms_tab_XX()` (com sufixo)
- ✅ Verificar se função está definida no arquivo `form_model_XX.py`
- ✅ Verificar se `load_assessment_module()` está usando o nome correto

---

## 📝 Notas Importantes

1. **Nomes de funções:****
   - Assessment 01 usa `process_forms_tab()` (sem sufixo numérico)
   - Assessments 02-99 usam `process_forms_tab_XX()` (com sufixo numérico)

2. **Chaves únicas:** Sempre usar chaves únicas para radio buttons (`assessment_XX_section_selector`)

3. **Mapeamento de seções:** Verificar seções reais na tabela antes de mapear

4. **Menu específico:** Não é obrigatório - assessments podem usar o bloco `else` genérico

5. **Dados template:** Garantir que existem dados com `user_id = 0`

6. **Testes:** Testar cada seção individualmente

7. **Caminhos de conteúdo:** Verificar se arquivos estão na subpasta `Conteudo/XX/`

8. **Referências de tabela:** Sempre usar `forms_tab_XX` (não `forms_tab`)

9. **Inicialização de variáveis:** Garantir que todas as variáveis sejam inicializadas em todos os caminhos

10. **Indentação:** Verificar indentação correta dos blocos `if/else`

11. **Estrutura de pastas:** Manter consistência na organização dos arquivos de conteúdo

12. **Substituição global:** Cuidado com substituições globais que podem criar nomes duplicados

13. **Scripts de importação:** Criar scripts baseados em `create_forms_04.py` para popular tabelas vazias

14. **Verificação de seções:** Sempre verificar seções reais na tabela antes de implementar

15. **Referências em análises:** Corrigir todas as referências em `resultados_XX.py` para usar tabelas numeradas

16. **Dados template:** Verificar se existem dados template (user_id = 0) antes de testar

17. **Sistema de carregamento:** O sistema usa `load_assessment_module()` para carregar dinamicamente os módulos

18. **Mapeamento de assessments:** Sempre adicionar novo assessment ao dicionário `assessment_modules` no `main.py`

---

## 📚 Lições Aprendidas

### **✅ Implementação Bem-Sucedida - Assessment 04**
- **Tempo total:** ~2 horas de implementação
- **Problemas encontrados:** 4 problemas principais
- **Soluções aplicadas:** Todas as correções funcionaram
- **Status final:** ✅ Assessment 04 funcionando completamente

### **🔧 Principais Desafios**
1. **Referências de tabela duplicadas:** Substituição global criou nomes incorretos
2. **Seções incorretas:** Dados importados com nomes de seção errados
3. **Tabela vazia:** Falta de dados template para novos usuários
4. **Referências em análises:** Uso de tabelas genéricas em vez de numeradas

### **✅ Implementação Bem-Sucedida - Assessment 02**
- **Tempo total:** ~1 hora de implementação
- **Problemas encontrados:** 3 problemas principais
- **Soluções aplicadas:** Todas as correções funcionaram
- **Status final:** ✅ Assessment 02 funcionando completamente

### **💡 Melhores Práticas Descobertas**
1. **Verificar seções reais** antes de implementar mapeamento
2. **Criar scripts de importação** baseados em exemplos funcionais
3. **Testar substituições globais** para evitar nomes duplicados
4. **Verificar dados template** antes de testar funcionalidades
5. **Corrigir todas as referências** em arquivos de análise
6. **Verificar caminhos de conteúdo** antes de implementar análises
7. **Usar substituição global cuidadosa** para evitar nomes duplicados
8. **Testar todas as funcionalidades** após correções

### **📋 Processo Otimizado**
1. **Verificar tabela** → 2. **Corrigir seções** → 3. **Importar dados** → 4. **Corrigir referências** → 5. **Testar funcionalidades**

---

## 🚀 Melhorias Implementadas

### **🔧 Sistema de Carregamento Dinâmico**
- **Função:** `load_assessment_module()` carrega módulos dinamicamente
- **Vantagem:** Facilita adição de novos assessments sem modificar código central
- **Mapeamento:** Dicionário `assessment_modules` centraliza configuração

### **🔧 Funcionalidades Adicionadas ao Sistema CRUD**
- **Deleção específica:** `delete_single_record()` com confirmação obrigatória
- **Deleção total:** `delete_all_records()` com warnings rigorosos
- **Controle de permissões:** `manage_assessment_permissions()` integrada
- **Melhorias de visualização:** Tabelas responsivas com controles adaptativos

---

## 🎯 Próximos Passos

1. **Implementar novos assessments** usando este guia
2. **Documentar problemas encontrados** para melhorar o guia
3. **Criar scripts automatizados** para verificação de tabelas
4. **Melhorar scripts de importação** com validações adicionais
5. **Implementar funcionalidades avançadas** no CRUD
6. **Otimizar performance** para tabelas muito grandes
7. **Padronizar estrutura de menus** para novos assessments

---

**Criado em:** 20/01/2025  
**Última atualização:** 09/11/2025 (v2.0 - Atualização completa com informações sobre load_assessment_module e estrutura atual)  
**Autor:** Sistema Multi-Assessment
