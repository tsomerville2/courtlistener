"""
Behave environment configuration for CourtFinder CLI
"""

def before_all(context):
    """Setup before all tests"""
    context.test_data_dir = "test_data"
    context.sample_files = []
    
def before_scenario(context, scenario):
    """Setup before each scenario"""
    pass
    
def after_scenario(context, scenario):
    """Cleanup after each scenario"""
    pass
    
def after_all(context):
    """Cleanup after all tests"""
    pass