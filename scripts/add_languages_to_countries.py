#!/usr/bin/env python3
"""
Add official languages to countries.json metadata.
This script adds a 'languages' field to each country with their primary official language(s).
"""

import json
import sys
from pathlib import Path

# Country to primary language mapping
COUNTRY_LANGUAGES = {
    "Afghanistan": "Pashto, Dari",
    "Albania": "Albanian",
    "Algeria": "Arabic",
    "Andorra": "Catalan",
    "Angola": "Portuguese",
    "Antigua and Barbuda": "English",
    "Argentina": "Spanish",
    "Armenia": "Armenian",
    "Australia": "English",
    "Austria": "German",
    "Azerbaijan": "Azerbaijani",
    "Bahamas": "English",
    "Bahrain": "Arabic",
    "Bangladesh": "Bengali",
    "Barbados": "English",
    "Belarus": "Belarusian, Russian",
    "Belgium": "Dutch, French, German",
    "Belize": "English",
    "Benin": "French",
    "Bhutan": "Dzongkha",
    "Bolivia": "Spanish",
    "Bosnia and Herzegovina": "Bosnian, Croatian, Serbian",
    "Botswana": "English, Setswana",
    "Brazil": "Portuguese",
    "Brunei": "Malay",
    "Bulgaria": "Bulgarian",
    "Burkina Faso": "French",
    "Burundi": "Kirundi, French",
    "Cabo Verde": "Portuguese",
    "Cambodia": "Khmer",
    "Cameroon": "French, English",
    "Canada": "English, French",
    "Central African Republic": "French",
    "Chad": "French, Arabic",
    "Chile": "Spanish",
    "China": "Mandarin Chinese",
    "Colombia": "Spanish",
    "Comoros": "Comorian, French, Arabic",
    "Congo": "French",
    "Costa Rica": "Spanish",
    "Croatia": "Croatian",
    "Cuba": "Spanish",
    "Cyprus": "Greek, Turkish",
    "Czechia": "Czech",
    "Democratic Republic of Congo": "French",
    "Denmark": "Danish",
    "Djibouti": "French, Arabic",
    "Dominica": "English",
    "Dominican Republic": "Spanish",
    "Ecuador": "Spanish",
    "Egypt": "Arabic",
    "El Salvador": "Spanish",
    "Equatorial Guinea": "Spanish, French, Portuguese",
    "Eritrea": "Tigrinya, Arabic, English",
    "Estonia": "Estonian",
    "Eswatini": "English, Swati",
    "Ethiopia": "Amharic",
    "Fiji": "English, Fijian",
    "Finland": "Finnish, Swedish",
    "France": "French",
    "Gabon": "French",
    "Gambia": "English",
    "Georgia": "Georgian",
    "Germany": "German",
    "Ghana": "English",
    "Greece": "Greek",
    "Grenada": "English",
    "Guatemala": "Spanish",
    "Guinea": "French",
    "Guinea-Bissau": "Portuguese",
    "Guyana": "English",
    "Haiti": "French, Haitian Creole",
    "Honduras": "Spanish",
    "Hungary": "Hungarian",
    "Iceland": "Icelandic",
    "India": "Hindi, English",
    "Indonesia": "Indonesian",
    "Iran": "Persian",
    "Iraq": "Arabic, Kurdish",
    "Ireland": "English, Irish Gaelic",
    "Israel": "Hebrew, Arabic",
    "Italy": "Italian",
    "Jamaica": "English",
    "Japan": "Japanese",
    "Jordan": "Arabic",
    "Kazakhstan": "Kazakh, Russian",
    "Kenya": "English, Swahili",
    "Kiribati": "English, Gilbertese",
    "Kuwait": "Arabic",
    "Kyrgyzstan": "Kyrgyz, Russian",
    "Laos": "Lao",
    "Latvia": "Latvian",
    "Lebanon": "Arabic",
    "Lesotho": "English, Sesotho",
    "Liberia": "English",
    "Libya": "Arabic",
    "Liechtenstein": "German",
    "Lithuania": "Lithuanian",
    "Luxembourg": "Luxembourgish, French, German",
    "Madagascar": "Malagasy, French",
    "Malawi": "English, Chichewa",
    "Malaysia": "Malay",
    "Maldives": "Dhivehi",
    "Mali": "French",
    "Malta": "Maltese, English",
    "Marshall Islands": "English, Marshallese",
    "Mauritania": "Arabic",
    "Mauritius": "English",
    "Mexico": "Spanish",
    "Micronesia": "English",
    "Moldova": "Romanian",
    "Monaco": "French",
    "Mongolia": "Mongolian",
    "Montenegro": "Montenegrin",
    "Morocco": "Arabic, Berber",
    "Mozambique": "Portuguese",
    "Myanmar": "Burmese",
    "Namibia": "English",
    "Nauru": "English, Nauruan",
    "Nepal": "Nepali",
    "Netherlands": "Dutch",
    "New Zealand": "English",
    "Nicaragua": "Spanish",
    "Niger": "French",
    "Nigeria": "English",
    "North Korea": "Korean",
    "North Macedonia": "Macedonian",
    "Norway": "Norwegian",
    "Oman": "Arabic",
    "Pakistan": "Urdu, English",
    "Palau": "English, Palauan",
    "Panama": "Spanish",
    "Papua New Guinea": "English",
    "Paraguay": "Spanish, Guarani",
    "Peru": "Spanish",
    "Philippines": "Filipino, English",
    "Poland": "Polish",
    "Portugal": "Portuguese",
    "Qatar": "Arabic",
    "Romania": "Romanian",
    "Russia": "Russian",
    "Rwanda": "Kinyarwanda, English, French",
    "Saint Kitts and Nevis": "English",
    "Saint Lucia": "English",
    "Saint Vincent-Grenadines": "English",
    "Samoa": "English, Samoan",
    "San Marino": "Italian",
    "Sao Tome and Principe": "Portuguese",
    "Saudi Arabia": "Arabic",
    "Senegal": "French",
    "Serbia": "Serbian",
    "Seychelles": "English, French, Seychellois Creole",
    "Sierra Leone": "English",
    "Singapore": "English, Malay, Mandarin Chinese, Tamil",
    "Slovakia": "Slovak",
    "Slovenia": "Slovenian",
    "Solomon Islands": "English",
    "Somalia": "Somali, Arabic",
    "South Africa": "English, Afrikaans, Zulu",
    "South Korea": "Korean",
    "South Sudan": "English",
    "Spain": "Spanish",
    "Sri Lanka": "Sinhala, Tamil",
    "Sudan": "Arabic",
    "Suriname": "Dutch",
    "Sweden": "Swedish",
    "Switzerland": "German, French, Italian, Romansh",
    "Syria": "Arabic",
    "Taiwan": "Mandarin Chinese",
    "Tajikistan": "Tajik",
    "Tanzania": "English, Swahili",
    "Thailand": "Thai",
    "Timor-Leste": "Portuguese, Tetum",
    "Togo": "French",
    "Tonga": "English, Tongan",
    "Trinidad and Tobago": "English",
    "Tunisia": "Arabic",
    "Turkey": "Turkish",
    "Turkmenistan": "Turkmen",
    "Tuvalu": "English, Tuvaluan",
    "Uganda": "English, Swahili",
    "Ukraine": "Ukrainian",
    "United Arab Emirates": "Arabic",
    "United Kingdom": "English",
    "United States": "English",
    "Uruguay": "Spanish",
    "Uzbekistan": "Uzbek",
    "Vanuatu": "English, French, Bislama",
    "Vatican City": "Italian, Latin",
    "Venezuela": "Spanish",
    "Vietnam": "Vietnamese",
    "Yemen": "Arabic",
    "Zambia": "English",
    "Zimbabwe": "English, Shona, Ndebele",
    # Additional countries found in countries.json
    "Bosnia Herzegovina": "Bosnian, Croatian, Serbian",
    "Cape Verde": "Portuguese",
    "Democratic Republic of the Congo": "French",
    "Greenland": "Danish, Greenlandic",
    "Ivory Coast": "French",
    "Kosovo": "Albanian, Serbian",
    "Palestine": "Arabic",
    "Republic of the Congo": "French",
    "São Tomé and Príncipe": "Portuguese"
}

