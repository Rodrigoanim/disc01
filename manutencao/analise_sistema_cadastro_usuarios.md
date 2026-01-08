# 📋 Análise do Sistema de Cadastro de Novos Usuários

**Data:** 09/11/2025  
**Versão:** 1.0  
**Objetivo:** Analisar o funcionamento completo do sistema de cadastro de novos usuários na plataforma

---

## 🎯 Visão Geral

O sistema permite que novos usuários se cadastrem na plataforma através de uma aba "Cadastro" na tela de login, **apenas se o cadastro estiver habilitado por um administrador**. O cadastro é controlado por uma configuração administrativa que pode ser habilitada ou desabilitada.

---

## 🔐 Controle de Acesso ao Cadastro

### **Função: `verificar_cadastro_habilitado()`**

**Localização:** `main.py` (linhas 296-343)

**Funcionamento:**
```python
def verificar_cadastro_habilitado():
    """
    Verifica se o cadastro de novos usuários está habilitado
    Retorna True se habilitado, False se desabilitado
    """
    # 1. Verifica se existe a tabela 'configuracoes'
    # 2. Se não existe, cria com cadastro DESABILITADO por padrão
    # 3. Busca a configuração 'cadastro_habilitado'
    # 4. Retorna True se valor = 'true', False caso contrário
    # 5. Em caso de erro, retorna False (segurança por padrão)
```

**Características:**
- ✅ **Segurança por padrão:** Cadastro vem **DESABILITADO** por padrão
- ✅ **Persistência:** Configuração salva na tabela `configuracoes` do banco de dados
- ✅ **Tratamento de erros:** Em caso de erro, assume desabilitado (mais seguro)

### **Função: `controlar_cadastro_usuarios()`**

**Localização:** `main.py` (linhas 81-259)

**Acesso:**
- Apenas usuários com perfil **'master'** podem acessar
- Disponível no módulo administrativo

**Funcionalidades:**
1. **Habilitar/Desabilitar Cadastro**
   - Botão "✅ Habilitar Cadastro" → Define `cadastro_habilitado = 'true'`
   - Botão "❌ Desabilitar Cadastro" → Define `cadastro_habilitado = 'false'`

2. **Configurar Assessments Padrão**
   - Permite selecionar quais assessments serão liberados automaticamente para novos usuários
   - Salva na configuração `assessments_padrao` (lista separada por vírgulas)

**Tabela de Configurações:**
```sql
CREATE TABLE configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    descricao TEXT
);

-- Exemplos de registros:
-- chave: 'cadastro_habilitado', valor: 'true' ou 'false'
-- chave: 'assessments_padrao', valor: '01,02,03' (IDs separados por vírgula)
```

---

## 🖥️ Interface de Login e Cadastro

### **Função: `authenticate_user()`**

**Localização:** `main.py` (linhas 524-745)

**Fluxo de Decisão:**

```
┌─────────────────────────────────────────┐
│  Usuário acessa a plataforma            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  verificar_cadastro_habilitado()        │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
   TRUE            FALSE
   │               │
   │               └─► Apenas aba "Login"
   │                   (sem opção de cadastro)
   │
   └─► Abas "Login" e "Cadastro"
       (usuário pode escolher)
```

**Código de Implementação:**
```python
# Verificar se cadastro está habilitado
cadastro_habilitado = verificar_cadastro_habilitado()

if cadastro_habilitado:
    # Mostrar abas: Login e Cadastro
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Cadastro"])
    with tab1:
        # Formulário de login
    with tab2:
        cadastrar_usuario()  # ← Função de cadastro
else:
    # Apenas formulário de login (sem aba de cadastro)
    with st.form("login_form"):
        # Formulário de login apenas
```

---

## 📝 Processo de Cadastro

### **Função: `cadastrar_usuario()`**

**Localização:** `main.py` (linhas 363-522)

### **Fluxo Completo:**

