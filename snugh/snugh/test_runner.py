from django.test.runner import DiscoverRunner
from django.core.management import call_command


class TestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        result = super(TestRunner, self).setup_databases(**kwargs)
        call_command('copydata')
        return result

    def teardown_databases(self, old_config, **kwargs):
        return super(TestRunner, self).teardown_databases(old_config, **kwargs)
        