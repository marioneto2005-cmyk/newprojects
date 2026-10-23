# Credplus Local — versão 0.2, protótipo para homologação

Aplicação desktop em português para preparar um resumo de seguro no padrão Sicoob do Excel fornecido. Não usa serviços externos, Excel/Office instalado, macros, conta Microsoft ou credenciais do AD. **O executável Windows ainda precisa ser construído e homologado no Windows.** O desenvolvimento e os testes de extração/exportação foram executados no Linux.

## Operação

1. Abra `CredplusLocal.exe` na pasta distribuída pela TI (mantenha toda a pasta `_internal`). Não exige instalação de Python na estação do usuário.
2. Selecione **uma proposta PDF por vez**. Escolha a seguradora de origem (uso interno) e a opção exata conforme a ordem no PDF. As opções não são uma comparação entre seguradoras. Não misture dados de clientes.
3. Clique **Ler proposta**. PDF com texto é extraído localmente; PDF escaneado usa OCR Tesseract português/inglês local. Aguarde as páginas. O programa não baixa OCR ou outros componentes em tempo de uso.
4. Abra o PDF original ao lado. Selecione cada campo, corrija o valor e clique **Confirmar valor / ausência**. Compare todos, inclusive CPF, chassi, datas, valores e colunas de coberturas. Use valores como `1.234,56` e datas `DD/MM/AAAA`. Não troque automaticamente O por 0 ou I por 1. Os campos sem leitura podem ser preenchidos manualmente. Branco significa **não informado**, e não ausência de cobertura. Não transforme APP conjunta em morte e invalidez sem evidência.
5. Preencha nome do consultor e WhatsApp se desejar; ambos começam em branco a cada abertura. Campos não localizados também devem ter sua ausência confirmada.
6. Marque a conferência final e gere PDF ou Excel. Nome do proponente, modelo e prêmio total são obrigatórios. Confira o arquivo gerado antes de enviar. O programa não envia mensagens ou documentos.

O documento contém dados pessoais, perfil, veículo, coberturas, franquias e pagamento revisados. Uma lista explícita de campos impede copiar número de cotação, número de apólice, CNPJ/endereço da seguradora e textos jurídicos integrais. A origem é usada somente para a extração e não é identificada no resumo. A identidade Sicoob é mantida. Não cole dados excluídos em campos manuais.

## Modelos e limitações

O PDF usa uma ficha compacta A4, com quatro colunas, campos lado a lado e as sete seções do Excel fornecido, mantendo a identidade Sicoob. O exemplo padrão cabe em uma página, sem depender do Excel instalado. Textos que excedem duas linhas na célula e complementos preenchidos seguem em páginas adicionais com referências na primeira página; nenhum valor revisado é cortado. Campos não informados usam uma indicação curta e uma explicação única no rodapé da ficha. O Excel mantém a primeira aba do modelo fornecido e cria `Complemento` para campos longos e campos sem espaço no original (vigência, tipo de franquia e APP conjunta). A segunda aba original, com outro cliente, foi removida. Dados e contatos de exemplo foram apagados. A etiqueta de prêmio foi corrigida para **prêmio total da opção selecionada**: não se presume desconto à vista nem parcelamento sem juros. Condições de pagamento são de preenchimento manual nesta versão. Há também cinco campos de complementos revisados para dados comerciais adicionais de segurado/condutor, perfil, veículo, coberturas e franquias fora dos espaços do modelo. Preencha esses complementos manualmente, sem copiar identificadores excluídos ou textos da seguradora; complementos vazios são omitidos do PDF.

Os PDFs escaneados podem perder ou trocar dígitos/colunas apesar de parecerem corretos. Todo valor extraído é um **candidato**, não confirmação automática. As regras atuais cobrem campos do modelo e não garantem extrair toda informação comercial de todo layout. Tabelas com múltiplos produtos, coberturas adicionais e textos fora desses campos exigem conferência no original. Uma proposta de layout desconhecido pode exigir preenchimento manual. Nenhum resultado de OCR tem garantia de exatidão. Não há IA de nuvem. PDFs protegidos precisam de cópia autorizada sem senha. Limite de 60 páginas; OCR pode levar alguns minutos.

