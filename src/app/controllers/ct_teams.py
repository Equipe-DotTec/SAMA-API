from flask import request, redirect, url_for, jsonify, session
from src.app.models.md_teams import Teams
from src.app.models.md_users import Users
from src.app.utilities.ut_validation import Validation
from functools import wraps
from src.app.models.md_log import Log
import shortuuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from src.app import app
from src.app import admin_email, admin_password
import os
import uuid

class TeamsController:
    def loginRequired(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'team' not in session:
                return redirect(url_for('teams_access'))
            return f(*args, **kwargs)
        return decorated_function
    
    def loginTeam():
        try:
            session.clear()
            id=request.form.get('input-id-team')
            password = request.form.get('input-password-team')
            teams=Teams()
            response = teams.login(id,password)
            if response:
                Log().register(operation=f'Team: Login')
                return jsonify({"status": True,"message": "Equipe logada com sucesso!"}), 200
            else:
                Log().register(operation=f'Team: Login Attempt ({id})')
                return jsonify({"status": False, "message": "Credenciais incorretas."}), 400
        except Exception as e:
            print(f"Error: {e}")
            Log().register(operation=f'Team: Login Attempt')
            return jsonify({"status": False,"message": "Erro ao logar equipe!"}), 400 

    #Função que recebe os dados
    def registerTeam():
        try:
            session.clear()
            team = request.form['input-nome-form-equipe']
            password = request.form['input-password-form']
            EmMaster = request.form['input-email-form-scmaster']
            EmPOwner = request.form['input-email-form-po']

            # Recebe os desenvolvedores como listas
            dev_emails = request.form.getlist('dev_email[]')

            teams=Teams()

            # Verifica se os desenvolvedores estão cadastrados
            if Validation.UserIsRegistered(EmMaster) == False:
                return jsonify({"status": False, "message": f"Desenvolvedor {EmMaster} não cadastrado."}), 400
            if Validation.UserIsRegistered(EmPOwner) == False:
                return jsonify({"status": False, "message": f"Desenvolvedor {EmPOwner} não cadastrado."}), 400

            # Verifica se há desenvolvedores duplicados
            if len(dev_emails) != len(set(dev_emails)):
                return jsonify({"status": False, "message": "Um mesmo desenvolvedor está sendo adicionado mais de uma vez."}), 400

            for email in dev_emails:
                if Validation.UserIsRegistered(email) == False:
                    return jsonify({"status": False, "message": f"Desenvolvedor {email} não cadastrado."}), 400
                
            # Verifica se o Master ou PO está repetido na lista de devs
            if EmMaster in dev_emails or EmPOwner in dev_emails:
                return jsonify({"status": False, "message": "Scrum Master ou Product Owner não pode ser listado como desenvolvedor."}), 400
                            
            if EmMaster == EmPOwner:
                return jsonify({"status": False, "message": "Scrum Master e Product Owner não podem ser o mesmo usuário."}), 400
            
            # Busca o nome dos membros pelo email
            users = Users()
            devs = []
            for email in dev_emails:
                user = users.readUser(email)
                nome = user[0].name
                devId = f"{(dev_emails.index(email) + 1):03}"
                dev = {
                    'devId': devId,
                    'email': email,
                    'nome': nome
                }
                devs.append(dev)
            master = users.readUser(EmMaster)[0].name
            pOwner = users.readUser(EmPOwner)[0].name

            id = str(shortuuid.uuid())
            TeamsController.sendEmail(id,EmMaster)

            if teams.saveDataTeam(id ,team, password, master, EmMaster, pOwner, EmPOwner, devs):
                Log().register(operation=f'Team: Register Team')
                return jsonify({"status": True, "message": "Equipe cadastrada com sucesso!"}), 200
            else:
                return jsonify({"status": False, "message": "Erro ao cadastrar equipe."}), 400
        #Validações
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"status": False, "message": "Erro ao validar!"}), 500
        

    #Função para ler os dados
    def readAllTeams():
        teams=Teams()
        return teams.readTeam()
        
    def readTeamById():
        try:
            teams=Teams().readTeam()
            for team in teams:
                if team.id == session['team']['id']:
                    return team
            return None
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"status": False, "message": "Erro ao ler dados da equipe!"}), 500
        
    #Função para editar equipe
    def update_team():
        try:
            if 'team' not in session:
                return jsonify({"status": False, "message": "Acesso não autorizado."}), 401
            
            team_id = session['team']['id']
            team_name = request.form.get('teamName')
            EmMaster = request.form.get('EmMaster')
            EmPOwner = request.form.get('EmPOwner')
            dev_emails = request.form.getlist('dev_email')
            file = request.files.get('teamLogo')

            if file and file.filename:
                img = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                Teams().saveImage(file, img)
            else:
                img = session['team']['img']

            # Verifica se os desenvolvedores está cadastrado
            if Validation.UserIsRegistered(EmMaster)==False:
                return jsonify({"status": False, "message": f"Desenvolvedor {EmMaster} não cadastrado."}), 400
            if Validation.UserIsRegistered(EmPOwner)==False:
                return jsonify({"status": False, "message": f"Desenvolvedor {EmPOwner} não cadastrado."}), 400
            for email in dev_emails:
                if Validation.UserIsRegistered(email)==False:
                    return jsonify({"status": False, "message": f"Desenvolvedor {email} não cadastrado."}), 400
                
            # Verifica se há desenvolvedores duplicados
            if len(dev_emails) != len(set(dev_emails)):
                return jsonify({"status": False, "message": "Um mesmo desenvolvedor está sendo adicionado mais de uma vez."}), 400
            
            # Verifica se o Master ou PO está repetido na lista de devs
            if EmMaster in dev_emails or EmPOwner in dev_emails:
                return jsonify({"status": False, "message": "Scrum Master ou Product Owner não pode ser listado como desenvolvedor."}), 400
            if EmMaster == EmPOwner:
                return jsonify({"status": False, "message": "Scrum Master e Product Owner não podem ser o mesmo usuário."}), 400
            
            if img == session['team']['img']:
                img = session['team']['img']
            else:
                # Remove a imagem antiga se houver
                if session['team']['img'] and session['team']['img'] != 'default.png':
                    Teams().deleteImage(session['team']['img'])


            # Busca o nome dos membros pelo email
            users = Users()
            devs = []
            for email in dev_emails:
                user = users.readUser(email)
                nome = user[0].name
                devId = f"{(dev_emails.index(email) + 1):03}"
                dev = {
                    'devId': devId,
                    'email': email,
                    'nome': nome
                }
                devs.append(dev)
            master = users.readUser(EmMaster)[0].name
            pOwner = users.readUser(EmPOwner)[0].name

            # Chama o método do model para atualizar
            if Teams().update_team(team_id, team_name, master, pOwner, EmMaster, EmPOwner, devs, img):
                # Atualiza a sessão
                session['team'] = {
                    'id': team_id,
                    'team': team_name,
                    'master': master,
                    'pOwner': pOwner,
                    'EmMaster': EmMaster,
                    'EmPOwner': EmPOwner,
                    'devs': devs,
                    'img': img
                }

                Log().register(operation=f'Team: Update Team Data ({team_id})')
                return jsonify({"status": True, "message": "Equipe atualizada com sucesso!"}), 200
            else:
                return jsonify({"status": False, "message": "Erro ao atualizar equipe."}), 400

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"status": False, "message": "Erro interno ao atualizar equipe."}), 500


        #Função para salvar avaliações
    def saveEvaluations():
        try:
            teams = Teams()
            team = session['team']
            raw_evaluations = dict(request.form)
            evaluations = {team['EmMaster']: {}, team['EmPOwner']: {}}
            for dev in team['devs']:
                evaluations[dev['email']] = {}
            for ev in ['proatividade', 'autonomia', 'colaboracao', 'entrega']:
                evaluations[team['EmMaster']][ev] = raw_evaluations['master_' + ev]
                evaluations[team['EmPOwner']][ev] = raw_evaluations['po_' + ev]
                for dev in team['devs']:
                    devEmail = dev['email']
                    devId = dev['devId']
                    evaluations[devEmail][ev] = raw_evaluations[devId + '_' + ev]

            if teams.save_evaluations(evaluations):
                Log().register(operation=f'Team: Evaluation Saved')
                return jsonify({"status": True, "message": "Avaliações salvas com sucesso!"}), 200
            else:
                Log().register(operation=f'Team: Failed Evaluation Attempt')
                return jsonify({"status": False, "message": "Não foi possível salvar avaliações"}), 400
        except Exception as e:
            print(e)
            Log().register(operation=f'Team: Failed Evaluation Attempt')
            return jsonify({"status": False, "message": "Não foi possível salvar avaliações"}), 500
        
    def sendEmail(id, email):
        try:
            logo_path = os.path.join(app.root_path, "..", "static", "images", "logo.jpg")
            body = f"""
            <html>
                <body style="font-family: 'Arial', sans-serif; background-color: #f4f4f9; color: #333333; margin: 0; padding: 0;">
                    <!-- Container Principal -->
                    <div style="width: 100%; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                        
                        <!-- Logo -->
                        <div style="text-align: center; margin-bottom: 30px;">
                            <img src="cid:logo" style="border-radius: 15px; width: 200px; margin-bottom: 20px;" alt="Logo" />
                        </div>

                        <!-- Título -->
                        <h2 style="text-align: center; font-size: 24px; color: #333333; font-weight: 600;">Cadastro de Equipe</h2>

                        <!-- Mensagem -->
                        <p style="text-align: center; font-size: 16px; color: #555555; margin-top: 10px;">Sua equipe foi cadastrada com sucesso!</p>

                        <!-- Código de Confirmação -->
                        <div style="text-align: center; margin: 20px 0;">
                            <h1 style="color: #3b8c6e; font-size: 36px; font-weight: bold; padding: 20px; background-color: #f0f9f4; border-radius: 8px; display: inline-block; min-width: 120px;">
                                {id}
                            </h1>
                        </div>

                        <!-- Instrução -->
                        <p style="text-align: center; font-size: 14px; color: #777777;">Para o acesso à equipe, utilize esse ID junto à senha cadastrada.</p>

                        <!-- Rodapé -->
                        <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #888888;">
                            <p>&copy; 2025 SAMA. Todos os direitos reservados.</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            # Criação da mensagem com partes (HTML + Imagem)
            msg = MIMEMultipart("related")
            msg['Subject'] = 'Cadastro de Equipe'
            msg['From'] = admin_email
            msg['To'] = email

            # Adicionando o corpo HTML
            customMsg = MIMEMultipart("alternative")
            customMsg.attach(MIMEText(body, 'html'))
            msg.attach(customMsg)

             # Adicionando a imagem da logo
            try:
                with open(logo_path, 'rb') as img:
                    image = MIMEImage(img.read())
                    image.add_header('Content-ID', '<logo>')
                    msg.attach(image)
            except Exception as e:
                print(f"Error: {e}")

            # Enviando e-mail
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(admin_email, admin_password)
                server.sendmail(admin_email, email, msg.as_string())
                server.quit()
                return True
            except Exception as e:
                print(f"Error: {e}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def deleteEvaluation():
        try:
            if 'team' not in session:
                return jsonify({"status": False, "message": "Acesso não autorizado."}), 401
            
            team_id = session['team']['id']
            evaluation_time = request.form.get('evaluation_time')

            if Teams().deleteEvaluation(team_id, evaluation_time):
                Log().register(operation=f'Team: Evaluation Deleted ({evaluation_time})')
                return jsonify({"status": True, "message": "Avaliação deletada com sucesso!"}), 200
            else:
                Log().register(operation=f'Team: Failed Evaluation Deletion Attempt ({evaluation_time})')
                return jsonify({"status": False, "message": "Erro ao deletar avaliação."}), 400
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"status": False, "message": "Erro interno ao deletar avaliação."}), 500
        
    def deleteTeam():
        try:
            teams = Teams()
            if teams.deleteTeam():
                session.clear()
                return jsonify({"status": True, "message": "Equipe excluída com sucesso!"}), 200
            else:
                return jsonify({"status": False, "message": "Erro ao excluir equipe."}), 400
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"status": False, "message": "Erro interno ao excluir equipe."}), 500