"""Modelo de regressao das regras; NAO executa VBA nem emula Excel."""
import re,unicodedata,datetime,json
from pathlib import Path
MONEY=r'(?:[0-9]{1,3}(?:\.[0-9]{3})*|[0-9]+),[0-9]{2}'
def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFD',s.replace('\r','').replace('\xa0',' ')) if not unicodedata.combining(c))
def rx(p): return re.compile(p,re.I|re.M)
def column(t,n):
 h=rx(r'^ +(Basico +Ampliado +Completo|Master +Exclusivo)[^\n]*').finditer(t)
 headers=[m for m in h if ('Basico' in m[0])==(n<=3)]
 if len(headers)!=1:return ''
 t=t[headers[0].end():]
 end=rx(r'^ +Master +Exclusivo|\*\* RCF:').search(t)
 if end:t=t[:end.start()]
 heads=list(rx(r'^.*Coberturas +Limite[^\n]*').finditer(t))
 if len(heads)!=1:return ''
 starts=[m.start()-4 for m in rx('Limite').finditer(heads[0][0])]
 if len(starts)!=(3 if n<=3 else 2):return ''
 k=n-1 if n<=3 else n-4; first=starts[0]; pos=starts[k]
 if first<1 or pos<1:return ''
 lines=[]
 for line in t.split('\n'):
  cell=line[pos:starts[k+1]] if k<len(starts)-1 else line[pos:]
  if rx(r'RCF\*\* - Danos|APP[*+]{2,3}').search(line[:first]):
   if not rx(r'^[ ]{0,8}[0-9][0-9.,]*[ ]').search(cell+' '):cell=' [LIMITE AUSENTE OU DESALINHADO]'
  lines.append(line[:first]+cell)
 return '\n'.join(lines)
def crop(t,start,end):
 if start.startswith('@ALLIANZ'):return column(t,int(start[-1]))
 if start:
  p=t.lower().find(start.lower())
  if p<0:return ''
  t=t[p:]
 if end:
  q=t.lower().find(end.lower(),len(start))
  if q>=0:t=t[:q]
 return t
def valid_id(id,s):
 if id in ('cpf','cpfcond'):
  n=re.sub('[. /-]','',s)
  if not re.fullmatch(r'(?:[0-9]{11}|[0-9]{14})',n) or len(set(n))==1:return False
  for j in (len(n)-1,len(n)):
   if len(n)==11: total=sum(int(n[i-1])*(j+1-i) for i in range(1,j))
   else:
    weights=[2+i%8 for i in range(j-1)]
    total=sum(int(c)*w for c,w in zip(n[:j-1][::-1],weights))
   d=11-total%11;d=0 if d>9 else d
   if d!=int(n[j-1]):return False
  return True
 if id=='cep':return bool(re.fullmatch('[0-9]{8}',s.replace(' ','').replace('-','')))
 if id=='placa':return bool(re.fullmatch('[A-Z]{3}[0-9][A-Z0-9][0-9]{2}',s.replace('-',''),re.I))
 if id=='chassi':return bool(re.fullmatch('[A-HJ-NPR-Z0-9]{17}',s,re.I))
 return True
def extract(text,insurer,offer,rules,corrected=False):
 t=norm(text); result={}
 for rule in rules:
  seg,id,start,end,pattern,group,kind,num=rule
  if seg!=insurer or str(num) not in ('*',str(offer)):continue
  chunk=crop(t,start,end); matches=list(rx(pattern).finditer(chunk))
  if not matches:continue
  vals=[m[int(group)] .strip() for m in matches]; value=vals[0]
  ev=matches[0][0];state='Revisar'
  if len(set(vals))>1:value=None;state='Leitura ambigua'
  elif kind=='N':
   if not re.fullmatch(MONEY,value):value=None;state='Leitura ambigua'
   else:value=float(value.replace('.','').replace(',','.'))
  elif kind=='D':
   try:value=datetime.datetime.strptime(value,'%d/%m/%Y').date().isoformat()
   except ValueError:value=None;state='Leitura ambigua'
  elif id=='jovens' and len(matches[0].groups())>1:value=ev
  if value is not None and not valid_id(id,str(value)):value=None;state='Leitura ambigua'
  if id=='cep' and value:value=value.replace(' ','').replace('-','')
  if corrected and id in result and result[id]['value']!=value:
   value=None;state='Leitura ambigua'
  result[id]={'value':value,'state':state,'evidence':ev}
 if corrected and insurer=='Zurich':
  glass=crop(t,'Maquina de Vidros','Clausulas')
  if rx(r'^ +[0-9][0-9.,]*\s*$').search(glass) or any(not rx(r'^ *'+label+r' +'+MONEY+r' *$').search(glass) for label in ['Vidro Traseiro','Lanterna Convencional']):
   for id in ['parabrisa','laterais','traseiro','farol','farolled','lanterna','lanternaled','retrovisor']:
    result[id]={'value':None,'state':'Leitura ambigua','evidence':'Tabela de vidros desalinhada; conferir imagem original.'}
 if corrected and insurer=='Allianz':
  pay=crop(t,'OUTRAS FORMAS DE PAGAMENTO','SEU CORRETOR')
  row=rx(r'^ *sem juros[^\n]+').search(pay)
  if row:
   amounts=rx(MONEY).findall(row[0])
   total=result.get('total',{}).get('value')
   if len(amounts)==5 and total is not None:
    n=float(amounts[offer-1].replace('.','').replace(',','.'))
    if abs(n-total)>0.005:result['total']['state']='Revisar divergencia'
 return result
