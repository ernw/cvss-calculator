# -*- coding: utf-8 -*-
# vim: fileencoding=utf-8 ts=4 sw=4 tw=79 : 
'''
Created on Nov 15, 2011

@author: bluec0re
'''


class Singleton(object):
    @classmethod
    def instance(cls):
        if not hasattr(cls,'cur_instance') or not cls.cur_instance:
            cls.cur_instance = cls()
        return cls.cur_instance
    

class I18N(Singleton):
    def set_lang(self, lang):
        lang = getattr(self, lang)
        self.lang = lang
        
    def __getattr__(self, item):
        return self.lang.get(item, item)
        
    def __getitem__(self, item):
        return self.lang.get(item, item)


class Strings(I18N):
    def __init__(self):
        self.en = dict()
        self.de = {
                   'The severity rating based on CVSS Version 2' : u'Die Bewertung nach CVSS Version 2 ergibt sich wie folgt',
                   'Reference File' : u'Referenzdatei',
                   'Base Vector' : u'Base Vector',
                   'Temporal Vector' : u'Temporal Vector',
                   'Environmental Vector' : u'Environmental Vector',
                   'CVSS Version 2 Score' : u'CVSS Version 2 Score',
                   'Severity' : u'Relevanz',
                   'Low' : u'Niedrig',
                   'Medium' : u'Mittel',
                   'High' : u'Hoch' 
                   }
        self.set_lang('en')
        
class Format(I18N):
    def __init__(self):
        self.en = {
                'word' :{
                    'refFile' : '%s\t\t\t%s',
                    'base' : '%s\t\t\t(%s)',
                    'base_score' : 'Base Score:\t\t\t%s',
                    'temp' : '%s\t\t\t(%s)',
                    'temp_score' : 'Temp Score\t\t\t%s',
                    'env' : '%s\t\t(%s)',
                    'score' : '%s\t\t%s',
                    'severity' : '%s\t\t\t\t%s'
                    }
                }
        self.de = {
                'word' :{
                    'refFile' : '%s\t\t\t%s',
                    'base' : '%s\t\t\t(%s)',
                    'base_score' : 'Base Score:\t\t\t%s',
                    'temp' : '%s\t\t\t(%s)',
                    'temp_score' : 'Temp Score\t\t\t%s',
                    'env' : '%s\t\t(%s)',
                    'score' : '%s\t\t%s',
                    'severity' : '%s\t\t\t\t%s'
                    }
                }
        self.set_lang('en')
