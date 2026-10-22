#!/usr/bin/env bash
# Headless dry runs of the two recorded demos (thickness, defects) with skill v4 and guarded iopic-Bond.
# Each run works in its own copy of the demo data; transcripts go to the scratchpad, not the demo folder.
SP="/c/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/submission/demo"
export PATH="/c/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/.venv/Scripts:$PATH"

P_THICK="Here are Raman spectra of six different CrSBr flakes, all measured with the same settings (532 nm, room temperature). Tell me what's different between them."
P_DEF="Here are Raman spectra of a 4-layer CrSBr flake before and after three processing steps, each measured with the laser polarised along the a and the b axis. What changed, and is the material still good for a device?"

run() {  # $1 name, $2 prompt
  cd "/c/Users/sadit/raman-demo/dryrun3/$1" || exit 1
  echo "[$(date +%T)] start $1"
  timeout 2700 claude -p "$2" --model claude-sonnet-5-5 \
    --setting-sources project \
    --plugin-dir "$SP/plugin-v4" \
    --strict-mcp-config --mcp-config "$SP/config/demo-mcp.json" \
    --settings "$SP/config/demo-settings.json" \
    --permission-mode acceptEdits \
    --allowedTools Bash Read Write Edit Glob Grep Skill "mcp__iopic-bond__*" \
    --disallowedTools WebSearch WebFetch Agent Task \
    --output-format stream-json --verbose > "$SP/dryruns/dryrun3-$1.jsonl" 2> "$SP/dryruns/dryrun3-$1.err"
  echo "[$(date +%T)] end $1 exit $?"
}
run thickness "$P_THICK"
run defects "$P_DEF"
