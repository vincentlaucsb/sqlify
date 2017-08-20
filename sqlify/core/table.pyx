'''
Table
=======
A general two-dimensional data structure
'''

from sqlify._globals import SQLIFY_PATH
from ._base_table import BaseTable
from ._core import strip
from ._table import *
from .column_list import ColumnList
from .schema import SQLType, SQLDialect, DialectSQLite, DialectPostgres

from collections import Counter, defaultdict, deque, Iterable
from inspect import signature
import re
import copy
import types
import functools
import warnings

def append(self, value):
    ''' Don't append rows with the wrong length '''
    
    cdef int n_cols = self.n_cols
    cdef value_len = len(value)
    cdef int i
    
    if n_cols != value_len:
        ''' Future: Add a warning before dropping '''
        pass
    else:
        # Add to type counter
        for i, j in enumerate(value):
            self._type_cnt[self.columns._idx[i]][type(j)] += 1
            
        super(Table, self).append(value)
   
def update_type_count(func):
    ''' Brute force approach to updating a Table's type counter '''

    @functools.wraps(func)
    def inner(table, *args, **kwargs):
        # Run the function first
        ret = func(table, *args, **kwargs)
        
        # Re-build counter
        table._type_cnt.clear()
        for col in table.col_names:
            for i in table[col]:
                table._type_cnt[col][type(i)] += 1
                
        return ret
    return inner    
           
