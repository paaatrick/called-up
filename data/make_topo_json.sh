#!/bin/bash

rm -f north_am.json
ogr2ogr \
  -f GeoJSON \
  -where "ADM0_A3 IN ('USA')" \
  -clipsrc -125 23 -64 53 \
  north_am.json \
  raw/ne_10m_admin_1_states_provinces_lakes.shp

topojson \
  -o north_am_topo.json \
  --id-property iso_a2 \
  --properties name \
  -q 1e4 \
  --simplify-proportion 0.10 \
  -- \
  north_am.json
