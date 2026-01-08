# 📋 Implementação do Assessment 06 - Inventário Vocacional e Profissional

**Data:** 30/12/2025  
**Versão:** 1.3  
**Assessment:** 06 - Inventário Vocacional e Profissional  
**Tabelas:** `forms_tab_06`, `forms_resultados_06`  
**Seções:** `inventario_p1`, `inventario_p2`, `resultado`

---

## 🎯 Objetivo

Este documento descreve passo a passo como foi implementado o Assessment 06 (Inventário Vocacional e Profissional) na Plataforma C.H.A.V.E. Comportamental, servindo como guia para futuras implementações de novos assessments.

---

## 📋 Informações do Assessment

- **ID:** 06
- **Nome:** Inventário Vocacional e Profissional
- **Tabelas de Dados:**
  - `forms_tab_06` (formulários e questões)
  - `forms_resultados_06` (Relatórios, análises e cálculos)
- **Seções:**
  - `inventario_p1` (Parte 1)
  - `inventario_p2` (Parte 2)
  - `resultado` (Resultados)

---

## 🔧 Passo a Passo da Implementação

### **PASSO 1: Criar Script de Importação de Dados**

**Arquivo Criado pelo Dev:** `create_forms_06.py`  
**Baseado em:** `create_forms_04.py`

**Ações Realizadas:**
1. Copiar `create_forms_04.py` para `create_forms_06.py`
2. Substituir todas as referências de `04` para `06`:
   - Funções: `import_forms_tab_04()` → `import_forms_tab_06()`
   - Funções: `import_forms_resultados_04()` → `import_forms_resultados_06()`
   - Tabelas: `forms_tab_04` → `forms_tab_06`
   - Tabelas: `forms_resultados_04` → `forms_resultados_06`
3. Atualizar mensagens e títulos: "ARMADILHAS DO EMPRESÁRIO" → "INVENTARIO VOCACIONAL E CARREIRA"
4. Implementar validação rigorosa de arquivos:
   - Passo 1 aceita apenas: `forms_tab_06.txt`
   - Passo 2 aceita apenas: `forms_resultados_06.txt`
   - Outros arquivos são recusados automaticamente

**Código de Validação:**
```python
def select_import_file(expected_filename):
    """Seleciona o arquivo TXT para importação e valida o nome exato."""
    if file_name_lower != expected_name_lower:
        # Recusa arquivo e exibe erro
        return None
```

**Linhas:** 648 linhas

---

### **PASSO 2: Atualizar Versão do Sistema**

**Arquivo Modificado:** `main.py`

**Ações Realizadas:**
1. Atualizar versão de `v.2.2c` para `v.2.2d` em 3 locais:
   - Linha 41: `page_title="CHAVE Comportamental - v.2.2d"`
   - Linha 46: `### Plataforma C.H.A.V.E. Comportamental - v.2.2d`
   - Linha 1434: `titulo_pagina = f"... - v.2.2d"`
2. Atualizar data da versão: Linha 48: `Versão 2.2d - 14/12/2025`

**Linhas Modificadas:** 4 linhas

---

### **PASSO 3: Configurar Assessment no Sistema**

**Arquivo Modificado:** `paginas/assessment_config.py`

**Ações Realizadas:**
Adicionar configuração do Assessment 06 no dicionário `ASSESSMENT_CONFIG`:
```python
"06": {
    "form_module": "form_model_06",
    "results_module": "resultados_06",
    "sections": {
        "📋 Parte 1": "inventario_p1",
        "✏️ Parte 2": "inventario_p2",
        "📊 Resultados": "resultado"
    },
    "has_menu": True,
    "menu_title": "#### 📋 Selecione a Parte que deseja",
    "menu_message": "IMPORTANTE: Precisa responder tanto a Parte 1 quanto a Parte 2",
    "selector_key": "inventario_section_selector",
    "selector_bottom_key": "inventario_section_selector_bottom",
    "target_section_key": "target_section_06"
}
```

**Linhas Adicionadas:** ~15 linhas

---

### **PASSO 4: Adicionar Mapeamento de Nome do Assessment**

**Arquivo Modificado:** `main.py`

**Ações Realizadas:**
Adicionar mapeamento no dicionário `mapping` da função `normalize_assessment_name()`:
```python
mapping = {
    "01": "DISC Essencial",
    "02": "DISC Integral",
    "03": "Âncoras de Carreira",
    "04": "Armadilhas do Empresário",
    "05": "Anamnese Completa",
    "06": "Inventario Vocacional e Profissional",  # ← Adicionado
}
```
Atualizar docstring da função para incluir o Assessment 06.

