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
        self.rubriker = headers
        self.värden = values
    def __str__(self):
        s = ''
        for i in range(len(self.rubriker)):
            s += f'{self.rubriker[i]}: \n {self.värden[i]}\t\n\n'
        return "{\n\n" + s + "}"

    def __add__(self, term):
        return getter(self.rubriker, self.värden + term)
    def __sub__(self, term):
        return getter(self.rubriker, self.värden - term)
    def __mul__(self, factor):
        return getter(self.rubriker, self.värden * factor)
    def __truediv__(self, term):
        return getter(self.rubriker, self.värden / term)
    
    def __getitem__(self, key):
        if isinstance(key, str):
            key = self.rubriker.index(key)
        return self.värden[key]
    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = self.rubriker.index(key)
        self.värden[key] = value


class läs:
    '''
    Läser och lagrar data från en csv-fil. Första raden i csv-filen måste vara rubrikerna. För använding med grafritare.

    Rådatan extrraheras med .x och .y. y-värdena kan indexeras med .y[header] om det finns flera kolumner.

    (Endast läsning)
    Rubrikerna lagras i .rubriker
    Filvägen lagras i .path

    Konfigurationsargument:
        path (str): Sökvägen till csv-filen. Default är 'data.csv'.
        x (str): Rubriken för x-värdena.

    Exempel:
        data = läs('data.csv')
    '''
    def __init__(self, path:str = 'data.csv', x:str= None): #helt lost?
        self.x = []
        self.y = []
        self.path = path
        with open(path, 'r') as file:
            reader = csv.DictReader(file)
            self.rubriker = reader.fieldnames.copy()
            if x is None:
                x = self.rubriker.pop(0)
            else:
                self.rubriker.remove(x)
            self.xlabel = x
            for row in reader:
                data = []
                self.x.append(float(row[x]))
                for header in self.rubriker:
                    data.append(float(row[header]))
                self.y.append(data)
        self.x = array(self.x)
        self.y = getter(self.rubriker, array(self.y).T)

    def nollställ(self, index=None):
        '''
        Nollsäller y-värdena så att det första y-värdet blir 0.

        Konfigurationsargument:
            index (str or int): Vilken y-kolumn som ska nollsättas. Default är None, vilket nollsätter alla kolumner.
        '''
        if index is not None:
            self.y[index] -= self.y[index][0]

    def medelvärde(self, ft:Sequence=None, index=None):
        '''
        Beräknar medelvärdet av y-värdena i ett visst intervall av x-värden.

        Konfigurationsargument:
            ft (arraylike): Intervall för x-värden.
            index (str or int): Vilken y-kolumn som ska användas. Default är None, vilket använder alla kolumner.
        
        Returnerar:
            float: Medelvärdet av y-värdena i det angivna intervallet.

        Exempel:
            data.medelvärde(ft=(0, 20), index='Temperature_K')
        '''
        mask = slice(None) if ft is None else (ft[0] <= self.x) & (self.x <= ft[1])
        if index is None:
            return self.y.värden.T[mask].T.mean()
        return self.y[index][mask].mean()
    
    def typevärde(self, ft:Sequence=None, index=None):
        '''
        Beräknar typevärdet av y-värdena i ett visst intervall av x-värden.

        Konfigurationsargument:
            ft (arraylike): Intervall för x-värden.
            index (str or int): Vilken y-kolumn som ska användas. Default är None, vilket använder alla kolumner.

        Returnerar:
            getter: En lista av intervall där flest linjer skär samma y-värde flest gånger.

        Exempel:
            data.typevärde(ft=(0, 20), index='Temperature_K')
        '''
        mask = slice(None) if ft is None else (ft[0] <= self.x) & (self.x <= ft[1])
        y = self.y.värden.T[mask].T if index is None else [self.y[index][mask]]
        
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
        return getter(self.rubriker, re)


