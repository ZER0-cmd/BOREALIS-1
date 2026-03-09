import matplotlib.pyplot as plt
from numpy import *
import csv
from copy import copy
from scipy.signal import find_peaks
from collections.abc import Sequence

class getter:
    '''
    RÖR INTE SOM DELTAGARE / DO NOT TOUCH AS A PARTICIPANT
    1darray dictionary edition for getting with both values and keys
    '''
    def __init__(self, headers, values):
        self.headers = headers
        self.values = values
    def __str__(self):
        s = ''
        for i in range(len(self.headers)):
            s += f'{self.headers[i]}: \n {self.values[i]}\t\n\n'
        return "{\n\n" + s + "}"

    def __add__(self, term):
        return getter(self.headers, self.values + term)
    def __sub__(self, term):
        return getter(self.headers, self.values - term)
    def __mul__(self, factor):
        return getter(self.headers, self.values * factor)
    def __truediv__(self, term):
        return getter(self.headers, self.values / term)
    
    def __getitem__(self, key):
        if isinstance(key, str):
            key = self.headers.index(key)
        return self.values[key]
    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = self.headers.index(key)
        self.values[key] = value


class read:
    def __init__(self, path:str = 'data.csv', x:str='Elevation_m'):
        '''
        Reads and stores data from a csv file. For usage with plotter

        The raw data is extrancted with .x and .y. The y-values can be indexed with .y[header] if there are multiple columns.
        
        (Read Only)
        The headers are stored in .headers
        The path is stored in .path

        Arguments:
            path (str): The path to the csv file.
        
        Optional arguments:
            x (str): The header for the x-values.
        
        Example:
            data = read('data.csv')
        '''
        self.x = []
        self.y = []
        self.path = path
        with open(path, 'r') as file:
            reader = csv.DictReader(file)
            self.headers = reader.fieldnames.copy()
            if x is None:
                x = self.headers.pop(0)
            else:
                self.headers.remove(x)
            self.xlabel = x
            for row in reader:
                data = []
                self.x.append(float(row[x]))
                for header in self.headers:
                    data.append(float(row[header]))
                self.y.append(data)
        self.x = array(self.x)
        self.y = getter(self.headers, array(self.y).T)

    def zero(self, index=None):
        '''
        Zeroes the y-values so that the first y-values is zero.

        Optional arguments:
            index (str or int): The header or index of the y-values to zero. If None, all y-values are zeroed.
        '''
        if index is not None:
            self.y[index] -= self.y[index][0]

    def mean(self, ft:Sequence=None, index=None):
        '''
        Returns the mean of the y-values in the given x-interval.
        
        Optional arguments:
            ft (arraylike): The x-interval to calculate the mean in
            index: The header or index of the y-values to calculate the mean for. If None, the mean of all y-values is calculated.
        
        Returns:
            float: The mean of the y-values in the given x-interval.
        
        Example:
            data.mean(ft=(0, 20), index='Temperature_K')
        '''
        mask = slice(None) if ft is None else (ft[0] <= self.x) & (self.x <= ft[1])
        if index is None:
            return self.y.values.T[mask].T.mean()
        return self.y[index][mask].mean()
    
    def typevalue(self, ft=None, index=None):
        '''
        Returns the typevalue of the y-values in the given x-interval.

        Optional arguments:
            ft (arraylike): The x-interval to calculate the typevalue in.
            index: The header or index of the y-values to calculate the typevalue for. If None, the typevalue of all y-values is calculated (potentially slow O(N³)).
        
        Returns:
            getter: A list of intervals of where the most lines intersect the same y-value the maximum ammount of times.

        Example:
            data.typevalue(ft=(0, 20), index='Temperature_K')
        '''
        mask = slice(None) if ft is None else (ft[0] <= self.x) & (self.x <= ft[1])
        y = self.y.values.T[mask].T if index is None else [self.y[index][mask]]
        
        re = []
        le = 0
        for a in y:
            le += 1
            interval = []
            n = 0
            lei = 0
            p = set(a[concatenate((find_peaks(a)[0], find_peaks(-a)[0]))])
            for ex in p:
                s = a-ex
                counts = 0
                for q in range(len(s)-1):
                    if s[q] * s[q+1] <= 0:
                        counts += 1
                
                if counts == n:
                    lei += 1
                    interval.append(ex)
                if counts > n:
                    n = counts
                    interval = [ex]
                    lei = 1
                
            interval.sort(reverse=True)
            rei = full((int(ceil(lei/2)),2), nan)
            for i in range(lei):
                if i % 2 == 0:
                    rei[int(i/2),0] = interval[i]
                else:
                    rei[int((i-1)/2),1] = interval[i]
            #rei is a 2darray which is a list of y-intervals where most lines intersect the same y-value
            re.append(rei)
        
        if le == 1:
            return re[0]
        return getter(self.headers, re)


