# Compliance Scoring Standard

Version: 2.1.0

## Ziel

Dieses Dokument definiert die offizielle Gewichtung und Gate-Logik fuer FPF-Compliance-Audits.

## Bereiche und Gewichtung

| Bereich | Gewicht |
| --- | --- |
| Security | 30 % |
| Governance | 25 % |
| Deployment | 20 % |
| SEO/Crawling | 15 % |
| CI/GitHub | 10 % |

## Score-Berechnung

- Bereichsscores werden auf 0 bis 100 normalisiert.
- Gesamtscore ist die gewichtete Summe der Bereichsscores.

Beispiel:

$$
Score = 0.30 \cdot Security + 0.25 \cdot Governance + 0.20 \cdot Deployment + 0.15 \cdot SEO + 0.10 \cdot CI
$$

## Gates

Wenn ein Gate unterschritten wird, gilt unabhaengig vom Gesamtscore:

`status = red`

### Gate-Schwellen

- Security Gate: mindestens 70
- Governance Gate: mindestens 60
- Deployment Gate: mindestens 60

## Statusklassifikation ohne Gate-Verletzung

- `green`: Gesamtscore >= 85
- `yellow`: Gesamtscore >= 65 und < 85
- `red`: Gesamtscore < 65

## Fail-Fast

Wenn `PROJECT_MASTER.md` oder `standards/` fehlen:

- Audit sofort abbrechen
- kein geschaetzter Score
- Status `framework-unverifizierbar`
