"""
CourtListener Domain Models

Based on real CourtListener data structures from API documentation:
https://www.courtlistener.com/help/api/
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum


class PrecedentialStatus(Enum):
    """Precedential status values from CourtListener"""
    PUBLISHED = "Published"
    UNPUBLISHED = "Unpublished"
    ERRATA = "Errata"
    SEPARATE = "Separate"
    IN_CHAMBERS = "In-chambers"
    RELATING_TO = "Relating-to"
    UNKNOWN = "Unknown"


class OpinionType(Enum):
    """Opinion type values from CourtListener"""
    COMBINED = "010combined"
    UNANIMOUS = "015unamimous"
    LEAD = "020lead"
    PLURALITY = "025plurality"
    CONCURRENCE = "030concurrence"
    CONCUR_IN_PART = "035concurrenceinpart"
    DISSENT = "040dissent"
    ADDENDUM = "050addendum"
    REMITTUR = "060remittitur"
    REHEARING = "070rehearing"
    ON_THE_MERITS = "080onthemerits"
    ON_MOTION_TO_STRIKE = "090onmotiontostrike"
    TRIAL_COURT = "100trialcourt"
    UNKNOWN = "999unknown"


@dataclass
class Court:
    """
    Court model based on CourtListener Courts CSV structure
    """
    id: str
    full_name: str
    short_name: str
    jurisdiction: str
    position: float
    citation_string: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate court data"""
        if not self.id:
            raise ValueError("Court ID is required")
        if not self.full_name:
            raise ValueError("Court full name is required")
        if not self.jurisdiction:
            raise ValueError("Court jurisdiction is required")
    
    def is_active(self) -> bool:
        """Check if court is currently active"""
        if self.end_date is None:
            return True
        return self.end_date > date.today()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'short_name': self.short_name,
            'jurisdiction': self.jurisdiction,
            'position': self.position,
            'citation_string': self.citation_string,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Court':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            full_name=data['full_name'],
            short_name=data['short_name'],
            jurisdiction=data['jurisdiction'],
            position=data['position'],
            citation_string=data['citation_string'],
            start_date=date.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None,
            notes=data.get('notes')
        )


