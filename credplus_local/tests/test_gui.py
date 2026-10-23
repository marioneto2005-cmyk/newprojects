"""Run with a desktop display, or a local Xvfb display in Linux CI."""
import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from credplus.core import FIELDS

@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requer tela gráfica')
class DesktopTests(unittest.TestCase):
 def setUp(self):
  from credplus.gui import App
  self.app=App();self.app.update()
 def tearDown(self):self.app.destroy()
 def test_confirm_then_edit_invalidates(self):
  a=self.app;a.tree.selection_set('nome');a.update();a.editor.insert('1.0','Cliente Exemplo');a.update();a._save_field();a.update()
  self.assertIn('nome',a.reviewed)
  a.tree.selection_set('nome');a.update();self.assertIn('nome',a.reviewed)
  a.editor.insert('end',' editado');a.update();self.assertNotIn('nome',a.reviewed)
 def test_switch_source_can_cancel_without_losing_values(self):
  a=self.app;a.values['nome']='Cliente Exemplo';a.insurer.set('HDI')
  with patch('credplus.gui.messagebox.askyesno',return_value=False):a._insurer_changed()
  self.assertEqual(a.insurer.get(),'Zurich');self.assertEqual(a.values['nome'],'Cliente Exemplo')
  a.insurer.set('Allianz')
  with patch('credplus.gui.messagebox.askyesno',return_value=True):a._insurer_changed()
  self.assertEqual(len(a.offerbox['values']),5);self.assertFalse(any(a.values.values()))
 def test_reset_clears_previous_source_evidence(self):
  a=self.app;a.candidates={'nome':{'evidence':'DADO DO CLIENTE ANTERIOR'}};a.values['nome']='Cliente anterior'
  a.tree.selection_set('nome');a.update();self.assertIn('ANTERIOR',a.evidence.get('1.0','end'))
  a._reset();a.update();self.assertEqual(a.evidence.get('1.0','end').strip(),'');self.assertIsNone(a.current);self.assertFalse(a.tree.selection())
 def test_export_blocked_before_review(self):
  a=self.app
  with patch('credplus.gui.filedialog.asksaveasfilename') as save,patch('credplus.gui.messagebox.showinfo') as info:
   a._export('pdf');self.assertTrue(info.called);self.assertFalse(save.called)
 def test_review_all_then_export_through_ui(self):
  a=self.app
  a.values.update(nome='CLIENTE EXEMPLO',modelo='VEÍCULO EXEMPLO',total='2.000,00')
  for f in FIELDS:
   a.tree.selection_set(f.key);a.update();a._save_field();a.update()
  self.assertEqual(len(a.reviewed),len(FIELDS));a.confirm.set(True)
  with tempfile.TemporaryDirectory() as tmp:
   for ext in ['pdf','xlsx']:
    dest=Path(tmp)/('resultado.'+ext)
    with patch('credplus.gui.filedialog.asksaveasfilename',return_value=str(dest)),patch('credplus.gui.messagebox.showinfo'),patch('credplus.gui.messagebox.showerror') as error:
     a._export(ext);self.assertFalse(error.called);self.assertTrue(dest.is_file())
