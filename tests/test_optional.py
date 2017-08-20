''' Test that optional dependencies are optional '''

from sqlify.testing import *
import sqlify

import unittest
import os
import configparser

class ImportTest(unittest.TestCase):
    def test_returns_none(self):
        '''
        Assert that trying to import a non-existent package
        returns None
        '''
        self.assertEqual(import_package('harambe'), None)

class ErrorTest(unittest.TestCase):
    ''' Test that the correct error messages for missing packages are displayed '''
    
    @unittest.skipUnless(not TEST_OPTIONAL_DEPENDENCY,
        'Currently testing optional dependencies')
    def test_html(self):
        with self.assertRaises(ImportError):
            sqlify.html.from_url('https://stackoverflow.com')        
        
    @unittest.skipUnless(not TEST_OPTIONAL_DEPENDENCY,
        'Currently testing optional dependencies')
    def test_pandas(self):
        with self.assertRaises(ImportError):
            sqlify.pandas_to_table([])
            
    # @unittest.skipUnless(not TEST_OPTIONAL_DEPENDENCY,
        # 'Currently testing optional dependencies')
    # def test_alchemy(self):
        # with self.assertRaises(ImportError):
            # x = sqlify.SQLTable()

if __name__ == '__main__':
    unittest.main()