"""Multi-option local proposal model. Only explicit source amounts are carried forward."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import json,re
from .rule_engine import extract,norm,MONEY
from .core import ASSETS,FIELD_MAP,format_value,read_pdf_text

CORRETORAS=('Aliro','Allianz','Azul','HDI','Mapfre','Tokio Marine','Yelum','Zurich')
COVER_KEYS=('casco','dm','dc','morais','appm','appi','appg','defesa','vidros','assistencia','reserva','franquia','tipofranquia','isencao_terceiro','desconto_despesas','reserva_terceiro','garantia_zero','martelinho','pintura','assistencia_casa','objetos')
GLASS_KEYS=('parabrisa','laterais','traseiro','farol','farolled','lanterna','lanternaled','retrovisor','auxiliar','lanternaaux','maquinavidros','retrovisorinterno','pelicula','farolmatrix','pequenos_reparos','parachoque','retrovisorled')
NUM=re.compile(r'(?<![\d.,])'+MONEY+r'(?![\d.,])')

def amounts(s):return NUM.findall(s)
def compact(s):return re.sub(r'\s+',' ',s).strip()
def money_float(s):return float(s.replace('.','').replace(',','.'))

@dataclass
class Offer:
    name:str
    values:dict=field(default_factory=dict)

@dataclass
class Payment:
    offer:str
    mode:str
    installments:int
    amount:str
    entry:str=''
    total:str=''
    interest:str=''
    condition:str=''
    last:str=''
    schedule:list[str]=field(default_factory=list)

@dataclass
class Proposal:
    corretora:str
    values:dict=field(default_factory=dict)
    offers:list[Offer]=field(default_factory=list)
    payments:list[Payment]=field(default_factory=list)
    notes:list[str]=field(default_factory=list)
    pages:int=0
    methods:list[str]=field(default_factory=list)
    diagnostics:list[str]=field(default_factory=list)

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)

def display(key,value):
    if value is None:return ''
    if key in FIELD_MAP:
        try:return format_value(FIELD_MAP[key],value)
        except ValueError:return ''
    if (key=='defesa' or key in GLASS_KEYS) and isinstance(value,(int,float)):
        return f'{value:,.2f}'.replace(',','_').replace('.',',').replace('_','.')
    return str(value)

def assign(target,key,value):
    value=display(key,value)
    if value!='':target[key]=value

def read_match(text,pattern,flags=re.I|re.M):
    matches=list(re.finditer(pattern,text,flags))
    values=[m[1].strip() for m in matches]
    return values[0] if values and len(set(values))==1 else ''

def same_line_amount(lines,label,index=0):
    found=[]
    for line in lines:
        if re.search(label,line,re.I):
            nums=amounts(line)
            if len(nums)>index:found.append(nums[index])
    return found[0] if found and len(set(found))==1 else ''

def _table_values(header,rows,columns):
    """Read cells by their printed header positions, including wrapped rows."""
    positions=[]
    for key,label in columns:
        m=re.search(label,header,re.I)
        if m:positions.append((m.start(),key))
    positions.sort();result={}
    for i,(start,key) in enumerate(positions):
        end=positions[i+1][0]-2 if i+1<len(positions) else None
        for row in rows:
            value=row[max(0,start-2):end].strip()
            if value:result[key]=value;break
    return result


def resolve_driver_identity(values):
    """Reuse an ID only for the same named person or an explicit own-insured indicator."""
    insured=compact(norm(str(values.get('nome','')))).casefold()
    driver=compact(norm(str(values.get('condutor','')))).casefold()
    own={'proprio segurado','o proprio segurado','a propria segurada','propria segurada',
         'proprio proponente','o proprio proponente','proponente','proprio(a) segurado(a)'}
    if driver in own and insured:
        values['condutor']=values['nome'];driver=insured
    if insured and driver==insured and not values.get('cpfcond') and values.get('cpf'):
        assign(values,'cpfcond',values['cpf'])
    return values


def common_fields(text,company):
    rules=json.loads((ASSETS/'regras.json').read_text(encoding='utf-8'))
    legacy_company='Yelum' if company=='Aliro' else company
    raw=extract(text,legacy_company,1,rules,corrected=True)
    common={k:display(k,v.get('value')) for k,v in raw.items() if k in FIELD_MAP and v.get('value') is not None}
    common={k:v for k,v in common.items() if v}
    t=norm(text)
    # Explicit anchored label fallbacks; never infer another person's ID from the insured's ID.
    patterns={
      'nome':[r'^Nome completo/Razao social:\s*([^\n]+)',r'^Nome do Segurado\s*:\s*([^\n]+)'],
      'condutor':[r'^Condutor principal:\s*([^\n]+)'],
      'modelo':[r'^Veiculo:\s*(.+?)(?= {2,}Ano|$)'],
    }
    for key,choices in patterns.items():
        if common.get(key):continue
        for pattern in choices:
            value=read_match(t,pattern)
            if value:assign(common,key,re.split(r' {2,}',value)[0]);break
    if company=='Azul':
        lines=t.splitlines()
        def following(header):
            for i,line in enumerate(lines):
                if re.search(header,line.lstrip()):
                    return next((l for l in lines[i+1:i+4] if l.strip()),'')
            return ''
        for key,header in [('nome',r'^Segurado\(a\) +Nascimento +CPF'),('condutor',r'^Condutor +Nascimento +CPF')]:
            row=following(header);m=re.match(r'\s*(.+?) {2,}\d{2}/\d{2}/\d{4} {2,}([\d./-]+)',row)
            if m:assign(common,key,m[1]);assign(common,'cpf' if key=='nome' else 'cpfcond',m[2])
        row=following(r'^Placa +Chassi +Veiculo +Ano')
        m=re.match(r'\s*(\S+) +(\S+) +(.+?) {2,}(\d{4} */ *\d{4})',row)
        if m:
            for k,v in zip(['placa','chassi','modelo','ano'],m.groups()):assign(common,k,v)
        row=following(r'^Tipo de uso +CEP de pernoite')
        m=re.match(r'\s*(.+?) {2,}([\d-]{8,9})',row)
        if m:assign(common,'uso',m[1]);assign(common,'cep',m[2])
        row=following(r'^Combustivel +Categoria');assign(common,'combustivel',re.split(r' {2,}',row.strip())[0])
        m=re.search(r'(\d{2}/\d{2}/\d{4}) ate (\d{2}/\d{2}/\d{4})',t)
        if m:assign(common,'inicio',m[1]);assign(common,'fim',m[2])
    if company=='Mapfre':
        for i,line in enumerate(t.splitlines()):
            if re.match(r'^Segurado: +CPF/CNPJ:',line):
                row=next((s for s in t.splitlines()[i+1:i+4] if s.strip()),'')
                m=re.match(r'\s*(.+?) {2,}([\d./-]+)',row)
                if m:assign(common,'nome',m[1]);assign(common,'cpf',m[2])
        for key,pattern in {
          'nome':r'^Nome:\s*(.+?)(?= {2,}|$)',
          'cpf':r'CPF/CNPJ:\s*([\d./-]+)',
          'modelo':r'^Veiculo:\s*(.+?)(?= {2,}|$)',
          'condutor':r'^- Nome do Principal +([^\n]+)',
          'uso':r'^Uso:\s*([^\n]+?)(?= {2,}|$)',
          'ano':r'^Ano Modelo: *([\d/]+)',
          'zero':r'0Km: *([^\n]+?)(?= {2,}|$)',
          'placa':r'Placa:\s*(\S+)', 'chassi':r'Chassi:\s*([A-Z0-9]+)',
          'ano':r'^Ano Modelo: *([\d/]+)',
          'cep':r'CEP de pernoite(?: do veiculo)?:\s*([\d-]+)',
        }.items():
            v=read_match(t,pattern)
            if v:assign(common,key,v)
    if company=='Tokio Marine':
        lines=t.splitlines()
        for i,line in enumerate(lines):
            if re.match(r'^\s*Proponente +CPF/CNPJ',line):
                cells=_table_values(line,lines[i+1:i+4],[('nome',r'\bProponente\b'),('cpf',r'CPF/CNPJ:?'),('condutor',r'Principal Condutor'),('_civil',r'Estado Civil')])
                for key in ('nome','cpf','condutor'):
                    if cells.get(key):assign(common,key,cells[key])
            if re.match(r'^\s*Tipo Seguro +Vigencia',line):
                cells=_table_values(line,lines[i+1:i+2],[('_tipo',r'Tipo Seguro'),('_vigencia',r'Vigencia'),('_decodificado',r'Chassi decodificado'),('placa',r'\bPlaca\b'),('chassi',r'\bChassi\b(?! +decodificado)'),('ano',r'Ano modelo')])
                for key in ('placa','chassi','ano'):
                    if cells.get(key):assign(common,key,cells[key])
                m=re.fullmatch(r'(\d{2}/\d{2}/\d{4}) *- *(\d{2}/\d{2}/\d{4})',cells.get('_vigencia',''))
                if m:assign(common,'inicio',m[1]);assign(common,'fim',m[2])
            if re.match(r'^\s*Fabricante +Veiculo',line):
                cells=_table_values(line,lines[i+1:i+2],[('_marca',r'Fabricante'),('modelo',r'Veiculo')])
                model=cells.get('modelo','');brand=cells.get('_marca','')
                if model:assign(common,'modelo',brand+' - '+model if brand and not norm(model).startswith(norm(brand)) else model)
            if re.match(r'^\s*Combustivel +Lotacao',line):
                cells=_table_values(line,lines[i+1:i+2],[('combustivel',r'Combustivel'),('_lotacao',r'Lotacao'),('zero',r'Zero KM'),('_fipe',r'Codigo FIPE')])
                for key in ('combustivel','zero'):
                    if cells.get(key):assign(common,key,cells[key])
            if re.match(r'^\s*Tipo de utilizacao',line):
                cells=_table_values(line,lines[i+1:i+2],[('uso',r'Tipo de utilizacao'),('_dispositivo',r'Dispositivo'),('_data',r'Data saida')])
                if cells.get('uso'):assign(common,'uso',cells['uso'])
            if re.match(r'^\s*CEP de pernoite\s*$',line):
                for row in lines[i+1:i+4]:
                    m=re.fullmatch(r'\s*(\d{5}-?\d{3}) +([Ss]im|[Nn]ao) *',row)
                    if m:assign(common,'cep',m[1]);assign(common,'garagem',m[2])
    if company=='Yelum':
        lines=t.splitlines()
        for i,line in enumerate(lines):
            if re.search(r'CEP de Pernoite +Tipo de Franquia',line,re.I):
                cells=_table_values(line,lines[i+1:i+2],[('_capacidade',r'Capacidade'),('_categoria',r'Categoria'),('_regiao',r'Reg\. de Tarif\.'),('cep',r'CEP de Pernoite'),('_franquia',r'Tipo de Franquia')])
                if re.fullmatch(r'\d{5}(?:-?\d{3})?',cells.get('cep','')):assign(common,'cep',cells['cep'])
    if company=='Aliro':
        # Aliro/Liberty headers differ from Yelum: table values are immediately after labels.
        lines=t.splitlines()
        for i,line in enumerate(lines):
            if re.match(r'^Nome do\(a\) Segurado\(a\) +CPF',line):
                row=next((s for s in lines[i+1:i+4] if s.strip()),'')
                m=re.match(r'\s*(.+?) {2,}([\d./-]+)',row)
                if m:assign(common,'nome',m[1]);assign(common,'cpf',m[2])
        for i,line in enumerate(lines):
            if re.match(r'^Codigo FIPE +Marca/Tipo do Veiculo',line):
                row=lines[i+1] if i+1<len(lines) else ''
                parts=re.split(r' {2,}',row.strip())
                if len(parts)>=3:assign(common,'modelo',parts[1]);assign(common,'ano',parts[2])
            if re.match(r'^Chassi +Placa +Capacidade',line):
                parts=re.split(r' {2,}',lines[i+1].strip())
                if len(parts)>=2:assign(common,'chassi',parts[0]);assign(common,'placa',parts[1])
        m=re.search(r'Das 24:00hs de (\d{2}/\d{2}/\d{4}) as 24:00hs de (\d{2}/\d{2}/\d{4})',t)
        if m:assign(common,'inicio',m[1]);assign(common,'fim',m[2])
    return resolve_driver_identity(common)


def allianz(text,p):
    lines=norm(text).splitlines()
    header=re.compile(r'^\s*(Roubo e Furto\s*\*? +Basico +Ampliado|Basico +Ampliado +Completo|Completo +Master +Exclusivo|Master +Exclusivo)\s*$')
    group=None;order=[];offers={}
    for i,line in enumerate(lines):
        h=header.match(line)
        if h:
            names=re.split(r' {2,}',h[1].strip())
            if len(names)<2:names=re.findall(r'Roubo e Furto\s*\*?|Basico|Ampliado|Completo|Master|Exclusivo',h[1])
            group=[{'Basico':'Básico'}.get(n.strip().rstrip('*').strip(),n.strip().rstrip('*').strip()) for n in names]
            for name in group:
                if name not in offers:offers[name]=Offer(name);order.append(name)
            continue
        if not group:continue
        if 'OUTRAS FORMAS DE PAGAMENTO' in line:group=None;continue
        n=len(group);nums=amounts(line)
        labels={'dm':r'^RCF\*\* - Danos Materiais','dc':r'^RCF\*\* - Danos Corporais',
                'morais':r'^RCF\*\* - Danos Morais e Esteticos','appm':r'^APP\*\*\* - Morte',
                'appi':r'^APP\*\*\* - Invalidez Permanente','defesa':r'^RCF\*\* - Gastos com Defesa'}
        for key,label in labels.items():
            if re.search(label,line.strip()) and len(nums)==n*2:
                for j,name in enumerate(group):assign(offers[name].values,key,money_float(nums[j*2]))
        if re.match(r'^\s*Preco Total\s',line) and len(nums)==n:
            for j,name in enumerate(group):assign(offers[name].values,'total',money_float(nums[j]))
        for key,label,pattern in [('casco','',r'\d+% FIPE'),('assistencia',r'^Guincho',r'(?:Km Livre|\d+ Km)'),('reserva',r'^Carro Reserva',r'\d+ Dias')]:
            if label and not re.search(label,line.strip()):continue
            vals=re.findall(pattern,line,re.I)
            if len(vals)==n:
                for name,value in zip(group,vals):assign(offers[name].values,key,value)
    p.offers=[offers[n] for n in order]
    mode=''
    for line in lines:
        for key in ['Boleto Bancario','Debito em Conta','Cartao de Credito']:
            if key.lower() in line.lower() and 'Oferta' in line:mode={'Boleto Bancario':'Boleto','Debito em Conta':'Débito em conta','Cartao de Credito':'Cartão de crédito'}[key]
        m=re.match(r'^\s*(\d{1,2}) +(sem juros|[\d.,]+%) +(.+)$',line,re.I)
        if mode and m:
            nums=amounts(m[3])
            if len(nums)==len(p.offers):
                for name,amount in zip(order,nums):p.payments.append(Payment(name,mode,int(m[1]),amount,interest=m[2]))
    if any('Roubo e Furto' in name for name in order):
        p.notes.append('Roubo e Furto: cobertura restrita a roubo, furto e incêndio total; não cobre colisão nem perda parcial nesses eventos.')
    for offer in p.offers:
        printed={r.amount for r in p.payments if r.offer==offer.name and r.installments==1}
        if printed and offer.values.get('total') not in printed:
            p.notes.append(f'{offer.name}: prêmio de cobertura R$ {offer.values.get("total", "")}; pagamento à vista R$ {", ".join(sorted(printed))} conforme tabela de pagamento.')


def dual_options(text,p):
    t=norm(text);lines=t.splitlines();company=p.corretora
    names=['Valor de mercado (FIPE)','Valor determinado'] if company=='HDI' else ['Auto','Auto Clássico']
    rules=json.loads((ASSETS/'regras.json').read_text(encoding='utf-8'))
    p.offers=[]
    for i,name in enumerate(names,1):
        raw=extract(text,company,i,rules,corrected=True)
        vals={k:display(k,v.get('value')) for k,v in raw.items() if k in (*COVER_KEYS,*GLASS_KEYS,'total') and v.get('value') is not None}
        vals={k:v for k,v in vals.items() if v};p.offers.append(Offer(name,vals))
    # Tables carry two LMI/premium pairs; use complete rows only.
    for line in lines:
        labels={'dm':r'RCF-V[ -]+DANOS MATERIAIS','dc':r'RCF-V[ -]+DANOS CORPORAIS',
                'morais':r'(?:RCF-V[ -]+)?DANOS MORAIS','appm':r'APP[ -]+MORTE','appi':r'APP[ -]+INVALIDEZ'}
        nums=amounts(line)
        for key,label in labels.items():
            if re.match(r'^\s*'+label,line,re.I) and len(nums)==4:
                for j,offer in enumerate(p.offers):assign(offer.values,key,money_float(nums[j*2]))
        if company=='HDI' and re.match(r'^\s*CASCO +',line) and len(nums)==5:
            # First amount is the FIPE percentage, followed by premium and determined LMI.
            assign(p.offers[0].values,'casco',nums[0]+'% FIPE')
            assign(p.offers[1].values,'casco','R$ '+nums[2]+' (valor determinado)')
            for offer in p.offers:assign(offer.values,'franquia',money_float(nums[-1]))
        if company=='HDI' and re.match(r'^\s*TOTAL A VISTA',line) and len(nums)==2:
            for offer,value in zip(p.offers,nums):assign(offer.values,'total',money_float(value))
    if company=='HDI':
        if re.search(r'Guincho Sem Limite de KM para sinistro',t,re.I):
            for offer in p.offers:assign(offer.values,'assistencia','Assistência 24h; guincho sem limite de km para sinistro')
        for key,label in [('maquinavidros','Maquina de Vidros'),('farolmatrix','Farol Matrix'),('retrovisorled','Retrovisor Led')]:
            m=re.search(label+r' com franquia de R\$ *('+MONEY+r')',t,re.I)
            if m:
                for offer in p.offers:assign(offer.values,key,money_float(m[1]))
    else:
        labels={'Possivel isencao de franquia parcial quando o segurado nao for culpado pelo sinistro':'isencao_terceiro',
                'Desconto na franquia parcial contratando despesas extras':'desconto_despesas',
                'Carro reserva quando o segurado for terceiro em outra seguradora':'reserva_terceiro',
                'Garantia padrao de Zero Km':'garantia_zero','Vidros':'vidros',
                'Martelinho e para-choque':'martelinho','Lataria e pintura':'pintura','Carro reserva':'reserva',
                'Assistencia 24 horas':'assistencia'}
        for line in lines:
            parts=re.split(r' {2,}',line.strip())
            if len(parts)<3:continue
            if parts[0] in labels:
                values=[parts[1],parts[3]] if len(parts)==5 else parts[1:3]
                for offer,value in zip(p.offers,values):assign(offer.values,labels[parts[0]],value)
            if parts[0]=='Km adicional de reboque' and len(parts)==5:
                for offer,value in zip(p.offers,[parts[1],parts[3]]):
                    current=offer.values.get('assistencia','')
                    assign(offer.values,'assistencia',current+('; ' if current else '')+'reboque '+value)
    if company=='HDI':
        section=t.split('Parcelamento Vlr. Mercado Referenciado')[-1].split('OUTRAS INFORMACOES')[0]
        anchors=[]
        for line in section.splitlines()[:8]:anchors += [m.start() for m in re.finditer(r'Plano',line)]
        anchors=sorted(set(anchors))
        if len(anchors)==6:
            for line in section.splitlines():
                for m in re.finditer(r'(\d{1,2})\s*x\s*('+MONEY+r')',line):
                    j=min(range(6),key=lambda k:abs(anchors[k]-m.start()))
                    if abs(anchors[j]-m.start())>8:continue
                    p.payments.append(Payment(names[j//3],['Cartão de crédito','Débito em conta','Carnê'][j%3],int(m[1]),m[2]))
    else:
        mode=''
        for line in lines:
            if re.match(r'^\s*Debito/ +Auto',line):mode='Débito / Pix automático'
            elif re.match(r'^\s*Ficha +Auto',line):mode='Ficha / boleto'
            elif re.match(r'^\s*Cartao +Auto',line):mode='Cartão de crédito'
            m=re.match(r'^\s*(\d{1,2}) +(.+)$',line)
            if mode and m:
                cells=re.findall(r'('+MONEY+r') +(Sem Juros|'+MONEY+r') +('+MONEY+r')',m[2],re.I)
                if len(cells)==2:
                    for name,(amount,interest,total) in zip(names,cells):p.payments.append(Payment(name,mode,int(m[1]),amount,total=total,interest=interest if interest.lower()=='sem juros' else interest+'%'))
        for offer in p.offers:
            totals={r.total for r in p.payments if r.offer==offer.name and r.installments==1 and r.total}
            if len(totals)==1:assign(offer.values,'total',money_float(next(iter(totals))))


def single_offer(text,p):
    t=norm(text);lines=t.splitlines();company=p.corretora;vals={k:v for k,v in p.values.items() if k in (*COVER_KEYS,*GLASS_KEYS,'total')}
    name={'Azul':'Azul Compacto','Mapfre':'Auto','Aliro':'Affinity Auto','Yelum':'Auto','Zurich':'Automóvel'}[company]
    offer=Offer(name,vals);p.offers=[offer]
    if company in ('Aliro','Yelum'):
        for i,line in enumerate(lines):
            if 'DEMONSTRATIVO DE PREMIO' in line:
                block='\n'.join(lines[i+1:i+6]);rows=[amounts(s) for s in block.splitlines() if len(amounts(s))>=5]
                if rows:
                    # Full Aliro: six values; Yelum omits the empty surcharge column.
                    nums=rows[0];assign(vals,'total',money_float(nums[-2]))
                break

        for i,line in enumerate(lines):
            if re.match(r'^BASICA - 01-COMPREENSIVA',line.strip()):
                nums=amounts(line)
                if nums:assign(vals,'franquia',money_float(nums[-1]))
                m=re.search(r'VMR(?: FIPE)? x *(\d+%)',line)
                if m:assign(vals,'casco',m[1]+' FIPE')
            for key,label in [('dm','DANOS MATERIAIS'),('dc','DANOS CORPORAIS'),('morais','DANOS MORAIS')]:
                if 'RESP CIVIL' in line and label in line and amounts(line):assign(vals,key,money_float(amounts(line)[0]))
            if 'ACIDENTES PESSOAIS PASSAGEIROS' in line:
                label=line+' '+(' '.join(lines[i+1:i+3]));nums=amounts(line)
                if nums:
                    if 'INVALIDEZ' in label:assign(vals,'appi',money_float(nums[0]))
                    elif 'MORTE' in label:assign(vals,'appm',money_float(nums[0]))
        if company=='Yelum':
            section=t.split('FORMA DE PAGAMENTO:')[-1].split('DADOS DO VEICULO')[0]
            for line in section.splitlines():
                m=re.match(r'^\s*(A vista|1 *\+ *\d+) +(.+)$',line,re.I)
                if not m:continue
                nums=amounts(m[2])
                if len(nums)==2:
                    n=1 if 'vista' in m[1].lower() else 1+int(re.search(r'\d+$',m[1])[0])
                    for mode,amount in zip(['Débito em conta','Cartão de crédito'],nums):p.payments.append(Payment(name,mode,n,amount))
        else:
            # An existing policy: carry only the printed schedule, without bank account details.
            section=t.split('FORMA DE PAGAMENTO')[-1].split('ATENCAO:')[0]
            n=read_match(section,r'^\s*(\d{1,2})\s*$')
            schedule={}
            for line in section.splitlines():
                m=re.search(r'(?:^| )0{2,3}(\d{1,2}) +',line)
                if m and re.search(r'\d{2}/\d{2}/\d{4}',line):
                    nums=amounts(line)
                    if nums:schedule[int(m[1])]=nums[-1]
            if n and len(schedule)==int(n) and set(schedule)==set(range(1,int(n)+1)):
                seq=[schedule[j] for j in range(1,int(n)+1)]
                p.payments.append(Payment(name,'Débito em conta (plano do documento)',int(n),seq[1] if len(seq)>1 else seq[0],entry=seq[0],total=vals.get('total',''),last=seq[-1],schedule=seq))
    elif company=='Zurich':
        for line in lines:
            m=re.match(r'^\s*(01(?: *\+ *\d{2})?) +(.+)$',line)
            if not m:continue
            nums=amounts(m[2])
            if len(nums)==3:
                n=1+int(m[1].split('+')[-1]) if '+' in m[1] else 1
                p.payments.append(Payment(name,'Parcelamento do documento',n,nums[1] if n>1 else nums[0],entry=nums[0] if n>1 else '',total=nums[2]))
        totals={r.total for r in p.payments if r.total}
        if len(totals)==1:assign(vals,'total',money_float(next(iter(totals))))
        for key,label in [('dm','RCV - Danos Materiais'),('dc','RCV - Danos Corporais'),('morais','RCV - Danos Morais'),('appg','APP - Acidentes Pessoais')]:
            value=same_line_amount(lines,label)
            if value:assign(vals,key,money_float(value))
        for key,label in [('maquinavidros','Maquina de Vidros'),('retrovisorinterno','Retrovisor Interno'),('pelicula','Pelicula'),('farolmatrix','Farol Matrix'),('pequenos_reparos','Pequenos Reparos Premium'),('parachoque','Pequenos Reparos Premium - Troca de Para-Choque')]:
            m=re.search(r'^ *'+label+r' +('+MONEY+r') *$',t,re.M)
            if m:assign(vals,key,money_float(m[1]))
        v=same_line_amount(lines,r'^Cobertura Especial para Vidros')
        if v:assign(vals,'vidros','LMG R$ '+v)
    elif company=='Mapfre':
        section=t.split('Coberturas')[-1].split('Formas de Pagamento')[0]
        labels={'dm':r'^RCFA - Danos Materiais','dc':r'^RCFA - Danos Corporais','morais':r'^RCFA - Danos Morais','appm':r'^APP - Morte','appi':r'^APP - Invalidez','franquia':r'^Casco:','parabrisa':r'^Para-brisa','laterais':r'^Vidros Laterais','traseiro':r'^Traseiro'}
        for key,label in labels.items():
            v=same_line_amount(section.splitlines(),label)
            if v:assign(vals,key,money_float(v))
        m=re.search(r'^Casco -[^\n]+?(\d+% FIPE)',section,re.M)
        if m:assign(vals,'casco',m[1])
        for line in section.splitlines():
            nums=amounts(line)
            if len(nums)==4 and re.fullmatch(r'[\d., ]+',line.strip()):assign(vals,'total',money_float(nums[-1]))
        mode_names=['Boleto','Débito em conta','Débito com primeira em boleto','Cartão de crédito']
        section=t.split('Formas de Pagamento')[-1]
        for line in section.splitlines():
            starts=list(re.finditer(r'(\d{1,2})x +(Sem Juros|Com Juros)',line,re.I))
            for j,m in enumerate(starts):
                tail=line[m.end():starts[j+1].start() if j+1<len(starts) else len(line)]
                nums=amounts(tail)
                if len(nums)!=2:continue
                # Native layout: four methods occupy distinct fixed columns, including missing 11x/12x cells.
                column=min(3,int(m.start()/40))
                p.payments.append(Payment(name,mode_names[column],int(m[1]),nums[0],total=nums[1],interest=m[2]))
        for key,label in [('vidros','Vidros - Basico'),('reserva','Carro Reserva - 7 dias - Economico com Ar'),('assistencia','Extensao de Reboque ILIMITADO')]:
            if label in t:assign(vals,key,label)
        if 'Assistencia Casa' in t:assign(vals,'assistencia_casa','Gratuita')
        if 'RCFA - Objetos Transportados pelo Veiculo' in t:assign(vals,'objetos','Gratuita')
    elif company=='Azul':
        for key,label in [('dm',r'^RCF-V Danos Materiais'),('dc',r'^RCF-V Danos Corporais'),('morais',r'^Danos Morais e Esteticos'),('appg',r'^Acidentes Pessoais Passageiros'),('defesa',r'^Custos de defesa auto')]:
            v=same_line_amount(lines,label)
            if v:assign(vals,key,money_float(v))
        m=re.search(r'^Compreensiva[^\n]*?(\d+\.\d+%)\s+R\$\s*('+MONEY+r')',t,re.M)
        if m:assign(vals,'casco',m[1]+' FIPE');assign(vals,'franquia',money_float(m[2]))
        v=same_line_amount(lines,r'Valor total')
        if v:assign(vals,'total',money_float(v))
        if 'Assistencia Gratuita - 200 Km' in t:assign(vals,'assistencia','Assistência 24h - 200 km')
        if 'Essencial 7 dias' in t:assign(vals,'reserva','Carro reserva básico - 7 dias (rede referenciada)')
        for key,label in [('parabrisa',r'Vidros \(Para-Brisa e Traseiro\)'),('traseiro',r'Vidros \(Para-Brisa e Traseiro\)'),('laterais',r'Vidros Laterais'),('farol',r'Farois/Lanternas'),('lanterna',r'Farois/Lanternas'),('retrovisor',r'Retrovisores'),('farolled',r'Farois de Xenonio'),('lanternaled',r'Lanternas de LED')]:
            m=re.search(label+r':\s*R\$\s*('+MONEY+r')',t,re.I)
            if m:assign(vals,key,money_float(m[1]))
        headers=list(re.finditer(r'^\s*(TODAS .+|1 BOLETO / .+|1 DEBITO C\. CORRENTE / .+|BOLETO)\s*$',t,re.M))
        for i,h in enumerate(headers):
            block=t[h.end():headers[i+1].start() if i+1<len(headers) else len(t)]
            mode=compact(h[1]).replace('TODAS ','')
            if mode=='BOLETO':
                m=re.search(r'R\$\s*('+MONEY+r')',block)
                if m:p.payments.append(Payment(name,'Boleto à vista',1,m[1],condition='5% de desconto, conforme documento'))
                continue
            line_nums=[]
            for line in block.splitlines():
                nums=amounts(line)
                if len(nums)>=8:line_nums=nums;break
            if not line_nums:continue
            first=2 if mode=='1 BOLETO / DEMAIS CARNE' else 1
            for n,amount in enumerate(line_nums,first):
                interest='Com juros' if ('CARNE' in mode and n>=5) else 'Sem juros'
                p.payments.append(Payment(name,mode,n,amount,interest=interest,condition='Descontos e condições específicos da modalidade'))
        p.notes.append('Azul: descontos variam conforme cartão, titularidade e modalidade. Valores de parcelas reproduzidos da tabela do documento.')


def parse_proposal(text,company,pages=0,methods=None):
    if company not in CORRETORAS:raise ValueError('Selecione uma corretora da lista.')
    p=Proposal(company,common_fields(text,company),pages=pages,methods=methods or [])
    if company=='Allianz':allianz(text,p)
    elif company in ('HDI','Tokio Marine'):dual_options(text,p)
    else:single_offer(text,p)
    # Per-option values stay in their own columns; common values never inherit one chosen option.
    for key in (*COVER_KEYS,'total'):
        p.values.pop(key,None)
    valid=[];seen=set()
    for row in p.payments:
        if not 1<=row.installments<=60 or not re.fullmatch(MONEY,row.amount):continue
        ident=(row.offer,row.mode,row.installments,row.amount,row.entry,row.total,row.interest,row.condition,row.last,tuple(row.schedule))
        if ident not in seen:seen.add(ident);valid.append(row)
    p.payments=valid
    p.offers=[o for o in p.offers if o.values or any(r.offer==o.name for r in p.payments)]
    if not p.offers:p.diagnostics.append('Nenhuma opção comercial foi identificada neste layout.')
    return p


def build_proposal(path,company,progress=None):
    text,methods=read_pdf_text(path,progress)
    return parse_proposal(text,company,len(methods),methods)