**Linhas Modificadas:** 2 linhas (linha 290 e linha 299)

---

### **PASSO 5-7: Adicionar Variáveis de Texto (Multilíngue)**

**Arquivos Modificados:** `variavel_texto.txt`, `variavel_texto_es.txt`, `variavel_texto_en.txt`

**Ações Realizadas:**

**Português (`variavel_texto.txt`):**
```
# === FORM_MODEL_06.PY - TÍTULOS DAS SEÇÕES ===
form_model_06_001=Parte 1 - Inventário Vocacional e Profissional
form_model_06_002=Parte 2 - Inventário Vocacional e Profissional
form_model_06_003=Resultados - Inventário Vocacional e Profissional

# === RESULTADOS_06.PY - MENSAGENS ===
resultados_06_001=Dê o próximo passo no desenvolvimento humano e profissional. <br>Converse com Erika Rossi – (11) 99506-6778.
```

**Espanhol (`variavel_texto_es.txt`):**
```
# === FORM_MODEL_06.PY - TÍTULOS DE SECCIONES ===
form_model_06_001=Parte 1 - Inventario Vocacional y Profesional
form_model_06_002=Parte 2 - Inventario Vocacional y Profesional
form_model_06_003=Resultados - Inventario Vocacional y Profesional

# === RESULTADOS_06.PY - MENSAJES ===
resultados_06_001=Dé el siguiente paso en el desarrollo humano y profesional. <br>Hable con Erika Rossi – (11) 99506-6778.
```

**Inglês (`variavel_texto_en.txt`):**
```
# === FORM_MODEL_06.PY - SECTION TITLES ===
form_model_06_001=Part 1 - Vocational and Professional Inventory
form_model_06_002=Part 2 - Vocational and Professional Inventory
form_model_06_003=Results - Vocational and Professional Inventory

# === RESULTADOS_06.PY - MESSAGES ===
resultados_06_001=Take the next step in human and professional development. <br>Talk to Erika Rossi – (11) 99506-6778.
```

**Linhas Adicionadas:** 5 linhas por arquivo (total: 15 linhas)

---

### **PASSO 8: Ajustar CRUD para Suportar Tabelas Numeradas**

**Arquivo Modificado:** `paginas/crude.py`

**Ações Realizadas:**
Adicionar lógica para que tabelas numeradas usem configurações genéricas de largura de colunas:
```python
# Para tabelas numeradas, usar configuração genérica
if selected_table.startswith('forms_tab_'):
    table_key = 'forms_tab'
elif selected_table.startswith('forms_resultados_'):
    table_key = 'forms_resultados'
else:
    table_key = selected_table

column_width = COLUMN_WIDTHS.get(table_key, {}).get(col_name, 'medium')
```

**Observação:** O sistema já detecta automaticamente as tabelas numeradas através das funções `get_assessment_tables()` e `check_numbered_tables()`. Quando as tabelas `forms_tab_06` e `forms_resultados_06` forem criadas, elas aparecerão automaticamente no CRUD.

**Linhas Modificadas:** ~10 linhas

---

### **PASSO 9: Registrar Assessment no Banco de Dados**

**Arquivo Criado:** `registrar_assessment_06.py`

**Objetivo:** Registrar o Assessment 06 na tabela `assessments` do banco de dados para que apareça no menu principal.

**Ações Realizadas:**
1. Criar script Python para inserir o Assessment 06 na tabela `assessments`
2. O script:
   - Verifica se o Assessment 06 já existe
   - Se não existir, insere com `user_id = 0` (template global)
   - Se existir, oferece opção de atualizar o nome
   - Exibe estatísticas após o registro

**Código Principal:**
```python
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
```

**Execução:**
```bash
python registrar_assessment_06.py
```

**Resultado:** Assessment 06 registrado com sucesso no banco de dados, aparecendo no menu principal após recarregar a página.

**Linhas Criadas:** ~100 linhas

---

### **PASSO 10: Criar Módulos Python do Assessment**

**Arquivos Criados:** `paginas/form_model_06.py` e `paginas/resultados_06.py`  
**Baseado em:** `form_model_04.py` e `resultados_04.py`

**Ações Realizadas:**

**1. Criar `form_model_06.py`:**
- Copiar `form_model_04.py` para `form_model_06.py`
- Substituir todas as referências de `04` para `06`:
  - Tabela: `forms_tab_04` → `forms_tab_06`
  - Função: `process_forms_tab_04()` → `process_forms_tab_06()`
- Atualizar seções:
  - `armadilhas_p1` → `inventario_p1`
  - `armadilhas_p2` → `inventario_p2`
  - Manter `resultado`
