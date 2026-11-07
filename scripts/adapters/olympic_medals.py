"""Resolve Olympic delegations for the present-day UN member-state view."""
import re

# The project country registry contains the 193 UN members plus these five.
NON_MEMBERS = frozenset({"GL", "XK", "PS", "TW", "VA"})
EXCLUDED = frozenset("""
4 AIN ANZ BOH BWI GDR EUN HKG IOA IOP ISV KOS MIX OAR ROC ROT EOR PUR
RAU TCH TPE URS YUG AHO BER
""".lower().split()) | frozenset({
    "australasia", "bermuda", "bohemia", "british west indies", "chinese taipei",
    "czechoslovakia", "east germany", "formosa", "fr yugoslavia", "hong kong",
    "independent olympic athletes", "independent olympic participants",
    "individual neutral athletes", "kosovo", "mixed team", "netherlands antilles",
    "puerto rico", "refugee olympic team", "russian empire", "serbia and montenegro",
    "soviet union", "taiwan", "unified team", "united arab republic", "virgin islands",
    "yugoslavia",
})
DELEGATION_NAMES = {
    "eua": "Germany",
    "frg": "Germany",
    "united team of germany": "Germany",
    "west germany": "Germany",
    "slo": "Slovenia",
    "lat": "Latvia",
    "rsa": "South Africa",
}


def records(rows, countries, resolve_country):
    result = {}
    for row in rows:
        label = re.sub(r"(?:\[[A-Za-z]+\])+$", "", str(row["country"])).strip()
        match = re.fullmatch(r"(.+?)\s+\(([A-Z]{3})\)", label)
        name, code = match.groups() if match else (label, label)
        name_key, code_key = name.casefold(), code.casefold()
        if name_key in EXCLUDED or code_key in EXCLUDED:
            continue
        country = DELEGATION_NAMES.get(code_key) or DELEGATION_NAMES.get(name_key)
        country = country or resolve_country(name)
        if country not in countries:
            raise ValueError(f"Unclassified Olympic delegation: {label}")
        iso2 = countries[country]["iso_a2"]
        if iso2 in NON_MEMBERS:
            continue

        year, value = float(row["year"]), float(row["value"])
        if not year.is_integer() or not value.is_integer() or value <= 0:
            raise ValueError(f"Invalid medal total or year for {label}")
        key = country, int(year)
        record = {"country": country, "iso2": iso2, "year": int(year), "value": value}
        if key in result and result[key] != record:
            raise ValueError(f"Conflicting Olympic medal totals for {country}, {int(year)}")
        result[key] = record
    return list(result.values())