```
┌─────────────────────────────────────────┐
│  1. Usuário preenche formulário         │
│     - Nome Completo *                   │
│     - E-mail *                          │
│     - Senha *                           │
│     - Confirmar Senha *                 │
│     - Empresa (opcional)                │
│     - Aceite dos termos *               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Validações no Submit                │
│     ✓ Nome não vazio                    │
│     ✓ E-mail não vazio                  │
│     ✓ Senha não vazia                   │
│     ✓ Senhas coincidem                  │
│     ✓ Termos aceitos                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Verificação de E-mail Duplicado     │
│     - Busca no banco: LOWER(email)      │
│     - Se existe → Erro                  │
│     - Se não existe → Continua          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. Geração de user_id                  │
│     - Busca MAX(user_id)                │
│     - novo_user_id = MAX + 1            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Inserção do Novo Usuário            │
│     INSERT INTO usuarios:               │
│     - user_id (gerado)                  │
│     - nome                               │
│     - email (lowercase)                 │
│     - senha (texto plano)              │
│     - perfil = 'usuario' (padrão)       │
│     - empresa (opcional)                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  6. Verificação de Inserção             │
│     - Verifica se usuário foi inserido  │
│     - Se não → Rollback e erro          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  7. Liberação de Assessments Padrão     │
│     - Busca assessments_padrao         │
│     - Para cada assessment:             │
│       INSERT INTO assessments:          │
│       - user_id                         │
│       - assessment_id                    │
│       - assessment_name                 │
│       - access_granted = 1              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  8. Commit e Finalização                │
│     - Commit da transação               │
│     - Registro no log                    │
│     - Mensagem de sucesso               │
│     - Redirecionamento para tela       │
│       de sucesso                        │
└─────────────────────────────────────────┘
```

### **Detalhamento das Etapas:**

#### **1. Formulário de Cadastro**

**Campos:**
- **Nome Completo** (obrigatório)
- **E-mail** (obrigatório, validado para duplicatas)
- **Senha** (obrigatório, tipo password)
- **Confirmar Senha** (obrigatório, tipo password)
- **Empresa** (opcional)
- **Aceite dos Termos** (obrigatório, checkbox)

**Validações em Tempo Real:**
- Verificação visual se senhas coincidem (antes do submit)

#### **2. Validações no Submit**

```python
if submit_button:
    # Validações
    if not nome.strip():
        st.error("❌ Nome completo é obrigatório!")
        return
    
    if not email.strip():
        st.error("❌ E-mail é obrigatório!")
        return
    
    if not senha:
        st.error("❌ Senha é obrigatória!")
        return
    
    if senha != confirmar_senha:
        st.error("❌ As senhas devem coincidir!")
        return
    
    if not aceite_termos:
        st.error("❌ Você deve aceitar os termos de uso!")
        return
```

#### **3. Verificação de E-mail Duplicado**

```python
cursor.execute("""
    SELECT id FROM usuarios WHERE LOWER(email) = LOWER(?)
""", (email.strip(),))
if cursor.fetchone():
    st.error("❌ Este e-mail já está cadastrado...")
    return
```

**Características:**
- ✅ Case-insensitive (LOWER)
- ✅ Verificação dentro da transação (segurança)
- ✅ Mensagem clara ao usuário

#### **4. Geração de user_id**

```python
cursor.execute("SELECT MAX(user_id) FROM usuarios")
max_user_id = cursor.fetchone()[0]
novo_user_id = (max_user_id or 0) + 1
```

**Características:**
- ✅ Incremental automático
- ✅ Trata caso de tabela vazia (or 0)

#### **5. Inserção do Usuário**

```python
cursor.execute("""
    INSERT INTO usuarios (user_id, nome, email, senha, perfil, empresa)
    VALUES (?, ?, ?, ?, ?, ?)
""", (
    novo_user_id,
    nome.strip(),
    email.strip().lower(),  # Email em lowercase
    senha,                   # Senha em texto plano
    'usuario',              # Perfil padrão
    empresa.strip() if empresa else None
))
```

**Características:**
- ✅ Email normalizado (lowercase)
- ✅ Perfil padrão: `'usuario'`
- ✅ Empresa opcional (None se vazio)

#### **6. Verificação de Inserção**

```python
cursor.execute("""
    SELECT id FROM usuarios WHERE user_id = ?
""", (novo_user_id,))
if not cursor.fetchone():
    st.error("❌ Erro: Usuário não foi inserido corretamente.")
    conn.rollback()
    return
```

**Características:**
- ✅ Verifica se inserção foi bem-sucedida
- ✅ Rollback em caso de falha

#### **7. Liberação de Assessments Padrão**

