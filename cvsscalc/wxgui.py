'''
Created on Oct 21, 2011

@author: bluec0re
'''
from __future__ import absolute_import

from datetime import datetime
import os.path
import wx
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


class MainFrame(wx.Frame):
    
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.fname = None
        self.score_panel = ScorePanel(self)
        nb = wx.Notebook(self)
        self.cvss_panel = CvssPanel(nb)
        
        bs = wx.BoxSizer(wx.VERTICAL)
        nb.AddPage(self.cvss_panel, 'CVSS2')
        bs.Add(self.score_panel)
        bs.Add(nb, wx.EXPAND|wx.ALL)
        self.SetSizerAndFit(bs)
        
        self.update_scores()
        self.refresh_score()
        
        self.cvss_panel.base_panel.set_handler(self.OnChoice)
        self.cvss_panel.tmp_panel.set_handler(self.OnChoice)
        self.cvss_panel.env_panel.set_handler(self.OnChoice)
        
        self.cvss_panel.util_panel.load_btn.Bind(wx.EVT_BUTTON, self.OnLoad)
        self.cvss_panel.util_panel.save_btn.Bind(wx.EVT_BUTTON, self.OnSave)
        self.cvss_panel.util_panel.copy_btn.Bind(wx.EVT_BUTTON, self.OnCopy)
    
    def OnChoice(self, evnt):
        self.update_scores()
        self.refresh_score()
        
    def OnLoad(self, event):
        fd = wx.FileDialog(self, wildcard='*.cvss', style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        fd.ShowModal()
        
        fname = fd.GetPath()
        
        with open(fname, 'r') as fp:
            self.load_from_file(fp)
        self.update_choices()
        self.refresh_score()

    def load_from_file(self, fp):
            lines = fp.readlines()
            idx = 1
            if fp.name.endswith('.cvss'):
                idx = 3
            self.cvss_panel.base_panel.score.from_string(lines[idx])
            self.cvss_panel.tmp_panel.score.from_string(lines[idx+1])
            self.cvss_panel.env_panel.score.from_string(lines[idx+2])
            date = wx.DateTime()
            date.ParseFormat(format='%m/%d/%Y %H:%M:%S', date=lines[7].strip())
            
            self.cvss_panel.util_panel.date.SetValue(date)
            self.cvss_panel.util_panel.time.SetValue(date)
            self.cvss_panel.util_panel.name.SetValue(lines[8].strip())
            self.fname = os.path.basename(fp.name)
            
    
    def OnSave(self, event):
        fd = wx.FileDialog(self, wildcard='*.cvss', style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        fd.ShowModal()
        fname = fd.GetPath()
        
        name = self.cvss_panel.util_panel.name.GetValue()
        date = self.cvss_panel.util_panel.date.GetValue()
        time = self.cvss_panel.util_panel.time.GetValue(as_wxTimeSpan=True)
        date.SetHour(0)
        date.SetMinute(0)
        date.SetSecond(0)
        date.AddTS(time)
                
        with open(fname, 'w') as fp:
            fp.write('- / - / - / - / - / - / -\r\n')
            fp.write('- / - / -\r\n')
            fp.write('- / -\r\n')
            fp.write(str(self.cvss_panel.base_panel.score) + '\r\n')
            fp.write(str(self.cvss_panel.tmp_panel.score) + '\r\n')
            fp.write(str(self.cvss_panel.env_panel.score) + '\r\n')
            fp.write('\r\n') # Desc
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
            self.fname = fd.GetFilename()
                
                
    
    def OnCopy(self, event):
        target = self.cvss_panel.util_panel.copy_cb.GetSelection()
        
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
                      ('Base Vector:', str(self.cvss_panel.base_panel.score)),
                      ('Temporal Vector:', str(self.cvss_panel.tmp_panel.score)),
                      ('Environmental Vector:', str(self.cvss_panel.env_panel.score)),
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
            
            compositeDataObject = wx.DataObjectComposite()
            
            rtf_string = r'{\rtf1\ansi\uc1\deff0{\fonttbl{\f0\fnil Verdana;}'
            rtf_string += '%s \\par\n' % header
            rtf_string += '%s \\tab\\tab\\tab %s\\par\n' % table_data[0]
            rtf_string += '%s \\tab\\tab\\tab (%s)\\par\n' % table_data[1]
            rtf_string += '%s \\tab\\tab (%s)\\par\n' % table_data[2]
            rtf_string += '%s \\tab\\tab (%s)\\par\n' % table_data[3]
            rtf_string += '%s \\tab\\tab %s\\par\n' % table_data[4]
            rtf_string += '%s \\tab\\tab\\tab\\highlight%d %s\\par\n' % (table_data[5][0], word_color, table_data[5][1])
            rtf_string += '}'
            
            cdf = wx.CustomDataFormat('application/rtf')
            rtf = wx.CustomDataObject(cdf)
            rtf.SetData(rtf_string.encode('latin1'))
            compositeDataObject.Add(rtf)
            cdf = wx.CustomDataFormat('text/richtext')
            rtf = wx.CustomDataObject(cdf)
            rtf.SetData(rtf_string.encode('latin1'))
            compositeDataObject.Add(rtf)
            cdf = wx.CustomDataFormat('Rich Text Format')
            rtf = wx.CustomDataObject(cdf)
            rtf.SetData(rtf_string.encode('latin1'))
            compositeDataObject.Add(rtf)
            cdo = wx.CustomDataObject(wx.CustomDataFormat('COMPOUND_TEXT'))
            cdo.SetData(string.encode('latin1'))
            compositeDataObject.Add(cdo)
            cdo = wx.CustomDataObject(wx.CustomDataFormat('text/plain'))
            cdo.SetData(string.encode('latin1'))
            compositeDataObject.Add(cdo)
            do = wx.TextDataObject()
            do.SetText(string)
            compositeDataObject.Add(do)
            
            if not wx.TheClipboard.IsOpened():
                wx.TheClipboard.Open()
        
            wx.TheClipboard.SetData(compositeDataObject)
            wx.TheClipboard.Close()
            return
        elif target == 1: # LaTeX
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
        elif target == 2: # Text
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
        self.cvss_panel.base_panel.update_choices()
        self.cvss_panel.tmp_panel.update_choices()
        self.cvss_panel.env_panel.update_choices()
    
    def update_scores(self):
        self.cvss_panel.base_panel.update_score()
        self.cvss_panel.tmp_panel.update_score()
        self.cvss_panel.env_panel.update_score()
    
    def refresh_score(self):
        base = self.cvss_panel.base_panel.score
        tmp = self.cvss_panel.tmp_panel.score
        env = self.cvss_panel.env_panel.score
        self.score_panel.base.SetLabel('%.2f' % base.get_score())
        self.score_panel.base_gauge.set_score(base.get_score())
        self.score_panel.tmp.SetLabel('%.2f' % tmp.get_score(base))
        self.score_panel.tmp_gauge.set_score(tmp.get_score(base))
        self.score_panel.env.SetLabel('%.2f' % env.get_score(base, tmp))
        self.score_panel.env_gauge.set_score(env.get_score(base, tmp))
        self.score_panel.total.SetLabel('%.2f' % env.get_score(base, tmp))
        self.score_panel.total_gauge.set_score(env.get_score(base, tmp))
        
    def get_total_score(self):
        base = self.cvss_panel.base_panel.score
        tmp = self.cvss_panel.tmp_panel.score
        env = self.cvss_panel.env_panel.score
        
        return env.get_score(base, tmp)

class CvssPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(CvssPanel, self).__init__(*args, **kwargs)
        sizer = wx.GridSizer(2, 2, 5, 5)
        self.base_panel = BasePanel(self)
        self.tmp_panel = TempPanel(self)
        self.env_panel = EnvPanel(self)
        self.util_panel = UtilPanel(self)
        sizer.Add(self.base_panel, wx.EXPAND|wx.ALL)
        sizer.Add(self.env_panel, wx.EXPAND|wx.ALL)
        sizer.Add(self.tmp_panel, wx.EXPAND|wx.ALL)
        sizer.Add(self.util_panel, wx.EXPAND|wx.ALL)
        self.SetSizer(sizer)
        
        
class UtilPanel(wx.Panel):
        def __init__(self, *args, **kwargs):
            super(UtilPanel, self).__init__(*args, **kwargs)
            
            gs = wx.GridSizer(4, 3, 5, 5)
            
            self.name = wx.TextCtrl(self)
            self.date = wx.DatePickerCtrl(self)
            self.time = TimeCtrl(self)
            self.load_btn = wx.Button(self, label='Load')
            self.save_btn = wx.Button(self, label='Save')
            self.copy_btn = wx.Button(self, label='Copy')
            self.copy_cb = wx.Choice(self, choices=['Word', 'LaTeX', 'Text'])
            
            gs.AddMany([
                        (wx.StaticText(self, label='Auditor'), 0, 0),
                        (self.name, 0, wx.EXPAND),
                        (wx.StaticText(self, -1, ''), 0, 0),
                        (wx.StaticText(self, label='Date'), 0, 0),
                        (self.date, 0, wx.EXPAND),
                        (self.time, 0, wx.EXPAND),
                        (self.load_btn, 0, 0),
                        (self.save_btn, 0, 0),
                        (wx.StaticText(self, -1, ''), 0, 0),
                        (self.copy_cb, 0, wx.EXPAND),
                        (self.copy_btn, 0, 0),
                        (wx.StaticText(self, -1, ''), 0, 0),
                        ])
            
            self.SetSizer(gs)
            
     
class BasePanel(wx.Panel):
    av = [
          ('Local', 'L'),
          ('Adjacent Network', 'AN'),
          ('Network', 'N')
          ]
    ac = [
          ('Low', 'L'),
          ('Medium', 'M'),
          ('High', 'H')
          ]
    au = [
          ('None', 'N'),
          ('Single', 'S'),
          ('Multiple', 'M')
          ]
    im = [
          ('None', 'N'),
          ('Partial', 'P'),
          ('Complete', 'C')
          ]
    
    def __init__(self, *args, **kwargs):
        super(BasePanel, self).__init__(*args, **kwargs)
        
        
        self.score = cvsscalc.Base()
        
        box = wx.StaticBox(self, -1, 'Base Score')
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        
        gs = wx.GridSizer(rows=6, cols=2, vgap=5, hgap=5)
        
        self.av = wx.Choice(self, choices=[a[0] for a in BasePanel.av])
        self.ac = wx.Choice(self, choices=[a[0] for a in BasePanel.ac])
        self.au = wx.Choice(self, choices=[a[0] for a in BasePanel.au])
        self.c = wx.Choice(self, choices=[a[0] for a in BasePanel.im])
        self.a = wx.Choice(self, choices=[a[0] for a in BasePanel.im])
        self.i = wx.Choice(self, choices=[a[0] for a in BasePanel.im])
        gs.AddMany([
                    (wx.StaticText(self, label='Attack Vector'), 0, 0),
                    (self.av, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Attack Complexity'), 0, 0),
                    (self.ac, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Authentication'), 0, 0),
                    (self.au, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Confidentiality Impact'), 0, 0),
                    (self.c, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Integrity Impact'), 0, 0),
                    (self.i, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Availability Impact'), 0, 0),
                    (self.a, 0, wx.EXPAND),
                    ])

        sizer.Add(gs, wx.EXPAND)
        self.SetSizer(sizer)
        
    def update_score(self):
        self.score.AV = BasePanel.av[self.av.CurrentSelection][1]
        self.score.AC = BasePanel.ac[self.ac.CurrentSelection][1]
        self.score.Au = BasePanel.au[self.au.CurrentSelection][1]
        self.score.C = BasePanel.im[self.c.CurrentSelection][1]
        self.score.A = BasePanel.im[self.a.CurrentSelection][1]
        self.score.I = BasePanel.im[self.i.CurrentSelection][1]
        
    def update_choices(self):
        def select(val, cb, ar):
            idx = 0
            for i in ar:
                if i[1] == val:
                    cb.Select(idx)
                    break
                idx += 1
               
        select(self.score.AV, self.av, BasePanel.av)
        select(self.score.AC, self.ac, BasePanel.ac)
        select(self.score.Au, self.au, BasePanel.au)
        select(self.score.C, self.c, BasePanel.im)
        select(self.score.A, self.a, BasePanel.im)
        select(self.score.I, self.i, BasePanel.im)

    def set_handler(self, handler):
        self.av.Bind(wx.EVT_CHOICE, handler)
        self.ac.Bind(wx.EVT_CHOICE, handler)
        self.au.Bind(wx.EVT_CHOICE, handler)
        self.c.Bind(wx.EVT_CHOICE, handler)
        self.a.Bind(wx.EVT_CHOICE, handler)
        self.i.Bind(wx.EVT_CHOICE, handler)
        
        
class TempPanel(wx.Panel):
    e = [
         ('Unproven', 'U'),
         ('Proof of Concept', 'POC'),
         ('Functional', 'F'),
         ('High', 'H'),
         ('Not defined', 'ND')
         ]
    rl = [
         ('Official Fix', 'OF'),
         ('Temporary Fix', 'TF'),
         ('Workaround', 'W'),
         ('Not defined', 'ND')
         ]
    rc = [
         ('Not Defined', 'ND'),
         ('Unconfirmed', 'UC'),
         ('Uncorrobated', 'UR'),
         ('Confirmed', 'C'),
         ]
    
    def __init__(self, *args, **kwargs):
        super(TempPanel, self).__init__(*args, **kwargs)
        
        self.score = cvsscalc.Temporal()
        
        box = wx.StaticBox(self, -1, 'Temporal Score')
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        
        gs = wx.GridSizer(rows=3, cols=2, vgap=5, hgap=5)
        
        self.e = wx.Choice(self, choices=[a[0] for a in TempPanel.e])
        self.rl = wx.Choice(self, choices=[a[0] for a in TempPanel.rl])
        self.rc = wx.Choice(self, choices=[a[0] for a in TempPanel.rc])
        gs.AddMany([
                    (wx.StaticText(self, label='Exploitability'), 0, 0),
                    (self.e, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Remedation Level'), 0, 0),
                    (self.rl, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Report Confidence'), 0, 0),
                    (self.rc, 0, wx.EXPAND),
                    ])
        
        sizer.Add(gs, wx.EXPAND|wx.ALL)
        self.SetSizer(sizer)
        
    def update_choices(self):
        def select(val, cb, ar):
            idx = 0
            for i in ar:
                if i[1] == val:
                    cb.Select(idx)
                    break
                idx += 1
               
        select(self.score.E, self.e, TempPanel.e)
        select(self.score.RL, self.rl, TempPanel.rl)
        select(self.score.RC, self.rc, TempPanel.rc)
        
    def update_score(self):
        self.score.E = TempPanel.e[self.e.CurrentSelection][1]
        self.score.RL = TempPanel.rl[self.rl.CurrentSelection][1]
        self.score.RC = TempPanel.rc[self.rc.CurrentSelection][1]
        
    def set_handler(self, handler):
        self.e.Bind(wx.EVT_CHOICE, handler)
        self.rl.Bind(wx.EVT_CHOICE, handler)
        self.rc.Bind(wx.EVT_CHOICE, handler)

class EnvPanel(wx.Panel):
    cdp = [
           ('None', 'N'),
           ('Low', 'L'),
           ('Low-Medium', "LM"),
           ('Medium-High', 'MH'),
           ('High', 'H'),
           ('Not defined', 'ND')
        ]
    td = [
           ('None (0%)', 'N'),
           ('Low (1%-25%)', 'L'),
           ('Medium (26%-75%)', 'M'),
           ('High (76%-100%)', 'H'),
           ('Not defined', 'ND')
        ]
    req = [
           ('Low', 'L'),
           ('Medium', 'M'),
           ('High', 'H'),
           ('Not defined', 'ND')
        ]
    def __init__(self, *args, **kwargs):
        super(EnvPanel, self).__init__(*args, **kwargs)
        
        self.score = cvsscalc.Environmental()
        
        box = wx.StaticBox(self, -1, 'Environmental Score')
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        
        gs = wx.GridSizer(rows=6, cols=2, vgap=5, hgap=5)
        
        self.cdp = wx.Choice(self, choices=[a[0] for a in EnvPanel.cdp])
        self.td = wx.Choice(self, choices=[a[0] for a in EnvPanel.td])
        self.cr = wx.Choice(self, choices=[a[0] for a in EnvPanel.req])
        self.ar = wx.Choice(self, choices=[a[0] for a in EnvPanel.req])
        self.ir = wx.Choice(self, choices=[a[0] for a in EnvPanel.req])
        gs.AddMany([
                    (wx.StaticText(self, label='Colleteral Damage Potential'), 0, 0),
                    (self.cdp, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Target Distribution'), 0, 0),
                    (self.td, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Confidentiality Requirement'), 0, 0),
                    (self.cr, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Integrity Requirement'), 0, 0),
                    (self.ir, 0, wx.EXPAND),
                    (wx.StaticText(self, label='Availability Requirement'), 0, 0),
                    (self.ar, 0, wx.EXPAND),
                    ])
        
        sizer.Add(gs, wx.EXPAND)
        self.SetSizer(sizer)
        
    def update_choices(self):
        def select(val, cb, ar):
            idx = 0
            for i in ar:
                if i[1] == val:
                    cb.Select(idx)
                    break
                idx += 1
               
        select(self.score.CDP, self.cdp, EnvPanel.cdp)
        select(self.score.TD, self.td, EnvPanel.td)
        select(self.score.CR, self.cr, EnvPanel.req)
        select(self.score.AR, self.ar, EnvPanel.req)
        select(self.score.IR, self.ir, EnvPanel.req)
        
    def update_score(self):
        self.score.CDP = EnvPanel.cdp[self.cdp.CurrentSelection][1]
        self.score.TD = EnvPanel.td[self.td.CurrentSelection][1]
        self.score.CR = EnvPanel.req[self.cr.CurrentSelection][1]
        self.score.AR = EnvPanel.req[self.ar.CurrentSelection][1]
        self.score.IR = EnvPanel.req[self.ir.CurrentSelection][1]
    
    def set_handler(self, handler):
        self.cdp.Bind(wx.EVT_CHOICE, handler)
        self.td.Bind(wx.EVT_CHOICE, handler)
        self.cr.Bind(wx.EVT_CHOICE, handler)
        self.ar.Bind(wx.EVT_CHOICE, handler)
        self.ir.Bind(wx.EVT_CHOICE, handler)


        
class ScoreGauge(ColorGauge):
    def __init__(self, *args, **kwargs):
        super(ScoreGauge, self).__init__(*args, **kwargs)
        
        self.add_color_key(0, 'green')
        self.add_color_key(40, 'yellow')
        self.add_color_key(70, 'red')
        
    def set_score(self, score):
        self.SetValue(score*10)

class ScorePanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScorePanel, self).__init__(*args, **kwargs)
        
        sizer = wx.GridSizer(rows=4, cols=3, vgap=5, hgap=5)
        
        self.base_gauge = ScoreGauge(self)
        self.base_gauge.set_score(0)
        self.base = wx.StaticText(self, label='0')
        self.tmp_gauge = ScoreGauge(self)
        self.tmp_gauge.set_score(0)
        self.tmp = wx.StaticText(self, label='0')
        self.env_gauge = ScoreGauge(self)
        self.env_gauge.set_score(0)
        self.env = wx.StaticText(self, label='0')
        self.total_gauge = ScoreGauge(self)
        self.total_gauge.set_score(0)
        self.total = wx.StaticText(self, label='0')
        
        sizer.AddMany([
                       (wx.StaticText(self, label='Base Score'), 0, 0),
                       (self.base_gauge, 0, wx.EXPAND ),
                       (self.base, 0, wx.EXPAND ),
                       (wx.StaticText(self, label='Temporal Score'), 0, 0),
                       (self.tmp_gauge, 0, wx.EXPAND ),
                       (self.tmp, 0, wx.EXPAND ),
                       (wx.StaticText(self, label='Environmental Score'), 0, 0),
                       (self.env_gauge, 0, wx.EXPAND ),
                       (self.env, 0, wx.EXPAND ),
                       (wx.StaticText(self, label='Total Score'), 0, 0),
                       (self.total_gauge, 0, wx.EXPAND ),
                       (self.total, 0, wx.EXPAND ),
                       ])
        
        self.SetSizer(sizer)

def main(infile=None):
    app = wx.App()
    frame = MainFrame(None, wx.ID_ANY, title='CVSS Calculator')
    app.TopWindow = frame
    if infile:
        frame.load_from_file(infile)
        frame.update_choices()
        frame.refresh_score()
    frame.Show()
    app.MainLoop()
    
if __name__ == '__main__':
    main()
