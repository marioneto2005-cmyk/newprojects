"""One readable digital page, shared by PDF and PNG exports."""
from pathlib import Path
import html,io,re
import fitz
from .core import FIELD_MAP,_atomic_save,safe_text
from .proposal import COVER_KEYS,GLASS_KEYS,Proposal

LABELS={**{k:f.label for k,f in FIELD_MAP.items()},'defesa':'Gastos com defesa','total':'Prêmio total',
 'isencao_terceiro':'Isenção de franquia quando não culpado pelo sinistro',
 'desconto_despesas':'Desconto na franquia com despesas extras',
 'reserva_terceiro':'Carro reserva quando terceiro em outro seguro',
 'garantia_zero':'Garantia padrão de zero km','martelinho':'Martelinho e para-choque',
 'pintura':'Lataria e pintura','assistencia_casa':'Assistência casa','objetos':'Objetos transportados',
 'maquinavidros':'Máquina de vidros','retrovisorinterno':'Retrovisor interno','pelicula':'Película',
 'farolmatrix':'Farol Matrix','pequenos_reparos':'Pequenos reparos premium',
 'parachoque':'Troca de para-choque','retrovisorled':'Retrovisor LED','res_incendio':'Residencial - incêndio, explosão e fumaça','res_rcf':'Residencial - responsabilidade civil familiar','res_aluguel':'Residencial - perda ou pagamento de aluguel'}

def present(value):
    return value is not None and str(value).strip().casefold() not in ('','não informado','nao informado','none','null','nan')

def text(value):return html.escape(safe_text(value)).replace('\n','<br/>')

def money(key,value):
    if not present(value):return ''
    numeric=key in ('defesa','res_incendio','res_rcf','res_aluguel') or key in GLASS_KEYS or (key in FIELD_MAP and FIELD_MAP[key].kind=='money')
    return ('R$ ' if numeric and not str(value).startswith('R$') else '')+str(value)


