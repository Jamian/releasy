import os
import unittest

from click.testing import CliRunner

from releasy.main import _is_iac, run

class TestReleasy(unittest.TestCase):

    def test_iac_regex_check_success(self):
        for repo_name in ['terraform-layer-foo', 'terraform-layer-some-thing-else', 'terraform-layer-aThing']:
            self.assertTrue(_is_iac(repo_name, '^terraform-layer-.*$'))

        for repo_name in ['bad', 'someapplication-terraform-layer']:
            self.assertFalse(_is_iac(repo_name, '^terraform-layer-.*$'))
    
    def test_run_value_errors_raised(self):
        runner = CliRunner()
        result = runner.invoke(run)
        self.assertTrue(result.exit_code, 1)
        self.assertTrue(type(result.exception) == ValueError)
        self.assertEqual(str(result.exception), 'Missing required input "version". Please see help.')

        result = runner.invoke(run, ['--version', '0.0.0'])
        self.assertTrue(result.exit_code, 1)
        self.assertTrue(type(result.exception) == ValueError)
        self.assertEqual(str(result.exception), 'Missing required input "projects". Please see help.')