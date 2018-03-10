#!/usr/bin/env python
# Copyright (c) 2015 Alan Hawrylyshen.
# See LICENSE for details.

# No apologies - this is a quick and horrid hack

import matplotlib
matplotlib.use('cairo')
#matplotlib.use('MacOSX')
from math import fmod, fabs
from itertools import product
from matplotlib.patches import Polygon as mpl_polygpn
import matplotlib.font_manager as fm
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np

verbose = False
debug = False
minyscale = None
mpl_use = None
pad_missing = False
logscale=True
error_bars = False

v_reg_max=28
ymax = int(((v_reg_max)/10)+1)*10
ymin = 2.0
on_hand_values = None

if __name__ == '__main__':
    try:
        mpl_use = True
        font = fm.FontProperties(
            family = 'SegoeUI',
            fname = '/Users/alan/Library/Fonts/segoeuil.ttf',
            size = 4.0 )
        if verbose:  print ('Wow - found matplotlib')
    except ImportError:
        if verbose: print ('No Matplotlib -- assuming running in nodebox')

def label_format(ax):
        ax.set_yticklabels(ax.get_yticks(), fontproperties = font)
        ax.set_xticklabels(ax.get_xticks(), fontproperties = font)

def to_err_range(x,err):
    return [ (1.-err)*x, (1.+err)*x ]

def tolerance_box(r1,r2,ax,tolerance=0.05,c='blue',alpha=0.5):
    x = []
    y = []
    for ra in to_err_range(r1,err=tolerance):
        for rb in to_err_range(r2,err=tolerance):
            x.append(rb)
            vout = v_out(ra,rb)
            y.append(vout)
    idx = [ 0, 1, 3, 2 ]
    xo = []
    yo = []
    for i in range(len(idx)):
        xo.append(x[idx[i]])
        yo.append(y[idx[i]])

    ax.fill(xo,yo,color=c,alpha=alpha,linewidth=0.2)

def v_out(r1,r2, i_adj=0.0):
    return 1.25*(1.+float(r2)/float(r1))+(i_adj*r2)

def lm317_filter(x,y):
    v_min = 2.5
    v_max = 25
    return  zip(*[ [a,b] for a,b in zip(x,y) if b > v_min and b<v_max ])


class ResistorCollection(object):
    def __init__(self, on_hand):
        self.__on_hand = on_hand
        self.__n_res = dict() # difficulties only - they encode nres
        self.__rvals = []
        for r in self.__on_hand:
            self._add_r_as_n(r)

# need to extend by iterating over myself! - interesting -- todo
    def _add_r_as_n(self,r,n=1,r1=None,r2=0,style='n'):
        # native, series, parallel
        r = int(r)
        if r1 is None:
            r1 = r

        difficulty_map = { 'n' : 0, 's': 1 , 'p' : 2  }
        difficulty = n*4 + difficulty_map[style]

        if r in self.__n_res and self.__n_res[r]['diff'] < difficulty:
            return # we have a better implementation of r

        self.__n_res[r] = { 'r':r,'n':n,'r1':r1,'r2':r2,'diff':difficulty,'style':style }
        if not r in self.__rvals:
            self.__rvals.append(r)
            self.__rvals.sort()

    def __iter__(self):
        return self.__rvals.__iter__()

    def on_hand(self):
        return self.__on_hand

    def implementation(self,r):
        return self.__n_res[r]

    def __str__(self):
        s =  "All Vals:" +str(self.__rvals) + '\n'
        s += "On Hand: "+ str(self.__on_hand) + '\n'
        return s

    def add_all_n_combos(self,n):
        if n == 2 :
            for r1,r2 in product(self.__on_hand,self.__on_hand):
                rp = (r1*r2*1.0)/(r1+r2)
                rs = r1+r2
                # self._add_r_as_n(rp,2,r1=r1,r2=r2,style='p')
                self._add_r_as_n(rs,2,r1=r1,r2=r2,style='s')
        else:
            raise InputError

    def __iterate__(self):
        for r in self.__rvals:
            yield r

    def all_vals(self):
        return self.__rvals

    def all_vals_with_implementation(self):
        for k in self.__n_res:
            v = self.__n_res[k]
            d = v % 4
            v /= 4
            difficulty_map = { 0:'n', 1:'s', 2:'p' }
            yeild ( v, difficulty_map[d] )

