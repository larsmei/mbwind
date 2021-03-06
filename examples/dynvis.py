# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 17:24:13 2012

@author: Rick Lupton
"""

from __future__ import division
import numpy as np
import matplotlib.pylab as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D # analysis:ignore (enables 3d projection)

def show(system, t, strains, tvals, fade=False, figsize=None):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111,projection='3d', xlabel='x', ylabel='y', zlabel='z')
    ax.plot([1,0,0,0,0],[0,0,1,0,0],[0,0,0,0,1], 'k-')
    ax.set_aspect(1,'datalim')
    ax._axis3don = False
    ax.hold(True)

    iDOF = system.q.indices_by_type('strain')
    N = len(iDOF)
    assert (strains.shape[0] == len(t)) and (strains.shape[1] == N)

    Ntvals = len(tvals)
    if fade:
        alphas = [((1+i)/Ntvals)**4 for i in range(Ntvals)]
    else:
        alphas = [1] * Ntvals

    for i in range(Ntvals):
        it = np.nonzero(t >= t[i])[0]
        if not len(it) > 0: break
        system.q[iDOF] = strains[it[0]]
        system.update_kinematics(t[it[0]], False)
        system.first_element.plot_chain(ax, alpha=alphas[i])
    return ax

def showsystem(system, view=None):
    fig = plt.figure()
    if view is None:
        ax = fig.add_subplot(111,projection='3d', xlabel='x', ylabel='y', zlabel='z')
        ax.plot([1,0,0,0,0],[0,0,1,0,0],[0,0,0,0,1], 'k-')
        ax.set_aspect(1,'datalim')
        ax.hold(True)
        system.first_element.plot_chain(ax)
    elif view in ('x','y','z'):
        x,y = {'x': (1,2), 'y': (0,2), 'z': (0,1)}[view]
        ax = fig.add_subplot(111, xlabel='XYZ'[x], ylabel='XYZ'[y])
        ax.hold(True)
        for el in system.iter_elements():
            for data,opts in zip(el.shape(), el.shape_plot_options):
                ax.plot(data[:,x], data[:,y], **opts)
    else:
        raise ValueError("view should be 'x', 'y', 'z', or None for 3d")

def anim(system, t, strains, vs=(0,1), lim1=None, lim2=None, scale=(1,1)):
    fig = plt.figure()
    fig.set_size_inches(10,10,forward=True)
    ax = fig.add_subplot(111, aspect=1, xlim=lim1,ylim=lim2)
    ax.grid()

    lines = []
    for el in system.iter_elements():
        ellines = [ax.plot([], [], **opt)[0] for opt in el.shape_plot_options]
        lines.append( (el,ellines) )
    time_template = 'time = %.1fs'
    time_text = ax.text(0.05, 0.9, '', transform=ax.transAxes)

    ax.set_xlabel('XYZ'[vs[0]])
    ax.set_ylabel('XYZ'[vs[1]])

    def init():
        for el,ellines in lines:
            for line in ellines:
                line.set_data([], [])
        time_text.set_text('')
        return [line for line in ellines for el,ellines in lines] + [time_text]

    iDOF = system.q.indices_by_type('strain')
    N = len(iDOF)
    assert (strains.shape[0] == len(t)) and (strains.shape[1] == N)
    
    def animate(i):
        # Update strain values
        system.q[iDOF] = strains[i]
        system.update_kinematics(t[i], False)

        for el,ellines in lines:
            linedata = el.shape()
            for data,line in zip(linedata,ellines):
                line.set_data(data[:,vs[0]]*scale[0], data[:,vs[1]]*scale[1])
        time_text.set_text(time_template%t[i])

        return [line for line in ellines for el,ellines in lines] + [time_text]

    print 'Starting animation....'
    ani = animation.FuncAnimation(fig, animate, np.arange(len(t)),
        interval=(t[1]-t[0])*1000, blit=False, init_func=init, repeat=False)
    return ani

def anim_modes(system, modeshapes, vs=(0,1), lim1=None, lim2=None):
    Ndof,Nmodes = modeshapes.shape
    iDOF = system.iFreeDOF
    assert Ndof == np.count_nonzero(iDOF)
    t = np.linspace(0, 2*np.pi, 50)

    fig = plt.figure()
    fig.set_size_inches(10,10,forward=True)

    axes_lines = []
    for imode in range(Nmodes):
        ax = fig.add_subplot(Nmodes//2,2,imode, aspect=1, xlim=lim1,ylim=lim2)
        ax.grid()

        axes_lines.append([])
        for el in system.iter_elements():
            ellines = [ax.plot([], [], **opt)[0] for opt in el.shape_plot_options]
            axes_lines[-1].append( (el,ellines) )
        ax.set_xlabel('XYZ'[vs[0]])
        ax.set_ylabel('XYZ'[vs[1]])

    all_lines = []
    for lines in axes_lines:
        for el,ellines in lines:
            for line in ellines:
                all_lines.append(line)

    def init():
        for line in all_lines:
            line.set_data([], [])
        return all_lines

    def animate(i):
        for imode, lines in enumerate(axes_lines):
            system.q[iDOF] = modeshapes[:, imode] * np.sin(t[i])
            system.update(0.0, False)

            for el, ellines in lines:
                linedata = el.shape()
                for data, line in zip(linedata, ellines):
                    line.set_data(data[:, vs[0]], data[:, vs[1]])

        return all_lines

    ani = animation.FuncAnimation(fig, animate, np.arange(len(t)),
        interval=1000, blit=False, init_func=init, repeat=False)
    return ani

def anim_mode(system, modeshape, xlim=None, ylim=None, zlim=None):
    Ndof = len(modeshape)
    iDOF = system.iFreeDOF
    assert Ndof == np.count_nonzero(iDOF)
    t = np.linspace(0, 2*np.pi, 50)

    fig = plt.figure()
    fig.set_size_inches(10,10,forward=True)

    axes_lines = [[], []]
    for iview,lim in enumerate((ylim,zlim)):
        ax = fig.add_subplot(2,1,(1+iview), aspect=1, xlim=xlim,ylim=lim)
        ax.grid()
        for el in system.iter_elements():
            ellines = [ax.plot([], [], **opt)[0] for opt in el.shape_plot_options]
            axes_lines[iview].append( (el,ellines) )
        ax.set_xlabel('X')
        ax.set_ylabel('YZ'[iview])

    all_lines = []
    for lines in axes_lines:
        for el,ellines in lines:
            for line in ellines:
                all_lines.append(line)

    def init():
        for line in all_lines:
            line.set_data([], [])
        return all_lines

    def animate(i):
        system.q[iDOF] = modeshape * np.sin(t[i])
        system.update(0.0, False)

        for iview, lines in enumerate(axes_lines):
            for el, ellines in lines:
                linedata = el.shape()
                for data, line in zip(linedata, ellines):
                    line.set_data(data[:,0], data[:,1+iview])

        return all_lines

    ani = animation.FuncAnimation(fig, animate, np.arange(len(t)),
        interval=10, blit=False, init_func=init, repeat=True)
    return ani

def show_modeshape(ma, imode):
    fig = plt.figure()
#    axy = fig.add_subplot(3,1,1, xlabel='x', ylabel='y')
#    axy.set_aspect(1,'datalim')
#    axy.hold(True)
#    axz = fig.add_subplot(3,1,2, xlabel='x', ylabel='z', sharex=axy)
#    axz.set_aspect(1,'datalim')
#    axz.hold(True)
#    axt = fig.add_subplot(3,1,3, xlabel='x', ylabel='torsion', sharex=axy)
#    axt.hold(True)

    shape = ma.shapes[imode]

    ax = fig.add_subplot(111, xlabel='x')
    ax.plot(ma.x0 + shape[:,0], shape[:,1], 'b-o',
            ma.x0 + shape[:,0], shape[:,2], 'r-o',
            ma.x0 + shape[:,0], shape[:,3], 'g-x')
    ax.legend(['Y','Z','Torsion'], loc='upper left')
    ax.set_title('Mode %d (%.2f Hz)' % (1+imode, ma.freqs[imode]/2/np.pi))

#    axy.plot(shape[:,0], shape[:,1], 'b-o')
#    axt.plot(shape[:,0], shape[:,3], 'g-x')
#    axz.plot(shape[:,0], shape[:,2], 'b-o')