- Atualizar títulos e mensagens para "Inventário Vocacional e Profissional"
- Corrigir parâmetro padrão: `section='perfil'` → `section='inventario_p1'`
- Atualizar docstring com seções corretas
- Remover todas as referências a outros assessments

**2. Criar `resultados_06.py`:**
- Copiar `resultados_04.py` para `resultados_06.py`
- Substituir todas as referências de `04` para `06`:
  - Tabela: `forms_resultados_04` → `forms_resultados_06`
  - Tabela: `forms_tab_04` → `forms_tab_06`
- Atualizar títulos e mensagens para "Inventário Vocacional e Profissional"
- Atualizar caminhos de conteúdo: `Conteudo/04/` → `Conteudo/06/`
- Função `show_results()` já presente no arquivo base

**Funções Implementadas:**
- `process_forms_tab_06(section='inventario_p1')` - Processa formulários do assessment
- `show_results(tabela_escolhida, titulo_pagina, user_id)` - Exibe resultados

**Linhas Criadas:** 
- `form_model_06.py`: ~1078 linhas
- `resultados_06.py`: ~2074 linhas

---

### **PASSO 11: Criar Módulo de Recálculo de Fórmulas**

**Arquivo Criado:** `paginas/form_model_recalc_06.py`  
**Baseado em:** `form_model_recalc_05.py`

**Ações Realizadas:**
1. Criar script de recálculo de fórmulas específico para o Assessment 06
2. Implementar funções:
   - `verificar_dados_usuario_06(cursor, user_id)` - Verifica/copia dados do template
   - `calculate_formula_06(cursor, name, user_id)` - Calcula fórmulas na `forms_tab_06`
   - `atualizar_formulas_06(cursor, user_id)` - Atualiza todas as fórmulas do usuário
3. Tabela utilizada: `forms_tab_06`
4. Tratamento de divisão por zero com função `safe_div`

**Código Principal:**
```python
def atualizar_formulas_06(cursor, user_id):
    """
    Atualiza todas as fórmulas em ordem específica para um determinado usuário na forms_tab_06
    """
    cursor.execute("""
        SELECT name_element, type_element, math_element, section
        FROM forms_tab_06 
        WHERE user_id = ? 
        AND (type_element = 'formula' OR type_element = 'formulaH')
        ORDER BY ID_element
    """, (user_id,))
    # ... processamento das fórmulas ...
```

**Linhas Criadas:** ~124 linhas

---

### **PASSO 12: Corrigir Referências a Outros Assessments**

**Arquivo Modificado:** `paginas/form_model_06.py`

**Problema Identificado:** O arquivo continha referências a outros assessments (Armadilhas do Empresário, seções de outros assessments).

**Ações Realizadas:**
1. Corrigir função `process_forms_tab_06()`:
   - Parâmetro padrão: `section='perfil'` → `section='inventario_p1'`
   - Docstring: atualizar de `'perfil', 'comportamento' ou 'resultado'` para `'inventario_p1', 'inventario_p2' ou 'resultado'`

2. Corrigir dicionário de títulos:
   - Remover referências a `'armadilhas_p1'` e "Armadilhas do Empresário"
   - Atualizar para:
     ```python
     titles = {
         'inventario_p1': "📋 Parte 1 - Inventário Vocacional e Profissional",
         'inventario_p2': "✏️ Parte 2 - Inventário Vocacional e Profissional", 
         'resultado': "📊 Resultados - Inventário Vocacional e Profissional"
     }
     ```

3. Atualizar título padrão: De "Assessment 06 - Armadilhas do Empresário" para "Assessment 06 - Inventário Vocacional e Profissional"

4. Atualizar cabeçalho do arquivo com informações específicas do Assessment 06

**Resultado:** Arquivo totalmente específico para o Assessment 06, sem referências a outros assessments.

**Linhas Modificadas:** ~10 linhas

---

## 📝 Resumo dos Arquivos Modificados

| # | Arquivo | Tipo | Ações | Linhas |
|---|---------|------|-------|--------|
| 1 | `create_forms_06.py` | Criado | Script de importação baseado no 04 | 648 |
| 2 | `main.py` | Modificado | Versão atualizada + mapeamento de nome | 6 |
| 3 | `paginas/assessment_config.py` | Modificado | Configuração do Assessment 06 | ~15 |
| 4 | `variavel_texto.txt` | Modificado | Variáveis em português | 5 |
| 5 | `variavel_texto_es.txt` | Modificado | Variáveis em espanhol | 5 |
| 6 | `variavel_texto_en.txt` | Modificado | Variáveis em inglês | 5 |
| 7 | `paginas/crude.py` | Modificado | Suporte para tabelas numeradas | ~10 |
| 8 | `registrar_assessment_06.py` | Criado | Script para registrar no banco de dados | ~100 |
| 9 | `paginas/form_model_06.py` | Criado | Módulo de processamento de formulários | ~1078 |
| 10 | `paginas/resultados_06.py` | Criado | Módulo de exibição de resultados | ~2074 |
| 11 | `paginas/form_model_recalc_06.py` | Criado | Módulo de recálculo de fórmulas | ~124 |

