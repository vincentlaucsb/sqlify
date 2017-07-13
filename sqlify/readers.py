'''
Functions signed to convert input sources to Python (Table) objects
'''

from sqlify._sqlify import preprocess, strip, resolve_duplicate
from sqlify.factory import Tabulate

import csv
import os

# Helper class for lazy loading files
class YieldTable:
    ''' Lazy loads files into Table objects'''
    
    def __init__(self, file, name, 
        delimiter=' ',
        type='text',
        header=0,
        col_rename={},
        col_names=None,
        col_types=None,
        na_values=None,
        skip_lines=None,
        chunk_size=10000,
        engine='sqlite',
        **kwargs):
        
        '''
        Arguments:
         * file:       A File I/O object
         * type:       Type of file ('text' or 'csv')
         * header:     Number of the line that contains a header (None if no header)
         * skip_lines: Skip the first n lines of the text file
         * delimiter:  How the file is separated
         * col_rename: A dictionary of original column names to new names
         * na_values:  How missing values are encoded (yield_table will replace them with None)
         * chunk_size: Maximum number of rows to read at a time
          * Set to None to load entire file into memory
        '''
        
        # Save user settings
        self.name = name
        self.delimiter = delimiter
        self.col_rename = col_rename
        self.na_values = na_values
        self.chunk_size = chunk_size
        self.type = type
        self.col_types = col_types
        self.kwargs = kwargs
        self.col_names = col_names
        self.engine = engine
        
        # Initalize iterator values
        self.line_num = 0
        
        # Convert boolean values of header to appropriate numeric values
        if isinstance(header, bool):        
            if header:
                self.header = 0 # header = True --> header is on line zero
            else:
                self.header = None
        else:
            self.header = header
        
        # Determine number of lines to skip
        if (skip_lines == None) or (skip_lines == 0):
            # Skip lines = line number of header + 1
            self.skip_lines = header + 1
        else:
            self.skip_lines = skip_lines
            
        # Store the file IO object
        self.io = file
        
        if type == 'csv':
            self.io = csv.reader(file, delimiter=delimiter)
    
    def split_line(self, line):
        # Split one line according to delimiter
    
        line = line.replace('\n', '')
    
        if self.delimiter:
            line = line.split(self.delimiter)
        
        return line
        
    def parse_header(self, row):
        '''
         * Given a header row, parse it according to the user's specifications
          * row should be a list of headers
        '''
        
        # Resolve duplicate names first
        col_names_new = resolve_duplicate(row)
        
        # import pdb; pdb.set_trace()
        
        # Begin rename     
        if self.col_rename:
            for name in self.col_rename:
                try:
                    col_names_new[row.index(name)] = self.col_rename[name]
                except ValueError:
                    raise ValueError(
                        "Can't find {col_name} in list of columns.".format(
                            col_name=name) \
                        + "(Column names are: {col_names})".format(
                            col_names = row))
        
        return col_names_new
    
    def read_next(self):
        # Read next 10000 lines from file
        row_values = None
        
        # Replace null values
        def na_rm(val):
            if val == self.na_values:
                return None
            return val
        
        for line in self.io:
            # For text files, split line along delimiter
            if self.type == 'text':
                line = self.split_line(line)
                
            # Get column names
            if not self.col_names:
                
                '''
                Use header not None because if header = 0, 
                then bool(header) = False
                '''
                
                if self.header is not None:
                    if self.header == self.line_num:
                        self.col_names = self.parse_header(line)
                else:
                    self.col_names = ['col' + str(i) for i in range(0, len(line))]
                    
                row_values = Tabulate.factory(
                    engine=self.engine,
                    name=self.name,
                    col_names=self.col_names,
                    col_types=self.col_types,
                    **self.kwargs)
                
            # Write values
            if self.line_num + 1 > self.skip_lines:
                if self.na_values:
                    line = [na_rm(i) for i in line]
                
                row_values.append(line)
            else:
                # Get file metadata
                if self.header == self.line_num:
                    row_values.raw_header = line
                else:
                    row_values.raw_skip_lines.append(line)
            
            # When len(row_values) = chunk_size: Save and dump values
            if self.chunk_size and self.line_num != 0 and \
                (self.line_num % self.chunk_size == 0):
                
                # Infer schema: Temporary 
                if not self.col_types: 
                    self.col_types = row_values.guess_type()
                    row_values.col_types = row_values.guess_type()
                
                yield row_values
                
                row_values = Tabulate.factory(
                    engine=self.engine,
                    name=self.name,
                    col_names=self.col_names,
                    col_types=self.col_types,
                    **self.kwargs)
                
            self.line_num += 1
    
        # End of loop --> Dump remaining data
        if row_values:
            yield row_values

@preprocess
def yield_table(file, *args, **kwargs):
    '''
    Arguments:
     * file:    Path to file
    '''
    
    with open(file, 'r') as infile: 
        data = YieldTable(file=infile, *args, **kwargs)
    
        for next_lines in data.read_next():
            yield next_lines
            
@preprocess
def head_table(file, *args, **kwargs):
    '''
    Just get the first n lines from a file
    
    Arguments:
     * file:    Path to file
    '''
    i = 0
    
    for tbl in yield_table(file, chunk_size=5000, *args, **kwargs):
        if i == 0:
            head_tbl = tbl
        else:
            break
            
        i += 1
        
    return head_tbl