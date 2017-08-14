'''
.. currentmodule:: sqlify
.. autofunction:: file_to_sqlite
'''

# SQLite Uploaders

from sqlify.core import assert_table, sanitize_names
from sqlify.core.from_text import sample_file, chunk_file
from sqlify.core.schema import DialectSQLite

import sqlite3
import sys

def file_to_sqlite(file, database, delimiter, **kwargs):
    '''
    Loads a file via mass-insert statements.
    
    Parameters
    ------------
    file:           str
                    Name of the file                                      
    database:       str
                    Name of the SQLite database. If it doesn't exist, it  
                    will be created.                                      
    header:         int
                    The line number of the header row
                     - Default: 0 (as in, line zero is the header)      
                     - All lines beyond header are skipped   
    skip_lines:     str 
                    How many lines after header to skip
    delimiter:      str
                    How entries in the file are separated                 
                     - Defaults to '\\t' when using text_to or             
                     - ',' when using csv_to
    '''
    
    with sqlite3.connect(database) as conn:
        build_counter = True
        col_names = []
        
        for chunk in sample_file(file, delimiter=delimiter, col_names=col_names,
            **kwargs):
            table = chunk['table']
            if build_counter:
                table.guess_type()
            table_to_sqlite(table, conn=conn,
                commit=False, **kwargs)
            
            # Pass file IO object between sample_file() calls
            if build_counter:
                build_counter = False
                col_names = table.col_names
            
        conn.commit()
        
@assert_table(dialect=DialectSQLite())
@sanitize_names
def table_to_sqlite(table, database=None, name=None, conn=None,
    commit=True, **kwargs):
    '''
    Load a Table into a SQLite database

    Parameters
    -----------
    table:      Table
    database:   str
                Name of SQLite database
    name:       str
                Name of SQLite table (default: table name)

    .. note:: Fails if there are blank entries in primary key column
    '''
    
    if not conn:
        conn = sqlite3.connect(database)
        
    # Create the table
    if name:
        table_name = name
    else:
        table_name = table.name
        
    # cols = [(column name, column type), ..., (column name, column type)]
    cols = ["{0} {1}".format(name, type) for name, type in \
        zip(table.col_names, table.col_types)]
    
    create_table = "CREATE TABLE IF NOT EXISTS {0} ({1})".format(
        table_name, ", ".join(cols))
    
    conn.execute(create_table)
    
    # Insert columns
    insert_into = "INSERT INTO {0} VALUES ({1})".format(
        table_name, ",".join(['?' for i in range(table.n_cols)]))

    conn.executemany(insert_into, table)
    
    # Moving this into the if branch below causes data to not be written... wtf
    conn.commit()
    
    if commit:
        conn.close()