## Construção para Windows — TI

A máquina de construção precisa de Windows x64, Python 3.12 x64 e acesso autorizado ao PyPI. As estações finais não precisam desses acessos. Não execute em modo administrador nem altere ExecutionPolicy, AppLocker, WDAC, Defender ou regras do AD para contornar bloqueios. A TI deve usar seu processo autorizado de execução de scripts, assinatura e distribuição.

Forneça uma distribuição Windows completa e aprovada de Tesseract 5, com `tesseract.exe`, DLLs, `tessdata/por.traineddata`, `tessdata/eng.traineddata` e licenças. O script não baixa executáveis OCR. O OCR de Linux foi testado com Tesseract 5.3.0; valide a distribuição Windows escolhida. Exemplo de construção, em PowerShell com política já autorizada:

```powershell
.\build_windows.ps1 -TesseractDir 'C:\FerramentasAprovadas\Tesseract-OCR'
```

Saída: `dist/CredplusLocal-Windows.zip`. Extraia a pasta completa. A TI deve revisar as licenças antes de distribuir, decidir assinatura e permitir o hash/certificado conforme suas políticas. O programa usa um processo filho Tesseract e a pasta temporária do usuário; essas capacidades também precisam estar permitidas. Não existe garantia de execução em um domínio AD sem testar suas políticas.

### Homologação necessária em Windows

- Usuário sem privilégios administrativos; sem Python, Office e conexão externa na estação final.
- Abrir a interface e cada um dos cinco PDFs de amostra autorizados; testar as opções separadamente.
- Conferir manualmente campos, seleção de produtos, CPF/chassi ambíguos, condições de pagamento e valores contra a página original.
- Corrigir campos; testar bloqueio de emissão antes da conferência e obrigatoriedade dos campos essenciais.
- Exportar PDF/Excel, abrir em leitores corporativos, conferir paginação e planilha complementar.
- Confirmar ausência de dados do cliente anterior, identificadores de cotação/apólice e identidade da seguradora.
- Testar caminho com espaços/acentos, PDF com senha, OCR ausente, pasta sem permissão de escrita, antivírus e controles de aplicação.

## Executar pelo código para desenvolvimento

```sh
python -m venv .venv
# Use o Python do ambiente virtual conforme seu sistema.
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_app.py
```

Requer Tkinter para a interface e Tesseract com português/inglês para PDFs escaneados. Opcionalmente configure `CREDPLUS_TESSERACT` com o caminho do executável e `CREDPLUS_TESSDATA` com a pasta dos idiomas. Sem OCR, o preenchimento manual permanece disponível. Dependências declaradas são apenas bibliotecas locais; a aplicação não usa rede. Os PDFs de clientes não estão incluídos neste código ou no pacote de distribuição. Os exemplos de saída usam dados fictícios.

## Atualizar da versão 0.1 para a 0.2

Feche o aplicativo e extraia o novo código em outra pasta. Na máquina Windows usada para construir, execute novamente `build_windows.ps1` com o mesmo diretório Tesseract autorizado. A versão nova só entra no programa depois da reconstrução: o executável anterior não muda automaticamente. Distribua a nova pasta completa `dist/CredplusLocal`, ou seu ZIP, para as estações de uso. Elas não precisam de Python, pip, Office ou instalação separada de Tesseract: esses componentes necessários ao processamento já acompanham o pacote gerado. A máquina de construção continua precisando de Python 3.12 e da distribuição OCR fornecida à construção. Preserve os documentos e o pacote anterior até conferir a atualização.

O PDF demonstrativo está em `exemplos/Exemplo_PDF_Compacto.pdf` e usa somente dados fictícios.
