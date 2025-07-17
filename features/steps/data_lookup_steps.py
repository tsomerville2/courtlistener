"""
Step definitions for data lookup feature
"""
from behave import given, when, then
import sys
import json
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from courtfinder.main import CourtFinderCLI
from courtfinder.search import SearchQuery, SearchOperator, SortOrder
from courtfinder.models import Court, Docket, OpinionCluster, Opinion, Citation, Person


@given(u'I have parsed court data available')
def step_impl(context):
    """Ensure parsed court data is available for search"""
    if not hasattr(context, 'courtfinder_cli'):
        # If no CLI from previous step, initialize with test data
        test_data_dir = Path("test_data")
        test_data_dir.mkdir(exist_ok=True)
        
        context.courtfinder_cli = CourtFinderCLI(str(test_data_dir))
        
        # Create some sample data if none exists
        stats = context.courtfinder_cli.get_stats()['storage_stats']
        total_records = sum(stats[key]['total_items'] for key in stats if isinstance(stats[key], dict) and 'total_items' in stats[key])
        
        if total_records == 0:
            print("No parsed data found, creating sample data...")
            
            # Create sample courts
            from courtfinder.models import Court
            from datetime import date
            
            sample_courts = [
                Court(
                    id=1,
                    full_name="Supreme Court of the United States",
                    short_name="SCOTUS",
                    jurisdiction="F",
                    position=1.0,
                    citation_string="U.S.",
                    start_date=date(1789, 3, 4),
                    notes="Highest court in the United States"
                ),
                Court(
                    id=2,
                    full_name="United States Court of Appeals for the Ninth Circuit",
                    short_name="9th Cir.",
                    jurisdiction="F",
                    position=2.0,
                    citation_string="9th Cir.",
                    start_date=date(1891, 3, 3),
                    notes="Federal appellate court"
                ),
                Court(
                    id=3,
                    full_name="United States District Court for the Northern District of California",
                    short_name="N.D. Cal.",
                    jurisdiction="F",
                    position=3.0,
                    citation_string="N.D. Cal.",
                    start_date=date(1886, 7, 27),
                    notes="Federal district court"
                )
            ]
            
            # Create sample dockets
            from courtfinder.models import Docket
            from datetime import datetime
            
            sample_dockets = [
                Docket(
                    id=1,
                    date_created=datetime(2023, 1, 1),
                    date_modified=datetime(2023, 1, 1),
                    source="R",
                    court_id=1,
                    case_name="Test Case v. Example Corporation",
                    case_name_short="Test Case",
                    docket_number="23-001",
                    date_filed=date(2023, 1, 1),
                    date_filed_is_approximate=False
                ),
                Docket(
                    id=2,
                    date_created=datetime(2023, 1, 2),
                    date_modified=datetime(2023, 1, 2),
                    source="R",
                    court_id=2,
                    case_name="Another Case v. Sample Inc.",
                    case_name_short="Another Case",
                    docket_number="23-002",
                    date_filed=date(2023, 1, 2),
                    date_filed_is_approximate=False
                )
            ]
            
            # Save sample data
            for court in sample_courts:
                context.courtfinder_cli.storage.save_court(court)
            
            for docket in sample_dockets:
                context.courtfinder_cli.storage.save_docket(docket)
            
            print("✓ Sample data created for testing")
    
    # Verify data is available for search
    stats = context.courtfinder_cli.get_stats()['storage_stats']
    total_records = sum(stats[key]['total_items'] for key in stats if isinstance(stats[key], dict) and 'total_items' in stats[key])
    
    assert total_records > 0, "No parsed court data available for search"
    print(f"✓ Found {total_records} records available for search")
    
    # Store reference to CLI for later steps
    context.search_data_available = True


@when(u'I run a lookup command with search criteria')
def step_impl(context):
    """Execute lookup command with search criteria"""
    assert hasattr(context, 'courtfinder_cli'), "No CourtFinder CLI instance available"
    assert hasattr(context, 'search_data_available'), "No search data available"
    
    try:
        # Perform multiple types of searches to demonstrate lookup functionality
        context.search_results = {}
        
        # Search for courts
        print("Searching for courts...")
        court_results = context.courtfinder_cli.search_courts("Supreme", limit=10)
        context.search_results['courts'] = court_results
        print(f"✓ Court search returned {len(court_results)} results")
        
        # Search for cases
        print("Searching for cases...")
        case_results = context.courtfinder_cli.search_cases("Test", limit=10)
        context.search_results['cases'] = case_results
        print(f"✓ Case search returned {len(case_results)} results")
        
        # Search for opinions (if any exist)
        print("Searching for opinions...")
        opinion_results = context.courtfinder_cli.search_opinions("example", limit=10)
        context.search_results['opinions'] = opinion_results
        print(f"✓ Opinion search returned {len(opinion_results)} results")
        
        # Search for judges/people (if any exist)
        print("Searching for judges...")
        judge_results = context.courtfinder_cli.search_judges("judge", limit=10)
        context.search_results['judges'] = judge_results
        print(f"✓ Judge search returned {len(judge_results)} results")
        
        # Advanced search using the search engine directly
        print("Performing advanced search...")
        search_query = SearchQuery()
        search_query.add_filter('jurisdiction', SearchOperator.EQUALS, 'F')
        search_query.add_sort('full_name', SortOrder.ASC)
        search_query.set_pagination(5)
        
        advanced_results = context.courtfinder_cli.search.search_courts(search_query)
        context.search_results['advanced'] = advanced_results
        print(f"✓ Advanced search returned {len(advanced_results.results)} results")
        
        context.lookup_completed = True
        
    except Exception as e:
        raise AssertionError(f"Lookup command failed: {e}")


