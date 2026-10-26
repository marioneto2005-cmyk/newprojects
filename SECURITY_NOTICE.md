# Aviso de segurança — versão 26.10.26.4 em análise

O Microsoft Defender de um usuário bloqueou o ZIP de código e empacotador com a detecção `Trojan:Script/Ulthar.A!ml`. O usuário informou que apenas baixou o arquivo, sem executar o script ou o aplicativo. A captura indicava status Removido.

**Mantenha o bloqueio. Não restaure o arquivo nem configure exclusões para continuar a construção. Esta versão não deve ser recomendada para execução até a avaliação da detecção.**

## Identificação do artefato

- Arquivo: `Proposta_Seguro_Auto_26.10.26.4_Codigo_e_Empacotador.zip`
- Tamanho: 848326 bytes.
- SHA-256: `57ac31414f181b637aa7d60da64427fad8aaa342160cde2efe093e296b343d6c`
- Commit que publicou o pacote: `82d2d1eddd761153a60c0a77366abc0ced93a0c1`.
- Repositório/branch: `marioneto2005-cmyk/newprojects`, `credplus-local-v0.1`, pasta `entregas`.

## Verificações realizadas

O ZIP obtido do endereço público foi comparado byte a byte com o pacote local e correspondeu integralmente. A integridade ZIP e o manifesto SHA-256 dos 51 arquivos foram conferidos; os fontes coincidem com os do projeto. Esse pacote contém código-fonte e um script PowerShell de construção; não contém executáveis EXE ou DLL. Isso não torna scripts ou arquivos de dados automaticamente seguros.

Os caminhos de execução revisados incluem instalação de dependências por pip no script de construção, execução de testes/PyInstaller, consulta do OCR, abertura local do PDF e APIs de ícone do Windows. A inspeção não estabelece uma varredura antimalware nem determina o componente que acionou o Defender. Os testes funcionais anteriores não certificam ausência de malware.

## Limitações e próximo passo

Este ambiente de revisão é Linux e não dispõe de Microsoft Defender para reproduzir a detecção. O veredicto continua **não determinado**; não foi confirmado falso positivo nem comprometimento do computador. Não foram enviados arquivos a serviços externos de análise.

A TI ou a Microsoft deve avaliar o artefato identificado pelo hash, a detecção e o histórico do Defender antes de qualquer liberação. Portal oficial de submissão/análise: https://www.microsoft.com/en-us/wdsi/filesubmission . O usuário não precisa restaurar a cópia removida para encaminhar estas informações à TI. Não será distribuída uma variante renomeada, ofuscada ou com controles desativados para contornar o bloqueio.
