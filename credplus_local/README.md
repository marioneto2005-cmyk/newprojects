# Proposta Seguro Auto - Segurado v26.10.26.4

Aplicativo desktop para transformar um PDF de seguro em uma proposta visual, com opções de cobertura e planos de pagamento. Processamento inteiramente local; não usa serviços externos, conta Microsoft ou integração com AD. O código e o empacotador estão neste pacote. O novo executável deve ser construído em Windows.

## Usar o programa

1. Abra `PropostaSeguroAuto_26.10.26.4.exe` na pasta completa distribuída. Não é necessário instalar Python, Office ou Tesseract nas estações finais: os componentes são incluídos na construção.
2. Clique **Importar proposta PDF**. Ao escolher um novo arquivo, os dados da proposta, os contatos e a prévia anteriores são limpos, mantendo a marca salva. A tela volta ao início da aba Cliente e veículo, antes de processar. Em seguida, abre a janela **Corretora** com Aliro, Allianz, Azul, HDI, Mapfre, Porto Seguro, Tokio Marine, Yelum e Zurich. Escolha a correspondente; a leitura começa automaticamente. O arquivo `ALRIO.pdf` foi identificado pelo conteúdo como Aliro.
3. Os dados aparecem em **Cliente e veículo**, **Opções e coberturas** e **Formas de pagamento**. Todas as opções identificadas são importadas; não há seletor de opção na tela principal. Os valores podem ser editados diretamente, sem confirmação individual. Nas tabelas, use duplo clique no valor. Também é possível adicionar opções e pagamentos manualmente.
4. No canto superior direito, clique **Alterar logomarca** e escolha PNG, JPEG ou WebP. A imagem é normalizada e salva no perfil do usuário; permanece após fechar o programa e trocar de pasta/versão. A imagem original não precisa permanecer no local. O botão **Remover** apaga a marca salva. Não há logomarca de cliente embutida no aplicativo; a marca dos exemplos é fictícia.
5. Informe consultor e WhatsApp se desejar. Esses dados começam vazios; não são persistidos com a logomarca.
6. Abra **Prévia do documento** ou clique diretamente em **Gerar PDF** / **Gerar PNG**. Não há checkbox de conferência ou confirmação obrigatória de campos. Campos vazios e marcadores “Não informado” não aparecem no documento do cliente. A exportação em Excel foi removida da interface.

Nome de corretora/seguradora pode aparecer na proposta. Número de cotação, número de apólice, dados bancários e seções jurídicas integrais não são copiados para a saída. O programa não envia arquivos ou mensagens. A identificação do fornecedor é utilizada conforme escolhido na janela Corretora.

## Documento em página única

PDF e PNG usam o mesmo desenho, com identidade visual configurável, blocos de cliente/veículo, comparação das coberturas, franquias e tabelas de pagamento. A fonte não é reduzida para espremer tudo em A4. A largura do PDF equivale à A4; **a altura é adaptada ao conteúdo**, mantendo uma página digital única. Propostas com seis opções e muitas formas de pagamento ficam mais longas. Na impressão em uma folha A4, a função “ajustar à página” do leitor reduzirá o conteúdo; o PNG é adequado para envio digital. A imagem é gerada a 150 dpi da própria página PDF.

Todas as linhas de parcelamento reconhecidas são preservadas, incluindo os planos intermediários, juros, entrada e totais quando expressos no documento. O número de parcelas inclui a entrada quando indicada. Um cronograma com primeira/última parcelas diferentes é apresentado com esses valores. Totais de parcelas não são inventados pela multiplicação de valores arredondados. Diferenças entre tabela de coberturas e tabela de pagamento são mantidas com nota explicativa.

Os nove fornecedores e os layouts anexados foram exercitados de ponta a ponta. Isso não garante leitura universal: novos modelos, versões de PDF ou OCR podem omitir campos e linhas não reconhecidos. Ausência de um campo não significa cobertura não contratada. Não há etapa de revisão obrigatória; a edição é opcional. Dados cuja leitura é ambígua continuam sem valor automático, e não são substituídos por estimativas. PDFs protegidos precisam de cópia autorizada sem senha. Limite de 60 páginas por documento.

