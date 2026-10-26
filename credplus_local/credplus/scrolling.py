"""Route wheel events inside each tab before native widget bindings can consume them."""
import math


class TabWheel:
    SEQUENCES=('<MouseWheel>','<Shift-MouseWheel>','<Button-4>','<Button-5>','<Shift-Button-4>','<Shift-Button-5>')

    def __init__(self,root,before_scroll=None):
        self.root=root;self.before_scroll=before_scroll;self.tag='PropostaWheel'+str(root.winfo_id());self.routes={};self.pending={}
        self.system=root.tk.call('tk','windowingsystem')
        for sequence in self.SEQUENCES:root.bind_class(self.tag,sequence,self.handle)

    def add(self,container,view):
        self.routes[container]=view;self.attach(container)

    def target(self,widget):
        # Walk parents: entries and labels inside a Canvas still belong to that tab.
        while widget is not None:
            if widget in self.routes:
                if widget.winfo_ismapped():return self.routes[widget]
                return None
            widget=getattr(widget,'master',None)
        return None

    def attach(self,widget):
        if self.target(widget) is not None or any(self._inside(widget,c) for c in self.routes):
            tags=widget.bindtags()
            if self.tag not in tags:widget.bindtags((self.tag,)+tags)
        for child in widget.winfo_children():self.attach(child)

    @staticmethod
    def _inside(widget,container):
        while widget is not None:
            if widget is container:return True
            widget=getattr(widget,'master',None)
        return False

    def handle(self,event):
        view=self.target(getattr(event,'widget',None))
        if view is None:return None
        try:state=int(getattr(event,'state',0) or 0)
        except (TypeError,ValueError):state=0
        axis='x' if state&1 else 'y'
        extent=view.xview() if axis=='x' else view.yview()
        if extent[1]-extent[0]>=1-1e-9:
            self.pending.pop((str(view),axis),None);return 'break'
        button=getattr(event,'num',None)
        if button in (4,5):ticks=-1 if button==4 else 1
        else:
            try:delta=float(getattr(event,'delta',0) or 0)
            except (TypeError,ValueError):delta=0
            ticks=-delta if self.system=='aqua' else -delta/120
        key=(str(view),axis)
        accumulated=self.pending.get(key,0)+ticks
        whole=math.trunc(round(accumulated,10));self.pending[key]=accumulated-whole
        if whole:
            position=(view.xview() if axis=='x' else view.yview())[0]
            if self.before_scroll and self.before_scroll(view) is False:return 'break'
            (view.xview_moveto if axis=='x' else view.yview_moveto)(position)
            fn=view.xview_scroll if axis=='x' else view.yview_scroll
            fn(whole*3,'units')
        # Stop native Treeview/Entry bindings from applying a second scroll or changing a field.
        return 'break'

    def reset(self):self.pending.clear()

    def close(self):
        for sequence in self.SEQUENCES:self.root.unbind_class(self.tag,sequence)
        self.routes.clear();self.pending.clear()
