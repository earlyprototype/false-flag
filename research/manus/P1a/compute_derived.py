#!/usr/bin/env python3
"""Compute derived gazetteer points with stated methods.
All inputs are sourced coordinates recorded in the accompanying gazetteer.md
dossier (Wikipedia/Wikidata values fetched 2026-08-28/29).
Great-circle midpoint formula: standard spherical midpoint (B x/y method).
"""
import math

def midpoint(lat1, lon1, lat2, lon2):
    """Great-circle midpoint between two points (degrees)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    l1 = math.radians(lon1)
    dl = math.radians(lon2 - lon1)
    bx = math.cos(p2) * math.cos(dl)
    by = math.cos(p2) * math.sin(dl)
    p3 = math.atan2(math.sin(p1) + math.sin(p2), math.sqrt((math.cos(p1) + bx) ** 2 + by * by))
    l3 = l1 + math.atan2(by, math.cos(p1) + bx)
    return math.degrees(p3), (math.degrees(l3) + 540) % 360 - 180

# --- Sourced endpoints ---
GREENLAND_EAST = (65.575278, -37.183333)   # Kulusuk, SE Greenland — en.wikipedia.org/wiki/Kulusuk
ICELAND_WESTFJORDS = (66.073778, -23.141719)  # Ísafjörður, Westfjords — Wikidata Q106896 P625
ICELAND_SE = (64.25, -15.216667)           # Höfn, SE Iceland — Wikidata Q817118 P625
FAROES = (62.0, -6.783333)                 # Faroe Islands article centroid — en.wikipedia.org/wiki/Faroe_Islands
SHETLAND = (60.333333, -1.333333)          # Shetland article centroid — en.wikipedia.org/wiki/Shetland
SEVEROMORSK = (69.066667, 33.416667)       # en.wikipedia.org/wiki/Severomorsk

# --- GIUK reference points (per issue #70 spec) ---
gi = midpoint(*GREENLAND_EAST, *ICELAND_WESTFJORDS)
print(f"GIUK_ref_Greenland_Iceland  {gi[0]:.4f}  {gi[1]:.4f}   midpoint(Kulusuk GL, Isafjordur IS) — Denmark Strait")

ifar = midpoint(*ICELAND_SE, *FAROES)
print(f"GIUK_ref_Iceland_Faroes     {ifar[0]:.4f}  {ifar[1]:.4f}   midpoint(Hofn IS, Faroe Islands centroid)")

fs = midpoint(*FAROES, *SHETLAND)
print(f"GIUK_ref_Faroes_Shetland    {fs[0]:.4f}  {fs[1]:.4f}   midpoint(Faroe Islands centroid, Shetland centroid) — Faroe-Shetland Channel")

# GIUK gap overall centroid: mean of the three reference midpoints
clat = (gi[0] + ifar[0] + fs[0]) / 3
clon = (gi[1] + ifar[1] + fs[1]) / 3
print(f"GIUK_gap_centroid           {clat:.4f}  {clon:.4f}   mean of the three reference midpoints")

# North Atlantic rendezvous: scenario = Russian Northern Fleet transiting Severomorsk -> GIUK.
# Representative staging point: great-circle midpoint Severomorsk -> GIUK Greenland-Iceland ref
# (Norwegian Sea / NE Atlantic transit corridor).
rv = midpoint(*SEVEROMORSK, *gi)
print(f"North_Atlantic_rendezvous   {rv[0]:.4f}  {rv[1]:.4f}   midpoint(Severomorsk, GIUK Greenland-Iceland ref) — Norwegian Sea transit corridor")

# East Anglia RAF bases cluster centroid: mean of sourced coords for Marham, Lakenheath, Mildenhall
MARHAM = (52.648333, 0.550556)      # en.wikipedia.org/wiki/RAF_Marham
LAKENHEATH = (52.408333, 0.556667)  # en.wikipedia.org/wiki/RAF_Lakenheath
MILDENHALL = (52.365, 0.480833)     # en.wikipedia.org/wiki/RAF_Mildenhall
elat = (MARHAM[0] + LAKENHEATH[0] + MILDENHALL[0]) / 3
elon = (MARHAM[1] + LAKENHEATH[1] + MILDENHALL[1]) / 3
print(f"East_Anglia_RAF_bases       {elat:.4f}  {elon:.4f}   mean(RAF Marham, RAF Lakenheath, RAF Mildenhall)")
