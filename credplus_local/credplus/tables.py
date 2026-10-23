"""Conservative multi-offer OCR table reader: never slice numbers by columns."""
import re
from .rule_engine import norm, MONEY
TABLE_KEYS=('total','dm','dc','morais','appm','appi','casco','assistencia','reserva','vidros')
AMOUNT=re.compile(r'(?<![\d.,])'+MONEY+r'(?![\d.,])')

def allianz_ocr_table(text,offer):
    text=norm(text)
    result={key:{'value':None,'state':'Tabela não localizada / conferir','evidence':'Confira a coluna da opção no PDF original.'} for key in TABLE_KEYS}
    headings=list(re.finditer(r'^ *Basico +Ampliado +Completo\s*$',text,re.M)) if offer<=3 else list(re.finditer(r'^ *Master +Exclusivo\s*$',text,re.M))
    if len(headings)!=1:return result
    chunk=text[headings[0].end():]
    end=re.search(r'^ *Master +Exclusivo\s*$|^ *\*\* RCF:',chunk,re.M)
    if end:chunk=chunk[:end.start()]
    count=3 if offer<=3 else 2;column=offer-1 if offer<=3 else offer-4
    labels={
      'dm':r'RCF\*\* - Danos Materiais', 'dc':r'RCF\*\* - Danos Corporais',
      'morais':r'RCF\*\* - Danos Morais e Esteticos',
      'appm':r'APP\*\*\* - Morte', 'appi':r'APP\*\*\* - Invalidez Permanente',
      'total':r'Preco Total',
    }
    for key,label in labels.items():
        rows=list(re.finditer(r'^ *'+label+r' +([^\n]+)$',chunk,re.M))
        if len(rows)!=1:continue
        values=AMOUNT.findall(rows[0][1]);expected=count if key=='total' else count*2
        if len(values)!=expected:continue
        # A leading sign or unmatched digits means a damaged row: reject instead of shifting values.
        residue=AMOUNT.sub('',rows[0][1])
        if re.search(r'[0-9-]',residue):continue
        selected=values[column if key=='total' else column*2]
        result[key]={'value':float(selected.replace('.','').replace(',','.')),'state':'Revisar OCR / opção','evidence':rows[0][0]}
    for key,label,pattern in [('assistencia','Guincho',r'Km Livre'),('reserva','Carro Reserva',r'\d+ Dias')]:
        rows=list(re.finditer(r'^ *'+label+r' +([^\n]+)$',chunk,re.M))
        if len(rows)!=1:continue
        matches=re.findall(pattern,rows[0][1],re.I)
        if len(matches)==count:result[key]={'value':matches[column],'state':'Revisar OCR / opção','evidence':rows[0][0]}
    # Distinct totals in the coverage and payment tables require manual resolution.
    payments=re.finditer(r'^ *0?1 +sem juros +([^\n]+)$',text,re.M)
    current=result['total']['value']
    for row in payments:
        vals=AMOUNT.findall(row[1])
        if len(vals)==5 and current is not None:
            payment=float(vals[offer-1].replace('.','').replace(',','.'))
            if abs(payment-current)>.005:
                result['total']={'value':None,'state':'Valores divergentes — preencher após conferir','evidence':f'Tabela de coberturas: {current:.2f}; tabela de pagamento: {payment:.2f}. Confira a proposta original.'}
                break
    return result
