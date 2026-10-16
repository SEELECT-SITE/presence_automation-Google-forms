import pandas as pd
import smtplib
import io
import os
import glob
import time
import random
import unicodedata
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSans-Bold.ttf'))

# Configurações
DIRETORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_CSVS = os.path.join(DIRETORIO_SCRIPT, 'frequencia')
TEMPLATE_CERTIFICADO = os.path.join(DIRETORIO_SCRIPT, 'certificado_padrao.pdf')
PASTA_SAIDA = os.path.join(DIRETORIO_SCRIPT, 'certificados_gerados')

EMAIL_REMETENTE = 'seelect2023@gmail.com' 
SENHA_REMETENTE = 'uegqadhyrluhxdgw' 
ASSUNTO_EMAIL = 'Certificado Visita Técnica Ajustado - SEELECT UFC 2026'
CORPO_EMAIL = 'Olá, {nome}!\n\nSegue em anexo o seu certificado de participação na visita técnica da SEELECT 2026.\n\nEm caso de dúvidas ou problemas, entre em contato por e-mail: seelect@ufc.br\n\nAtenciosamente,\nEquipe Organizadora da SEELECT'

# Coordenadas (X, Y) no certificado
COORD_NOME = (421, 370)        
COORD_TEXTO_NOVO = (421, 310)  
COORD_HORAS = (421, 240)       


def sanitizar_nome_arquivo(texto):
    """Remove acentos para uso seguro em nomes de arquivo."""
    texto_normalizado = unicodedata.normalize('NFD', str(texto))
    sem_acento = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    return sem_acento.replace(' ', '_')

if not os.path.exists(PASTA_SAIDA):
    os.makedirs(PASTA_SAIDA)

def preencher_certificado(nome, horas, caminho_saida, nome_evento):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=landscape(A4))
    
    c.setFont("DejaVu-Bold", 30)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(COORD_NOME[0], COORD_NOME[1], str(nome))
    
    c.setFont("DejaVu", 16)
    
    
    texto_linhas = [
        f"participou da visita técnica a(o) {nome_evento},",
        "promovida pela Semana de Engenharia Elétrica, da Computação e de",
        "Telecomunicações da UFC, com carga horária total de 4 horas."
    ]
    
    espaco = 25 
    for i, linha in enumerate(texto_linhas):
        altura_atual = COORD_TEXTO_NOVO[1] - (i * espaco)
        c.drawCentredString(COORD_TEXTO_NOVO[0], altura_atual, linha)
    
    c.save()
  
    packet.seek(0)
    novo_pdf = PdfReader(packet)
    
    template = PdfReader(open(TEMPLATE_CERTIFICADO, "rb"))
    output = PdfWriter()
    
    pagina = template.pages[0]
    pagina.merge_page(novo_pdf.pages[0])
    output.add_page(pagina)
    
    with open(caminho_saida, "wb") as outputStream:
        output.write(outputStream)

# Envio dos emails

def enviar_email(nome, email_destinatario, arquivo_certificado, horas):
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = email_destinatario
    msg['Subject'] = ASSUNTO_EMAIL
    
    corpo = CORPO_EMAIL.format(nome=nome, horas=horas)
    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
    
    with open(arquivo_certificado, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(arquivo_certificado)}"')
        msg.attach(part)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        server.send_message(msg)
        server.quit()
        print(f"E-mail enviado com sucesso para: {email_destinatario}")
    except Exception as e:
        print(f"Erro ao enviar e-mail para {email_destinatario}: {e}")

