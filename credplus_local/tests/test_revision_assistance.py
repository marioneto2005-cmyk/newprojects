import tempfile,unittest,io
from pathlib import Path
from unittest.mock import patch
import fitz
from PIL import Image,ImageDraw
from credplus.core import ASSETS,read_pdf_text
from credplus.proposal import parse_proposal,insured_addresses,Proposal,Offer,CORRETORAS
from credplus.document import pdf_bytes,export_document

FIX=Path(__file__).parent/'fixtures_commercial'
def load(name,company):return parse_proposal((FIX/(name+'.txt')).read_text(encoding='utf-8'),company)

class InsuredLocationTests(unittest.TestCase):
 def test_insured_address_scope_does_not_copy_branch_address(self):
  text='\n'.join(['DADOS DO(A) SEGURADO(A)','Nome do(a) Segurado(a) CPF/CNPJ','CLIENTE EXEMPLO','Endereço','RUA DO CLIENTE, 10',f'{"Bairro":40}{"Cidade":40}{"UF":6}CEP',f'{"CENTRO":40}{"CIDADE EXEMPLO":40}{"SP":6}12345-678','DADOS DA FILIAL','Endereço','RUA DA SEGURADORA, 99',f'{"Bairro":40}{"Cidade":40}{"UF":6}CEP',f'{"OUTRO":40}{"OUTRA CIDADE":40}{"RJ":6}99999-999'])
  data=insured_addresses(text);self.assertEqual(data['endereco'],'RUA DO CLIENTE, 10');self.assertEqual(data['cep_segurado'],'12345-678');self.assertEqual(data['cidade_uf'],'CIDADE EXEMPLO / SP');self.assertNotIn('SEGURADORA',str(data));self.assertNotIn('99999',str(data))
 def test_broker_address_is_not_presented_as_insured_address(self):
  text='Dados do seguro-segurado\nSegurado: CLIENTE EXEMPLO\nDados do Veículo\nDados do Corretor: EMPRESA\nEndereço completo: RUA DA CORRETORA, 10 - 99999-999'
  data=insured_addresses(text);self.assertFalse(data)
 def test_explicit_overnight_and_circulation_are_separate(self):
  data=insured_addresses('Endereço de pernoite: RUA PERNOITE, 20\nCEP de Circulação: 12345678\nCEP cadastral: 87654-321')
  self.assertEqual(data['endereco_pernoite'],'RUA PERNOITE, 20');self.assertEqual(data['cep_circulacao'],'12345678');self.assertEqual(data['cep_segurado'],'87654-321')
 def test_highlight_is_in_pdf_and_png(self):
  proposal=Proposal('Mapfre',{'nome':'CLIENTE EXEMPLO','endereco':'RUA EXEMPLO, 10','cep':'12345-678'},[Offer('Auto',{'total':'1.000,00'})])
  with tempfile.TemporaryDirectory() as tmp:
   png=Path(tmp)/'proposta.png';export_document(png,proposal,'png')
   with fitz.open(stream=pdf_bytes(proposal),filetype='pdf') as d:
    yellow=[x for x in d[0].get_drawings() if x.get('fill') and x['fill'][0]>.99 and .94<x['fill'][1]<.98 and .59<x['fill'][2]<.64]
    self.assertGreaterEqual(len(yellow),4);self.assertIn('RUA EXEMPLO, 10',d[0].get_text());self.assertIn('12345-678',d[0].get_text())
   with Image.open(png) as image:
    yellow=sum(count for count,color in image.convert('RGB').getcolors(image.width*image.height) if color[0]>=250 and 240<=color[1]<=250 and 150<=color[2]<=170);self.assertGreater(yellow,20)

