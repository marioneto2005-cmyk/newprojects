"""Verify real viewport movement, focus/value preservation and tab isolation."""
import os,tempfile,unittest
from types import SimpleNamespace as Event
from unittest.mock import patch
from pathlib import Path
from credplus.proposal import Proposal,Offer,Payment

@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requer tela gráfica')
class WheelTests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'PROPOSTA_SETTINGS_DIR':str(Path(self.tmp.name)/'settings')});self.env.start()
    from credplus.gui import App
    self.app=App();self.app.update();self.app._wheel.system='win32'
 def tearDown(self):self.app.destroy();self.env.stop();self.tmp.cleanup()
 def wheel(self,widget,delta=-120,state=0,num=None):
    result=self.app._wheel.handle(Event(widget=widget,delta=delta,state=state,num=num));self.app.update();return result
 def field(self,key='nome'):
    def walk(widget):
     for child in widget.winfo_children():yield child;yield from walk(child)
    return next(w for w in walk(self.app.client_tab) if w.winfo_class()=='TEntry' and str(w.cget('textvariable'))==str(self.app.client_vars[key]))
 def populate(self):
    a=self.app;a.proposal=Proposal('HDI',{'nome':'CLIENTE EXEMPLO'},[Offer('Auto',{'total':'1.000,00'})],[Payment('Auto','Cartão',n,'100,00') for n in range(1,41)]);a._populate();a.update()
 def test_client_scrolls_down_and_up_while_over_entry(self):
    a=self.app;entry=self.field();self.assertEqual(a.client_canvas.yview()[0],0)
    self.assertEqual(self.wheel(entry),'break');self.assertGreater(a.client_canvas.yview()[0],0)
    self.wheel(entry,120);self.assertEqual(a.client_canvas.yview()[0],0)
 def test_real_tk_wheel_event_on_entry_reaches_canvas(self):
    a=self.app;entry=self.field();entry.event_generate('<MouseWheel>',delta=-120);a.update();self.assertGreater(a.client_canvas.yview()[0],0)
 def test_wheel_does_not_change_field_text_or_focus(self):
    a=self.app;entry=self.field();a.client_vars['nome'].set('CLIENTE EXEMPLO');entry.focus_force();a.update();before=a.focus_get()
    self.wheel(entry);self.assertEqual(a.client_vars['nome'].get(),'CLIENTE EXEMPLO');self.assertIs(a.focus_get(),before)
 def test_fractional_windows_delta_accumulates(self):
    a=self.app;entry=self.field()
    for _ in range(3):self.wheel(entry,-30)
    self.assertEqual(a.client_canvas.yview()[0],0)
    self.wheel(entry,-30);self.assertGreater(a.client_canvas.yview()[0],0)
 def test_very_small_delta_not_lost_to_floating_point(self):
    a=self.app;entry=self.field()
    for _ in range(120):self.wheel(entry,-1)
    self.assertGreater(a.client_canvas.yview()[0],0)
 def test_linux_buttons_and_macos_delta(self):
    a=self.app;entry=self.field();self.wheel(entry,num=5);self.assertGreater(a.client_canvas.yview()[0],0);self.wheel(entry,num=4);self.assertEqual(a.client_canvas.yview()[0],0)
    a._wheel.system='aqua';self.wheel(entry,-1);self.assertGreater(a.client_canvas.yview()[0],0)
 def test_options_tree_scrolls_exactly_once(self):
    self.populate();a=self.app;a.tabs.select(a.offer_tab);a.update();view=a.offer_tree
    view.yview_scroll(3,'units');expected=view.yview()[0];self.assertGreater(expected,0);view.yview_moveto(0)
    view.event_generate('<MouseWheel>',delta=-120);a.update();self.assertAlmostEqual(view.yview()[0],expected)
 def test_payment_tree_scrolls(self):
    self.populate();a=self.app;a.tabs.select(a.payment_tab);a.update();self.wheel(a.payment_tree);self.assertGreater(a.payment_tree.yview()[0],0)
 def test_shift_wheel_scrolls_payment_columns_horizontally(self):
    self.populate();a=self.app;a.tabs.select(a.payment_tab);a.update()
    for col in a.payment_columns:a.payment_tree.column(col,width=230,stretch=False)
    a.update();self.assertEqual(a.payment_tree.xview()[0],0);self.wheel(a.payment_tree,state=1);self.assertGreater(a.payment_tree.xview()[0],0)
 def test_preview_canvas_scrolls(self):
    a=self.app;a.tabs.select(a.preview_tab)
    with patch.object(a,'_preview'):a.update()
    a.preview_canvas.create_rectangle(0,0,800,6000);a.preview_canvas.configure(scrollregion=(0,0,800,6000));self.wheel(a.preview_canvas);self.assertGreater(a.preview_canvas.yview()[0],0)
 def test_canvas_without_overflow_does_not_move(self):
    a=self.app;a.tabs.select(a.preview_tab)
    with patch.object(a,'_preview'):a.update()
    a.preview_canvas.configure(scrollregion=(0,0,100,100));a.update();before=a.preview_canvas.yview();self.wheel(a.preview_canvas);self.assertEqual(a.preview_canvas.yview(),before)
 def test_hidden_tab_and_popup_do_not_scroll_current_tab(self):
    a=self.app;entry=self.field();a.tabs.select(a.offer_tab);a.update();before=a.client_canvas.yview()
    self.assertIsNone(self.wheel(entry));self.assertEqual(a.client_canvas.yview(),before)
    import tkinter as tk
    pop=tk.Toplevel(a);outside=tk.Entry(pop);outside.pack();a.update();self.assertIsNone(self.wheel(outside));pop.destroy()
 def test_new_document_clears_partial_wheel_movement(self):
    a=self.app;self.wheel(self.field(),-90);a._clear_import(Path('new.pdf'));a.update();self.wheel(self.field(),-30);self.assertEqual(a.client_canvas.yview()[0],0)
 def test_dynamic_cell_editor_saves_then_scrolls_table(self):
    self.populate();a=self.app;a.tabs.select(a.payment_tab);a.update();view=a.payment_tree
    x,y,w,h=view.bbox('0','#4');a._edit_cell(view,Event(x=x+5,y=y+h//2),'payment');a.update()
    editor=next(c for c in view.winfo_children() if c.winfo_class()=='TEntry');self.assertIn(a._wheel.tag,editor.bindtags())
    editor.delete(0,'end');editor.insert(0,'125,00');self.wheel(editor)
    self.assertEqual(a.proposal.payments[0].amount,'125,00');self.assertFalse(editor.winfo_exists());self.assertGreater(view.yview()[0],0)
