import pandas as pd
import smtplib
import io
import os
import glob
import time
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from pypdf import PdfReader, PdfWriter

# Configurações
DIRETORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
# Detecta automaticamente 'lista_presenca' (singular) ou 'listas_presenca' (plural)
PASTA_CSVS = os.path.join(DIRETORIO_SCRIPT, 'lista_presenca') if os.path.exists(os.path.join(DIRETORIO_SCRIPT, 'lista_presenca')) else os.path.join(DIRETORIO_SCRIPT, 'listas_presenca')
TEMPLATE_CERTIFICADO = os.path.join(DIRETORIO_SCRIPT, 'certificado_padrao.pdf')
PASTA_SAIDA = os.path.join(DIRETORIO_SCRIPT, 'certificados_gerados')

EMAIL_REMETENTE = 'seelect2023@gmail.com' 
SENHA_REMETENTE = 'uegqadhyrluhxdgw' 
ASSUNTO_EMAIL = 'Certificado de Participação SEELECT 2025'
CORPO_EMAIL = 'Olá, {nome}!\n\nSegue em anexo o seu certificado de participação da SEELECT 2025.\n\nDevido a um erro de compatibilidade, estamos reenviando o certificado. Em caso de dúvidas ou problemas, entre em contato por e-mail: seelect@ufc.br\n\nAtenciosamente,\nEquipe Organizadora da SEELECT'

# Coordenadas (X, Y)
COORD_NOME = (421, 370)        
COORD_TEXTO_NOVO = (421, 310)  
COORD_HORAS = (421, 240)       


if not os.path.exists(PASTA_SAIDA):
    os.makedirs(PASTA_SAIDA)

