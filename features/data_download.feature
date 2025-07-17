Feature: Download Court Data
  As a legal researcher
  I want to download manageable samples of court data
  So that I can analyze court records without overwhelming my system

  Scenario: Download sample data with size limit
    Given the freelaw.org bulk data is available
    When I run the download command with a 500MB limit
    Then a sample dataset should be downloaded successfully
    And the downloaded file should be under 500MB
    And the data should be validated and ready for parsing