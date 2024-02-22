import re
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dados da Pessoa
class Pessoa:
    def __init__(self, nomeCompleto, dataDeNascimento, endereco, cpf, estadoCivil):
        self.nomeCompleto = nomeCompleto
        self.dataDeNascimento = dataDeNascimento
        self.endereco = endereco
        self.cpf = cpf
        self.estadoCivil = estadoCivil
        

# Juntar Banco de Dados
class GerenciarPessoas:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def conectarBanco(self):
        self.conn = sqlite3.connect('pessoas.db')
        self.cursor = self.conn.cursor()

    def criarTabela(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pessoas (
                nomeCompleto TEXT,
                dataDeNascimento TEXT,
                endereco TEXT,
                cpf TEXT,
                estadoCivil TEXT
            )
        ''')
        self.conn.commit()

    def validarCpf(self, cpf):

        cpfNum = ''.join(filter(str.isdigit, cpf))

        # CPF 11 dígitos
        if len(cpfNum) == 11 and re.match(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
            return True
        else:
            return False
        

    def cadastrarPessoa(self, nova_pessoa):
        if not self.validarCpf(nova_pessoa.cpf):
            return "CPF inválido."

        self.cursor.execute('INSERT INTO pessoas VALUES (?, ?, ?, ?, ?)',
                            (nova_pessoa.nomeCompleto, nova_pessoa.dataDeNascimento,
                             nova_pessoa.endereco, nova_pessoa.cpf, nova_pessoa.estadoCivil))
        self.conn.commit()

        return "Cadastro realizado."
    
    def buscarBanco(self):
        self.cursor.execute('SELECT * FROM pessoas')
        pessoas = self.cursor.fetchall()
        return [Pessoa(*pessoa) for pessoa in pessoas]
        
    def listarPessoas(self):
        return self.buscarBanco()

    def visualizarTabela(self):
        return self.listarPessoas()

    def atualizarPessoa(self, nome_antigo, nova_pessoa):
        pessoa = self.cursor.execute('SELECT * FROM pessoas WHERE nomeCompleto = ?', (nome_antigo,)).fetchone()

        if pessoa:
            self.cursor.execute('''
                UPDATE pessoas
                SET nomeCompleto=?, dataDeNascimento=?, endereco=?, cpf=?, estadoCivil=?
                WHERE nomeCompleto=?
            ''', (nova_pessoa.nomeCompleto, nova_pessoa.dataDeNascimento,
                  nova_pessoa.endereco, nova_pessoa.cpf, nova_pessoa.estadoCivil, nome_antigo))
            self.conn.commit()
            return f"{nome_antigo} atualizado para {nova_pessoa.nomeCompleto}"
        else:
            return f"Pessoa {nome_antigo} não encontrada."

    def excluirPessoa(self, nome):
        pessoa = self.cursor.execute('SELECT * FROM pessoas WHERE nomeCompleto = ?', (nome,)).fetchone()

        if pessoa:
            self.cursor.execute('DELETE FROM pessoas WHERE nomeCompleto = ?', (nome,))
            self.conn.commit()
            return f"Pessoa {nome} excluída com sucesso."
        else:
            return f"Pessoa {nome} não encontrada."

    def fecharConexao(self):
        if self.conn:
            self.conn.close()

# Flask
@app.route('/')
def index():
    gerenciador = GerenciarPessoas()
    with app.app_context():
        gerenciador.conectarBanco()
        gerenciador.criarTabela()
        pessoas = gerenciador.listarPessoas()
    gerenciador.fecharConexao()
    return render_template('index.html', pessoas=pessoas)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    data = request.form

    nova_pessoa = Pessoa(
        data['nome'],
        data['data_nascimento'],
        data['endereco'],
        data['cpf'],
        data['estado_civil']
    )

    gerenciador = GerenciarPessoas()
    with app.app_context():
        gerenciador.conectarBanco()
        gerenciador.criarTabela()
        mensagem = gerenciador.cadastrarPessoa(nova_pessoa)

    if "CPF inválido" in mensagem:
            # Erro no CPF volta a lista de pessoas
            pessoas = gerenciador.listarPessoas()
            gerenciador.fecharConexao()
            return render_template('listar_pessoas.html', pessoas=pessoas, mensagem=mensagem)
    gerenciador.fecharConexao()
    
    return redirect(url_for('listar'))

@app.route('/listar_pessoas')
def listar():
    gerenciador = GerenciarPessoas()
    with app.app_context():
        gerenciador.conectarBanco()
        gerenciador.criarTabela()
        pessoas = gerenciador.listarPessoas()
    return render_template('listar_pessoas.html', pessoas=pessoas)

@app.route('/editar/<nome>', methods=['GET'])
def editar(nome):
    gerenciador = GerenciarPessoas()
    with app.app_context():
        gerenciador.conectarBanco()
        gerenciador.criarTabela()
        pessoas = gerenciador.listarPessoas()

        for pessoa in pessoas:
            if pessoa.nomeCompleto == nome:
                pessoa.editando = True
            else:
                pessoa.editando = False

    gerenciador.fecharConexao()
    return render_template('listar_pessoas.html', pessoas=pessoas)

@app.route('/salvar_atualizacao/<nome>', methods=['POST'])
def salvar_atualizacao(nome):
    gerenciador = GerenciarPessoas()
    with app.app_context():
        gerenciador.conectarBanco()
        gerenciador.criarTabela()

        nova_pessoa = Pessoa(
            request.form['nome'],
            request.form['data_nascimento'],
            request.form['endereco'],
            request.form['cpf'],
            request.form['estado_civil']
        )

        mensagem = gerenciador.atualizarPessoa(nome, nova_pessoa)

    gerenciador.fecharConexao()
    return redirect(url_for('listar'))

@app.route('/excluir', methods=['POST'])
def excluir():
    nome = request.form['nome']

    gerenciador = GerenciarPessoas()
    with app.app_context():
        gerenciador.conectarBanco()
        gerenciador.criarTabela()
        mensagem = gerenciador.excluirPessoa(nome)
    return redirect(url_for('listar'))

if __name__ == '__main__':
    app.run(debug=True)
