Feature: Parse Court Data
  As a legal researcher
  I want to parse downloaded bulk data into structured records
  So that I can search and analyze court information effectively

  Scenario: Parse data including problematic columns
    Given I have downloaded court data files
    When I run the parse command
    Then the data should be extracted into structured records
    And columns 12-18 should be parsed successfully
    And the parsed data should be searchable