#!/usr/bin/env python2

import inspect
import sys

def get_user_attributes(cls):
    """
    
    Keyword arguments:
    cls -- 
    
    """
    boring = dir(type('dummy', (object,), {}))
    return [item
            for item in inspect.getmembers(cls, lambda x: not inspect.ismethod(x))
            if item[0] not in boring]

class Score:
    def __init__(self, string=None):
        """Constructor
        
        Keyword arguments:
        string -- (Default: None)
        
        """
        self.from_string(string)
                    
    def from_string(self, string):
        """
        
        Keyword arguments:
        string -- 
        
        """
        cls_vars = get_user_attributes(self.__class__)
        if not string:
            for var, val in cls_vars:
                self.__dict__[var] = None
        else: 
            data = dict([d.strip().split(':') for d in string.strip(' ()').split('/')])
            for var, val in cls_vars:
                if var in data:
                    self.__dict__[var] = data[var]
                else:
                    self.__dict__[var] = None

                    
    def __str__(self):
        """
        
        Keyword arguments:
        
        """
        cls_vars = get_user_attributes(self.__class__)
        
        tmp = []
        for name, val in cls_vars:
            if self.__dict__[name]:
                tmp.append('%s:%s' % (name, self.__dict__[name]))
            else:
                tmp.append('0')
        
        return ' / '.join(tmp)
            
class Base(Score):
    AV = {
        'L' : 0.395,
        'A' : 0.646,
        'N' : 1.0
        }
    AC = {
        'H' : 0.35,
        'M' : 0.61,
        'L' : 0.71
        }
    Au = {
        'M' : 0.45,
        'S' : 0.56,
        'N' : 0.704
        }
    C = A = I = {
        'N' : 0.0,
        'P' : 0.275,
        'C' : 0.660
        }
        
    def get_score(self):
        """
        
        Keyword arguments:
        
        """
        impact = 10.41 * (1 - 
                (1 - Base.C[self.C]) * 
                (1 - Base.I[self.I]) * 
                (1 - Base.A[self.A]))
        exploit = 20 * (Base.AV[self.AV] * 
                        Base.AC[self.AC] * 
                        Base.Au[self.Au])
        f_impact = impact and 1.176
        
        return round(((0.6 * impact) + (0.4 * exploit) - 1.5) * f_impact, 1) 
    
    def __str__(self):
        """
        
        Keyword arguments:
        
        """
        return 'AV:%s / AC:%s / Au:%s / C:%s / I:%s / A:%s' % (self.AV,
                self.AC, self.Au, self.C, self.I, self.A)

    def from_string(self, string):
        cls_vars = get_user_attributes(self.__class__)
        if not string:
            for var, val in cls_vars:
                self.__dict__[var] = None
        else: 
            data = dict([d.strip().split(':') for d in string.strip(' ()').split('/')])
            if data['AV'] == 'AN':
                data['AV'] = 'A'
            for var, val in cls_vars:
                if var in data:
                    self.__dict__[var] = data[var]
                else:
                    self.__dict__[var] = None


                    
class Temporal(Score):
    E = {
        'U'  : 0.85,
        'POC': 0.9,
        'F'  : 0.95,
        'H'  : 1.0,
        'ND'  : 1.0
        }
    RL = {
        'OF' : 0.87,
        'TF' : 0.9,
        'W'  : 0.95,
        'U'  : 1.0,
        'ND'  : 1.0
        }
    RC = {
        'UC' : 0.9,
        'UR' : 0.95,
        'C'  : 1.0,
        'ND' : 1.0
        }
        
    def get_score(self, base):
        """
        
        Keyword arguments:
        base -- 
        
        """
        if isinstance(base, Base):
            base = base.get_score()
        
        return round(base * 
                Temporal.E[self.E] * 
                Temporal.RL[self.RL] * 
                Temporal.RC[self.RC], 1)
        
    def __str__(self):
        """
        
        Keyword arguments:
        
        """
        return 'E:%s / RL:%s / RC:%s' % (self.E,
                self.RL, self.RC)
        
class Environmental(Score):
    CDP = {
        'N'  : 0.0,
        'L'  : 0.1,
        'LM' : 0.3,
        'MH' : 0.4,
        'H'  : 0.5,
        'ND' : 0.0 
        }
    TD = {
        'N'  : 0.0,
        'L'  : 0.25,
        'M'  : 0.75,
        'H'  : 1.0,
        'ND' : 1.0
        }
    CR = IR = AR = {
        'L'  : 0.5,
        'M'  : 1.0,
        'H'  : 1.51,
        'ND' : 1.0
        }
    
    def get_score(self, base, temp):
        """
        
        Keyword arguments:
        base -- 
        temp -- 
        
        """
        adj_impact = min(10,
            10.41 * (1 - 
                (1 - Base.C[base.C] * Environmental.CR[self.CR]) * 
                (1 - Base.I[base.I] * Environmental.IR[self.IR]) * 
                (1 - Base.A[base.A] * Environmental.AR[self.AR])))
        exploit = (20 * (Base.AV[base.AV] * 
                        Base.AC[base.AC] * 
                        Base.Au[base.Au]))
        f_impact = adj_impact and 1.176
        
        adj_base = round(((0.6 * adj_impact) + (0.4 * exploit) - 1.5) * f_impact, 1)
        
        tmp_score = temp.get_score(adj_base)
        
        return round((tmp_score + (10 - tmp_score) * 
            Environmental.CDP[self.CDP]) * Environmental.TD[self.TD], 1)
                
    def __str__(self):
        """
        
        Keyword arguments:
        
        """
        return 'CDP:%s / TD:%s / CR:%s / IR:%s / AR:%s' % (self.CDP,
                self.TD, self.CR, self.IR, self.AR)
class Cvss2:
    
            
    def __init__(self):
        """Constructor
        
        Keyword arguments:
        
        """
        self.base = Base()
        self.tmp = Temporal()
        self.env = Environmental()
    
    def get_score(self):
        """
        
        Keyword arguments:
        
        """
        return self.env.get_score(self.base, self.tmp)


def main(fp, out=sys.stdout):
    """
    
    Keyword arguments:
    fp -- 
    out -- (Default: sys.stdout)
    
    """
    import os.path
    lines = fp.readlines()
    fp.close()
    
    cvss = Cvss2()
    cvss.base = Base(lines[3])
    cvss.tmp = Temporal(lines[4])
    cvss.env = Environmental(lines[5])
    
    score = cvss.get_score()
    out.writelines(lines[:3])
    out.write(str(cvss.base) + "\n")
    out.write(str(cvss.tmp) + "\n")
    out.write(str(cvss.env) + "\n")
    out.writelines(lines[6:9])
    out.write(str(score) + "\n")
    if score < 4.0:
        out.write('Low\n')
    elif score >= 7:
        out.write('High\n')
    else:
        out.write('Medium\n')

if __name__ == '__main__':
    fp = open(sys.argv[1])

    main(fp)

# vim: set ts=4 sw=4 tw=79 :

