'''
Created on Oct 21, 2011

@author: bluec0re
'''
from __future__ import absolute_import, division


import os.path
import sys
import zipfile
import functools
import tempfile
import wx
import re
from wx import xrc

from cvsscalc import cvsscalc
from wx.lib.masked import TimeCtrl

try:
    import wx.lib.agw.pygauge as PG
    
    class ColorGauge(PG.PyGauge):
        def __init__(self, *args, **kwargs):
            """Constructor
            
            Keyword arguments:
            *args -- 
            **kwargs -- 
            
            """
            super(ColorGauge, self).__init__(*args, **kwargs)
            self.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
            col = wx.Color()
            col.SetFromString('grey')
            self.SetBorderColor(col)
            self.SetBorderPadding(2)
            self._keys = {}
            
        def add_color_key(self, pos, color):
            """Adds a new color keypoint
            
            Keyword arguments:
            pos -- Position where the color starts
            color -- which color
            
            """
            if isinstance(color, int):
                color = '#%06x' % color
            col = wx.Color()
            col.SetFromString(color)
            self._keys[pos] = col
        
        def SetValue(self, pos):
            """Sets the new gauge value
            
            Keyword arguments:
            pos -- gauge value
            
            """
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
            """Dummy function. Does nothing
            """
            pass

def find_file(path, mode='r'):
    """Find the file named path in the sys.path.
    Returns the full path name if found, None if not found"""
    for dirname in sys.path:
        if os.path.isfile(dirname):
            zf = zipfile.ZipFile(dirname, mode='r')
            if path in zf.namelist():
                data = zf.read(path)
                zf.close()
                return data

            continue

        possible = os.path.join(dirname, path)
        if os.path.isfile(possible):
            with open(possible, mode) as fp:
                return fp.read()
    return None


class ScoreGauge(ColorGauge):
    def __init__(self, *args, **kwargs):
        """Constructor
        
        Keyword arguments:
        *args -- 
        **kwargs -- 
        
        """
        super(ScoreGauge, self).__init__(*args, **kwargs)
        
        self.add_color_key(0, 'green')
        self.add_color_key(40, 'yellow')
        self.add_color_key(70, 'red')
        
    def set_score(self, score):
        """Wrapper around SetValue.
        
        Keyword arguments:
        score -- 
        
        """
        self.SetValue(score*10)
     

class TimeCtrlHandler(xrc.XmlResourceHandler):
    def __init__(self):
        """Constructor
        
        
        """
        xrc.XmlResourceHandler.__init__(self)
        # Standard styles
        self.AddWindowStyles()
        # Custom styles
        
    def CanHandle(self,node):
        """returns True if this Handler can handle the given node
        
        Keyword arguments:
        node -- 
        
        """
        return self.IsOfClass(node, 'TimeCtrl')
    
    def DoCreateResource(self):
        """Creates a new Resource
        
        
        """
        assert self.GetInstance() is None
        w = TimeCtrl(parent=self.GetParentAsWindow(),
                     id=self.GetID(),
                     pos=self.GetPosition(),
                     size=self.GetSize(),
                     style=self.GetStyle())
        if self.GetText('value'):
            w.SetValue(self.GetText('value'))
        else:
            w.SetValue(wx.DateTime.Now())
        self.SetupWindow(w)
        return w
    
        
