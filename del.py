from utility.CaseInsensitiveDict import CaseInsensitiveDict

a = CaseInsensitiveDict({'Allen':1, 'brad':2, 'taMMy':3})

names = ['allen', 'tammy', 'brad']

for name in names:
    if name in a:
        print a[name]