class plotter:
    def __init__(self, data:read, ft:Sequence=None):
        '''
        Plots the data from a read (data) object.

        The x and y labels can be changed by modifying .xlabel and .ylabel.

        Arguments:
            data (read): The data to plot.
        
        Optional arguments:
            ft (arraylike): The x-interval to plot in.

        Example:
            graph = plotter(data, ft=(0, 20))
        '''
        self.data = copy(data)
        self.xlabel = copy(self.data.xlabel)
        self.ylabel = None
        self.dict = {}
        self.plots = []
        mask = slice(None) if ft is None else (ft[0] <= self.data.x) & (self.data.x <= ft[1])
        self.data.x = self.data.x[mask]
        self.data.y = getter(self.data.headers, self.data.y.values.T[mask].T)
    
    def __update(self, index, target, n):
        if index not in self.dict.keys():
            self.dict[index] = [None,None,None]
        self.dict[index][n] = target
    
    def __linreg(self, index):
        y = self.data.y[index]
        k = polyfit(self.data.x, y, 1)
        ymean = mean(y)
        yhat = polyval(k, self.data.x)
        sstot = sum((y-ymean)**2)
        ssres = sum((y - yhat)**2)
        r2 = 1 - ssres/sstot if sstot != 0 else 1.
        return [k[0], k[1], r2]

    def plot(self, index=None):
        '''
        Plots the data and prepares it for .show()

        Optional arguments:
            index (str or int): The header name or index of the data to plot.
        
        Example:
            graph.plot('Temperature_K')
    
        '''
        if index is not None:
            if not isinstance(index, str):
                index = self.data.headers[index]
            self.__update(index, self.data.y[index], 0)

        else:
            for i in self.data.headers:
                self.__update(i, self.data.y[i], 0)

    def trend(self, index=None, name=False):
        '''
        Plots the trendline for the data and prepares it for .show()

        Arguments:
            index (str or int): The header name or index of the data to plot the trendline for. If None, trendlines for all data are plotted.
            name (bool): Whether to include the slope, intercept and R^2 value in the legend. Default is False.
        '''
        if index is not None:
            if not isinstance(index, str):
                index = self.data.headers[index]
            
            k = self.__linreg(index)
            self.__update(index, k[0]*self.data.x + k[1], 1)
            if name:
                self.__update(index, f'Trendline for {index}:\nk = {k[0]:.4f}\nm = {k[1]:.4f}\nR^2 = {k[2]:.4f}', 2)

        else:
            for i in self.data.headers:
                k = self.__linreg(i)
                self.__update(i, k[0]*self.data.x + k[1], 1)
                if name:
                    self.__update(i, f'Trendline for {i}:\nk = {k[0]:.4f}\nm = {k[1]:.4f}\nR^2 = {k[2]:.4f}', 2)

    def show(self, *, markers=True, lines=True, invert:bool=True, grid:bool=True):
        '''
        Shows the plot.

        Optional keyword arguments:
            markers (bool): Whether to mark the datapoints in the plot. Default is True.
            lines (bool): Whether to connect the datapoints with lines. Default is True.
            invert (bool): Whether to invert the x and y axes (usually so altitude becomes y-axis). Default is True.
            grid (bool): Whether to show a grid in the plot. Default is True.
        '''
        fig, ax = plt.subplots(label=self.data.path)
        lstyle = '-' if lines else ''
        markrs = 'x' if markers else ''
        ldict = 0

        for k,v in self.dict.items():
            if not(v[0] is None and v[1] is not None):
                ldict += 1
                yname = k
                color = ax._get_lines.get_next_color()
                if invert:
                    if v[0] is not None:
                        ax.plot(v[0], self.data.x, label=k, color=color, marker=markrs, linestyle=lstyle)
                    if v[1] is not None:
                        ax.plot(v[1], self.data.x, label=v[2], color=color, linestyle=':', alpha=0.7)
                else:
                    if v[0] is not None:
                        ax.plot(self.data.x, v[0], label=k, color=color, marker=markrs, linestyle=lstyle)
                    if v[1] is not None:
                        ax.plot(self.data.x, v[1], label=v[2], color=color, linestyle=':', alpha=0.7)

        if grid:
            ax.grid(alpha=0.3)

        if invert:
            ax.set_ylabel(self.xlabel)
            if self.xlabel is None:
                if ldict == 1:
                    ax.set_xlabel(yname)
                else:
                    fig.legend()
            else:
                ax.set_xlabel(self.ylabel)
        else:
            ax.set_xlabel(self.xlabel)
            if self.ylabel is None:
                if ldict == 1:
                    ax.set_ylabel(yname)
                else:
                    fig.legend()
            else:
                ax.set_ylabel(self.ylabel)
        
        fig.tight_layout()
        plt.show()
    
    def showbox(self, *, grid:bool=True):
        '''
        Shows a box plot of the data.

        Optional arguments:
            grid (bool): Whether to show a grid in the plot. Default is True.
        '''
        fig, ax = plt.subplots(label=self.data.path)
        label = []
        q = []
        for k, v in self.dict.items():
            if v[0] is not None:
                label.append(k)
                q.append(v[0])
        ax.boxplot(q, showfliers=False)
        ax.set_xticklabels(label)
        if grid:
            ax.yaxis.grid(alpha=0.3)
        fig.tight_layout()
        ax.set_ylabel(self.ylabel)
        plt.show()

    def showdist(self, normal:bool=True, title:bool=False, *, grid:bool=True, res=100):
        '''
        Shows how many times the data intersect certain values.

        Optional arguments:
            normal (bool): Whether to show the normal distribution curve. Default is True.
            title (bool): Whether to show the header name as the title of each subplot. Default is False.
        Optional keyword arguments:
            grid (bool): Whether to show a grid in the plot. Default is True.
            res (int): The resolution of the histogram. Default is 100.
        '''
        q = []
        label = []
        for k, p in self.dict.items():
            if p[0] is not None:
                q.append(p[0])
                label.append(k)
        lenq = len(q)
        w = int(sqrt(lenq))
        h = int((lenq/w)+.999999999)

        fig, ax = plt.subplots(h, w, label=self.data.path)
        if lenq == 1:
            ax = [ax]
        ax = reshape(ax, -1)

        for j in range(lenq):
            yrange = linspace(q[j].min(), q[j].max(), res)
            count = []
            for y in yrange:
                bl = sign(q[j] - y)
                for i in range(len(bl)-1):
                    if bl[i] != bl[i+1]:
                        count.append(y)
            sigma = std(q[j])
            mu = mean(q[j])
            factor = (q[j].max()-q[j].min())/res * len(count)
            color = ax[j]._get_lines.get_next_color()
            if normal:
                ax[j].plot(yrange, factor/(sigma * sqrt(2*pi)) * e**(- (yrange - mu)**2 / (2*sigma**2)), color=color, label=f'Normal Distribution:\n$\sigma = {sigma:.4f}$\n$\mu = {mu:.4f}$')
                ax[j].legend()
            color = ax[j]._get_lines.get_next_color()
            ax[j].hist(count, bins=res, color = color)
            if title:
                ax[j].set_title(label[j])
            if self.ylabel is None:
                ax[j].set_xlabel(label[j])
            else:
                ax[j].set_xlabel(self.ylabel)
            ax[j].set_ylabel('Occurrences')

        if grid:
            for k in ax:
                k.grid(alpha=0.3)
        fig.tight_layout()
        plt.show()
