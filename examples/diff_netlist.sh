#!/usr/bin/env bash

GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}** Compare MergedQC.rpt ***${NC}"
echo -e "${GREEN}===========================${NC}"

diff --color MergedQC.rpt ../tests/data/expected/MergedQC.rpt

echo -e "${GREEN}*** Compare MergedQC.summary.rpt ***${NC}"
echo -e "${GREEN}=====================================${NC}"

diff --color MergedQC.summary.rpt ../tests/data/expected/MergedQC.summary.rpt