@dataclass
class Docket:
    """
    Docket model based on CourtListener Dockets CSV structure
    """
    id: int
    court_id: str
    case_name: str
    docket_number: str
    date_created: datetime
    date_modified: datetime
    source: str
    appeal_from_id: Optional[str] = None
    case_name_short: Optional[str] = None
    case_name_full: Optional[str] = None
    slug: Optional[str] = None
    date_filed: Optional[date] = None
    date_terminated: Optional[date] = None
    date_last_filing: Optional[date] = None
    appeal_from_str: Optional[str] = None
    assigned_to_str: Optional[str] = None
    referred_to_str: Optional[str] = None
    panel_str: Optional[str] = None
    date_last_index: Optional[datetime] = None
    date_cert_granted: Optional[date] = None
    date_cert_denied: Optional[date] = None
    date_argued: Optional[date] = None
    date_reargued: Optional[date] = None
    date_reargument_denied: Optional[date] = None
    docket_number_core: Optional[str] = None
    cause: Optional[str] = None
    nature_of_suit: Optional[str] = None
    jury_demand: Optional[str] = None
    jurisdiction_type: Optional[str] = None
    federal_dn_case_type: Optional[str] = None
    federal_dn_office_code: Optional[str] = None
    federal_defendant_number: Optional[str] = None
    
    def __post_init__(self):
        """Validate docket data"""
        if not self.id:
            raise ValueError("Docket ID is required")
        if not self.court_id:
            raise ValueError("Court ID is required")
        if not self.case_name:
            raise ValueError("Case name is required")
        if not self.docket_number:
            raise ValueError("Docket number is required")
    
    def is_active(self) -> bool:
        """Check if docket represents an active case"""
        return self.date_terminated is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'court_id': self.court_id,
            'case_name': self.case_name,
            'docket_number': self.docket_number,
            'date_created': self.date_created.isoformat(),
            'date_modified': self.date_modified.isoformat(),
            'source': self.source,
            'appeal_from_id': self.appeal_from_id,
            'case_name_short': self.case_name_short,
            'case_name_full': self.case_name_full,
            'slug': self.slug,
            'date_filed': self.date_filed.isoformat() if self.date_filed else None,
            'date_terminated': self.date_terminated.isoformat() if self.date_terminated else None,
            'date_last_filing': self.date_last_filing.isoformat() if self.date_last_filing else None,
            'appeal_from_str': self.appeal_from_str,
            'assigned_to_str': self.assigned_to_str,
            'referred_to_str': self.referred_to_str,
            'panel_str': self.panel_str,
            'date_last_index': self.date_last_index.isoformat() if self.date_last_index else None,
            'date_cert_granted': self.date_cert_granted.isoformat() if self.date_cert_granted else None,
            'date_cert_denied': self.date_cert_denied.isoformat() if self.date_cert_denied else None,
            'date_argued': self.date_argued.isoformat() if self.date_argued else None,
            'date_reargued': self.date_reargued.isoformat() if self.date_reargued else None,
            'date_reargument_denied': self.date_reargument_denied.isoformat() if self.date_reargument_denied else None,
            'docket_number_core': self.docket_number_core,
            'cause': self.cause,
            'nature_of_suit': self.nature_of_suit,
            'jury_demand': self.jury_demand,
            'jurisdiction_type': self.jurisdiction_type,
            'federal_dn_case_type': self.federal_dn_case_type,
            'federal_dn_office_code': self.federal_dn_office_code,
            'federal_defendant_number': self.federal_defendant_number
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Docket':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            court_id=data['court_id'],
            case_name=data['case_name'],
            docket_number=data['docket_number'],
            date_created=datetime.fromisoformat(data['date_created']),
            date_modified=datetime.fromisoformat(data['date_modified']),
            source=data['source'],
            appeal_from_id=data.get('appeal_from_id'),
            case_name_short=data.get('case_name_short'),
            case_name_full=data.get('case_name_full'),
            slug=data.get('slug'),
            date_filed=date.fromisoformat(data['date_filed']) if data.get('date_filed') else None,
            date_terminated=date.fromisoformat(data['date_terminated']) if data.get('date_terminated') else None,
            date_last_filing=date.fromisoformat(data['date_last_filing']) if data.get('date_last_filing') else None,
            appeal_from_str=data.get('appeal_from_str'),
            assigned_to_str=data.get('assigned_to_str'),
            referred_to_str=data.get('referred_to_str'),
            panel_str=data.get('panel_str'),
            date_last_index=datetime.fromisoformat(data['date_last_index']) if data.get('date_last_index') else None,
            date_cert_granted=date.fromisoformat(data['date_cert_granted']) if data.get('date_cert_granted') else None,
            date_cert_denied=date.fromisoformat(data['date_cert_denied']) if data.get('date_cert_denied') else None,
            date_argued=date.fromisoformat(data['date_argued']) if data.get('date_argued') else None,
            date_reargued=date.fromisoformat(data['date_reargued']) if data.get('date_reargued') else None,
            date_reargument_denied=date.fromisoformat(data['date_reargument_denied']) if data.get('date_reargument_denied') else None,
            docket_number_core=data.get('docket_number_core'),
            cause=data.get('cause'),
            nature_of_suit=data.get('nature_of_suit'),
            jury_demand=data.get('jury_demand'),
            jurisdiction_type=data.get('jurisdiction_type'),
            federal_dn_case_type=data.get('federal_dn_case_type'),
            federal_dn_office_code=data.get('federal_dn_office_code'),
            federal_defendant_number=data.get('federal_defendant_number')
        )