**Total de Arquivos:** 11 (5 criados, 6 modificados)

---

## ✅ Checklist para Próxima Implementação

Use este checklist ao adicionar um novo assessment (ex: Assessment 07):

### **Preparação:**
- [ ] Definir ID do novo assessment (ex: "07")
- [ ] Definir nome do assessment
- [ ] Identificar seções (ex: `secao_p1`, `secao_p2`, `resultado`)
- [ ] Preparar arquivos TXT de importação:
  - [ ] `forms_tab_XX.txt`
  - [ ] `forms_resultados_XX.txt`

### **Implementação:**
- [ ] **PASSO 1:** Criar `create_forms_XX.py` baseado em `create_forms_06.py`
  - [ ] Substituir todas as referências `06` por `XX`
  - [ ] Atualizar nomes de tabelas
  - [ ] Atualizar mensagens e títulos
  - [ ] Implementar validação de arquivos

- [ ] **PASSO 2:** Atualizar versão em `main.py` (se necessário)
  - [ ] Atualizar `page_title`
  - [ ] Atualizar menu "About"
  - [ ] Atualizar data da versão

- [ ] **PASSO 3:** Adicionar configuração em `paginas/assessment_config.py`
  - [ ] Adicionar entrada no dicionário `ASSESSMENT_CONFIG`
  - [ ] Definir `form_module` e `results_module`
  - [ ] Mapear seções
  - [ ] Configurar `has_menu` e chaves de seleção

- [ ] **PASSO 4:** Adicionar mapeamento de nome em `main.py`
  - [ ] Adicionar entrada no dicionário `mapping` de `normalize_assessment_name()`
  - [ ] Atualizar docstring

- [ ] **PASSO 5-7:** Adicionar variáveis de texto multilíngue
  - [ ] `variavel_texto.txt` (português)
  - [ ] `variavel_texto_es.txt` (espanhol)
  - [ ] `variavel_texto_en.txt` (inglês)

- [ ] **PASSO 8:** Ajustar `paginas/crude.py` (se necessário)
  - [ ] Verificar se tabelas numeradas são detectadas automaticamente
  - [ ] Adicionar lógica para usar configurações genéricas de colunas (se necessário)

- [ ] **PASSO 9:** Registrar assessment no banco de dados
  - [ ] Criar script `registrar_assessment_XX.py` baseado em `registrar_assessment_06.py`
  - [ ] Substituir referências de `06` para `XX`
  - [ ] Executar script para inserir na tabela `assessments`
  - [ ] Verificar se aparece no menu principal após recarregar

- [ ] **PASSO 10:** Criar módulos Python do assessment
  - [ ] Criar `paginas/form_model_XX.py` baseado em `form_model_06.py`
    - [ ] Substituir todas as referências de `06` para `XX`
    - [ ] Atualizar nomes de tabelas (`forms_tab_XX`)
    - [ ] Atualizar seções específicas do assessment
    - [ ] Atualizar títulos e mensagens
    - [ ] Corrigir parâmetro padrão da função principal
  - [ ] Criar `paginas/resultados_XX.py` baseado em `resultados_06.py`
    - [ ] Substituir todas as referências de `06` para `XX`
    - [ ] Atualizar nomes de tabelas
    - [ ] Atualizar caminhos de conteúdo (`Conteudo/XX/`)

- [ ] **PASSO 11:** Criar módulo de recálculo de fórmulas
  - [ ] Criar `paginas/form_model_recalc_XX.py` baseado em `form_model_recalc_06.py`
  - [ ] Substituir todas as referências de `06` para `XX`
  - [ ] Atualizar nomes de tabelas e funções

- [ ] **PASSO 12:** Verificar e corrigir referências a outros assessments
  - [ ] Verificar se há referências a outros assessments nos módulos criados
  - [ ] Remover referências a seções de outros assessments
  - [ ] Garantir que todos os títulos e mensagens sejam específicos do novo assessment
  - [ ] Atualizar docstrings e comentários

### **Arquivos Adicionais Necessários (se aplicável):**
- [ ] Criar conteúdo em `Conteudo/XX/` (se necessário)

