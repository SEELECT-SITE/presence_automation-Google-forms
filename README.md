# Automação de Certificados e Envio de E-mails - SEELECT

> [!WARNING]: Nunca faça o commit das presenças no github. Sempre verifique se existem arquivos CSV ou PDFs com dados sensíveis antes de subir o repositório.

Este repositório contém duas automações em Python desenvolvidas para processar as listas de presença (exportadas do Google Forms em formato CSV), gerar certificados personalizados em PDF e realizar o envio automático dos certificados por e-mail para os participantes.

## Estrutura do Repositório

├── Certificados das Visitas Técnicas/
│ ├── automacao.py # Script para certificados de visitas técnicas individuais
│ ├── certificado_padrao.pdf # Template base do certificado em PDF
│ ├── frequencia/ # [Entrada] Onde devem ser colocados os CSVs das visitas
│ └── certificados_gerados/ # [Saída] Onde os PDFs gerados serão salvos
│
├── Certificados dos Eventos SEELECT/
│ ├── automacao.py # Script para palestras e eventos gerais com soma de horas
│ ├── certificado_padrao.pdf # Template base do certificado em PDF
│ ├── lista_presenca/ # [Entrada] Onde devem ser colocados os CSVs dos eventos
│ └── certificados_gerados/ # [Saída] Onde os PDFs gerados serão salvos
│
└── README.md

## Onde Alterar as Frases e Textos

### 1. Frases do E-mail (Assunto e Mensagem)

Em ambos os arquivos `automacao.py`, as configurações de e-mail ficam no início do script:

- **Certificados dos Eventos SEELECT**: linhas ~25 a 27.
- **Certificados das Visitas Técnicas**: linhas ~29 a 31.

## Detalhes Importantes de Funcionamento

### 1. O Nome do Arquivo CSV define o Nome do Evento

O script extrai o nome do evento diretamente do nome do arquivo `.csv` (removendo a extensão).

- **Atenção**: Nomeie os arquivos CSV na pasta de entrada de forma limpa e padronizada antes de rodar o código.

## Como Executar

1. **Instale as dependências necessárias**:

   ```bash
   pip install pandas reportlab pypdf
   ```

2. **Para gerar certificados dos Eventos Gerais**:
   - Coloque os CSVs dos formulários na pasta `Certificados dos Eventos SEELECT/lista_presenca/`.
   - Certifique-se de que o arquivo `certificado_padrao.pdf` está presente na pasta.
   - Execute:
     ```bash
     cd "Certificados dos Eventos SEELECT"
     python automacao.py
     ```

3. **Para gerar certificados das Visitas Técnicas**:
   - Coloque os CSVs dos formulários na pasta `Certificados das Visitas Técnicas/frequencia/`.
   - Certifique-se de que o arquivo `certificado_padrao.pdf` (e os arquivos `.ttf` de fonte se aplicável) estão na pasta.
   - Execute:
     ```bash
     cd "Certificados das Visitas Técnicas"
     python automacao.py
     ```