class AllianzRevisionTests(unittest.TestCase):
 def test_deductible_from_participation_section(self):
  p=load('ALLIANZ','Allianz')
  for offer in p.offers:
   if offer.name=='Roubo e Furto':self.assertNotIn('franquia',offer.values)
   else:self.assertEqual(offer.values['franquia'],'3.478,14');self.assertEqual(offer.values['tipofranquia'],'50% da Normal')
  self.assertEqual(len(p.payments),180)
 def test_payment_headers_without_oferta_are_supported(self):
  text='''Básico          Ampliado          Completo
Preço Total 1.000,00 2.000,00 3.000,00
Master          Exclusivo
Preço Total 4.000,00 5.000,00
OUTRAS FORMAS DE PAGAMENTO
Boleto Bancário
Oferta (R$)
01 sem juros 1.000,00  2.000,00  3.000,00  4.000,00  5.000,00
02 sem juros 500,00  1.000,00  ILEGIVEL  2.000,00  2.500,00
Cartão de Crédito
01 sem juros 1.000,00  2.000,00  3.000,00  4.000,00  5.000,00
'''
  p=parse_proposal(text,'Allianz');self.assertEqual(len(p.payments),14)
  self.assertFalse(any(r.offer=='Completo' and r.installments==2 for r in p.payments))
  self.assertEqual(next(r for r in p.payments if r.offer=='Master' and r.installments==2).amount,'2.000,00')
 def test_conflicting_deductible_is_not_invented(self):
  text=(FIX/'ALLIANZ.txt').read_text().replace('50% da Normal                              3.478,14','50% da Normal                              3.478,14\n50% da Normal                              4.000,00')
  p=parse_proposal(text,'Allianz');self.assertTrue(all('franquia' not in o.values for o in p.offers))
 def test_blue_ocr_background_removed_only_when_requested(self):
  image=Image.new('RGB',(250,120),'#a4ccd6');ImageDraw.Draw(image).rectangle((10,10,40,40),fill='black');buffer=io.BytesIO();image.save(buffer,format='PNG')
  with tempfile.TemporaryDirectory() as tmp:
   pdf=Path(tmp)/'scan.pdf';d=fitz.open();d.new_page(width=250,height=120).insert_image(fitz.Rect(0,0,250,120),stream=buffer.getvalue());d.save(pdf);d.close()
   def ocr(command):
    with Image.open(command[1]) as converted:self.assertEqual(set(converted.tobytes()),{0,255})
    return b'OUTRAS FORMAS DE PAGAMENTO\nBoleto Bancario'
   with patch('credplus.core.find_tesseract',return_value='/fake/tesseract'),patch('credplus.core._run',side_effect=ocr):
    text,methods=read_pdf_text(pdf,clean_ocr=True);self.assertEqual(methods,['OCR']);self.assertIn('Boleto Bancario',text)

class TokioAndPortoTests(unittest.TestCase):
 def test_tokio_classico_removed_from_model_and_customer_art(self):
  p=load('TOKIO','Tokio Marine');self.assertEqual([o.name for o in p.offers],['Auto']);self.assertEqual(len(p.payments),34);self.assertTrue(all(r.offer=='Auto' for r in p.payments))
  with fitz.open(stream=pdf_bytes(p),filetype='pdf') as d:self.assertNotIn('Clássico',d[0].get_text());self.assertNotIn('Classico',d[0].get_text())
 def test_section_title_for_every_insurer(self):
  for company in CORRETORAS:
   p=Proposal(company,{},[Offer('Auto',{'total':'1.000,00','parabrisa':'250,00'})])
   with fitz.open(stream=pdf_bytes(p),filetype='pdf') as d:
    self.assertIn('FRANQUIA E ASSISTÊNCIAS',d[0].get_text());self.assertNotIn('FRANQUIAS DOS COMPONENTES',d[0].get_text())
 def test_porto_product_premium_and_residential_coverages(self):
  p=load('PORTO','Porto Seguro');self.assertEqual(len(p.offers),1);o=p.offers[0]
  self.assertIn('Proteção Combinada',o.name);self.assertEqual(o.values['total'],'1.694,91');self.assertEqual(o.values['franquia'],'2.608,00');self.assertEqual(o.values['res_incendio'],'500.000,00');self.assertEqual(o.values['res_rcf'],'8.000,00');self.assertEqual(o.values['res_aluguel'],'10.000,00');self.assertEqual(len(p.payments),54)
  self.assertEqual(next(r for r in p.payments if 'AQUISICAO' in r.mode and r.installments==1).amount,'1.528,84')
  self.assertEqual(next(r for r in p.payments if r.mode=='Boleto à vista').amount,'1.610,12')
 def test_calculator_assets_are_valid_multisize_icons(self):
  with Image.open(ASSETS/'calculator.ico') as ico:self.assertTrue({(16,16),(32,32),(256,256)}.issubset(ico.ico.sizes()))
  with Image.open(ASSETS/'calculator.png') as png:self.assertEqual(png.size,(256,256));self.assertEqual(png.mode,'RGBA')
