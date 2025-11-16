#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 RealityCheck – Test Auto Country Mapping Agent
──────────────────────────────────────────────
Testet die Funktionalität des automatischen Country-Mapping-Agenten
"""

import json
import shutil
from pathlib import Path
from auto_resolve_pending_mappings import CountryMappingAgent

# Test-Pfade
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent.resolve() 
DATA_DIR = ROOT_DIR / "data"
META_DIR = DATA_DIR / "meta"

TEST_PENDING = {
    "DEU": "Unknown alias; please map in country_mappings.json",
    "USA": "Unknown alias; please map in country_mappings.json", 
    "Deutschland": "Unknown alias; please map in country_mappings.json",
    "Frankreich": "Unknown alias; please map in country_mappings.json",
    "GER": "Unknown alias; please map in country_mappings.json",
    "GBR": "Unknown alias; please map in country_mappings.json",
    "United States of America": "Unknown alias; please map in country_mappings.json",
    "Russian Federation": "Unknown alias; please map in country_mappings.json",
    "Czech Republic": "Unknown alias; please map in country_mappings.json",
    "Korea, Rep.": "Unknown alias; please map in country_mappings.json",
    "World Bank Group": "Unknown alias; please map in country_mappings.json",
    "European Union": "Unknown alias; please map in country_mappings.json",
    "East Asia & Pacific": "Unknown alias; please map in country_mappings.json",
    "Soviet Union": "Unknown alias; please map in country_mappings.json",
    "Mixed team": "Unknown alias; please map in country_mappings.json",
    "Independent Olympic Athletes": "Unknown alias; please map in country_mappings.json",
    "High income": "Unknown alias; please map in country_mappings.json",
    "Argentina (ARG)": "Unknown alias; please map in country_mappings.json",
    "Germany (GER)": "Unknown alias; please map in country_mappings.json"
}

def run_test():
    """Führe Test des Auto-Mapping-Agenten aus"""
    print("🧪 Testing Auto Country Mapping Agent...")
    
    # Backup der original pending file falls vorhanden
    pending_file = META_DIR / "country_mappings_pending.json"
    backup_file = META_DIR / "country_mappings_pending.json.backup"
    
    original_exists = pending_file.exists()
    if original_exists:
        shutil.copy2(pending_file, backup_file)
        print(f"📁 Backup erstellt: {backup_file}")
    
    try:
        # Test-Daten schreiben
        with pending_file.open("w", encoding="utf-8") as f:
            json.dump(TEST_PENDING, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Test pending mappings geschrieben ({len(TEST_PENDING)} entries)")
        
        # Agent ausführen
        agent = CountryMappingAgent()
        resolved, remaining, log_entries = agent.process_pending_mappings()
        
        print("\n📊 TEST ERGEBNISSE:")
        print(f"   ✅ Resolved: {len(resolved)}")
        print(f"   ⏳ Remaining: {len(remaining)}")
        
        if resolved:
            print(f"\n✅ RESOLVED MAPPINGS:")
            for alias, target in resolved.items():
                print(f"   '{alias}' → '{target}'")
        
        if remaining:
            print(f"\n⏳ REMAINING PENDING (erste 10):")
            for i, (alias, _) in enumerate(remaining.items()):
                if i >= 10:
                    print(f"   ... und {len(remaining) - 10} weitere")
                    break
                print(f"   '{alias}'")
        
        # Erwartete Ergebnisse prüfen
        expected_resolved = {
            "DEU": "Germany",
            "USA": "United States", 
            "Deutschland": "Germany",
            "Frankreich": "France",
            "GER": "Germany",
            "GBR": "United Kingdom",
            "United States of America": "United States",
            "Russian Federation": "Russia",
            "Czech Republic": "Czech Republic",
            "Korea, Rep.": "South Korea",
            "Argentina (ARG)": "Argentina",
            "Germany (GER)": "Germany"
        }
        
        expected_excluded = {
            "World Bank Group", "European Union", "East Asia & Pacific",
            "Soviet Union", "Mixed team", "Independent Olympic Athletes", 
            "High income"
        }
        
        print(f"\n🔍 VALIDIERUNG:")
        
        # Prüfe resolved mappings
        validation_errors = 0
        for alias, expected_target in expected_resolved.items():
            if alias in resolved:
                actual_target = resolved[alias]
                if actual_target == expected_target:
                    print(f"   ✅ '{alias}' → '{actual_target}' (korrekt)")
                else:
                    print(f"   ❌ '{alias}' → '{actual_target}' (erwartet: '{expected_target}')")
                    validation_errors += 1
            else:
                print(f"   ⚠️ '{alias}' nicht resolved (erwartet: '{expected_target}')")
                validation_errors += 1
        
        # Prüfe ausgeschlossene Einträge
        for alias in expected_excluded:
            if alias in remaining:
                print(f"   ✅ '{alias}' korrekt ausgeschlossen")
            else:
                print(f"   ❌ '{alias}' wurde nicht ausgeschlossen")
                validation_errors += 1
        
        print(f"\n🏁 TEST ZUSAMMENFASSUNG:")
        print(f"   📊 Total processed: {len(TEST_PENDING)}")
        print(f"   ✅ Resolved: {len(resolved)} (erwartet: {len(expected_resolved)})")
        print(f"   🚫 Excluded: {len([a for a in remaining if a in expected_excluded])} (erwartet: {len(expected_excluded)})")
        print(f"   ⚠️ Validation errors: {validation_errors}")
        
        if validation_errors == 0:
            print("   🎉 ALLE TESTS ERFOLGREICH!")
        else:
            print(f"   ❌ {validation_errors} Fehler gefunden")
        
        return validation_errors == 0
        
    finally:
        # Cleanup: Original pending file wiederherstellen
        if original_exists:
            shutil.copy2(backup_file, pending_file)
            backup_file.unlink()
            print(f"🔄 Original pending file wiederhergestellt")
        else:
            if pending_file.exists():
                pending_file.unlink()
            print("🗑️ Test pending file entfernt")

if __name__ == "__main__":
    success = run_test()
    exit(0 if success else 1)