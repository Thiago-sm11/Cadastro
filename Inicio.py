import streamlit as st
import pandas as pd
import base64
from PIL import Image
import datetime
import sql_funcoes as sf # Importa o módulo com as funções do banco de dados

# Configurações do banco de dados
NOME_DB = "estoque_unificado.db" # Nome do seu arquivo de banco de dados
NOME_TABELA_PRODUTOS = "produtos" # Nome da tabela para armazenar os produtos

# Assegura que a tabela do banco de dados seja criada
sf.criar_tabela_produtos(NOME_DB, NOME_TABELA_PRODUTOS)

# Assegura que as chaves de session_state essenciais existam
if "produto_selecionado_id" not in st.session_state:
    st.session_state["produto_selecionado_id"] = None
if "carrinho" not in st.session_state:
    st.session_state["carrinho"] = {}
if "mostrar_todos_produtos" not in st.session_state:
    st.session_state["mostrar_todos_produtos"] = False
if "preco_total_estoque_geral" not in st.session_state:
    st.session_state["preco_total_estoque_geral"] = 0.0

# IMPORTANTE: Garanta que essas chaves também existam para o login
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "acesso_privilegiado" not in st.session_state:
    st.session_state["acesso_privilegiado"] = False
if "last_logged_in_user" not in st.session_state:
    st.session_state["last_logged_in_user"] = "usuário"


# --- Função para calcular o valor total do estoque (agora lendo do DB) ---
def calcular_preco_total_estoque():
    total_valor = 0.0
    colunas, dados = sf.selecionar_todos_produtos(NOME_DB, NOME_TABELA_PRODUTOS)
    if dados:
        # Criar um DataFrame temporário para cálculo
        df_estoque_temp = pd.DataFrame(dados, columns=colunas)
        
        df_estoque_temp["preco_compra"] = pd.to_numeric(df_estoque_temp["preco_compra"], errors='coerce').fillna(0)
        df_estoque_temp["quantidade"] = pd.to_numeric(df_estoque_temp["quantidade"], errors='coerce').fillna(0)
        
        total_valor = (df_estoque_temp["quantidade"] * df_estoque_temp["preco_compra"]).sum()
    st.session_state["preco_total_estoque_geral"] = total_valor

