"""Fail the build if its EXE still embeds a Python/default/previous icon."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from credplus.icon_resources import verify_executable

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--exe',required=True);p.add_argument('--ico',required=True);args=p.parse_args()
    try:
        count=verify_executable(args.exe,args.ico)
    except Exception as exc:
        print('ERRO NA VERIFICACAO DO ICONE:',str(exc),file=sys.stderr);raise SystemExit(1)
    print('Icone de folha de cotacao confirmado no executavel:',count,'tamanhos verificados.')
