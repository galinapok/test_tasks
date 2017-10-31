from testp4 import create_dest_folder 
from testp4 import check_for_updates 
from testp4 import run_build
from testp4 import read_config
from P4 import P4,P4Exception 
import unittest
import os
import shutil
class MyTest(unittest.TestCase):
    directory =  ""
    def test_create_dest_folder(self):
        print (self.directory)
        self.directory = create_dest_folder(os.getcwd())
        print (self.directory)
        self.assertTrue(os.path.exists(self.directory))   

    def test_read_config(self):
        self.assertEqual(len(read_config("config.ini")), 10)

    
    def test_run_build(self):    
        self.assertEqual(len(run_build("//test/proj1/...")), 3)

    def test_check_for_updates(self):
        with self.assertRaises(SystemExit) as cm:
            check_for_updates(P4(), "")
        self.assertEqual(cm.exception.code, 1)

    def tearDown(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)



if __name__ == '__main__':
    unittest.main()

