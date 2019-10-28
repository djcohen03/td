import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from db.models import *

def plotsurface(fetch):
    '''
    '''
    # set up a figure twice as wide as it is tall
    fig = plt.figure(figsize=plt.figaspect(0.5))
    ax = fig.add_subplot(1, 1, 1, projection='3d')

    # plot a 3D surface like in the example mplot3d/surface3d_demo
    X = np.arange(-5, 5, 0.25)
    Y = np.arange(-5, 5, 0.25)
    X, Y = np.meshgrid(X, Y)
    Z = X * Y
    ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)

    plt.show()




if __name__ == '__main__':
    surface = None
    plotsurface(surface)
