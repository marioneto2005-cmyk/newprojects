import copy,io,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from PIL import Image
from credplus.proposal import parse_proposal,Proposal,Offer,Payment,CORRETORAS
from credplus.document import export_document,pdf_bytes
from credplus.settings import save_logo,saved_logo,remove_logo

FIX=Path(__file__).parent/'fixtures_commercial'
NAMES={'ALLIANZ':'Allianz','ALRIO':'Aliro','AZUL':'Azul','HDI':'HDI','MAPFRE':'Mapfre','TOKIO':'Tokio Marine','YELUM':'Yelum','ZURICH':'Zurich'}
def load(name):return parse_proposal((FIX/(name+'.txt')).read_text(encoding='utf-8'),NAMES[name])

class CommercialTests(unittest.TestCase):
 def test_eight_layouts_option_and_payment_counts(self):
  expected={'ALLIANZ':(6,180),'ALRIO':(1,1),'AZUL':(1,74),'HDI':(2,64),'MAPFRE':(1,42),'TOKIO':(2,68),'YELUM':(1,22),'ZURICH':(1,10)}
  for name,(offers,payments) in expected.items():
   with self.subTest(name=name):
    p=load(name);self.assertEqual(len(p.offers),offers);self.assertEqual(len(p.payments),payments)
    self.assertEqual(len({(r.offer,r.mode,r.installments) for r in p.payments}),payments)
 def test_allianz_six_options_correct_lmi_not_premium(self):
  p=load('ALLIANZ')
  self.assertEqual([o.values['total'] for o in p.offers],['943,87','1.988,30','2.025,51','2.076,93','2.163,59','2.350,48'])
  self.assertEqual([o.values['dm'] for o in p.offers],['100.000,00','100.000,00','150.000,00','200.000,00','400.000,00','1.000.000,00'])
  self.assertTrue(any('restrita' in n for n in p.notes))
 def test_allianz_cent_difference_is_visible(self):
  p=load('ALLIANZ');self.assertEqual(p.offers[4].values['total'],'2.163,59')
  self.assertTrue(any(r.offer=='Master' and r.installments==1 and r.amount=='2.163,60' for r in p.payments))
  self.assertTrue(any('2.163,59' in note and '2.163,60' in note for note in p.notes))
 def test_hdi_options_and_methods_keep_their_columns(self):
  p=load('HDI');self.assertEqual(p.offers[0].values['total'],'3.758,96');self.assertEqual(p.offers[1].values['total'],'3.535,83')
  self.assertEqual(p.offers[1].values['casco'],'R$ 64.656,00 (valor determinado)')
  self.assertTrue(any(r.offer==p.offers[0].name and r.mode=='Carnê' and r.installments==2 and r.amount=='1.920,83' for r in p.payments))
  self.assertTrue(any(r.offer==p.offers[1].name and r.mode=='Carnê' and r.installments==2 and r.amount=='1.806,80' for r in p.payments))
  self.assertFalse(any(r.interest for r in p.payments)) # no invented "sem juros"
 def test_tokio_preserves_interest_totals(self):
  p=load('TOKIO');self.assertEqual([o.values['total'] for o in p.offers],['4.048,28','3.893,94'])
  r=next(r for r in p.payments if r.offer=='Auto' and r.mode=='Débito / Pix automático' and r.installments==6)
  self.assertEqual((r.amount,r.total,r.interest),('700,21','4.202,15','3,80%'))
 def test_tokio_additional_benefits_keep_option_differences(self):
  p=load('TOKIO');self.assertEqual(p.offers[0].values['garantia_zero'],'180 dias');self.assertEqual(p.offers[1].values['garantia_zero'],'30 dias')
  self.assertEqual(p.offers[0].values['isencao_terceiro'],'Disponivel');self.assertEqual(p.offers[1].values['isencao_terceiro'],'Nao Disponivel')
  self.assertIn('reboque Ilimitado',p.offers[0].values['assistencia'])
 def test_mapfre_missing_methods_do_not_shift_11x(self):
  p=load('MAPFRE');eleven=[r for r in p.payments if r.installments==11]
  self.assertEqual(len(eleven),1);self.assertEqual(eleven[0].mode,'Cartão de crédito');self.assertEqual(eleven[0].amount,'365,60')
  r=next(r for r in p.payments if r.mode=='Boleto' and r.installments==3)
  self.assertEqual((r.amount,r.total,r.interest),('1.367,20','4.101,60','Com Juros'))
 def test_azul_discounts_and_missing_first_boleto(self):
  p=load('AZUL');self.assertEqual(p.offers[0].values['casco'],'80.00% FIPE')
  self.assertTrue(any(r.installments==1 and r.amount=='2.736,62' and 'AQUISICAO' in r.mode for r in p.payments))
  carne=[r for r in p.payments if r.mode=='1 BOLETO / DEMAIS CARNE'];self.assertEqual(min(r.installments for r in carne),2)
  self.assertEqual(next(r for r in carne if r.installments==5).amount,'667,97')
 def test_aliro_different_first_and_last_installments(self):
  p=load('ALRIO');r=p.payments[0];self.assertEqual(r.installments,10)
  self.assertEqual(r.schedule,['284,26']+['284,19']*8+['284,20']);self.assertEqual(r.total,'2.841,98')
 def test_yelum_eleven_installments_and_no_inferred_total(self):
  p=load('YELUM');r=next(r for r in p.payments if r.mode=='Débito em conta' and r.installments==11)
  self.assertEqual(r.amount,'174,90');self.assertEqual(r.total,'')
 def test_zurich_entry_and_total(self):
  p=load('ZURICH');r=next(r for r in p.payments if r.installments==3)
  self.assertEqual((r.entry,r.amount,r.total),('781,34','781,34','2.344,02'))
 def test_no_stale_values_from_previous_layout(self):
  a=load('ALLIANZ');b=parse_proposal('Sem dados comerciais','Allianz')
  self.assertGreater(len(a.offers),0);self.assertFalse(b.offers);self.assertFalse(b.payments)
 def test_no_account_or_quote_fields_are_copied(self):
  p=parse_proposal('Numero da apolice: APOLICE_PRIVADA\nNumero da cotacao: COTACAO_PRIVADA\nConta: CONTA_PRIVADA','Azul')
  self.assertNotIn('PRIVADA',str(p.to_dict()))

class VisualDocumentTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_all_eight_layouts_are_single_page_and_no_placeholders(self):
  for name in NAMES:
   p=load(name);p.values.update(nome='CLIENTE DEMONSTRATIVO',modelo='VEÍCULO EXEMPLO')
   with fitz.open(stream=pdf_bytes(p),filetype='pdf') as d:
    self.assertEqual(len(d),1,name);text=d[0].get_text()
    self.assertNotIn('Não informado',text);self.assertNotIn('NÃO INFORMADO',text)
    self.assertIn(p.corretora,text)
    for word in d[0].get_text('words'):
     self.assertGreaterEqual(word[0],20);self.assertLessEqual(word[2],d[0].rect.width-15)
 def test_pdf_and_png_same_page_at_150_dpi(self):
  p=load('ALLIANZ');pdf=self.root/'proposta.pdf';png=self.root/'proposta.png'
  export_document(pdf,p,'pdf');export_document(png,p,'png')
  with fitz.open(pdf) as d:
   expected=d[0].get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False)
   with Image.open(png) as im:self.assertEqual(im.size,(expected.width,expected.height));self.assertEqual(im.convert('RGB').tobytes(),expected.samples);self.assertAlmostEqual(im.info['dpi'][0],150,delta=1)
 def test_intermediate_payment_values_are_not_omitted(self):
  p=load('MAPFRE')
  with fitz.open(stream=pdf_bytes(p),filetype='pdf') as d:
   text=''.join(d[0].get_text().split())
   for r in p.payments:self.assertIn(r.amount,text);self.assertIn(r.total,text)
 def test_aliro_schedule_and_zurich_entry_are_explicit(self):
  with fitz.open(stream=pdf_bytes(load('ALRIO')),filetype='pdf') as d:
   t=d[0].get_text();self.assertIn('284,26',t);self.assertIn('284,20',t)
  with fitz.open(stream=pdf_bytes(load('ZURICH')),filetype='pdf') as d:self.assertIn('+ 2x R$',d[0].get_text())
 def test_logo_is_rendered_and_preserves_aspect(self):
  logo=self.root/'logo.png';Image.new('RGB',(400,100),'green').save(logo)
  with fitz.open(stream=pdf_bytes(load('HDI'),logo=logo),filetype='pdf') as d:
   images=d[0].get_images();self.assertGreater(len(images),0);self.assertEqual(images[0][2]/images[0][3],4)
 def test_empty_values_do_not_create_client_rows(self):
  p=Proposal('HDI',{'nome':'','cpf':'Não informado'},[Offer('Auto',{'total':'0,00','dm':''})])
  with fitz.open(stream=pdf_bytes(p),filetype='pdf') as d:
   t=d[0].get_text();self.assertNotIn('CPF',t);self.assertNotIn('CLIENTE E VEÍCULO',t);self.assertIn('0,00',t)
 def test_blank_proposal_does_not_replace_existing_file(self):
  dest=self.root/'existente.pdf';dest.write_bytes(b'original')
  with self.assertRaises(ValueError):export_document(dest,Proposal('HDI'))
  self.assertEqual(dest.read_bytes(),b'original')
 def test_long_text_stays_on_single_page_without_shrinking_font(self):
  p=load('HDI');p.values['perfil_extra']='Condição adicional. '*60
  with fitz.open(stream=pdf_bytes(p),filetype='pdf') as d:
   self.assertEqual(len(d),1);self.assertIn('Condição adicional.',d[0].get_text())
   for block in d[0].get_text('dict')['blocks']:
    for line in block.get('lines',[]):
     for span in line['spans']:self.assertGreaterEqual(span['size'],7)

class LogoSettingsTests(unittest.TestCase):
 def test_logo_survives_source_file_removal(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'PROPOSTA_SETTINGS_DIR':str(Path(tmp)/'settings')}):
   source=Path(tmp)/'marca.png';Image.new('RGBA',(400,100),(10,200,100,255)).save(source)
   result=save_logo(source);source.unlink();self.assertEqual(saved_logo(),result)
   with Image.open(result) as im:self.assertEqual(im.size,(400,100))
   self.assertEqual(list(result.parent.iterdir()),[result]);remove_logo();self.assertIsNone(saved_logo())
 def test_invalid_logo_preserves_previous_logo(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'PROPOSTA_SETTINGS_DIR':str(Path(tmp)/'settings')}):
   source=Path(tmp)/'marca.png';Image.new('RGB',(100,40),'blue').save(source);save_logo(source);before=saved_logo().read_bytes()
   source.write_text('not an image')
   with self.assertRaises(Exception):save_logo(source)
   self.assertEqual(saved_logo().read_bytes(),before)
