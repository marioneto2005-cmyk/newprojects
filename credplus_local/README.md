# Proposta Seguro Auto - Segurado v26.10.23.1

Aplicativo desktop para transformar um PDF de seguro em uma proposta visual, com opções de cobertura e planos de pagamento. Processamento inteiramente local; não usa serviços externos, conta Microsoft ou integração com AD. O código e o empacotador estão neste pacote. O novo executável deve ser construído em Windows.

## Usar o programa

1. Abra `PropostaSeguroAuto.exe` na pasta completa distribuída. Não é necessário instalar Python, Office ou Tesseract nas estações finais: os componentes são incluídos na construção.
2. Clique **Importar proposta PDF**. Logo após escolher o arquivo, abre a janela **Corretora** com Aliro, Allianz, Azul, HDI, Mapfre, Tokio Marine, Yelum e Zurich. Escolha a correspondente; a leitura começa automaticamente. O arquivo `ALRIO.pdf` foi identificado pelo conteúdo como Aliro.
3. Os dados aparecem em **Cliente e veículo**, **Opções e coberturas** e **Formas de pagamento**. Todas as opções identificadas são importadas; não há seletor de opção na tela principal. Os valores podem ser editados diretamente, sem confirmação individual. Nas tabelas, use duplo clique no valor. Também é possível adicionar opções e pagamentos manualmente.
4. No canto superior direito, clique **Alterar logomarca** e escolha PNG, JPEG ou WebP. A imagem é normalizada e salva no perfil do usuário; permanece após fechar o programa e trocar de pasta/versão. A imagem original não precisa permanecer no local. O botão **Remover** apaga a marca salva. Não há logomarca de cliente embutida no aplicativo; a marca dos exemplos é fictícia.
5. Informe consultor e WhatsApp se desejar. Esses dados começam vazios; não são persistidos com a logomarca.
6. Abra **Prévia do documento** ou clique diretamente em **Gerar PDF** / **Gerar PNG**. Não há checkbox de conferência ou confirmação obrigatória de campos. Campos vazios e marcadores “Não informado” não aparecem no documento do cliente. A exportação em Excel foi removida da interface.

Nome de corretora/seguradora pode aparecer na proposta. Número de cotação, número de apólice, dados bancários e seções jurídicas integrais não são copiados para a saída. O programa não envia arquivos ou mensagens. A identificação do fornecedor é utilizada conforme escolhido na janela Corretora.

## Documento em página única

PDF e PNG usam o mesmo desenho, com identidade visual configurável, blocos de cliente/veículo, comparação das coberturas, franquias e tabelas de pagamento. A fonte não é reduzida para espremer tudo em A4. A largura do PDF equivale à A4; **a altura é adaptada ao conteúdo**, mantendo uma página digital única. Propostas com seis opções e muitas formas de pagamento ficam mais longas. Na impressão em uma folha A4, a função “ajustar à página” do leitor reduzirá o conteúdo; o PNG é adequado para envio digital. A imagem é gerada a 150 dpi da própria página PDF.

Todas as linhas de parcelamento reconhecidas são preservadas, incluindo os planos intermediários, juros, entrada e totais quando expressos no documento. O número de parcelas inclui a entrada quando indicada. Um cronograma com primeira/última parcelas diferentes é apresentado com esses valores. Totais de parcelas não são inventados pela multiplicação de valores arredondados. Diferenças entre tabela de coberturas e tabela de pagamento são mantidas com nota explicativa.

Os oito layouts anexados foram exercitados de ponta a ponta. Isso não garante leitura universal: novos modelos, versões de PDF ou OCR podem omitir campos e linhas não reconhecidos. Ausência de um campo não significa cobertura não contratada. Não há etapa de revisão obrigatória; a edição é opcional. Dados cuja leitura é ambígua continuam sem valor automático, e não são substituídos por estimativas. PDFs protegidos precisam de cópia autorizada sem senha. Limite de 60 páginas por documento.

## Construir o executável no Windows

Use uma máquina Windows x64 com Python 3.12 x64, Tcl/Tk, pip e acesso autorizado aos pacotes Python. Forneça um diretório Tesseract 5 completo, com executável, DLLs, licenças e `tessdata/por.traineddata` e `tessdata/eng.traineddata`. O script não baixa executáveis OCR.

Abra o PowerShell na pasta extraída e execute:

```powershell
.\build_windows.ps1 -TesseractDir 'C:\Program Files\Tesseract-OCR'
```

O script instala as dependências na máquina de construção, executa os testes e empacota o aplicativo. Saídas:

```text
dist\PropostaSeguroAuto\PropostaSeguroAuto.exe
dist\PropostaSeguroAuto-26.10.23.1-Windows.zip
```

Distribua **a pasta completa ou o ZIP**, incluindo `_internal`; não copie somente o executável. O executável anterior não se atualiza automaticamente. Construa em uma nova pasta e feche a versão antiga antes de trocar o pacote. A marca salva é reaproveitada no perfil do usuário.

Em computador corporativo, use o processo autorizado da TI para scripts, assinatura e distribuição, sem alterar as políticas do AD/AppLocker/WDAC. A TI deve homologar o executável com usuário padrão. O aplicativo precisa executar o processo filho OCR e escrever no temporário/perfil do usuário. Esta versão foi testada no Linux com tela virtual; o pacote Windows deve ser reconstruído e homologado no Windows.

## Desenvolvimento

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_app.py
```

Requer Tkinter para a interface. Para OCR, instale Tesseract com português/inglês ou use `CREDPLUS_TESSERACT` e `CREDPLUS_TESSDATA`. Os testes gráficos requerem uma tela; no Linux, podem usar Xvfb. As fixtures comerciais contêm trechos de tabelas sem nomes, documentos de identidade ou contas de clientes; os PDFs originais não são distribuídos.

A marca é armazenada em `%LOCALAPPDATA%\PropostaSeguroAuto\logo.png` no Windows. Para testes/ambientes especiais, `PROPOSTA_SETTINGS_DIR` substitui essa pasta. Nenhum projeto ou dado de cliente é salvo automaticamente nessa configuração.

Veja `exemplos/Proposta_Exemplo.pdf`, `exemplos/Proposta_Exemplo.png`, `exemplos/Tela_Interface.png` e `RELATORIO.md`. Os exemplos usam dados pessoais fictícios e valores comerciais de demonstração.