def gerenciar_estoque_completo():
    st.header("📦 Gerenciamento de Estoque")
    st.write("---")

    # Dicionário de cores CSS para as tags 
    cores_css = {
        "Nenhuma": "transparent",
        "Vermelho": "#FF0000", "Azul": "#0000FF", "Verde": "#008000",
        "Amarelo": "#FFFF00", "Laranja": "#FFA500", "Roxo": "#800080",
        "Preto": "#000000", "Branco": "#FFFFFF",
        "Ciano": "#00FFFF", "Magenta": "#FF00FF", "Lima": "#00FF00",
        "Rosa": "#FFC0CB", "Marrom": "#A52A2A", "Cinza Claro": "#D3D3D3",
        "Dourado": "#FFD700", "Índigo": "#4B0082", "Turquesa": "#40E0D0",
        "Violeta": "#EE82EE", "Bronze": "#CD7F32", "Marinho": "#000080",
        "Carmesim": "#DC143C", "Esmeralda": "#50C878", "Chocolate": "#D2691E",
        "Oliva": "#808000", "Prata": "#C0C0C0", "Salmão": "#FA8072",
        "Aqua": "#00FFFF", "Ouro Velho": "#B8860B", "Púrpura": "#800080"
    }

    # --- Seção para Usuários Logados (Admin e Comum) ---
    if st.session_state["logado"]:
        st.write(f"Bem-vindo(a), {st.session_state.get('last_logged_in_user', 'usuário')}!")

        calcular_preco_total_estoque()
        st.markdown(f"### Valor Total do Estoque: R$ {st.session_state['preco_total_estoque_geral']:,.2f}")
        st.write("---")

        # --- Seção de Avisos ---
        st.subheader("⚠️ Avisos de Estoque")
        colunas_db, dados_db = sf.selecionar_todos_produtos(NOME_DB, NOME_TABELA_PRODUTOS)
        df_estoque_atual_avisos = pd.DataFrame(dados_db, columns=colunas_db)

        if not df_estoque_atual_avisos.empty:
            produtos_baixo_estoque = df_estoque_atual_avisos[
                (df_estoque_atual_avisos["quantidade"] <= df_estoque_atual_avisos["estoque_minimo"]) & 
                (df_estoque_atual_avisos["quantidade"] > 0)
            ]
            produtos_sem_estoque = df_estoque_atual_avisos[df_estoque_atual_avisos["quantidade"] == 0]
            produtos_estoque_negativo = df_estoque_atual_avisos[df_estoque_atual_avisos["quantidade"] < 0]

            if not produtos_estoque_negativo.empty:
                st.error("🚨 **ALERTA CRÍTICO:** Produtos com estoque negativo!")
                for i, row in produtos_estoque_negativo.iterrows():
                    st.write(f"- **{row['nome_produto']}**: Estoque atual: {int(row['quantidade'])} unidades.")
                st.write("---")

            if not produtos_sem_estoque.empty:
                st.warning("⚠️ **ALERTA:** Produtos com estoque zerado!")
                for i, row in produtos_sem_estoque.iterrows():
                    st.write(f"- **{row['nome_produto']}**")
                st.write("---")

            if not produtos_baixo_estoque.empty:
                st.warning("🔔 **AVISO:** Produtos com estoque baixo!")
                for i, row in produtos_baixo_estoque.iterrows():
                    st.write(f"- **{row['nome_produto']}**: Estoque atual: {int(row['quantidade'])} (Mínimo: {int(row['estoque_minimo'])})")
                st.write("---")

            if produtos_baixo_estoque.empty and produtos_sem_estoque.empty and produtos_estoque_negativo.empty:
                st.success("✅ Nenhum aviso de estoque no momento.")
        else:
            st.info("Nenhum produto cadastrado para verificar avisos de estoque.")
        st.write("---")

        # --- Seção Adicionar/Editar Produto (SOMENTE PARA ADMIN) ---
        if st.session_state["acesso_privilegiado"]:
            st.subheader("Adicionar/Editar Produto")
            with st.form("form_produto"):
                produto_para_editar_db = None
                if st.session_state["produto_selecionado_id"] is not None:
                    produto_para_editar_db = sf.selecionar_produto_por_id(NOME_DB, NOME_TABELA_PRODUTOS, st.session_state["produto_selecionado_id"])
                    if produto_para_editar_db:
                        # Mapear os nomes das colunas do DB para os nomes esperados na UI
                        nome_padrão = produto_para_editar_db["nome_produto"]
                        quantidade_padrao = produto_para_editar_db["quantidade"]
                        padrao_preco_compra = produto_para_editar_db["preco_compra"]
                        padrao_cor_tag = produto_para_editar_db["cor_tag"]
                        padrao_estoque_minimo = produto_para_editar_db["estoque_minimo"]
                        
                        # Conversão da data de string para objeto date
                        data_compra_str = produto_para_editar_db.get("data_compra")
                        if data_compra_str:
                            try:
                                padrao_data_compra = datetime.datetime.strptime(data_compra_str, '%Y-%m-%d').date()
                            except ValueError:
                                padrao_data_compra = datetime.date.today()
                        else:
                            padrao_data_compra = datetime.date.today()
                        
                        padrao_descricao = produto_para_editar_db.get("descricao_produto", "")

                        st.info(f"Editando produto: **{nome_padrão}**")
                    else:
                        st.warning("Produto selecionado para edição não encontrado no banco de dados.")
                        st.session_state["produto_selecionado_id"] = None
                        st.rerun()
                else:
                    nome_padrão = ""
                    quantidade_padrao = 0
                    padrao_preco_compra = 0.0
                    padrao_cor_tag = "Nenhuma"
                    padrao_estoque_minimo = 100
                    padrao_data_compra = datetime.date.today()
                    padrao_descricao = ""

                nome = st.text_input("Nome do Produto", value=nome_padrão, key="input_nome")
                quantidade = st.number_input("Quantidade", min_value=0, value=quantidade_padrao, step=1, key="input_quantidade")
                preco_compra = st.number_input("Preço do produto (R$) por unidade", min_value=0.0, value=padrao_preco_compra, step=0.01, format="%.2f", key="input_compra")
                data_compra = st.date_input("Data da Compra", value=padrao_data_compra, key='input_data_compra')
                estoque_minimo = st.number_input("Estoque Mínimo para Alerta", min_value=0, value=padrao_estoque_minimo, step=1, key="input_min_stock")
                descricao = st.text_area ("Descrição do Produto", value = padrao_descricao, height = 150, key = "input_descricao" )
                
                # *** INÍCIO DA PARTE AJUSTADA PARA O PROBLEMA DA IMAGEM ***
                # Criar uma chave única para o st.file_uploader
                # Se estiver editando, a chave inclui o ID do produto. Se for um novo produto, uma chave genérica.
                uploader_key = f"input_image_{st.session_state['produto_selecionado_id']}" if st.session_state["produto_selecionado_id"] is not None else "input_image_new_product"

                uploaded_image = st.file_uploader("Upload de Imagem do Produto (opcional)", 
                                                    type=["png", "jpg", "jpeg"], 
                                                    key=uploader_key)
                # *** FIM DA PARTE AJUSTADA PARA O PROBLEMA DA IMAGEM ***
                
                cores_disponiveis = list(cores_css.keys())
                cor_selecionada = st.selectbox("Escolha uma cor para a tag", options=cores_disponiveis, index=cores_disponiveis.index(padrao_cor_tag), key="input_color")

                col1_btn, col2_btn = st.columns(2)
                with col1_btn:
                    if st.session_state["produto_selecionado_id"] is None:
                        adicionar_button = st.form_submit_button("Adicionar Produto")
                    else:
                        adicionar_button = st.form_submit_button("Salvar Alterações")
                with col2_btn:
                    if st.session_state["produto_selecionado_id"] is not None:
                        cancelar_edicao_button = st.form_submit_button("Cancelar Edição")
                        if cancelar_edicao_button:
                            st.session_state["produto_selecionado_id"] = None
                            st.rerun() # Reinicia para limpar o formulário e o file_uploader

                if adicionar_button:
                    if not nome:
                        st.error("O nome do produto não pode ser vazio.")
                    elif quantidade < 0:
                        st.error("A quantidade não pode ser negativa.")
                    else:
                        imagem_base64 = None
                        if uploaded_image:
                            try:
                                imagem_bytes = uploaded_image.getvalue()
                                imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
                            except Exception as e:
                                st.warning(f"Não foi possível processar a imagem. Erro: {e}")
                                imagem_base64 = None
                        elif produto_para_editar_db: # Se estiver editando e não uploadar nova imagem, mantém a existente
                            imagem_base64 = produto_para_editar_db.get("imagem")

                        produto_data_db = {
                            "Nome do Produto": nome,
                            "Quantidade": quantidade,
                            "Preço de Compra (R$)": preco_compra,
                            "Imagem": imagem_base64,
                            "Cor da Tag": cor_selecionada,
                            "Estoque Mínimo": estoque_minimo,
                            "Data de Compra": data_compra.strftime('%Y-%m-%d'), # Salva a data como string
                            "Descrição do Produto": descricao
                        }

                        if st.session_state["produto_selecionado_id"] is None:
                            # Inserir no banco de dados
                            id_inserido = sf.inserir_produto(NOME_DB, NOME_TABELA_PRODUTOS, produto_data_db)
                            if id_inserido:
                                st.success(f"Produto '{nome}' adicionado ao estoque (ID: {id_inserido})!")
                            else:
                                st.error("Erro ao adicionar produto ao banco de dados.")
                        else:
                            # Atualizar no banco de dados
                            sucesso_atualizacao = sf.atualizar_produto(NOME_DB, NOME_TABELA_PRODUTOS, st.session_state["produto_selecionado_id"], produto_data_db)
                            if sucesso_atualizacao:
                                st.success(f"Produto '{nome}' atualizado no estoque!")
                                # *** NOVO: Reseta o produto_selecionado_id e força rerun para limpar o formulário ***
                                st.session_state["produto_selecionado_id"] = None 
                            else:
                                st.error("Erro ao atualizar produto no banco de dados.")
                        
                        calcular_preco_total_estoque()
                        st.rerun() # Força a reexecução para limpar o formulário e o file_uploader
            st.write("---")
        else: # Este else é para a seção "Adicionar/Editar Produto"
            st.info("Apenas administradores podem adicionar ou editar produtos.")
            st.write("---")

        # --- Seção de Visualização do Estoque (PARA ADMIN E USUÁRIO COMUM) ---
        st.subheader("Visualização do Estoque")

        colunas_db, dados_db = sf.selecionar_todos_produtos(NOME_DB, NOME_TABELA_PRODUTOS)
        df_estoque_atual = pd.DataFrame(dados_db, columns=colunas_db)

        if df_estoque_atual.empty:
            st.info("Nenhum produto cadastrado no estoque.")
        else:
            # Filtro por Tags de Cor
            cores_disponiveis_filtro = ["Todas"] + sorted(list(df_estoque_atual["cor_tag"].dropna().unique()))
            if "Nenhuma" in cores_disponiveis_filtro:
                cores_disponiveis_filtro.remove("Nenhuma")
            cores_disponiveis_filtro.insert(1, "Nenhuma")

            filtro_cor_visualizacao = st.selectbox("Filtrar por Tag de Cor na Visualização:", options=cores_disponiveis_filtro, key="filtro_cor_visualizacao")

            df_filtrado_visualizacao = df_estoque_atual.copy()
            if filtro_cor_visualizacao != "Todas":
                df_filtrado_visualizacao = df_filtrado_visualizacao[df_filtrado_visualizacao["cor_tag"] == filtro_cor_visualizacao]

            if df_filtrado_visualizacao.empty:
                st.info(f"Nenhum produto encontrado com a tag de cor '{filtro_cor_visualizacao}'.")
            else:
                cols_per_row = 3
                
                # Ordenar por ID para pegar os mais recentes, assumindo que IDs crescem
                produtos_para_exibir_viz = df_filtrado_visualizacao.sort_values(by="id", ascending=False).reset_index(drop=True)

                if not st.session_state["mostrar_todos_produtos"]:
                    produtos_para_exibir_viz_limitado = produtos_para_exibir_viz.head(3)
                    if len(produtos_para_exibir_viz_limitado) < len(produtos_para_exibir_viz):
                        st.info(f"Mostrando os {len(produtos_para_exibir_viz_limitado)} produtos mais recentes. Clique para ver todos.")
                    else:
                        st.info("Mostrando todos os produtos.")
                else:
                    produtos_para_exibir_viz_limitado = produtos_para_exibir_viz
                    st.info("Mostrando todos os produtos. Clique para ver apenas os mais recentes.")

                if len(produtos_para_exibir_viz) > 3:
                    if st.button("Mostrar Todos / Mostrar Recentes", key="toggle_view_products"):
                        st.session_state["mostrar_todos_produtos"] = not st.session_state["mostrar_todos_produtos"]
                        st.rerun()

                cols_viz = st.columns(cols_per_row)
                col_idx_viz = 0

                for i, row in produtos_para_exibir_viz_limitado.iterrows():
                    with cols_viz[col_idx_viz]:
                        st.markdown(f"**{row['nome_produto']}**")
                        st.write(f"Estoque: {int(row['quantidade'])} unidades")
                        st.write(f"Preço de Compra: R$ {row['preco_compra']:.2f}")
                        
                        if 'data_compra' in row and pd.notna(row['data_compra']):
                            # A data já está como string %Y-%m-%d
                            data_formatada = datetime.datetime.strptime(row['data_compra'], '%Y-%m-%d').strftime('%d/%m/%Y')
                            st.write(f"Data de Compra: {data_formatada}")
                        else:
                            st.write("Data de Compra: Não informada")

                        if 'descricao_produto' in row and pd.notna(row['descricao_produto']) and row["descricao_produto"].strip() != "":
                            st.markdown(f"**Descrição:** {row['descricao_produto']}")
                        else:
                            st.markdown ("**(Sem descrição)**")

                        if row["imagem"]:
                            try:
                                img_data = base64.b64decode(row["imagem"])
                                st.image(img_data, width=150, use_container_width="always")
                            except Exception:
                                st.image("https://via.placeholder.com/150?text=Sem+Imagem", width=150, use_container_width="always")
                        else:
                            st.image("https://via.placeholder.com/150?text=Sem+Imagem", width=150, use_container_width="always")

                        # Tag de cor
                        if row["cor_tag"] != "Nenhuma":
                            st.markdown(
                                f"""
                                <div style="
                                    display: inline-block; 
                                    padding: 5px 10px; 
                                    border-radius: 5px; 
                                    background-color: {cores_css.get(row['cor_tag'], 'gray')}; 
                                    color: {'black' if row['cor_tag'] in ['Amarelo', 'Branco', 'Cinza Claro', 'Lima', 'Salmão', 'Dourado', 'Prata', 'Bronze', 'Esmeralda', 'Aqua'] else 'white'}; 
                                    font-size: 0.8em;
                                    margin-top: 5px;
                                ">
                                    {row['cor_tag']}
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        
                        if st.session_state["acesso_privilegiado"]:
                            if st.button(f"Editar {row['nome_produto']}", key=f"edit_viz_{row['id']}"):
                                st.session_state["produto_selecionado_id"] = row['id'] # O ID é agora o do banco de dados
                                st.rerun()
                            # Botão de exclusão para administradores
                            if st.button(f"Excluir {row['nome_produto']}", key=f"delete_viz_{row['id']}"):
                                sf.deletar_produto(NOME_DB, NOME_TABELA_PRODUTOS, row['id'])
                                st.success(f"Produto '{row['nome_produto']}' excluído com sucesso!")
                                st.rerun()

                        st.markdown("---")
                    
                    col_idx_viz = (col_idx_viz + 1) % cols_per_row
                    if col_idx_viz == 0 and i < len(produtos_para_exibir_viz_limitado) -1 :
                        cols_viz = st.columns(cols_per_row)
                
        st.write("---")

        # --- Nova Seção: Gráfico de Produtos por Cor e Quantidade ---
        st.subheader ("📊 Quantidade de Produtos por Cor")
        if not df_estoque_atual.empty:
            df_chart = df_estoque_atual.copy()
            df_chart ['quantidade'] = pd.to_numeric(df_chart["quantidade"], errors ='coerce').fillna (0)



            df_chart_filtered = df_chart[df_chart["cor_tag"] != "Nenhuma"]

            if not df_chart_filtered.empty:
                chart_data = df_chart_filtered.groupby("cor_tag")["quantidade"].sum().reset_index()
                chart_data.columns = ["Cor da Tag", "Quantidade Total"]
                st.bar_chart(chart_data, x="Cor da Tag", y="Quantidade Total", use_container_width=True)
            else:
                st.info("Nenhum produto com uma tag de cor definida e quantidade disponível para exibir no gráfico.")
        else:
            st.info("Nenhum produto no estoque para gerar o gráfico.")
        st.write("---")

        # --- Área Privilegiada: Retirar/Ajustar Estoque (SOMENTE PARA ADMIN) ---
        st.subheader("Área Privilegiada: Retirada/Ajuste de Estoque")
        st.warning("🚨 **ATENÇÃO:** Esta seção permite ajustar o estoque para valores abaixo de zero (negativos). Use com cautela!")
        
        if st.session_state["acesso_privilegiado"]:
            colunas_db, dados_db = sf.selecionar_todos_produtos(NOME_DB, NOME_TABELA_PRODUTOS)
            df_estoque_atual = pd.DataFrame(dados_db, columns=colunas_db)

            if df_estoque_atual.empty:
                st.info("Nenhum produto no estoque para ajustar.")
            else:
                opcoes_mapa_id = {f"{row['nome_produto']} (ID: {row['id']})": row['id'] for _, row in df_estoque_atual.iterrows()}
                opcoes_exibicao = list(opcoes_mapa_id.keys())
                
                # Certifique-se de que a lista de opções não esteja vazia antes de acessar o primeiro elemento
                valor_padrao_selectbox = opcoes_exibicao[0] if opcoes_exibicao else None

                produto_selecionado_exibicao = st.selectbox(
                    "Selecione o produto para ajustar:", 
                    options=opcoes_exibicao, 
                    index=opcoes_exibicao.index(valor_padrao_selectbox) if valor_padrao_selectbox else 0,
                    key="select_ajuste_estoque"
                )
                
                idx_produto_ajustar_id = opcoes_mapa_id.get(produto_selecionado_exibicao)
                
                produto_para_ajustar_db = None
                if idx_produto_ajustar_id is not None:
                    produto_para_ajustar_db = sf.selecionar_produto_por_id(NOME_DB, NOME_TABELA_PRODUTOS, idx_produto_ajustar_id)
                
                # --- INÍCIO DA CORREÇÃO ---
                if produto_para_ajustar_db is not None:
                    st.info(f"Estoque atual de '{produto_para_ajustar_db['nome_produto']}': **{int(produto_para_ajustar_db['quantidade'])}** unidades.")

                    current_qty = int(produto_para_ajustar_db['quantidade'])
                    min_stock = int(produto_para_ajustar_db['estoque_minimo'])

                    if current_qty == 0:
                        st.warning(f"⚠️ **Este produto está com estoque zerado!**")
                    elif current_qty <= min_stock and current_qty > 0:
                        st.warning(f"🔔 **Aviso:** Estoque baixo! Quantidade atual ({current_qty}) é menor ou igual ao estoque mínimo ({min_stock}).")
                    
                    quantidade_ajustar = st.number_input(
                        "Quantidade a ajustar (pode ser negativo para baixar, positivo para aumentar):", 
                        value=0,
                        step=1, 
                        key="input_quantidade_ajuste"
                    )

                    if st.button("Aplicar Ajuste de Estoque", key="button_ajustar_estoque"):
                        nova_quantidade = int(produto_para_ajustar_db["quantidade"]) + quantidade_ajustar
                        
                        produto_data_temp = produto_para_ajustar_db.copy() # Agora é seguro chamar .copy()
                        produto_data_temp['quantidade'] = nova_quantidade
                        
                        # Garante que 'data_compra' sempre exista, mesmo se não estiver no DB para produtos antigos
                        produto_data_temp["data_compra"] = produto_data_temp.get("data_compra", datetime.date.today().strftime('%Y-%m-%d'))

                        sucesso_ajuste = sf.atualizar_produto(NOME_DB, NOME_TABELA_PRODUTOS, idx_produto_ajustar_id, {
                            "Nome do Produto": produto_data_temp["nome_produto"],
                            "Quantidade": produto_data_temp["quantidade"],
                            "Preço de Compra (R$)": produto_data_temp["preco_compra"],
                            "Imagem": produto_data_temp["imagem"],
                            "Cor da Tag": produto_data_temp["cor_tag"],
                            "Estoque Mínimo": produto_data_temp["estoque_minimo"],
                            "Data de Compra": produto_data_temp["data_compra"],
                            "Descrição do Produto": produto_data_temp["descricao_produto"]
                        })
                        
                        if sucesso_ajuste:
                            st.success(f"Estoque de '{produto_para_ajustar_db['nome_produto']}' ajustado em {quantidade_ajustar} unidades. Novo estoque: {nova_quantidade}.")
                            calcular_preco_total_estoque()
                            st.rerun()
                        else:
                            st.error("Erro ao aplicar ajuste de estoque no banco de dados.")
                else:
                    st.warning("Nenhum produto selecionado ou produto não encontrado. Por favor, selecione um produto válido no campo acima.")
                # --- FIM DA CORREÇÃO ---
        else:
            st.info("A Área Privilegiada é exclusiva para administradores.")
        st.write("---")


        # --- Seção de Retirada de Produtos (Venda/Múltiplos Itens) (PARA ADMIN E USUÁRIO COMUM) ---
        st.header("🛒 Retirada de Produtos (Múltiplos Itens)")
        st.write("Selecione os produtos e as quantidades que deseja retirar do estoque.")
        st.write("---")


        colunas_db, dados_db = sf.selecionar_todos_produtos(NOME_DB, NOME_TABELA_PRODUTOS)
        df_estoque_retirada = pd.DataFrame(dados_db, columns= colunas_db)
        
        if df_estoque_retirada.empty:
            st.info("Nenhum produto disponível no estoque para retirada em lote.")
        else:
            produtos_disponiveis = df_estoque_retirada[df_estoque_retirada["quantidade"] >= 0].copy() # Permite selecionar produtos com 0 ou mais para exibir o aviso
            
            if produtos_disponiveis.empty:
                st.info("Nenhum produto com estoque disponível para retirada.")
                return

            opcoes_produtos_nomes = [ 
                f"{row['nome_produto']} (ID: {row['id']})" for _, row in produtos_disponiveis.iterrows()
            ]
                
            produtos_selecionados_multiselect = st.multiselect (
                "Selecione os produtos para o carrinho:",
                options = opcoes_produtos_nomes,
                key = "multiselect_carrinho"
            )
            
            produtos_selecionados_ids = []
            for nome in produtos_selecionados_multiselect:
                try:
                    # Extrai o ID entre "ID: " e ")"
                    id_str = nome.split("(ID: ")[1].replace(")", "")
                    produtos_selecionados_ids.append(int(id_str))
                except (IndexError, ValueError):
                    st.warning(f"Erro ao extrair ID do produto: {nome}. Pode ser um formato inválido.")
                    continue

            # Limpar itens do carrinho que não estão mais selecionados no multiselect
            ids_no_carrinho_atualmente = list(st.session_state["carrinho"].keys())
            for prod_id in ids_no_carrinho_atualmente:
                if prod_id not in produtos_selecionados_ids:
                    del st.session_state["carrinho"][prod_id]

            if not produtos_selecionados_ids:
                st.info("Selecione produtos acima para adicioná-los ao carrinho.")
            else:
                st.subheader("Quantidades para Retirada")
                for produto_id in produtos_selecionados_ids:
                    # Buscar o produto do DB para ter os dados mais recentes
                    produto = sf.selecionar_produto_por_id(NOME_DB, NOME_TABELA_PRODUTOS, produto_id)
                    if produto: # Certifica que o produto foi encontrado
                        max_qty = int(produto['quantidade'])
                        min_stock = int(produto['estoque_minimo']) # Obter o estoque mínimo
                        
                        qty_key = f"retirada_lote_produto_input_{produto_id}" 
                        
                        current_qty_in_cart = st.session_state["carrinho"].get(produto_id, 0)

                        # O max_value precisa considerar o que já está "no carrinho" mas ainda não foi retirado do estoque
                        effective_max_value = max_qty + current_qty_in_cart 
                        if max_qty == 0 and current_qty_in_cart == 0: 
                            effective_max_value = 0

                        quantidade_a_retirar = st.number_input(
                            f"**{produto['nome_produto']}** (Disponível: {max_qty}):",
                            min_value=0,
                            max_value=effective_max_value,
                            value=current_qty_in_cart,
                            step=1,
                            key=qty_key,
                            help=f"Preço Unitário: R$ {produto['preco_compra']:.2f}"
                        )

                        # --- Adicionar aviso de estoque baixo/zerado aqui ---
                        if max_qty == 0:
                            st.warning(f"⚠️ **Este produto está com estoque zerado!**")
                        elif max_qty <= min_stock and max_qty > 0:
                            st.warning(f"🔔 **Aviso:** Estoque baixo! Quantidade disponível ({max_qty}) é menor ou igual ao estoque mínimo ({min_stock}).")
                        # --- Fim do aviso de estoque ---

                        if quantidade_a_retirar > 0:
                            st.session_state["carrinho"][produto_id] = quantidade_a_retirar
                        elif quantidade_a_retirar == 0 and produto_id in st.session_state["carrinho"]:
                            del st.session_state["carrinho"][produto_id]
                    else:
                        st.warning(f"Produto com ID {produto_id} não encontrado no estoque. Removendo do carrinho.")
                        if produto_id in st.session_state["carrinho"]:
                            del st.session_state["carrinho"][produto_id]

                st.markdown("---")
                st.subheader("Resumo do Carrinho")
                
                if not st.session_state["carrinho"]:
                    st.info("Carrinho vazio. Adicione quantidades aos produtos selecionados.")
                else:
                    carrinho_df_data = []
                    total_valor_retirada_lote = 0
                    for produto_id, quantidade_no_carrinho in st.session_state["carrinho"].items():
                        produto = sf.selecionar_produto_por_id(NOME_DB, NOME_TABELA_PRODUTOS, produto_id)
                        if produto: # Certifica que o produto ainda existe no DB
                            subtotal = produto["preco_compra"] * quantidade_no_carrinho
                            carrinho_df_data.append({
                                "Produto": produto["nome_produto"],
                                "Quantidade": quantidade_no_carrinho,
                                "Preço Unitário": f"R$ {produto['preco_compra']:.2f}",
                                "Subtotal": f"R$ {subtotal:.2f}"
                            })
                            total_valor_retirada_lote += subtotal
                    
                    carrinho_df = pd.DataFrame(carrinho_df_data)
                    st.table(carrinho_df)
                    st.markdown(f"**Valor Total da Retirada em Lote: R$ {total_valor_retirada_lote:,.2f}**")

                    if st.button("Finalizar Retirada (Processar Carrinho)", key="finalizar_retirada_lote_button"):
                        sucesso_retirada_lote = True
                        mensagens = []
                        
                        for produto_id, quantidade_retirar in st.session_state["carrinho"].items():
                            if quantidade_retirar > 0:
                                produto_no_estoque = sf.selecionar_produto_por_id(NOME_DB, NOME_TABELA_PRODUTOS, produto_id)
                                if produto_no_estoque and produto_no_estoque["quantidade"] < quantidade_retirar:
                                    sucesso_retirada_lote = False
                                    st.error(f"Erro: Não há estoque suficiente para '{produto_no_estoque['nome_produto']}'. Disponível: {int(produto_no_estoque['quantidade'])}. Tentando retirar: {quantidade_retirar}.")
                                    break
                                elif not produto_no_estoque:
                                    sucesso_retirada_lote = False
                                    st.error(f"Erro: Produto com ID {produto_id} não encontrado no estoque para retirada.")
                                    break
                        
                        if sucesso_retirada_lote:
                            for produto_id, quantidade_retirar in st.session_state["carrinho"].items():
                                if quantidade_retirar > 0:
                                    produto_no_estoque = sf.selecionar_produto_por_id(NOME_DB, NOME_TABELA_PRODUTOS, produto_id)
                                    if produto_no_estoque:
                                        nova_quantidade = int(produto_no_estoque["quantidade"]) - quantidade_retirar
                                        
                                        # Atualizar a quantidade no banco de dados
                                        produto_data_temp = produto_no_estoque # Já é um dicionário
                                        produto_data_temp['quantidade'] = nova_quantidade
                                        
                                        # Convertendo a data de volta para string para atualização
                                        # Garante que 'data_compra' sempre exista antes de acessá-la
                                        produto_data_temp["data_compra"] = produto_data_temp.get("data_compra", datetime.date.today().strftime('%Y-%m-%d'))

                                        sucesso_update = sf.atualizar_produto(NOME_DB, NOME_TABELA_PRODUTOS, produto_id, {
                                            "Nome do Produto": produto_data_temp["nome_produto"],
                                            "Quantidade": produto_data_temp["quantidade"],
                                            "Preço de Compra (R$)": produto_data_temp["preco_compra"],
                                            "Imagem": produto_data_temp["imagem"],
                                            "Cor da Tag": produto_data_temp["cor_tag"],
                                            "Estoque Mínimo": produto_data_temp["estoque_minimo"],
                                            "Data de Compra": produto_data_temp["data_compra"],
                                            "Descrição do Produto": produto_data_temp["descricao_produto"]
                                        })
                                        
                                        if sucesso_update:
                                            mensagens.append(f"Retirados {quantidade_retirar} unidades de '{produto_no_estoque['nome_produto']}'. Novo estoque: {nova_quantidade}.")
                                        else:
                                            mensagens.append(f"Erro ao atualizar estoque para '{produto_no_estoque['nome_produto']}'.")
                                    else:
                                        mensagens.append(f"Produto com ID {produto_id} não encontrado durante a finalização da retirada.")
                            
                            for msg in mensagens:
                                st.write(msg)
                            st.session_state["carrinho"] = {}
                            calcular_preco_total_estoque()
                            st.rerun()
                        else:
                            st.error("Por favor, ajuste as quantidades no carrinho para finalizar a retirada.")
    else: # Este else é para o IF PRINCIPAL "if st.session_state["logado"]:"
        st.warning("Por favor, faça login para acessar as funcionalidades do estoque.")
        st.image("https://via.placeholder.com/300?text=Faça+Login", use_container_width="always")



if __name__ == "__main__":

    gerenciar_estoque_completo()