def preencher_certificado(nome, horas, caminho_saida):
    """Gera um PDF com o texto e mescla por cima do template padrão."""
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=landscape(A4))
    
    
    c.setFont("Helvetica-Bold", 30)
    c.setFillColorRGB(1, 1, 1)  # Set font color to white
    c.drawCentredString(COORD_NOME[0], COORD_NOME[1], str(nome))
    
    c.setFont("Helvetica", 16)
    

    texto_linhas = [
        "participou da Semana de Engenharia Elétrica, da Computação e de",
        "Telecomunicações da Universidade Federal do Ceará, no período",
        f"de 3 a 7 de novembro de 2025, com carga horária total de {horas} horas."
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

def enviar_email(nome, email_destinatario, arquivo_certificado, horas):
    """Envia o e-mail com o certificado em anexo."""
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
    print(" INICIANDO LEITURA DE MÚLTIPLAS PLANILHAS ")
    
    # Encontra todos os arquivos CSV na pasta especificada
    arquivos_csv = glob.glob(os.path.join(PASTA_CSVS, "*.csv"))
    
    if not arquivos_csv:
        print(f"ERRO: Nenhum arquivo CSV encontrado na pasta '{PASTA_CSVS}'!")
        print("Crie a pasta, coloque os arquivos CSV lá dentro e tente novamente.")
        return
        
    print(f"Encontrados {len(arquivos_csv)} arquivos de presença. Juntando dados...")
    
    # Lê e junta todas as planilhas
    lista_dfs = []
    for arquivo in arquivos_csv:
        df_temp = pd.read_csv(arquivo)
        
        df_temp.columns = df_temp.columns.str.strip()
        
        # PROTEÇÃO CONTRA COLUNAS DUPLICADAS DO GOOGLE FORMS
      
        if 'Email' in df_temp.columns and 'Endereço de e-mail' in df_temp.columns:
            df_temp = df_temp.drop(columns=['Endereço de e-mail'])
            
        if 'Nome Completo' in df_temp.columns and 'Nome completo' in df_temp.columns:
             df_temp = df_temp.drop(columns=['Nome completo'])
        elif 'Nome Completo' in df_temp.columns and 'Nome' in df_temp.columns:
             df_temp = df_temp.drop(columns=['Nome'])
        
        #  O TRADUTOR DE COLUNAS (Padronização)
        # Sinta-se à vontade para adicionar outras variações aqui se encontrar nos seus CSVs
        tradutor_colunas = {
            'Nome': 'Nome Completo',
            'nome completo': 'Nome Completo', 
            'Nome do Participante': 'Nome Completo',
            'Nome completo': 'Nome Completo',
            'nome': 'Nome Completo',
            
            'Endereço de e-mail': 'Email',
            'email': 'Email',
            'E-mail': 'Email',
            
            'Matricula': 'Matrícula',
            'Nº da Matrícula': 'Matrícula',
            'matricula': 'Matrícula'
        }
        df_temp = df_temp.rename(columns=tradutor_colunas)
   
        nome_do_evento = os.path.basename(arquivo).replace('.csv', '')
        df_temp['Eventos Participados'] = nome_do_evento
    

        #  Remove o mesmo aluno assinando a lista duas vezes no mesmo dia
        if 'Matrícula' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Matrícula'])
        else:
            print(f"AVISO: A coluna 'Matrícula' não foi encontrada no arquivo {arquivo}! Verifique o cabeçalho.")
            
        lista_dfs.append(df_temp)
        
    df_total = pd.concat(lista_dfs, ignore_index=True)

    # Calcula as horas agrupando pela Matrícula
    # Conta em quantas planilhas diferentes a matrícula apareceu
    contagem_presencas = df_total.groupby('Matrícula').size().reset_index(name='Presencas')
    
    # Pega o primeiro nome e email associados àquela matrícula para usar no certificado
    # Pega o primeiro nome, email e JUNTA os eventos participados
    alunos_unicos = df_total.groupby('Matrícula').agg({
        'Nome Completo': 'first',
        'Email': 'first',
        'Eventos Participados': lambda x: ', '.join(x)  
    }).reset_index()
    
    # Junta os dados do aluno com o total de presenças
    df_final = pd.merge(alunos_unicos, contagem_presencas, on='Matrícula')
    
    # Multiplica cada presença por 2 horas ( 1 palestra = 2 horas)
    df_final['Horas'] = df_final['Presencas'] * 2
    
    print(f"Cálculo concluído! {len(df_final)} alunos únicos receberão certificados.\n")
    
    #  RELATÓRIO GERAL EM CSV 
    print("Gerando relatório final de participantes...")

    colunas_relatorio = ['Nome Completo', 'Matrícula', 'Email', 'Horas', 'Eventos Participados']
    df_relatorio = df_final[colunas_relatorio]
    caminho_relatorio = os.path.join(DIRETORIO_SCRIPT, 'relatorio_final_participantes.csv')
    df_relatorio.to_csv(caminho_relatorio, index=False, encoding='utf-8-sig')
    print(" Relatório 'relatorio_final_participantes.csv' salvo com sucesso!\n")

    
    print(" GERAÇÃO DOS CERTIFICADOS ")
    for index, row in df_final.iterrows():
  
        try:
            nome = str(row['Nome Completo'])
            email = row['Email']
            horas = row['Horas']
            matricula = row['Matrícula'] # Pegamos a matrícula para caso dê erro
            
  
            if nome.lower() == 'nan' or nome.strip() == '':
                print(f" AVISO: Nome em branco encontrado! Matrícula: {matricula} | Email: {email}. Pulando este certificado...")
                continue 
                
            nome_arquivo = f"Certificado_{nome.replace(' ', '_')}.pdf"
            caminho_certificado = os.path.join(PASTA_SAIDA, nome_arquivo)
            
            print(f"A gerar certificado para {nome} ({horas} horas)...")
            preencher_certificado(nome, horas, caminho_certificado)
            
        except Exception as e:
            print("\n" + "="*40)
            print(f" ERRO AO GERAR CERTIFICADO!")
            print(f"Provável causador - Matrícula: {row.get('Matrícula', 'Não encontrada')}")
            print(f"Dados da linha: \n{row}")
            print(f"Erro do Python: {e}")
            print("="*40 + "\n")
    
  
    
    #  Envio de e-mails
    resposta = input("\nDeseja enviar os e-mails agora? (Escreva 'S' para Sim, ou qualquer outra tecla para cancelar): ")
    
    if resposta.strip().upper() == 'S':
        print("\n ENVIO DE E-MAILS ")
        for index, row in df_final.iterrows():
            nome = row['Nome Completo']
            email = row['Email']
            horas = row['Horas']
            
            nome_arquivo = f"Certificado_{nome.replace(' ', '_')}.pdf"
            caminho_certificado = os.path.join(PASTA_SAIDA, nome_arquivo)
            
            print(f"A preparar envio para {email}...")
            enviar_email(nome, email, caminho_certificado, horas)
            
            print("A aguardar 3 segundos para evitar bloqueio por spam.")
            time.sleep(3*random.uniform(2, 5))
   
            print("-" * 30)
            
        print("\nProcesso de envio concluído com sucesso!")
    else:
        print("\nEnvio cancelado pelo usuário.")



if __name__ == "__main__":
    main()