def pdf_bytes(proposal,consultant='',phone='',logo=None):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from PIL import Image as PILImage
    if not any(present(v) for v in proposal.values.values()) and not any(o.values for o in proposal.offers) and not proposal.payments:
        raise ValueError('Selecione uma proposta ou preencha algum dado antes de gerar.')
    width=595.28;inner=width-48;green=colors.HexColor('#075e52');ink=colors.HexColor('#172e39');muted=colors.HexColor('#647982');light=colors.HexColor('#edf5f3')
    style={
      'body':ParagraphStyle('body',fontName='Helvetica',fontSize=8.3,leading=11,textColor=ink),
      'label':ParagraphStyle('label',fontName='Helvetica-Bold',fontSize=8,leading=10.5,textColor=ink),
      'small':ParagraphStyle('small',fontName='Helvetica',fontSize=7.3,leading=9.5,textColor=muted),
      'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=green),
      'section':ParagraphStyle('section',fontName='Helvetica-Bold',fontSize=10,leading=13,textColor=green),
      'th':ParagraphStyle('th',fontName='Helvetica-Bold',fontSize=7.8,leading=10,textColor=colors.white),
    }
    def p(s,kind='body',highlight=False):
        content=text(s)
        if highlight:content='<font backColor="#FFF59D">'+content+'</font>'
        return Paragraph(content,style[kind])
    def table(rows,widths,header=True):
        t=Table(rows,colWidths=widths,hAlign='LEFT')
        commands=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#dce6e3'))]
        if header:commands += [('BACKGROUND',(0,0),(-1,0),green),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8f7')])]
        else:commands += [('BACKGROUND',(0,0),(-1,-1),light)]
        t.setStyle(TableStyle(commands));return t
    story=[]
    company=proposal.corretora
    if company=='Porto Seguro' and any('Azul Seguros' in n for n in proposal.notes):company='Porto Seguro / Azul'
    title=[p('Proposta de Seguro Auto','title'),Spacer(1,5),p(proposal.corretora and 'Seguradora: '+company or 'Seguro automóvel','small')]
    logoimage=''
    if logo and Path(logo).is_file():
        with PILImage.open(logo) as im:
            ratio=min(130/im.width,65/im.height);logoimage=Image(str(logo),width=im.width*ratio,height=im.height*ratio)
    head=Table([[title,logoimage]],colWidths=[inner-150,150]);head.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(1,0),(1,0),'RIGHT'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
    story += [head,Spacer(1,18)]
    ordinary=[f for f in FIELD_MAP.values() if f.section in ('Segurado','Perfil','Veículo') and present(proposal.values.get(f.key))]
    ordinary.sort(key=lambda f:{'Segurado':0,'Perfil':1,'Veículo':2}[f.section])
    if ordinary:
        story += [p('CLIENTE E VEÍCULO','section'),Spacer(1,7)]
        cells=[]
        for f in ordinary:
            highlight=f.key in ('endereco','bairro','cidade_uf','cep_segurado','endereco_pernoite','cidade_pernoite','cep','cep_circulacao')
            cells.append([p(f.label,'small',highlight),p(proposal.values[f.key],'label',highlight)])
        rows=[]
        for i in range(0,len(cells),3):rows.append(cells[i:i+3]+['']*(3-len(cells[i:i+3])))
        story += [table(rows,[inner/3]*3,False),Spacer(1,16)]
    offers=proposal.offers
    if offers:
        story += [p('OPÇÕES DE COBERTURA','section'),Spacer(1,7)]
        keys=[key for key in COVER_KEYS if any(present(o.values.get(key)) for o in offers)]
        keys=[k for k in keys if k not in ('franquia','tipofranquia')]+[k for k in ('franquia','tipofranquia','total') if any(present(o.values.get(k)) for o in offers)]
        # Different component franchises remain in their respective option columns.
        keys += [k for k in GLASS_KEYS if len({str(o.values.get(k,'')) for o in offers if present(o.values.get(k))})>1]
        # At most six options per block: readable columns even for unfamiliar larger documents.
        for start in range(0,len(offers),6):
            group=offers[start:start+6];wlabel=145;wvalue=(inner-wlabel)/len(group)
            rows=[[p('Cobertura / condição','th')]+[p(o.name,'th') for o in group]]
            for key in keys:
                values=[o.values.get(key,'') for o in group]
                if not any(present(v) for v in values):continue
                rows.append([p(LABELS.get(key,key),'label')]+[p(money(key,v)) for v in values])
            story += [table(rows,[wlabel]+[wvalue]*len(group)),Spacer(1,12)]
    component=[]
    for key in GLASS_KEYS:
        vals=[o.values.get(key) for o in offers if present(o.values.get(key))]
        value=proposal.values.get(key)
        if len(set(vals))==1:value=vals[0]
        elif len(set(vals))>1:continue
        if present(value):component.append((LABELS[key],money(key,value)))
    if component:
        story += [p('FRANQUIA E ASSISTÊNCIAS','section'),Spacer(1,7)]
        rows=[]
        for i in range(0,len(component),3):
            row=[[p(label,'small'),p(value,'label')] for label,value in component[i:i+3]];rows.append(row+['']*(3-len(row)))
        story += [table(rows,[inner/3]*3,False),Spacer(1,16)]
    if proposal.payments:
        story += [p('FORMAS DE PAGAMENTO','section'),Spacer(1,4),p('A quantidade de parcelas inclui a entrada quando indicada. Valores, juros e totais seguem o documento.','small'),Spacer(1,8)]
        # Pivot all plans; never hide the intermediate installment options or substitute maxima.
        columns=list(dict.fromkeys((r.mode,r.offer) for r in proposal.payments))
        modes=list(dict.fromkeys(r.mode for r in proposal.payments))
        preferred=['Cartão de crédito','Débito em conta','Débito / Pix automático','Boleto','Ficha / boleto','Carnê']
        mode_order={m:i for i,m in enumerate(preferred+[m for m in modes if m not in preferred])}
        offer_order={o.name:i for i,o in enumerate(offers)}
        columns.sort(key=lambda c:(mode_order.get(c[0],99),offer_order.get(c[1],99)))
        for start in range(0,len(columns),6):
            group=columns[start:start+6];counts=sorted({r.installments for r in proposal.payments if (r.mode,r.offer) in group})
            grid={}
            for r in proposal.payments:
                if (r.mode,r.offer) not in group:continue
                cell='R$ '+r.amount
                if r.schedule:
                    runs=[];a=0
                    while a<len(r.schedule):
                        b=a
                        while b+1<len(r.schedule) and r.schedule[b+1]==r.schedule[a]:b+=1
                        label=f'{a+1}ª' if a==b else f'{a+1}ª–{b+1}ª'
                        runs.append(label+' R$ '+r.schedule[a]);a=b+1
                    cell='; '.join(runs)
                elif present(r.entry):cell='Entrada R$ '+r.entry+('\n+ '+str(r.installments-1)+'x R$ '+r.amount if r.installments>1 else '')
                if present(r.total):cell+='\nTotal: R$ '+r.total
                if present(r.interest):
                    interest='Sem juros' if r.interest.lower()=='sem juros' else r.interest
                    cell+='\n'+interest
                identity=((r.mode,r.offer),r.installments)
                # Retain conflicting printed conditions instead of silently overwriting them.
                if identity in grid and grid[identity]!=cell:grid[identity]+='\nAlternativa: '+cell
                else:grid[identity]=cell
            rows=[[p('Plano','th')]+[p(mode+(' / '+offer if len(offers)>1 else ''),'th') for mode,offer in group]]
            for n in counts:rows.append([p(str(n)+'x','label')]+[p(grid.get((column,n),'')) for column in group])
            w=(inner-43)/len(group);story += [table(rows,[43]+[w]*len(group)),Spacer(1,10)]
        conditions=list(dict.fromkeys(r.condition for r in proposal.payments if present(r.condition)))
        for condition in conditions:story += [p(condition,'small'),Spacer(1,4)]
    manual=[(LABELS.get(k,k),v) for k,v in proposal.values.items() if present(v) and (k.endswith('_extra') or k in ('pagamento_cartao','pagamento_outros'))]
    if manual:
        story += [Spacer(1,6),p('INFORMAÇÕES ADICIONAIS','section'),Spacer(1,7)]
        for label,value in manual:story += [p(label,'label'),p(value),Spacer(1,6)]
    for note in proposal.notes:
        if present(note):story += [p(note,'small'),Spacer(1,5)]
    if consultant or phone:
        story += [Spacer(1,10),table([[p('SEU ATENDIMENTO','small'),p(' | '.join(x for x in [consultant,phone] if x),'label')]],[100,inner-100],False)]
    story += [Spacer(1,12),p('Condições e valores conforme o documento apresentado. Contratação sujeita à aceitação e às condições do produto.','small')]
    # Size the page around its content instead of shrinking fonts or dropping payment plans.
    content_height=sum(flow.wrap(inner-12,100000)[1] for flow in story)
    height=max(841.89,content_height+72)
    if height>14000:raise ValueError('A proposta é extensa demais para uma página legível. Reduza os textos adicionais.')
    out=io.BytesIO();doc=SimpleDocTemplate(out,pagesize=(width,height),leftMargin=24,rightMargin=24,topMargin=24,bottomMargin=24,title='Proposta de Seguro Auto',author='Proposta Seguro Auto')
    doc.build(story)
    data=out.getvalue()
    with fitz.open(stream=data,filetype='pdf') as check:
        if len(check)!=1:raise RuntimeError('Não foi possível organizar o documento em página única.')
    return data


def export_document(path,proposal,kind='pdf',consultant='',phone='',logo=None):
    if kind not in ('pdf','png'):raise ValueError('Selecione PDF ou PNG.')
    data=pdf_bytes(proposal,consultant,phone,logo)
    if kind=='pdf':_atomic_save(path,lambda p:Path(p).write_bytes(data));return
    with fitz.open(stream=data,filetype='pdf') as doc:
        # The PNG uses the very same page as the PDF, at 150 dpi, with an opaque background.
        pix=doc[0].get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False)
        pix.set_dpi(150,150)
        _atomic_save(path,lambda p:Path(p).write_bytes(pix.tobytes('png')))
