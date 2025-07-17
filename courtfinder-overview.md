# CourtListener.com (FLP) – Product & Data Overview  
*Version: 14 May 2025*
- Courtlistener.com is a website that is ran by the freelaw project, and the freelaw project has free bulk data of all 900K court cases.  You will need this map of how the entities fit together, and what github projects they have to help us utilize that data.

## Overall resources
### Getting Started with FLP
- **FLP GitHub**  
- **FLP GitHub Search**  
- **FLP Volunteer backlog**  
- **FLP Developer Guide**

### Data and APIs
- **Complete Schema**
- **Bulk Data**
- **APIs**
  - Search API
  - Webhook API
- **Replication**
- **How to load bulk data**

---

## Databases & Collections

### 1. Case Law
- **WHAT:** A collection of legal decisions (opinions) judges write to interpret the law.  
- **HOW:** Contributed.

#### Case Law Database Structure
- Courts  
- Dockets  
- Clusters  
- Opinions  
- Judges  
- Citations  

**Courts** – data about courts; every docket belongs to one court.  
**Dockets** – case metadata (initiation date, docket #); each cluster belongs to a docket.  
**Clusters** – group opinions from the same panel (e.g., majority, dissent); cluster_id is the unique identifier shown in search results.  
**Opinions** – text of each decision and author metadata; links to citations and judges.

---

### 2. Parenthetical
- **WHAT:** Short summary (written by the judge) explaining why an opinion cited another opinion.  
- **HOW:** Extracted/scraped from cases.

#### Parenthetical Database Structure
- Parentheticals (available only as bulk data)

---

### 3. Citation
- **WHAT:** Table of Authorities for each opinion (both cited and citing opinions).  
- **HOW:** Extracted with **eyecite** and/or contributed datasets.

#### Citation Database Structure
- Courts  
- Dockets  
- Clusters  
- Citations  

**Citations** – linked with Reporters‑DB; power the citation graph and lookup/verification.

---

### 4. RECAP Archive
- **WHAT:** PACER (U.S. federal court) docket entries & documents.  
- **HOW:** Scraped via **juriscraper** and/or uploaded by users through the RECAP Suite.

#### RECAP Database Structure
- Courts  
- Dockets  
- Docket Entries  
- Documents  
- Roles  
- Parties  
- Judges  
- Attorneys  
- Originating Court  
- Integrated Database  

Key entities:  
- **Docket Entries** – one row per upload, linking to one or more documents.  
- **Documents** – may include case‑law opinions.  
- **Parties** and **Attorneys** – rich metadata; parties link to judges/attorneys.  
- **Originating Court** – maps appellate dockets back to lower courts.  
- **Integrated Database** – Federal Judicial Center data regularly merged in.

---

### 5. Oral Arguments
- **WHAT:** Audio files (plus generated transcripts) of U.S. Supreme Court & Circuit oral arguments.  
- **HOW:** Scraped from court websites.

#### Oral Arguments Database Structure
- Courts  
- Dockets  
- Oral Argument Audios  
- Judges  

---

### 6. Judges
- **WHAT:** Growing collection of state & federal judges.  
- **HOW:** Curated from books, court sites, commercial data, FOIA requests, and disclosure forms.

#### Persons Database Structure
- Person  
- Judges  

**Person** – umbrella record for judges, appointers (e.g., presidents), attorneys, etc.  
**Judges** – bio, positions, ABA rating, party, race, appointments, portraits, etc.

---

### 7. Financial Disclosures
- **WHAT:** Judges’ financial disclosures (investments & potential conflicts).  
- **HOW:** Requested from the Financial Disclosures Office, Senate records, and partner orgs.

#### Financial Disclosures Database Structure
- Person  
- Judges  
- Financial Disclosures  

---

### 8. Reporters
- **WHAT:** Collection of reporters, journals, and abbreviations.  
- **HOW:** Extracted/scraped from cases.

#### Reporters‑DB Structure
- JSON files with structured information about almost every American legal reporter.

---

## Tooling & Services

### Core Python / Data Tools
- **Juriscraper** – gathers & parses opinions, PACER content, and oral arguments.  
- **X‑Ray** – finds bad redactions in PDFs (rectangle‑on‑text type, continuously improved).  
- **Eyecite** – extracts legal citations via Reporters‑DB patterns.  
- **Doctor** – Django microservice for converting, extracting, and modifying documents/audio.

### The RECAP Suite
| Component | Purpose |
|-----------|---------|
| **RECAP Extension** | Browser add‑on: fetches free copies if already in the archive and uploads newly purchased PACER docs. |
| **Fetch API** | Free API: uses user PACER creds to purchase & archive documents automatically. |
| **RECAP.email** | Watches PACER notification emails and auto‑uploads attachments. |

### Bots.law
- **Big Cases Bot** – social posts for high‑profile case updates.  
- **Little Cases Bots** – topical bots maintained by community experts.

### Alerts (CourtListener.com feature)
1. **Docket Alerts for PACER** – follow federal cases & bankruptcies.  
2. **Search Alerts** – updates on keyword/topic search results.  
3. **Citation Alerts** – notifications when a case is cited.



## Overall resources / links / githubs

### Getting Started with FLP
- **[FLP GitHub](https://github.com/freelawproject)**
- **[FLP GitHub Search](https://github.com/search?q=org%3Afreelawproject+test&type=issues)**
- **[FLP Volunteer Backlog](https://github.com/orgs/freelawproject/projects/31/views/1)**
- **[FLP Developer Guide](https://github.com/freelawproject/courtlistener/wiki/Getting-Started-Developing-CourtListener#how-settings-work-in-courtlistener)** 

### Data & APIs
- **Complete Schema** – ![ER diagram](https://storage.courtlistener.com/static/png/complete-model-v3.13.4c12f7e373d3.png)
- **[Bulk Data](https://www.courtlistener.com/help/api/bulk-data/)**
- **[APIs overview](https://www.courtlistener.com/help/api/rest/)**
  - **[Search API](https://www.courtlistener.com/help/api/rest/search/)**
  - **[Webhook API](https://www.courtlistener.com/help/api/webhooks/)**
  - **[Replication](https://www.courtlistener.com/help/api/replication/)**
- **[How to load bulk data](https://github.com/freelawproject/courtlistener/discussions/3173)**

---

## Databases & Collections

### 1 · Case Law
- **WHAT:** Legal decisions (opinions) judges write to interpret the law.  
- **HOW:** Contributed by courts/users.  
- **Browse opinions:** <https://www.courtlistener.com/opinion/>  
- **REST endpoint:** <https://www.courtlistener.com/help/api/rest/case-law/>  
- **Example clusters:** <https://www.courtlistener.com/c/>  

#### Structure
Courts → Dockets → Clusters → Opinions → Judges → Citations

### 2 · Parenthetical
- **WHAT:** Judge‑written snippets explaining why an opinion cites another.  
- **Link:** <https://www.courtlistener.com/parenthetical/>  
- **Blog post:** “Summarizing Important Cases” – <https://free.law/2022/03/17/summarizing-important-cases>

### 3 · Citation
- **WHAT:** Table‑of‑Authorities for every opinion (cited + citing).  
- **REST endpoints:**  
  - <https://www.courtlistener.com/help/api/rest/citations/>  
  - <https://www.courtlistener.com/help/api/rest/citation-lookup/>  
- **Visualization:** SCOTUS Mapper – <https://www.courtlistener.com/visualizations/scotus-mapper/>

### 4 · RECAP Archive
- **WHAT:** Federal (PACER) dockets & documents.  
- **Landing page:** <https://www.courtlistener.com/recap/>  
- **REST endpoints:**  
  - <https://www.courtlistener.com/help/api/rest/recap/>  
  - <https://www.courtlistener.com/help/api/rest/recap/#pacer-fetch>  
  - <https://www.courtlistener.com/help/api/rest/pacer/>  
- **External data:** FJC Integrated Database – <https://www.fjc.gov/research/idb>  
- **Bulk overview:** <https://free.law/recap>

#### Structure
Courts → Dockets → Docket Entries → Documents / Parties / Attorneys / Judges …  

### 5 · Oral Arguments
- **WHAT:** Audio (plus transcripts) from SCOTUS & Circuit Courts.  
- **Browse audio:** <https://www.courtlistener.com/audio/>  
- **REST endpoint:** <https://www.courtlistener.com/help/api/rest/oral-arguments/>

### 6 · Judges
- **WHAT:** Biographical data for state & federal judges.  
- **Directory:** <https://www.courtlistener.com/person/>  
- **Portrait micro‑service:** <https://free.law/projects/judge-pics>  
- **REST endpoint:** <https://www.courtlistener.com/help/api/rest/judges/>

### 7 · Financial Disclosures
- **WHAT:** Judges’ annual financial statements.  
- **Browse filings:** <https://www.courtlistener.com/financial-disclosures/>  
- **REST endpoint:** <https://www.courtlistener.com/help/api/rest/financial-disclosures/>

### 8 · Reporters
- **WHAT:** Reporter & abbreviation metadata.  
- **Repo:** <https://github.com/freelawproject/reporters-db/>

---

## Tooling & Services

| Tool / Service | Purpose / Link |
|----------------|----------------|
| **[Juriscraper](https://free.law/projects/juriscraper)** | Python library that gathers opinions, PACER dockets, and oral‑argument audio. |
| **RECAP Suite** | <https://free.law/recap> (overview); **Fetch API** docs at <https://www.courtlistener.com/help/api/rest/recap/#pacer-fetch>; **RECAP.email** setup at <https://www.courtlistener.com/help/recap/email/> |
| **Bots.law** | Main site: <https://bots.law/> — includes **Big Cases Bot** (<https://bots.law/big-cases/about/>) and **Little Cases Bots** (<https://bots.law/little-cases/>) |
| **[X‑Ray](https://free.law/projects/x-ray)** | Finds bad PDF redactions. |
| **[Eyecite](https://free.law/projects/eyecite)** | Extracts legal citations. |
| **[Doctor](https://free.law/projects/doctor)** | Document + audio conversion micro‑service. |
| **[Alerts](https://www.courtlistener.com/help/alerts/)** | Search, docket, and citation alerts on CourtListener.com. |

---

## Reference links (one‑per‑line for easy copy)
<https://free.law/>  
<http://courtlistener.com>  
<https://github.com/freelawproject>  
<https://github.com/search?q=org%3Afreelawproject+test&type=issues>  
<https://github.com/orgs/freelawproject/projects/31/views/1>  
<https://storage.courtlistener.com/static/png/complete-model-v3.13.4c12f7e373d3.png>  
<https://github.com/freelawproject/courtlistener/wiki/Getting-Started-Developing-CourtListener#how-settings-work-in-courtlistener>  
<https://www.courtlistener.com/help/api/bulk-data/>  
<https://www.courtlistener.com/help/api/rest/>  
<https://www.courtlistener.com/help/api/rest/search/>  
<https://www.courtlistener.com/help/api/webhooks/>  
<https://www.courtlistener.com/help/api/replication/>  
<https://github.com/freelawproject/courtlistener/discussions/3173>  
<https://www.courtlistener.com/opinion/>  
<https://www.courtlistener.com/help/api/rest/case-law/>  
<https://www.courtlistener.com/parenthetical/>  
<https://free.law/2022/03/17/summarizing-important-cases>  
<https://www.courtlistener.com/c/>  
<https://www.courtlistener.com/help/api/rest/citations/>  
<https://www.courtlistener.com/visualizations/scotus-mapper/>  
<https://www.courtlistener.com/help/api/rest/citation-lookup/>  
<https://www.courtlistener.com/recap/>  
<https://www.fjc.gov/research/idb>  
<https://www.courtlistener.com/help/api/rest/pacer/>  
<https://www.courtlistener.com/audio/>  
<https://www.courtlistener.com/help/api/rest/oral-arguments/>  
<https://www.courtlistener.com/person/>  
<https://free.law/projects/judge-pics>  
<https://www.courtlistener.com/help/api/rest/judges/>  
<https://www.courtlistener.com/financial-disclosures/>  
<https://www.courtlistener.com/help/api/rest/financial-disclosures/>  
<https://free.law/projects/juriscraper>  
<https://free.law/recap>  
<https://www.courtlistener.com/help/api/rest/recap/>  
<https://www.courtlistener.com/help/api/rest/recap/#pacer-fetch>  
<https://www.courtlistener.com/help/recap/email/>  
<https://bots.law/>  
<https://bots.law/big-cases/about/>  
<https://bots.law/little-cases/>  
<https://free.law/projects/x-ray>  
<https://free.law/projects/eyecite>  
<https://free.law/projects/doctor>  
<https://www.courtlistener.com/help/alerts/>  
<https://github.com/freelawproject/reporters-db/>
