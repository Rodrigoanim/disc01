# texto_manager.py
# Sistema de gerenciamento de textos externos com suporte multi-idioma
# Data: 03/08/2025 - Hora: 21:15

import os
import sqlite3
from config import DB_PATH

# Cache global para evitar múltiplas leituras de arquivo
_TEXTOS_CACHE = {}
_USER_LANGUAGE_CACHE = {}

def get_user_language(user_id=None):
    """
    Obtém o idioma do usuário logado
    
    Args:
        user_id (str, optional): ID do usuário. Se None, tenta obter da sessão
        
    Returns:
        str: Código do idioma ('pt', 'en', 'es') ou 'pt' como padrão
    """
    global _USER_LANGUAGE_CACHE
    
    # Se já foi consultado, retorna do cache
    if user_id in _USER_LANGUAGE_CACHE:
        return _USER_LANGUAGE_CACHE[user_id]
    
    # Verificar se é usuário temporário (para tela de login)
    if user_id and user_id.startswith('temp_'):
        language = user_id.split('_')[1]
        if language in ['pt', 'en', 'es']:
            _USER_LANGUAGE_CACHE[user_id] = language
            return language
    
    # Se não foi fornecido user_id, tenta obter da sessão do Streamlit
    if user_id is None:
        try:
            import streamlit as st
            user_id = st.session_state.get('user_id')
        except ImportError:
            # Streamlit não disponível, retorna padrão
            return 'pt'
    
    if not user_id:
        return 'pt'
    
    try:
        # Verifica se o banco existe
        if not DB_PATH.exists():
            return 'pt'
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verifica se a coluna idioma existe
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'idioma' not in columns:
            # Coluna não existe, retorna padrão
            conn.close()
            return 'pt'
        
        # Busca o idioma do usuário
        cursor.execute("SELECT idioma FROM usuarios WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result and result[0]:
            language = result[0]
            # Valida se é um idioma suportado
            if language in ['pt', 'en', 'es']:
                _USER_LANGUAGE_CACHE[user_id] = language
                return language
        
        # Se não encontrou ou idioma inválido, retorna padrão
        _USER_LANGUAGE_CACHE[user_id] = 'pt'
        return 'pt'
        
    except Exception as e:
        print(f"⚠️ AVISO: Erro ao obter idioma do usuário: {str(e)}")
        return 'pt'

def _carregar_textos_base(language='pt'):
    """
    Carrega todos os textos do arquivo específico do idioma
    
    Args:
        language (str): Código do idioma ('pt', 'en', 'es')
        
    Returns:
        dict: Dicionário com chave->valor dos textos
    """
    global _TEXTOS_CACHE
    
    # Se já foi carregado para este idioma, retorna do cache
    if language in _TEXTOS_CACHE:
        return _TEXTOS_CACHE[language]
    
    # Define o nome do arquivo baseado no idioma
    if language == 'pt':
        arquivo_textos = 'variavel_texto.txt'
    else:
        arquivo_textos = f'variavel_texto_{language}.txt'
    
    textos = {}
    
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(arquivo_textos):
            print(f"⚠️ AVISO: Arquivo {arquivo_textos} não encontrado! Usando português como fallback.")
            # Se não existe arquivo específico, tenta carregar português
            if language != 'pt':
                return _carregar_textos_base('pt')
            else:
                _TEXTOS_CACHE[language] = {}
                return {}
        
        # Carrega os textos
        with open(arquivo_textos, 'r', encoding='utf-8') as f:
            for numero_linha, linha in enumerate(f, 1):
                linha = linha.strip()
                
                # Ignora linhas vazias e comentários
                if not linha or linha.startswith('#'):
                    continue
                
                # Processa linhas com formato chave=valor
                if '=' in linha:
                    try:
                        chave, valor = linha.split('=', 1)
                        chave = chave.strip()
                        valor = valor.strip()
                        textos[chave] = valor
                    except Exception as e:
                        print(f"⚠️ AVISO: Linha {numero_linha} inválida no arquivo de textos: {linha}")
        
        # Armazena no cache
        _TEXTOS_CACHE[language] = textos
        return textos
        
    except Exception as e:
        print(f"❌ ERRO: Falha ao carregar textos para idioma {language}: {str(e)}")
        _TEXTOS_CACHE[language] = {}
        return {}

def get_texto(chave, default=None, user_id=None):
    """
    Obtém um texto específico do carregamento global baseado no idioma do usuário
    
    Args:
        chave (str): Chave do texto
        default (str, optional): Valor padrão se não encontrado
        user_id (str, optional): ID do usuário para determinar idioma
        
    Returns:
        str: Texto correspondente ou valor padrão
    """
    # Obtém o idioma do usuário
    language = get_user_language(user_id)
    
    # Carrega textos para o idioma específico
    textos = _carregar_textos_base(language)
    
    if chave not in textos:
        if default is None:
            return f"[TEXTO_{chave}_NÃO_ENCONTRADO]"
        return default
    
    return textos[chave]

def carregar_textos(user_id=None):
    """
    Carrega todos os textos com cache do Streamlit (quando disponível)
    
    Args:
        user_id (str, optional): ID do usuário para determinar idioma
        
    Returns:
        dict: Dicionário com chave->valor dos textos
    """
    try:
        import streamlit as st
        
        @st.cache_data
        def _carregar_textos_cached():
            language = get_user_language(user_id)
            return _carregar_textos_base(language)
        
        return _carregar_textos_cached()
    except ImportError:
        # Streamlit não está disponível, usa versão básica
        language = get_user_language(user_id)
        return _carregar_textos_base(language)

def inicializar_textos():
    """Inicializa o sistema de textos após configuração do Streamlit"""
    # Força recarregamento com cache do Streamlit
    global _TEXTOS_CACHE, _USER_LANGUAGE_CACHE
    _TEXTOS_CACHE = {}  # Limpa cache para forçar recarregamento com Streamlit
    _USER_LANGUAGE_CACHE = {}  # Limpa cache de idiomas
    return carregar_textos()

def set_user_language(user_id, language):
    """
    Define o idioma do usuário no banco de dados
    
    Args:
        user_id (str): ID do usuário
        language (str): Código do idioma ('pt', 'en', 'es')
    """
    if language not in ['pt', 'en', 'es']:
        print(f"⚠️ AVISO: Idioma '{language}' não suportado. Usando 'pt'.")
        language = 'pt'
    
    try:
        if not DB_PATH.exists():
            print("⚠️ AVISO: Banco de dados não encontrado!")
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verifica se a coluna idioma existe
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'idioma' not in columns:
            print("⚠️ AVISO: Coluna 'idioma' não existe na tabela usuarios!")
            conn.close()
            return False
        
        # Atualiza o idioma do usuário
        cursor.execute("UPDATE usuarios SET idioma = ? WHERE user_id = ?", (language, user_id))
        
        if cursor.rowcount == 0:
            print(f"⚠️ AVISO: Usuário {user_id} não encontrado!")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        # Limpa cache do idioma para forçar recarregamento
        if user_id in _USER_LANGUAGE_CACHE:
            del _USER_LANGUAGE_CACHE[user_id]
        
        print(f"✅ Idioma do usuário {user_id} alterado para {language}")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Falha ao alterar idioma do usuário: {str(e)}")
        return False