class ScoreGaugeHandler(xrc.XmlResourceHandler):
    def __init__(self):
        """Constructor
        
        
        """
        xrc.XmlResourceHandler.__init__(self)
        # Standard styles
        self.AddWindowStyles()
        # Custom styles
        self.AddStyle('wxGA_HORIZONTAL', wx.GA_HORIZONTAL)
        
        
    def CanHandle(self,node):
        """
        
        Keyword arguments:
        node -- 
        
        """
        return self.IsOfClass(node, 'ScoreGauge')
    
    def DoCreateResource(self):
        """
        
        
        """
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
            'av' : (
                  ('Local', 'L'),
                  ('Adjacent Network', 'AN'),
                  ('Network', 'N')
                  ),
            'ac' : (
                  ('Low', 'L'),
                  ('Medium', 'M'),
                  ('High', 'H')
                  ),
            'au' : (
                  ('None', 'N'),
                  ('Single', 'S'),
                  ('Multiple', 'M')
                  ),
            'c' : (
                  ('None', 'N'),
                  ('Partial', 'P'),
                  ('Complete', 'C')
                  ),
            'i' : (
                  ('None', 'N'),
                  ('Partial', 'P'),
                  ('Complete', 'C')
                  ),
            'a' : (
                  ('None', 'N'),
                  ('Partial', 'P'),
                  ('Complete', 'C')
                  )
            }
    
    temp = {
            'e' : (
                 ('Unproven', 'U'),
                 ('Proof of Concept', 'POC'),
                 ('Functional', 'F'),
                 ('High', 'H'),
                 ('Not defined', 'ND')
                 ),
            'rl' : (
                 ('Official Fix', 'OF'),
                 ('Temporary Fix', 'TF'),
                 ('Workaround', 'W'),
                 ('Not defined', 'ND')
                 ),
            'rc' : (
                 ('Not Defined', 'ND'),
                 ('Unconfirmed', 'UC'),
                 ('Uncorrobated', 'UR'),
                 ('Confirmed', 'C'),
                 ),
            }
    
    env = {
           'cdp' : (
                   ('None', 'N'),
                   ('Low', 'L'),
                   ('Low-Medium', "LM"),
                   ('Medium-High', 'MH'),
                   ('High', 'H'),
                   ('Not defined', 'ND')
                ),
            'td' : (
                   ('None (0%)', 'N'),
                   ('Low (1%-25%)', 'L'),
                   ('Medium (26%-75%)', 'M'),
                   ('High (76%-100%)', 'H'),
                   ('Not defined', 'ND')
                ),
            'cr' : (
                   ('Low', 'L'),
                   ('Medium', 'M'),
                   ('High', 'H'),
                   ('Not defined', 'ND')
                ),
            'ir' : (
                   ('Low', 'L'),
                   ('Medium', 'M'),
                   ('High', 'H'),
                   ('Not defined', 'ND')
                ),
            'ar' : (
                   ('Low', 'L'),
                   ('Medium', 'M'),
                   ('High', 'H'),
                   ('Not defined', 'ND')
                )
           }
            
    def OnInit(self):
        """Sets up the gui
        
        
        """
        # initialises the cvsss2 handler
        self.base_score = cvsscalc.Base()
        self.temp_score = cvsscalc.Temporal()
        self.env_score = cvsscalc.Environmental()

        # flag for determining if the gui has changed
        self.modified = False
        # last filename
        self.fname = None
        
        # read the xml file
        content = find_file('cvsscalc/xrcgui.xrc')
        self.res = xrc.EmptyXmlResource()
        # add custom control handler
        self.res.AddHandler(TimeCtrlHandler())
        self.res.AddHandler(ScoreGaugeHandler())
        # load the gui
        self.res.LoadFromString(content)
        
        # receive windows
        self.frame = self.res.LoadFrame(None, 'MyFrame')
        self.set_title('CVSS Calculator')
        self.base_panel = xrc.XRCCTRL(self.frame, 'base_panel')
        self.env_panel = xrc.XRCCTRL(self.frame, 'env_panel')
        self.temp_panel = xrc.XRCCTRL(self.frame, 'temp_panel')
        self.util_panel = xrc.XRCCTRL(self.frame, 'util_panel')
        self.score_panel = xrc.XRCCTRL(self.frame, 'score_panel')
        self.load_panel = xrc.XRCCTRL(self.frame, 'load_panel')
        
        # setup panels
        self.setup_panel(self.base_panel)
        self.setup_panel(self.temp_panel)
        self.setup_panel(self.env_panel)
        
        # update score panel
        self.update_scores()
        self.refresh_score()
        
        
        icon_content = find_file('cvsscalc/cvsscalc.ico', mode='rb')
        tmpfile = tempfile.mkstemp()
        os.write(tmpfile[0], icon_content)
        os.close(tmpfile[0])
        self.frame.SetIcon(wx.Icon(tmpfile[1], wx.BITMAP_TYPE_ANY))
        os.unlink(tmpfile[1])

        # resize and show
        self.frame.Fit()
        self.frame.Show()
        
        # connect keybindings
        self.bind_keys()
        
        return True
    
    def setup_panel(self, panel):
        """Initializes a panel
        
        Keyword arguments:
        panel -- panel which has choice and button controls
        
        """
        # load question icon
        pic = wx.ArtProvider.GetBitmap(wx.ART_QUESTION)
        # get panel name, eg. base of base_panel
        panel_name,_ = panel.GetName().split('_')
        for child in panel.GetChildren():
            # choice control found
            if isinstance(child, wx.Choice):
                choice = child # save current choice for tooltip

                # get choice name, eg. av of av_choice
                choice_name,_ = child.GetName().split('_')
                
                # get data for choice
                items = MyApp.__dict__[panel_name.encode()][choice_name.encode()]
                # insert strings
                for item in items:
                    child.Append(item[0])
                # select first element
                child.SetSelection(0)
                # bind onchoice
                child.Bind(wx.EVT_CHOICE, self.OnChoice)
            # button found
            elif isinstance(child, wx.BitmapButton):
                # set questionmark icon
                child.SetBitmapLabel(pic)
                # get btn name, eg. av of av_help_btn
                btn_name,_,_ = child.GetName().split('_')
                
                # get data for tooltip
                items = MyApp.__dict__[panel_name.encode()][btn_name.encode()]
                # add tooltip and help text
                self.add_tooltip(choice, child, panel_name, btn_name, items)
                
    def update_score(self, panel):
        """Update the score item with selection of panel
        
        Keyword arguments:
        panel -- panel with choice fields
        
        """
        # get panel name, eg. base of base_panel
        panel_name,_ = panel.GetName().split('_')
        for child in panel.GetChildren():
            # choice control found
            if isinstance(child, wx.Choice):
                # get choice name, eg. av of av_choice
                choice_name,_ = child.GetName().split('_')
                
                # get data of choice
                items = MyApp.__dict__[panel_name.encode()][choice_name.encode()]
                
                # get corresponding score object
                score = getattr(self, '%s_score' % panel_name)
                
                # find object field
                if choice_name in score.__dict__:
                    attr_name = choice_name
                elif choice_name.upper() in score.__dict__:
                    attr_name = choice_name.upper()
                elif choice_name.capitalize() in score.__dict__:
                    attr_name = choice_name.capitalize()
                # set value
                setattr(score, attr_name, items[child.GetSelection()][1])
    
    def update_panel_choices(self, panel):
        """Updates the selection of choice fields of panel
        
        Keyword arguments:
        panel -- panel with choice fields
        
        """
        def select(val, cb, ar):
            """select val in cb 
            
            Keyword arguments:
            val -- value to select
            cb -- choice control
            ar -- map with (<choice value>,<val>) elements
            
            """
            idx = 0
            for i in ar:
                if i[1] == val:
                    cb.Select(idx)
                    break
                idx += 1
        
        # get panel name, eg. base of base_panel
        panel_name,_ = panel.GetName().split('_')
        for child in panel.GetChildren():
            # choice control found
            if isinstance(child, wx.Choice):
                # get choice name, eg. av of av_choice
                choice_name,_ = child.GetName().split('_')
                
                # get data of choice
                items = MyApp.__dict__[panel_name.encode()][choice_name.encode()]
                
                # get corresponding score object
                score = getattr(self, '%s_score' % panel_name)
                
                # find object field
                if choice_name in score.__dict__:
                    attr_name = choice_name
                elif choice_name.upper() in score.__dict__:
                    attr_name = choice_name.upper()
                elif choice_name.capitalize() in score.__dict__:
                    attr_name = choice_name.capitalize()
                # change selection of choice control
                select(getattr(score, attr_name), child, items)
    
    def update_scores(self):
        """Updates all scores
        """
        self.update_score(self.base_panel)
        self.update_score(self.temp_panel)
        self.update_score(self.env_panel)
        
    def bind_keys(self):
        """Binds all keys
        """
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        xrc.XRCCTRL(self.util_panel, 'load_btn').Bind(wx.EVT_BUTTON, self.OnLoad)
        xrc.XRCCTRL(self.util_panel, 'save_btn').Bind(wx.EVT_BUTTON, self.OnSave)
        xrc.XRCCTRL(self.util_panel, 'copy_btn').Bind(wx.EVT_BUTTON, self.OnCopy)
        self.frame.Bind(wx.EVT_CLOSE, self.OnClose)
        xrc.XRCCTRL(self.load_panel, 'load_base_score_btn').Bind(wx.EVT_BUTTON, 
                    functools.partial(self.OnStringLoad, 
                                      xrc.XRCCTRL(self.load_panel, 'base_score_str'),
                                      self.base_score))
        xrc.XRCCTRL(self.load_panel, 'load_temp_score_btn').Bind(wx.EVT_BUTTON, 
                    functools.partial(self.OnStringLoad, 
                                      xrc.XRCCTRL(self.load_panel, 'temp_score_str'),
                                      self.temp_score))
        xrc.XRCCTRL(self.load_panel, 'load_env_score_btn').Bind(wx.EVT_BUTTON, 
                    functools.partial(self.OnStringLoad, 
                                      xrc.XRCCTRL(self.load_panel, 'env_score_str'),
                                      self.env_score))
        xrc.XRCCTRL(self.load_panel, 'load_all_scores_btn').Bind(wx.EVT_BUTTON, 
                    self.OnStringLoadAll)
        xrc.XRCCTRL(self.load_panel, 'load_block_btn').Bind(wx.EVT_BUTTON, 
                    self.OnStringLoadBlock)
        
        
    def OnStringLoad(self, textctrl, score, event=None):
        score.from_string(textctrl.GetValue())
        self.update_choices()
        self.refresh_score()
        
    def OnStringLoadAll(self, event=None):
        self.OnStringLoad(xrc.XRCCTRL(self.load_panel, 'base_score_str'), self.base_score, event)
        self.OnStringLoad(xrc.XRCCTRL(self.load_panel, 'env_score_str'), self.env_score, event)
        self.OnStringLoad(xrc.XRCCTRL(self.load_panel, 'temp_score_str'), self.temp_score, event)
        
    def OnStringLoadBlock(self, tevent=None):
        block_text = xrc.XRCCTRL(self.load_panel, 'cvss_block_ctrl').GetValue()
        regex = re.compile(r'\(((([a-zA-Z]+:[a-zA-Z]+|-) / )+([a-zA-Z]+:[a-zA-Z]+|-))\)')
        file_regex = re.compile(r'^.+\s(.+\.cvss)$')
        
        for line in block_text.split('\n'):
            line = line.strip()
            
            m = regex.search(line)
            if m:
                if len(m.group(1).split('/')) == 6:
                    self.base_score.from_string(m.group(1))
                elif len(m.group(1).split('/')) == 3:
                    self.temp_score.from_string(m.group(1))
                elif len(m.group(1).split('/')) == 5:
                    self.env_score.from_string(m.group(1))
            m = file_regex.search(line)
            if m:
                self.fname = m.group(1)
                self.set_title('CVSS Calculator [{0}*]', os.path.abspath(self.fname))

        self.update_choices()
        self.refresh_score()
    
    def OnKey(self, event):
        """Called on KEY_EVENT
        
        Keyword arguments:
        event -- the key event
        
        """
        # CTRL pressed?
        if event.ControlDown():
            # CTRL+c => copy
            if event.GetKeyCode() == ord('c') or event.GetKeyCode() == ord('C'):
                self.OnCopy()
            # CTRL+s => save
            elif event.GetKeyCode() == ord('s') or event.GetKeyCode() == ord('S'):
                self.OnSave(save_old=(not event.ShiftDown()))
            # CTRL+o => open
            elif event.GetKeyCode() == ord('o') or event.GetKeyCode() == ord('O'):
                self.OnLoad()
            # execute next handler
            else:
                event.Skip()
        # execute next handler
        else:
            event.Skip()
            
    def OnClose(self, event=None):
        """Called on window close
        
        Keyword arguments:
        event -- (Default: None)
        
        """
        # not saved modifications
        if self.modified:
            ret = wx.MessageBox('File was not save!\nSave it now?',
                    'Not saved', wx.YES_NO | wx.CANCEL | wx.ICON_EXCLAMATION)

            # save file
            if ret == wx.YES:
                self.OnSave(save_old=True)
            # remain open
            elif ret == wx.CANCEL:
                return
        # close window
        self.frame.Destroy()
    
    def OnChoice(self, event=None):
        """Choice control has changed
        
        Keyword arguments:
        event -- (Default: None)
        
        """
        # recalculate and update score panel
        self.update_scores()
        self.refresh_score()
        # set mod flag
        self.modified = True

        # update title
        if self.frame.GetTitle().endswith(']'):
            self.set_title(self.frame.GetTitle()[:-1] + '*]')
        else:
            self.set_title(self.frame.GetTitle() + '[<never saved before>*]')
        
    def OnLoad(self, event=None):
        """Called on Load btn or CTRL+o
        
        Keyword arguments:
        event -- (Default: None)
        
        """
        # show file select dialog
        fd = wx.FileDialog(self.frame, wildcard='*.cvss', style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        fd.ShowModal()
        
        fname = fd.GetPath()
        
        # nothing selected
        if fname == '':
            return

        # load file
        with open(fname, 'r') as fp:
            self.load_from_file(fp)
        # update choice controls and score panel
        self.update_choices()
        self.refresh_score()

    def load_from_file(self, fp):
        """Load from file
        
        Keyword arguments:
        fp -- file like object
        
        """
        lines = fp.readlines()
        idx = 1
        # skip cvss 1
        if fp.name.endswith('.cvss'):
            idx = 3
        # parse scores
        self.base_score.from_string(lines[idx])
        self.temp_score.from_string(lines[idx+1])
        self.env_score.from_string(lines[idx+2])

        # parse date
        date = wx.DateTime()
        date.ParseFormat(format='%m/%d/%Y %H:%M:%S', date=lines[7].strip())
       
        # set values
        xrc.XRCCTRL(self.util_panel, 'date_ctrl').SetValue(date)
        xrc.XRCCTRL(self.util_panel, 'time_ctrl').SetValue(date)
        xrc.XRCCTRL(self.util_panel, 'author_ctrl').SetValue(lines[8].strip())

        # save filename
        self.fname = os.path.basename(fp.name)
        # change cwd
        if os.path.dirname(fp.name):
            os.chdir(os.path.dirname(fp.name))

        # update mod flag and title
        self.modified = False
        self.set_title('CVSS Calculator [{0}]', fp.name)
            
    
    def OnSave(self, event=None, save_old=False):
        """Called on save btn or CTRL+s
        
        Keyword arguments:
        event -- (Default: None)
        save_old -- save to old file if possible (Default: False)
        
        """
        if not save_old or not self.fname:
            # open file select dialog
            cur_dir = os.getcwd()
            fd = wx.FileDialog(self.frame, wildcard='*.cvss',
                    style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
                    defaultDir=cur_dir, defaultFile=self.fname)
            fd.ShowModal()
            fname = fd.GetPath()
        else:
            fname = os.path.join(os.getcwd(), self.fname)

        # no file selected
        if fname == '':
            return

        # append .cvss
        if not fname.endswith('.cvss'):
            fname += '.cvss'
        
        # get values
        name = xrc.XRCCTRL(self.util_panel, 'author_ctrl').GetValue()
        date = xrc.XRCCTRL(self.util_panel, 'date_ctrl').GetValue()
        time = xrc.XRCCTRL(self.util_panel, 'time_ctrl').GetValue(as_wxTimeSpan=True)
        date.SetHour(0)
        date.SetMinute(0)
        date.SetSecond(0)
        date.AddTS(time)
        
        # write to file
        with open(fname, 'w') as fp:
            # cvss 1
            fp.write('- / - / - / - / - / - / -\r\n')
            fp.write('- / - / -\r\n')
            fp.write('- / -\r\n')
            # cvss 2
            fp.write(str(self.base_score) + '\r\n')
            fp.write(str(self.temp_score) + '\r\n')
            fp.write(str(self.env_score) + '\r\n')
            fp.write('%s\r\n' % os.path.basename(fname).replace('_', ' ')[:-5]) # Desc
            fp.write(date.Format('%m/%d/%Y %H:%M:%S') + '\r\n')
            fp.write(name + '\r\n') # auditor
            # score
            score = self.get_total_score()
            fp.write('%.1f\n' % score)
            # severity
            if score < 4:
                fp.write('Low\n')
            elif score >= 7:
                fp.write('High\n')
            else:
                fp.write('Medium\n')
            # remember filename
            self.fname = os.path.basename(fname)
            # change cwd
            os.chdir(os.path.dirname(fname))
            # update mod flag and title
            self.modified = False
            self.set_title('CVSS Calculator [{0}]', fp.name)
                
    
    def OnCopy(self, event=None):
        """Called on Copy btn or CTRL+c
        
        Keyword arguments:
        event -- (Default: None)
        
        """
        # get copy type
        target = xrc.XRCCTRL(self.util_panel, 'copy_choice').GetSelection()
        
        # collect data
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
        
        # insert into clipboard
        if not wx.TheClipboard.IsOpened():
            wx.TheClipboard.Open()
            
        do = wx.TextDataObject()
        do.SetText(string)
        wx.TheClipboard.SetData(do)
        wx.TheClipboard.Close()
        
    
    def update_choices(self):
        """Update all choice controls
        """
        self.update_panel_choices(self.base_panel)
        self.update_panel_choices(self.temp_panel)
        self.update_panel_choices(self.env_panel)
    
    def refresh_score(self):
        """update score panel
        """
        # shortcuts
        base = self.base_score
        tmp = self.temp_score
        env = self.env_score
        # update panel controls
        xrc.XRCCTRL(self.score_panel, 'base_score').SetLabel('%.2f' % base.get_score())
        xrc.XRCCTRL(self.score_panel, 'base_gauge').SetValue(base.get_score() * 10)
        xrc.XRCCTRL(self.score_panel, 'temp_score').SetLabel('%.2f' % tmp.get_score(base))
        xrc.XRCCTRL(self.score_panel, 'temp_gauge').SetValue(tmp.get_score(base) * 10)
        xrc.XRCCTRL(self.score_panel, 'env_score').SetLabel('%.2f' % env.get_score(base, tmp))
        xrc.XRCCTRL(self.score_panel, 'env_gauge').SetValue(env.get_score(base, tmp) * 10)
        xrc.XRCCTRL(self.score_panel, 'total_score').SetLabel('%.2f' % env.get_score(base, tmp))
        xrc.XRCCTRL(self.score_panel, 'total_gauge').SetValue(env.get_score(base, tmp) * 10)
        
    def get_total_score(self):
        """Calculate total score
        """
        # shortcuts
        base = self.base_score
        tmp = self.temp_score
        env = self.env_score
        
        return env.get_score(base, tmp)
    
    def add_tooltip(self, choice, btn, panel, name, data):
        """Add a tooltip to choice control and button
        
        Keyword arguments:
        choice -- the choice control
        btn -- the help button
        panel -- the panel name (str, eg. base)
        name -- the choice name (str, eg. av)
        data -- the choice data
        """
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
            """Onclick handler for help btn
            
            Keyword arguments:
            txt -- help text
            event -- 
            
            """
            wx.MessageBox(txt)

        btn.Bind(wx.EVT_BUTTON, functools.partial(onclick, txt))

    def set_title(self, new_title, path=None):
        if path:
            if len(path) > 75:
                segments = path.split(os.sep)
                while len(path) > 75:
                    del segments[len(segments) // 2]
                    path = segments[:len(segments) // 2]
                    path.append('...')
                    path += segments[len(segments) // 2:]
                    path = os.path.join(*path)
            new_title = new_title.format(path)

        self.frame.SetTitle(new_title)


def main(infile=None):
    """main function
    
    Keyword arguments:
    infile -- file like object to load (Default: None)
    
    """
    app = MyApp()
    if infile:
        app.load_from_file(infile)
        app.update_choices()
        app.refresh_score()
    app.MainLoop()
    
if __name__ == '__main__':
    main()
