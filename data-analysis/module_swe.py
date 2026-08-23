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
    def __init__(self, path: str = 'data.csv', x: str = None):
        self.x = []
        self.y = []
        self.path = path
        with open(path, 'r') as file:
            reader = csv.DictReader(file)
            self.rubriker = reader.fieldnames.copy()
            if x is None:
                for name in self.rubriker:
                    if 'elevation' in name.lower() or 'altitude' in name.lower():
                        x = name
                        break
            if x is None:
                raise NameError("No compoatible elevation data found. Manually input as argument instead")
            self.rubriker.remove(x)
            try:
                self.rubriker.remove("datetime")
                self.rubriker.remove("elapsed_s")
            except Exception:
                pass

            self.xlabel = x
            for row in reader:
                data = []
                self.x.append(float(row[x]))
                for header in self.rubriker:
                    data.append(float(row[header]))
                self.y.append(data)
        self.x = array(self.x)
        self.y = getter(self.rubriker, array(self.y).T)

    def norm(self, rubrik=""):
        self.rubriker = [rubrik]
        self.y = getter([rubrik], linalg.norm(self.y.värden, axis=0)[newaxis, :])

    def _resolve_indices(self, index: tuple) -> list:
        '''
        Intern hjälpmetod. Konverterar *index-argument till en lista av strängnycklar.
        Tomt index → alla kolumner. Strängar används direkt, heltal slås upp i rubriker.
        '''
        if not index:
            return list(self.rubriker)
        resolved = []
        for idx in index:
            if isinstance(idx, str):
                if idx not in self.rubriker:
                    raise KeyError(f"Kolumnen '{idx}' finns inte. Tillgängliga: {self.rubriker}")
                resolved.append(idx)
            elif isinstance(idx, int):
                resolved.append(self.rubriker[idx])
            else:
                raise TypeError(f"Index måste vara str eller int, fick {type(idx).__name__}")
        return resolved

    def nollställ(self, *index):
        '''
        Nollsätter y-värdena så att det första y-värdet blir 0.

        Argument:
            *index (str or int): Kolumner att nollsätta. Ange ingen för att nollsätta alla.

        Exempel:
            data.nollställ()                          # alla kolumner
            data.nollställ('Temperature_K')           # en kolumn via namn
            data.nollställ(0)                         # en kolumn via index
            data.nollställ('Temperature_K', 'Volt')   # flera kolumner
        '''
        for idx in self._resolve_indices(index):
            self.y[idx] -= self.y[idx][0]

    def medelvärde(self, *index, ft: Sequence = None):
        '''
        Beräknar medelvärdet av y-värdena i ett visst intervall av x-värden.

        Argument:
            *index (str or int): Kolumner att beräkna medelvärdet för. Ange ingen för totalt medelvärde.

        Nyckelordsargument:
            ft (arraylike): Intervall för x-värden.

        Returnerar:
            float om ingen eller en kolumn anges, getter med floats om flera kolumner anges.

        Exempel:
            data.medelvärde()                                     # totalt medelvärde
            data.medelvärde('Temperature_K', ft=(0, 20))          # en kolumn
            data.medelvärde('Temperature_K', 'Volt', ft=(0, 20))  # flera kolumner
            data.medelvärde(0, 1, ft=(0, 20))                     # via heltalsindex
        '''
        mask = slice(None) if ft is None else (ft[0] <= self.x) & (self.x <= ft[1])
        targets = self._resolve_indices(index)

        if not index:
            return self.y.värden.T[mask].T.mean()
        if len(targets) == 1:
            return self.y[targets[0]][mask].mean()
        return getter(targets, array([self.y[i][mask].mean() for i in targets]))

    def typevärde(self, *index, ft: Sequence = None):
        '''
        Beräknar typevärdet av y-värdena i ett visst intervall av x-värden.

        Argument:
            *index (str or int): Kolumner att beräkna typevärdet för. Ange ingen för alla kolumner.

        Nyckelordsargument:
            ft (arraylike): Intervall för x-värden.

        Returnerar:
            En lista av intervall där flest linjer skär samma y-värde flest gånger.
            En kolumn returnerar arrayen direkt, flera kolumner returnerar en getter.

        Exempel:
            data.typevärde()                                     # alla kolumner
            data.typevärde('Temperature_K', ft=(0, 20))          # en kolumn
            data.typevärde('Temperature_K', 'Volt', ft=(0, 20))  # flera kolumner
            data.typevärde(0, ft=(0, 20))                        # via heltalsindex
        '''
        mask = slice(None) if ft is None else (ft[0] <= self.x) & (self.x <= ft[1])
        targets = self._resolve_indices(index)
        y_data = [self.y[i][mask] for i in targets]

        re = []
        for a in y_data:
            interval = []
            n = 0
            lei = 0
            p = set(a[concatenate((find_peaks(a)[0], find_peaks(-a)[0]))])
            for ex in p:
                s = a - ex
                counts = 0
                for q in range(len(s) - 1):
                    if s[q] * s[q + 1] <= 0:
                        counts += 1

                if counts == n:
                    lei += 1
                    interval.append(ex)
                if counts > n:
                    n = counts
                    interval = [ex]
                    lei = 1

            interval.sort(reverse=True)
            rei = full((int(ceil(lei / 2)), 2), nan)
            for i in range(lei):
                if i % 2 == 0:
                    rei[int(i / 2), 0] = interval[i]
                else:
                    rei[int((i - 1) / 2), 1] = interval[i]
            re.append(rei)

        if len(targets) == 1:
            return re[0]
        return getter(targets, re)


