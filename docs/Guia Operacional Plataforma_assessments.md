# Guia de Procedimentos - Plataforma de Assessments

**Versão:** 2.0  
**Data:** 2025  
**Objetivo:** Guia prático para adicionar e manter assessments na plataforma modular

---

## Sumário

1. [Procedimento: Adicionar Novo Assessment](#procedimento-adicionar-novo-assessment)
2. [Padrões Obrigatórios](#padrões-obrigatórios)
3. [Estrutura de Arquivos](#estrutura-de-arquivos)
4. [Arquitetura do Sistema](#arquitetura-do-sistema)
5. [Referência Rápida](#referência-rápida)

---

## Procedimento: Adicionar Novo Assessment

### Checklist Passo a Passo

#### 1. Adicionar Configuração em `assessment_config.py`

Editar `paginas/assessment_config.py` e adicionar nova entrada no dicionário `ASSESSMENT_CONFIG`:

```python
ASSESSMENT_CONFIG = {
    # ... assessments existentes ...
    
    "XX": {  # Substituir XX pelo ID do novo assessment (ex: "06", "07")
        "form_module": "form_model_XX",           # Obrigatório
        "results_module": "resultados_XX",        # Obrigatório
        "sections": {                             # Obrigatório se has_menu=True
            "📋 Parte 1": "secao_1",             # Rótulo da interface → variável interna
            "✏️ Parte 2": "secao_2",
            "📊 Resultados": "resultado"
        },
        "has_menu": True,                         # True = exibe menu, False = executa direto
        "menu_title": "#### 📋 Selecione a Parte que deseja",  # Obrigatório se has_menu=True
        "menu_message": "IMPORTANTE: Precisa responder tanto a Parte 1 quanto a Parte 2",  # Obrigatório se has_menu=True
        "selector_key": "assessment_XX_section_selector",  # Obrigatório se has_menu=True
        "selector_bottom_key": "assessment_XX_section_selector_bottom",  # Obrigatório se has_menu=True
        "target_section_key": "target_section_XX"  # Obrigatório se has_menu=True
    }
}
```

**Nota:** Se `has_menu=False`, os campos `menu_title`, `menu_message`, `selector_key`, `selector_bottom_key` e `target_section_key` podem ser `None`.

#### 2. Criar Módulo de Formulário

Criar arquivo `paginas/form_model_XX.py` com a seguinte estrutura mínima:

```python
# form_model_XX.py
# Módulo de formulário do Assessment XX
# Data: [data de criação]

import streamlit as st
import sqlite3
from config import DB_PATH

def new_user(cursor, user_id):
    """
    Inicializa registros para novo usuário.
    Copia dados do user_id 0 (template) para o novo user_id.
    """
    cursor.execute("""
        SELECT COUNT(*) FROM forms_tab_XX WHERE user_id = ?
    """, (user_id,))
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute("""
            INSERT INTO forms_tab_XX 
            SELECT NULL, ?, name_element, type, math_element, ...
            FROM forms_tab_XX WHERE user_id = 0
        """, (user_id,))
        # ... outras inicializações necessárias ...

def process_forms_tab_XX(section='secao_1'):
    """
    Processa seções do assessment XX.
    
    Args:
        section: Nome da seção a processar (deve corresponder aos valores em 'sections' da config)
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Usuário não identificado.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Inicializar dados do usuário se necessário
    new_user(cursor, user_id)
    conn.commit()
    
    # Processar seção específica
    if section == 'secao_1':
        # Implementação da Parte 1
        pass
    elif section == 'secao_2':
        # Implementação da Parte 2
        pass
    elif section == 'resultado':
        # Exibir resultados ou redirecionar
        pass
    
    conn.close()
```

**Obrigatório:**
- Função `new_user(cursor, user_id)` para inicializar dados
- Função `process_forms_tab_XX(section)` onde XX é o ID do assessment
- A função deve aceitar o parâmetro `section` mesmo se `has_menu=False`

#### 3. Criar Módulo de Resultados

Criar arquivo `paginas/resultados_XX.py` com a seguinte estrutura mínima:

```python
# resultados_XX.py
# Módulo de resultados do Assessment XX
# Data: [data de criação]

import streamlit as st
import sqlite3
from config import DB_PATH

def new_user(cursor, user_id: int, tabela: str):
    """
    Inicializa resultados para novo usuário.
    
    Args:
        cursor: Cursor do banco de dados
        user_id: ID do usuário
        tabela: Nome da tabela de resultados (ex: "forms_resultados_XX")
    """
    # Implementação específica do assessment
    pass

def show_results(tabela_escolhida: str, titulo_pagina: str, user_id: int):
    """
    Exibe resultados do assessment XX.
    
    Args:
        tabela_escolhida: Nome da tabela de resultados (ex: "forms_resultados_XX")
        titulo_pagina: HTML com título da página
        user_id: ID do usuário
    """
    # Implementação específica do assessment
    # - Consultas ao banco
    # - Cálculos
    # - Gráficos e visualizações
    # - Análises e interpretações
    pass
```

**Obrigatório:**
- Função `new_user(cursor, user_id, tabela)` para inicializar resultados
- Função `show_results(tabela_escolhida, titulo_pagina, user_id)` para exibir resultados

#### 4. Criar Tabelas no Banco de Dados

Criar as seguintes tabelas no banco de dados (`data/calcrh2.db`):

```sql
-- Tabela de dados do formulário
CREATE TABLE forms_tab_XX (
    ID_element INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name_element TEXT NOT NULL,
    type TEXT,
    math_element TEXT,
    -- ... outros campos específicos do assessment ...
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Tabela de resultados calculados
CREATE TABLE forms_resultados_XX (
    ID_resultado INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    -- ... campos específicos dos resultados ...
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Criar índices para melhor performance
CREATE INDEX idx_forms_tab_XX_user ON forms_tab_XX(user_id);
CREATE INDEX idx_forms_resultados_XX_user ON forms_resultados_XX(user_id);
```

**Importante:** 
- Sempre incluir `user_id` nas tabelas
- Criar registro com `user_id = 0` como template para novos usuários
- Adicionar índices nas colunas `user_id` para performance

#### 5. Registrar Assessment no Banco de Dados

Inserir registro na tabela `assessments`:

```sql
INSERT INTO assessments (assessment_id, assessment_name, description, active)
VALUES ('XX', 'Nome do Assessment', 'Descrição do assessment', 1);
```

#### 6. Verificação Final

- [ ] Configuração adicionada em `assessment_config.py`
- [ ] Módulo `form_model_XX.py` criado com função `process_forms_tab_XX()`
- [ ] Módulo `resultados_XX.py` criado com função `show_results()`
- [ ] Tabelas `forms_tab_XX` e `forms_resultados_XX` criadas no banco
- [ ] Registro inserido na tabela `assessments`
- [ ] Template com `user_id = 0` populado nas tabelas
- [ ] Testado funcionamento do menu (se `has_menu=True`)
- [ ] Testado funcionamento direto (se `has_menu=False`)
- [ ] Testado cálculo e exibição de resultados

**Observação:** Não é necessário modificar `main.py`. O sistema detecta automaticamente o novo assessment através da configuração.

---

## Padrões Obrigatórios

### Nomenclatura

#### Arquivos
- **Módulo de formulário:** `form_model_XX.py` (onde XX é o ID do assessment com 2 dígitos)
- **Módulo de resultados:** `resultados_XX.py` (onde XX é o ID do assessment com 2 dígitos)

#### Funções
- **Processamento de formulário:** `process_forms_tab_XX(section)` - sempre com sufixo numérico
- **Inicialização de usuário (form):** `new_user(cursor, user_id)`
- **Inicialização de usuário (resultados):** `new_user(cursor, user_id, tabela)`
- **Exibição de resultados:** `show_results(tabela_escolhida, titulo_pagina, user_id)`

#### Tabelas do Banco de Dados
- **Dados do formulário:** `forms_tab_XX`
- **Resultados calculados:** `forms_resultados_XX`

#### Chaves de Configuração
- **Selector key:** `assessment_XX_section_selector` (ou nome específico do assessment)
- **Selector bottom key:** `assessment_XX_section_selector_bottom`
- **Target section key:** `target_section_XX`

### Estrutura de Módulos

#### Módulo `form_model_XX.py`
```python
# Cabeçalho com nome, função e data
# Imports necessários
# Função new_user(cursor, user_id)
# Função process_forms_tab_XX(section)
```

#### Módulo `resultados_XX.py`
```python
# Cabeçalho com nome, função e data
# Imports necessários
# Função new_user(cursor, user_id, tabela)
# Função show_results(tabela_escolhida, titulo_pagina, user_id)
```

### Configuração Obrigatória

Todas as configurações devem estar em `paginas/assessment_config.py` no dicionário `ASSESSMENT_CONFIG`.

**Campos obrigatórios:**
- `form_module`: Nome do módulo (ex: `"form_model_01"`)
- `results_module`: Nome do módulo (ex: `"resultados_01"`)
- `has_menu`: Boolean indicando se exibe menu de seções

**Campos obrigatórios se `has_menu=True`:**
- `sections`: Dicionário mapeando rótulos da interface para variáveis internas
- `menu_title`: Título do menu (Markdown)
- `menu_message`: Mensagem do menu
- `selector_key`: Chave única para o seletor de seções
- `selector_bottom_key`: Chave única para o seletor no rodapé
- `target_section_key`: Chave para seção alvo no session_state

---

## Estrutura de Arquivos

```
Plataforma_CH/
│
├── main.py                          # Orquestrador principal
│   ├── show_assessment_execution()  # Função genérica de execução
│   ├── load_assessment_module()     # Carrega módulos dinamicamente
│   └── render_section_menu()         # Renderiza menu genérico
│
├── paginas/
│   │
│   ├── assessment_config.py         # ⭐ CONFIGURAÇÃO CENTRALIZADA
│   │   └── ASSESSMENT_CONFIG         # Dicionário com todos os assessments
│   │
│   ├── form_model_01.py            # Assessment 01 - Formulário
│   ├── resultados_01.py             # Assessment 01 - Resultados
│   ├── form_model_02.py            # Assessment 02 - Formulário
│   ├── resultados_02.py             # Assessment 02 - Resultados
│   ├── form_model_03.py            # Assessment 03 - Formulário
│   ├── resultados_03.py             # Assessment 03 - Resultados
│   ├── form_model_04.py            # Assessment 04 - Formulário
│   ├── resultados_04.py             # Assessment 04 - Resultados
│   ├── form_model_05.py            # Assessment 05 - Formulário
│   ├── resultados_05.py             # Assessment 05 - Resultados
│   ├── form_model_06.py            # Assessment 06 - Formulário
│   └── resultados_06.py             # Assessment 06 - Resultados
│
└── data/
    └── calcrh2.db                   # Banco de dados SQLite
        ├── forms_tab_01              # Tabela do Assessment 01
        ├── forms_tab_02              # Tabela do Assessment 02
        ├── forms_resultados_01       # Resultados do Assessment 01
        ├── forms_resultados_02       # Resultados do Assessment 02
        └── ... (outras tabelas)
```

### Agrupamento por Assessment

Cada assessment é composto por:

1. **Configuração** em `assessment_config.py` (chave "XX")
2. **Módulo de formulário** `form_model_XX.py`
3. **Módulo de resultados** `resultados_XX.py`
4. **Tabelas no banco:**
   - `forms_tab_XX` (dados do formulário)
   - `forms_resultados_XX` (resultados calculados)
5. **Registro** na tabela `assessments` do banco de dados

---

## Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                    main.py (Orquestrador)                   │
│  - show_assessment_execution()                              │
│  - load_assessment_module()                                 │
│  - render_section_menu()                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Usa
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          assessment_config.py (Configuração)                │
│  - ASSESSMENT_CONFIG (dicionário centralizado)             │
│  - get_assessment_config()                                  │
│  - get_function_name()                                       │
│  - has_menu()                                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Define estrutura de
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Módulos Específicos por Assessment             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ form_model_  │  │ form_model_  │  │ form_model_  │    │
│  │   01.py      │  │   02.py      │  │   03.py      │    │
│  │              │  │              │  │              │    │
│  │ process_     │  │ process_     │  │ process_     │    │
│  │ forms_tab_   │  │ forms_tab_   │  │ forms_tab_   │    │
│  │ 01()         │  │ 02()         │  │ 03()         │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ resultados_  │  │ resultados_  │  │ resultados_  │    │
│  │   01.py      │  │   02.py      │  │   03.py      │    │
│  │              │  │              │  │              │    │
│  │ show_        │  │ show_        │  │ show_        │    │
│  │ results()    │  │ results()    │  │ results()    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo de Execução

```
1. Usuário seleciona assessment
   ↓
2. show_assessment_execution() é chamado
   ↓
3. get_assessment_config(assessment_id) busca configuração
   ↓
4. load_assessment_module() carrega módulos dinamicamente
   ├─ get_form_module_name() → "form_model_XX"
   ├─ get_results_module_name() → "resultados_XX"
   └─ get_function_name() → "process_forms_tab_XX"
   ↓
5. Verifica se tem menu (has_menu())
   ├─ SIM → render_section_menu() (usa configuração)
   └─ NÃO → process_forms_tab() diretamente
   ↓
6. process_forms_tab_XX(section) executa o assessment
```

### Carregamento Dinâmico

O sistema usa `importlib` para carregar módulos em tempo de execução:

```python
# Exemplo do que acontece internamente
form_module = importlib.import_module(f"paginas.form_model_XX")
process_forms_tab = getattr(form_module, "process_forms_tab_XX")
```

Isso permite adicionar novos assessments sem modificar `main.py`.

---

## Referência Rápida

### Funções Principais em `main.py`

| Função | Propósito |
|--------|-----------|
| `show_assessment_execution()` | Executa o assessment selecionado usando configuração centralizada |
| `load_assessment_module(assessment_id)` | Carrega dinamicamente os módulos do assessment |
| `render_section_menu(assessment_id, config, process_forms_tab)` | Renderiza menu genérico de seleção de seções |

### Funções Helper em `assessment_config.py`

| Função | Retorno |
|--------|---------|
| `get_assessment_config(assessment_id)` | Dicionário com configuração do assessment |
| `get_form_module_name(assessment_id)` | Nome do módulo form_model (ex: `"form_model_01"`) |
| `get_results_module_name(assessment_id)` | Nome do módulo resultados (ex: `"resultados_01"`) |
| `get_function_name(assessment_id)` | Nome da função padronizado (ex: `"process_forms_tab_01"`) |
| `has_menu(assessment_id)` | Boolean indicando se o assessment tem menu |
| `get_sections(assessment_id)` | Dicionário com mapeamento de seções |
| `get_all_assessment_ids()` | Lista de todos os IDs de assessments configurados |

### Estrutura de Configuração

```python
ASSESSMENT_CONFIG = {
    "XX": {
        "form_module": str,           # Obrigatório
        "results_module": str,         # Obrigatório
        "sections": dict,             # Obrigatório se has_menu=True
        "has_menu": bool,             # Obrigatório
        "menu_title": str,            # Obrigatório se has_menu=True
        "menu_message": str,           # Obrigatório se has_menu=True
        "selector_key": str,          # Obrigatório se has_menu=True
        "selector_bottom_key": str,   # Obrigatório se has_menu=True
        "target_section_key": str     # Obrigatório se has_menu=True
    }
}
```

### Padrão de Nomes

| Componente | Padrão | Exemplo |
|------------|--------|---------|
| Módulo form | `form_model_XX.py` | `form_model_06.py` |
| Módulo resultados | `resultados_XX.py` | `resultados_06.py` |
| Função processamento | `process_forms_tab_XX()` | `process_forms_tab_06()` |
| Tabela formulário | `forms_tab_XX` | `forms_tab_06` |
| Tabela resultados | `forms_resultados_XX` | `forms_resultados_06` |
| Selector key | `assessment_XX_section_selector` | `assessment_06_section_selector` |

### Exemplo de Configuração Completa

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

---

## Notas Importantes

1. **Não modificar `main.py`** ao adicionar novos assessments. O sistema é totalmente baseado em configuração.

2. **Sempre usar nomenclatura padronizada.** Desvios causam erros no carregamento dinâmico.

3. **Template com `user_id = 0`** deve existir em todas as tabelas para inicialização de novos usuários.

4. **Função `process_forms_tab_XX()`** deve sempre aceitar o parâmetro `section`, mesmo que não seja usado quando `has_menu=False`.

5. **Chaves de session_state** devem ser únicas para cada assessment para evitar conflitos.

---

**Última atualização:** 2025  
**Versão do documento:** 2.0
