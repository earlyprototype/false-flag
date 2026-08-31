# P1a — Gazetteer QA dossier

**Summary.** Verification table for the ~30 named locations in the war_game_2025 scenario (issue #70, task P1a), plus `East_Anglia_RAF_bases` (added on owner instruction — it appears as a location key in `data/scenarios/war_game_2025/initial_conditions.yaml:310`). 19 of the 20 point locations verified HIGH confidence against Wikipedia/Wikidata coordinates with official MOD/service pages confirming identity; St Fergus gas terminal is MEDIUM (village-level coordinate, the terminal sits ~0.5–1 km east — see exceptions). Seven derived/definition entries (GIUK references, North Atlantic rendezvous, East Anglia centroid, UK territorial waters) are CHECK-flagged with methods stated. Nothing unsourced; three figures spot-checked against live pages (RAF Marham, HMNB Clyde, Severomorsk — all matched to 4 dp).

**Confidence note (overall):** high for point locations (Wikipedia/Wikidata floor per issue spec, no conflicts >0.01° found); medium for derived points by construction (computed, not sourced facts).

## Verification table

| name | lat | lon | identification | confidence | sources |
|---|---|---|---|---|---|
| London (Whitehall) | 51.5042 | -0.1264 | UK government district; ministries and Cabinet Office, Westminster, London | high | [1] |
| Portsmouth naval base | 50.8042 | -1.1025 | HMNB Portsmouth; home of RN surface fleet incl. aircraft carriers, Hampshire | high | [2] [3] |
| Plymouth (Devonport) | 50.3850 | -4.1850 | HMNB Devonport; largest naval base in Western Europe, Plymouth, Devon | high | [4] [5] |
| Faslane (HMNB Clyde) | 56.0661 | -4.8175 | HMNB Clyde (Faslane); home of UK Submarine Service and nuclear deterrent, Gare Loch, Scotland | high | [6] [7] |
| RAF Marham | 52.6483 | 0.5506 | RAF station; home of the F-35B Lightning Force, Norfolk | high | [8] [9] |
| RNAS Yeovilton | 51.0086 | -2.6378 | Royal Naval Air Station; Fleet Air Arm Wildcat and Commando Helicopter Force, Somerset | high | [10] [11] |
| RAF Lossiemouth | 57.7053 | -3.3392 | RAF station; Typhoon QRA North and P-8 Poseidon base, Moray, Scotland | high | [12] [13] |
| RAF Coningsby | 53.0931 | -0.1661 | RAF station; Typhoon QRA South and Battle of Britain Memorial Flight, Lincolnshire | high | [14] [15] |
| RAF Fylingdales | 54.3589 | -0.6697 | RAF station; ballistic missile early warning and space surveillance, North Yorkshire | high | [16] [17] |
| Northwood HQ | 51.6194 | -0.4094 | Permanent Joint Headquarters (PJHQ); UK joint operations command, Northwood, Hertfordshire | high | [18] [19] |
| GCHQ Cheltenham | 51.8994 | -2.1244 | Government Communications Headquarters ("The Doughnut"), Cheltenham, Gloucestershire | high | [20] [21] |
| Drax power station | 53.7358 | -0.9964 | Drax Power Station; largest UK power station by output, near Selby, North Yorkshire | high | [22] |
| St Fergus gas terminal | 57.5583 | -1.8364 | St Fergus Gas Terminal; North Sea gas reception plant near Peterhead, Aberdeenshire | medium | [23] |
| Heathrow | 51.4775 | -0.4614 | London Heathrow Airport; UK's primary international airport, Hillingdon, West London | high | [24] [25] |
| Oxford Circus | 51.5153 | -0.1419 | Road junction of Oxford Street and Regent Street, central London | high | [26] [27] |
| Orkney Islands (Scapa Flow) | 58.9000 | -3.0500 | Scapa Flow; sheltered naval anchorage in the Orkney Islands, Scotland | high | [28] |
| Aberdeen | 57.1500 | -2.1100 | Aberdeen; North Sea oil and gas port city, Aberdeenshire, Scotland | high | [29] |
| Scrabster | 58.6097 | -3.5525 | Scrabster; ferry and fishing port near Thurso, Caithness, Scotland | high | [30] |
| Severomorsk | 69.0667 | 33.4167 | Severomorsk; administrative HQ of the Russian Northern Fleet, Murmansk Oblast, Russia | high | [31] |
| Murmansk | 68.9706 | 33.0750 | Murmansk; largest city above the Arctic Circle; major Barents Sea port, Russia | high | [32] |
| East_Anglia_RAF_bases | 52.4739 | 0.5294 | Representative centroid of the East Anglia RAF cluster (Marham, Lakenheath, Mildenhall) | low (derived) | [9] [33] [34] |
| UK_territorial_waters | — | — | UK territorial sea: 12 nautical miles from baselines per Territorial Sea Act 1987 s.1; definition note only, no centroid | n/a (definition) | [35] [36] |
| North_Atlantic_rendezvous | 70.6191 | -0.7178 | Representative staging point for Northern Fleet group transiting Severomorsk toward GIUK; Norwegian Sea | low (derived) | [31] [37] [38] |
| GIUK_gap | 63.4556 | -15.0178 | GIUK gap overall centroid; Greenland–Iceland–UK naval chokepoint, North Atlantic | low (derived) | [37] [38] [39] [40] [41] [42] |
| GIUK_ref_Greenland_Iceland | 65.9852 | -30.2309 | GIUK reference point: Denmark Strait between Greenland and Iceland | low (derived) | [37] [38] |
| GIUK_ref_Iceland_Faroes | 63.1875 | -10.8363 | GIUK reference point: strait between Iceland and the Faroe Islands | low (derived) | [39] [40] |
| GIUK_ref_Faroes_Shetland | 61.1940 | -3.9863 | GIUK reference point: Faroe–Shetland Channel between Faroes and Shetland | low (derived) | [40] [41] |

## CSV (machine-readable, for `gazetteer.yaml` intake)

```csv
name,lat,lon,identification,source_urls,confidence,notes
London (Whitehall),51.5042,-0.1264,"UK government district; ministries and Cabinet Office, Westminster, London",https://en.wikipedia.org/wiki/Whitehall,HIGH,"Wikipedia article coordinate; street-level feature, coordinate is mid-Whitehall"
Portsmouth naval base,50.8042,-1.1025,"HMNB Portsmouth; home of RN surface fleet incl. aircraft carriers, Hampshire",https://www.royalnavy.mod.uk/locations-and-operations/bases-and-stations/hmnb-portsmouth; https://en.wikipedia.org/wiki/HMNB_Portsmouth,HIGH,"RN page confirms identity/address (PO1 3LS); coordinates from Wikipedia"
Plymouth (Devonport),50.3850,-4.1850,"HMNB Devonport; largest naval base in Western Europe, Plymouth, Devon",https://www.royalnavy.mod.uk/locations-and-operations/bases-and-stations/hmnb-devonport; https://en.wikipedia.org/wiki/HMNB_Devonport,HIGH,"RN page confirms identity/address (PL2 2BG); coordinates from Wikipedia"
Faslane (HMNB Clyde),56.0661,-4.8175,"HMNB Clyde (Faslane); home of UK Submarine Service and nuclear deterrent, Gare Loch, Scotland",https://www.royalnavy.mod.uk/locations-and-operations/bases-and-stations/hmnb-clyde; https://en.wikipedia.org/wiki/HMNB_Clyde,HIGH,"RN page confirms identity/address (G84 0EH); coordinates from Wikipedia; spot-checked on article page"
RAF Marham,52.6483,0.5506,"RAF station; home of the F-35B Lightning Force, Norfolk",https://www.raf.mod.uk/our-organisation/stations/raf-marham/; https://en.wikipedia.org/wiki/RAF_Marham,HIGH,"RAF page confirms identity; coordinates from Wikipedia; spot-checked on article page"
RNAS Yeovilton,51.0086,-2.6378,"Royal Naval Air Station; Fleet Air Arm Wildcat and Commando Helicopter Force, Somerset",https://www.royalnavy.mod.uk/locations-and-operations/bases-and-stations/rnas-yeovilton; https://en.wikipedia.org/wiki/RNAS_Yeovilton,HIGH,"RN page confirms identity/address (BA22 8HT); coordinates from Wikipedia"
RAF Lossiemouth,57.7053,-3.3392,"RAF station; Typhoon QRA North and P-8 Poseidon base, Moray, Scotland",https://www.raf.mod.uk/our-organisation/stations/raf-lossiemouth/; https://en.wikipedia.org/wiki/RAF_Lossiemouth,HIGH,"RAF page confirms identity; coordinates from Wikipedia"
RAF Coningsby,53.0931,-0.1661,"RAF station; Typhoon QRA South and Battle of Britain Memorial Flight, Lincolnshire",https://www.raf.mod.uk/our-organisation/stations/raf-coningsby/; https://en.wikipedia.org/wiki/RAF_Coningsby,HIGH,"RAF page confirms identity; coordinates from Wikipedia"
RAF Fylingdales,54.3589,-0.6697,"RAF station; ballistic missile early warning and space surveillance, North Yorkshire",https://www.raf.mod.uk/our-organisation/stations/raf-fylingdales/; https://en.wikipedia.org/wiki/RAF_Fylingdales,HIGH,"RAF page confirms identity (BMEWS role stated); coordinates from Wikipedia"
Northwood HQ,51.6194,-0.4094,"Permanent Joint Headquarters (PJHQ); UK joint operations command, Northwood, Hertfordshire",https://www.gov.uk/government/groups/the-permanent-joint-headquarters; https://en.wikipedia.org/wiki/Northwood_Headquarters,HIGH,"gov.uk page confirms PJHQ identity; coordinates from Wikipedia"
GCHQ Cheltenham,51.8994,-2.1244,"Government Communications Headquarters ('The Doughnut'), Cheltenham, Gloucestershire",https://www.gchq.gov.uk/; https://en.wikipedia.org/wiki/GCHQ,HIGH,"GCHQ official site confirms organisation; coordinates from Wikipedia (GCHQ article)"
Drax power station,53.7358,-0.9964,"Drax Power Station; largest UK power station by output, near Selby, North Yorkshire",https://en.wikipedia.org/wiki/Drax_Power_Station,HIGH,"Coordinates from Wikipedia; drax.com blocked automated fetch (403) so official URL not verified"
St Fergus gas terminal,57.5583,-1.8364,"St Fergus Gas Terminal; North Sea gas reception plant near Peterhead, Aberdeenshire",https://en.wikipedia.org/wiki/St_Fergus,medium,"Coordinate is St Fergus village (Wikipedia); terminal sits adjacent (~0.5 km) — see exceptions"
Heathrow,51.4775,-0.4614,"London Heathrow Airport; UK's primary international airport, Hillingdon, West London",https://www.heathrow.com/; https://en.wikipedia.org/wiki/Heathrow_Airport,HIGH,"heathrow.com reachable (200); coordinates from Wikipedia"
Oxford Circus,51.5153,-0.1419,"Road junction of Oxford Street and Regent Street, central London",https://en.wikipedia.org/wiki/Oxford_Circus; https://www.wikidata.org/wiki/Q1996213,HIGH,"Coordinates from Wikidata Q1996213 P625 (enwiki article Oxford Circus)"
Orkney Islands (Scapa Flow),58.9000,-3.0500,"Scapa Flow; sheltered naval anchorage in the Orkney Islands, Scotland",https://en.wikipedia.org/wiki/Scapa_Flow,HIGH,"Coordinate is Scapa Flow body of water (Wikipedia); scenario references Orkney anchorage — fit for purpose"
Aberdeen,57.1500,-2.1100,"Aberdeen; North Sea oil and gas port city, Aberdeenshire, Scotland",https://en.wikipedia.org/wiki/Aberdeen,HIGH,"City-centre coordinate (Wikipedia)"
Scrabster,58.6097,-3.5525,"Scrabster; ferry and fishing port near Thurso, Caithness, Scotland",https://en.wikipedia.org/wiki/Scrabster,HIGH,"Harbour village coordinate (Wikipedia)"
Severomorsk,69.0667,33.4167,"Severomorsk; administrative HQ of the Russian Northern Fleet, Murmansk Oblast, Russia",https://en.wikipedia.org/wiki/Severomorsk,HIGH,"City coordinate (Wikipedia); spot-checked on article page; naval base piers lie on the bay adjacent"
Murmansk,68.9706,33.0750,"Murmansk; largest city above the Arctic Circle; major Barents Sea port, Russia",https://en.wikipedia.org/wiki/Murmansk,HIGH,"City coordinate (Wikipedia)"
East_Anglia_RAF_bases,52.4739,0.5294,"Representative centroid of the East Anglia RAF cluster (Marham, Lakenheath, Mildenhall)",https://en.wikipedia.org/wiki/RAF_Marham; https://en.wikipedia.org/wiki/RAF_Lakenheath; https://en.wikipedia.org/wiki/RAF_Mildenhall,CHECK,"DERIVED: arithmetic mean of the three sourced station coordinates; method stated — not a real airfield location"
UK_territorial_waters,,,"UK territorial sea: 12 nautical miles from baselines per Territorial Sea Act 1987 s.1; definition note only, no centroid",https://www.legislation.gov.uk/ukpga/1987/49/section/1; https://www.legislation.gov.uk/uksi/2014/1353/contents,CHECK,"DEFINITION NOTE ONLY per issue spec — no single defensible centroid exists for a non-contiguous zone; see exceptions"
North_Atlantic_rendezvous,70.6191,-0.7178,"Representative staging point for Northern Fleet group transiting Severomorsk toward GIUK; Norwegian Sea",https://en.wikipedia.org/wiki/Severomorsk; https://en.wikipedia.org/wiki/Kulusuk; https://www.wikidata.org/wiki/Q106896,CHECK,"DERIVED: great-circle midpoint Severomorsk — GIUK Greenland-Iceland reference; method stated; scenario-defined area, not a charted feature"
GIUK_gap,63.4556,-15.0178,"GIUK gap overall centroid; Greenland-Iceland-UK naval chokepoint, North Atlantic",https://en.wikipedia.org/wiki/GIUK_gap; https://en.wikipedia.org/wiki/Kulusuk; https://www.wikidata.org/wiki/Q106896; https://www.wikidata.org/wiki/Q817118; https://en.wikipedia.org/wiki/Faroe_Islands; https://en.wikipedia.org/wiki/Shetland,CHECK,"DERIVED: mean of the three reference midpoints below; method stated"
GIUK_ref_Greenland_Iceland,65.9852,-30.2309,"GIUK reference point: Denmark Strait between Greenland and Iceland",https://en.wikipedia.org/wiki/Kulusuk; https://www.wikidata.org/wiki/Q106896,CHECK,"DERIVED: great-circle midpoint Kulusuk (SE Greenland) — Isafjordur (Westfjords, Iceland); method stated"
GIUK_ref_Iceland_Faroes,63.1875,-10.8363,"GIUK reference point: strait between Iceland and the Faroe Islands",https://www.wikidata.org/wiki/Q817118; https://en.wikipedia.org/wiki/Faroe_Islands,CHECK,"DERIVED: great-circle midpoint Hofn (SE Iceland) — Faroe Islands article centroid; method stated"
GIUK_ref_Faroes_Shetland,61.1940,-3.9863,"GIUK reference point: Faroe-Shetland Channel between Faroes and Shetland",https://en.wikipedia.org/wiki/Faroe_Islands; https://en.wikipedia.org/wiki/Shetland,CHECK,"DERIVED: great-circle midpoint Faroe Islands article centroid — Shetland article centroid; method stated"
```

## Method notes (derived entries)

All derived points use sourced endpoint coordinates; no precision invented beyond sources. Great-circle midpoints use the standard spherical midpoint formula (Bx/By method); reproducible arithmetic in `compute_derived.py` (same folder).

- **GIUK_ref_Greenland_Iceland** (65.9852, -30.2309): midpoint of Kulusuk, SE Greenland (65.5753, -37.1833 [37]) and Ísafjörður, Westfjords, Iceland (66.0738, -23.1417 [38]) — spans the Denmark Strait.
- **GIUK_ref_Iceland_Faroes** (63.1875, -10.8363): midpoint of Höfn, SE Iceland (64.2500, -15.2167 [39]) and the Faroe Islands article centroid (62.0000, -6.7833 [40]).
- **GIUK_ref_Faroes_Shetland** (61.1940, -3.9863): midpoint of the Faroe Islands centroid [40] and the Shetland article centroid (60.3333, -1.3333 [41]) — spans the Faroe–Shetland Channel.
- **GIUK_gap** (63.4556, -15.0178): arithmetic mean of the three reference midpoints above.
- **North_Atlantic_rendezvous** (70.6191, -0.7178): great-circle midpoint of Severomorsk (69.0667, 33.4167 [31]) and GIUK_ref_Greenland_Iceland — lies on the Northern Fleet transit corridor in the Norwegian Sea, consistent with `initial_conditions.yaml` ("North Atlantic rendezvous point, moving southwest toward UK").
- **East_Anglia_RAF_bases** (52.4739, 0.5294): arithmetic mean of RAF Marham (52.6483, 0.5506 [9]), RAF Lakenheath (52.4083, 0.5567 [33]), RAF Mildenhall (52.3650, 0.4808 [34]).

## Exceptions list

1. **UK_territorial_waters — no centroid supplied (by design).** The issue asks for a "definition note only." The UK territorial sea is a non-contiguous 12 nm band around Great Britain, Northern Ireland, and numerous islands; any single centroid would be invented precision. Definition sourced to Territorial Sea Act 1987 s.1 (12 nm from baselines) [35] with the 2014 baseline Order [36]. If the globe needs a renderable stand-in, that is a design decision for the engineering loop — recommend deriving it from a published UK territorial-sea GIS boundary rather than a hand point.
2. **St Fergus gas terminal** — coordinate is St Fergus village (57.5583, -1.8364 [23]); the terminal itself sits on the coast roughly 0.5–1 km east. Village-level precision is adequate for globe plotting but flagged medium confidence; no authoritative page publishing terminal coordinates was found (Wikipedia floor used).
3. **All seven derived points are CHECK/low by construction** — they are computed, not sourced facts. Endpoint coordinates are sourced; methods stated above.
4. **North_Atlantic_rendezvous** is a scenario-defined staging area, not a charted feature. If the red doctrine legs in PR #69 planning assume a different staging geometry, this point should be re-derived to match.
5. **Official MOD pages confirm identity, not coordinates.** RAF/RN station pages (verified live 2026-08-28/29) carry addresses and roles but no lat/lon; all coordinates come from Wikipedia/Wikidata — the issue's stated floor. No conflicts >0.01° found between Wikipedia article coordinates and Wikidata where both exist.
6. **drax.com returned 403** to automated fetch; Drax coordinate sourced to Wikipedia only (still high — unambiguous single site) [22].
7. **Orkney Islands (Scapa Flow)** — the issue names the island group but the scenario uses the anchorage; coordinate is Scapa Flow itself (58.9000, -3.0500 [28]). If an Orkney-Islands-centroid entry is also needed for the "12 nm off Orkney" inject geometry, that is a one-line addition.

## Sources

1. https://en.wikipedia.org/wiki/Whitehall
2. https://www.royalnavy.mod.uk/locations-and-operations/bases-and-stations/hmnb-portsmouth
3. https://en.wikipedia.org/wiki/HMNB_Portsmouth
4. https://www.royalnavy.mod.uk/locations-and-operations/bases-and-stations/hmnb-devonport
5. https://en.wikipedia.org/wiki/HMNB_Devonport
6. https://www.royalnavy.mod.uk/locations-and-operations/bases-and-stations/hmnb-clyde
7. https://en.wikipedia.org/wiki/HMNB_Clyde
8. https://www.raf.mod.uk/our-organisation/stations/raf-marham/
9. https://en.wikipedia.org/wiki/RAF_Marham
10. https://www.royalnavy.mod.uk/locations-and-operations/bases-and-stations/rnas-yeovilton
11. https://en.wikipedia.org/wiki/RNAS_Yeovilton
12. https://www.raf.mod.uk/our-organisation/stations/raf-lossiemouth/
13. https://en.wikipedia.org/wiki/RAF_Lossiemouth
14. https://www.raf.mod.uk/our-organisation/stations/raf-coningsby/
15. https://en.wikipedia.org/wiki/RAF_Coningsby
16. https://www.raf.mod.uk/our-organisation/stations/raf-fylingdales/
17. https://en.wikipedia.org/wiki/RAF_Fylingdales
18. https://www.gov.uk/government/groups/the-permanent-joint-headquarters
19. https://en.wikipedia.org/wiki/Northwood_Headquarters
20. https://www.gchq.gov.uk/
21. https://en.wikipedia.org/wiki/GCHQ
22. https://en.wikipedia.org/wiki/Drax_Power_Station
23. https://en.wikipedia.org/wiki/St_Fergus
24. https://www.heathrow.com/
25. https://en.wikipedia.org/wiki/Heathrow_Airport
26. https://en.wikipedia.org/wiki/Oxford_Circus
27. https://www.wikidata.org/wiki/Q1996213
28. https://en.wikipedia.org/wiki/Scapa_Flow
29. https://en.wikipedia.org/wiki/Aberdeen
30. https://en.wikipedia.org/wiki/Scrabster
31. https://en.wikipedia.org/wiki/Severomorsk
32. https://en.wikipedia.org/wiki/Murmansk
33. https://en.wikipedia.org/wiki/RAF_Lakenheath
34. https://en.wikipedia.org/wiki/RAF_Mildenhall
35. https://www.legislation.gov.uk/ukpga/1987/49/section/1
36. https://www.legislation.gov.uk/uksi/2014/1353/contents
37. https://en.wikipedia.org/wiki/Kulusuk
38. https://www.wikidata.org/wiki/Q106896
39. https://www.wikidata.org/wiki/Q817118
40. https://en.wikipedia.org/wiki/Faroe_Islands
41. https://en.wikipedia.org/wiki/Shetland
42. https://en.wikipedia.org/wiki/GIUK_gap
