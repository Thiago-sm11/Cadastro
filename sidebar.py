import streamlit as st
import pandas as pd
import io
from PIL import Image
import base64 # Importe a biblioteca base64
import datetime # Importe datetime para lidar com datas
import sql_funcoes as sf

# Certifique-se que o arquivo Inicio.py está na mesma pasta
from Inicio import gerenciar_estoque_completo

# Inicialização das chaves de session_state
if "estoque" not in st.session_state:
    # ATUALIZAÇÃO IMPORTANTE: Incluindo "Data de Compra" na inicialização do DataFrame
    st.session_state["estoque"] = pd.DataFrame(columns=[
        "Nome do Produto", "Quantidade", "Preço de Compra (R$)",
        "Imagem", "Cor da Tag", "Estoque Mínimo", "Data de Compra","Descrição Produto" # <-- Adicionado aqui
    ])
if "produto_selecionado_id" not in st.session_state:
    st.session_state["produto_selecionado_id"] = None
if "carrinho" not in st.session_state:
    st.session_state["carrinho"] = {}
if "mostrar_todos_produtos" not in st.session_state:
    st.session_state["mostrar_todos_produtos"] = False

if "usuarios_cadastrados" not in st.session_state:
    st.session_state["usuarios_cadastrados"] = [
        {"usuario": "admin", "email": "admin@example.com", "senha": "admin", "admin": True},
        {"usuario": "user", "email": "user@example.com", "senha": "user", "admin": False}
    ]

if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "acesso_privilegiado" not in st.session_state:
    st.session_state["acesso_privilegiado"] = False
if "last_logged_in_user" not in st.session_state:
    st.session_state["last_logged_in_user"] = ""

st.set_page_config(
    page_title="Estoque Maker",
    layout="centered",
)

# --- CÓDIGO PARA BACKGROUND ---
IMAGEM_BACKGROUND_PATH = 'wallpaper.jpg'

@st.cache_data # Cache a imagem para não recarregar toda vez
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        st.error(f"Erro: Imagem de fundo não encontrada em '{file_path}'. Verifique o caminho.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar a imagem de fundo: {e}")
        return None

img_base64 = get_img_as_base64(IMAGEM_BACKGROUND_PATH)

