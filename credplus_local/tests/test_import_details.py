"""Anonymized personal-data layout regression cases; no uploaded identities here."""
import unittest,tempfile
from pathlib import Path
from credplus.proposal import common_fields,resolve_driver_identity,Proposal,Offer
from credplus.core import format_value,FIELD_MAP
from credplus.document import pdf_bytes
import fitz
from PIL import Image

def row(*cells):
    line=''
    for pos,value in sorted(cells):
        if len(line)>pos:raise ValueError('Overlapping test columns')
        line+=' '*(pos-len(line))+value
    return line

def tokio(own=True):
    return '\n'.join([
      row((0,'Proponente'),(104,'CPF/CNPJ:'),(155,'Principal Condutor'),(206,'Estado Civil principal condutor')),
      row((206,'Casado(a) ou vive em uniao')),
      row((0,'ANA CLIENTE EXEMPLO'),(104,'529.982.247-25'),(155,'Proprio Segurado' if own else 'BRUNO CONDUTOR EXEMPLO')),
      row((206,'estavel')),
      'Nome Social:',
      row((0,'Tipo Seguro'),(31,'Vigencia'),(65,'Chassi decodificado'),(86,'Placa'),(98,'Chassi'),(121,'Ano modelo')),
      row((0,'Seguro Novo'),(31,'21/10/2026 - 21/10/2027'),(65,'Nao'),(86,'ABC-1D23'),(98,'1HGCM82633A004352'),(121,'2027')),
      row((0,'Fabricante'),(65,'Veiculo')),
      row((0,'MARCA EXEMPLO'),(65,'MODELO EXEMPLO HIBRIDO')),
      row((0,'Combustivel'),(31,'Lotacao'),(65,'Zero KM'),(121,'Codigo FIPE')),
      row((0,'Hibrido'),(31,'5'),(65,'Sim'),(121,'000000-0')),
      row((0,'Tipo de utilizacao'),(65,'Dispositivo comodatoChassi remarcado'),(121,'Data saida veiculo 0Km')),
      row((0,'Particular - Lazer / ida e volta ao trabalho'),(65,'Nao possui'),(86,'Nao'),(121,'08/10/2026')),
      'CEP de pernoite',row((54,'residencia habitual para o veiculo segurado?')),
      row((0,'12345-678'),(54,'Sim')),
    ])

def yelum(cep):
    return '\n'.join([
      row((0,'Capacidade'),(39,'Categoria'),(126,'Reg. de Tarif.'),(169,'CEP de Pernoite'),(209,'Tipo de Franquia')),
      row((0,'5'),(39,'PASSEIO'),(126,'1601'),(169,cep),(209,'0.5 - FACULTATIVA')),
    ])

class ImportDetailsTests(unittest.TestCase):
 def test_tokio_wrapped_insured_header_and_own_driver(self):
    v=common_fields(tokio(),'Tokio Marine')
    self.assertEqual(v['nome'],'ANA CLIENTE EXEMPLO');self.assertEqual(v['cpf'],'529.982.247-25');self.assertEqual(v['condutor'],v['nome']);self.assertEqual(v['cpfcond'],v['cpf'])
 def test_tokio_car_and_usage_headers(self):
    v=common_fields(tokio(),'Tokio Marine')
    expected={'placa':'ABC-1D23','chassi':'1HGCM82633A004352','ano':'2027','modelo':'MARCA EXEMPLO - MODELO EXEMPLO HIBRIDO','combustivel':'Hibrido','zero':'Sim','inicio':'21/10/2026','fim':'21/10/2027','cep':'12345-678','garagem':'Sim'}
    for key,value in expected.items():self.assertEqual(v[key],value,key)
    self.assertIn('ida e volta ao trabalho',v['uso'])
 def test_tokio_distinct_driver_does_not_inherit_insured_id(self):
    v=common_fields(tokio(False),'Tokio Marine');self.assertEqual(v['condutor'],'BRUNO CONDUTOR EXEMPLO');self.assertFalse(v.get('cpfcond'))
 def test_matching_names_can_reuse_id(self):
    v=resolve_driver_identity({'nome':'ANA CLÁUDIA EXEMPLO','condutor':'ana claudia exemplo','cpf':'529.982.247-25'})
    self.assertEqual(v['cpfcond'],v['cpf'])
 def test_other_person_does_not_inherit_id(self):
    v=resolve_driver_identity({'nome':'ANA EXEMPLO','condutor':'BRUNO EXEMPLO','cpf':'529.982.247-25'});self.assertNotIn('cpfcond',v)
 def test_explicit_driver_id_is_never_overwritten(self):
    v=resolve_driver_identity({'nome':'ANA EXEMPLO','condutor':'ANA EXEMPLO','cpf':'529.982.247-25','cpfcond':'111.444.777-35'});self.assertEqual(v['cpfcond'],'111.444.777-35')
 def test_company_id_can_be_reused_when_explicitly_same(self):
    v=resolve_driver_identity({'nome':'EMPRESA EXEMPLO LTDA','condutor':'Proprio Segurado','cpf':'04.252.011/0001-10'});self.assertEqual(v['cpfcond'],v['cpf'])
 def test_missing_identity_does_not_create_a_driver_id(self):
    v=resolve_driver_identity({'condutor':'Proprio Segurado','cpf':'529.982.247-25'});self.assertNotIn('cpfcond',v)
 def test_yelum_full_postcode_in_correct_column(self):
    self.assertEqual(common_fields(yelum('12345-678'),'Yelum')['cep'],'12345-678')
 def test_yelum_partial_postcode_is_labelled_not_completed(self):
    v=common_fields(yelum('12345'),'Yelum');self.assertEqual(v['cep'],'12345 (parcial no documento)');self.assertNotIn('12345000',v['cep'])
 def test_partial_postcode_survives_editing_roundtrip(self):
    value=format_value(FIELD_MAP['cep'],'12345');self.assertEqual(format_value(FIELD_MAP['cep'],value),value)
 def test_yelum_tariff_region_is_not_used_as_postcode(self):
    self.assertNotIn('cep',common_fields(yelum(''),'Yelum'))
 def test_title_and_insurer_are_correct_with_logo(self):
    with tempfile.TemporaryDirectory() as tmp:
      logo=Path(tmp)/'marca.png';Image.new('RGB',(400,100),'green').save(logo)
      proposal=Proposal('Mapfre',{'nome':'CLIENTE EXEMPLO'},[Offer('Auto',{'total':'2.000,00'})])
      with fitz.open(stream=pdf_bytes(proposal,logo=logo),filetype='pdf') as d:
       text=d[0].get_text();self.assertIn('Seguradora: Mapfre',text);self.assertNotIn('Corretora:',text)
       lines=[line for block in d[0].get_text('dict')['blocks'] for line in block.get('lines',[])]
       title=next(line for line in lines if ''.join(span['text'] for span in line['spans'])=='Proposta de Seguro Auto')
       self.assertEqual(len(title['spans']),1);self.assertEqual(title['spans'][0]['size'],16)