## Construir o executável no Windows

Use uma máquina Windows x64 com Python 3.12 x64, Tcl/Tk, pip e acesso autorizado aos pacotes Python. Forneça um diretório Tesseract 5 completo, com executável, DLLs, licenças e `tessdata/por.traineddata` e `tessdata/eng.traineddata`. O script não baixa executáveis OCR.

Abra o PowerShell na pasta extraída e execute:

```powershell
.\build_windows.ps1 -TesseractDir 'C:\Program Files\Tesseract-OCR'
```

O script instala as dependências na máquina de construção, executa os testes e empacota o aplicativo. Saídas:

```text
dist\PropostaSeguroAuto_26.10.26.4\PropostaSeguroAuto_26.10.26.4.exe
dist\PropostaSeguroAuto-26.10.26.4-Windows.zip
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

## Histórico: correção 26.10.23.2

A construção 26.10.23.1 relatada no Windows parou em dois testes de edição porque simulavam uma tecla Enter que depende do foco da janela. A edição agora usa um evento de salvamento compartilhado por Enter, Enter do teclado numérico e a automação gráfica, mantendo o salvamento ao sair do campo. Os testes de interface acionam esse evento sem depender da janela ativa. Dois testes adicionais cobrem a edição sem foco e o salvamento na perda de foco. Nenhum teste foi desativado, e o empacotador continua interrompendo a construção se houver falhas. A suite de 64 testes passou no Linux com Xvfb; a nova construção deve ser executada no Windows.

## Revisão 26.10.26.1

A arte PDF/PNG usa o rótulo **Seguradora** e o título **Proposta de Seguro Auto** em uma linha, com fonte de 16 pontos. A janela de seleção continua com o nome Corretora, conforme o fluxo anterior solicitado. A revisão corrige a leitura das tabelas de proponente/condutor e veículo da Tokio, incluindo placa, chassi, ano, fabricante e modelo. Se o documento identifica o condutor como o próprio segurado/proponente, ou traz os mesmos nomes completos, o CPF/CNPJ do proponente pode preencher o CPF/CNPJ do condutor vazio. Um documento de condutor já preenchido não é substituído; pessoas diferentes não recebem o mesmo documento automaticamente.

O CEP da Yelum é lido na coluna de pernoite, sem confundir com a região tarifária. Se o original trouxer somente cinco dígitos, a aplicação mostra `12345 (parcial no documento)`, sem acrescentar `000`. O anexo analisado traz `35595`, sem os últimos três dígitos. É possível informar um CEP completo conhecido no campo, mantendo a marcação parcial enquanto só houver o prefixo.

Ao cancelar apenas o seletor de arquivos, a proposta atual permanece. Depois de escolher um novo PDF, a proposta antiga já foi limpa mesmo que a janela de Corretora seja cancelada. Os 81 testes passaram no Linux com tela virtual; a construção Windows continua necessária para gerar o executável desta revisão.

## Revisão 26.10.26.2

- Endereços, bairro/cidade e CEPs do segurado/pernoite/circulação são realçados em amarelo no PDF e PNG quando disponíveis. Endereços de corretor, filial e ouvidoria não são reaproveitados como se fossem do cliente. Os novos campos também podem ser preenchidos na aba Cliente e veículo. Nenhum endereço é completado a partir de CEP ou nome.
- A seção dos componentes passa a se chamar **Franquia e Assistências** para todos os fornecedores.
- A Allianz lê a franquia na seção **Franquia - Participação Obrigatória** e reconhece modalidades de pagamento mesmo quando “Oferta (R$)” não está na mesma linha. A leitura dos cabeçalhos em PDFs escaneados remove o fundo azul claro antes do OCR. Valores ilegíveis em uma coluna não deslocam os das outras colunas. A franquia de perda parcial não é atribuída à opção Roubo e Furto, que exclui esse evento.
- A Tokio importa somente **Auto**; Auto Clássico e seus pagamentos foram excluídos da importação automática.
- **Porto Seguro** foi adicionada à janela de seleção. O arquivo recebido é escaneado e apresenta o produto Azul Tradicional e Proteção Combinada, co-branded Porto Seguro/Azul; essa identificação é preservada na arte. As coberturas residenciais combinadas e os pagamentos do documento são incluídos.
- Na versão 26.10.26.2 foi usado o ícone de calculadora; ele foi substituído pela folha de cotação aprovada na revisão 26.10.26.3.

93 testes passaram no Linux com Xvfb. A nova compilação Windows ainda precisa ser executada. Nos PDFs digitalizados, OCR pode omitir ou confundir dígitos; a versão não inventa valores para completar campos ilegíveis. No Allianz escaneado de cinco opções foram recuperados 146 valores de parcelas de 150 posições; quatro permaneceram sem leitura válida. No Allianz de seis opções com texto, foram lidos os 180 planos.

## Revisão 26.10.26.3 — ícone de folha de cotação

O ícone aprovado na prévia foi convertido em PNG e ICO transparente, com tamanhos de 16, 20, 24, 32, 48, 64, 128 e 256 pixels. O desenho é uma folha de cotação com canto dobrado, cabeçalho COTAÇÃO, tabela e faixa R$. Substitui o desenho de calculadora das versões anteriores; não altera a logomarca escolhida para a arte do cliente.

A janela recebe o mesmo desenho em PNG/ICO e, no Windows, os ícones nativos pequeno e grande são aplicados à janela principal. O identificador de aplicativo e o nome do executável incluem a versão, distinguindo a distribuição dos arquivos anteriores. Crie seu atalho a partir de `PropostaSeguroAuto_26.10.26.3.exe` na pasta nova. A logomarca salva no perfil continua sendo reutilizada.

O empacotador verifica os recursos PE do executável após o PyInstaller: o grupo de ícones padrão deve conter todas as imagens do ICO fornecido. Se houver um ícone diferente, a construção não gera o ZIP de distribuição. Isso verifica o arquivo produzido no Windows, em vez de verificar somente se o ICO existe na pasta. Ao concluir, o script deve mostrar `Icone de folha de cotacao confirmado no executavel`.

104 testes passaram no Linux com tela virtual. Os testes validam os recursos esperados, rejeição de ícones antigos/diferentes, manipulação dos ícones nativos com identificadores de 64 bits e liberação dos recursos. Não foi produzido nem executado um novo binário Windows nesta máquina; a apresentação efetiva no Explorador, janela e barra de tarefas deve ser conferida na máquina Windows após construir.

## Revisão 26.10.26.4 — rolagem com o mouse

A roda do mouse rola a aba sob o ponteiro: Cliente e veículo, Opções e coberturas, Formas de pagamento e Prévia do documento. Funciona sobre os campos, rótulos e conteúdo das tabelas/prévia, sem exigir clique na barra de rolagem. **Shift + roda** move as tabelas na horizontal. Barras de rolagem continuam disponíveis.

Os eventos são encaminhados antes do comportamento padrão dos controles para evitar rolagem dupla e alterações indesejadas no campo. Movimentos pequenos da roda são acumulados. Se uma célula da tabela estiver em edição, seu valor é salvo antes de mover as linhas; a posição de rolagem é preservada durante esse salvamento. Popups e abas ocultas não recebem a rolagem da aba atual. Uma nova importação limpa o movimento parcial da roda e volta ao início de Cliente e veículo. A folha de cotação continua como ícone e a logomarca salva é preservada.

118 testes passaram, sem pulos, no Linux com Xvfb. Os novos testes exercitam movimentos reais das áreas de visualização, roda sobre campos, evento Tk da roda, ausência de rolagem dupla, entrada de alta resolução, tabelas horizontais, prévia e isolamento de janelas/abas. A compilação e a verificação com mouse físico no Windows precisam ocorrer na máquina Windows.