**Importante:** As tabelas de dados são `forms_tab_XX` e `forms_resultados_XX`. Os nomes `form_model_XX` e `resultados_XX` na configuração referem-se aos módulos Python.

---

## 🔍 Observações Importantes

### **Validação de Arquivos:**
O script `create_forms_XX.py` implementa validação rigorosa:
- Aceita apenas arquivos com nome exato esperado
- Recusa qualquer arquivo que não corresponda
- Exibe mensagem de erro clara quando arquivo incorreto

### **Nomenclatura de Seções:**
- Verificar na tabela `forms_tab_XX` quais são os nomes reais das seções
- Usar exatamente os mesmos nomes na configuração
- Exemplo: Se na tabela está `resultado` (singular), usar `resultado` na config

### **Sistema de Carregamento Dinâmico:**
O sistema já está preparado para carregar novos assessments automaticamente:
- Não é necessário modificar `main.py` além dos passos descritos
- O sistema usa `assessment_config.py` para carregar módulos dinamicamente
- Funções são chamadas automaticamente: `process_forms_tab_XX()` e `show_results()`

### **Ordem de Execução:**
1. Primeiro: Criar script de importação e importar dados
2. Segundo: Configurar assessment no sistema
3. Terceiro: Registrar assessment no banco de dados (executar `registrar_assessment_XX.py`)
4. Quarto: Verificar se aparece no menu principal (recarregar página)
5. Quinto: Criar módulos `form_model_XX.py` e `resultados_XX.py`
6. Sexto: Criar módulo `form_model_recalc_XX.py`
7. Sétimo: Verificar e corrigir referências a outros assessments
8. Oitavo: Testar funcionalidade completa

### **Registro no Banco de Dados:**
- **Importante:** O assessment precisa estar registrado na tabela `assessments` para aparecer no menu
- Use o script `registrar_assessment_XX.py` para inserir o registro
- O registro com `user_id = 0` faz o assessment aparecer para usuários master/adm
- Para usuários comuns, é necessário conceder permissão ou adicionar à lista de `assessments_padrao`

---

## 🎯 Resultado Final

Após a implementação, o Assessment 06 está:
- ✅ Configurado no sistema (`assessment_config.py`)
- ✅ Mapeamento de nome adicionado (`main.py`)
- ✅ Variáveis de texto em 3 idiomas (pt, es, en)
- ✅ Integrado ao sistema de carregamento dinâmico
- ✅ Registrado no banco de dados (tabela `assessments`)
- ✅ Aparecendo no menu principal
- ✅ Suporte no CRUD para tabelas numeradas
- ✅ Script de importação criado (`create_forms_06.py`)
- ✅ Módulo de formulários criado (`paginas/form_model_06.py`)
- ✅ Módulo de resultados criado (`paginas/resultados_06.py`)
- ✅ Módulo de recálculo criado (`paginas/form_model_recalc_06.py`)
- ✅ Referências a outros assessments removidas
- ✅ Totalmente específico para Inventário Vocacional e Profissional

**Tabelas de Dados:**
- `forms_tab_06` (formulários e questões)
- `forms_resultados_06` (resultados e cálculos)

**Módulos Python Criados:**
- `paginas/form_model_06.py` - Processamento de formulários
- `paginas/resultados_06.py` - Exibição de resultados
- `paginas/form_model_recalc_06.py` - Recálculo de fórmulas

**Próximos Passos:**
1. Executar `create_forms_06.py` para importar dados das tabelas
2. Testar funcionalidade completa do assessment
3. Criar conteúdo em `Conteudo/06/` (se necessário)

---

## 📚 Referências

- **Documentação Base:** `docs/guia_implementacao_assessments.md`
- **Guia Alternativo:** `docs/Guia2_Implementação_Novo_Assessment.md`
- **Assessment Base:** Assessment 04 (Armadilhas do Empresário)
- **Script Base:** `create_forms_04.py`
- **Script de Registro:** `registrar_assessment_06.py` (criado para este assessment)

---

## 📝 Histórico de Versões

- **v1.2 (14/12/2025):** Adicionados PASSO 10 (criação dos módulos Python), PASSO 11 (módulo de recálculo) e PASSO 12 (correção de referências)
- **v1.1 (14/12/2025):** Adicionados PASSO 8 (ajuste do CRUD) e PASSO 9 (registro no banco de dados)
- **v1.0 (14/12/2025):** Versão inicial com passos 1 a 7

---

**Documento criado em:** 14/12/2025  
**Última atualização:** 14/12/2025 (v1.2)  
**Autor:** Sistema de Documentação - Plataforma C.H.A.V.E.
