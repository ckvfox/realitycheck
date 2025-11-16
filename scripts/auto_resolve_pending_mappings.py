#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 RealityCheck – Auto-Resolve Pending Country Mappings Agent
────────────────────────────────────────────────────────────
Automatischer Agent zur intelligenten Verarbeitung von country_mappings_pending.json

Verarbeitet EINDEUTIGE Mappings basierend auf:
1. ISO 2/3-Codes (GER → Germany, DEU → Germany)  
2. Deutsche Namen (Deutschland → Germany, Frankreich → France)
3. Bekannte Varianten (United States of America → United States)
4. Olympische Codes (GBR → United Kingdom, USA → United States)

Lässt UNKLARE Einträge für manuelle Prüfung in pending.json:
- Regionale Gruppen (World Bank, UN, etc.)
- Historische Entitäten (Soviet Union, Yugoslavia, etc.) 
- Nicht-Länder (Mixed team, Independent Olympic Athletes)
"""

import json
import re
from pathlib import Path
from typing import Dict, Set, List, Tuple
from script_utils import safe_write_json, setup_logger, ensure_utf8_stdout

# UTF-8 Fix für Windows
ensure_utf8_stdout()

# === Pfade ===
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent.resolve()
DATA_DIR = ROOT_DIR / "data"
META_DIR = DATA_DIR / "meta"

COUNTRIES_FILE = META_DIR / "countries.json"
MAPPINGS_FILE = META_DIR / "country_mappings.json"
PENDING_FILE = META_DIR / "country_mappings_pending.json"
LOG_FILE = DATA_DIR / "fetch_log.txt"

logger = setup_logger("auto_mapping", LOG_FILE)

def log(msg: str) -> None:
    """Log message to both console and file"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Fallback ohne Emojis für Windows-Terminals
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(safe_msg)
    logger.info(msg)

