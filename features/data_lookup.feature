Feature: Lookup Court Records
  As a legal researcher
  I want to search and query parsed court data
  So that I can find specific court records and information

  Scenario: Search court records by criteria
    Given I have parsed court data available
    When I run a lookup command with search criteria
    Then relevant court records should be returned
    And the results should be formatted for easy reading