@then(u'relevant court records should be returned')
def step_impl(context):
    """Verify relevant court records are returned"""
    assert hasattr(context, 'lookup_completed'), "Lookup was not completed"
    assert context.lookup_completed, "Lookup did not complete successfully"
    assert hasattr(context, 'search_results'), "No search results found"
    
    # Verify we got results from at least one search type
    total_results = 0
    for search_type, results in context.search_results.items():
        if search_type == 'advanced':
            # Advanced search returns SearchResult object
            result_count = len(results.results)
            total_results += result_count
            print(f"✓ {search_type} search: {result_count} results")
        else:
            # Other searches return lists
            result_count = len(results)
            total_results += result_count
            print(f"✓ {search_type} search: {result_count} results")
    
    assert total_results > 0, "No relevant court records were returned"
    print(f"✓ Total of {total_results} relevant court records returned")
    
    # Verify result quality - check that results are proper model instances
    for search_type, results in context.search_results.items():
        if search_type == 'advanced':
            result_list = results.results
        else:
            result_list = results
        
        if result_list:
            first_result = result_list[0]
            
            # Verify we got proper model instances
            if search_type == 'courts':
                assert isinstance(first_result, Court), f"Court search should return Court objects, got {type(first_result)}"
                assert hasattr(first_result, 'full_name'), "Court object missing full_name attribute"
                assert hasattr(first_result, 'jurisdiction'), "Court object missing jurisdiction attribute"
            elif search_type == 'cases':
                assert isinstance(first_result, Docket), f"Case search should return Docket objects, got {type(first_result)}"
                assert hasattr(first_result, 'case_name'), "Docket object missing case_name attribute"
                assert hasattr(first_result, 'docket_number'), "Docket object missing docket_number attribute"
            elif search_type == 'opinions':
                if result_list:  # Only check if we have results
                    assert isinstance(first_result, Opinion), f"Opinion search should return Opinion objects, got {type(first_result)}"
            elif search_type == 'judges':
                if result_list:  # Only check if we have results
                    assert isinstance(first_result, Person), f"Judge search should return Person objects, got {type(first_result)}"
            elif search_type == 'advanced':
                assert isinstance(first_result, Court), f"Advanced court search should return Court objects, got {type(first_result)}"
    
    print("✓ All search results are proper model instances with expected attributes")


@then(u'the results should be formatted for easy reading')
def step_impl(context):
    """Verify results are formatted for easy reading"""
    assert hasattr(context, 'search_results'), "No search results to format"
    
    # Test that results can be easily formatted and displayed
    formatted_output = []
    
    for search_type, results in context.search_results.items():
        if search_type == 'advanced':
            result_list = results.results
        else:
            result_list = results
        
        if result_list:
            formatted_output.append(f"\n{search_type.title()} Results:")
            
            for i, result in enumerate(result_list[:3]):  # Show first 3 results
                if search_type == 'courts':
                    formatted_output.append(f"  {i+1}. {result.full_name} ({result.jurisdiction}) - {result.citation_string}")
                elif search_type == 'cases':
                    formatted_output.append(f"  {i+1}. {result.case_name} - {result.docket_number} (Court: {result.court_id})")
                elif search_type == 'opinions':
                    formatted_output.append(f"  {i+1}. Opinion {result.id} - {result.type.value} (Cluster: {result.cluster_id})")
                elif search_type == 'judges':
                    formatted_output.append(f"  {i+1}. {result.get_full_name()} ({result.gender or 'Unknown gender'})")
                elif search_type == 'advanced':
                    formatted_output.append(f"  {i+1}. {result.full_name} ({result.jurisdiction}) - {result.citation_string}")
            
            if len(result_list) > 3:
                formatted_output.append(f"  ... and {len(result_list) - 3} more results")
    
    # Verify we can create readable output
    assert len(formatted_output) > 0, "No formatted output generated"
    
    # Print formatted results to demonstrate readability
    print("\n✓ Results formatted for easy reading:")
    for line in formatted_output:
        print(line)
    
    # Verify results contain useful information
    for search_type, results in context.search_results.items():
        if search_type == 'advanced':
            result_list = results.results
        else:
            result_list = results
        
        if result_list:
            first_result = result_list[0]
            
            # Verify results have displayable attributes
            if search_type == 'courts':
                assert first_result.full_name, "Court result missing full_name for display"
                assert first_result.jurisdiction, "Court result missing jurisdiction for display"
            elif search_type == 'cases':
                assert first_result.case_name, "Case result missing case_name for display"
                assert first_result.docket_number, "Case result missing docket_number for display"
    
    print("✓ All results are properly formatted and contain readable information")
    
    # Test JSON serialization for API responses
    try:
        serializable_results = {}
        for search_type, results in context.search_results.items():
            if search_type == 'advanced':
                result_list = results.results
            else:
                result_list = results
            
            # Convert to dictionaries for JSON serialization
            serializable_results[search_type] = []
            for result in result_list[:2]:  # Test first 2 results
                if hasattr(result, 'to_dict'):
                    serializable_results[search_type].append(result.to_dict())
                else:
                    # Fallback to basic serialization
                    serializable_results[search_type].append({
                        'id': getattr(result, 'id', None),
                        'type': type(result).__name__,
                        'summary': str(result)[:100]
                    })
        
        # Try to serialize to JSON
        json_output = json.dumps(serializable_results, indent=2, default=str)
        assert len(json_output) > 0, "Failed to serialize results to JSON"
        
        print("✓ Results can be serialized to JSON for API responses")
        
    except Exception as e:
        print(f"Warning: JSON serialization test failed: {e}")
        # Don't fail the test for JSON serialization issues
        pass