def main():
    # Paths
    repo_root = Path(__file__).parent.parent
    countries_file = repo_root / "data" / "meta" / "countries.json"
    
    if not countries_file.exists():
        print(f"❌ Countries file not found: {countries_file}")
        return 1
    
    # Load existing countries data
    try:
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries = json.load(f)
    except Exception as e:
        print(f"❌ Error loading countries.json: {e}")
        return 1
    
    print(f"📚 Loaded {len(countries)} countries from {countries_file}")
    
    # Add languages to each country
    updated_count = 0
    missing_countries = []
    
    for country_name, country_data in countries.items():
        if country_name in COUNTRY_LANGUAGES:
            # Only add if not already present
            if "languages" not in country_data:
                country_data["languages"] = COUNTRY_LANGUAGES[country_name]
                updated_count += 1
            else:
                print(f"⏭️  {country_name}: languages already present")
        else:
            missing_countries.append(country_name)
    
    # Report missing mappings
    if missing_countries:
        print(f"\n⚠️  {len(missing_countries)} countries not found in language mapping:")
        for country in sorted(missing_countries):
            print(f"   - {country}")
    
    # Save updated countries.json
    if updated_count > 0:
        try:
            with open(countries_file, 'w', encoding='utf-8') as f:
                json.dump(countries, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Updated {updated_count} countries with languages")
            print(f"💾 Saved to {countries_file}")
        except Exception as e:
            print(f"❌ Error saving countries.json: {e}")
            return 1
    else:
        print("ℹ️  No updates needed - all countries already have languages")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())