def main():
    import sys
    global verbose


    v_target = 9
    tolerance = 0.05
    v_errthreshold = 0.5

    if len(sys.argv) > 1:
        v_target = float(sys.argv[1])
    if len(sys.argv) > 2:
        v_errthreshold = float(sys.argv[2])
    if len(sys.argv) > 3:
        tolerance = float(sys.argv[3])

    fig = plt.figure()
    fig.subplots_adjust(left=None, bottom=None, right=None,
                        top=None, wspace=None, hspace=0.6)

    if True:
        # Setup your resitor values here -- if you only have a few.
        on_hand_values = [ 50, 100, 220, 235, 440, 470, 500, 1000,
                           1470, 1500, 1770, 2200 ]
        # Things I can trivially make from those...
        # Pairs Series
        #on_hand_values.extend( [200, 320,440, 690,  940, 2000, 4400] )
        # parallel
        #on_hand_values.extend( [110, 235, 500, 1100, 1220, 1470] )

    recommended_r1_values = [ 220, 240, 270 ]

    rc = ResistorCollection([ 50, 100, 220, 470, 1000, 1500, 2200])
    rc.add_all_n_combos(2)
    print (rc)

    ax = fig.add_subplot(1,1,1)
    ax.grid(color='grey',linestyle='-',linewidth=0.5)

    if not logscale is None and logscale:
        ax.set_yscale('log')
        ax.set_xscale('log')

    plt.title('LM317 R1 Curves')
    plt.ylabel('Vout')
    plt.xlabel('R2 (ohms)')

    ax.set_ylim(ymin,ymax)
    ax.plot( [ min(rc),max(rc)], [ v_target, v_target ],
             color='r', linestyle='-', marker=None)
    # A curve for each value of r1 with appropriate range
    v_reg_all = []

    ax.yaxis.set_ticks( [2,2.5,3,4,5,6,7,8,9,10,11,12,13,14,15,17,20,25] )

    ax.xaxis.grid(color='#eeeeff',
                  linestyle='-',
                  linewidth=0.5)

    plt.xticks( rc.all_vals(), rotation=90 )

    # Compute
    # [ r for r in rc.all_vals()
    # if r >= min(recommended_r1_values) and r <= max(recommended_r1_values) ]:
    for r1 in rc.all_vals():
        v_reg = [ v_out(r1=r1,r2=r2) for r2 in rc.all_vals() ]
        print ("### COMPUTED Vouts for %d:%d\n"%(r1,0,))
        try:
            px,py = lm317_filter(x=rc.all_vals(),y=v_reg)
        except:
            continue

        for r2,v in zip(px,py):
            v_reg_all.append([ v, r1, r2 ])
            if r1 >= min(recommended_r1_values) and r1 <= max(recommended_r1_values) :
                c = 'b'
            else:
                c = 'r'
            if False and args.tolerance_boxes:
                tolerance_box(ax=ax,r1=r1,r2=r2,tolerance=tolerance,c=c)
        if True or error_bars:
            v_errs_min = [ v_out(r1=r1,r2=r)-v_out(r1=r1,r2=(1.-tolerance)*r)
                           for r in px ]
            v_errs_max = [ v_out(r1=r1,r2=(1.+tolerance)*r)-v_out(r1,r)
                           for r in px ]
            ax.errorbar(px,py, #xerr=[ tolerance * r for r in px ],
                        yerr = [v_errs_min,v_errs_max],
                        linestyle='-',linewidth=0.5,color='0.5',markersize=2.0,
                        capsize=0.5)
        else:
            ax.plot(px,py,
                    linestyle='-',linewidth=0.5,color='0.0',
                    markersize=2.0)

        ax.text(px[-1]*1.05,py[-1],str(r1),fontsize=6)

    label_format(ax)
    v_reg_all.sort()

    print ('len(v_reg_all)=',len(v_reg_all))

    errs = map(lambda x: { 'err':fabs(x[0] - v_target),
                           'Vout':x[0], 'r1': x[1],'r2': x[2]},
               v_reg_all)

    #errs.sort()
    hdr = '%-5s %-5s %-8s %-12s  %20s'
    print (hdr%('R1','R2','V','Verr','Implementation'))
    fmt = '%-5d %-5d %-8.3f (%-8.6f) [%20s]'
    clist = [ c for c in errs if c['err'] < v_errthreshold ]

    for candidate in clist:
        r2 = candidate['r2']
        print (fmt%(candidate['r1'],r2,
                   candidate['Vout'],candidate['err'],rc.implementation(r2)))
        if True or args.tolerance_boxes:
            tolerance_box(ax=ax,r1=candidate['r1'],r2=r2,
                          tolerance=tolerance, alpha=0.5,c='green')

    fig.savefig('lm317.pdf')


if  __name__ == '__main__':
    main()
