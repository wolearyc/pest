

import string
from pathlib import Path

# Important global objects for keeping track of the date, samples, and the 
# next available sample ID. 
date_global = ''
samples_global = []

# Expect the date as MMMM DD YYY
def date(date_string):
    global date_global
    [m, d, y] = date_string.lower().split()
    m = m[:3]
    y = '\'' + y[-2:]

    try:
        int(d)
        assert(m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 
                     'sep', 'oct', 'nov', 'dec'])
    except:
        raise Exception('Could not parse date')

    date_global = m + d + y

data_types = {'xrd':'.xrdml','sem':'-sem','tem':'-tem','test':'-test'}


class Sample:
    
    id = 0

    # Constructor
    # create_op     operation that created the sample
    # label         starting label for the sample
    # parent_id     id of the parent sample
    def __init__(self, create_op, label, parent_id=None):
        global date_global
        global samples_global

        create_op['date'] = date_global
        samples_global.append(self)

        prefix = ''
        if parent_id:
            prefix = f'{parent_id}.'

        ids = [s.id for s in samples_global]
        i = 1
        while(f'{prefix}{i}' in ids):
            i += 1
        
        self.history   = [create_op]     # List of past operations.
        self.label     = label           # Human-readable label for storage
        self.id        = f'{prefix}{i}'  # Numerical ID
        self.retired   = False           # If retired
        self.lost      = False           # If lost
        self.has_error = False           # If labeled inaccurately, botched, etc.

    # Applies an operation to the sample.
    # op     the operation to apply
    # label  label to append corresponding to the new material
    def apply_op(self, op, op_label):
        global date_global
        op['date'] = date_global
        self.history.append(op)
        self.label += op_label

    def __str__(self):
        s = ''
        for h in self.history:
            s += str(h)
        return s

    def split(self, n=1):
        birth_op = {'op' : 'birthed', 'parent' : self}
        children = [Sample(birth_op, self.label, self.id) for _ in range(n)]
        
        split_op = {'op' : 'split', 'children' : children}
        label = ''
        self.apply_op(split_op, label)

        return children

    def report_retired(self):
        self.retired = True

    def report_lost(self):
        self.lost = True

    def report_error(self):
        self.has_error = True

    def is_active(self):
        return(not self.retired and not self.lost and not self.has_error)

    # Calcination - time in hr, temp in C
    def calcine(self, time, temp):
        op = {'op'   : 'calcine', 
               'time' : time, 
               'temp' : temp
               }
        label = f' ca.{time}h.{temp}C'
        self.apply_op(op, label)

    # Press pellet - time in min, press in bar
    def press_pellet(self, time, pressure):
        op = {'op' : 'press_pellet', 
               'time' : time, 'pressure' : pressure}
        label = f' pp.{time}m.{pressure}b'
        self.apply_op(op, label)

    def exsolve(self, time, temp, frac_H2, frac_Ar, flow_rate):
        assert(frac_H2 + frac_Ar == 1)
        op = {'op' : 'exsolve', 
              'time' : time,
              'temp' : temp,
              'frac_H2' : frac_H2,
              'frac_Ar' : frac_Ar,
              'flow_rate' : flow_rate}
        label = f' ex.{time}h.{temp}C.{int(frac_H2*100)}H2'
        self.apply_op(op, label)

    # Evaluate sample in reactor. Information is incomplete, given complexity of
    # reactor program.
    def test(self):
        op = {'op' : 'test'}
        label = f' test'
        self.apply_op(op, label)

    def num_tests(self):
        result = 0
        for op in self.history:
            if op['op'] == 'test':
                result += 1
        return result

    def has_data(self, data_label):
        if data_label not in data_types:
            raise Exception(f'{data_label} data not implemented')
        file_suffix = data_types[data_label]
        if data_label == 'test':
            num = self.num_tests()
            if num == 0:
                return False
            if num == 1:
                file = Path(f'{self.id}/{self.id}{file_suffix}/rga.csv')
                return file.exists()
            for test_num in range(1, num+1):
                file = Path(f'{self.id}/{self.id}{file_suffix}-{test_num}/rga.csv')
                if not file.exists():
                    return False
            return True
        else:
            file = Path(f'{self.id}/{self.id}{file_suffix}')
            return(file.exists())



# Form sample with a pechini gel. 
def pechini_gel(comp):
    elements = []
    stoichs = []
    try:
        elements = (''.join(c if c.isalpha() else ' ' for c in comp)).split()
        stoichs = (''.join(c if not c.isalpha() else ' ' for c in comp)).split()
    except:
        raise Exception('composition could not be parsed')

    op = {'op' : 'pechini', 'elements' : elements, 'stoichs' : stoichs}

    label = ''
    try:
        assert(len(stoichs) == len(elements))
        for s in stoichs:
            assert(float(s)>0)
        label = ''
        for e, s in zip(elements,stoichs):
            whole, decimal = s.split('.')
            whole = int(whole)
            if whole == 0:
                label = label + e + decimal
            else:
                label = label + e + whole + decimal
        assert(label is not '')
    except:
        raise Exception('label could not be created for composition')

    return Sample(op, label)

def get_sample(id):
    for sample in samples_global:
        if sample.id == id:
            return sample
    raise Exception(f'sample "{id}" could not be found')


# Printing

# ANSI codes for terminal color
class colors:
    HEADER = '\u001b[46;1m'
    RED = '\u001b[31m'
    BOLD ='\u001b[30;1m'
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\u001b[0m'
    CYAN = '\u001b[36m'

def print_counts():
    num_active = 0
    num_retired = 0
    num_lost = 0
    num_error = 0
    for sample in samples_global:
        if sample.retired:
            num_retired += 1
        elif sample.lost:
            num_lost += 1
        elif sample.is_active():
            num_active += 1
        elif sample.has_error:
            num_error += 1 
    print(colors.HEADER + ' Sample Counts '.center(120) + colors.RESET)
    print('Active '.ljust(20, '.') + f' {num_active}')
    print('Retired '.ljust(20, '.') + f' {num_retired}')
    print('Lost '.ljust(20, '.') + f' {num_lost}')
    print('Error '.ljust(20, '.') + f' {num_error}')
    print(colors.BOLD + 'Total '.ljust(20,'.') + f' {len(samples_global)}' + colors.RESET)

def print_active():
    print(colors.HEADER + ' Active Samples '.center(120) + colors.RESET)
    for sample in samples_global:
        if sample.is_active():
            l = colors.CYAN + f'  {sample.id}'.ljust(12) + colors.RESET
            l +=  sample.label
            l += ''.rjust(100-len(l))

            for i, data_label in enumerate(data_types):
                if data_label == 'test' and sample.num_tests() == 0:
                    l += '      '
                    continue
                color = colors.RED
                if sample.has_data(data_label):
                    color = colors.GREEN
                l += color + data_label + '  ' + colors.RESET
            print(l)



#def print_history():
#    print(colors.HEADER + ' History '.center(80) + colors.RESET)
#    
#    for sample in samples_global:
#        if not sample.retired:
#            labels = sample.label.split()
#            ops = [op if op['op'] not in ['split', 'birthed'] for op in 
# sample.history]
#         assert(len(labels) == len(ops))
#         l = f'  {sample.id}'.ljust(12) + '| '
#         for i in range(len(labels)):
#             l += labels[i].ljust(40-6) + '| ' + ops[i].date.ljust(40-6)
#             print(l)
#             l = ''.ljust(40-6)