class grafritare:
    '''
    Skapar en grafritare med data från en läs (data) objekt. Förbereder datan för att ritas.

    x och y-axelns titlar kan ändras genom att modifiera .xtitel och .ytitel.

    Argument:
        data (läs): Datan som ska ritas.

    Nyckelordsargument:
        ft (arraylike): Intervall för x-värden.

    Exempel:
        graf = grafritare(data, ft=(0, 20))
    '''
    def __init__(self, data: läs, ft: Sequence = None):
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
            self.dict[index] = [None, None, None]
        self.dict[index][n] = target

    def __linreg(self, index):
        y = self.data.y[index]
        k = polyfit(self.data.x, y, 1)
        ymean = mean(y)
        yhat = polyval(k, self.data.x)
        sstot = sum((y - ymean) ** 2)
        ssres = sum((y - yhat) ** 2)
        r2 = 1 - ssres / sstot if sstot != 0 else 1.
        return [k[0], k[1], r2]

    def rita(self, *index):
        '''
        Ritar data och förbereder det för .visa()

        Argument:
            *index (str or int): Kolumner att rita. Ange ingen för att rita alla kolumner.

        Exempel:
            graf.rita()                        # alla kolumner
            graf.rita('Temperature_K')         # en kolumn via namn
            graf.rita(0)                       # en kolumn via index
            graf.rita('Temperature_K', 'Volt') # flera kolumner
        '''
        for i in self.data._resolve_indices(index):
            self.__update(i, self.data.y[i], 0)

    def trend(self, *index, namn: bool = False):
        '''
        Beräknar och förbereder en trendlinje för .visa()

        Argument:
            *index (str or int): Kolumner att beräkna trendlinjer för. Ange ingen för alla kolumner.

        Nyckelordsargument:
            namn (bool): Om True, lägger till en etikett med lutning, intercept och R^2-värde i legendan. Default är False.

        Exempel:
            graf.trend()                              # alla kolumner
            graf.trend('Temperature_K', namn=True)    # en kolumn med etikett
            graf.trend(0, 1)                          # flera kolumner via index
        '''
        for i in self.data._resolve_indices(index):
            k = self.__linreg(i)
            self.__update(i, k[0] * self.data.x + k[1], 1)
            if namn:
                self.__update(i, f'Trendlinje för {i}:\nk = {k[0]:.4f}\nm = {k[1]:.4f}\nR^2 = {k[2]:.4f}', 2)

    def visa(self, *, markörer: bool = True, linjer: bool = True, invertera: bool = True, rutnät: bool = True):
        '''
        Visar grafen.

        Nyckelordsargument:
            markörer (bool): Om True, ritar markörer på datapunkterna. Default är True.
            linjer (bool): Om True, ritar linjer mellan datapunkterna. Default är True.
            invertera (bool): Om True, inverterar x- och y-axlarna. Default är True.
            rutnät (bool): Om True, ritar ett rutnät. Default är True.
        '''
        fig, ax = plt.subplots(label=self.data.path)
        lstyle = '-' if linjer else ''
        markrs = 'x' if markörer else ''
        ldict = 0

        for k, v in self.dict.items():
            if not (v[0] is None and v[1] is not None):
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

    def visalådagram(self, *, rutnät: bool = True):
        '''
        Visar ett lådagram för datan.

        Nyckelordsargument:
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

    def visafördelning(self, normal: bool = True, title: bool = False, *, rutnät: bool = True, res=100):
        '''
        Visar hur många gånger datan korsar olika y-värden, vilket kan ge en indikation på datans fördelning.

        Konfigurationsargument:
            normal (bool): Om True, ritar en normalfördelningskurva baserat. Default är True.
            title (bool): Om True, sätter titlar på varje subplot. Default är False.

        Nyckelordsargument:
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
        h = int((lenq / w) + .999999999)

        fig, ax = plt.subplots(h, w, label=self.data.path)
        if lenq == 1:
            ax = [ax]
        ax = reshape(ax, -1)

        for j in range(lenq):
            yrange = linspace(q[j].min(), q[j].max(), res)
            count = []
            for y in yrange:
                bl = sign(q[j] - y)
                for i in range(len(bl) - 1):
                    if bl[i] != bl[i + 1]:
                        count.append(y)
            sigma = std(q[j])
            mu = mean(q[j])
            factor = (q[j].max() - q[j].min()) / res * len(count)
            color = ax[j]._get_lines.get_next_color()
            if normal:
                ax[j].plot(yrange, factor / (sigma * sqrt(2 * pi)) * e ** (-(yrange - mu) ** 2 / (2 * sigma ** 2)),
                           color=color, label=f'Normal Distribution:\n$\\sigma = {sigma:.4f}$\n$\\mu = {mu:.4f}$')
                ax[j].legend()
            color = ax[j]._get_lines.get_next_color()
            ax[j].hist(count, bins=res, color=color)
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