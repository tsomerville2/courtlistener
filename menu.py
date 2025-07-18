#!/usr/bin/env python3
"""
CourtFinder CLI - Beautiful Menu Interface

Transform 300GB freelaw.org bulk court data into accessible, searchable court records.
This is the main entry point providing an intuitive menu-driven experience.
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.layout import Layout
    from rich.align import Align
    from rich.rule import Rule
    from rich.syntax import Syntax
    from rich.traceback import install
    from rich.live import Live
    from rich.status import Status
    from rich.columns import Columns
    from rich.padding import Padding
    from rich.box import ROUNDED
    import questionary
except ImportError:
    print("Installing required dependencies...")
    os.system("pip install rich questionary")
    print("Please restart the application after installation.")
    sys.exit(1)

# Install rich traceback handler for better error display
install(show_locals=True)

# Import our domain models and services
try:
    from courtfinder.main import CourtFinderCLI
    from courtfinder.models import Court, Docket, OpinionCluster, Opinion, Citation, Person
    from courtfinder.search import SearchQuery, SearchOperator, SortOrder
    from courtfinder.storage import CourtFinderStorage
except ImportError as e:
    console = Console()
    console.print(f"[red]Error importing CourtFinder modules: {e}[/red]")
    console.print("[yellow]Please ensure the CourtFinder package is properly installed.[/yellow]")
    sys.exit(1)


class CourtFinderMenu:
    """Beautiful menu interface for CourtFinder CLI"""
    
    def __init__(self):
        self.console = Console()
        self.data_dir = Path("data")
        self.test_data_dir = Path("test_data")
        self.real_data_dir = Path("real_data")
        self.courtfinder_cli = None
        
        # Initialize with real data if available, then test data, then regular data
        if self.real_data_dir.exists():
            try:
                self.courtfinder_cli = CourtFinderCLI(str(self.real_data_dir))
                self.using_test_data = False
                self.using_real_data = True
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not initialize with real data: {e}[/yellow]")
                self.courtfinder_cli = CourtFinderCLI(str(self.data_dir))
                self.using_test_data = False
                self.using_real_data = False
        elif self.test_data_dir.exists():
            try:
                self.courtfinder_cli = CourtFinderCLI(str(self.test_data_dir))
                self.using_test_data = True
                self.using_real_data = False
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not initialize with test data: {e}[/yellow]")
                self.courtfinder_cli = CourtFinderCLI(str(self.data_dir))
                self.using_test_data = False
                self.using_real_data = False
        else:
            self.courtfinder_cli = CourtFinderCLI(str(self.data_dir))
            self.using_test_data = False
            self.using_real_data = False
    
    def show_banner(self):
        """Display beautiful welcome banner"""
        banner_text = Text.assemble(
            ("🏛️  ", "bright_yellow"),
            ("CourtFinder CLI", "bright_blue bold"),
            ("  🏛️", "bright_yellow")
        )
        
        subtitle = Text.assemble(
            ("Transform 300GB Legal Data into Searchable Records", "bright_white italic")
        )
        
        # Show data source status
        if self.using_real_data:
            data_source = Text.assemble(
                ("Data Source: ", "dim"),
                ("✅ Real FreeLaw Bulk Data (657+ courts)", "bright_green")
            )
        elif self.using_test_data:
            data_source = Text.assemble(
                ("Data Source: ", "dim"),
                ("⚠️  Test Data (sample records)", "bright_yellow")
            )
        else:
            data_source = Text.assemble(
                ("Data Source: ", "dim"),
                ("❌ No data - run download/parse first", "bright_red")
            )
        
        banner_content = Align.center(
            Text.assemble(
                banner_text, "\n",
                subtitle, "\n\n",
                data_source
            )
        )
        
        panel = Panel(
            banner_content,
            box=ROUNDED,
            border_style="bright_blue",
            padding=(1, 2),
            width=84
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def _build_menu_items(self):
        """Build contextual menu items based on current state"""
        # Check system state
        downloads_dir = Path("downloads")
        real_data_dir = Path("real_data")
        
        # Check what's downloaded
        bz2_files = list(downloads_dir.glob("*.bz2")) if downloads_dir.exists() else []
        has_downloads = len(bz2_files) > 0
        
        # Check what's parsed
        has_parsed_data = real_data_dir.exists() and self.using_real_data
        
        # Check if there's searchable data
        has_searchable_data = has_parsed_data
        
        # Build contextual menu
        menu_items = []
        
        # Always show data status first
        menu_items.append(("1", "📊", "View Data Status", "See what data you have and what's available", "bright_cyan"))
        
        # Download options
        if not has_downloads:
            menu_items.append(("2", "📥", "Download Court Data", "Download ~30GB real FreeLaw bulk data", "bright_blue"))
        else:
            total_size = sum(f.stat().st_size for f in bz2_files)
            menu_items.append(("2", "📥", "Manage Downloads", f"You have {len(bz2_files)} files ({total_size/1024/1024:.1f}MB) - download more?", "bright_blue"))
        
        # Parse options
        if has_downloads and not has_parsed_data:
            menu_items.append(("3", "🔧", "Parse Downloaded Data", "⭐ NEXT STEP: Process your downloads with progress UI", "bright_yellow"))
        elif has_downloads and has_parsed_data:
            menu_items.append(("3", "🔧", "Re-parse Data", "✅ Already parsed - reprocess with different options?", "dim"))
        elif not has_downloads:
            menu_items.append(("3", "🔧", "Parse Data", "❌ No downloads found - download data first", "dim"))
        
        # Search options
        if has_searchable_data:
            menu_items.append(("4", "🔍", "Search Court Records", "✅ Search your parsed data", "bright_magenta"))
        else:
            menu_items.append(("4", "🔍", "Search Records", "❌ No searchable data - parse data first", "dim"))
        
        # Quick start for new users
        if not has_downloads and not has_parsed_data:
            menu_items.append(("5", "🚀", "Quick Start", "⭐ NEW USER: Download sample → Parse → Search", "bright_green"))
        
        # Always available
        menu_items.append(("6", "❓", "Help", "Show detailed help information", "bright_white"))
        menu_items.append(("7", "🚪", "Exit", "Exit CourtFinder CLI", "bright_red"))
        
        return menu_items
    
    def show_menu(self):
        """Display contextual menu options based on current state"""
        menu_items = self._build_menu_items()
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("", width=3)
        table.add_column("", width=3)
        table.add_column("", width=25)
        table.add_column("", width=45)
        
        for num, emoji, title, desc, color in menu_items:
            table.add_row(
                f"[{color}]{num}.[/{color}]",
                f"{emoji}",
                f"[{color} bold]{title}[/{color} bold]",
                f"[dim]{desc}[/dim]"
            )
        
        panel = Panel(
            table,
            title="[bright_white bold]Main Menu[/bright_white bold]",
            border_style="bright_blue",
            padding=(1, 2),
            width=84
        )
        
        self.console.print(panel)
        self.console.print()
    
    def quick_start(self):
        """Quick start workflow: Download sample → Parse → Search"""
        self.console.print(Panel(
            "[bright_green bold]🚀 Quick Start: Complete CourtFinder Workflow[/bright_green bold]",
            border_style="bright_green"
        ))
        
        if not self.using_test_data:
            self.console.print("[yellow]Note: This will download sample data for demonstration.[/yellow]")
            if not Confirm.ask("Continue with Quick Start?"):
                return
        
        try:
            # Step 1: Check/Setup Sample Data
            with Status("[bright_blue]Checking sample data...[/bright_blue]", console=self.console):
                stats = self.courtfinder_cli.get_stats()
                court_count = stats['storage_stats']['courts']['total_items']
                
            if court_count == 0:
                self.console.print("[yellow]No data found. Setting up sample data...[/yellow]")
                self._setup_sample_data()
            else:
                self.console.print(f"[green]✓ Found {court_count} courts in storage[/green]")
            
            # Step 2: Interactive Search Demo
            self.console.print("\n[bright_blue]🔍 Now let's search the data![/bright_blue]")
            self._demo_search()
            
        except Exception as e:
            self.console.print(f"[red]Error during quick start: {e}[/red]")
            self.console.print("[yellow]Try individual menu options for more control.[/yellow]")
    
    def _setup_sample_data(self):
        """Set up sample data for demonstration"""
        self.console.print("[bright_blue]Setting up sample data...[/bright_blue]")
        
        # If test data directory exists, try to use it
        if self.test_data_dir.exists():
            self.console.print("[green]✓ Using existing test data[/green]")
            return
        
        # Otherwise, create some sample data
        self.console.print("[yellow]Creating sample court data...[/yellow]")
        
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
        
        try:
            for court in sample_courts:
                self.courtfinder_cli.storage.save_court(court)
            self.console.print("[green]✓ Sample data created successfully[/green]")
        except Exception as e:
            self.console.print(f"[red]Error creating sample data: {e}[/red]")
    
    def _demo_search(self):
        """Demonstrate search capabilities"""
        self.console.print("\n[bright_magenta]Let's search for courts![/bright_magenta]")
        
        # Search for courts
        try:
            search_term = Prompt.ask("Enter search term (or press Enter for 'Supreme')", default="Supreme")
            
            with Status(f"[bright_blue]Searching for '{search_term}'...[/bright_blue]", console=self.console):
                results = self.courtfinder_cli.search_courts(search_term, limit=10)
            
            if results:
                self.console.print(f"\n[green]✓ Found {len(results)} courts:[/green]")
                
                table = Table(show_header=True, header_style="bold bright_blue")
                table.add_column("ID", width=6)
                table.add_column("Full Name", width=40)
                table.add_column("Jurisdiction", width=12)
                table.add_column("Citation", width=15)
                
                for court in results:
                    table.add_row(
                        str(court.id),
                        court.full_name,
                        court.jurisdiction,
                        court.citation_string
                    )
                
                self.console.print(table)
            else:
                self.console.print(f"[yellow]No courts found matching '{search_term}'[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]Search error: {e}[/red]")
    
    def download_data(self):
        """Download bulk data from CourtListener using working standalone script"""
        self.console.print(Panel(
            "[bright_blue bold]📥 Download Court Data[/bright_blue bold]\n" +
            "[dim]Downloads real FreeLaw bulk data from CourtListener with progress bars[/dim]",
            border_style="bright_blue"
        ))
        
        # Check if downloads directory already exists
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            bz2_files = list(downloads_dir.glob("*.bz2"))
            if bz2_files:
                total_size = sum(f.stat().st_size for f in bz2_files)
                self.console.print(f"[yellow]⚠️  Downloads directory already contains {len(bz2_files)} files ({total_size/1024/1024:.1f} MB)[/yellow]")
                self.console.print(f"[bright_green]✨ The new UI will show existing files and let you skip them[/bright_green]")
        
        # Show what will be downloaded
        self.console.print(f"\n[bright_yellow]Essential Files (~40GB compressed):[/bright_yellow]")
        self.console.print(f"[dim]courts, people, opinions, citations, dockets, opinion-clusters[/dim]")
        self.console.print(f"[bright_blue]🚀 Launching beautiful asciimatics download UI...[/bright_blue]")
        self.console.print(f"[bright_green]✨ Features: Real-time progress, smart file detection, keyboard shortcuts[/bright_green]")
        
        try:
            import subprocess
            import time
            
            self.console.print(f"\n[dim]Opening interactive progress window in 2 seconds...[/dim]")
            time.sleep(2)
            
            # Use the new improved download script with asciimatics UI
            cmd = [sys.executable, "download_with_progress_v2.py"]
            
            # Run the download script with progress UI (no capture_output so UI shows)
            result = subprocess.run(cmd, cwd=Path.cwd())
            
            if result.returncode == 0:
                self.console.print(f"[green]✓ Download completed successfully![/green]")
                
                # Show the output from the script
                if result.stdout:
                    self.console.print("\n[bright_white]Download summary:[/bright_white]")
                    # Show last few lines of output which contain the summary
                    lines = result.stdout.strip().split('\n')
                    for line in lines[-10:]:  # Show last 10 lines
                        if line.strip():
                            self.console.print(f"  {line}")
                
                # Check what was actually downloaded
                if downloads_dir.exists():
                    bz2_files = list(downloads_dir.glob("*.bz2"))
                    if bz2_files:
                        total_size = sum(f.stat().st_size for f in bz2_files)
                        self.console.print(f"\n[green]📁 Downloads directory now contains {len(bz2_files)} files ({total_size/1024/1024:.1f} MB)[/green]")
                        self.console.print(f"[bright_yellow]💡 Next step: Use 'Parse Downloaded Data' to process these files[/bright_yellow]")
            else:
                self.console.print(f"[red]❌ Download failed with exit code {result.returncode}[/red]")
                if result.stderr:
                    self.console.print(f"[red]Error: {result.stderr}[/red]")
                if result.stdout:
                    self.console.print(f"[dim]Output: {result.stdout}[/dim]")
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Download cancelled by user.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error running download script: {e}[/red]")
    
    def parse_data(self):
        """Parse downloaded bulk data with UI and flexible options"""
        self.console.print(Panel(
            "[bright_yellow bold]🔧 Parse Downloaded Data[/bright_yellow bold]\n" +
            "[dim]Interactive import with progress visualization and flexible data limits[/dim]",
            border_style="bright_yellow"
        ))
        
        # Check if downloads directory exists
        downloads_dir = Path("downloads")
        if not downloads_dir.exists():
            self.console.print("[red]❌ No downloads/ directory found. Please download data first.[/red]")
            return
        
        # Check for bz2 files (the real bulk data format)
        bz2_files = list(downloads_dir.glob("*.bz2"))
        if not bz2_files:
            self.console.print("[yellow]⚠️  No .bz2 files found in downloads/ directory.[/yellow]")
            self.console.print("[bright_blue]💡 Run 'Download Court Data' first to get the bulk data files.[/bright_blue]")
            return
        
        # Show available files
        self.console.print(f"[bright_blue]Found {len(bz2_files)} bulk data files:[/bright_blue]")
        
        table = Table(show_header=True, header_style="bold bright_blue")
        table.add_column("File", width=35)
        table.add_column("Size", width=12)
        table.add_column("Type", width=20)
        
        total_size = 0
        for file_path in bz2_files:
            stat = file_path.stat()
            size = stat.st_size
            total_size += size
            size_str = self._format_size(size)
            
            # Determine data type from filename
            if "courts" in file_path.name:
                data_type = "Court metadata"
            elif "dockets" in file_path.name:
                data_type = "Case dockets"
            elif "opinions" in file_path.name and "cluster" not in file_path.name:
                data_type = "Full opinion text"
            elif "opinion-clusters" in file_path.name:
                data_type = "Opinion metadata"
            elif "citations" in file_path.name:
                data_type = "Citation data"
            elif "people" in file_path.name:
                data_type = "Judge information"
            else:
                data_type = "Unknown"
            
            table.add_row(file_path.name, size_str, data_type)
        
        self.console.print(table)
        self.console.print(f"\n[bright_blue]Total data to process: {self._format_size(total_size)}[/bright_blue]")
        
        # Check if real_data already exists
        real_data_dir = Path("real_data")
        if real_data_dir.exists():
            self.console.print(f"[yellow]⚠️  real_data/ directory already exists[/yellow]")
            if not Confirm.ask("Do you want to continue (may overwrite existing data)?"):
                return
        
        # Ask user about import scope
        self.console.print(f"\n[bright_yellow]Import Options:[/bright_yellow]")
        
        import_choice = questionary.select(
            "Choose processing scope:",
            choices=[
                "Limited Processing - Fast sample (1000 courts, 5000 dockets, 2000 clusters, 1000 opinions) - Your original working approach",
                "Full Processing - Complete dataset (All records) - Expands to ~300GB, may take hours",
                "Cancel"
            ]
        ).ask()
        
        if not import_choice or import_choice == "Cancel":
            return
        
        use_full_processing = "Full Processing" in import_choice
        
        if use_full_processing:
            self.console.print(f"[bright_red]⚠️  WARNING: Full processing will expand to ~300GB![/bright_red]")
            self.console.print(f"[bright_red]   This processes ALL records and may take several hours[/bright_red]")
            if not Confirm.ask("Are you sure you want to proceed with full processing?"):
                return
            
            scope_text = "ALL records (expands to ~300GB)"
        else:
            scope_text = "limited samples (your original working approach)"
        
        self.console.print(f"\n[bright_yellow]This will:[/bright_yellow]")
        self.console.print(f"  • Process compressed .bz2 files with progress UI")
        self.console.print(f"  • Import court records into real_data/ directory")
        self.console.print(f"  • Create searchable database of courts, cases, and opinions")
        self.console.print(f"  • Process {scope_text}")
        
        if not Confirm.ask("Do you want to proceed with processing?"):
            return
        
        try:
            import subprocess
            
            self.console.print(f"\n[bright_blue]🚀 Starting import using import_ALL_freelaw_data_FIXED.py...[/bright_blue]")
            self.console.print(f"[dim]This may take several minutes depending on data size...[/dim]")
            
            # Run the complete import script with UI
            self.console.print("[bright_blue]Starting import with interactive progress display...[/bright_blue]")
            
            # Build command with appropriate flags
            cmd = [sys.executable, "import_ALL_freelaw_data_FIXED.py", "--ui"]
            if use_full_processing:
                cmd.append("--no-limits")
            
            result = subprocess.run(cmd, cwd=Path.cwd())
            
            if result.returncode == 0:
                self.console.print(f"\n[green]✓ Import completed successfully![/green]")
                
                # Check what was created
                if real_data_dir.exists():
                    self.console.print(f"[green]📁 real_data/ directory created with processed court data[/green]")
                    self.console.print(f"[bright_yellow]💡 Next step: Use 'Search Court Records' to explore the data[/bright_yellow]")
                    
                    # Force menu to reinitialize with real data
                    self.console.print(f"[dim]Restarting menu to use real data...[/dim]")
                    self.__init__()  # Reinitialize to pick up real_data
                    
            else:
                self.console.print(f"[red]❌ Import failed with exit code {result.returncode}[/red]")
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Import cancelled by user.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error running import script: {e}[/red]")
    
    def search_records(self):
        """Search court records with interactive interface"""
        self.console.print(Panel(
            "[bright_magenta bold]🔍 Search Court Records[/bright_magenta bold]",
            border_style="bright_magenta"
        ))
        
        search_types = [
            ("Courts", "Search by court name or jurisdiction"),
            ("Cases", "Search by case name"),
            ("Opinions", "Search opinion text content"),
            ("Judges", "Search by judge name"),
            ("Case Details", "Get complete case information"),
            ("Citation Network", "Explore citation relationships")
        ]
        
        self.console.print("[bright_white]Available search types:[/bright_white]")
        for i, (name, desc) in enumerate(search_types, 1):
            self.console.print(f"  {i}. [bright_blue]{name}[/bright_blue] - {desc}")
        
        try:
            choice = questionary.select(
                "Select search type:",
                choices=[f"{name} - {desc}" for name, desc in search_types]
            ).ask()
            
            if not choice:
                return
            
            search_type = choice.split(" - ")[0].lower()
            
            if search_type == "courts":
                self._search_courts()
            elif search_type == "cases":
                self._search_cases()
            elif search_type == "opinions":
                self._search_opinions()
            elif search_type == "judges":
                self._search_judges()
            elif search_type == "case details":
                self._search_case_details()
            elif search_type == "citation network":
                self._search_citation_network()
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Search cancelled by user.[/yellow]")
    
    def _search_courts(self):
        """Search courts interactively"""
        query = Prompt.ask("Enter court name or jurisdiction to search")
        if not query:
            return
        
        with Status(f"[bright_blue]Searching courts for '{query}'...[/bright_blue]", console=self.console):
            results = self.courtfinder_cli.search_courts(query, limit=20)
        
        if results:
            self.console.print(f"\n[green]✓ Found {len(results)} courts:[/green]")
            
            table = Table(show_header=True, header_style="bold bright_blue")
            table.add_column("ID", width=6)
            table.add_column("Full Name", width=35)
            table.add_column("Short Name", width=15)
            table.add_column("Jurisdiction", width=10)
            table.add_column("Citation", width=12)
            
            for court in results:
                table.add_row(
                    str(court.id),
                    court.full_name,
                    court.short_name,
                    court.jurisdiction,
                    court.citation_string
                )
            
            self.console.print(table)
        else:
            self.console.print(f"[yellow]No courts found matching '{query}'[/yellow]")
    
    def _search_cases(self):
        """Search cases interactively"""
        case_name = Prompt.ask("Enter case name to search")
        if not case_name:
            return
        
        court_id_str = Prompt.ask("Enter court ID (optional)", default="")
        court_id = court_id_str if court_id_str else None
        
        with Status(f"[bright_blue]Searching cases for '{case_name}'...[/bright_blue]", console=self.console):
            results = self.courtfinder_cli.search_cases(case_name, court_id, limit=20)
        
        if results:
            self.console.print(f"\n[green]✓ Found {len(results)} cases:[/green]")
            
            table = Table(show_header=True, header_style="bold bright_blue")
            table.add_column("ID", width=8)
            table.add_column("Case Name", width=35)
            table.add_column("Docket Number", width=20)
            table.add_column("Court ID", width=10)
            table.add_column("Date Filed", width=15)
            
            for docket in results:
                table.add_row(
                    str(docket.id),
                    docket.case_name,
                    docket.docket_number,
                    str(docket.court_id),
                    docket.date_filed.strftime("%Y-%m-%d") if docket.date_filed else "N/A"
                )
            
            self.console.print(table)
        else:
            self.console.print(f"[yellow]No cases found matching '{case_name}'[/yellow]")
    
    def _search_opinions(self):
        """Search opinions interactively"""
        text = Prompt.ask("Enter text to search in opinions")
        if not text:
            return
        
        with Status(f"[bright_blue]Searching opinions for '{text}'...[/bright_blue]", console=self.console):
            results = self.courtfinder_cli.search_opinions(text, limit=20)
        
        if results:
            self.console.print(f"\n[green]✓ Found {len(results)} opinions:[/green]")
            
            table = Table(show_header=True, header_style="bold bright_blue")
            table.add_column("ID", width=8)
            table.add_column("Type", width=15)
            table.add_column("Cluster ID", width=10)
            table.add_column("Has Text", width=10)
            table.add_column("Page Count", width=12)
            
            for opinion in results:
                table.add_row(
                    str(opinion.id),
                    opinion.type.value,
                    str(opinion.cluster_id),
                    "Yes" if opinion.has_text() else "No",
                    str(opinion.page_count) if opinion.page_count else "N/A"
                )
            
            self.console.print(table)
        else:
            self.console.print(f"[yellow]No opinions found containing '{text}'[/yellow]")
    
    def _search_judges(self):
        """Search judges interactively"""
        name = Prompt.ask("Enter judge name to search")
        if not name:
            return
        
        with Status(f"[bright_blue]Searching judges for '{name}'...[/bright_blue]", console=self.console):
            results = self.courtfinder_cli.search_judges(name, limit=20)
        
        if results:
            self.console.print(f"\n[green]✓ Found {len(results)} judges:[/green]")
            
            table = Table(show_header=True, header_style="bold bright_blue")
            table.add_column("ID", width=8)
            table.add_column("Full Name", width=30)
            table.add_column("Birth Date", width=15)
            table.add_column("Birth Place", width=20)
            table.add_column("Gender", width=10)
            
            for person in results:
                birth_date = person.date_dob.strftime("%Y-%m-%d") if person.date_dob else "N/A"
                birth_place = f"{person.dob_city}, {person.dob_state}" if person.dob_city and person.dob_state else "N/A"
                
                table.add_row(
                    str(person.id),
                    person.get_full_name(),
                    birth_date,
                    birth_place,
                    person.gender or "N/A"
                )
            
            self.console.print(table)
        else:
            self.console.print(f"[yellow]No judges found matching '{name}'[/yellow]")
    
    def _search_case_details(self):
        """Get complete case details"""
        docket_id_str = Prompt.ask("Enter docket ID")
        if not docket_id_str:
            return
        
        try:
            docket_id = int(docket_id_str)
        except ValueError:
            self.console.print("[red]Invalid docket ID. Please enter a number.[/red]")
            return
        
        with Status(f"[bright_blue]Getting case details for docket {docket_id}...[/bright_blue]", console=self.console):
            details = self.courtfinder_cli.get_case_details(docket_id)
        
        if details:
            self.console.print(f"\n[green]✓ Case details for docket {docket_id}:[/green]")
            
            # Display docket information
            docket = details['docket']
            self.console.print(f"\n[bright_white]Case:[/bright_white] {docket.case_name}")
            self.console.print(f"[bright_white]Docket Number:[/bright_white] {docket.docket_number}")
            self.console.print(f"[bright_white]Court ID:[/bright_white] {docket.court_id}")
            self.console.print(f"[bright_white]Date Filed:[/bright_white] {docket.date_filed or 'N/A'}")
            
            # Display clusters and opinions
            clusters = details['clusters']
            self.console.print(f"\n[bright_white]Opinion Clusters:[/bright_white] {len(clusters)}")
            
            for cluster_info in clusters:
                cluster = cluster_info['cluster']
                opinions = cluster_info['opinions']
                
                self.console.print(f"\n  [bright_blue]Cluster {cluster.id}:[/bright_blue]")
                self.console.print(f"    Judges: {cluster.judges or 'N/A'}")
                self.console.print(f"    Date Filed: {cluster.date_filed or 'N/A'}")
                self.console.print(f"    Opinions: {len(opinions)}")
                
                for opinion in opinions:
                    self.console.print(f"      • Opinion {opinion.id}: {opinion.type.value}")
        else:
            self.console.print(f"[yellow]No case details found for docket {docket_id}[/yellow]")
    
    def _search_citation_network(self):
        """Explore citation network"""
        opinion_id_str = Prompt.ask("Enter opinion ID")
        if not opinion_id_str:
            return
        
        try:
            opinion_id = int(opinion_id_str)
        except ValueError:
            self.console.print("[red]Invalid opinion ID. Please enter a number.[/red]")
            return
        
        depth_str = Prompt.ask("Enter search depth (1-3)", default="1")
        try:
            depth = int(depth_str)
            if depth < 1 or depth > 3:
                depth = 1
        except ValueError:
            depth = 1
        
        with Status(f"[bright_blue]Building citation network for opinion {opinion_id}...[/bright_blue]", console=self.console):
            network = self.courtfinder_cli.get_citation_network(opinion_id, depth)
        
        if network and (network['nodes'] or network['edges']):
            self.console.print(f"\n[green]✓ Citation network for opinion {opinion_id}:[/green]")
            self.console.print(f"[bright_white]Nodes:[/bright_white] {len(network['nodes'])}")
            self.console.print(f"[bright_white]Edges:[/bright_white] {len(network['edges'])}")
            
            # Display nodes
            if network['nodes']:
                self.console.print("\n[bright_blue]Connected Opinions:[/bright_blue]")
                for node in network['nodes'][:10]:  # Show first 10 nodes
                    opinion = node['opinion']
                    self.console.print(f"  • Opinion {opinion.id}: {opinion.type.value} (depth: {node['depth']})")
                
                if len(network['nodes']) > 10:
                    self.console.print(f"  ... and {len(network['nodes']) - 10} more opinions")
            
            # Display edges
            if network['edges']:
                self.console.print("\n[bright_blue]Citation Relationships:[/bright_blue]")
                for edge in network['edges'][:10]:  # Show first 10 edges
                    quoted_str = " (quoted)" if edge['quoted'] else ""
                    self.console.print(f"  • {edge['citing_id']} → {edge['cited_id']}{quoted_str}")
                
                if len(network['edges']) > 10:
                    self.console.print(f"  ... and {len(network['edges']) - 10} more citations")
        else:
            self.console.print(f"[yellow]No citation network found for opinion {opinion_id}[/yellow]")
    
    def view_data_status(self):
        """Display comprehensive data status and workflow guide"""
        self.console.print(Panel(
            "[bright_cyan bold]📊 Data Status & Next Steps[/bright_cyan bold]",
            border_style="bright_cyan"
        ))
        
        # Check all data states
        downloads_dir = Path("downloads")
        real_data_dir = Path("real_data")
        test_data_dir = Path("test_data")
        
        # Downloads status
        self.console.print("\n[bright_white]📥 Downloaded Data:[/bright_white]")
        if downloads_dir.exists():
            bz2_files = list(downloads_dir.glob("*.bz2"))
            if bz2_files:
                total_size = sum(f.stat().st_size for f in bz2_files)
                self.console.print(f"  ✅ {len(bz2_files)} files ({total_size/1024/1024:.1f}MB)")
                
                # Show breakdown
                for file_path in bz2_files:
                    size_str = self._format_size(file_path.stat().st_size)
                    self.console.print(f"     • {file_path.name} ({size_str})")
            else:
                self.console.print("  ❌ No .bz2 files found")
        else:
            self.console.print("  ❌ No downloads/ directory")
        
        # Parsed data status
        self.console.print("\n[bright_white]🔧 Parsed Data:[/bright_white]")
        if real_data_dir.exists() and self.using_real_data:
            try:
                stats = self.courtfinder_cli.get_stats()
                storage_stats = stats['storage_stats']
                self.console.print("  ✅ Real data available and ready to search")
                
                # Show record counts
                for data_type, type_stats in storage_stats.items():
                    if data_type != 'total_disk_usage' and type_stats['total_items'] > 0:
                        self.console.print(f"     • {data_type.replace('_', ' ').title()}: {type_stats['total_items']:,} records")
                        
                total_size = storage_stats['total_disk_usage']
                self.console.print(f"  💾 Total size: {self._format_size(total_size)}")
            except Exception as e:
                self.console.print(f"  ⚠️ Real data directory exists but error reading: {e}")
        elif test_data_dir.exists():
            self.console.print("  ⚠️ Using test data (sample records)")
        else:
            self.console.print("  ❌ No parsed data - need to run import")
        
        # Show workflow status
        self.console.print("\n[bright_white]🔄 Workflow Status:[/bright_white]")
        
        has_downloads = downloads_dir.exists() and len(list(downloads_dir.glob("*.bz2"))) > 0
        has_parsed = real_data_dir.exists() and self.using_real_data
        
        if not has_downloads and not has_parsed:
            self.console.print("  📍 Status: [bright_red]Getting Started[/bright_red]")
            self.console.print("  ⭐ Next: Download data or try Quick Start")
        elif has_downloads and not has_parsed:
            self.console.print("  📍 Status: [bright_yellow]Ready to Parse[/bright_yellow]")
            self.console.print("  ⭐ Next: Parse your downloaded data")
        elif has_parsed:
            self.console.print("  📍 Status: [bright_green]Ready to Search[/bright_green]")
            self.console.print("  ⭐ Next: Search your data or download more")
        
        # Available actions
        self.console.print(f"\n[bright_white]💡 Available Actions:[/bright_white]")
        if not has_downloads:
            self.console.print("  • Download real FreeLaw data (~5.5GB)")
            self.console.print("  • Try Quick Start for demo")
        if has_downloads and not has_parsed:
            self.console.print("  • Parse your downloads (with progress UI)")
        if has_downloads and has_parsed:
            self.console.print("  • Re-parse with different options")
        if has_parsed:
            self.console.print("  • Search courts, cases, opinions, judges")
        if has_downloads:
            self.console.print("  • Download additional data files")

    def view_statistics(self):
        """Display system statistics"""
        self.console.print(Panel(
            "[bright_cyan bold]📊 System Statistics[/bright_cyan bold]",
            border_style="bright_cyan"
        ))
        
        try:
            with Status("[bright_blue]Gathering statistics...[/bright_blue]", console=self.console):
                stats = self.courtfinder_cli.get_stats()
            
            # Storage statistics
            storage_stats = stats['storage_stats']
            
            self.console.print("\n[bright_white]Storage Statistics:[/bright_white]")
            
            table = Table(show_header=True, header_style="bold bright_blue")
            table.add_column("Data Type", width=20)
            table.add_column("Total Items", width=15)
            table.add_column("Disk Usage", width=15)
            table.add_column("Indexed Fields", width=15)
            
            for data_type, type_stats in storage_stats.items():
                if data_type != 'total_disk_usage':
                    table.add_row(
                        data_type.replace('_', ' ').title(),
                        str(type_stats['total_items']),
                        self._format_size(type_stats['disk_usage']),
                        str(len(type_stats['indexed_fields']))
                    )
            
            self.console.print(table)
            
            # Total disk usage
            total_size = storage_stats['total_disk_usage']
            self.console.print(f"\n[bright_white]Total Disk Usage:[/bright_white] {self._format_size(total_size)}")
            
            # Search statistics
            search_stats = stats['search_stats']
            self.console.print(f"\n[bright_white]Search Engine:[/bright_white]")
            self.console.print(f"  Supported Types: {', '.join(search_stats['supported_search_types'])}")
            self.console.print(f"  Available Operators: {len(search_stats['available_operators'])}")
            
            # Data directory info
            if hasattr(self, 'using_real_data') and self.using_real_data:
                data_dir = "real_data"
                data_type = "Real FreeLaw Bulk Data"
            elif self.using_test_data:
                data_dir = "test_data"
                data_type = "Test Data"
            else:
                data_dir = "data"
                data_type = "Default Data"
            self.console.print(f"\n[bright_white]Data Directory:[/bright_white] {data_dir}")
            self.console.print(f"[bright_white]Data Type:[/bright_white] {data_type}")
            
        except Exception as e:
            self.console.print(f"[red]Error gathering statistics: {e}[/red]")
    
    def show_help(self):
        """Show detailed help information"""
        self.console.print(Panel(
            "[bright_white bold]❓ CourtFinder CLI Help[/bright_white bold]",
            border_style="bright_white"
        ))
        
        help_sections = [
            {
                "title": "🚀 Quick Start",
                "content": [
                    "The fastest way to get started with CourtFinder.",
                    "• Sets up sample data if needed",
                    "• Demonstrates search capabilities",
                    "• Perfect for first-time users"
                ]
            },
            {
                "title": "📥 Download Court Data",
                "content": [
                    "Download bulk data from CourtListener.com",
                    "• Supports courts, dockets, opinions, etc.",
                    "• Automatically extracts compressed files",
                    "• Requires internet connection"
                ]
            },
            {
                "title": "🔧 Parse Downloaded Data",
                "content": [
                    "Interactive import with progress visualization",
                    "• Choose: Sample data (fast) or Full import (complete)",
                    "• Rich UI with progress bars and error tracking", 
                    "• Real-time speed monitoring and ETA",
                    "• No command-line parameters to remember"
                ]
            },
            {
                "title": "🔍 Search Court Records",
                "content": [
                    "Search across all imported data",
                    "• Courts: Search by name or jurisdiction",
                    "• Cases: Search by case name",
                    "• Opinions: Full-text search",
                    "• Judges: Search by name",
                    "• Case Details: Complete case information",
                    "• Citation Network: Explore relationships"
                ]
            },
            {
                "title": "📊 Statistics",
                "content": [
                    "View system and storage statistics",
                    "• Storage usage by data type",
                    "• Record counts",
                    "• Index information"
                ]
            }
        ]
        
        for section in help_sections:
            self.console.print(f"\n[bright_blue]{section['title']}[/bright_blue]")
            for line in section['content']:
                self.console.print(f"  {line}")
        
        self.console.print(f"\n[bright_white]Data Source:[/bright_white] {'Test Data' if self.using_test_data else 'Full Data'}")
        self.console.print(f"[bright_white]Version:[/bright_white] CourtFinder CLI 1.0")
        self.console.print(f"[bright_white]Repository:[/bright_white] https://github.com/courtfinder")
        
        self.console.print(f"\n[bright_green]💡 Tip: menu.py is the user-friendly entry point - no command-line parameters needed![/bright_green]")
        self.console.print(f"[dim]   Just run 'python menu.py' and choose your options interactively[/dim]")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes as human-readable size"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {units[i]}"
    
    def run(self):
        """Main menu loop"""
        try:
            while True:
                self.console.clear()
                self.show_banner()
                self.show_menu()
                
                # Build dynamic choices based on menu items
                menu_items = self._build_menu_items()
                choices = []
                for num, emoji, title, desc, color in menu_items:
                    choices.append(f"{num}. {emoji} {title}")
                
                choice = questionary.select(
                    "Select an option:",
                    choices=choices
                ).ask()
                
                # Extract the number from the choice
                choice = choice.split(".")[0] if choice else "7"
                
                self.console.print()
                
                if choice == "1":
                    self.view_data_status()
                elif choice == "2":
                    self.download_data()
                elif choice == "3":
                    self.parse_data()
                elif choice == "4":
                    self.search_records()
                elif choice == "5":
                    self.quick_start()
                elif choice == "6":
                    self.show_help()
                elif choice == "7":
                    self.console.print("[bright_green]Thank you for using CourtFinder CLI! 👋[/bright_green]")
                    break
                
                if choice != "7":
                    self.console.print("\n" + "─" * 80)
                    Prompt.ask("Press Enter to continue", show_default=False)
                    
        except KeyboardInterrupt:
            self.console.print("\n[bright_yellow]Goodbye! 👋[/bright_yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Unexpected error: {e}[/red]")
            self.console.print("[yellow]Please report this issue on GitHub.[/yellow]")


def main():
    """Main entry point"""
    menu = CourtFinderMenu()
    menu.run()


if __name__ == "__main__":
    main()