#!/usr/bin/env nu
# merge-config.nu
# Pulls global kilocode / opencode configuration into this repo.
# Run from the repo root:  nu scripts/merge-config.nu

def main [] {
    let repo_root = ($env.FILE_PWD | path dirname)
    let kilocode_src  = ($env.HOME | path join ".kilocode")
    let opencode_src  = ($env.HOME | path join ".config" "kilo" "opencode.json")

    # ── opencode.json ────────────────────────────────────────────────────────
    let opencode_dst = ($repo_root | path join "opencode.json")
    if ($opencode_src | path exists) {
        print $"Copying opencode.json  →  ($opencode_dst)"
        cp $opencode_src $opencode_dst
    } else {
        print "opencode.json not found in ~/.config/kilo — skipping."
    }

    # ── KiloCode skills ──────────────────────────────────────────────────────
    let skills_src = ($kilocode_src | path join "skills")
    let skills_dst = ($repo_root | path join ".kilocode" "skills")
    if ($skills_src | path exists) {
        print $"Syncing skills/  →  ($skills_dst)"
        mkdir $skills_dst
        cp -r ($skills_src | path join "*") $skills_dst
    } else {
        print "No skills/ directory found in ~/.kilocode — skipping."
    }

    # ── MCP settings ─────────────────────────────────────────────────────────
    let mcp_src = ($kilocode_src | path join "cli" "global" "settings" "mcp_settings.json")
    let mcp_dst = ($repo_root | path join ".kilocode" "cli" "global" "settings" "mcp_settings.json")
    if ($mcp_src | path exists) {
        print $"Copying mcp_settings.json  →  ($mcp_dst)"
        mkdir ($mcp_dst | path dirname)
        cp $mcp_src $mcp_dst
    } else {
        print "mcp_settings.json not found — skipping."
    }

    # ── Custom modes ─────────────────────────────────────────────────────────
    let modes_src = ($kilocode_src | path join "cli" "global" "settings" "custom_modes.yaml")
    let modes_dst = ($repo_root | path join ".kilocode" "cli" "global" "settings" "custom_modes.yaml")
    if ($modes_src | path exists) {
        print $"Copying custom_modes.yaml  →  ($modes_dst)"
        mkdir ($modes_dst | path dirname)
        cp $modes_src $modes_dst
    } else {
        print "custom_modes.yaml not found — skipping."
    }

    print ""
    print "Done. Review changes with: git diff"
    print ""
    print "NOTE: The following files are intentionally NOT pulled (sensitive/runtime data):"
    print "  ~/.kilocode/cli/config.json          (contains auth token)"
    print "  ~/.kilocode/cli/global/global-state.json  (task history / runtime state)"
    print "  ~/.kilocode/cli/global/secrets.json  (secrets)"
    print "  ~/.kilocode/cli/global/cache|tasks|workspaces/"
}
