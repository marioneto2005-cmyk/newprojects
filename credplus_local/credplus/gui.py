"""Desktop UI. No HTTP clients, telemetry, or persisted customer projects."""
import os, queue, subprocess, sys, threading, tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from .core import FIELDS, FIELD_MAP, INSURERS, extract_pdf, export_pdf, export_xlsx, format_value

class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title('Credplus Local - revisão de propostas');self.geometry('1180x800');self.minsize(960,650)
        self.values={f.key:'' for f in FIELDS};self.candidates={};self.reviewed=set();self.file=None;self.current=None;self.busy=False;self.events=queue.Queue()
        self.confirm=tk.BooleanVar(value=False);self.insurer=tk.StringVar(value='Zurich');self.offer=tk.StringVar(value='Única')
        self.active_insurer='Zurich';self.active_offer='Única'
        self.consultant=tk.StringVar();self.phone=tk.StringVar();self.status=tk.StringVar(value='Selecione um PDF ou preencha os campos manualmente. Nenhum documento é enviado à internet.')
        style=ttk.Style(self);style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10),background='#ffffff',foreground='#183c34')
        style.configure('TButton',padding=6)
        style.configure('Treeview',rowheight=26,font=('Segoe UI',10),fieldbackground='#ffffff')
        style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),background='#e8f1ed')
        style.map('Treeview',background=[('selected','#006b58')],foreground=[('selected','#ffffff')])
        self._build();self.poll_id=self.after(100,self._poll)
        self.protocol('WM_DELETE_WINDOW',self._close)
    def _build(self):
        outer=ttk.Frame(self,padding=14);outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='SICOOB CREDPLUS - Preparar resumo para o cliente',font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(outer,text='1. Selecione o PDF e a opção  >  2. Confira e confirme cada campo  >  3. Gere PDF ou Excel',wraplength=1100).pack(anchor='w',pady=(4,10))
        bar=ttk.Frame(outer);bar.pack(fill='x')
        self.select=ttk.Button(bar,text='Selecionar PDF',command=self._select);self.select.pack(side='left')
        ttk.Button(bar,text='Abrir PDF original',command=self._open).pack(side='left',padx=5)
        self.pathlabel=ttk.Label(bar,text='Nenhum PDF selecionado',wraplength=650);self.pathlabel.pack(side='left',padx=8)
        controls=ttk.Frame(outer);controls.pack(fill='x',pady=10)
        ttk.Label(controls,text='Origem (somente uso interno):').pack(side='left')
        self.insbox=ttk.Combobox(controls,textvariable=self.insurer,values=list(INSURERS),state='readonly',width=16);self.insbox.pack(side='left',padx=5);self.insbox.bind('<<ComboboxSelected>>',self._insurer_changed)
        ttk.Label(controls,text='Opção:').pack(side='left')
        self.offerbox=ttk.Combobox(controls,textvariable=self.offer,values=INSURERS['Zurich'],state='readonly',width=32);self.offerbox.pack(side='left',padx=5);self.offerbox.bind('<<ComboboxSelected>>',self._offer_changed)
        self.analyze=ttk.Button(controls,text='Ler proposta',command=self._analyze);self.analyze.pack(side='left',padx=10)
        ttk.Button(controls,text='Limpar formulário',command=self._clear_prompt).pack(side='right')
        ttk.Label(outer,text='Origem e número da opção não saem no documento. Campos vazios significam não informado, nunca não contratado.',wraplength=1100).pack(anchor='w')
        pane=ttk.Panedwindow(outer,orient='horizontal');pane.pack(fill='both',expand=True,pady=8)
        left=ttk.Frame(pane);pane.add(left,weight=3)
        self.tree=ttk.Treeview(left,columns=('field','value','state'),show='headings',selectmode='browse')
        for col,label,width in [('field','Campo',245),('value','Valor para o cliente',290),('state','Conferência',130)]:self.tree.heading(col,text=label);self.tree.column(col,width=width,minwidth=80)
        scroll=ttk.Scrollbar(left,orient='vertical',command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self._selected)
        self.tree.tag_configure('pending',background='#fff4dc');self.tree.tag_configure('done',background='#e7f4ed')
        right=ttk.Frame(pane,padding=(12,0));pane.add(right,weight=1)
        self.field_label=ttk.Label(right,text='Selecione um campo',font=('Segoe UI',11,'bold'),wraplength=280);self.field_label.pack(anchor='w')
        self.editor=tk.Text(right,height=7,width=30,wrap='word');self.editor.pack(fill='x',pady=8);self.editor.bind('<<Modified>>',self._editing)
        self.savefield=ttk.Button(right,text='Confirmar valor / ausência',command=self._save_field);self.savefield.pack(fill='x')
        ttk.Label(right,text='Trecho localizado no documento (uso interno):').pack(anchor='w',pady=(15,3))
        self.evidence=tk.Text(right,height=9,width=30,wrap='word',state='disabled',background='#f1f3f4');self.evidence.pack(fill='both',expand=True)
        ttk.Label(right,text='OCR pode trocar letras, dígitos e colunas. Compare nomes, CPF, chassi, coberturas e valores com o PDF original.',wraplength=280).pack(anchor='w',pady=10)
        contacts=ttk.Frame(outer);contacts.pack(fill='x',pady=5)
        ttk.Label(contacts,text='Consultor / gerente:').pack(side='left');ttk.Entry(contacts,textvariable=self.consultant,width=34).pack(side='left',padx=5)
        ttk.Label(contacts,text='WhatsApp:').pack(side='left',padx=(15,0));ttk.Entry(contacts,textvariable=self.phone,width=24).pack(side='left',padx=5)
        ttk.Checkbutton(outer,text='Conferi todos os campos com o PDF e reconheço os campos não informados. Autorizo a geração deste resumo.',variable=self.confirm).pack(anchor='w',pady=7)
        bottom=ttk.Frame(outer);bottom.pack(fill='x')
        self.pdfbutton=ttk.Button(bottom,text='Gerar PDF para o cliente',command=lambda:self._export('pdf'));self.pdfbutton.pack(side='left')
        self.xlsxbutton=ttk.Button(bottom,text='Gerar Excel no modelo',command=lambda:self._export('xlsx'));self.xlsxbutton.pack(side='left',padx=8)
        ttk.Label(outer,textvariable=self.status,wraplength=1100).pack(anchor='w',pady=(8,0))
        self._refresh()
    def _editing(self,event=None):
        if self.editor.edit_modified():
            if self.current:self.reviewed.discard(self.current)
            self.confirm.set(False);self.editor.edit_modified(False)
    def _refresh(self):
        for f in FIELDS:
            value=self.values.get(f.key,'');done=f.key in self.reviewed
            state='Confirmado' if done else ('Conferir leitura' if value else self.candidates.get(f.key,{}).get('state','Não localizado'))
            data=(f'{f.section} - {f.label}',value or 'Não informado',state)
            if self.tree.exists(f.key):self.tree.item(f.key,values=data,tags=('done' if done else 'pending',))
            else:self.tree.insert('','end',iid=f.key,values=data,tags=('pending',))
    def _selected(self,event=None):
        selection=self.tree.selection()
        if not selection:return
        self.current=selection[0];f=FIELD_MAP[self.current]
        self.field_label.config(text=f.label+(' (R$ 1.234,56)' if f.kind=='money' else ''))
        self.editor.delete('1.0','end');self.editor.insert('1.0',self.values[self.current]);self.editor.edit_modified(False)
        # Inserting text fires a queued modification event; the flag is cleared above.
        self.evidence.config(state='normal');self.evidence.delete('1.0','end');self.evidence.insert('1.0',self.candidates.get(self.current,{}).get('evidence','Não localizado automaticamente. Confira o PDF e preencha ou confirme a ausência.'));self.evidence.config(state='disabled')
    def _save_field(self):
        if self.busy or not self.current:return
        key=self.current
        try:self.values[key]=format_value(FIELD_MAP[key],self.editor.get('1.0','end').strip())
        except ValueError as e:messagebox.showerror('Confira o campo',str(e));return
        self.reviewed.add(key);self.confirm.set(False);self._refresh()
        idx=next(i for i,f in enumerate(FIELDS) if f.key==key)
        if idx+1<len(FIELDS):self.tree.selection_set(FIELDS[idx+1].key);self.tree.see(FIELDS[idx+1].key)
        self.status.set(f'{len(self.reviewed)}/{len(FIELDS)} campos conferidos. Campos ausentes também precisam ser confirmados.')
    def _reset(self):
        self.values={f.key:'' for f in FIELDS};self.candidates={};self.reviewed.clear();self.confirm.set(False);self.current=None
        self.tree.selection_remove(*self.tree.selection());self.field_label.config(text='Selecione um campo')
        self.editor.delete('1.0','end');self.editor.edit_modified(False)
        self.evidence.config(state='normal');self.evidence.delete('1.0','end');self.evidence.config(state='disabled')
        self._refresh()
    def _discard_ok(self):
        return not (self.reviewed or any(self.values.values())) or messagebox.askyesno('Descartar formulário atual?','A troca descarta os dados em memória. Deseja continuar?')
    def _select(self):
        if self.busy:return
        if not self._discard_ok():return
        name=filedialog.askopenfilename(filetypes=[('Documento PDF','*.pdf')])
        if name:self._reset();self.file=Path(name);self.pathlabel.config(text=self.file.name);self.status.set('Selecione a origem e a opção exatas antes de ler o PDF.')
    def _open(self):
        if not self.file:return
        try:
            if os.name=='nt':os.startfile(self.file)
            else:subprocess.Popen(['open' if sys.platform=='darwin' else 'xdg-open',str(self.file)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except OSError:messagebox.showerror('Abrir original','Abra o PDF pelo explorador de arquivos.')
    def _insurer_changed(self,event=None):
        if not self._discard_ok():
            self.insurer.set(self.active_insurer);return
        self._reset();options=INSURERS[self.insurer.get()];self.offerbox.config(values=options);self.offer.set(options[0])
        self.active_insurer=self.insurer.get();self.active_offer=self.offer.get()
    def _offer_changed(self,event=None):
        if not self._discard_ok():
            self.offer.set(self.active_offer);return
        self._reset();self.active_offer=self.offer.get()
    def _clear_prompt(self):
        if not self.busy and self._discard_ok():self._reset()
    def _analyze(self):
        if self.busy:return
        if not self.file:messagebox.showinfo('Selecione o PDF','Selecione um PDF antes de iniciar a leitura.');return
        if not self._discard_ok():return
        self._reset();self._set_busy(True);path=self.file;insurer=self.insurer.get();offer=INSURERS[insurer].index(self.offer.get())+1
        def work():
            try:self.events.put(('result',extract_pdf(path,insurer,offer,progress=lambda s:self.events.put(('progress',s)))))
            except Exception as e:self.events.put(('error',str(e)))
        threading.Thread(target=work,daemon=True).start()
    def _set_busy(self,value):
        self.busy=value
        for widget in [self.select,self.analyze,self.pdfbutton,self.xlsxbutton,self.savefield]:widget.config(state='disabled' if value else 'normal')
        self.editor.config(state='disabled' if value else 'normal')
        for widget in [self.insbox,self.offerbox]:widget.config(state='disabled' if value else 'readonly')
    def _poll(self):
        try:
            while True:
                kind,payload=self.events.get_nowait()
                if kind=='progress':self.status.set(payload)
                elif kind=='error':self._set_busy(False);self.status.set('A leitura não foi concluída. O preenchimento manual continua disponível.');messagebox.showerror('Leitura não concluída',payload)
                elif kind=='result':
                    self._set_busy(False);self.candidates=payload['fields'];self.values={f.key:self.candidates.get(f.key,{}).get('display','') for f in FIELDS};self._refresh()
                    count=sum(bool(v) for v in self.values.values());self.status.set(f'{payload["pages"]} páginas processadas localmente; {count}/{len(FIELDS)} campos candidatos. Confira todos antes de emitir.');self.tree.selection_set(FIELDS[0].key)
        except queue.Empty:pass
        self.poll_id=self.after(100,self._poll)
    def _export(self,extension):
        if self.busy:return
        if len(self.reviewed)!=len(FIELDS) or not self.confirm.get():messagebox.showinfo('Conferência obrigatória','Confirme cada campo (inclusive ausências) e marque a conferência final antes de gerar.');return
        path=filedialog.asksaveasfilename(defaultextension='.'+extension,initialfile='Resumo_Seguro_Auto.'+extension,filetypes=[(extension.upper(),'*.'+extension)])
        if not path:return
        if self.file and Path(path).resolve()==self.file.resolve():messagebox.showerror('Escolha outro nome','O PDF original não pode ser sobrescrito.');return
        try:
            (export_pdf if extension=='pdf' else export_xlsx)(path,self.values,self.consultant.get(),self.phone.get())
            self.status.set('Documento gerado. Confira o arquivo final antes de enviar ao cliente.');messagebox.showinfo('Documento gerado','Arquivo salvo. Confira o resultado antes de enviar ao cliente.')
        except Exception as e:messagebox.showerror('Não foi possível gerar',str(e))
    def destroy(self):
        if getattr(self,'poll_id',None):
            self.after_cancel(self.poll_id);self.poll_id=None
        super().destroy()
    def _close(self):
        if self.busy and not messagebox.askyesno('Leitura em andamento','Sair e interromper a leitura local?'):return
        self.destroy()

def main():App().mainloop()
