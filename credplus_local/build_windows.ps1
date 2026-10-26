param(
    [Parameter(Mandatory=$true)][string]$TesseractDir
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if ($env:OS -ne 'Windows_NT') { throw 'Execute a construção no Windows.' }
$ocr = (Resolve-Path $TesseractDir).Path
foreach ($file in @('tesseract.exe','tessdata\por.traineddata','tessdata\eng.traineddata')) {
    if (!(Test-Path (Join-Path $ocr $file))) { throw "Falta $file no OCR aprovado pela TI." }
}
# A TI deve fornecer uma distribuição legítima completa, incluindo DLLs e licenças.
$env:PYTHONDONTWRITEBYTECODE = '1'
& py -3.12 -m venv .venv-build
if ($LASTEXITCODE -ne 0) { throw 'Instale Python 3.12 x64 na máquina de construção autorizada.' }
$python = Join-Path $PSScriptRoot '.venv-build\Scripts\python.exe'
& $python -m pip install -r requirements.txt 'pyinstaller==6.16.0'
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependências verificadas via HTTPS.' }
& $python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Os testes falharam; pacote não será gerado.' }
& $python -m PyInstaller --noconfirm --clean --onedir --windowed --name PropostaSeguroAuto --add-data 'credplus/assets;credplus/assets' --add-data "$ocr;credplus/assets/ocr" --collect-all reportlab --collect-submodules pymupdf --copy-metadata PyMuPDF --copy-metadata openpyxl --copy-metadata reportlab --copy-metadata pillow --copy-metadata et-xmlfile run_app.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao empacotar.' }
Copy-Item 'README.md' 'dist\PropostaSeguroAuto\LEIA-ME.md'
Copy-Item 'PRIVACIDADE.md' 'dist\PropostaSeguroAuto\PRIVACIDADE.md'
Copy-Item 'LICENCAS.md' 'dist\PropostaSeguroAuto\LICENCAS.md'
& 'dist\PropostaSeguroAuto\_internal\credplus\assets\ocr\tesseract.exe' --version
if ($LASTEXITCODE -ne 0) { throw 'O runtime OCR empacotado não inicia. Verifique DLLs da distribuição aprovada.' }
Compress-Archive -Path 'dist\PropostaSeguroAuto' -DestinationPath 'dist\PropostaSeguroAuto-26.10.26.1-Windows.zip' -Force
Get-FileHash 'dist\PropostaSeguroAuto-26.10.26.1-Windows.zip' -Algorithm SHA256
Write-Host 'Pacote construído. Teste em Windows com usuário padrão e solicite a liberação pela TI antes da distribuição.'