```python
assessments_padrao = obter_assessments_padrao()
if assessments_padrao:
    for assessment_id in assessments_padrao:
        cursor.execute("""
            INSERT OR REPLACE INTO assessments 
            (user_id, assessment_id, assessment_name, access_granted)
            VALUES (?, ?, ?, ?)
        """, (novo_user_id, assessment_id, f"Assessment {assessment_id}", 1))
```

**Características:**
- ✅ Libera apenas assessments configurados como padrão
- ✅ `access_granted = 1` (habilitado)
- ✅ Nome do assessment: `"Assessment {assessment_id}"`

#### **8. Finalização**

```python
# Commit
conn.commit()

# Registrar no log
registrar_acesso(
    user_id=novo_user_id,
    programa="main.py",
    acao="cadastro_usuario"
)

# Mensagem de sucesso
st.success("🎉 **Cadastro realizado com sucesso!**")

# Salvar dados no session_state
st.session_state["cadastro_sucesso"] = True
st.session_state["novo_usuario_email"] = email.strip().lower()
st.session_state["novo_usuario_nome"] = nome.strip()

# Redirecionar
time.sleep(3)
st.rerun()
```

---

## 🔄 Tela de Sucesso do Cadastro

**Quando aparece:** Após cadastro bem-sucedido, `cadastro_sucesso = True`

**Conteúdo:**
```python
st.markdown("### 🎉 Cadastro Realizado com Sucesso!")
st.success(f"**Parabéns, {nome}!** Seu cadastro foi realizado...")
st.info(f"""
    **📧 E-mail cadastrado:** {email}
    
    **🔐 Próximos passos:**
    1. Vá para a aba "Login" acima
    2. Digite seu e-mail e senha
    3. Comece a usar a plataforma!
""")
```

**Características:**
- ✅ Mostra nome do usuário
- ✅ Mostra e-mail cadastrado
- ✅ Instruções claras para próximo passo
- ✅ Informa sobre assessments liberados (se houver)

---

## ⚠️ Pontos de Atenção e Possíveis Problemas

### **1. Dados Iniciais dos Assessments**

**Problema Potencial:**
Quando um novo usuário faz login e acessa um assessment pela primeira vez, os dados iniciais (templates) precisam ser copiados do `user_id = 0` para o novo `user_id`.

**Como funciona:**
- A função `new_user()` em cada `form_model_XX.py` é chamada automaticamente
- Ela verifica se existem registros para o usuário
- Se não existem, copia dados do `user_id = 0`

**Verificação necessária:**
- ✅ Verificar se existem dados template (`user_id = 0`) para todos os assessments
- ✅ Verificar se `new_user()` está sendo chamada corretamente

### **2. Senha em Texto Plano**

**Problema de Segurança:**
```python
senha,  # Senha em texto plano
```

**Risco:**
- Senhas armazenadas sem criptografia
- Se o banco for comprometido, senhas ficam expostas

**Recomendação:**
- Considerar usar hash (bcrypt, argon2, etc.)
- Implementar hash na inserção e verificação

### **3. Validação de E-mail**

**Atual:**
- Verifica apenas duplicatas
- Não valida formato de e-mail

**Recomendação:**
- Adicionar validação de formato (regex ou biblioteca)
- Verificar se e-mail é válido antes de inserir

### **4. Validação de Senha**

**Atual:**
- Apenas verifica se não está vazia
- Não verifica força da senha

**Recomendação:**
- Adicionar critérios de senha forte:
  - Mínimo de caracteres
  - Letras maiúsculas e minúsculas
  - Números
  - Caracteres especiais

### **5. Assessments Padrão**

**Funcionamento:**
- Se nenhum assessment padrão estiver configurado, novo usuário não terá acesso a nenhum assessment
- Usuário precisará que administrador libere manualmente

**Recomendação:**
- Considerar sempre liberar pelo menos um assessment padrão
- Ou mostrar aviso claro ao administrador ao desabilitar todos

### **6. Inicialização de Dados**

**Fluxo Atual:**
1. Usuário se cadastra
2. Assessments são liberados na tabela `assessments`
3. Quando usuário acessa assessment pela primeira vez, `new_user()` copia dados do `user_id = 0`

