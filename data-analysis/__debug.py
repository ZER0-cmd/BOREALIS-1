import module_eng as en
import module_swe as sw

data = en.read('standard_atmosphere_si_noisy_strong.csv')
temp = data.y['Temperature_K']
alt = data.x
temp -= 273.15
alt /= 1000

graph = en.plotter(data,ft=(0, 20))
graph.plot('Temperature_K')
graph.trend(name=True)
graph.show(invert=False)