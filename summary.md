# BDD Project Initialized - CourtFinder CLI

## Generated Structure
- ✅ BDD framework configured (behave)
- ✅ Domain model defined (docs/ddd.md)
- ✅ State flow mapped (docs/state-diagram.md)
- ✅ Mission clarified (docs/mission.md)
- ✅ Features created (data_download.feature, data_parsing.feature, data_lookup.feature)
- ✅ Architecture planned (main_controller.pseudo, data_downloader.pseudo, data_parser.pseudo, data_searcher.pseudo)

## Quick Start
1. Review the generated documents in docs/
2. Examine the features/ directory
3. Check pseudocode/ for the planned architecture

## Next Steps
Run the bddloop command to:
- Generate step definitions
- Implement the pseudocode as real code
- Make all tests pass

## Configuration
- Tech Stack: python-fastapi
- BDD Framework: behave
- App Goal: "Create python CLI that can download freelaw.org bulk data samples, parse them including problematic columns 12-18, and provide interactive lookup functionality"

## Key Features
- **Download**: Manages sample downloads with size limits to handle 300GB dataset
- **Parse**: Handles problematic columns 12-18 with special parsing logic
- **Lookup**: Interactive CLI search using questionary/rich for user-friendly queries