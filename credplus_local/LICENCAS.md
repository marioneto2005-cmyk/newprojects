# Revisão de licenças antes da distribuição

O código reaproveita o motor de regras e as regras Credplus existentes no repositório do solicitante. Confirme direitos de uso do código, modelo e identidade Sicoob com a organização.

Dependências: PyMuPDF/MuPDF (licença AGPL v3 ou licença comercial, conforme contratação), openpyxl (MIT), ReportLab (BSD) e suas dependências transitivas. PyInstaller possui GPL com exceção para distribuição do aplicativo empacotado. Tesseract e os modelos tessdata têm licença Apache 2.0; distribuições Windows podem incluir bibliotecas com outras licenças.

A utilização de PyMuPDF requer avaliação da obrigação AGPL e/ou contratação comercial. Este pacote é um protótipo para avaliação, não uma autorização de distribuição proprietária. A TI/jurídico deve revisar as licenças e fornecer os avisos/textos exigidos de **todos** os componentes da distribuição escolhida antes de redistribuir. Não remova licenças do diretório OCR ao construir o pacote. Consulte os textos de licença das versões instaladas e a distribuição oficial do fornecedor; este arquivo não os substitui.
