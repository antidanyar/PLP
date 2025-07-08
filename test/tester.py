import unittest
from test_utils import TestUtils
from test_segment import TestSegment
from test_sequence import TestSequence
from test_rule import TestRule
from test_alphabet import TestAlphabet
from test_plp import TestPLP

'''
A script to run all the test cases.
'''
# load test suites
test_utils_suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
test_segment_suite = unittest.TestLoader().loadTestsFromTestCase(TestSegment)
test_sequence_suite = unittest.TestLoader().loadTestsFromTestCase(TestSequence)
test_rule_suite = unittest.TestLoader().loadTestsFromTestCase(TestRule)
test_alphabet_suite = unittest.TestLoader().loadTestsFromTestCase(TestAlphabet)
test_plp_suite = unittest.TestLoader().loadTestsFromTestCase(TestPLP)
# combine the test suites
suites = unittest.TestSuite([test_utils_suite,
                             test_segment_suite,
                             test_sequence_suite,
                             test_rule_suite,
                             test_alphabet_suite,
                             test_plp_suite])
# run the test suites
unittest.TextTestRunner(verbosity=2).run(suites)
