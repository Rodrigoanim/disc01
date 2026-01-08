---

### **Manual de Boas Práticas e Guia de Referência Detalhado do Streamlit**

Este documento serve como uma referência técnica completa para a equipe de desenvolvimento. O objetivo é fornecer um entendimento profundo dos conceitos, funcionalidades e melhores práticas ao utilizar o framework Streamlit com Python.

#### **1. O Modelo de Execução do Streamlit**

1.1. **Filosofia Central: Script como App**
    1.1.1. O Streamlit foi projetado para transformar scripts de dados em aplicações web interativas com o mínimo de esforço. A principal filosofia é que cada aplicação é simplesmente um script Python que é executado de cima para baixo.
    1.1.2. Não há necessidade de definir rotas, callbacks complexos ou gerenciar o estado do frontend. O framework abstrai essas complexidades.

1.2. **O Fluxo de Re-execução (Rerun)**
    1.2.1. O pilar da interatividade no Streamlit é o seu modelo de re-execução. O script Python inteiro é re-executado do início ao fim sempre que:
        1.2.1.1. O código-fonte do script é modificado e salvo.
        1.2.1.2. Um usuário interage com um widget na interface da aplicação (e.g., move um slider, clica em um botão, insere texto).
    1.2.2. A cada re-execução, a interface do usuário é redesenhada com os valores atualizados, garantindo que o que é exibido na tela seja sempre um reflexo direto do estado atual do código e das variáveis.
    1.2.3. **Callbacks e Ordem de Execução**: Se um widget possui um callback associado (através dos parâmetros `on_change` ou `on_click`), essa função de callback é executada *antes* da re-execução do restante do script.

#### **2. Executando sua Aplicação**

2.1. **Comando Principal**
    2.1.1. Para executar uma aplicação Streamlit, utilize o seguinte comando no seu terminal, a partir do diretório do projeto:
        ```bash
        streamlit run seu_script.py
        ```
    2.1.2. Este comando inicia um servidor web local e abre a sua aplicação em uma nova aba do navegador.

2.2. **Execução como Módulo Python**
    2.2.1. Uma alternativa, útil para configurações em IDEs como o PyCharm, é executar o Streamlit como um módulo:
        ```bash
        python -m streamlit run seu_script.py
        ```

2.3. **Argumentos de Linha de Comando**
    2.3.1. Para passar argumentos para o seu próprio script, utilize `--` para separá-los dos argumentos do Streamlit.
        ```bash
        streamlit run seu_script.py -- --meu_argumento valor
        ```

2.4. **Executando de uma URL**
    2.4.1. É possível executar um script diretamente de uma URL, o que é especialmente útil para compartilhar gists do GitHub.
        ```bash
        streamlit run https://raw.githubusercontent.com/streamlit/demo-uber-nyc-pickups/master/streamlit_app.py
        ```

#### **3. Exibição de Dados e Elementos Visuais**

3.1. **Magic Commands e `st.write()`**
    3.1.1. **Magic Commands**: Streamlit permite "magia". Qualquer variável, literal, ou DataFrame do Pandas colocado em sua própria linha no script será automaticamente renderizado na aplicação usando `st.write()`.
        ```python
        # Exemplo de Magic Command
        import pandas as pd
        df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        df # O DataFrame será renderizado aqui
        ```
    3.1.2. **`st.write()`**: Considerado o "canivete suíço" do Streamlit, `st.write()` é um comando versátil que inspeciona o tipo do dado passado e decide a melhor forma de renderizá-lo. Aceita múltiplos argumentos.
        3.1.2.1. **Tipos Suportados**: `st.write()` pode renderizar strings (como Markdown), dataframes, dicionários, listas, figuras do Matplotlib, gráficos do Altair, e muitos outros tipos de objetos.
        3.1.2.2. **Quando usar Comandos Específicos**: Embora `st.write()` seja poderoso, opte por comandos mais específicos (como `st.dataframe()` ou `st.line_chart()`) quando precisar de mais customização ou quando quiser modificar o elemento retornado posteriormente.

3.2. **Elementos de Texto**
    3.2.1. **Títulos e Cabeçalhos**: Use `st.title()`, `st.header()` e `st.subheader()` para estruturar hierarquicamente o conteúdo textual.
    3.2.2. **Markdown**: `st.markdown()` renderiza texto formatado com GitHub-flavored Markdown. Suporta emojis, LaTeX, e cores.
        *Exemplo de cores*: `st.markdown(':red[Texto em vermelho]')`
    3.2.3. **Código, Texto Pré-formatado e LaTeX**:
        * `st.code()`: Exibe um bloco de código com destaque de sintaxe opcional.
        * `st.text()`: Exibe texto de largura fixa, sem formatação Markdown.
        * `st.latex()`: Renderiza expressões matemáticas em LaTeX.

