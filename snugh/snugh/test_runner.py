from django.test.runner import DiscoverRunner
from django.core.management import call_command


class TestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        pass

    def teardown_databases(self, old_config, **kwargs):
        pass
