# Processamento e dados locais

Não há telemetria, API externa, upload ou integração com AD. Os documentos são abertos somente para leitura; o aplicativo não envia propostas. Campos e tabelas ficam em memória e são substituídos ao importar outro documento.

A única preferência persistida é a logomarca normalizada em `%LOCALAPPDATA%\PropostaSeguroAuto\logo.png` (ou pasta equivalente no Linux). Ela permanece até ser removida ou trocada. Contatos do atendimento e dados de clientes não são salvos automaticamente. PDF/PNG gerados contêm dados pessoais e permanecem na pasta escolhida pelo usuário, sujeitos aos controles de acesso e retenção da organização.

OCR usa imagens temporárias locais que são removidas ao terminar normalmente. Encerramento forçado pode deixar resíduos `credplus-*` no temporário; exclusão comum não é apagamento forense. A TI pode aplicar limpeza e políticas de armazenamento. Não publique PDFs reais em repositórios ou logs de suporte. Os exemplos fornecidos usam identidade fictícia; as fixtures de testes são trechos comerciais sem documentos de identidade e contas de clientes.