3.3. **Elementos de Dados Tabulares**
    3.3.1. **`st.dataframe(df)`**: Renderiza um DataFrame do Pandas (ou similar) como uma tabela interativa, permitindo ordenação, busca e rolagem.
        3.3.1.1. **Estilização**: Aceita objetos `Styler` do Pandas para formatação condicional, como destacar valores máximos: `st.dataframe(df.style.highlight_max(axis=0))`.
    3.3.2. **`st.table(df)`**: Exibe uma tabela estática. Todo o conteúdo da tabela é renderizado de uma vez, sem rolagem. Ideal para tabelas menores.
    3.3.3. **`st.metric(label, value, delta)`**: Exibe uma métrica em destaque, com um valor principal e um indicador opcional de mudança (`delta`).

3.4. **Gráficos e Mapas**
    3.4.1. **Gráficos Nativos**: Para visualizações rápidas, utilize `st.line_chart()`, `st.bar_chart()`, `st.area_chart()` e `st.scatter_chart()`.
    3.4.2. **Bibliotecas Externas**: Streamlit possui suporte nativo para as principais bibliotecas de visualização, como Matplotlib (`st.pyplot()`), Altair (`st.altair_chart()`), Plotly (`st.plotly_chart()`), e outras.
    3.4.3. **Mapas**: `st.map()` é um atalho para exibir pontos de dados de latitude/longitude em um mapa. Para mapas mais complexos e customizáveis, use `st.pydeck_chart()`.

3.5. **Mídia**
    3.5.1. Use `st.image()`, `st.audio()` e `st.video()` para exibir arquivos de mídia a partir de um caminho local, URL ou bytes em memória.

#### **4. Widgets Interativos**

4.1. **Conceito Fundamental**: Widgets são tratados como variáveis no código. O valor retornado por um widget em um dado momento é o seu estado atual naquela re-execução do script.

4.2. **Botões**
    4.2.1. **`st.button(label)`**: Retorna `True` no exato momento (na re-execução) em que é clicado, e `False` em todas as outras execuções. Ideal para disparar ações.
    4.2.2. **`st.download_button(...)`**: Permite que o usuário baixe dados (texto, CSV, arquivos binários) diretamente do app.
    4.2.3. **`st.link_button(label, url)`**: Um botão que abre uma URL em uma nova aba.

4.3. **Seleção e Opções**
    4.3.1. **`st.checkbox(label)`**: Retorna `True` se a caixa estiver marcada.
    4.3.2. **`st.radio(label, options)`**: Apresenta uma lista de opções onde apenas uma pode ser selecionada.
    4.3.3. **`st.selectbox(label, options)`**: Um menu dropdown para seleção de uma única opção.
    4.3.4. **`st.multiselect(label, options)`**: Similar ao selectbox, mas permite a seleção de múltiplas opções, retornando uma lista.

4.4. **Entrada de Dados**
    4.4.1. **Texto**: `st.text_input()` para uma única linha de texto e `st.text_area()` para múltiplas linhas.
    4.4.2. **Números**: `st.number_input()` para entrada numérica com botões de incremento/decremento.
    4.4.3. **Datas e Horas**: `st.date_input()` e `st.time_input()` para seleção de datas e horários.
    4.4.4. **Arquivos**: `st.file_uploader()` permite o upload de um ou mais arquivos pelo usuário. `st.camera_input()` permite capturar uma imagem da webcam do usuário.

4.5. **Sliders**
    4.5.1. **`st.slider(label, min_value, max_value)`**: Um controle deslizante para selecionar um valor numérico ou um intervalo (passando uma tupla como valor).
    4.5.2. **`st.select_slider(label, options)`**: Similar ao slider, mas seleciona um valor de uma lista de opções, não necessariamente numéricas.

#### **5. Layout e Estrutura da Aplicação**

5.1. **`st.sidebar`**: Adiciona elementos a uma barra lateral à esquerda da aplicação. Qualquer comando pode ser chamado no objeto sidebar (e.g., `st.sidebar.title(...)`) ou dentro de um bloco `with st.sidebar:`.

5.2. **Colunas com `st.columns()`**
    5.2.1. `st.columns(spec)` cria containers lado a lado. `spec` pode ser um inteiro (para colunas de larguras iguais) ou uma lista de números (para larguras relativas, e.g., `[2, 1]` cria duas colunas, a primeira com o dobro da largura da segunda).
    5.2.2. Elementos são adicionados às colunas usando a notação `with`.

5.3. **Containers e Organização**
    5.3.1. **`st.container()`**: Cria um container "invisível" que pode ser usado para agrupar elementos e inseri-los fora da ordem sequencial do script.
    5.3.2. **`st.expander(label)`**: Cria um container recolhível. O conteúdo dentro do `with st.expander(...)` só é visível quando o usuário o expande.
    5.3.3. **`st.tabs(list_of_labels)`**: Cria um conjunto de abas, retornando um container para cada aba.

5.4. **Aplicações Multi-Página**
    5.4.1. **Método `pages/`**: A forma mais simples de criar múltiplas páginas é criar um diretório chamado `pages` na raiz do projeto. Cada arquivo `.py` dentro desse diretório se torna uma página navegável na barra lateral.
        5.4.1.1. A ordem e o nome das páginas são inferidos a partir dos nomes dos arquivos. Use prefixos numéricos para ordenar (e.g., `1_Página_Principal.py`).
    5.4.2. **Método `st.navigation` (Recomendado)**: Para controle total sobre a navegação, use `st.Page()` para definir cada página (a partir de um arquivo ou função) e `st.navigation()` no seu script de entrada para construir o menu de navegação. Este método permite menus dinâmicos e condicionais.

