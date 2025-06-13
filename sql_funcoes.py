import sqlite3

def criar_conexao(nome_db):
    """Cria uma conexão com o banco de dados SQLite especificado."""
    conn = None
    try:
        conn = sqlite3.connect(nome_db)
        # Habilita o acesso por nome da coluna
        conn.row_factory = sqlite3.Row # <--- ADICIONE ESTA LINHA
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
    return conn

"""Cria a tabela de produtos se ela não existir."""
def criar_tabela_produtos(nome_db, nome_tabela):
    # conecta o sql com banco de dados
    conn = criar_conexao(nome_db)
    if conn:
        # try ve se o codigo ta certo, se sim (if) continua normalmente
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {nome_tabela} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_produto TEXT NOT NULL,
                    quantidade INTEGER NOT NULL,
                    preco_compra REAL NOT NULL,
                    imagem TEXT,
                    cor_tag TEXT,
                    estoque_minimo INTEGER,
                    data_compra TEXT,
                    descricao_produto TEXT
                );
            """)
            conn.commit()
            print(f"Tabela '{nome_tabela}' verificada/criada com sucesso.")
        except sqlite3.Error as e:
            print(f"Erro ao criar tabela: {e}")
        finally:
            if conn:
                conn.close()

def inserir_produto(nome_db, nome_tabela, produto_data):
    """Insere um produto no banco de dados."""
    conn = criar_conexao(nome_db)
    if conn:
        try:
            cursor = conn.cursor() # o isert into abaixo os entre parentese (nome_produto...) cria os itens na tabela
            cursor.execute(f"""
                
                INSERT INTO {nome_tabela} (nome_produto, quantidade, preco_compra, imagem, cor_tag, estoque_minimo, data_compra, descricao_produto)

                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                produto_data["Nome do Produto"],
                produto_data["Quantidade"],
                produto_data["Preço de Compra (R$)"],
                produto_data["Imagem"],
                produto_data["Cor da Tag"],
                produto_data["Estoque Mínimo"],
                produto_data["Data de Compra"],
                produto_data["Descrição do Produto"]
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Erro ao inserir produto: {e}")
            return None
        finally:
            if conn:
                conn.close()

def selecionar_todos_produtos(nome_db, nome_tabela):
    """Seleciona todos os produtos do banco de dados."""
    conn = criar_conexao(nome_db)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {nome_tabela};")
            dados = cursor.fetchall()
            colunas = [description[0] for description in cursor.description]
            
            # Converte cada Row para um dicionário para consistência
            # Isso é importante para que o pd.DataFrame funcione corretamente
            dados_dict = []
            for row in dados:
                dados_dict.append(dict(row))
            
            return colunas, dados_dict
        except sqlite3.Error as e:
            print(f"Erro ao selecionar todos os produtos: {e}")
            return [], []
        finally:
            if conn:
                conn.close()

def selecionar_produto_por_id(nome_db, nome_tabela, produto_id):
    """Seleciona um produto específico pelo ID."""
    conn = criar_conexao(nome_db)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {nome_tabela} WHERE id = ?;", (produto_id,))
            produto = cursor.fetchone()
            
            if produto:
                return dict(produto) # <--- AQUI ESTÁ A CHAVE DA CORREÇÃO
            else:
                return None
        except sqlite3.Error as e:
            print(f"Erro ao selecionar produto por ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

def atualizar_produto(nome_db, nome_tabela, produto_id, produto_data):
    """Atualiza um produto existente no banco de dados."""
    conn = criar_conexao(nome_db)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE {nome_tabela} SET
                    nome_produto = ?,
                    quantidade = ?,
                    preco_compra = ?,
                    imagem = ?,
                    cor_tag = ?,
                    estoque_minimo = ?,
                    data_compra = ?,
                    descricao_produto = ?
                WHERE id = ?;
            """, (
                produto_data["Nome do Produto"],
                produto_data["Quantidade"],
                produto_data["Preço de Compra (R$)"],
                produto_data["Imagem"],
                produto_data["Cor da Tag"],
                produto_data["Estoque Mínimo"],
                produto_data["Data de Compra"],
                produto_data["Descrição do Produto"],
                produto_id
            ))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao atualizar produto: {e}")
            return False
        finally:
            if conn:
                conn.close()

def deletar_produto(nome_db, nome_tabela, produto_id):
    """Deleta um produto do banco de dados pelo ID."""
    conn = criar_conexao(nome_db)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {nome_tabela} WHERE id = ?;", (produto_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao deletar produto: {e}")
            return False
        finally:
            if conn:
                conn.close()

def atualizar_quantidade_produto(nome_db, nome_tabela, produto_id, nova_quantidade):
    """Atualiza a quantidade de um produto específico."""
    conn = criar_conexao(nome_db)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE {nome_tabela} SET quantidade = ? WHERE id = ?;", (nova_quantidade, produto_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao atualizar quantidade do produto: {e}")
            return False
        finally:
            if conn:
                conn.close()