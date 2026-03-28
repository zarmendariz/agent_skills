#!/usr/bin/env nu

# Push skills from the local repo to the global Kilo configuration.
# Skills in ~/.kilocode/skills/ will be overwritten if they already exist.

def main [
    --dry-run (-n)  # Show what would be copied without making changes
    --force (-f)    # Skip confirmation prompt when overwriting existing skills
] {
    let repo_skills_dir = ($env.FILE_PWD | path dirname | path join ".kilocode" "skills")
    let global_skills_dir = ($env.HOME | path join ".kilocode" "skills")

    if not ($repo_skills_dir | path exists) {
        error make {msg: $"Source skills directory not found: ($repo_skills_dir)"}
    }

    let skills = (ls $repo_skills_dir | where type == dir | get name | each { |p| $p | path basename })

    if ($skills | length) == 0 {
        print "No skills found in the source directory."
        return
    }

    print $"Source:      ($repo_skills_dir)"
    print $"Destination: ($global_skills_dir)"
    print ""

    # Determine which skills already exist at the destination
    let existing = if ($global_skills_dir | path exists) {
        $skills | where { |s| ($global_skills_dir | path join $s) | path exists }
    } else {
        []
    }

    print $"Skills to push: ($skills | str join ', ')"

    if ($existing | length) > 0 {
        print $"Will overwrite: ($existing | str join ', ')"
    }

    if $dry_run {
        print ""
        print "[dry-run] No changes made."
        return
    }

    if ($existing | length) > 0 and not $force {
        print ""
        let answer = (input "Overwrite existing skills? [y/N] ")
        if ($answer | str downcase) not-in ["y", "yes"] {
            print "Aborted."
            return
        }
    }

    # Ensure destination directory exists
    if not ($global_skills_dir | path exists) {
        mkdir $global_skills_dir
        print $"Created directory: ($global_skills_dir)"
    }

    # Copy each skill directory
    for skill in $skills {
        let src = ($repo_skills_dir | path join $skill)
        let dst = ($global_skills_dir | path join $skill)

        if ($dst | path exists) {
            # Remove old version first so cp -r doesn't nest directories
            rm -rf $dst
        }

        ^cp -r $src $dst

        let result = $env.LAST_EXIT_CODE
        if $result != 0 {
            print $"  [FAILED] ($skill)"
        } else {
            print $"  [OK]     ($skill)"
        }
    }

    print ""
    print "Done."
}