if img_base64:
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    /* CORREÇÃO: Removido 'ding-bottom: 1rem;' que estava truncado e incorreto */
    /* ATENÇÃO: Os paddings e border-radius abaixo devem ser para o .main .block-container */

    .st-emotion-cache-vk3ypu.e1fqkh3f11 {{ /* Este é o seletor para a sidebar. Pode mudar! */
        background-color: rgba(0, 0, 0, 0.8); /* Fundo semi-transparente para a sidebar */
        border-radius: 10px;
    }}

    /* Seletor para o texto dentro da sidebar (se precisar ajustar a cor) */
    .st-emotion-cache-vk3ypu.e1fqkh3f11 .stText,
    .st-emotion-cache-vk3ypu.e1fqkh3f11 .stButton button,
    .st-emotion-cache-vk3ypu.e1fqkh3f11 .stRadio > label {{
        color: white; /* Garante que o texto na sidebar seja branco */
    }}

    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stAlert p, .stButton button {{
        color: white !important; /* Garante que todo o texto seja branco, importante! */
    }}

    /* Estilos para os elementos internos do Streamlit para melhor contraste */
    /* CORREÇÃO E CLAREZA: Aplicando estilos para o container principal de conteúdo */
    .main .block-container {{
        background-color: rgba(0, 0, 0, 0.7); /* Fundo semi-transparente para o conteúdo */
        padding-top: 1rem;
        padding-bottom: 1rem; /* CORREÇÃO: Adicionado padding-bottom completo */
        padding-left: 1rem;
        padding-right: 1rem;
        border-radius: 10px; /* Bordas arredondadas para o container principal */
    }}

    /* Seletor para o st.info, st.success, st.error, st.warning para garantir legibilidade */
    div[data-testid="stStatusWidget"] div[data-testid="stMarkdownContainer"] p {{
        color: black !important; /* A cor padrão é branca, mude para preto se o fundo do status for claro */
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)
# --- FIM DO CÓDIGO PARA BACKGROUND ---

st.markdown(
    """
    <style>
    .st-emotion-cache-1xgtwnd { /* Ajuste esta classe se o Streamlit mudar */
        background-color: rgba(20, 20, 40, 0.85);
        color: white;
    }

    .st-emotion-cache-tj3uvl { /* Ajuste esta classe se o Streamlit mudar */
        background-color: rgba(20, 20, 40, 0.85);
        color: white;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Imagem da logo no fundo do site
st.image ("logologo.png",use_container_width = True)

# Carregar logo e título
logo_path = "logologo.png" # O caminho da imagem do logo também deve ser relativo e na mesma pasta

logo_imagem = None
try:
    logo_imagem = Image.open(logo_path)
    st.logo(logo_imagem, size="large", link="http://localhost:8501")
    # st.title(" App de Estoque")
except FileNotFoundError:
    st.error(f"Arquivo de logo não encontrado em '{logo_path}'. Verifique o caminho.")
    st.title("Meu App de Estoque")
except Exception as e:
    st.error(f"Ocorreu um erro ao carregar o logo: {e}")
    st.title("App de Estoque")

st.write('---')

def pagina_cadastro_login():
    st.header("Bem-vindo(a)! Faça Login ou Cadastre-se")
    st.write("---")

    st.subheader("Fazer Login")
    login_usuario = st.text_input("Usuário (Login)", key="login_user_input")
    login_senha = st.text_input("Senha (Login)", type="password", key="login_pass_input")

    if st.button("Entrar", key="login_button"):
        usuario_encontrado = None
        for user_data in st.session_state["usuarios_cadastrados"]:
            if user_data["usuario"] == login_usuario and user_data["senha"] == login_senha:
                usuario_encontrado = user_data
                break

        if usuario_encontrado:
            st.success(f"Login realizado com sucesso! Bem-vindo(a), {login_usuario}!")
            st.session_state["logado"] = True
            st.session_state["acesso_privilegiado"] = usuario_encontrado.get("admin", False)
            st.session_state["last_logged_in_user"] = login_usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
            st.session_state["logado"] = False
            st.session_state["acesso_privilegiado"] = False

    st.write("---")

    st.subheader("Novo Cadastro")
    cadastro_usuario = st.text_input("Nome de Usuário (Cadastro)", key="cadastro_user_input")
    cadastro_email = st.text_input("E-mail (Cadastro)", key="cadastro_email_input")
    # CORREÇÃO: Rótulos mais claros para os campos de senha
    cadastro_senha = st.text_input("Senha (Cadastro)", type="password", key="cadastro_senha_input")
    cadastro_confirma_senha = st.text_input("Confirmar Senha (Cadastro)", type="password", key="cadastro_confirma_senha_input")
    cadastro_admin_checkbox = st.checkbox("Quero me cadastrar como administrador", key="cadastro_admin_check")

    if st.button("Cadastrar", key="cadastro_button"):
        if cadastro_senha != cadastro_confirma_senha:
            st.error("As senhas não coincidem.")
        elif not cadastro_usuario or not cadastro_senha:
            st.error("Nome de usuário e senha são obrigatórios.")
        elif any(user["usuario"] == cadastro_usuario for user in st.session_state["usuarios_cadastrados"]):
            st.error("Nome de usuário já existe. Por favor, escolha outro.")
        else:
            novo_usuario = {
                "usuario": cadastro_usuario,
                "email": cadastro_email,
                "senha": cadastro_senha,
                "admin": cadastro_admin_checkbox
            }
            st.session_state["usuarios_cadastrados"].append(novo_usuario)
            st.success(f"Usuário '{cadastro_usuario}' cadastrado com sucesso!")
            if cadastro_admin_checkbox:
                st.info("Você se cadastrou como administrador!")
            else:
                st.info("Você se cadastrou como usuário comum.")

def pagina_area_privilegiada():
    if "logado" in st.session_state and st.session_state["logado"] and \
        "acesso_privilegiado" in st.session_state and st.session_state["acesso_privilegiado"]:

        st.header("Conteúdo da Área Privilegiada (Admin)")
        st.success("Bem-vindo(a) à área restrita, Administrador!")
    

        st.write("---")

        st.subheader("Download e Visualização de Dados de Estoque") # Título atualizado
        st.write("Clique no botão abaixo para baixar todo o estoque atual e visualizá-lo na tela.")

        NOME_DB = "estoque_unificado.db" 
        NOME_TABELA_DB = "produtos"

        colunas_db, dados_db = sf.selecionar_todos_produtos (NOME_DB, NOME_TABELA_DB )
        df_estoque = pd.DataFrame (dados_db, columns= colunas_db)

        # ATUALIZAÇÃO: Verifica se o DataFrame de estoque está vazio
        if df_estoque.empty:
            st.info("O estoque está vazio. Não há dados para baixar ou visualizar.")
            # return # Opcional: Saia da função se não houver dados. Removido para que o restante da página carregue.
        else:
            csv_buffer = io.StringIO()
            df_estoque.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode('utf-8')

            # ATUALIZAÇÃO: Layout com colunas para botão e visualização
            col_download, col_visualizar = st.columns([0.4, 0.6]) # Ajuste as proporções conforme desejar

            with col_download:
                st.download_button(
                    label="Baixar Estoque (CSV)",
                    data=csv_bytes,
                    file_name="Estoque_atual.csv",
                    mime="text/csv",
                    help="Baixa uma lista de todo o Estoque atual em formato CSV."
                )

            with col_visualizar:
                st.subheader("Estoque Atual na Tela:") # Subtítulo para a visualização
                st.dataframe(df_estoque) # ATUALIZAÇÃO: Exibe o DataFrame na tela

        st.write("---")
        df_usuarios = pd.DataFrame(st.session_state["usuarios_cadastrados"])

        st.subheader("Visualizar Usuários Cadastrados")
        if not df_usuarios.empty:
            df_display = df_usuarios.drop(columns=["senha"], errors='ignore')
            st.dataframe(df_display)
        else:
            st.info("Nenhum usuário cadastrado ainda.")
    else:
        st.error("Acesso negado. Você não tem permissão para visualizar esta página.")
        st.info("Por favor, faça login como administrador para acessar esta área.")

st.sidebar.title("Navegação Principal")

if st.session_state["logado"] and not st.session_state["acesso_privilegiado"]:
    pagina_selecionada = st.sidebar.radio(
        "Escolha uma opção:",
        ("Cadastro / Login", "Início"),
        index=0 if st.session_state["logado"] == False else 1
    )
elif st.session_state["logado"] and st.session_state["acesso_privilegiado"]:
    pagina_selecionada = st.sidebar.radio(
        "Escolha uma opção:",
        ("Cadastro / Login", "Início", "Área Privilegiada"),
        index=0 if st.session_state["logado"] == False else 1
    )
else:
    pagina_selecionada = st.sidebar.radio(
        "Escolha uma opção:",
        ("Cadastro / Login",),
        index=0
    )


if pagina_selecionada == "Cadastro / Login":
    pagina_cadastro_login()
elif pagina_selecionada == "Início":
    gerenciar_estoque_completo()
elif pagina_selecionada == "Área Privilegiada":
    pagina_area_privilegiada()

st.sidebar.write("---")
if st.session_state["logado"]:
    status_login = "Logado como: Usuário Comum"
    username = st.session_state.get("last_logged_in_user", "")

    if st.session_state["acesso_privilegiado"]:
        status_login = "Logado como: **Administrador**"
        if username:
            status_login += f" ({username})"
    elif username:
        status_login += f" ({username})"

    st.sidebar.success(status_login)

    if st.sidebar.button("Sair"):
        keys_to_delete = ["logado", "acesso_privilegiado", "last_logged_in_user"]
        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

else:
    st.sidebar.info("Não logado.")

st.sidebar.write("---")
st.sidebar.info("Desenvolvido com Streamlit")