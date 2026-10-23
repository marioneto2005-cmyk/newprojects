"""Only the normalized logo is persisted. Customer documents remain in memory."""
import os,tempfile
from pathlib import Path
from PIL import Image,ImageOps

def settings_dir():
    custom=os.environ.get('PROPOSTA_SETTINGS_DIR')
    if custom:return Path(custom)
    root=Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.local'/'share')
    return root/'PropostaSeguroAuto'

def saved_logo():
    p=settings_dir()/'logo.png'
    return p if p.is_file() else None

def save_logo(source):
    with Image.open(source) as im:
        if im.width*im.height>20_000_000:raise ValueError('Escolha uma logomarca de até 20 megapixels.')
        im=ImageOps.exif_transpose(im).convert('RGBA');im.thumbnail((1600,800))
        root=settings_dir();root.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(suffix='.png',dir=root);os.close(fd)
        try:im.save(tmp,format='PNG');os.replace(tmp,root/'logo.png')
        finally:Path(tmp).unlink(missing_ok=True)
    return root/'logo.png'

def remove_logo():
    p=saved_logo()
    if p:p.unlink()
