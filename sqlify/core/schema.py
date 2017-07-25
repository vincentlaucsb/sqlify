''' Functions for inferring and converting schemas '''

PY_TYPES_SQLITE = {
    'str': 'TEXT',
    'int': 'INTEGER',
    'float': 'REAL'
}

PY_TYPES_POSTGRES = {
    'str': 'TEXT',
    'int': 'BIGINT',
    'float': 'DOUBLE PRECISION'
}

def convert_schema(types, from_, to_):
    '''
    Convert SQLite column types to Postgres column types or vice-versa
    
    Arguments:
     * types:           String or list of strings (types)
     * from_, to_:      "sqlite" to "postgres" or vice-versa
    '''
    
    # Use existing py_types dictionaries to avoid duplication of effort
    if from_ == 'sqlite':
        source_types = PY_TYPES_SQLITE
    elif from_ == 'postgres':
        source_types = PY_TYPES_POSTGRES
        
    if to_ == 'postgres':
        dest_types = PY_TYPES_POSTGRES
    if to_ == 'sqlite':
        dest_types = PY_TYPES_SQLITE        
    
    # Should map source dtypes to destination dtypes
    convert = { source_types[dtype].lower(): dest_types[dtype].lower() \
        for dtype in source_types.keys() }
    
    def convert_type(type):
        ''' Converts a single data type '''
        type = type.lower()
        
        try:
            return convert[type]
        except KeyError:
            return type
    
    if isinstance(types, str):
        return convert_type(type)
    elif isinstance(types, list):
        return [convert_type(i) for i in types]
    else:
        raise ValueError('Argument must either be a string or a list of strings.')
    
    return types

class SQLDialect(object):
    '''
    Should be placed as an attribute for Tables so they can properly infer schema
    
    Arguments:
     * py_types:    Mapping of Python types to SQL types
     * guesser:     Function for guessing data types
     * compatible:  A function for determining if two data types are compatible
    '''
    
    def __init__(self, py_types, guesser, compatible):
        self.py_types = py_types
        
        # Dynamically add methods
        self.guesser = guesser
        self.compatible = compatible
        
class DialectSQLite(SQLDialect):
    def __init__(self):
        guesser = guess_data_type_sqlite
        compatible = compatible_sqlite
    
        super(DialectSQLite, self).__init__(PY_TYPES_SQLITE, guesser, compatible)
        
    def __repr__(self):
        return "sqlite"
        
class DialectPostgres(SQLDialect):
    def __init__(self):
        guesser = guess_data_type_pg
        compatible = compatible_pg

        super(DialectPostgres, self).__init__(PY_TYPES_POSTGRES, guesser, compatible)
        
    def __repr__(self):
        return "postgres"

def guess_data_type_sqlite(item):
    ''' Try to guess what data type a given string actually is '''
    
    if item is None:
        return 'INTEGER'
    elif isinstance(item, int):
        return 'INTEGER'
    elif isinstance(item, float):
        return 'REAL'
    else:
        # Strings and other types
        if item.isnumeric():
            return 'INTEGER'
        elif (not item.isnumeric()) and \
            (item.replace('.', '', 1).replace('-', '', 1).isnumeric()):
            '''
            Explanation:
             * A floating point number, e.g. '3.14', in string will not be 
               recognized as being a number by Python via .isnumeric()
             * However, after removing the '.', it should be
            '''
            return 'REAL'
        else:
            return 'TEXT'
            
def guess_data_type_pg(item):
    if item is None:
        # Select option that would have least effect on choosing a type
        return 'BIGINT'
    elif isinstance(item, int):
        return 'BIGINT'
    elif isinstance(item, float):
        return 'DOUBLE PRECISION'
    else:
        # Strings and other types
        if item.isnumeric():
            return 'BIGINT'
        elif (not item.isnumeric()) and \
            (item.replace('.', '', 1).replace('-', '', 1).isnumeric()):
            '''
            Explanation:
             * A floating point number, e.g. '-3.14', in string will not be 
               recognized as being a number by Python via .isnumeric()
             * However, after removing the '.' and '-', it should be
            '''
            return 'DOUBLE PRECISION'
        else:
            return 'TEXT'

def compatible_sqlite(a, b):
    ''' Return if type A can be stored in a column of type B '''
    
    if a == b or a == 'INTEGER':
        return True
    else:
        # Map of types to columns they CANNOT be stored in
        compat = {
            'REAL': ['INTEGER'],
            'TEXT': ['INTEGER', 'REAL'],
        }
        
        return bool(not(b in compat[a]))
            
def compatible_pg(a, b):
    ''' Return if type A can be stored in a column of type B '''
    
    if a == b or a == 'BIGINT':
        return True
    else:
        # Map of types to columns they CANNOT be stored in
        compat = {
            'DOUBLE PRECISION': ['BIGINT'],
            'TEXT': ['BIGINT', 'DOUBLE PRECISION'],
        }
        
        return bool(not(b in compat[a]))