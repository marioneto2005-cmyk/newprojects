"""Verify that the default Windows executable icon matches the shipped ICO exactly."""
import hashlib,struct


def ico_frames(data):
    if len(data)<6:raise ValueError('Arquivo ICO incompleto.')
    reserved,kind,count=struct.unpack_from('<HHH',data)
    if reserved!=0 or kind!=1 or not count or len(data)<6+16*count:raise ValueError('Cabeçalho ICO inválido.')
    result=[]
    for i in range(count):
        w,h,colors,zero,planes,bits,size,offset=struct.unpack_from('<BBBBHHII',data,6+i*16)
        if size==0 or offset<6+16*count or offset+size>len(data):raise ValueError('Imagem ICO incompleta.')
        result.append({'width':w or 256,'height':h or 256,'data':data[offset:offset+size]})
    return result


def verify_default_icon(expected_ico,group_data,icons):
    frames=ico_frames(expected_ico)
    if len(group_data)<6:raise ValueError('O executável não contém um grupo de ícones válido.')
    reserved,kind,count=struct.unpack_from('<HHH',group_data)
    if reserved!=0 or kind!=1 or count!=len(frames) or len(group_data)<6+14*count:raise ValueError('O ícone padrão do executável não corresponde ao ícone da proposta.')
    embedded=[]
    for i in range(count):
        w,h,colors,zero,planes,bits,size,ident=struct.unpack_from('<BBBBHHIH',group_data,6+i*14)
        choices=icons.get(ident,[])
        if isinstance(choices,bytes):choices=[choices]
        if not choices:raise ValueError('Falta uma imagem do ícone no executável.')
        embedded.append((w or 256,h or 256,size,{hashlib.sha256(b).digest() for b in choices if len(b)==size}))
    for frame in frames:
        digest=hashlib.sha256(frame['data']).digest()
        if not any(w==frame['width'] and h==frame['height'] and size==len(frame['data']) and digest in hashes for w,h,size,hashes in embedded):
            raise ValueError('O executável contém um ícone diferente da folha de cotação. A distribuição foi interrompida.')
    return len(frames)


def verify_executable(executable,icon_path):
    from pathlib import Path
    import pefile # Installed by PyInstaller on Windows; not needed by the runtime application.
    with pefile.PE(str(executable)) as pe:
        resources=getattr(pe,'DIRECTORY_ENTRY_RESOURCE',None)
        if resources is None:raise ValueError('O executável não tem recursos de ícone.')
        icons={};groups=[]
        for entry in resources.entries:
            if entry.id not in (3,14):continue
            for item in entry.directory.entries:
                for lang in item.directory.entries:
                    value=lang.data.struct;blob=pe.get_data(value.OffsetToData,value.Size)
                    if entry.id==3:icons.setdefault(item.id,[]).append(blob)
                    else:groups.append((item.id if item.id is not None else -1,str(item.name or ''),blob))
        if not groups:raise ValueError('O executável não possui ícone padrão.')
        default_key=min((g[0],g[1]) for g in groups)
        # All language variants of the default group must match: Windows may prefer a localized one.
        selected=[g for g in groups if (g[0],g[1])==default_key]
        expected=Path(icon_path).read_bytes()
        verified=[verify_default_icon(expected,g[2],icons) for g in selected]
        return verified[0]
