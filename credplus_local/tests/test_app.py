import tempfile,unittest,zipfile,json
from pathlib import Path
from unittest.mock import patch
import fitz,openpyxl
from credplus.core import FIELD_MAP,FIELDS,ASSETS,format_value,validate_values,export_pdf,export_xlsx,extract_pdf
from credplus.tables import allianz_ocr_table

BASE={'nome':'CLIENTE EXEMPLO','modelo':'VEÍCULO EXEMPLO 1.0','total':'2.345,67'}
TABLE='''Básico                   Ampliado                   Completo
Coberturas Limite Limite Limite
RCF** - Danos Materiais 100.000,00 28,00 200.000,00 38,00 300.000,00 48,00
RCF** - Danos Corporais 100.000,00 12,00 200.000,00 13,00 300.000,00 14,00
APP*** - Morte 10.000,00 1,00 20.000,00 2,00 30.000,00 3,00
Preço Total 1.000,00 2.000,00 3.000,00
Master                   Exclusivo
Coberturas Limite Limite
RCF** - Danos Materiais 400.000,00 50,00 1.000.000,00 60,00
Preço Total 4.000,00 5.000,00
** RCF: responsabilidade
01 sem juros 1.000,00 2.000,00 3.000,00 4.000,00 5.001,00
'''
class ValidationTests(unittest.TestCase):
 def test_required(self):
  for key in ['nome','modelo','total']:
   data=dict(BASE);data.pop(key)
   with self.assertRaises(ValueError):validate_values(data)
 def test_money(self):
  self.assertEqual(format_value(FIELD_MAP['total'],'R$ 1.234,56'),'1.234,56')
  self.assertEqual(format_value(FIELD_MAP['total'],0),'0,00')
 def test_bad_money(self):
  for s in ['1.234','12,3','-2,00','NaN','inf','1,00,00']:
   with self.assertRaises(ValueError):format_value(FIELD_MAP['total'],s)
 def test_invalid_ids(self):
  for key,value in [('cpf','11111111111'),('chassi','9B3D281BMTSYGO05430'),('cep','12345'),('placa','ABC123')]:
   with self.assertRaises(ValueError):format_value(FIELD_MAP[key],value)
 def test_dates(self):
  self.assertEqual(format_value(FIELD_MAP['inicio'],'2026-10-23'),'23/10/2026')
  with self.assertRaises(ValueError):format_value(FIELD_MAP['inicio'],'31/02/2026')
 def test_allowlist(self):
  data=validate_values({**BASE,'numero_cotacao':'SEGREDO','numero_apolice':'SEGREDO','seguradora':'SEGREDO'})
  self.assertNotIn('SEGREDO',str(data));self.assertEqual(set(data),set(FIELD_MAP))
 def test_provider_name_removed(self):
  self.assertEqual(format_value(FIELD_MAP['assistencia'],'Assistência Zurich'),'Assistência')

class TableTests(unittest.TestCase):
 def test_separate_options_not_premiums(self):
  for n,expected in [(1,100000),(2,200000),(3,300000),(4,400000),(5,1000000)]:
   self.assertEqual(allianz_ocr_table(TABLE,n)['dm']['value'],expected)
 def test_missing_amount_blocks_row(self):
  damaged=TABLE.replace('100.000,00 28,00','28,00')
  for n in [1,2,3]:self.assertIsNone(allianz_ocr_table(damaged,n)['dm']['value'])
 def test_damaged_amount_not_shifted(self):
  damaged=TABLE.replace('200.000,00 38,00','20000000 38,00')
  self.assertIsNone(allianz_ocr_table(damaged,2)['dm']['value'])
 def test_total_divergence(self):
  r=allianz_ocr_table(TABLE,5)['total'];self.assertIsNone(r['value']);self.assertIn('divergentes',r['state'])
 def test_duplicate_header_blocked(self):
  self.assertIsNone(allianz_ocr_table(TABLE+TABLE,1)['total']['value'])
 def test_zero_distinct_missing(self):
  t=TABLE.replace('100.000,00 28,00','0,00 28,00');self.assertEqual(allianz_ocr_table(t,1)['dm']['value'],0)

class ExportTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_pdf_contains_values_not_excluded_fields(self):
  p=self.root/'resultado.pdf';export_pdf(p,{**BASE,'numero_apolice':'APOLICE_SECRETA','seguradora':'Zurich','inicio':'01/01/2026','coberturas_extra':'Gastos com defesa: R$ 10.000,00'})
  with fitz.open(p) as d:
   text='\n'.join(page.get_text() for page in d)
   self.assertGreater(len(d),0);self.assertIn('CLIENTE EXEMPLO',text);self.assertIn('2.345,67',text);self.assertIn('01/01/2026',text);self.assertIn('Gastos com defesa',text)
   for forbidden in ['APOLICE_SECRETA','Zurich']:self.assertNotIn(forbidden,text)
 def test_xlsx_clean_and_complete(self):
  p=self.root/'resultado.xlsx';export_xlsx(p,{**BASE,'parabrisa':'123,45','appg':'20.000,00','inicio':'01/01/2026','garagem':'Perfil extenso para conferência. '*30,'numero_cotacao':'SEGREDO'})
  w=openpyxl.load_workbook(p);s=w.active
  self.assertEqual(w.sheetnames,['Cotação Seguro Auto Sicoob','Complemento'])
  template=openpyxl.load_workbook(ASSETS/'modelo_limpo.xlsx')
  for field in FIELDS:
   if field.cell:self.assertIsNone(template.active[field.cell].value)
  self.assertIsNone(template.active['B7'].value);self.assertIn('__________________',s['A49'].value)
  self.assertEqual(s['B32'].value,'123,45');self.assertEqual(s['C38'].value,'2.345,67');self.assertEqual(s['C24'].value,'Não informado')
  texts=' '.join(str(c.value) for sh in w for row in sh for c in row if c.value is not None)
  for forbidden in ['SEGREDO','Zurich','PORTO SEGURO']:self.assertNotIn(forbidden,texts)
  self.assertIn('20.000,00',texts);self.assertIn('01/01/2026',texts);self.assertEqual(s['D11'].value,'Detalhes na aba Complemento');self.assertIn('Perfil extenso para conferência. '*30,texts)
 def test_excel_formula_injection(self):
  p=self.root/'resultado.xlsx';export_xlsx(p,{**BASE,'nome':'=1+1','pagamento_cartao':'=HYPERLINK("evil")'},consultant='=1+1')
  w=openpyxl.load_workbook(p)
  self.assertEqual(w.active['B5'].data_type,'s');self.assertEqual(w.active['C39'].data_type,'s')
  for s in w:
   for row in s:
    for c in row:self.assertNotEqual(c.data_type,'f')
 def test_pdf_markup_safe(self):
  p=self.root/'resultado.pdf';export_pdf(p,{**BASE,'nome':'Cliente <exemplo> & teste'})
  with fitz.open(p) as d:self.assertIn('Cliente <exemplo> & teste',''.join(x.get_text() for x in d))
 def test_long_content_paginates(self):
  p=self.root/'longo.pdf';export_pdf(p,{**BASE,'garagem':'Texto para conferência. '*45})
  with fitz.open(p) as d:self.assertGreaterEqual(len(d),2)
 def test_failed_write_preserves_existing(self):
  p=self.root/'original.pdf';p.write_bytes(b'original')
  with self.assertRaises(ValueError):export_pdf(p,{})
  self.assertEqual(p.read_bytes(),b'original')

class ExtractionTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_invalid_product(self):
  with self.assertRaises(ValueError):extract_pdf('none','HDI',99)
 def test_scan_without_ocr_explains_manual(self):
  p=self.root/'scan.pdf';d=fitz.open();d.new_page();d.save(p);d.close()
  with patch('credplus.core.find_tesseract',return_value=None):
   with self.assertRaisesRegex(RuntimeError,'manualmente'):extract_pdf(p,'Zurich')
 def test_password(self):
  p=self.root/'protegido.pdf';d=fitz.open();d.new_page();d.save(p,encryption=fitz.PDF_ENCRYPT_AES_256,owner_pw='owner',user_pw='test');d.close()
  with self.assertRaisesRegex(ValueError,'senha'):extract_pdf(p,'Zurich')
 def test_text_pdf_without_ocr_and_original_unchanged(self):
  p=self.root/'texto.pdf';d=fitz.open();page=d.new_page();page.insert_text((40,40),'Cliente exemplo dados demonstrativos suficientes para extracao de texto sem OCR. '*2);d.save(p);d.close();original=p.read_bytes()
  with patch('credplus.core.find_tesseract',side_effect=AssertionError('Não deve chamar OCR')):
   r=extract_pdf(p,'HDI')
  self.assertEqual(r['methods'],['texto']);self.assertEqual(p.read_bytes(),original)
 def test_max_pages(self):
  p=self.root/'muitas.pdf';d=fitz.open()
  for _ in range(61):d.new_page()
  d.save(p);d.close()
  with self.assertRaisesRegex(ValueError,'60'):extract_pdf(p,'Zurich')

if __name__=='__main__':unittest.main()
