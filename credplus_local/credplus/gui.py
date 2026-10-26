"""Desktop application: automatic import, inline editing, persistent branding, PDF/PNG."""
import copy,os,queue,subprocess,sys,threading,tkinter as tk
from pathlib import Path
from tkinter import ttk,filedialog,messagebox,simpledialog
from PIL import Image,ImageTk
import fitz
from . import __version__,APP_NAME
from .core import FIELDS,FIELD_MAP,format_value,ASSETS
from .proposal import Proposal,Offer,Payment,CORRETORAS,COVER_KEYS,GLASS_KEYS,build_proposal
from .document import export_document,pdf_bytes,LABELS
from .settings import saved_logo,save_logo,remove_logo
from .windows_icons import set_application_id,set_window_icons,release_window_icons

BG='#f3f6f8';WHITE='#ffffff';INK='#19323f';MUTED='#6c808a';GREEN='#087763';NAVY='#112e3b'

class App(tk.Tk):
    def __init__(self):
        set_application_id(__version__)
        super().__init__();self._native_icon_handles=[]
        self._app_icon=tk.PhotoImage(file=str(ASSETS/'quote_document.png'));self.iconphoto(True,self._app_icon)
        if os.name=='nt':
            self.iconbitmap(str(ASSETS/'quote_document.ico'));self.iconbitmap(default=str(ASSETS/'quote_document.ico'))
        self.title(APP_NAME);self.geometry('1380x880');self.minsize(1120,740);self.configure(bg=BG)
        self.file=None;self.proposal=Proposal('');self.values=self.proposal.values;self.busy=False;self.events=queue.Queue();self.logo=saved_logo();self.editor_popup=None
        self.consultant=tk.StringVar();self.phone=tk.StringVar();self.client_vars={};self.loading_fields=False;self.preview_image=None;self.logo_image=None;self.preview_dirty=True
        self._style();self._build();self._refresh_logo()
        self._native_icon_handles=set_window_icons(self,ASSETS/'quote_document.ico')
        self.poll_id=self.after(100,self._poll);self.protocol('WM_DELETE_WINDOW',self._close)
    def _style(self):
        s=ttk.Style(self);s.theme_use('clam')
        s.configure('.',font=('Segoe UI',10),background=BG,foreground=INK)
        s.configure('TFrame',background=BG);s.configure('Card.TFrame',background=WHITE)
        s.configure('TLabel',background=BG);s.configure('Card.TLabel',background=WHITE)
        s.configure('Muted.TLabel',foreground=MUTED);s.configure('TButton',padding=(13,9),background=WHITE,borderwidth=0)
        s.map('TButton',background=[('active','#e5efeb')])
        s.configure('Primary.TButton',background=GREEN,foreground=WHITE,font=('Segoe UI',10,'bold'))
        s.map('Primary.TButton',background=[('active','#065f50'),('disabled','#afc2bb')],foreground=[('disabled','#f1f5f3')])
        s.configure('TEntry',padding=7,fieldbackground=WHITE,bordercolor='#dce4e8',lightcolor='#dce4e8',darkcolor='#dce4e8')
        s.configure('TNotebook',background=BG,borderwidth=0);s.configure('TNotebook.Tab',padding=(18,10),background='#e8eef1',font=('Segoe UI',10,'bold'))
        s.map('TNotebook.Tab',background=[('selected',WHITE)],foreground=[('selected',GREEN)])
        s.configure('Treeview',rowheight=36,font=('Segoe UI',10),fieldbackground=WHITE,background=WHITE,borderwidth=0)
        s.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),background='#e8f0f0',padding=9)
        s.map('Treeview',background=[('selected','#d6eee7')],foreground=[('selected',INK)])
    def _build(self):
        header=ttk.Frame(self,padding=(24,18));header.pack(fill='x')
        title=ttk.Frame(header);title.pack(side='left')
        ttk.Label(title,text='Proposta Seguro Auto - Segurado',font=('Segoe UI',20,'bold')).pack(anchor='w')
        ttk.Label(title,text='v'+__version__+'  /  Propostas visuais em PDF e PNG',style='Muted.TLabel').pack(anchor='w',pady=(4,0))
        brand=ttk.Frame(header);brand.pack(side='right')
        self.logo_label=ttk.Label(brand,text='Sua logomarca',width=20,anchor='center');self.logo_label.pack(side='left',padx=12)
        ttk.Button(brand,text='Alterar logomarca',command=self._choose_logo).pack(side='left')
        ttk.Button(brand,text='Remover',command=self._remove_logo).pack(side='left',padx=(5,0))
        body=ttk.Frame(self,padding=(20,0,20,18));body.pack(fill='both',expand=True)
        side=tk.Frame(body,bg=NAVY,width=245);side.pack(side='left',fill='y',padx=(0,18));side.pack_propagate(False)
        tk.Label(side,text='SUA PROPOSTA',bg=NAVY,fg='#9bd7c8',font=('Segoe UI',11,'bold'),anchor='w').pack(fill='x',padx=20,pady=(24,12))
        self.file_label=tk.Label(side,text='Nenhum documento\nimportado',bg=NAVY,fg=WHITE,font=('Segoe UI',12,'bold'),wraplength=200,justify='left',anchor='w');self.file_label.pack(fill='x',padx=20)
        self.company_label=tk.Label(side,text='',bg=NAVY,fg='#b2c5ce',font=('Segoe UI',10),anchor='w');self.company_label.pack(fill='x',padx=20,pady=(8,18))
        self.select_button=ttk.Button(side,text='Importar proposta PDF',style='Primary.TButton',command=self._select);self.select_button.pack(fill='x',padx=16,pady=4)
        self.reread_button=ttk.Button(side,text='Ler novamente',command=self._reread);self.reread_button.pack(fill='x',padx=16,pady=4)
        ttk.Button(side,text='Abrir documento original',command=self._open).pack(fill='x',padx=16,pady=4)
        self.progress=ttk.Progressbar(side,mode='indeterminate')
        self.activity=tk.Label(side,text='',bg=NAVY,fg='#b2c5ce',font=('Segoe UI',9),wraplength=200,justify='left');self.activity.pack(fill='x',padx=20)
        self.stats_label=tk.Label(side,text='',bg=NAVY,fg='#9bd7c8',font=('Segoe UI',11,'bold'),justify='left',anchor='w');self.stats_label.pack(fill='x',padx=20,pady=18)
        exports=tk.Frame(side,bg=NAVY);exports.pack(side='bottom',fill='x',padx=16,pady=22)
        self.pngbutton=ttk.Button(exports,text='Gerar PNG',command=lambda:self._export('png'));self.pngbutton.pack(fill='x',pady=5)
        self.pdfbutton=ttk.Button(exports,text='Gerar PDF',style='Primary.TButton',command=lambda:self._export('pdf'));self.pdfbutton.pack(fill='x',pady=5)
        main=ttk.Frame(body);main.pack(side='left',fill='both',expand=True)
        contact=ttk.Frame(main,style='Card.TFrame',padding=14);contact.pack(fill='x',pady=(0,14))
        ttk.Label(contact,text='Seu atendimento',style='Card.TLabel',font=('Segoe UI',10,'bold')).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,9))
        ttk.Label(contact,text='Consultor / gerente',style='Card.TLabel').grid(row=1,column=0,sticky='w')
        ttk.Label(contact,text='WhatsApp',style='Card.TLabel').grid(row=1,column=1,sticky='w',padx=(18,0))
        ttk.Entry(contact,textvariable=self.consultant).grid(row=2,column=0,sticky='ew',pady=(5,0))
        ttk.Entry(contact,textvariable=self.phone).grid(row=2,column=1,sticky='ew',padx=(18,0),pady=(5,0))
        contact.columnconfigure(0,weight=1);contact.columnconfigure(1,weight=1)
        for var in (self.consultant,self.phone):var.trace_add('write',lambda *_:self._dirty())
        self.tabs=ttk.Notebook(main);self.tabs.pack(fill='both',expand=True)
        self.client_tab=ttk.Frame(self.tabs,style='Card.TFrame');self.offer_tab=ttk.Frame(self.tabs,style='Card.TFrame',padding=12);self.payment_tab=ttk.Frame(self.tabs,style='Card.TFrame',padding=12);self.preview_tab=ttk.Frame(self.tabs,style='Card.TFrame')
        for frame,label in [(self.client_tab,'Cliente e veículo'),(self.offer_tab,'Opções e coberturas'),(self.payment_tab,'Formas de pagamento'),(self.preview_tab,'Prévia do documento')]:self.tabs.add(frame,text=label)
        self.tabs.bind('<<NotebookTabChanged>>',self._tab_changed)
        self._build_fields()
        offerbar=ttk.Frame(self.offer_tab,style='Card.TFrame');offerbar.pack(fill='x',pady=(0,10))
        ttk.Label(offerbar,text='Todas as opções do documento',style='Card.TLabel',font=('Segoe UI',11,'bold')).pack(side='left')
        ttk.Button(offerbar,text='+ Opção',command=self._add_offer).pack(side='right')
        self.offer_tree=self._tree(self.offer_tab,['field'],['Cobertura / condição']);self.offer_tree.bind('<Double-1>',lambda e:self._edit_cell(self.offer_tree,e,'offer'))
        paybar=ttk.Frame(self.payment_tab,style='Card.TFrame');paybar.pack(fill='x',pady=(0,10))
        ttk.Label(paybar,text='Parcelas por modalidade e opção',style='Card.TLabel',font=('Segoe UI',11,'bold')).pack(side='left')
        ttk.Button(paybar,text='Excluir linha',command=self._delete_payment).pack(side='right',padx=4)
        ttk.Button(paybar,text='+ Pagamento',command=self._add_payment).pack(side='right')
        self.payment_columns=['offer','mode','installments','amount','entry','total','interest','condition']
        self.payment_tree=self._tree(self.payment_tab,self.payment_columns,['Opção','Modalidade','Parcelas','Valor / parcela','Entrada','Total','Juros','Condições']);self.payment_tree.bind('<Double-1>',lambda e:self._edit_cell(self.payment_tree,e,'payment'))
        previewbar=ttk.Frame(self.preview_tab,style='Card.TFrame',padding=10);previewbar.pack(fill='x')
        ttk.Button(previewbar,text='Atualizar prévia',command=self._preview).pack(side='left')
        self.preview_canvas=tk.Canvas(self.preview_tab,bg='#e5ecee',highlightthickness=0)
        scroll=ttk.Scrollbar(self.preview_tab,orient='vertical',command=self.preview_canvas.yview);scroll.pack(side='right',fill='y');self.preview_canvas.configure(yscrollcommand=scroll.set);self.preview_canvas.pack(fill='both',expand=True)
    def _tree(self,parent,cols,labels):
        holder=ttk.Frame(parent,style='Card.TFrame');holder.pack(fill='both',expand=True)
        tree=ttk.Treeview(holder,columns=cols,show='headings',selectmode='browse')
        for key,label in zip(cols,labels):tree.heading(key,text=label);tree.column(key,width=150,minwidth=80,stretch=True)
        ys=ttk.Scrollbar(holder,command=tree.yview);xs=ttk.Scrollbar(holder,orient='horizontal',command=tree.xview)
        tree.configure(yscrollcommand=ys.set,xscrollcommand=xs.set);ys.pack(side='right',fill='y');xs.pack(side='bottom',fill='x');tree.pack(fill='both',expand=True)
        return tree
    def _build_fields(self):
        canvas=tk.Canvas(self.client_tab,bg=WHITE,highlightthickness=0);self.client_canvas=canvas;ys=ttk.Scrollbar(self.client_tab,command=canvas.yview);ys.pack(side='right',fill='y');canvas.configure(yscrollcommand=ys.set);canvas.pack(fill='both',expand=True)
        inside=ttk.Frame(canvas,style='Card.TFrame',padding=18);win=canvas.create_window((0,0),window=inside,anchor='nw')
        inside.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(win,width=e.width))
        fields=[f for f in FIELDS if f.section in ('Segurado','Perfil','Veículo') or f.kind=='supplement']
        order={'Segurado':0,'Perfil':1,'Veículo':2}
        fields.sort(key=lambda f:order.get(f.section,3))
        section=None;row=0;position=0
        for f in fields:
            if f.section!=section:
                if position%2:row+=2
                section=f.section;position=0
                ttk.Label(inside,text=section.upper(),style='Card.TLabel',foreground=GREEN,font=('Segoe UI',10,'bold')).grid(row=row,column=0,columnspan=2,sticky='w',pady=(14,9));row+=1
            column=position%2
            ttk.Label(inside,text=f.label,style='Card.TLabel',font=('Segoe UI',9)).grid(row=row,column=column,sticky='w',padx=(0,16),pady=(0,3))
            var=tk.StringVar();self.client_vars[f.key]=var;var.trace_add('write',lambda *_,key=f.key:self._field_changed(key))
            entry=ttk.Entry(inside,textvariable=var);entry.grid(row=row+1,column=column,sticky='ew',padx=(0,16),pady=(0,13))
            position+=1
            if position%2==0:row+=2
        inside.columnconfigure(0,weight=1);inside.columnconfigure(1,weight=1)
    def _field_changed(self,key):
        if not self.loading_fields:self.proposal.values[key]=self.client_vars[key].get();self._dirty()
    def _dirty(self):self.preview_dirty=True
    def _choose_company(self,path):
        popup=tk.Toplevel(self);popup.title('Corretora');popup.transient(self);popup.resizable(False,False);popup.grab_set()
        frame=ttk.Frame(popup,padding=24);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Qual é a Corretora?',font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(frame,text=path.name,style='Muted.TLabel',wraplength=400).pack(anchor='w',pady=(6,16))
        selected=tk.StringVar();result=[]
        suggested={'ALRIO':'Aliro','ALIRO':'Aliro','TOKIO':'Tokio Marine','YELUM':'Yelum','PORTO':'Porto Seguro'}
        for name in CORRETORAS:
            if name.upper() in path.stem.upper():selected.set(name)
        for key,value in suggested.items():
            if key in path.stem.upper():selected.set(value)
        grid=ttk.Frame(frame);grid.pack(fill='x')
        for i,name in enumerate(CORRETORAS):ttk.Radiobutton(grid,text=name,value=name,variable=selected).grid(row=i//2,column=i%2,sticky='w',padx=(0,50),pady=8)
        def proceed():
            if selected.get():result.append(selected.get());popup.destroy()
        ttk.Button(frame,text='Importar proposta',style='Primary.TButton',command=proceed).pack(fill='x',pady=(20,0))
        popup.bind('<Return>',lambda e:proceed());popup.update_idletasks()
        x=self.winfo_rootx()+max(0,(self.winfo_width()-popup.winfo_reqwidth())//2);y=self.winfo_rooty()+max(0,(self.winfo_height()-popup.winfo_reqheight())//2)
        popup.geometry(f'+{x}+{y}');self.wait_window(popup)
        return result[0] if result else None
    def _clear_import(self,path,company=''):
        # Remove active cell editors before replacing their underlying document.
        for tree in (self.offer_tree,self.payment_tree):
            for widget in tree.winfo_children():
                if widget.winfo_class()=='TEntry':widget.unbind('<FocusOut>');widget.destroy()
        self.file=path;self.proposal=Proposal(company)
        self.consultant.set('');self.phone.set('')
        self.preview_canvas.delete('all');self.preview_image=None
        self.preview_canvas.configure(scrollregion=(0,0,0,0));self.preview_canvas.yview_moveto(0);self.preview_canvas.xview_moveto(0)
        self._populate();self.tabs.select(self.client_tab);self.client_canvas.yview_moveto(0)
    def _select(self):
        if self.busy:return
        name=filedialog.askopenfilename(filetypes=[('Documento PDF','*.pdf')])
        if not name:return
        path=Path(name)
        # A chosen file starts a clean document, even if the company popup is cancelled.
        self._clear_import(path)
        company=self._choose_company(path)
        if not company:return
        self.proposal.corretora=company;self._import()
    def _reread(self):
        if not self.file or self.busy:return
        if not self.proposal.corretora:
            company=self._choose_company(self.file)
            if not company:return
            self.proposal.corretora=company
        self._import()
    def _import(self):
        path=self.file;company=self.proposal.corretora
        self._clear_import(path,company);self._set_busy(True)
        def work():
            try:self.events.put(('result',build_proposal(path,company,lambda s:self.events.put(('progress',s)))))
            except Exception as e:self.events.put(('error',str(e)))
        threading.Thread(target=work,daemon=True).start()
    def _set_busy(self,value):
        self.busy=value
        for w in [self.select_button,self.reread_button,self.pdfbutton,self.pngbutton]:w.configure(state='disabled' if value else 'normal')
        if value:self.progress.pack(fill='x',padx=20,pady=(18,5),before=self.activity);self.progress.start(15);self.activity.configure(text='Lendo o documento...')
        else:self.progress.stop();self.progress.pack_forget();self.activity.configure(text='')
    def _poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='progress':self.activity.configure(text=value)
                elif kind=='error':self._set_busy(False);messagebox.showerror('Não foi possível importar',value)
                elif kind=='result':self._set_busy(False);self.proposal=value;self._populate()
        except queue.Empty:pass
        self.poll_id=self.after(100,self._poll)
    def _populate(self):
        self.values=self.proposal.values;self.loading_fields=True
        for key,var in self.client_vars.items():var.set(self.values.get(key,''))
        self.loading_fields=False
        self.file_label.configure(text=self.file.name if self.file else 'Nenhum documento\nimportado');self.company_label.configure(text='Corretora: '+self.proposal.corretora if self.proposal.corretora else '')
        self.stats_label.configure(text=f'{len(self.proposal.offers)} opções\n{len(self.proposal.payments)} planos de pagamento' if self.proposal.offers else '')
        self._refresh_tables();self._dirty()
    def _refresh_tables(self):
        cols=['field']+[f'o{i}' for i in range(len(self.proposal.offers))];self.offer_tree.configure(columns=cols)
        self.offer_tree.heading('field',text='Cobertura / condição');self.offer_tree.column('field',width=245,minwidth=180)
        for i,offer in enumerate(self.proposal.offers):self.offer_tree.heading(f'o{i}',text=offer.name);self.offer_tree.column(f'o{i}',width=160,minwidth=120)
        self.offer_tree.delete(*self.offer_tree.get_children())
        keys=list(dict.fromkeys((*COVER_KEYS,*GLASS_KEYS,'total'))) if self.proposal.offers else []
        for key in keys:self.offer_tree.insert('','end',iid=key,values=[LABELS.get(key,key)]+[o.values.get(key,'') for o in self.proposal.offers])
        self.payment_tree.delete(*self.payment_tree.get_children())
        for i,row in enumerate(self.proposal.payments):self.payment_tree.insert('','end',iid=str(i),values=[getattr(row,k) for k in self.payment_columns])
    def _edit_cell(self,tree,event,kind):
        if self.busy:return
        row=tree.identify_row(event.y);column=tree.identify_column(event.x)
        if not row or not column:return
        index=int(column[1:])-1
        if kind=='offer' and index==0:return
        box=tree.bbox(row,column)
        if not box:return
        editor=ttk.Entry(tree);editor.place(x=box[0],y=box[1],width=box[2],height=box[3]);editor.insert(0,tree.item(row,'values')[index]);editor.focus_set();editor.select_range(0,'end')
        saving={'active':False}
        def save(event=None):
            if saving['active'] or not editor.winfo_exists():return
            saving['active']=True
            try:
                value=editor.get().strip()
                if kind=='offer':
                    if row in FIELD_MAP:value=format_value(FIELD_MAP[row],value)
                    self.proposal.offers[index-1].values[row]=value
                else:
                    key=self.payment_columns[index];obj=self.proposal.payments[int(row)]
                    if key=='installments':
                        value=int(value)
                        if not 1<=value<=60:raise ValueError('Informe de 1 a 60 parcelas.')
                    elif key in ('amount','entry','total') and value:value=format_value(FIELD_MAP['total'],value)
                    setattr(obj,key,value)
                    if key in ('amount','entry','installments'):obj.schedule=[];obj.last=''
                editor.destroy();self._refresh_tables();self._dirty()
            except (ValueError,KeyError) as e:messagebox.showerror('Formato inválido',str(e));editor.focus_set()
            finally:saving['active']=False
        # Keyboard events need OS focus; virtual commits also support deterministic UI automation.
        # Return and numpad Enter use the same real save/validation handler.
        editor.event_add('<<CommitCellEdit>>','<Return>','<KP_Enter>')
        editor.bind('<<CommitCellEdit>>',save)
        editor.bind('<FocusOut>',save);editor.bind('<Escape>',lambda e:editor.destroy())
    def _add_offer(self):
        name=simpledialog.askstring('Adicionar opção','Nome da opção:',parent=self)
        if name:
            self.proposal.offers.append(Offer(name.strip(),{}));self._refresh_tables()
            # Empty editable rows make manual completion possible without a review workflow.
            for key in ('casco','dm','dc','franquia','total'):
                if not self.offer_tree.exists(key):self.offer_tree.insert('','end',iid=key,values=[LABELS.get(key,key)]+['']*len(self.proposal.offers))
            self._dirty()
    def _add_payment(self):
        if not self.proposal.offers:messagebox.showinfo('Pagamento','Adicione uma opção de cobertura primeiro.');return
        pop=tk.Toplevel(self);pop.title('Adicionar pagamento');pop.transient(self);pop.grab_set();frame=ttk.Frame(pop,padding=20);frame.pack(fill='both',expand=True)
        names=[o.name for o in self.proposal.offers];vars={k:tk.StringVar() for k in ['offer','mode','installments','amount','entry','total','interest']};vars['offer'].set(names[0])
        for i,(key,label) in enumerate([('offer','Opção'),('mode','Modalidade'),('installments','Número de parcelas'),('amount','Valor de cada parcela (R$)'),('entry','Entrada (opcional)'),('total','Total (opcional)'),('interest','Juros / condição (opcional)')]):
            ttk.Label(frame,text=label).grid(row=i*2,column=0,sticky='w',pady=(6,2))
            widget=ttk.Combobox(frame,textvariable=vars[key],values=names,state='readonly') if key=='offer' else ttk.Entry(frame,textvariable=vars[key]);widget.grid(row=i*2+1,column=0,sticky='ew')
        def save():
            try:
                data={k:v.get().strip() for k,v in vars.items()};n=int(data.pop('installments'))
                if not 1<=n<=60 or not data['mode']:raise ValueError('Informe modalidade e número de parcelas válido.')
                for key in ('amount','entry','total'):data[key]=format_value(FIELD_MAP['total'],data[key])
                if not data['amount']:raise ValueError('Informe o valor da parcela.')
                self.proposal.payments.append(Payment(installments=n,**data));pop.destroy();self._refresh_tables();self._dirty()
            except ValueError as e:messagebox.showerror('Formato inválido',str(e),parent=pop)
        ttk.Button(frame,text='Adicionar',style='Primary.TButton',command=save).grid(row=15,column=0,sticky='ew',pady=(15,0))
    def _delete_payment(self):
        selected=self.payment_tree.selection()
        if selected:self.proposal.payments.pop(int(selected[0]));self._refresh_tables();self._dirty()
    def _collect(self):
        proposal=copy.deepcopy(self.proposal)
        for key,var in self.client_vars.items():proposal.values[key]=format_value(FIELD_MAP[key],var.get())
        return proposal
    def _tab_changed(self,event=None):
        if self.tabs.select()==str(self.preview_tab) and self.preview_dirty and not self.busy:self._preview()
    def _preview(self):
        if self.busy:return
        try:
            data=pdf_bytes(self._collect(),self.consultant.get(),self.phone.get(),self.logo)
            with fitz.open(stream=data,filetype='pdf') as doc:
                width=max(500,self.preview_canvas.winfo_width()-35);scale=width/doc[0].rect.width;pix=doc[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
                image=Image.open(__import__('io').BytesIO(pix.tobytes('png')));self.preview_image=ImageTk.PhotoImage(image)
            self.preview_canvas.delete('all');self.preview_canvas.create_image(12,12,image=self.preview_image,anchor='nw');self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox('all'));self.preview_dirty=False
        except Exception as e:messagebox.showerror('Prévia',str(e))
    def _export(self,kind):
        if self.busy:return
        try:proposal=self._collect()
        except ValueError as e:messagebox.showerror('Formato inválido',str(e));return
        path=filedialog.asksaveasfilename(defaultextension='.'+kind,initialfile='Proposta_Seguro_Auto.'+kind,filetypes=[(kind.upper(),'*.'+kind)])
        if not path:return
        if self.file and Path(path).resolve()==self.file.resolve():messagebox.showerror('Escolha outro arquivo','O documento original não pode ser sobrescrito.');return
        try:export_document(path,proposal,kind,self.consultant.get(),self.phone.get(),self.logo);messagebox.showinfo('Arquivo gerado','Proposta salva com sucesso.')
        except Exception as e:messagebox.showerror('Não foi possível gerar',str(e))
    def _choose_logo(self):
        name=filedialog.askopenfilename(filetypes=[('Imagens','*.png *.jpg *.jpeg *.webp')])
        if not name:return
        try:self.logo=save_logo(name);self._refresh_logo();self._dirty()
        except Exception as e:messagebox.showerror('Logomarca',str(e))
    def _remove_logo(self):
        try:remove_logo();self.logo=None;self._refresh_logo();self._dirty()
        except OSError as e:messagebox.showerror('Logomarca',str(e))
    def _refresh_logo(self):
        self.logo_image=None
        if self.logo:
            try:
                with Image.open(self.logo) as im:
                    im=im.copy();im.thumbnail((130,58));self.logo_image=ImageTk.PhotoImage(im)
            except OSError:self.logo=None
        self.logo_label.configure(image=self.logo_image or '',text='' if self.logo_image else 'Sua logomarca')
    def _open(self):
        if not self.file:return
        try:
            if os.name=='nt':os.startfile(self.file)
            else:subprocess.Popen(['open' if sys.platform=='darwin' else 'xdg-open',str(self.file)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except OSError as e:messagebox.showerror('Documento original',str(e))
    def destroy(self):
        if getattr(self,'poll_id',None):self.after_cancel(self.poll_id);self.poll_id=None
        super().destroy()
        release_window_icons(self._native_icon_handles)
    def _close(self):self.destroy()

def main():App().mainloop()
