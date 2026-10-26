import struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from credplus.core import ASSETS
from credplus.icon_resources import ico_frames,verify_default_icon,verify_executable
from credplus.windows_icons import application_id,set_window_icons,release_window_icons


def group(frames,first=1):
    return struct.pack('<HHH',0,1,len(frames))+b''.join(struct.pack('<BBBBHHIH',f['width']%256,f['height']%256,0,0,1,32,len(f['data']),i) for i,f in enumerate(frames,first))

class ResourceIconTests(unittest.TestCase):
 def setUp(self):self.data=(ASSETS/'quote_document.ico').read_bytes();self.frames=ico_frames(self.data)
 def test_shipped_ico_has_all_small_and_large_frames(self):
    self.assertTrue({16,20,24,32,48,64,128,256}.issubset({f['width'] for f in self.frames}))
 def test_default_group_matches_approved_icon(self):
    icons={i:f['data'] for i,f in enumerate(self.frames,1)}
    self.assertEqual(verify_default_icon(self.data,group(self.frames),icons),len(self.frames))
 def test_old_or_python_default_icon_is_rejected(self):
    icons={i:f['data'] for i,f in enumerate(self.frames,1)};icons[1]=b'x'*len(icons[1])
    with self.assertRaises(ValueError):verify_default_icon(self.data,group(self.frames),icons)
 def test_missing_resource_frame_is_rejected(self):
    icons={i:f['data'] for i,f in enumerate(self.frames,1)};icons.pop(1)
    with self.assertRaises(ValueError):verify_default_icon(self.data,group(self.frames),icons)
 def test_truncated_ico_is_rejected(self):
    with self.assertRaises(ValueError):ico_frames(self.data[:16])
 def test_verifier_checks_default_group_not_any_matching_group(self):
    blobs={};offset=0
    def leaf(ident,data):
     nonlocal offset
     offset+=1;blobs[offset]=data
     return NS(id=ident,name=None,directory=NS(entries=[NS(data=NS(struct=NS(OffsetToData=offset,Size=len(data))))]))
    icons=[leaf(i,f['data']) for i,f in enumerate(self.frames,1)]
    groups=[leaf(1,b'old icon group'),leaf(2,group(self.frames))]
    class FakePE:
     DIRECTORY_ENTRY_RESOURCE=NS(entries=[NS(id=3,directory=NS(entries=icons)),NS(id=14,directory=NS(entries=groups))])
     def __enter__(self):return self
     def __exit__(self,*args):pass
     def get_data(self,offset,size):return blobs[offset]
    with patch.dict(sys.modules,{'pefile':NS(PE=lambda path:FakePE())}):
     with self.assertRaises(ValueError):verify_executable('fake.exe',ASSETS/'quote_document.ico')

 def test_old_localized_default_group_is_rejected(self):
    blobs={};offset=0
    def lang(data):
     nonlocal offset
     offset+=1;blobs[offset]=data
     return NS(data=NS(struct=NS(OffsetToData=offset,Size=len(data))))
    icons=[NS(id=i,name=None,directory=NS(entries=[lang(f['data'])])) for i,f in enumerate(self.frames,1)]
    groups=[NS(id=1,name=None,directory=NS(entries=[lang(group(self.frames)),lang(b'old localized icon')]))]
    class FakePE:
     DIRECTORY_ENTRY_RESOURCE=NS(entries=[NS(id=3,directory=NS(entries=icons)),NS(id=14,directory=NS(entries=groups))])
     def __enter__(self):return self
     def __exit__(self,*args):pass
     def get_data(self,offset,size):return blobs[offset]
    with patch.dict(sys.modules,{'pefile':NS(PE=lambda path:FakePE())}):
     with self.assertRaises(ValueError):verify_executable('fake.exe',ASSETS/'quote_document.ico')

class NativeCall:
 def __init__(self,fn):self.fn=fn;self.calls=[]
 def __call__(self,*args):self.calls.append(args);return self.fn(*args)

class WindowsWindowIconTests(unittest.TestCase):
 def fake(self,fail_second=False):
    handles=iter([0x123456789,0 if fail_second else 0x23456789A])
    api=NS(GetAncestor=NativeCall(lambda hwnd,flag:0x3456789AB),LoadImageW=NativeCall(lambda *args:next(handles)),SendMessageW=NativeCall(lambda *args:0x999999999),GetSystemMetrics=NativeCall(lambda n:16 if n in (49,50) else 32),DestroyIcon=NativeCall(lambda h:1))
    root=NS(update_idletasks=lambda:None,winfo_id=lambda:0x456789ABC)
    return root,api
 def test_small_and_big_icon_go_to_native_wrapper_without_handle_truncation(self):
    root,api=self.fake();handles=set_window_icons(root,ASSETS/'quote_document.ico',api)
    self.assertEqual(handles,[0x123456789,0x23456789A])
    self.assertEqual(api.GetAncestor.calls,[(0x456789ABC,2)])
    self.assertEqual(api.SendMessageW.calls,[(0x3456789AB,0x80,0,0x123456789),(0x3456789AB,0x80,1,0x23456789A)])
    self.assertEqual([call[3:5] for call in api.LoadImageW.calls],[(16,16),(32,32)])
 def test_cleanup_frees_only_owned_handles_not_borrowed_previous_icons(self):
    root,api=self.fake();handles=set_window_icons(root,ASSETS/'quote_document.ico',api);release_window_icons(handles,api)
    self.assertEqual(api.DestroyIcon.calls,[(0x123456789,),(0x23456789A,)]);self.assertFalse(handles)
 def test_failed_load_cleans_up_first_handle(self):
    root,api=self.fake(fail_second=True)
    with self.assertRaises(OSError):set_window_icons(root,ASSETS/'quote_document.ico',api)
    self.assertEqual(api.DestroyIcon.calls,[(0x123456789,)])
 def test_versioned_application_id_changes_with_release(self):
    self.assertNotEqual(application_id('26.10.26.2'),application_id('26.10.26.3'));self.assertNotIn(' ',application_id('26.10.26.3'))
