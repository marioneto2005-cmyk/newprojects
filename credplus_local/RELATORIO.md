# Proposta Seguro Auto - Segurado v26.10.23.1

## Alterações entregues

Interface reorganizada em painel lateral, cartões e abas; nome e versão atualizados. A importação abre uma janela de Corretora, lê automaticamente o documento e inclui todas as opções reconhecidas. Seletores antigos de origem/opção, confirmação de campos, checkbox de conferência, mensagem inferior estática e botão Excel foram removidos. Edição direta permanece disponível. Exportações PDF/PNG compartilham o mesmo desenho e omitem campos sem valor. Logomarca persistente no perfil do usuário, com seleção no canto superior direito.

## Oito PDFs analisados

Todos os oito anexos novos contêm texto extraível. Foram processados pela API completa de importação e geração, sem depender de textos ou resultados armazenados de outro cliente.

| Arquivo | Identificação | Opções | Linhas de planos de pagamento |
|---|---|---:|---:|
| ALLIANZ.pdf | Allianz | 6 | 180 |
| ALRIO.pdf | Aliro | 1 | 1 cronograma com 10 parcelas |
| AZUL.pdf | Azul | 1 | 74 |
| HDI.pdf | HDI | 2 | 64 |
| MAPFRE.pdf | Mapfre | 1 | 42 |
| TOKIO.pdf | Tokio Marine | 2 | 68 |
| YELUM.pdf | Yelum | 1 | 22 |
| ZURICH.pdf | Zurich | 1 | 10 |

Uma linha de plano liga modalidade, opção de cobertura e quantidade de parcelas; não representa uma parcela avulsa. Allianz: 6 opções × 3 modalidades × 10 quantidades. HDI: dois tipos de indenização com cartão, débito e carnê. Tokio: Auto e Auto Clássico, com diferentes juros e totais por modalidade. Mapfre mantém parcelas 11/12 apenas para cartão. Azul mantém os descontos e a ausência da primeira parcela em determinada modalidade sem deslocar colunas. Yelum inclui 11 parcelas. Zurich mantém entrada e total. Aliro preserva primeira parcela R$284,26, oito de R$284,19 e última de R$284,20, total R$2.841,98, sem copiar dados bancários.

A Allianz apresenta diferença de um centavo no Master entre coberturas (R$2.163,59) e pagamento à vista (R$2.163,60); ambos são preservados e a diferença aparece em nota. A opção Roubo e Furto mantém sua restrição a eventos cobertos, sem ser apresentada como colisão compreensiva.

## Validação

62 testes automatizados passaram, sem erros, falhas ou pulos, no Linux com Xvfb. Exercitam os oito layouts comerciais, correspondência das colunas, juros, totais, cronograma desigual, ausência de mistura entre clientes, formulário e popup, geração sem conferência, edição imediata, persistência da marca, prévia e exportação PDF/PNG. A imagem PNG foi comparada pixel a pixel com a renderização a 150 dpi da página PDF. Os oito documentos reais também geraram uma página sem campos “Não informado”, e seus valores de parcelas apareceram na saída. Exemplo e interface foram inspecionados visualmente.

Os testes não estabelecem precisão universal nem conferência humana integral de todos os dados pessoais. Layouts novos e OCR podem ter campos omitidos. A versão remove a revisão obrigatória conforme solicitado; não converte valores ausentes em estimativas.

## Página única e distribuição

A página digital tem largura A4 e altura variável para manter o conteúdo legível e completo. Uma proposta extensa não equivale a uma folha A4 física sem redução na impressão. O PNG usa a mesma página. Não há novo executável Windows compilado nesta máquina Linux: o script de construção atualizado deve ser executado no Windows. O pacote de distribuição resultante inclui Python e OCR, dispensando essas instalações nas estações finais, e mantém a necessidade de homologação nas políticas corporativas.