**Possível Melhoria:**
- Inicializar dados de todos os assessments liberados no momento do cadastro
- Evitar delay na primeira utilização

---

## 📊 Estrutura de Dados

### **Tabela: `usuarios`**

```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha TEXT NOT NULL,        -- ⚠️ Texto plano
    perfil TEXT DEFAULT 'usuario',
    empresa TEXT,
    -- outros campos...
);
```

**Campos do Cadastro:**
- `user_id`: Gerado automaticamente (MAX + 1)
- `nome`: Nome completo do usuário
- `email`: E-mail em lowercase
- `senha`: Senha em texto plano
- `perfil`: Sempre `'usuario'` para novos cadastros
- `empresa`: Opcional (pode ser NULL)

### **Tabela: `assessments`**

```sql
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    assessment_id TEXT NOT NULL,
    assessment_name TEXT,
    access_granted INTEGER DEFAULT 0,  -- 0 = negado, 1 = permitido
    -- outros campos...
);
```

**Dados Criados no Cadastro:**
- Para cada assessment em `assessments_padrao`:
  - `user_id`: ID do novo usuário
  - `assessment_id`: ID do assessment (ex: "01", "02")
  - `assessment_name`: `"Assessment {assessment_id}"`
  - `access_granted`: `1` (permitido)

### **Tabela: `configuracoes`**

```sql
CREATE TABLE configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    descricao TEXT
);
```

**Configurações Relacionadas:**
- `cadastro_habilitado`: `'true'` ou `'false'`
- `assessments_padrao`: `'01,02,03'` (IDs separados por vírgula)

---

## 🔍 Análise de Segurança

### **Pontos Fortes:**
- ✅ Cadastro desabilitado por padrão
- ✅ Apenas usuários 'master' podem habilitar
- ✅ Verificação de e-mail duplicado
- ✅ Validações de campos obrigatórios
- ✅ Aceite de termos obrigatório
- ✅ Registro de ações no log

### **Pontos de Melhoria:**
- ⚠️ **Senha em texto plano** (alta prioridade)
- ⚠️ **Validação de formato de e-mail** (média prioridade)
- ⚠️ **Validação de força de senha** (média prioridade)
- ⚠️ **Rate limiting** para cadastros (baixa prioridade)
- ⚠️ **Captcha** para prevenir bots (baixa prioridade)

---

## 🔄 Fluxo Completo Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    TELA DE LOGIN                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  verificar_cadastro_habilitado()                   │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                       │
│            ┌────────┴────────┐                             │
│            │                 │                              │
│            ▼                 ▼                              │
│      TRUE (Habilitado)  FALSE (Desabilitado)               │
│            │                 │                              │
│            │                 └─► Apenas aba "Login"         │
│            │                                                 │
│            ▼                                                 │
│  ┌─────────────────────────────────────┐                 │
│  │  Abas: [Login] [Cadastro]            │                 │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Usuário clica em "Cadastro"         │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  cadastrar_usuario()                │                   │
│  │  - Formulário de cadastro           │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Usuário preenche e submete         │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Validações                         │                   │
│  │  ✓ Campos obrigatórios              │                   │
│  │  ✓ Senhas coincidem                 │                   │
│  │  ✓ E-mail não duplicado             │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Inserção no Banco                   │                   │
│  │  - INSERT INTO usuarios              │                   │
│  │  - Gerar user_id                     │                   │
│  │  - Perfil = 'usuario'                │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Liberar Assessments Padrão         │                   │
│  │  - obter_assessments_padrao()       │                   │
│  │  - INSERT INTO assessments          │                   │
│  │    (para cada assessment padrão)    │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Commit e Log                        │                   │
│  │  - conn.commit()                     │                   │
│  │  - registrar_acesso()                │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Tela de Sucesso                     │                   │
│  │  - Mensagem de parabéns              │                   │
│  │  - Instruções para login             │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Usuário faz Login                   │                   │
│  │  - Usa e-mail e senha cadastrados   │                   │
│  └──────────────────┬────────────────────┘                 │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │  Acesso à Plataforma                 │                   │
│  │  - Assessments liberados           │                   │
│  │  - Dados inicializados na 1ª vez    │                   │
│  └─────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Checklist de Funcionamento

