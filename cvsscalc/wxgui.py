'''
Created on Oct 21, 2011

@author: bluec0re
'''
from __future__ import absolute_import

from datetime import datetime
import os
import os.path
import sys
import zipfile
import functools
import wx
from wx import xrc
import StringIO

from cvsscalc import cvsscalc
from wx.lib.masked import TimeCtrl

try:
    import wx.lib.agw.pygauge as PG
    
    class ColorGauge(PG.PyGauge):
        def __init__(self, *args, **kwargs):
            super(ColorGauge, self).__init__(*args, **kwargs)
            self.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
            col = wx.Color()
            col.SetFromString('grey')
            self.SetBorderColor(col)
            self.SetBorderPadding(2)
            self._keys = {}
            
        def add_color_key(self, pos, color):
            if isinstance(color, int):
                color = '#%06x' % color
            col = wx.Color()
            col.SetFromString(color)
            self._keys[pos] = col
        
        def SetValue(self, pos):
            color = self.GetBarColor()
    
            for key,col in self._keys.items():
                if pos == key:
                    color = col
                    break
                elif pos > key:
                    color = col
                elif pos < key:
                    break
            
            self.SetBarColour(color)
            super(ColorGauge, self).SetValue(pos)
            self.Refresh()
except ImportError:
    class ColorGauge(wx.Gauge):            
        def add_color_key(self, pos, color):
            pass

def find_file(path):
    """Find the file named path in the sys.path.
    Returns the full path name if found, None if not found"""
    for dirname in sys.path:
        if os.path.isfile(dirname):
            zf = zipfile.ZipFile(dirname)
            if path in zf.namelist():
                data = zf.read(path)
                zf.close()
                return data

            continue

        possible = os.path.join(dirname, path)
        if os.path.isfile(possible):
            with open(possible, 'r') as fp:
                return fp.read()
    return None


class ScoreGauge(ColorGauge):
    def __init__(self, *args, **kwargs):
        super(ScoreGauge, self).__init__(*args, **kwargs)
        
        self.add_color_key(0, 'green')
        self.add_color_key(40, 'yellow')
        self.add_color_key(70, 'red')
        
    def set_score(self, score):
        self.SetValue(score*10)
     

class TimeCtrlHandler(xrc.XmlResourceHandler):
    def __init__(self):
        xrc.XmlResourceHandler.__init__(self)
        # Standard styles
        self.AddWindowStyles()
        # Custom styles
        
    def CanHandle(self,node):
        return self.IsOfClass(node, 'TimeCtrl')
    
    def DoCreateResource(self):
        assert self.GetInstance() is None
        w = TimeCtrl(parent=self.GetParentAsWindow(),
                     id=self.GetID(),
                     pos=self.GetPosition(),
                     size=self.GetSize(),
                     style=self.GetStyle())
        if self.GetText('value'):
            w.SetValue(self.GetText('value'))
        self.SetupWindow(w)
        return w
    
        
class ScoreGaugeHandler(xrc.XmlResourceHandler):
    def __init__(self):
        xrc.XmlResourceHandler.__init__(self)
        # Standard styles
        self.AddWindowStyles()
        # Custom styles
        self.AddStyle('wxGA_HORIZONTAL', wx.GA_HORIZONTAL)
        
        
    def CanHandle(self,node):
        return self.IsOfClass(node, 'ScoreGauge')
    
    def DoCreateResource(self):
        assert self.GetInstance() is None
        w = ScoreGauge(parent=self.GetParentAsWindow(),
                     id=self.GetID(),
                     pos=self.GetPosition(),
                     size=self.GetSize(),
                     style=self.GetStyle()|wx.GA_HORIZONTAL)
        if self.GetText('value'):
            w.SetValue(self.GetText('value'))
        self.SetupWindow(w)
        return w
        
                
