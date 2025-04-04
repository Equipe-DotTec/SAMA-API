from app import app
from flask import render_template, redirect, url_for, session, send_from_directory
from app.controllers.ct_certificates import *
from app.controllers.ct_secretary import *
from app.controllers.ct_dashboard_atestados import *
import os

#TELAS
#Home
@app.route("/")
def home():
    return render_template("certificates/vw_home.html")

@app.route("/home")
def home_redirect():
    return redirect(url_for('home'))

@app.route("/faq")
def faq():
    return render_template("certificates/vw_faq.html")

#Página de cadastro de atestados
@app.route("/atestados/cadastro")
def atestados():
    return render_template('certificates/vw_form_register.html')

#Página de login
@app.route("/atestados/acesso")
def acesso_secretaria():
    return render_template("certificates/vw_form_login.html")

#Página de consulta de atestados
@app.route("/atestados/consulta/aluno", methods=['GET'])
def consulta_atestados_aluno():
    dados = consultar_atestados_alunos()
    return render_template("certificates/vw_search.html", dados=dados)

#Página de consulta de atestados
@app.route("/atestados/consulta/secretaria")
@login_required_secretaria
def consulta_atestados_secretaria():
    dados = consultar_atestados_secretaria()
    return render_template("certificates/vw_query.html", dados=dados)

#Página de painel de atestados
@app.route("/painel/atestados")
@login_required_secretaria
def painel_atestados():
    estado = coletar_estados()
    metricas = coletar_metricas()
    cids = coletar_cids()
    return render_template("certificates/vw_dashboard.html", metricas = metricas, estado = estado, cids = cids)
#TELAS

#FUNÇÕES
#Função para servir arquivos de atestados
@app.route('/uploads/atestados/<filename>')
def serve_file_atestados(filename):
    # Caminho correto para o diretório de 'atestados' dentro de 'UPLOAD_FOLDER'
    atestados_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'atestados')
    
    # Verifica se o arquivo existe no diretório de 'atestados'
    try:
        return send_from_directory(atestados_folder, filename)
    except FileNotFoundError:
        return "Arquivo não encontrado", 404
    
@app.route('/atestado/consulta/secretaria/id', methods=['POST'])
def consultar_atestados_id():
    dados = consultar_atestados_secretaria_id()
    return dados

#Cadastrar atestados
@app.route("/atestados/cadastro/validar", methods=['POST'])
def validar():
    response = validar_dados()
    return response  

@app.route("/atestados/cadastro/cadastrar", methods=['POST'])
def cadastrar():
    response = cadastrar_atestado()
    return response  
#Cadastrar atestados


@app.route('/atestados/acesso/logar', methods=['POST'])
def logar():
    response = logar_secretaria()
    return response

@app.route('/atestados/acesso/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
#FUNÇÕES