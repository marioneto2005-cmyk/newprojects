# Proposta Seguro Auto - Segurado v26.10.26.4

## Alterações entregues

Interface reorganizada em painel lateral, cartões e abas; nome e versão atualizados. A importação abre uma janela de Corretora, lê automaticamente o documento e inclui todas as opções reconhecidas. Seletores antigos de origem/opção, confirmação de campos, checkbox de conferência, mensagem inferior estática e botão Excel foram removidos. Edição direta permanece disponível. Exportações PDF/PNG compartilham o mesmo desenho e omitem campos sem valor. Logomarca persistente no perfil do usuário, com seleção no canto superior direito.

## Documentos analisados

Os oito anexos anteriores contêm texto extraível; o novo PORTO e o Allianz antigo são digitalizados. Foram processados pela API completa de importação e geração, sem depender de textos ou resultados armazenados de outro cliente.

| Arquivo | Identificação | Opções | Linhas de planos de pagamento |
|---|---|---:|---:|
| ALLIANZ.pdf | Allianz | 6 | 180 |
| ALRIO.pdf | Aliro | 1 | 1 cronograma com 10 parcelas |
| AZUL.pdf | Azul | 1 | 74 |
| HDI.pdf | HDI | 2 | 64 |
| MAPFRE.pdf | Mapfre | 1 | 42 |
| TOKIO.pdf | Tokio Marine (Auto) | 1 | 34 |
| YELUM.pdf | Yelum | 1 | 22 |
| ZURICH.pdf | Zurich | 1 | 10 |
| PORTO.pdf | Porto Seguro / Azul | 1 | 54 |

Uma linha de plano liga modalidade, opção de cobertura e quantidade de parcelas; não representa uma parcela avulsa. Allianz: 6 opções × 3 modalidades × 10 quantidades. HDI: dois tipos de indenização com cartão, débito e carnê. Tokio: Auto e Auto Clássico, com diferentes juros e totais por modalidade. Mapfre mantém parcelas 11/12 apenas para cartão. Azul mantém os descontos e a ausência da primeira parcela em determinada modalidade sem deslocar colunas. Yelum inclui 11 parcelas. Zurich mantém entrada e total. Aliro preserva primeira parcela R$284,26, oito de R$284,19 e última de R$284,20, total R$2.841,98, sem copiar dados bancários.

A Allianz apresenta diferença de um centavo no Master entre coberturas (R$2.163,59) e pagamento à vista (R$2.163,60); ambos são preservados e a diferença aparece em nota. A opção Roubo e Furto mantém sua restrição a eventos cobertos, sem ser apresentada como colisão compreensiva.

## Validação

118 testes automatizados passaram, sem erros, falhas ou pulos, no Linux com Xvfb. Exercitam os oito layouts comerciais, correspondência das colunas, juros, totais, cronograma desigual, ausência de mistura entre clientes, formulário e popup, geração sem conferência, edição imediata, persistência da marca, prévia e exportação PDF/PNG. A imagem PNG foi comparada pixel a pixel com a renderização a 150 dpi da página PDF. Os oito documentos reais também geraram uma página sem campos “Não informado”, e seus valores de parcelas apareceram na saída. Exemplo e interface foram inspecionados visualmente.

Os testes não estabelecem precisão universal nem conferência humana integral de todos os dados pessoais. Layouts novos e OCR podem ter campos omitidos. A versão remove a revisão obrigatória conforme solicitado; não converte valores ausentes em estimativas.

## Página única e distribuição

A página digital tem largura A4 e altura variável para manter o conteúdo legível e completo. Uma proposta extensa não equivale a uma folha A4 física sem redução na impressão. O PNG usa a mesma página. Não há novo executável Windows compilado nesta máquina Linux: o script de construção atualizado deve ser executado no Windows. O pacote de distribuição resultante inclui Python e OCR, dispensando essas instalações nas estações finais, e mantém a necessidade de homologação nas políticas corporativas.

## Correção de construção na versão 26.10.23.2

O log recebido do usuário para 26.10.23.1 mostrou 60 testes aprovados e duas falhas de edição de células durante a simulação de Enter no Windows. O empacotamento foi interrompido corretamente. A mesma ausência de salvamento foi reproduzida em desenvolvimento ao simular a tecla sem foco no editor. O salvamento foi associado ao evento gráfico `<<CommitCellEdit>>`, utilizado por Enter e Enter numérico e exercitado pelos testes sem exigir foco da janela do sistema operacional. A perda de foco continua salvando o campo. Foram adicionados dois cenários de regressão, totalizando 64 testes aprovados no Linux com Xvfb. Nenhum teste foi pulado ou desativado. Não houve nova compilação Windows nesta máquina; o log anterior não comprova execução desta correção no Windows.

## Arte 26.10.26.1

PDF e PNG identificam a companhia como Seguradora. O título Proposta de Seguro Auto usa 16 pontos em uma única linha. O seletor da interface mantém a nomenclatura anterior; esta alteração trata da arte solicitada.

## Leitura e troca de documento 26.10.26.1

A seleção de um novo PDF limpa dados pessoais, opções, pagamentos, contatos não persistidos e a imagem anterior, retornando ao topo de Cliente e veículo antes da leitura. A logomarca permanece. A Tokio usa uma tabela com cabeçalhos Proponente / CPF/CNPJ / Principal Condutor, com linhas quebradas de estado civil; o parser agora respeita essas colunas e as tabelas separadas de veículo. A identificação explícita de próprio segurado ou a igualdade dos nomes completos permite reutilizar CPF/CNPJ somente quando o campo do condutor estiver vazio. Casos de pessoas distintas e documento explícito diferente foram testados para evitar sobrescrita indevida.