class MyApp(wx.App):
    base = {
            'av' : [
                  ('Local', 'L'),
                  ('Adjacent Network', 'AN'),
                  ('Network', 'N')
                  ],
            'ac' : [
                  ('Low', 'L'),
                  ('Medium', 'M'),
                  ('High', 'H')
                  ],
            'au' : [
                  ('None', 'N'),
                  ('Single', 'S'),
                  ('Multiple', 'M')
                  ],
            'c' : [
                  ('None', 'N'),
                  ('Partial', 'P'),
                  ('Complete', 'C')
                  ],
            'i' : [
                  ('None', 'N'),
                  ('Partial', 'P'),
                  ('Complete', 'C')
                  ],
            'a' : [
                  ('None', 'N'),
                  ('Partial', 'P'),
                  ('Complete', 'C')
                  ]
            }
    
    temp = {
            'e' : [
                 ('Unproven', 'U'),
                 ('Proof of Concept', 'POC'),
                 ('Functional', 'F'),
                 ('High', 'H'),
                 ('Not defined', 'ND')
                 ],
            'rl' : [
                 ('Official Fix', 'OF'),
                 ('Temporary Fix', 'TF'),
                 ('Workaround', 'W'),
                 ('Not defined', 'ND')
                 ],
            'rc' : [
                 ('Not Defined', 'ND'),
                 ('Unconfirmed', 'UC'),
                 ('Uncorrobated', 'UR'),
                 ('Confirmed', 'C'),
                 ],
            }
    
    env = {
           'cdp' : [
                   ('None', 'N'),
                   ('Low', 'L'),
                   ('Low-Medium', "LM"),
                   ('Medium-High', 'MH'),
                   ('High', 'H'),
                   ('Not defined', 'ND')
                ],
            'td' : [
                   ('None (0%)', 'N'),
                   ('Low (1%-25%)', 'L'),
                   ('Medium (26%-75%)', 'M'),
                   ('High (76%-100%)', 'H'),
                   ('Not defined', 'ND')
                ],
            'cr' : [
                   ('Low', 'L'),
                   ('Medium', 'M'),
                   ('High', 'H'),
                   ('Not defined', 'ND')
                ],
            'ir' : [
                   ('Low', 'L'),
                   ('Medium', 'M'),
                   ('High', 'H'),
                   ('Not defined', 'ND')
                ],
            'ar' : [
                   ('Low', 'L'),
                   ('Medium', 'M'),
                   ('High', 'H'),
                   ('Not defined', 'ND')
                ]
           }
            
    def OnInit(self):
        self.base_score = cvsscalc.Base()
        self.temp_score = cvsscalc.Temporal()
        self.env_score = cvsscalc.Environmental()
        self.modified = False
        self.fname = None
        
        content = find_file('cvsscalc/xrcgui.xrc')
        self.res = xrc.EmptyXmlResource()
        self.res.AddHandler(TimeCtrlHandler())
        self.res.AddHandler(ScoreGaugeHandler())
        self.res.LoadFromString(content)
        
        self.frame = self.res.LoadFrame(None, 'MyFrame')
        self.frame.SetTitle('CVSS Calculator')
        self.base_panel = xrc.XRCCTRL(self.frame, 'base_panel')
        self.env_panel = xrc.XRCCTRL(self.frame, 'env_panel')
        self.temp_panel = xrc.XRCCTRL(self.frame, 'temp_panel')
        self.util_panel = xrc.XRCCTRL(self.frame, 'util_panel')
        self.score_panel = xrc.XRCCTRL(self.frame, 'score_panel')
        
        self.setup_panel(self.base_panel)
        self.setup_panel(self.temp_panel)
        self.setup_panel(self.env_panel)
        
        self.update_scores()
        self.refresh_score()
        
        self.frame.Fit()
        self.frame.Show()
        
        self.bind_keys()
        
        return True
    
    def setup_panel(self, panel):
        pic = wx.ArtProvider.GetBitmap(wx.ART_QUESTION)
        panel_name,_ = panel.GetName().split('_')
        for child in panel.GetChildren():
            if isinstance(child, wx.Choice):
                choice = child
                choice_name,_ = child.GetName().split('_')
                
                items = MyApp.__dict__[panel_name.encode()][choice_name.encode()]
                for item in items:
                    child.Append(item[0])
                child.SetSelection(0)
                child.Bind(wx.EVT_CHOICE, self.OnChoice)
            elif isinstance(child, wx.BitmapButton):
                child.SetBitmapLabel(pic)
                choice_name,_,_ = child.GetName().split('_')
                
                items = MyApp.__dict__[panel_name.encode()][choice_name.encode()]
                self.add_tooltip(choice, child, panel_name, choice_name, items)
                
    def update_score(self, panel):
        panel_name,_ = panel.GetName().split('_')
        for child in panel.GetChildren():
            if isinstance(child, wx.Choice):
                choice_name,_ = child.GetName().split('_')
                
                items = MyApp.__dict__[panel_name.encode()][choice_name.encode()]
                
                score = getattr(self, '%s_score' % panel_name)
                
                if choice_name in score.__dict__:
                    attr_name = choice_name
                elif choice_name.upper() in score.__dict__:
                    attr_name = choice_name.upper()
                elif choice_name.capitalize() in score.__dict__:
                    attr_name = choice_name.capitalize()
                setattr(score, attr_name, items[child.GetSelection()][1])
    
    def update_panel_choices(self, panel):
        def select(val, cb, ar):
            idx = 0
            for i in ar:
                if i[1] == val:
                    cb.Select(idx)
                    break
                idx += 1
        
        panel_name,_ = panel.GetName().split('_')
        for child in panel.GetChildren():
            if isinstance(child, wx.Choice):
                choice_name,_ = child.GetName().split('_')
                
                items = MyApp.__dict__[panel_name.encode()][choice_name.encode()]
                
                score = getattr(self, '%s_score' % panel_name)
                
                if choice_name in score.__dict__:
                    attr_name = choice_name
                elif choice_name.upper() in score.__dict__:
                    attr_name = choice_name.upper()
                elif choice_name.capitalize() in score.__dict__:
                    attr_name = choice_name.capitalize()
                select(getattr(score, attr_name), child, items)
    
    def update_scores(self):
        self.update_score(self.base_panel)
        self.update_score(self.temp_panel)
        self.update_score(self.env_panel)
        
    def bind_keys(self):
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        xrc.XRCCTRL(self.util_panel, 'load_btn').Bind(wx.EVT_BUTTON, self.OnLoad)
        xrc.XRCCTRL(self.util_panel, 'save_btn').Bind(wx.EVT_BUTTON, self.OnSave)
        xrc.XRCCTRL(self.util_panel, 'copy_btn').Bind(wx.EVT_BUTTON, self.OnCopy)
        self.frame.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def OnKey(self, event):
        if event.ControlDown():
            if event.GetKeyCode() == ord('c') or event.GetKeyCode() == ord('C'):
                self.OnCopy()
            elif event.GetKeyCode() == ord('s') or event.GetKeyCode() == ord('S'):
                self.OnSave(save_old=(not event.ShiftDown()))
            elif event.GetKeyCode() == ord('o') or event.GetKeyCode() == ord('O'):
                self.OnLoad()
            else:
                event.Skip()
        else:
            event.Skip()
            
    def OnClose(self, event=None):
        if self.modified:
            ret = wx.MessageBox('File was not save!\nSave it now?',
                    'Not saved', wx.YES_NO | wx.CANCEL | wx.ICON_EXCLAMATION)

            if ret == wx.YES:
                self.OnSave(save_old=True)
            elif ret == wx.CANCEL:
                return
        self.frame.Destroy()
    
    def OnChoice(self, event=None):
        self.update_scores()
        self.refresh_score()
        self.modified = True
        if self.frame.GetTitle().endswith(']'):
            self.frame.SetTitle(self.frame.GetTitle()[:-1] + '*]')
        else:
            self.frame.SetTitle(self.frame.GetTitle() + '[<never saved before>*]')
        
    def OnLoad(self, event=None):
        fd = wx.FileDialog(self.frame, wildcard='*.cvss', style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        fd.ShowModal()
        
        fname = fd.GetPath()
        
        if fname == '':
            return

        with open(fname, 'r') as fp:
            self.load_from_file(fp)
        self.update_choices()
        self.refresh_score()

    def load_from_file(self, fp):
        lines = fp.readlines()
        idx = 1
        if fp.name.endswith('.cvss'):
            idx = 3
        self.base_score.from_string(lines[idx])
        self.temp_score.from_string(lines[idx+1])
        self.env_score.from_string(lines[idx+2])
        date = wx.DateTime()
        date.ParseFormat(format='%m/%d/%Y %H:%M:%S', date=lines[7].strip())
       
        xrc.XRCCTRL(self.util_panel, 'date_ctrl').SetValue(date)
        xrc.XRCCTRL(self.util_panel, 'time_ctrl').SetValue(date)
        xrc.XRCCTRL(self.util_panel, 'author_ctrl').SetValue(lines[8].strip())
        self.fname = os.path.basename(fp.name)
        os.chdir(os.path.dirname(fp.name))

        self.modified = False
        self.frame.SetTitle('CVSS Calculator [%s]' % fp.name)
            
    
    def OnSave(self, event=None, save_old=False):
        if not save_old or not self.fname:
            fd = wx.FileDialog(self.frame, wildcard='*.cvss', style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
            fd.ShowModal()
            fname = fd.GetPath()
        else:
            fname = os.path.join(os.getcwd(), self.fname)

        if fname == '':
            return

        if not fname.endswith('.cvss'):
            fname += '.cvss'
        
        name = xrc.XRCCTRL(self.util_panel, 'author_ctrl').GetValue()
        date = xrc.XRCCTRL(self.util_panel, 'date_ctrl').GetValue()
        time = xrc.XRCCTRL(self.util_panel, 'time_ctrl').GetValue(as_wxTimeSpan=True)
        date.SetHour(0)
        date.SetMinute(0)
        date.SetSecond(0)
        date.AddTS(time)
                
        with open(fname, 'w') as fp:
            fp.write('- / - / - / - / - / - / -\r\n')
            fp.write('- / - / -\r\n')
            fp.write('- / -\r\n')
            fp.write(str(self.base_score) + '\r\n')
            fp.write(str(self.temp_score) + '\r\n')
            fp.write(str(self.env_score) + '\r\n')
            fp.write('%s\r\n' % os.path.basename(fname).replace('_', ' ')[:-5]) # Desc
            fp.write(date.Format('%m/%d/%Y %H:%M:%S') + '\r\n')
            fp.write(name + '\r\n') # auditor
            score = self.get_total_score()
            fp.write('%.1f\n' % score)
            if score < 4:
                fp.write('Low\n')
            elif score >= 7:
                fp.write('High\n')
            else:
                fp.write('Medium\n')
            self.fname = os.path.basename(fname)
            os.chdir(os.path.dirname(fname))
            self.modified = False
            self.frame.SetTitle('CVSS Calculator [%s]' % fp.name)
                
                
    
    def OnCopy(self, event=None):
        target = xrc.XRCCTRL(self.util_panel, 'copy_choice').GetSelection()
        
        header = 'The severity rating based on CVSS Version 2:'
        score = self.get_total_score()
        if score < 4:
            tex_color = 'green'
            word_color = 4
            severity = 'Low'
        elif score >= 7:
            tex_color = 'red'
            word_color = 6
            severity = 'High'
        else:
            tex_color = 'yellow'
            word_color = 7
            severity = 'Medium'
            
        table_data = [
                      ('Reference File:', self.fname),
                      ('Base Vector:', str(self.base_score)),
                      ('Temporal Vector:', str(self.temp_score)),
                      ('Environmental Vector:', str(self.env_score)),
                      ('CVSS Version 2 Score:', '%.1f' % score),
                      ('Severity:', severity)
                      ]
        
        
        if target == 0: # Word
            string = '%s\n' % header
            string += '%s\t\t\t%s\n' % table_data[0]
            string += '%s\t\t\t(%s)\n' % table_data[1]
            string += '%s\t\t(%s)\n' % table_data[2]
            string += '%s\t\t(%s)\n' % table_data[3]
            string += '%s\t\t%s\n' % table_data[4]
            string += '%s\t\t\t%s\n' % table_data[5]
            
            
            do = wx.TextDataObject()
            do.SetText(string)
            
            if not wx.TheClipboard.IsOpened():
                wx.TheClipboard.Open()
        
            wx.TheClipboard.SetData(do)
            wx.TheClipboard.Close()
            return
        elif target == 2: # LaTeX
            string = '%s\n' % header
            string += '\\begin{tabular}{@{}ll}\n'
            for data in table_data:
                if table_data.index(data) == 5:
                    string += '  %s & \\colorbox{%s}{%s}\n' % (data[0], tex_color, data[1])
                elif table_data.index(data) in (1, 2, 3):
                    string += '  %s & (%s)\n' % data
                else:
                    string += '  %s & %s\n' % data
            string += '\\end{tabular}\n'
        elif target == 1: # Text
            string = '%s\n' % header
            string += '%s       %s\n' % table_data[0]
            string += '%s          (%s)\n' % table_data[1]
            string += '%s      (%s)\n' % table_data[2]
            string += '%s (%s)\n' % table_data[3]
            string += '%s %s\n' % table_data[4]
            string += '%s             %s\n' % table_data[5]
        
        
        if not wx.TheClipboard.IsOpened():
            wx.TheClipboard.Open()
            
        do = wx.TextDataObject()
        do.SetText(string)
        wx.TheClipboard.SetData(do)
        wx.TheClipboard.Close()
        
    
    def update_choices(self):
        self.update_panel_choices(self.base_panel)
        self.update_panel_choices(self.temp_panel)
        self.update_panel_choices(self.env_panel)
    
    def refresh_score(self):
        base = self.base_score
        tmp = self.temp_score
        env = self.env_score
        xrc.XRCCTRL(self.score_panel, 'base_score').SetLabel('%.2f' % base.get_score())
        xrc.XRCCTRL(self.score_panel, 'base_gauge').SetValue(base.get_score() * 10)
        xrc.XRCCTRL(self.score_panel, 'temp_score').SetLabel('%.2f' % tmp.get_score(base))
        xrc.XRCCTRL(self.score_panel, 'temp_gauge').SetValue(tmp.get_score(base) * 10)
        xrc.XRCCTRL(self.score_panel, 'env_score').SetLabel('%.2f' % env.get_score(base, tmp))
        xrc.XRCCTRL(self.score_panel, 'env_gauge').SetValue(env.get_score(base, tmp) * 10)
        xrc.XRCCTRL(self.score_panel, 'total_score').SetLabel('%.2f' % env.get_score(base, tmp))
        xrc.XRCCTRL(self.score_panel, 'total_gauge').SetValue(env.get_score(base, tmp) * 10)
        
    def get_total_score(self):
        base = self.base_score
        tmp = self.temp_score
        env = self.env_score
        
        return env.get_score(base, tmp)
    
    def add_tooltip(self, choice, btn, panel, name, data):
        txt = ''
        for title, key in data:
            key = key.lower()

            content = find_file('tooltips/%s/%s_%s.txt' % (panel, name, key))
            txt += "%s:\n" % title
            txt += content
            txt += "\n"
        
        txt = txt.strip()
        choice.SetToolTipString(txt)

        def onclick(txt, event):
            wx.MessageBox(txt)

        btn.Bind(wx.EVT_BUTTON, functools.partial(onclick, txt))

def main(infile=None):
    app = MyApp()
    #frame = MainFrame(None, wx.ID_ANY, title='CVSS Calculator')
    #app.TopWindow = frame
    #if infile:
    #    frame.load_from_file(infile)
    #    frame.update_choices()
    #    frame.refresh_score()
    #app.bind_keys()
    #frame.Show()
    app.MainLoop()
    
if __name__ == '__main__':
    main()
