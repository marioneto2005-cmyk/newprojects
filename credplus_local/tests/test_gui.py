"""Desktop interaction tests; automatic generation, with no review gate."""
import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from credplus import APP_NAME
from credplus.proposal import Proposal,Offer,Payment,CORRETORAS

@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requer tela gráfica')
class DesktopTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'PROPOSTA_SETTINGS_DIR':str(Path(self.tmp.name)/'settings')});self.env.start()
  from credplus.gui import App
  self.app=App();self.app.update()
 def tearDown(self):self.app.destroy();self.env.stop();self.tmp.cleanup()
 def populated(self):
  a=self.app;a.proposal=Proposal('HDI',{'nome':'CLIENTE EXEMPLO','modelo':'VEÍCULO EXEMPLO'},[Offer('Auto',{'total':'2.000,00','dm':'200.000,00'})],[Payment('Auto','Cartão',10,'200,00')]);a._populate();a.update();return a
 def test_name_and_removed_controls(self):
  a=self.app;self.assertEqual(a.title(),APP_NAME);self.assertFalse(hasattr(a,'confirm'));self.assertFalse(hasattr(a,'reviewed'));self.assertFalse(hasattr(a,'xlsxbutton'));self.assertFalse(hasattr(a,'offerbox'));self.assertFalse(hasattr(a,'insbox'))
  def walk(w):
   for c in w.winfo_children():yield c;yield from walk(c)
  self.assertFalse(any(w.winfo_class()=='TCheckbutton' for w in walk(a)))
 def test_import_asks_company_then_starts_automatically(self):
  a=self.app;new=Path(self.tmp.name)/'nova.pdf'
  with patch('credplus.gui.filedialog.askopenfilename',return_value=str(new)),patch.object(a,'_choose_company',return_value='Mapfre') as choose,patch.object(a,'_import') as read:
   a._select();choose.assert_called_once_with(new);read.assert_called_once()
  self.assertEqual(a.proposal.corretora,'Mapfre');self.assertEqual(a.file,new)
 def test_new_selection_clears_data_and_returns_to_client_before_popup(self):
  a=self.populated();a.consultant.set('CONTATO ANTERIOR');a.phone.set('99999');a.preview_canvas.create_text(10,10,text='CLIENTE ANTERIOR');a.client_canvas.yview_moveto(1);a.tabs.select(a.payment_tab);a.update()
  def choose(path):
   self.assertEqual(a.tabs.select(),str(a.client_tab));self.assertFalse(a.proposal.values);self.assertFalse(a.proposal.offers);self.assertFalse(a.proposal.payments)
   self.assertEqual(a.client_canvas.yview()[0],0);self.assertFalse(a.client_vars['nome'].get());self.assertFalse(a.consultant.get());self.assertFalse(a.phone.get());self.assertFalse(a.preview_canvas.find_all())
   return 'Mapfre'
  with patch('credplus.gui.filedialog.askopenfilename',return_value='new.pdf'),patch.object(a,'_choose_company',side_effect=choose),patch.object(a,'_import') as start:
   a._select();start.assert_called_once()
 def test_cancel_company_popup_keeps_new_file_clean(self):
  a=self.populated();a.tabs.select(a.offer_tab);a.update()
  with patch('credplus.gui.filedialog.askopenfilename',return_value='new.pdf'),patch.object(a,'_choose_company',return_value=None):a._select()
  self.assertFalse(a.proposal.values);self.assertFalse(a.proposal.offers);self.assertFalse(a.proposal.payments);self.assertEqual(a.file,Path('new.pdf'));self.assertEqual(a.tabs.select(),str(a.client_tab))
 def test_select_from_preview_removes_render_and_shows_client_tab(self):
  a=self.populated();a.tabs.select(a.preview_tab);a.update();self.assertIsNotNone(a.preview_image)
  def choose(path):
   self.assertEqual(a.tabs.select(),str(a.client_tab));self.assertIsNone(a.preview_image);self.assertFalse(a.preview_canvas.find_all());self.assertFalse(a.proposal.values)
   return None
  with patch('credplus.gui.filedialog.askopenfilename',return_value='new.pdf'),patch.object(a,'_choose_company',side_effect=choose):a._select()
 def test_cancel_file_picker_preserves_current_document(self):
  a=self.populated();before=a.proposal
  with patch('credplus.gui.filedialog.askopenfilename',return_value=''):a._select()
  self.assertIs(a.proposal,before)
 def test_import_resets_before_worker_and_preserves_logo(self):
  a=self.populated();a.file=Path('new.pdf');a.tabs.select(a.offer_tab);a.update();marker=Path(self.tmp.name)/'marca.png';a.logo=marker
  class Worker:
   def __init__(self,*args,**kwargs):pass
   def start(self):pass
  with patch('credplus.gui.threading.Thread',Worker):a._import()
  self.assertFalse(a.proposal.values);self.assertFalse(a.proposal.offers);self.assertFalse(a.proposal.payments);self.assertEqual(a.tabs.select(),str(a.client_tab));self.assertEqual(a.logo,marker);self.assertTrue(a.busy)
 def test_pdf_and_png_export_without_confirmation(self):
  a=self.populated()
  for kind in ['pdf','png']:
   dest=Path(self.tmp.name)/('saida.'+kind)
   with patch('credplus.gui.filedialog.asksaveasfilename',return_value=str(dest)),patch('credplus.gui.messagebox.showinfo'),patch('credplus.gui.messagebox.showerror') as errors:
    a._export(kind);self.assertFalse(errors.called);self.assertTrue(dest.is_file())
 def test_edit_client_value_is_immediate(self):
  a=self.populated();a.client_vars['nome'].set('CLIENTE ALTERADO');a.update();self.assertEqual(a._collect().values['nome'],'CLIENTE ALTERADO')
 def test_new_document_clears_previous_fields_and_payments(self):
  a=self.populated();a.proposal=Proposal('Azul');a._populate();a.update();self.assertEqual(a.client_vars['nome'].get(),'');self.assertFalse(a.payment_tree.get_children());self.assertFalse(a.offer_tree.get_children())
 def test_preview_uses_generated_page(self):
  a=self.populated();a._preview();self.assertIsNotNone(a.preview_image);self.assertFalse(a.preview_dirty)
 def test_logo_persists_in_another_application_instance(self):
  a=self.app;source=Path(self.tmp.name)/'marca.png';Image.new('RGB',(200,80),'green').save(source)
  with patch('credplus.gui.filedialog.askopenfilename',return_value=str(source)):a._choose_logo()
  self.assertTrue(a.logo.is_file());source.unlink();a.destroy()
  from credplus.gui import App
  self.app=App();self.app.update();self.assertTrue(self.app.logo.is_file());self.assertIsNotNone(self.app.logo_image)
 def test_popup_lists_all_eight_and_no_option_choice(self):
  a=self.app
  def select():
   for popup in a.winfo_children():
    if popup.winfo_class()=='Toplevel':
     def walk(w):
      for c in w.winfo_children():yield c;yield from walk(c)
     radios=[w for w in walk(popup) if w.winfo_class()=='TRadiobutton'];self.assertEqual({w.cget('text') for w in radios},set(CORRETORAS));radios[0].invoke()
     for w in walk(popup):
      if w.winfo_class()=='TButton':w.invoke();return
  a.after(100,select);self.assertEqual(a._choose_company(Path('arquivo.pdf')),CORRETORAS[0])
 def test_offer_inline_edit_saves_without_confirmation(self):
  from types import SimpleNamespace
  a=self.populated();a.tabs.select(a.offer_tab);a.update()
  x,y,w,h=a.offer_tree.bbox('dm','#2');a._edit_cell(a.offer_tree,SimpleNamespace(x=x+5,y=y+h//2),'offer');a.update()
  editor=next(c for c in a.offer_tree.winfo_children() if c.winfo_class()=='TEntry')
  editor.delete(0,'end');editor.insert(0,'250.000,00');editor.event_generate('<<CommitCellEdit>>');a.update()
  self.assertEqual(a.proposal.offers[0].values['dm'],'250.000,00')
 def test_payment_inline_edit_saves_without_confirmation(self):
  from types import SimpleNamespace
  a=self.populated();a.tabs.select(a.payment_tab);a.update()
  x,y,w,h=a.payment_tree.bbox('0','#4');a._edit_cell(a.payment_tree,SimpleNamespace(x=x+5,y=y+h//2),'payment');a.update()
  editor=next(c for c in a.payment_tree.winfo_children() if c.winfo_class()=='TEntry')
  editor.delete(0,'end');editor.insert(0,'210,00');editor.event_generate('<<CommitCellEdit>>');a.update()
  self.assertEqual(a.proposal.payments[0].amount,'210,00')
 def test_edit_commit_does_not_depend_on_active_os_window(self):
  from types import SimpleNamespace
  a=self.populated();a.tabs.select(a.offer_tab);a.update()
  x,y,w,h=a.offer_tree.bbox('dm','#2');a.withdraw()
  a._edit_cell(a.offer_tree,SimpleNamespace(x=x+5,y=y+h//2),'offer');a.update()
  editor=next(c for c in a.offer_tree.winfo_children() if c.winfo_class()=='TEntry')
  self.assertNotEqual(a.focus_get(),editor)
  keys=editor.event_info('<<CommitCellEdit>>')
  self.assertTrue(any('Return' in key for key in keys));self.assertTrue(any('KP_Enter' in key for key in keys))
  editor.delete(0,'end');editor.insert(0,'350.000,00');editor.event_generate('<<CommitCellEdit>>');a.update()
  self.assertEqual(a.proposal.offers[0].values['dm'],'350.000,00');self.assertFalse(editor.winfo_exists())
 def test_edit_commit_on_focus_out(self):
  from types import SimpleNamespace
  a=self.populated();a.tabs.select(a.payment_tab);a.update()
  x,y,w,h=a.payment_tree.bbox('0','#4');a._edit_cell(a.payment_tree,SimpleNamespace(x=x+5,y=y+h//2),'payment');a.update()
  editor=next(c for c in a.payment_tree.winfo_children() if c.winfo_class()=='TEntry')
  editor.delete(0,'end');editor.insert(0,'220,00');editor.event_generate('<FocusOut>');a.update()
  self.assertEqual(a.proposal.payments[0].amount,'220,00');self.assertFalse(editor.winfo_exists())
 def test_original_pdf_is_never_overwritten(self):
  a=self.populated();source=Path(self.tmp.name)/'original.pdf';source.write_bytes(b'original');a.file=source
  with patch('credplus.gui.filedialog.asksaveasfilename',return_value=str(source)),patch('credplus.gui.messagebox.showerror') as error:a._export('pdf');self.assertTrue(error.called)
  self.assertEqual(source.read_bytes(),b'original')
