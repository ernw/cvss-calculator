# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 set ts=4 sw=4 tw=79 : 
'''
Created on Nov 15, 2011

@author: bluec0re
'''

class Strings(object):
    cur_instance = None
    
    @classmethod
    def instance(cls):
        if not cls.cur_instance:
            cls.cur_instance = Strings()
        return cls.cur_instance
    
    def __init__(self):
        self.en = dict()
        self.de = {
                   'The severity rating based on CVSS Version 2' : 'Die Kritikalitätsbewertung nach CVSS Version 2 ergibt sich wie folgt',
                   'Reference File' : 'Referenz Datei',
                   'Base Vector' : 'Basis Wert',
                   'Temporal Vector' : 'Temporärer Wert',
                   'Environmental Vector' : 'Umgebungs Wert',
                   'CVSS Version 2 Score' : 'CVSS Version 2 Wert',
                   'Severity' : 'Kritikalität',
                   'Low' : 'Niedrig',
                   'Medium' : 'Mittel',
                   'High' : 'Hoch' 
                   }
        self.set_lang(self.de)
        
    def set_lang(self, lang):
        self.lang = lang
        
    def __getattr__(self, item):
        return self.lang.get(item, item)
        
    def __getitem__(self, item):
        return self.lang.get(item, item)