''' Tests for converting files to JSON '''

import sqlify

import unittest
import json
import os

class JSONOutputTest(unittest.TestCase):
    ''' Test that JSONs are being outputted correctly '''
    
    @staticmethod
    def json_load(json_file):
        ''' Simple helper method which loads JSON files into dicts '''
        with open(json_file, 'r') as test_file:
            test_json = ''.join(test_file.readlines()).replace('\n', '')
        return json.loads(test_json)
        
    def test_output_txt(self):
        ''' Test if a simple TXT file is outputted correctly '''
        
        sqlify.text_to_json('data/tab_delim.txt', 'tab_delim_test.json')
        output = self.json_load('tab_delim_test.json')
        self.assertEqual(output, [
            {"Capital": "Washington", "Country": "USA"},
            {"Capital": "Moscow", "Country": "Russia"},
            {"Capital": "Ottawa", "Country": "Canada"}
        ])
        
    def test_output_csv(self):
        '''
        Compare output vs a previously ouputted JSON which has been
        manually inspected for correctness
        '''
        
        sqlify.csv_to_json('data/us_states.csv', 'us_states_test.json')
        test_json = self.json_load('us_states_test.json')
        compare_json = self.json_load('data/us_states.json')
        self.assertEqual(test_json, compare_json)
        
    def test_output_csv_zip(self):
        ''' Same as above but the input file is compressed '''
        
        zip_file = sqlify.read_zip('data/us_states.zip')
        sqlify.csv_to_json(zip_file['us_states.csv'], 'us_states_zip_test.json')
        
        test_json = self.json_load('us_states_zip_test.json')
        compare_json = self.json_load('data/us_states.json')
        self.assertEqual(test_json, compare_json)
        
    @classmethod
    def tearDownClass(cls):
        os.remove('tab_delim_test.json')
        os.remove('us_states_test.json')
        os.remove('us_states_zip_test.json')
        
# class SimplePGUpload(unittest.TestCase):
    # ''' Test that a simple JSON file is being uploaded correctly '''
    
    # @classmethod
    # def setUpClass(cls):
        # sqlify.json_to_pg('')
        
    # @classmethod
    # def tearDown(cls):
        # os.remove('us_states_test.json')

if __name__ == '__main__':
    unittest.main()