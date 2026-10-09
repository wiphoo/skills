#!/bin/bash
# gh-discussion-manager helper
# Usage: ./scripts/gh-discuss.sh <pr>
# Review-thread resolution state exists only in the GraphQL API; --paginate follows pageInfo/$endCursor.
repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Unresolved threads for PR $1:"
gh api graphql --paginate \
  -f query='query($o:String!,$r:String!,$n:Int!,$endCursor:String){repository(owner:$o,name:$r){pullRequest(number:$n){
    reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor}
      nodes{id isResolved root:comments(first:1){nodes{databaseId author{login} body}} latest:comments(last:1){nodes{databaseId createdAt author{login} body}}}}}}}' \
  -f o="${repo%/*}" -f r="${repo#*/}" -F n="$1" \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)
        | {thread:.id, id:.root.nodes[0].databaseId, user:.root.nodes[0].author.login, body:.root.nodes[0].body[:80],
           latest:{id:.latest.nodes[0].databaseId, user:.latest.nodes[0].author.login, at:.latest.nodes[0].createdAt, body:.latest.nodes[0].body[:80]}}'