@dataclass
class OpinionCluster:
    """
    Opinion Cluster model based on CourtListener Opinion Clusters CSV structure
    """
    id: int
    docket_id: int
    date_created: datetime
    date_modified: datetime
    judges: Optional[str] = None
    date_filed: Optional[date] = None
    date_filed_is_approximate: bool = False
    slug: Optional[str] = None
    case_name: Optional[str] = None
    case_name_short: Optional[str] = None
    case_name_full: Optional[str] = None
    scdb_id: Optional[str] = None
    scdb_decision_direction: Optional[str] = None
    scdb_votes_majority: Optional[int] = None
    scdb_votes_minority: Optional[int] = None
    source: Optional[str] = None
    procedural_history: Optional[str] = None
    attorneys: Optional[str] = None
    nature_of_suit: Optional[str] = None
    posture: Optional[str] = None
    syllabus: Optional[str] = None
    headnotes: Optional[str] = None
    summary: Optional[str] = None
    disposition: Optional[str] = None
    history: Optional[str] = None
    other_dates: Optional[str] = None
    cross_reference: Optional[str] = None
    correction: Optional[str] = None
    citation_count: int = 0
    precedential_status: Optional[PrecedentialStatus] = None
    date_blocked: Optional[date] = None
    blocked: bool = False
    sub_opinions: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate opinion cluster data"""
        if not self.id:
            raise ValueError("Opinion Cluster ID is required")
        if not self.docket_id:
            raise ValueError("Docket ID is required")
    
    def is_published(self) -> bool:
        """Check if opinion cluster is published"""
        return self.precedential_status == PrecedentialStatus.PUBLISHED
    
    def is_blocked(self) -> bool:
        """Check if opinion cluster is blocked"""
        return self.blocked
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'docket_id': self.docket_id,
            'date_created': self.date_created.isoformat(),
            'date_modified': self.date_modified.isoformat(),
            'judges': self.judges,
            'date_filed': self.date_filed.isoformat() if self.date_filed else None,
            'date_filed_is_approximate': self.date_filed_is_approximate,
            'slug': self.slug,
            'case_name': self.case_name,
            'case_name_short': self.case_name_short,
            'case_name_full': self.case_name_full,
            'scdb_id': self.scdb_id,
            'scdb_decision_direction': self.scdb_decision_direction,
            'scdb_votes_majority': self.scdb_votes_majority,
            'scdb_votes_minority': self.scdb_votes_minority,
            'source': self.source,
            'procedural_history': self.procedural_history,
            'attorneys': self.attorneys,
            'nature_of_suit': self.nature_of_suit,
            'posture': self.posture,
            'syllabus': self.syllabus,
            'headnotes': self.headnotes,
            'summary': self.summary,
            'disposition': self.disposition,
            'history': self.history,
            'other_dates': self.other_dates,
            'cross_reference': self.cross_reference,
            'correction': self.correction,
            'citation_count': self.citation_count,
            'precedential_status': self.precedential_status.value if self.precedential_status else None,
            'date_blocked': self.date_blocked.isoformat() if self.date_blocked else None,
            'blocked': self.blocked,
            'sub_opinions': self.sub_opinions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpinionCluster':
        """Create from dictionary"""
        precedential_status = None
        if data.get('precedential_status'):
            precedential_status = PrecedentialStatus(data['precedential_status'])
        
        return cls(
            id=data['id'],
            docket_id=data['docket_id'],
            date_created=datetime.fromisoformat(data['date_created']),
            date_modified=datetime.fromisoformat(data['date_modified']),
            judges=data.get('judges'),
            date_filed=date.fromisoformat(data['date_filed']) if data.get('date_filed') else None,
            date_filed_is_approximate=data.get('date_filed_is_approximate', False),
            slug=data.get('slug'),
            case_name=data.get('case_name'),
            case_name_short=data.get('case_name_short'),
            case_name_full=data.get('case_name_full'),
            scdb_id=data.get('scdb_id'),
            scdb_decision_direction=data.get('scdb_decision_direction'),
            scdb_votes_majority=data.get('scdb_votes_majority'),
            scdb_votes_minority=data.get('scdb_votes_minority'),
            source=data.get('source'),
            procedural_history=data.get('procedural_history'),
            attorneys=data.get('attorneys'),
            nature_of_suit=data.get('nature_of_suit'),
            posture=data.get('posture'),
            syllabus=data.get('syllabus'),
            headnotes=data.get('headnotes'),
            summary=data.get('summary'),
            disposition=data.get('disposition'),
            history=data.get('history'),
            other_dates=data.get('other_dates'),
            cross_reference=data.get('cross_reference'),
            correction=data.get('correction'),
            citation_count=data.get('citation_count', 0),
            precedential_status=precedential_status,
            date_blocked=date.fromisoformat(data['date_blocked']) if data.get('date_blocked') else None,
            blocked=data.get('blocked', False),
            sub_opinions=data.get('sub_opinions', [])
        )


@dataclass
class Opinion:
    """
    Opinion model based on CourtListener Opinions CSV structure
    """
    id: int
    cluster_id: int
    date_created: datetime
    date_modified: datetime
    type: OpinionType
    sha1: Optional[str] = None
    page_count: Optional[int] = None
    download_url: Optional[str] = None
    local_path: Optional[str] = None
    plain_text: Optional[str] = None
    html: Optional[str] = None
    html_lawbox: Optional[str] = None
    html_columbia: Optional[str] = None
    html_anon_2020: Optional[str] = None
    xml_harvard: Optional[str] = None
    html_with_citations: Optional[str] = None
    extracted_by_ocr: bool = False
    author_id: Optional[int] = None
    per_curiam: bool = False
    joined_by: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate opinion data"""
        if not self.id:
            raise ValueError("Opinion ID is required")
        if not self.cluster_id:
            raise ValueError("Cluster ID is required")
        if not self.type:
            raise ValueError("Opinion type is required")
    
    def has_text(self) -> bool:
        """Check if opinion has text content"""
        return bool(self.plain_text or self.html)
    
    def get_text_content(self) -> Optional[str]:
        """Get text content, preferring plain text over HTML"""
        return self.plain_text or self.html
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'cluster_id': self.cluster_id,
            'date_created': self.date_created.isoformat(),
            'date_modified': self.date_modified.isoformat(),
            'type': self.type.value,
            'sha1': self.sha1,
            'page_count': self.page_count,
            'download_url': self.download_url,
            'local_path': self.local_path,
            'plain_text': self.plain_text,
            'html': self.html,
            'html_lawbox': self.html_lawbox,
            'html_columbia': self.html_columbia,
            'html_anon_2020': self.html_anon_2020,
            'xml_harvard': self.xml_harvard,
            'html_with_citations': self.html_with_citations,
            'extracted_by_ocr': self.extracted_by_ocr,
            'author_id': self.author_id,
            'per_curiam': self.per_curiam,
            'joined_by': self.joined_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Opinion':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            cluster_id=data['cluster_id'],
            date_created=datetime.fromisoformat(data['date_created']),
            date_modified=datetime.fromisoformat(data['date_modified']),
            type=OpinionType(data['type']),
            sha1=data.get('sha1'),
            page_count=data.get('page_count'),
            download_url=data.get('download_url'),
            local_path=data.get('local_path'),
            plain_text=data.get('plain_text'),
            html=data.get('html'),
            html_lawbox=data.get('html_lawbox'),
            html_columbia=data.get('html_columbia'),
            html_anon_2020=data.get('html_anon_2020'),
            xml_harvard=data.get('xml_harvard'),
            html_with_citations=data.get('html_with_citations'),
            extracted_by_ocr=data.get('extracted_by_ocr', False),
            author_id=data.get('author_id'),
            per_curiam=data.get('per_curiam', False),
            joined_by=data.get('joined_by', [])
        )


