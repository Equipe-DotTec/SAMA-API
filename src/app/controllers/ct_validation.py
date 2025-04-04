import random
from flask import session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from app import admin_email, admin_password
import re
import os
from app import app

class Validade:

    def validar_cpf(cpf):
         # Remove qualquer caractere não numérico
        cpf = re.sub(r'[^0-9]', '', cpf)
    
        # Verifica se o CPF tem 11 dígitos
        if len(cpf) != 11:
            return False
    
        # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
        if cpf == cpf[0] * 11:
            return False
    
        # Validação do primeiro dígito verificador
        soma_1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito_1 = (soma_1 * 10) % 11
        if digito_1 == 10 or digito_1 == 11:
            digito_1 = 0
    
        # Validação do segundo dígito verificador
        soma_2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito_2 = (soma_2 * 10) % 11
        if digito_2 == 10 or digito_2 == 11:
            digito_2 = 0
    
        # Verifica se os dígitos verificadores estão corretos
        if cpf[9] == str(digito_1) and cpf[10] == str(digito_2):
            return True
        return False

    def enviar_codigo(email):
        session['codigo'] = str(random.randint(100000, 999999))
        logo_path = os.path.join(app.root_path, "..", "static", "images", "logo.jpg")
        corpo = f"""
            <html>
                <body style="font-family: Arial; color: #000000;">
                    <img src="cid:logo" style="border-radius:15px;width: 500px; margin-bottom: 20px;">
                    <h2 style="text-align:center">Confirmação de E-mail</h2>
                    <p style="text-align:center">Seu código de confirmação:</p>
                    <h1 style="color: #3b8c6e; text-align:center">{session['codigo']}</h1>
                </body>
            </html>
            """

        # Criação da mensagem com partes (HTML + Imagem)
        msg = MIMEMultipart("related")
        msg['Subject'] = 'Código de Confirmação'
        msg['From'] = admin_email
        msg['To'] = email

        # Adicionando o corpo HTML
        msg_alternativo = MIMEMultipart("alternative")
        msg_alternativo.attach(MIMEText(corpo, 'html'))
        msg.attach(msg_alternativo)

        # Adicionando a imagem da logo
        try:
            with open(logo_path, 'rb') as img:
                imagem = MIMEImage(img.read())
                imagem.add_header('Content-ID', '<logo>')
                msg.attach(imagem)
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")

        # Enviando e-mail
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(admin_email, admin_password)
            server.sendmail(admin_email, email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            return False
    
    def confirmar_email(codigo):
        try:
            if codigo == session['codigo']:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False
        
    def validar_arquivo(arquivo):
        if arquivo.filename.endswith(".pdf"):
            return True
        return False