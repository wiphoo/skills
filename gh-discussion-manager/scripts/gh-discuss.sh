#!/bin/bash
# gh-discussion-manager helper
# Usage: ./scripts/gh-discuss.sh <pr>
# Review-thread resolution state exists only in the GraphQL API.
repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Unresolved threads for PR $1:"
gh api graphql \
  -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){
    reviewThreads(first:100){nodes{id isResolved comments(first:1){nodes{databaseId author{login} body}}}}}}}' \
  -f o="${repo%/*}" -f r="${repo#*/}" -F n="$1" \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)
        | {thread:.id, id:.comments.nodes[0].databaseId, user:.comments.nodes[0].author.login, body:.comments.nodes[0].body[:80]}'