def main():
    print("--- INICIANDO LEITURA DE MÚLTIPLAS PLANILHAS ---")
    
    
    arquivos_csv = glob.glob(os.path.join(PASTA_CSVS, "*.csv"))
    
    if not arquivos_csv:
        print(f"ERRO: Nenhum arquivo CSV encontrado na pasta '{PASTA_CSVS}'!")
        print("Crie a pasta, coloque os arquivos CSV lá dentro e tente novamente.")
        return
        
    print(f"Encontrados {len(arquivos_csv)} arquivos de presença. Juntando dados...")

    print("## VERIFICANDO ARQUIVOS ##")
    for arquivo in arquivos_csv:
        try:
            pd.read_csv(arquivo)
            print(f" OK: {os.path.basename(arquivo)}")
        except Exception as e:
            print(f" PROBLEMA: {os.path.basename(arquivo)} → {e}")
    print("----------------------------\n")
    

    lista_dfs = []
    for arquivo in arquivos_csv:
        df_temp = pd.read_csv(arquivo, on_bad_lines='skip')
        
       
        df_temp.columns = df_temp.columns.str.strip()
        
        if 'Email' in df_temp.columns and 'Endereço de e-mail' in df_temp.columns:
            df_temp = df_temp.drop(columns=['Endereço de e-mail'])
            
        if 'Nome Completo' in df_temp.columns and 'Nome completo' in df_temp.columns:
             df_temp = df_temp.drop(columns=['Nome completo'])
        elif 'Nome Completo' in df_temp.columns and 'Nome' in df_temp.columns:
             df_temp = df_temp.drop(columns=['Nome'])
        
        #  TRADUTOR DE COLUNAS (Padronização)
        tradutor_colunas = {
            'Nome': 'Nome Completo',
    'nome completo': 'Nome Completo', 
    'Nome do Participante': 'Nome Completo',
    'Nome completo': 'Nome Completo',
    'nome': 'Nome Completo',
    'NOME COMPLETO': 'Nome Completo', 
    'Nome do Aluno': 'Nome Completo',  
    'Endereço de e-mail': 'Email',
    'email': 'Email',
    'E-mail': 'Email'
        }
        df_temp = df_temp.rename(columns=tradutor_colunas)
        
        nome_do_evento = os.path.basename(arquivo).replace('.csv', '')
        df_temp['Eventos Participados'] = nome_do_evento

        # Removendo o mesmo aluno assinando a lista duas vezes no mesmo dia (Agora usando o Email)
        if 'Email' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Email'])
        else:
            print(f"AVISO: A coluna de e-mail não foi encontrada no arquivo {arquivo}! Verifique o cabeçalho.")
            
        lista_dfs.append(df_temp)
        
    df_total = pd.concat(lista_dfs, ignore_index=True)

    df_final = df_total[['Nome Completo', 'Email', 'Eventos Participados']].copy()
    df_final['Horas'] = 4  # Fixo: 4 horas por visita

    print(f"Cálculo concluído! {len(df_final)} certificados serão gerados.\n")

    # GERA RELATÓRIO GERAL EM CSV 
    print("Gerando relatório final de participantes...")
    df_final.to_csv('relatorio_final_participantes.csv', index=False, encoding='utf-8-sig')
    print("Relatório 'relatorio_final_participantes.csv' salvo com sucesso!\n")

    print("--- FASE 1: GERAÇÃO DOS CERTIFICADOS ---")
    for index, row in df_final.iterrows():
        try:
            nome = str(row['Nome Completo'])
            email = row['Email']
            horas = row['Horas']
            nome_evento = row['Eventos Participados']

            if nome.lower() == 'nan' or nome.strip() == '':
                print(f" AVISO: Nome em branco! Email: {email}. Pulando...")
                continue

            # Nome do arquivo inclui o evento para não sobrescrever
            nome_arquivo = f"Certificado_{sanitizar_nome_arquivo(nome)}_{sanitizar_nome_arquivo(nome_evento)}.pdf"
            caminho_certificado = os.path.join(PASTA_SAIDA, nome_arquivo)

            print(f"A gerar certificado para {nome} | Visita: {nome_evento}...")
            preencher_certificado(nome, horas, caminho_certificado, nome_evento)

        except Exception as e:
            print("\n" + "="*40)
            print(f" ERRO AO GERAR CERTIFICADO!")
            print(f"Email: {row.get('Email', 'Não encontrado')} | Evento: {row.get('Eventos Participados', '?')}")
            print(f"Erro: {e}")
            print("="*40 + "\n")

    # Confirmando se envia os emails
    resposta = input("\nDeseja enviar os e-mails agora? (Escreva 'S' para Sim, ou qualquer outra tecla para cancelar): ")

    if resposta.strip().upper() == 'S':
        print("\n - ENVIO DE EMAILS - ")
        for index, row in df_final.iterrows():
            nome = str(row['Nome Completo'])
            email = str(row['Email'])
            horas = row['Horas']
            nome_evento = str(row['Eventos Participados'])

            if nome.lower() == 'nan' or email.lower() == 'nan':
                print(f" Dados inválidos na linha {index}. Pulando...")
                continue

            nome_arquivo = f"Certificado_{sanitizar_nome_arquivo(nome)}_{sanitizar_nome_arquivo(nome_evento)}.pdf"
            caminho_certificado = os.path.join(PASTA_SAIDA, nome_arquivo)

            print(f"A preparar envio para {email} | Visita: {nome_evento}...")
            enviar_email(nome, email, caminho_certificado, horas)

            print("Pausa para evitar bloqueio por spam.")
            tempo = random.uniform(3, 7)
            time.sleep(tempo)
            print("-" * 30)

        print("\nProcesso de envio concluído com sucesso!")
    else:
        print("\nEnvio cancelado pelo usuário.")

if __name__ == "__main__":
    main()