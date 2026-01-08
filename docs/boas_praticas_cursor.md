# 📘 Boas Práticas para Codificação com IA

**Data do documento:** 29/07/2025  
**Projeto:** Python + Streamlit + SQLite  
**IDE:** Cursor  
**Infra:** Render.com (cloud, com disco persistente SSD)  
**Deploy:** via GitHub

---

## 🧱 Estrutura Lógica do Sistema

- A lógica simula uma planilha Excel, usando o modelo célula (letra + número), ex: `B9`, `C789`, `DC9876`.
- Exemplo prático:  
  Quando a palavra `formulaH` é encontrada na coluna `type`, o sistema usará a fórmula da coluna `math_element`.

---

## 🧑‍💻 Boas Práticas ao Criar um Novo Arquivo Python

Inclua sempre no início:

```python
# <nome do programa>
# <função/funcionalidade>
# <data e hora da atualização>
```

---

## 🌐 Atualizações e Recomendações do Streamlit

### 1. Query Parameters
- ✅ Usar: `st.query_params`  
- ❌ Não usar: `st.experimental_get_query_params` (obsoleto)

### 2. Títulos e Textos
- Evitar `<h1>` a `<h6>` — preferir `<p>` para impedir criação automática de âncoras (hash-links)
- Exemplo de uso recomendado:
```python
st.markdown("""
<p style='
    text-align: center;
    font-size: 40px;
    font-weight: bold;
'>Título</p>
""", unsafe_allow_html=True)
```

### 3. Destaque Visual em Tabelas
- Exemplo para coluna de configuração ou destaque:
```python
st.markdown("""
<div style='background-color:#f0f0f0;padding:10px;border-radius:5px;color:#ff0000;font-size:16px;'>Recomenda</div>
""", unsafe_allow_html=True)
```

### 4. Comentários em SQL
- ❌ Evitar comentários com `#` dentro de queries SQL.
- ✅ Remova os comentários para evitar erros como:  
  `unrecognized token: "#"`

### 5. Parâmetros obsoletos
- ❌ `use_column_width` (obsoleto)  
- ✅ Usar: `use_container_width` no lugar

---

## 🐞 Práticas de Debug

### 6. Comentário padrão
- Use `# Debug` nos prints temporários para facilitar busca e limpeza.

### 7. Local de saída
- Preferir que o debug apareça no **terminal da IDE Cursor**, e não via Streamlit.

---

## 🚫 Restrições de Criação Automática

### 8. Importante:
- ❌ Nunca criar via código:
  - Banco de dados
  - Tabelas
  - Pastas
- ✅ Apenas emitir `warnings` preventivos se algo estiver ausente.

---

## 📌 Instruções Importantes de Implementação

1. Implemente **passo a passo**, com cuidado para não quebrar o app.
2. Aguarde **feedback do usuário antes de seguir** para o próximo passo.
3. **Só inicie após receber instrução clara do objetivo do dia.**
4. Modificações nas tabelas do banco de dados **serão feitas manualmente** pelo usuário.  
   - ❌ Não sugerir código para esta tarefa.
5. Criar um **arquivo `.txt` documentando as alterações**, incluindo:  
   - Descrição da alteração  
   - Programa afetado  
   - Linha modificada
6. Salvar os arquivos `.txt` da documentação de alterações na pasta: `\manutencao\`
