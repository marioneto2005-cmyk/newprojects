# Entrega 0.2 — Credplus Local

Primeiro protótipo funcional para homologação, desenvolvido em Python. Entrega código-fonte, modelo limpo, regras de leitura, interface desktop, testes e script de empacotamento Windows. **Não inclui um executável Windows já compilado.**

## Atualização 0.2 — impressão compacta

PDF redesenhado como uma ficha A4 de quatro colunas, com as sete seções do Excel. O exemplo fictício e o cenário padrão com APP conjunta cabem em uma página. Valores longos e complementos seguem em páginas adicionais com referências, preservando todos os campos revisados. Foram executados 32 testes sem falhas ou pulos no Linux com Xvfb, incluindo o fluxo da interface até a geração de PDF e Excel. Os novos testes verificam uma página A4 no caso padrão, preservação de todos os valores, referências de complemento, fonte mínima de 7 pontos e limites horizontais da página. O exemplo foi renderizado e inspecionado visualmente. Não foi compilado um novo executável Windows neste ambiente; a atualização precisa de reconstrução na máquina Windows usada pelo usuário.

## Histórico: validação inicial de extração na versão 0.1

As cinco propostas anexadas foram abertas e processadas localmente. HDI possui texto; as outras quatro exigiram OCR local português/inglês. Resultados da primeira opção:

| Proposta | Páginas | Leitura | Campos candidatos / 44 campos padrão |
|---|---:|---|---:|
| Allianz | 6 | OCR | 33 / 44 |
| HDI | 2 | Texto com preservação de tabelas | 35 / 44 |
| Tokio Marine | 5 | OCR | 28 / 44 |
| Yelum | 2 | OCR | 35 / 44 |
| Zurich | 2 | OCR | 34 / 44 |

“Candidato” significa que há um valor para conferir; **não é uma medida de acerto**. Não foi feita conferência humana de todos os dados contra as imagens dos PDFs. Campos sem leitura ficam em branco, com conferência manual obrigatória. Há outros cinco campos manuais de complementos, totalizando 49 campos no formulário. Condições de pagamento são manuais nesta versão. Detalhes fora das regras/layouts conhecidos não são transferidos automaticamente.

Foram executados 29 testes automatizados de validação, exportação, segurança de células Excel, tabelas com múltiplas opções, limpeza de dados e interface. Todos passaram, sem testes pulados, com tela virtual Xvfb no Linux. A interface foi exercitada até a geração efetiva de PDF e XLSX. Também passaram 36 comparações numéricas contra referências das propostas já disponíveis no projeto, incluindo HDI e Tokio nas duas opções e limites de cobertura Allianz nas cinco opções. Essas comparações não substituem a revisão integral do documento final.

### Divergência de valores identificada

Na Allianz, a opção Exclusivo apresenta R$ 2.383,99 em coberturas e R$ 2.384,00 no pagamento. O leitor detectou a diferença e deixa o total sem preenchimento automático para resolução manual. Não transforma prêmio de cobertura em limite de indenização quando a tabela está danificada. Não reaproveita o cliente de um formulário anterior.

### Saídas

PDF com identidade Sicoob e seções do modelo; Excel com a primeira aba do modelo e uma aba de complemento. Os arquivos de demonstração entregues usam dados fictícios. O modelo distribuído não contém os clientes nem os contatos que estavam na planilha de exemplo. Consultor e WhatsApp começam em branco. Os PDFs de clientes e os resultados privados de extração não fazem parte do pacote.

## O que falta para a versão Windows de produção

A construção e a execução do pacote Windows não foram realizadas neste ambiente Linux. A TI precisa fornecer uma distribuição completa e autorizada de Tesseract para Windows, com português/inglês, e executar `build_windows.ps1` em Windows com Python 3.12 x64. O script constrói uma pasta portátil, com Python e bibliotecas embarcados via PyInstaller, e gera um ZIP de distribuição. Depois, a TI deve homologar execução com usuário padrão e as políticas reais de AD/AppLocker/WDAC/antivírus, assinatura e distribuição. A aplicação precisa conseguir executar o OCR filho e escrever no temporário do usuário. Não pressupõe privilégios administrativos na estação final.

Consulte README.md para instruções completas e LICENCAS.md para as condições dos componentes, incluindo a licença AGPL/comercial do PyMuPDF. O aplicativo e os testes desta entrega foram validados no Linux; não há promessa de liberação automática nas máquinas corporativas.
