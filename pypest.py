# PEST - Programable Experimental Sample Tree
# Author: Willis O'Leary 

import string
import re
from pathlib import Path

# Global variables for keeping track of some things...
date_global = ''         # Last date set by user with date()
samples_global = []      # List of all samples
data_modules_global = [] # List of loaded data modules

def date(date_string):
    """Sets the working date. Expects the format MMM DD YYYY."""
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

def set_data_modules(*data_modules):
    """Sets any number of data modules to use."""
    global data_modules_global
    data_modules_global = data_modules

def to_base_36(num):
    """Returns num, a base 10 integer, as a base 36 string.""" 
    b = 36
    numerals='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ((num == 0) and numerals[0]) or (to_base_36(num // b).lstrip(numerals[0]) + numerals[num % b])

class DataModule:
    """Abstract class implemented by all data modules. sub_path is a format
    string describing data directories within a sample's directory. Version
    is a unique string with the classes version."""
    def __init__(self, label, sub_dir, version):
        self.label = label
        self.sub_dir = sub_dir
        self.version = version

    def get_label(self):
        """Returns the data module's name."""
        return self.label

    def is_relevant_to(self, sample):
        """Returns wether or not a data module is relevant to a given sample."""
        return True

    def data_exists_for(self, sample):
        """Checks wether or not the sub directory exists for a sample."""
        file = Path(f'{sample.id}/{self.sub_dir}')
        return file.exists()

    def reanalysis_needed_for(self, sample):
        try:
            version = None
            with open(f'{sample.id}/{self.sub_dir}/version', 'r') as file:
                version = file.read()
            if version != self.version:
                return True
        except:
            return True
        return False

    def run_analysis_on(self, sample):
        """Runs an automatic analysis on the data."""
        return None

    def write_version(self, sample):
        with open(f'{sample.id}/{self.sub_dir}/version', 'w') as file:
            file.write(self.version)

class Operation:
    """Abstract class implemented by all operations."""
    def __init__(self, name, label):
        """Constructes operation with a name and a label."""
        self.name = name
        self.label = label
        self.date = date_global

    def get_label(self):
        """Returns the operation's label."""
        return self.label

    def act_on(self, sample):
        """Performs an action on the sample, optionally returning something."""
        return None


class Branch(Operation):
    """Branches a sample any number of times."""
    def __init__(self, branches = 1):
        super().__init__(name = "branch", label = None)
        self.branches = branches

    """Application onto a sample results in a number of children"""
    def act_on(self, sample):
        if sample.children is None:
            sample.children = []
        children = []
        for _ in range(self.branches):
            children.append(Sample(create_op = self, parent = sample))
        sample.children += children 
        if self.branches == 1:
            return children[0]
        else:
            return children

class Sample:
    
    id = None

    def __init__(self, create_op, parent = None):
        """Creates a sample from some operation create_op and optionally 
        a parent sample"""
        global samples_global
        samples_global.append(self)

        prefix = ''
        if parent:
            prefix = f'{parent.id}.'

        ids = [s.id for s in samples_global]
        i = 1
        while(f'{prefix}{i}' in ids):
            i += 1
        id = f'{prefix}{to_base_36(i)}'
        
        self.branch_history   = [create_op] # List of past operations.
        self.parent    = parent      # Parent sample
        self.children  = None        # List of children. Can be None.
        self.id        = id          # Numerical ID
        self.retired   = False       # If retired
        self.lost      = False       # If lost
        self.has_error = False       # If labeled inaccurately, botched, etc.


    def do(self, operation):
        """Applies an operation, returning the results of the operation's act 
        method"""
        self.branch_history.append(operation)
        return operation.act_on(self)

    def report_retired(self):
        """Reports the sample as retired."""
        self.retired = True

    def report_lost(self):
        """Reports the sample as lost."""
        self.lost = True

    def report_error(self):
        """Reports the sample as an error."""
        self.has_error = True

    def is_active(self):
        """Returns True if the sample isn't retired, lost, or botched."""
        return(not self.retired and not self.lost and not self.has_error)

    def get_label(self):
        """Recursively returns the sample's label."""
        label = ''
        if self.parent:
            label = self.parent.get_label()
        label += self.get_branch_label()
        return label

    def get_branch_label(self):
        """Recursively returns the sample's label."""
        label = ''
        for operation in self.branch_history:
            if operation.get_label() is not None:
                label += ' ' + operation.get_label()

        return label

    def get_history(self):
        """Recursively returns the sample's history."""
        history = self.branch_history
        if self.parent:
            history = self.parent.get_history() + history
        return history

    def get_branch_history(self):
        """Returns the sample's history since the last branch."""
        return self.branch_history

    def analyze(self, data_module):
        if data_module.data_exists_for(self):
            return data_module.run_analysis_on(self)
        return None

    def analyze_all(self):
        return [self.analyse(data_module) for data_module in data_modules_global]


def get_sample(id):
    """Returns sample possessing id."""
    for sample in samples_global:
        if sample.id == id:
            return sample
    raise Exception(f'sample "{id}" could not be found')

def update_progress_bar(modules_done, current_module, samples_done, tot_samples, current_sample):
    """Helper function for progress bars."""
    module_label = current_module.label
    sample_id = current_sample.id
    tot_modules = len(data_modules_global)
    bar = '#' * int(modules_done/tot_modules * 25)
    output = f"\r {module_label} ({modules_done}/{tot_modules}): [{bar:25s}]   "
    bar = '#' * int(samples_done/tot_samples * 25)
    output += f" {sample_id} ({samples_done}/{tot_samples}): [{bar:25s}]"
    print(output, end="", flush=True)


# Autoanalysis
def analyze_all():
    for i, data_module in enumerate(data_modules_global):
        samples = []
        for sample in samples_global:
            active = sample.is_active()
            relevant = data_module.is_relevant_to(sample)
            data_exists = data_module.data_exists_for(sample)
            analysis_needed = data_module.reanalysis_needed_for(sample)
            if active and relevant and data_exists and analysis_needed:
                samples.append(sample)
        for j, sample in enumerate(samples):
            update_progress_bar(i+1, data_module, j+1, len(samples), sample)
            try: 
                data_module.run_analysis_on(sample)
                data_module.write_version(sample)
            except Exception as e:
                print(colors.RED + f'{data_module.label} analysis on {sample.id} failed.' + colors.RESET)
                print(e)
    print('\n')


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
            l +=  sample.get_label()
            l += ''.rjust(100-len(l))

            for data_module in data_modules_global:
                label = data_module.get_label()
                if data_module.is_relevant_to(sample):
                    color = colors.RED
                    if data_module.data_exists_for(sample):
                        color = colors.GREEN
                    l += color + label + ' ' + colors.RESET
                else:
                    l += ' ' * len(label) + ' '
            print(l)

def print_tree():
    print(colors.HEADER + ' Sample Tree '.center(120) + colors.RESET)
    parents = [s for s in samples_global if s.parent == None and s.is_active()]
    
    def rec_helper(sample, depth):
        l = colors.CYAN + ' ' * depth + f'  {sample.id}' + colors.RESET
        l +=  sample.get_branch_label()
        print(l)
        if sample.children:
            for child in sample.children:
                rec_helper(child, depth + 1)
    
    for parent in parents:
        rec_helper(parent, 0)
