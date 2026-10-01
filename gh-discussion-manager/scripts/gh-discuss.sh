#!/bin/bash
# gh-discussion-manager helper
# Usage: ./scripts/gh-discuss.sh <pr> [command]
echo "Unresolved threads for PR $1:"
gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/pulls/$1/comments --jq '.[] | select(.unresolved==true) | {id:.id, user:.user.login, body:.body[:80]}'