@dataclass
class Citation:
    """
    Citation model based on CourtListener Citation Map CSV structure
    """
    cited_opinion_id: int
    citing_opinion_id: int
    depth: int
    quoted: bool = False
    parenthetical_id: Optional[int] = None
    parenthetical_text: Optional[str] = None
    
    def __post_init__(self):
        """Validate citation data"""
        if not self.cited_opinion_id:
            raise ValueError("Cited opinion ID is required")
        if not self.citing_opinion_id:
            raise ValueError("Citing opinion ID is required")
        if self.depth < 0:
            raise ValueError("Citation depth must be non-negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'cited_opinion_id': self.cited_opinion_id,
            'citing_opinion_id': self.citing_opinion_id,
            'depth': self.depth,
            'quoted': self.quoted,
            'parenthetical_id': self.parenthetical_id,
            'parenthetical_text': self.parenthetical_text
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Citation':
        """Create from dictionary"""
        return cls(
            cited_opinion_id=data['cited_opinion_id'],
            citing_opinion_id=data['citing_opinion_id'],
            depth=data['depth'],
            quoted=data.get('quoted', False),
            parenthetical_id=data.get('parenthetical_id'),
            parenthetical_text=data.get('parenthetical_text')
        )


@dataclass
class Person:
    """
    Person model based on CourtListener People CSV structure
    """
    id: int
    date_created: datetime
    date_modified: datetime
    name_first: Optional[str] = None
    name_middle: Optional[str] = None
    name_last: Optional[str] = None
    name_suffix: Optional[str] = None
    date_dob: Optional[date] = None
    date_granularity_dob: Optional[str] = None
    date_dod: Optional[date] = None
    date_granularity_dod: Optional[str] = None
    dob_city: Optional[str] = None
    dob_state: Optional[str] = None
    dod_city: Optional[str] = None
    dod_state: Optional[str] = None
    gender: Optional[str] = None
    religion: Optional[str] = None
    ftm_total_received: Optional[float] = None
    ftm_eid: Optional[str] = None
    has_photo: bool = False
    is_alias_of: Optional[int] = None
    
    def __post_init__(self):
        """Validate person data"""
        if not self.id:
            raise ValueError("Person ID is required")
    
    def get_full_name(self) -> str:
        """Get full name combining all name parts"""
        name_parts = []
        if self.name_first:
            name_parts.append(self.name_first)
        if self.name_middle:
            name_parts.append(self.name_middle)
        if self.name_last:
            name_parts.append(self.name_last)
        if self.name_suffix:
            name_parts.append(self.name_suffix)
        return ' '.join(name_parts)
    
    def is_deceased(self) -> bool:
        """Check if person is deceased"""
        return self.date_dod is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'date_created': self.date_created.isoformat(),
            'date_modified': self.date_modified.isoformat(),
            'name_first': self.name_first,
            'name_middle': self.name_middle,
            'name_last': self.name_last,
            'name_suffix': self.name_suffix,
            'date_dob': self.date_dob.isoformat() if self.date_dob else None,
            'date_granularity_dob': self.date_granularity_dob,
            'date_dod': self.date_dod.isoformat() if self.date_dod else None,
            'date_granularity_dod': self.date_granularity_dod,
            'dob_city': self.dob_city,
            'dob_state': self.dob_state,
            'dod_city': self.dod_city,
            'dod_state': self.dod_state,
            'gender': self.gender,
            'religion': self.religion,
            'ftm_total_received': self.ftm_total_received,
            'ftm_eid': self.ftm_eid,
            'has_photo': self.has_photo,
            'is_alias_of': self.is_alias_of
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Person':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            date_created=datetime.fromisoformat(data['date_created']),
            date_modified=datetime.fromisoformat(data['date_modified']),
            name_first=data.get('name_first'),
            name_middle=data.get('name_middle'),
            name_last=data.get('name_last'),
            name_suffix=data.get('name_suffix'),
            date_dob=date.fromisoformat(data['date_dob']) if data.get('date_dob') else None,
            date_granularity_dob=data.get('date_granularity_dob'),
            date_dod=date.fromisoformat(data['date_dod']) if data.get('date_dod') else None,
            date_granularity_dod=data.get('date_granularity_dod'),
            dob_city=data.get('dob_city'),
            dob_state=data.get('dob_state'),
            dod_city=data.get('dod_city'),
            dod_state=data.get('dod_state'),
            gender=data.get('gender'),
            religion=data.get('religion'),
            ftm_total_received=data.get('ftm_total_received'),
            ftm_eid=data.get('ftm_eid'),
            has_photo=data.get('has_photo', False),
            is_alias_of=data.get('is_alias_of')
        )