### **Pré-requisitos:**
- [ ] Tabela `configuracoes` existe
- [ ] Tabela `usuarios` existe
- [ ] Tabela `assessments` existe
- [ ] Dados template (`user_id = 0`) existem para todos os assessments

### **Configuração Administrativa:**
- [ ] Cadastro habilitado via `controlar_cadastro_usuarios()`
- [ ] Assessments padrão configurados (se desejado)
- [ ] Apenas usuários 'master' podem configurar

### **Interface de Cadastro:**
- [ ] Aba "Cadastro" aparece quando habilitado
- [ ] Formulário completo e funcional
- [ ] Validações funcionando
- [ ] Mensagens de erro claras

### **Processo de Cadastro:**
- [ ] Validação de campos obrigatórios
- [ ] Verificação de e-mail duplicado
- [ ] Geração de user_id
- [ ] Inserção do usuário
- [ ] Liberação de assessments padrão
- [ ] Registro no log

### **Pós-Cadastro:**
- [ ] Tela de sucesso aparece
- [ ] Usuário pode fazer login
- [ ] Assessments liberados aparecem
- [ ] Dados iniciais são copiados na primeira utilização

---

## 🔧 Recomendações de Melhorias

### **1. Segurança (Alta Prioridade)**

**Criptografia de Senhas:**
```python
import hashlib
# ou melhor ainda:
import bcrypt

# No cadastro:
senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

# No login:
if bcrypt.checkpw(password.encode('utf-8'), senha_hash):
    # Login válido
```

### **2. Validações (Média Prioridade)**

**Validação de E-mail:**
```python
import re

def validar_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

**Validação de Senha Forte:**
```python
def validar_senha_forte(senha):
    if len(senha) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    if not re.search(r'[A-Z]', senha):
        return False, "Senha deve conter letra maiúscula"
    if not re.search(r'[a-z]', senha):
        return False, "Senha deve conter letra minúscula"
    if not re.search(r'\d', senha):
        return False, "Senha deve conter número"
    return True, "Senha válida"
```

### **3. Inicialização de Dados (Média Prioridade)**

**Inicializar Dados no Cadastro:**
```python
# Após liberar assessments, inicializar dados
for assessment_id in assessments_padrao:
    # Carregar módulo do assessment
    form_module = importlib.import_module(f"paginas.form_model_{assessment_id}")
    new_user_func = getattr(form_module, "new_user", None)
    
    if new_user_func:
        # Inicializar dados do assessment
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        new_user_func(cursor, novo_user_id)
        conn.commit()
        conn.close()
```

### **4. Experiência do Usuário (Baixa Prioridade)**

**Login Automático Após Cadastro:**
```python
# Após cadastro bem-sucedido, fazer login automático
st.session_state["logged_in"] = True
st.session_state["user_profile"] = 'usuario'
st.session_state["user_id"] = novo_user_id
st.session_state["user_name"] = nome.strip()
st.rerun()
```

**Confirmação por E-mail:**
- Enviar e-mail de confirmação
- Link de ativação
- Verificação de e-mail válido

---

## 📝 Resumo Executivo

### **Funcionamento Atual:**
1. ✅ Cadastro controlado por configuração administrativa
2. ✅ Aba "Cadastro" aparece apenas se habilitado
3. ✅ Processo de cadastro completo e funcional
4. ✅ Validações básicas implementadas
5. ✅ Assessments padrão são liberados automaticamente
6. ✅ Dados iniciais são copiados na primeira utilização

### **Pontos Fortes:**
- Sistema seguro por padrão (cadastro desabilitado)
- Controle administrativo completo
- Validações básicas funcionando
- Integração com sistema de permissões

### **Pontos de Atenção:**
- ⚠️ Senha em texto plano (risco de segurança)
- ⚠️ Falta validação de formato de e-mail
- ⚠️ Falta validação de força de senha
- ⚠️ Dados iniciais só são copiados na primeira utilização (pode causar delay)

### **Recomendações:**
1. **Alta Prioridade:** Implementar criptografia de senhas
2. **Média Prioridade:** Adicionar validações de e-mail e senha
3. **Média Prioridade:** Inicializar dados no momento do cadastro
4. **Baixa Prioridade:** Login automático após cadastro

---

**Criado em:** 09/11/2025  
**Autor:** Análise do Sistema  
**Versão:** 1.0

