from src.app import app
from flask import render_template, redirect, url_for, session, send_from_directory
from src.app.controllers.ct_teams import *
import os
from src.app.controllers.ct_dashboard_teams import DashboardTeams

#TELAS
#Página de login
@app.route("/equipes/acesso")
def teams_access():
    return render_template("teams/vw_form_login.html")

#Página de painel de atestados
@app.route("/painel/equipes")
@TeamsController.loginRequired
def teams_panel():
    data, avarage = DashboardTeams.getData()
    return render_template("teams/vw_dashboard.html", data = data, avarage = avarage)

#Página de cadastro de equipes
@app.route("/equipes/cadastro")
def register_teams():
    return render_template("teams/vw_form_register.html")

# Página de política de privacidade
@app.route("/equipes/privacidade")
def privacy_policy_teams():
    return render_template("teams/vw_privacy_policy.html")

#Página de visualização de equipes
@app.route("/equipes/visualizar")
def view_teams():
    return render_template("teams/vw_view_teams.html", teams=TeamsController.readAllTeams())

#Página de minha equipe
@app.route("/equipes/equipe")
@TeamsController.loginRequired  
def team_profile():
    return render_template("teams/vw_profile.html", team=TeamsController.readTeamById())

#Página de criar avaliações
@app.route("/equipes/avaliacoes")
@TeamsController.loginRequired 
def evaluate():
    return render_template("teams/vw_form_evaluate.html")
#TELAS


#FUNÇÕES
#Página de cadastro de equipes (Back)
@app.route("/equipes/cadastro/cadastrar", methods=['POST'])
def register_team():
    return TeamsController.registerTeam()

#Função para fazer o login da equipe
@app.route('/equipes/acesso/logar', methods=['POST'])
def login_team():
    return TeamsController.loginTeam()

#Página de edição de equipe
@app.route("/equipes/atualizar", methods=['POST'])
@TeamsController.loginRequired  
def update_team():
    return TeamsController.update_team()

#Função para registrar avaliação
@app.route('/equipes/avaliacoes/avaliar', methods=['POST'])
@TeamsController.loginRequired
def save_evaluations():
    return TeamsController.saveEvaluations()

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/equipes/avaliacoes/deletar", methods=['POST'])
@TeamsController.loginRequired
def delete_evaluation():
    return TeamsController.deleteEvaluation()

@app.route('/equipes/perfil/excluir', methods=['POST'])
@TeamsController.loginRequired
def delete_team():
    return TeamsController.deleteTeam()
#FUNÇÕES