#### **6. Performance: Caching**

6.1. **A Necessidade do Cache**: Como o script re-executa a cada interação, operações custosas (carregar grandes datasets, treinar modelos, fazer chamadas de API) degradariam a performance. O cache do Streamlit evita re-computações desnecessárias.

6.2. **`@st.cache_data`**: O decorador principal para cache. Use-o para funções que retornam "dados" serializáveis (DataFrames, arrays, dicionários, strings, etc.).
    6.2.1. **Como Funciona**: `st.cache_data` cria um hash do código da função e dos valores de seus parâmetros de entrada. Se a combinação já foi executada, ele retorna o resultado do cache. Importante: ele retorna uma *cópia* do dado, o que o torna seguro contra mutações acidentais que poderiam afetar outras sessões.
    6.2.2. **Parâmetros de Controle**:
        * `ttl` (Time To Live): Define por quanto tempo (em segundos) o cache é válido. Essencial para dados que podem ficar desatualizados (e.g., `ttl=3600` para atualizar a cada hora).
        * `max_entries`: Limita o número de entradas no cache para controlar o uso de memória.

6.3. **`@st.cache_resource`**: Use este decorador para "recursos" globais, que são caros para criar e geralmente não são serializáveis, como conexões de banco de dados e modelos de Machine Learning.
    6.3.1. **Comportamento de Singleton**: Diferente do `cache_data`, `cache_resource` retorna a *mesma instância* do objeto em cada chamada. Isso economiza memória, mas significa que qualquer mutação no objeto será compartilhada entre todas as sessões do app. O objeto retornado deve ser thread-safe.

#### **7. Gerenciamento de Estado com `st.session_state`**

7.1. **O que é**: `st.session_state` é um objeto, similar a um dicionário, que persiste através das re-execuções do script *dentro de uma mesma sessão de usuário*. Cada usuário (cada aba do navegador) tem seu próprio `session_state` isolado.

7.2. **Casos de Uso**:
    7.2.1. Manter valores entre interações (e.g., um contador de cliques).
    7.2.2. Passar informações entre páginas de uma aplicação multi-página.
    7.2.3. Armazenar o estado de widgets que podem ser removidos e re-adicionados dinamicamente à tela.

7.3. **Utilização Prática**:
    7.3.1. **Inicialização**: Sempre verifique a existência de uma chave antes de usá-la para evitar erros. A inicialização deve ocorrer apenas uma vez por sessão.
        ```python
        if 'contador' not in st.session_state:
            st.session_state.contador = 0
        ```
    7.3.2. **Leitura e Escrita**: Acesse e modifique os valores usando a sintaxe de dicionário (`st.session_state['chave']`) ou de atributo (`st.session_state.chave`).

7.4. **Integração com Widgets**: Todo widget que possui um parâmetro `key` tem seu estado automaticamente vinculado ao `st.session_state`. Por exemplo, `st.text_input("Nome", key="nome")` permite acessar o valor do input a qualquer momento via `st.session_state.nome`.

#### **8. Conexões e Gerenciamento de Segredos**

8.1. **`st.connection()`**: Uma forma simplificada e gerenciada pelo Streamlit para se conectar a fontes de dados como bancos SQL. Ele gerencia o cache da conexão automaticamente, usando `@st.cache_resource` internamente.

8.2. **Gerenciamento de Segredos (`secrets.toml`)**:
    8.2.1. Nunca armazene credenciais (senhas, chaves de API) diretamente no código. Crie um arquivo `.streamlit/secrets.toml` no diretório do seu projeto.
    8.2.2. Este arquivo deve ser adicionado ao seu `.gitignore` para não ser enviado ao seu repositório de código.
    8.2.3. Os segredos definidos neste arquivo são acessíveis através do objeto `st.secrets` (e.g., `st.secrets["db_credentials"]["password"]`).
    8.2.4. Ao fazer o deploy na Streamlit Community Cloud, os segredos devem ser configurados na interface da plataforma.

#### **9. Customização e Funcionalidades Adicionais**

9.1. **Temas**: A aparência da aplicação (cores, fontes) pode ser customizada no arquivo `.streamlit/config.toml` na seção `[theme]`.

9.2. **Aplicações Multi-Página (`pages/`)**: Crie um diretório chamado `pages` na raiz do projeto. Cada arquivo `.py` neste diretório será uma página navegável.

9.3. **Servindo Arquivos Estáticos**: Para servir imagens ou outros arquivos diretamente via URL, habilite `enableStaticServing = true` em `config.toml` e coloque os arquivos em um diretório chamado `static` na raiz do projeto.

9.4. **Testes de Aplicação**: Streamlit possui um framework de testes nativo (`AppTest`) que permite simular a execução do app, interagir com widgets e inspecionar os resultados de forma programática, facilitando a criação de testes automatizados com ferramentas como `pytest`.