class CountryMappingAgent:
    """Intelligenter Agent für automatische Country-Mapping-Verarbeitung"""
    
    def __init__(self):
        self.countries = self._load_countries()
        self.existing_mappings = self._load_existing_mappings()
        self.pending_mappings = self._load_pending_mappings()
        
        # ISO 2/3 Code Lookup basierend auf countries.json
        self.iso_lookup = self._build_iso_lookup()
        
        # Deutsche → Englische Namen
        self.german_names = self._build_german_lookup()
        
        # Olympische Codes → Ländernamen
        self.olympic_codes = self._build_olympic_lookup()
        
        # Bekannte Varianten von Ländernamen
        self.name_variants = self._build_name_variants()
        
        # Gruppen/Regionen die NICHT automatisch gemappt werden sollen
        self.excluded_patterns = self._build_exclusion_patterns()
    
    def _load_countries(self) -> Dict:
        """Lade countries.json"""
        try:
            with COUNTRIES_FILE.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"❌ Fehler beim Laden von countries.json: {e}")
            return {}
    
    def _load_existing_mappings(self) -> Dict:
        """Lade bestehende country_mappings.json"""
        try:
            with MAPPINGS_FILE.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"❌ Fehler beim Laden von country_mappings.json: {e}")
            return {}
    
    def _load_pending_mappings(self) -> Dict:
        """Lade pending mappings"""
        try:
            with PENDING_FILE.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"⚠️ Keine pending mappings gefunden: {e}")
            return {}
    
    def _build_iso_lookup(self) -> Dict[str, str]:
        """Erstelle ISO Code → Country Name Lookup"""
        iso_map = {}
        for country_name, country_data in self.countries.items():
            if isinstance(country_data, dict):
                # ISO A2 codes
                if "iso_a2" in country_data:
                    iso_map[country_data["iso_a2"]] = country_name
                # ISO A3 codes  
                if "iso_a3" in country_data:
                    iso_map[country_data["iso_a3"]] = country_name
        return iso_map
    
    def _build_german_lookup(self) -> Dict[str, str]:
        """Deutsche Namen → Englische Namen"""
        return {
            "Deutschland": "Germany",
            "Frankreich": "France", 
            "Italien": "Italy",
            "Spanien": "Spain",
            "Niederlande": "Netherlands",
            "Belgien": "Belgium",
            "Österreich": "Austria",
            "Schweiz": "Switzerland",
            "Schweden": "Sweden",
            "Norwegen": "Norway",
            "Dänemark": "Denmark",
            "Finnland": "Finland",
            "Polen": "Poland",
            "Tschechien": "Czech Republic",
            "Slowakei": "Slovakia",
            "Slowenien": "Slovenia",
            "Ungarn": "Hungary",
            "Rumänien": "Romania",
            "Bulgarien": "Bulgaria",
            "Kroatien": "Croatia",
            "Serbien": "Serbia",
            "Bosnien und Herzegowina": "Bosnia and Herzegovina",
            "Nordmazedonien": "North Macedonia",
            "Albanien": "Albania",
            "Griechenland": "Greece",
            "Türkei": "Turkey",
            "Russland": "Russia",
            "Vereinigtes Königreich": "United Kingdom",
            "Irland": "Ireland",
            "Portugal": "Portugal",
            "Brasilien": "Brazil",
            "Argentinien": "Argentina",
            "Mexiko": "Mexico",
            "Kolumbien": "Colombia",
            "Kanada": "Canada",
            "Vereinigte Staaten": "United States",
            "Australien": "Australia",
            "Neuseeland": "New Zealand",
            "Japan": "Japan",
            "Südkorea": "South Korea",
            "China": "China",
            "Volksrepublik China": "China",
            "Indien": "India",
            "Indonesien": "Indonesia",
            "Thailand": "Thailand",
            "Singapur": "Singapore",
            "Malaysia": "Malaysia",
            "Philippinen": "Philippines",
            "Vietnam": "Vietnam",
            "Südafrika": "South Africa",
            "Ägypten": "Egypt",
            "Marokko": "Morocco",
            "Kenia": "Kenya",
            "Nigeria": "Nigeria",
            "Äthiopien": "Ethiopia",
            "Ghana": "Ghana",
            "Israel": "Israel",
            "Saudi-Arabien": "Saudi Arabia",
            "Vereinigte Arabische Emirate": "United Arab Emirates",
            "Iran": "Iran",
            "Irak": "Iraq",
            "Syrien": "Syria",
            "Libanon": "Lebanon",
            "Jordanien": "Jordan"
        }
    
    def _build_olympic_lookup(self) -> Dict[str, str]:
        """Olympische IOC Codes → Ländernamen"""
        return {
            "GER": "Germany",
            "GBR": "United Kingdom", 
            "USA": "United States",
            "CAN": "Canada",
            "FRA": "France",
            "ITA": "Italy",
            "ESP": "Spain",
            "NED": "Netherlands",
            "BEL": "Belgium",
            "AUT": "Austria",
            "SUI": "Switzerland",
            "SWE": "Sweden",
            "NOR": "Norway",
            "DEN": "Denmark",
            "FIN": "Finland",
            "POL": "Poland",
            "CZE": "Czech Republic",
            "SVK": "Slovakia",
            "SVN": "Slovenia",
            "HUN": "Hungary",
            "ROU": "Romania",
            "BUL": "Bulgaria",
            "CRO": "Croatia",
            "SRB": "Serbia",
            "MKD": "North Macedonia",
            "ALB": "Albania",
            "GRE": "Greece",
            "TUR": "Turkey",
            "RUS": "Russia",
            "IRL": "Ireland",
            "POR": "Portugal",
            "BRA": "Brazil",
            "ARG": "Argentina",
            "MEX": "Mexico",
            "COL": "Colombia",
            "AUS": "Australia",
            "NZL": "New Zealand",
            "JPN": "Japan",
            "KOR": "South Korea",
            "CHN": "China",
            "IND": "India",
            "IDN": "Indonesia",
            "THA": "Thailand",
            "SIN": "Singapore",
            "MAS": "Malaysia",
            "PHI": "Philippines",
            "VIE": "Vietnam",
            "RSA": "South Africa",
            "EGY": "Egypt",
            "MAR": "Morocco",
            "KEN": "Kenya",
            "NGA": "Nigeria",
            "ETH": "Ethiopia",
            "GHA": "Ghana",
            "ISR": "Israel",
            "KSA": "Saudi Arabia",
            "UAE": "United Arab Emirates",
            "IRI": "Iran",
            "IRQ": "Iraq",
            "SYR": "Syria",
            "LBN": "Lebanon",
            "JOR": "Jordan"
        }
    
    def _build_name_variants(self) -> Dict[str, str]:
        """Bekannte Ländername-Varianten"""
        return {
            "United States of America": "United States",
            "Russian Federation": "Russia",
            "Czech Republic": "Czech Republic",
            "Slovak Republic": "Slovakia", 
            "Viet Nam": "Vietnam",
            "Korea, Rep.": "South Korea",
            "Korea, Dem. People's Rep.": "North Korea",
            "Iran, Islamic Rep.": "Iran",
            "Egypt, Arab Rep.": "Egypt",
            "Yemen, Rep.": "Yemen",
            "Lao PDR": "Laos",
            "Kyrgyz Republic": "Kyrgyzstan",
            "Syrian Arab Republic": "Syria",
            "Venezuela, RB": "Venezuela",
            "Turkiye": "Turkey",
            "Congo, Rep.": "Republic of the Congo",
            "Congo, Dem. Rep.": "Democratic Republic of the Congo",
            "Cote d'Ivoire": "Ivory Coast",
            "Cabo Verde": "Cape Verde",
            "Gambia, The": "Gambia",
            "Bahamas, The": "Bahamas",
            "Micronesia, Fed. Sts.": "Micronesia",
            "St. Lucia": "Saint Lucia",
            "St. Kitts and Nevis": "Saint Kitts and Nevis",
            "St. Vincent and the Grenadines": "Saint Vincent and the Grenadines",
            "Sao Tome and Principe": "São Tomé and Príncipe",
            "Bosnia and Herzegovina": "Bosnia and Herzegovina",
            "Brunei Darussalam": "Brunei",
            "Hong Kong SAR, China": "Hong Kong",
            "Macao SAR, China": "Macau"
        }
    
    def _build_exclusion_patterns(self) -> List[str]:
        """Patterns für Einträge die NICHT automatisch gemappt werden sollen"""
        return [
            # World Bank Regionen
            r".*\(WB\)$",
            r"East Asia.*Pacific.*WB",
            r"Europe.*Central Asia.*WB", 
            r"Latin America.*Caribbean.*WB",
            r"Middle East.*North Africa.*WB",
            r"South Asia.*WB",
            r"Sub-Saharan Africa.*WB",
            # UN Regionen
            r".*\(UN\)$", 
            r"Africa \(UN\)",
            r"Asia \(UN\)",
            r"Europe \(UN\)",
            r"Americas.*UN",
            # UNDP/SIPRI/GCP Regionen
            r".*\(UNDP\)$",
            r".*\(SIPRI\)$", 
            r".*\(GCP\)$",
            # Einkomensgruppen
            r"High income",
            r"Low income", 
            r"Middle income",
            r"Upper.*middle.*income",
            r"Lower.*middle.*income",
            # Spezielle Gruppen
            r"World",
            r"Mixed team",
            r"Independent Olympic.*",
            r"Refugee Olympic Team",
            r".*small states",
            r"Least developed countries",
            r"OECD members", 
            r"European Union",
            r"Euro area",
            # Historische Entitäten
            r"Soviet Union",
            r"Yugoslavia", 
            r"Czechoslovakia",
            r"East Germany",
            r"West Germany",
            r".*Empire$",
            # Kontinente
            r"^Africa$",
            r"^Asia$", 
            r"^Europe$",
            r"^Oceania$",
            r"^Americas$",
            # Sonstige Gruppen
            r".*population-weighted.*"
        ]
    
    def _should_exclude(self, alias: str) -> bool:
        """Prüfe ob ein Alias automatisch ausgeschlossen werden soll"""
        for pattern in self.excluded_patterns:
            if re.search(pattern, alias, re.IGNORECASE):
                return True
        return False
    
    def _find_mapping(self, alias: str) -> str | None:
        """Finde automatisches Mapping für einen Alias"""
        
        # 1. Bereits in existing mappings?
        if alias in self.existing_mappings:
            existing = self.existing_mappings[alias]
            if existing and existing in self.countries:
                return existing
        
        # 2. Direkte Übereinstimmung mit Ländernamen?
        if alias in self.countries:
            return alias
        
        # 3. ISO 2/3 Code?
        if alias in self.iso_lookup:
            return self.iso_lookup[alias]
        
        # 4. Deutscher Name?
        if alias in self.german_names:
            german_target = self.german_names[alias]
            if german_target in self.countries:
                return german_target
        
        # 5. Olympischer Code?
        if alias in self.olympic_codes:
            olympic_target = self.olympic_codes[alias]
            if olympic_target in self.countries:
                return olympic_target
        
        # 6. Bekannte Namensvariante?
        if alias in self.name_variants:
            variant_target = self.name_variants[alias]
            if variant_target in self.countries:
                return variant_target
        
        # 7. Olympischer Code mit (XXX) Suffix?
        olympic_match = re.match(r"(.+?)\s*\([A-Z]{3}\)$", alias)
        if olympic_match:
            country_part = olympic_match.group(1).strip()
            if country_part in self.countries:
                return country_part
        
        # Kein automatisches Mapping gefunden
        return None
    
    def process_pending_mappings(self) -> Tuple[Dict, Dict, List]:
        """
        Verarbeite pending mappings und returniere:
        (resolved_mappings, remaining_pending, resolution_log)
        """
        resolved = {}
        remaining = {}
        log_entries = []
        
        for alias, _ in self.pending_mappings.items():
            
            # Soll dieser Alias ausgeschlossen werden?
            if self._should_exclude(alias):
                remaining[alias] = "Unknown alias; please map in country_mappings.json"
                log_entries.append(f"EXCLUDED (Gruppe/Region): '{alias}'")
                continue
            
            # Versuche automatisches Mapping zu finden
            target = self._find_mapping(alias)
            
            if target:
                resolved[alias] = target
                log_entries.append(f"AUTO-RESOLVED: '{alias}' -> '{target}'")
            else:
                remaining[alias] = "Unknown alias; please map in country_mappings.json"
                log_entries.append(f"REMAINS PENDING: '{alias}' (keine eindeutige Zuordnung)")
        
        return resolved, remaining, log_entries
    
    def update_mappings_file(self, resolved_mappings: Dict) -> None:
        """Aktualisiere country_mappings.json mit resolved mappings"""
        if not resolved_mappings:
            log("INFO: Keine neuen Mappings zum Hinzufügen")
            return
            
        # Merge mit bestehenden mappings
        updated_mappings = {**self.existing_mappings, **resolved_mappings}
        
        # Sortiere alphabetisch für bessere Lesbarkeit
        sorted_mappings = dict(sorted(updated_mappings.items()))
        
        # Schreibe zurück
        safe_write_json(MAPPINGS_FILE, sorted_mappings)
        log(f"SUCCESS: {len(resolved_mappings)} neue Mappings zu country_mappings.json hinzugefügt")
    
    def update_pending_file(self, remaining_pending: Dict) -> None:
        """Aktualisiere country_mappings_pending.json mit verbleibenden Einträgen"""
        if remaining_pending:
            safe_write_json(PENDING_FILE, remaining_pending)
            log(f"PENDING: {len(remaining_pending)} Einträge verbleiben in pending für manuelle Prüfung")
        else:
            # Lösche pending file wenn alles resolved wurde
            if PENDING_FILE.exists():
                PENDING_FILE.unlink()
            log("SUCCESS: Alle pending mappings resolved! Pending-Datei gelöscht.")
    
    def run(self) -> None:
        """Hauptfunktion: Führe automatische Mapping-Resolution aus"""
        log("Starting Auto Country Mapping Agent...")
        
        if not self.pending_mappings:
            log("INFO: Keine pending mappings gefunden. Nichts zu tun.")
            return
        
        log(f"FOUND: {len(self.pending_mappings)} pending mappings gefunden")
        
        # Verarbeite pending mappings
        resolved, remaining, log_entries = self.process_pending_mappings()
        
        # Log alle Aktionen
        for entry in log_entries:
            log(entry)
        
        # Aktualisiere Dateien
        if resolved:
            self.update_mappings_file(resolved)
        
        self.update_pending_file(remaining)
        
        # Zusammenfassung
        log(f"""
ZUSAMMENFASSUNG:
   Automatisch resolved: {len(resolved)}
   Verbleiben pending:    {len(remaining)}
   Total processed:      {len(self.pending_mappings)}
   Countries verfügbar:  {len(self.countries)}
        """)

def main():
    """Hauptfunktion"""
    try:
        agent = CountryMappingAgent()
        agent.run()
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(f"Traceback:\n{traceback.format_exc()}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())