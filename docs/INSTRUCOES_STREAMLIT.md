# Instruções Operacionais - Streamlit

## Regra: Estilização de Fontes no Streamlit

### Problema Identificado
Ao tentar ajustar tamanhos de fonte e estilos em elementos do Streamlit usando CSS global ou classes CSS, ocorrem conflitos com os estilos padrão do Streamlit, resultando em alterações que não são aplicadas corretamente.

### Solução Recomendada
**Usar HTML com estilo inline diretamente no `st.markdown()` ao invés de CSS global ou classes CSS.**

### Exemplo Prático

#### ❌ NÃO RECOMENDADO (CSS Global - causa conflitos)
```python
st.markdown("""
    <style>
        .titulo-custom {
            font-size: 42px !important;
        }
    </style>
""", unsafe_allow_html=True)
st.markdown('<p class="titulo-custom">Título</p>', unsafe_allow_html=True)
```

#### ✅ RECOMENDADO (HTML com estilo inline)
```python
st.markdown(f"""
    <h2 style="text-align: center; font-size: 42px; font-weight: 600; color: #2c3e50; margin: 20px 0; padding: 12px;">{msg}</h2>
""", unsafe_allow_html=True)
```

### Vantagens da Abordagem HTML Inline
1. **Evita conflitos**: Não interfere com os estilos padrão do Streamlit
2. **Mais direto**: Estilo aplicado diretamente no elemento
3. **Mais confiável**: Menos propenso a problemas de especificidade CSS
4. **Mais simples**: Não requer CSS global que pode afetar outros elementos

### Quando Usar
- Ajustar tamanhos de fonte de títulos, subtítulos e textos
- Personalizar cores, espaçamentos e alinhamentos
- Aplicar estilos específicos a elementos individuais

### Quando NÃO Usar
- Estilos que precisam ser aplicados a múltiplos elementos (neste caso, considere criar uma função helper)
- Estilos muito complexos que requerem media queries ou seletores avançados

### Caso de Uso Real
**Localização**: `paginas/resultados_04.py`, função `grafico_barra()`, linhas 368-372

```python
# Adiciona o título antes do gráfico usando HTML direto
if msg:
    st.markdown(f"""
        <h2 style="text-align: center; font-size: 42px; font-weight: 600; color: #2c3e50; margin: 20px 0; padding: 12px; letter-spacing: 0.5px;">{msg}</h2>
    """, unsafe_allow_html=True)
```

### Tags HTML Recomendadas
- `<h1>`, `<h2>`, `<h3>` - Para títulos e subtítulos
- `<p>` - Para parágrafos
- `<div>` - Para containers
- `<span>` - Para elementos inline

### Notas Importantes
- Sempre usar `unsafe_allow_html=True` no `st.markdown()`
- Usar aspas duplas (`"`) para o atributo `style` e aspas simples (`'`) para o `st.markdown()` ou vice-versa para evitar conflitos
- Testar em diferentes navegadores para garantir compatibilidade

---
**Data de criação**: 06/01/2026  
**Última atualização**: 06/01/2026  
**Contexto**: Resolução de problema com ajuste de fonte do título de gráfico no Streamlit

