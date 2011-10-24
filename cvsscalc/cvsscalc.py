#!/usr/bin/env python2

import inspect

def get_user_attributes(cls):
    boring = dir(type('dummy', (object,), {}))
    return [item
            for item in inspect.getmembers(cls, lambda x: not inspect.ismethod(x))
            if item[0] not in boring]

class Score:
    def __init__(self, string=None):
        self.from_string(string)
                    
    def from_string(self, string):
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
        'AN': 0.646,
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
        impact = 10.41 * (1 - 
                (1 - Base.C[self.C]) * 
                (1 - Base.I[self.I]) * 
                (1 - Base.A[self.A]))
        exploit = 20 * (Base.AV[self.AV] * 
                        Base.AC[self.AC] * 
                        Base.Au[self.Au])
        f_impact = impact and 1.176
        
        return round(((0.6 * impact) + (0.4 * exploit) - 1.5) * f_impact, 1) 
                    
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
        if isinstance(base, Base):
            base = base.get_score()
        
        return (base * 
                Temporal.E[self.E] * 
                Temporal.RL[self.RL] * 
                Temporal.RC[self.RC])
        
        
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
            Environmental.CDP[self.CDP]) * Environmental.TD[self.TD])
                
class Cvss2:
    
            
    def __init__(self):
        self.base = Base()
        self.tmp = Temporal()
        self.env = Environmental()
    
    def get_score(self):
        return self.env.get_score(self.base, self.tmp)


def main(fp):
    import os.path
    lines = fp.readlines()
    fp.close()
    
    cvss = Cvss2()
    cvss.base = Base(lines[3])
    cvss.tmp = Temporal(lines[4])
    cvss.env = Environmental(lines[5])
    
    score = cvss.get_score()
    print os.path.basename(fp.name)
    print cvss.base
    print cvss.tmp
    print cvss.env
    #print "".join(lines[3:6]),
    print score
    if score < 4.0:
        print 'Low'
    elif score >= 7:
        print 'High'
    else:
        print 'Medium'

if __name__ == '__main__':
    import sys
    fp = open(sys.argv[1])

    main(fp)

# vim: set ts=4 sw=4 tw=79 :