O PDF YELUM anexado imprime apenas `35595` no campo CEP de pernoite; o trecho original foi renderizado para confirmação. A saída preserva `35595 (parcial no documento)`, sem adivinhar os três dígitos restantes. CEP completo de oito dígitos também foi testado. Foram executados 81 testes sem falhas, erros ou pulos no Linux com Xvfb. Os oito PDFs foram reprocessados, preservando as 461 associações de planos de pagamento e uma página por saída; os campos de identidade/veículo da Tokio e o CEP parcial da Yelum foram verificados nos anexos reais. Não houve nova compilação Windows neste ambiente.

## Endereços, Allianz, Tokio, Porto e ícone — 26.10.26.2

Endereços e CEPs são destacados com marca-texto amarelo na própria página compartilhada por PDF e PNG. Foram testadas a leitura do bloco cadastral do segurado e a exclusão dos endereços de corretora/filial. A seção global agora se chama Franquia e Assistências.

A Allianz de seis opções fornecida contém franquia de 50% da Normal, R$3.478,14; a de cinco opções digitalizada contém R$3.213,20. O parser procura a seção de participação obrigatória em vez de extrair uma franquia de vidros. A opção Roubo e Furto não recebe a franquia de perda parcial. Os pagamentos de seis opções geram 180 planos. No arquivo antigo digitalizado, a remoção do fundo azul recuperou as três modalidades; foram lidos 146 valores de 150 posições, mantendo vazias quatro células sem leitura válida. A versão evita deslocar colunas ou completar separadores monetários por estimativa.

Na Tokio foram mantidos somente Auto e seus 34 planos; Auto Clássico foi removido do modelo e da saída. O novo PORTO.pdf tem quatro páginas sem texto extraível; foi processado localmente por OCR com configuração específica de resolução e segmentação. Identifica o produto Azul Tradicional e Proteção Combinada e indica Azul Seguros no original, sob apresentação Porto Seguro/Azul. Importa 54 planos e as coberturas residenciais de incêndio/explosão/fumaça, responsabilidade civil familiar e aluguel, sem reutilizar dados pessoais de outro arquivo.

Foi criado um ícone de calculadora em PNG e ICO com tamanhos de 16 a 256 pixels. Ele é carregado na janela e registrado no empacotador; o identificador do aplicativo para a barra de tarefas é definido antes de abrir a janela no Windows. Os arquivos e a carga do ícone na interface foram verificados, mas a compilação e a apresentação efetiva na barra de tarefas Windows não foram executadas nesta máquina Linux.

## Ícone aprovado — 26.10.26.3

Aplicado o desenho de folha de cotação aprovado pelo usuário: folha branca, canto dobrado, cabeçalho COTAÇÃO, tabela e total R$. Os mesmos pixels na imagem de 256 pixels são utilizados pelo PNG da janela e pelo ICO do executável, com versões menores para o Windows. O empacotador inclui o recurso e valida suas imagens no grupo padrão do executável com pefile. A comparação dos bytes do ICO com RT_ICON/RT_GROUP_ICON segue a forma de cópia de recursos do PyInstaller 6.16.0. Um grupo padrão errado é rejeitado mesmo que outro grupo contenha o ícone correto.

Na execução Windows, identificador versionado é definido antes de criar a janela; são configurados os ícones Tk atual/padrão e os ícones nativos pequeno/grande por WM_SETICON na janela principal, com tipos de ponteiro de 64 bits e ciclo de vida controlado dos recursos. O arquivo passa a se chamar PropostaSeguroAuto_26.10.26.3.exe.

104 testes passaram, sem pulos, no Linux com Xvfb. Incluem verificação do validador de recursos com casos de ícone antigo, imagem faltante e grupo padrão incorreto, e testes da integração nativa por simulação de API. A interface Linux carregou o PNG real. A compilação, a verificação PE de um executável real desta versão e a apresentação no Windows continuam pendentes de execução na máquina Windows do usuário. O aplicativo de propostas e a logomarca não tiveram alterações de dados nesta revisão.

## Rolagem nas abas — 26.10.26.4

Os Canvas do formulário e da prévia tinham barras, mas não recebiam automaticamente a roda quando o ponteiro estava sobre seus controles/itens. Foi adicionado encaminhamento de eventos limitado aos descendentes das quatro abas, antes dos bindings nativos dos controles. As tabelas usam o mesmo caminho sem rolagem dupla. Não há binding global de toda a aplicação; popups ficam fora desse encaminhamento. A rolagem aceita deltas da roda Windows, movimentos pequenos, eventos de botões de roda X11 e deltas macOS. Shift seleciona o eixo horizontal.

A integração salva a célula de tabela em edição antes de mover linhas, sem deixar o editor flutuando sobre outro registro. O foco e o texto dos campos do formulário são preservados ao rolar. Foram adicionados 14 cenários, totalizando 118 testes aprovados no Linux com Xvfb, sem falhas ou pulos. O evento Tk MouseWheel foi exercitado além das chamadas do roteador, verificando a mudança efetiva do viewport. O ícone, extração e exportação permanecem cobertos pela suíte existente. Não houve construção ou teste físico no Windows neste ambiente.