class Table(BaseTable):
    '''
    Two-dimensional data structure reprsenting a tabular dataset
     - Is a list of lists
    
    Attributes
    -----------
    name:       str
                Name of the Table
    col_names:  list
                List of column names
    col_types:  list
                List of column types, always lowercase
    p_key:      int
                Index of the primary key
    _type_cnt:  defaultdict
                Mappings of column names to counters of data types for that column
    
    .. note:: All Table manipulation actions modify a Table in place unless otherwise specified
    '''
    
    # Define attributes to save memory
    __slots__ = ['name', 'columns', '_dialect', '_pk_idx', '_type_cnt']
        
    def __init__(self, name, dialect='sqlite', columns=None, col_names=[], p_key=None, type_count=True,
        *args, **kwargs):
        '''
        Parameters
        -----------
        name:       str
                    Name of the Table
        dialect:    SQLDialect
                    A SQLDialect object
        col_names   list
                    A list specifying names of columns (Either this or columns required)
        row_values: list
                    A list of rows (i.e. a list of lists)
        col_values: list
                    A list of column values
        p_key:      int
                    Index of column used as a primary key
        type_count: bool
                    Build an auto-updating type counter
                    
        Structure of Type Counter
        --------------------------
        Suppose 'apples' and 'oranges' are column names
        
        {
         'apples': {
          'str': <Number of strings>,
          'datetime': <Number of datetime objects>
         }, {
         'oranges':
          'int': <Number of ints>,
          'float': <Number of floats>
         }        
        }
        '''
        
        self.dialect = dialect
        
        # Dynamically overload append method to build a counter
        if type_count:
            self._type_cnt = defaultdict(lambda: defaultdict(int))
            self.append = types.MethodType(append, self)
        
        # Build content
        if 'col_values' in kwargs:
            # Convert columns to rows
            n_rows = range(0, len(kwargs['col_values'][0]))
            row_values = [[col[row] for col in kwargs['col_values']] for row in n_rows]
        elif 'row_values' in kwargs:
            row_values = kwargs['row_values']
        else:
            row_values = []
            
        # Set up column information
        if columns:
            self.columns = columns
        else:
            self.columns = ColumnList(col_names=col_names, col_types='text', p_key=p_key)
            
        self._pk_idx = {}
        
        # Add row values to type counter
        if row_values:
            for row in row_values:
                for i, j in enumerate(row):
                    self._type_cnt[self.columns._idx[i]][type(j)] += 1
        
        # Add methods dynamically
        self.add_dicts = types.MethodType(add_dicts, self)
        self.guess_type = types.MethodType(guess_type, self)
        
        super(Table, self).__init__(name=name, row_values=row_values)
    
    def _create_pk_index(self):
        ''' Create an index for the primary key column '''
        if self.p_key is not None:
            self._pk_idx = {row[self.p_key]: row for row in self}

    @property
    def col_names(self):
        return self.columns.col_names
        
    @col_names.setter
    def col_names(self, value):
        rename = {x: y for x, y in zip(self.col_names, value)}
        self.columns.col_names = value
        
        # Re-build counter
        for old_name, new_name in zip(rename.keys(), rename.values()):
            self._type_cnt[new_name] = self._type_cnt[old_name]
            del self._type_cnt[old_name]
            
    @property
    def col_names_sanitized(self):
        return self.columns.sanitize()
        
    @property
    def col_types(self):
        return self.columns.col_types
        
    @col_types.setter
    def col_types(self, value):
        self.columns.col_types = value
        
    @property
    def n_cols(self):
        return self.columns.n_cols
        
    @property
    def p_key(self):
        return self.columns.p_key
        
    @p_key.setter
    def p_key(self, value):
        self.columns.p_key = value
        self._create_pk_index()
        
    @property
    def dialect(self):
        return self._dialect
        
    @dialect.setter
    def dialect(self, value):
        if isinstance(value, SQLDialect):
            self._dialect = value
        elif value == 'sqlite':
            self._dialect = DialectSQLite()
        elif value == 'postgres':
            self._dialect = DialectPostgres()
        else:
            raise ValueError("'dialect' must either 'sqlite' or 'postgres'")

    @staticmethod
    def copy_attr(table_, row_values=[]):
        ''' Returns a new Table with just the same attributes '''
        return Table(name=table_.name, dialect=table_.dialect,
            columns=table_.columns, row_values=row_values)
    
    def __getitem__(self, key):
        if isinstance(key, slice):
            # Make slice operator return a Table object not a list
            return self.copy_attr(self,
                row_values=super(Table, self).__getitem__(key))
        elif isinstance(key, tuple):
            # Support indexing by primary key
            if len(key) == 1:
                return self._pk_idx[key[0]]
            else:
                if isinstance(key[0], str):
                    return self._pk_idx[key[0]][self.columns.index(key[1])]
                else:
                    return self._pk_idx[key[0]][key[1]]
        elif isinstance(key, str):
            # Support indexing by column name
            return [row[self.columns.index(key)] for row in self]
        else:
            return super(Table, self).__getitem__(key)
    
    def to_string(self):
        ''' Return this table as a StringIO object for writing via copy() '''
        return self.dialect.to_string(self)
    
    ''' Table merging functions '''
    def widen(self, w, placeholder='', in_place=True):
        '''
        Widen table until it is of width w
         * Fills in new columns with placeholder
         * in_place:    Widen in place if True, else return copy
        '''
        
        add_this_much = w - self.n_cols
        self.n_cols = w
        
        if in_place:
            for row in self:
                row += [placeholder]*add_this_much
        else:
            new_table = self.copy()
            new_table.widen(w)
            
            return new_table
    
    def __add__(self, other):
        ''' 
        For Tables:
            Merge two tables vertically (returns new Table)
             * Column names are from first table
             * Less wide tables auto-filled with placeholders
             
        For Others:
            * Call parent method       
        '''
        
        if isinstance(other, Table):
            widen_this_much = max(self.n_cols, other.n_cols)
            
            if self.n_cols > other.n_cols:
                other.widen(widen_this_much, in_place=False)
            elif other.n_cols < self.n_cols:
                self.widen(widen_this_much, in_place=False)
            
            return self.copy_attr(self, row_values =
                super(Table, self).__add__(other))
        else:
            return super(Table, self).__add__(other)
            
    ''' Table Manipulation Methods '''
    def drop_empty(self):
        ''' Remove all empty rows '''
        remove = deque()  # Need something in LIFO order
        
        for i, row in enumerate(self):
            if not sum([bool(j or j == 0) for j in row]):
                remove.append(i)
            
        # Remove from bottom first
        while remove:
            del self[remove.pop()]
    
    @update_type_count
    def as_header(self, i=0):
        '''
        Replace the current set of column names with the data from the 
        ith column. Defaults to first row.
        '''
        
        self.col_names = copy.copy(self[i])
        del self[i]
    
    def delete(self, col):
        '''
        Delete a column
        
        Parameters
        ------------
        col:        str, int
                    Delete column named col or at position col
        '''
        
        index = self._parse_col(col)
        self.columns.del_col(index)
        
        for row in self:
            del row[index]
            
    def apply(self, *args, **kwargs):
        super(Table, self).apply(*args, **kwargs)

    def aggregate(self, col, func=None):
        super(Table, self).aggregate(col, func)
    
    @update_type_count
    def add_col(self, col, fill):
        ''' Add a new column to the Table
        
        Parameters
        -----------
        col:        str
                    Name of new column
        fill:      
                    What to put in new column
        '''
        self.columns.add_col(col)
        
        for row in self:
            row.append(fill)

    def label(self, col, label):
        ''' Add a label to the dataset '''        
        self.add_col(col, label)
    
    def mutate(self, col, func, *args):
        '''
        Similar to `apply()`, but creates a new column--instead of modifying 
        a current one--based on the values of other columns.
        
        Parameters
        -----------
        col:            str
                        Name of new column (string)
        func:           function
                        Function or lambda to apply
        *args:          str, int
                        Names of indices of columns that func needs
        '''
            
        source_indices = [self._parse_col(i) for i in args]

        try:
            col_index = self.col_names.index(col)
        except ValueError:
            col_index = None
            
        if col_index:
            raise ValueError('{} already exists. Use apply() to transform existing columns.'.format(col))
        else:
            self.columns.add_col(col)
        
        for row in self:
            row.append(func(*[row[i] for i in source_indices]))
        
    def reorder(self, *args):
        '''
        Return a **new** Table in the specified order (instead of modifying in place)
         * Arguments should be names or indices of columns
         * Can be used to take a subset of the current Table
         * Method runs in O(mn) time where m = number of columns in new Table
           and n is number of rows
        '''

        '''
        Time Complexity:
         * Reference: https://wiki.python.org/moin/TimeComplexity
         * Let m = width of new table, n = number of rows
         * List Comp: [row[i] for i in org_indices]
           * List access is O(1), so this list comp is O(2m) ~ O(m)
             where m is width of new table
         * For Loop: Executes inner listcomp for every row
         * So reorder() is O(mn)
        '''
        
        orig_indices = [self._parse_col(i) for i in args]
        
        new_table = Table(
            name = self.name,
            dialect = self.dialect,
            col_names = [self.col_names[i] for i in orig_indices])
            
        # TEMPORARY: Update p_key
        if self.p_key in orig_indices:
            new_table.p_key = orig_indices.index(self.p_key)
        
        for row in self:
            new_table.append([row[i] for i in orig_indices])
            
        new_table.guess_type()
        
        return new_table
        
    def subset(self, *cols):
        '''
        Return a subset of the Table with the specified columns
         * Really just an alias for reorder()
        '''
        return self.reorder(*cols)
        
    def transpose(self, include_header=True):
        '''
        Swap rows and columns
        
        Parameters
        -----------
        include_header:     bool
                            Treat header as a row in the operation
        '''
        if include_header:
            row_values = [[col] + self[col] for col in self.col_names]
        else:
            row_values = [self[col] for col in self.col_names]
        
        return Table(
            name = self.name,
            row_values = row_values
        )
        
    def groupby(self, col):
        ''' 
        Return a dict of Tables where the keys are unique entries
        in col and values are all rows with where row[col] = that key
        '''
        
        col_index = self._parse_col(col)
        table_dict = defaultdict(lambda: self.copy_attr(self))
        
        # Group by
        for row in self:
            table_dict[row[col_index]].append(row)
            
        # Set table names equal to key
        for k in table_dict:
            table_dict[k].name = k
            
        return table_dict
            
    def add_dict(self, dict, *args, **kwargs):
        self.add_dicts([dict], *args, **kwargs)