class grafritare:
    def __init__(self, data:läs, ft:Sequence=None):
        '''
        Skapar en grafritare med data från en läs (data) objekt. Förbereder datan för att ritas.

        x och y-axelns titlar kan ändras genom att modifiera .xtitel och .ytitel.
        
        Argument:
            data (läs): Datan som ska ritas.
            ft (arraylike): Intervall för x-värden.
        
        Konfigurationsargument:
            ft (arraylike): Intervall för x-värden.

        Exempel:
            graf = grafritare(data, ft=(0, 20))
        '''
        self.data = copy(data)
        self.xtitel = copy(self.data.xlabel)
        self.ytitel = None
        self.dict = {}
        self.plots = []
        mask = slice(None) if ft is None else (ft[0] <= self.data.x) & (self.data.x <= ft[1])
        self.data.x = self.data.x[mask]
        self.data.y = getter(self.data.rubriker, self.data.y.värden.T[mask].T)
    
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

    def rita(self, index=None):
        '''
        Ritar data och förbereder det för .visa()

        Konfigurationsargument:
            index (str or int): Vilken y-kolumn som ska ritas. Default är None, vilket ritar alla kolumner.
        
        Exempel:
            graf.rita(index='Temperature_K')
        '''
        if index is not None:
            if not isinstance(index, str):
                index = self.data.rubriker[index]
            self.__update(index, self.data.y[index], 0)

        else:
            for i in self.data.rubriker:
                self.__update(i, self.data.y[i], 0)

    def trend(self, index=None, namn=False):
        '''
        Beräknar och förbereder en trendlinje för .visa()
        
        Konfigurationsargument:
            index (str or int): Vilken y-kolumn som ska användas för trendlinjen. Default är None, vilket använder alla kolumner.
            namn (bool): Om True, lägger till en etikett med lutning, intercept och R^2-värde i legendan. Default är False.
        '''
        if index is not None:
            if not isinstance(index, str):
                index = self.data.rubriker[index]
            
            k = self.__linreg(index)
            self.__update(index, k[0]*self.data.x + k[1], 1)
            if namn:
                self.__update(index, f'Trendlinje för {index}:\nk = {k[0]:.4f}\nm = {k[1]:.4f}\nR^2 = {k[2]:.4f}', 2)

        else:
            for i in self.data.rubriker:
                k = self.__linreg(i)
                self.__update(i, k[0]*self.data.x + k[1], 1)
                if namn:
                    self.__update(i, f'Trendlinje för {i}:\nk = {k[0]:.4f}\nm = {k[1]:.4f}\nR^2 = {k[2]:.4f}', 2)

    def visa(self, *, markörer=True, linjer=True, invertera:bool=True, rutnät:bool=True):
        '''
        Visar grafen.

        Konfigurationsargument (nyckelord):
            markörer (bool): Om True, ritar markörer på datapunkterna. Default är True.
            linjer (bool): Om True, ritar linjer mellan datapunkterna. Default är True.
            invertera (bool): Om True, inverterar x- och y-axlarna. Default är True.
            rutnät (bool): Om True, ritar ett rutnät. Default är True.
        '''
        fig, ax = plt.subplots(label=self.data.path)
        lstyle = '-' if linjer else ''
        markrs = 'x' if markörer else ''
        ldict = 0

        for k,v in self.dict.items():
            if not(v[0] is None and v[1] is not None):
                ldict += 1
                yname = k
                color = ax._get_lines.get_next_color()
                if invertera:
                    if v[0] is not None:
                        ax.plot(v[0], self.data.x, label=k, color=color, marker=markrs, linestyle=lstyle)
                    if v[1] is not None:
                        ax.plot(v[1], self.data.x, label=v[2], color=color, linestyle=':', alpha=0.7)
                else:
                    if v[0] is not None:
                        ax.plot(self.data.x, v[0], label=k, color=color, marker=markrs, linestyle=lstyle)
                    if v[1] is not None:
                        ax.plot(self.data.x, v[1], label=v[2], color=color, linestyle=':', alpha=0.7)

        if rutnät:
            ax.grid(alpha=0.3)

        if invertera:
            ax.set_ylabel(self.xtitel)
            if self.xtitel is None:
                if ldict == 1:
                    ax.set_xlabel(yname)
                else:
                    fig.legend()
            else:
                ax.set_xlabel(self.ytitel)
        else:
            ax.set_xlabel(self.xtitel)
            if self.ytitel is None:
                if ldict == 1:
                    ax.set_ylabel(yname)
                else:
                    fig.legend()
            else:
                ax.set_ylabel(self.ytitel)
        
        fig.tight_layout()
        plt.show()
    
    def visalådagram(self, *, rutnät:bool=True):
        '''
        Visar ett lådagram för datan.

        Konfigurationsargument:
            rutnät (bool): Om True, ritar ett rutnät. Default är True.
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
        if rutnät:
            ax.yaxis.grid(alpha=0.3)
        fig.tight_layout()
        ax.set_ylabel(self.ytitel)
        plt.show()

    def visafördelning(self, normal:bool=True, title:bool=False, *, rutnät:bool=True, res=100):
        '''
        Visar hur många gånger datan korsar olika y-värden, vilket kan ge en indikation på datans fördelning.

        Konfigurationsargument:
            normal (bool): Om True, ritar en normalfördelningskurva baserat. Default är True.
            title (bool): Om True, sätter titlar på varje subplot. Default är False.
            rutnät (bool): Om True, ritar ett rutnät. Default är True.
            res (int): Antal y-värden att räkna korsningar för. Default är 100.
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
                ax[j].plot(yrange, factor/(sigma * sqrt(2*pi)) * e**(- (yrange - mu)**2 / (2*sigma**2)), color=color, label=f'Normal Distribution:\n$\\sigma = {sigma:.4f}$\n$\\mu = {mu:.4f}$')
                ax[j].legend()
            color = ax[j]._get_lines.get_next_color()
            ax[j].hist(count, bins=res, color = color)
            if title:
                ax[j].set_title(label[j])
            if self.ytitel is None:
                ax[j].set_xlabel(label[j])
            else:
                ax[j].set_xlabel(self.ytitel)
            ax[j].set_ylabel('Occurrences')

        if rutnät:
            for k in ax:
                k.grid(alpha=0.3)
        fig.tight_layout()
        plt.show()
