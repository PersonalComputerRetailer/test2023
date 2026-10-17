---
name: publish-blog-post
description: Prepare and publish an article on Will's Hugo blog, from a supplied draft or Markdown file through summary, build, GitHub Pages deployment, and live verification. Use when the user provides an article for this blog to post; do not deploy for review-only, draft-only, or local-only requests.
---

# Publish a blog post

This repository is the source for https://willscyber.net/. A request to post an article here includes publishing it, unless the user specifies otherwise. Follow the current repository instructions and deployment configuration; do not assume they have remained unchanged.

## Prepare the article

1. Read the complete supplied text or file, including any referenced local images. Preserve the original file, language, technical commands, warnings, links, and meaning. Publish one post per supplied article; don't create translations unless requested. If essential content or an asset is missing, ask the user rather than inventing it.
2. Inspect `git status`, existing post conventions in `content/posts/`, and the publishing workflow. Preserve unrelated changes, including theme submodules and anything already staged. Don't overwrite an existing post or generated file with user changes.
3. Create a uniquely named Markdown file under `content/posts/`. Use the supplied title and metadata when present; otherwise choose an appropriate title and stable, descriptive slug. Follow the site's TOML front matter conventions: publication date in the user's local date unless specified, `draft = false`, `author = ["Will"]`, and suitable tags and categories. Respect an explicitly requested future date or draft status. Do not duplicate an existing front matter block.
4. Write a concise summary in the article's language before the body. Following the site's convention, end the summary with `...<!--more-->` and then `<div style="clear:both;"></div>`. Keep the article body after the separator so list pages show only the summary. Preserve an existing suitable summary and separator rather than adding duplicates.
5. Ensure referenced assets will be available in the deployed site and links resolve. Copy needed user-provided assets into an appropriate site location without changing the originals; do not invent missing assets.

## Build and publish

1. Check for pre-existing changes to tracked generated files before building: `hugo --minify` writes to `public/`. If a build would overwrite unrelated work, stop and ask how to preserve it. Build the site, check the resulting diff, and verify that the relevant list page shows the summary only and the individual post contains the full body. Check pagination when a post isn't on the first page.
2. For an authorized publication, inspect the current branch, remote and `.github/workflows/hugo.yml`; this site currently deploys pushes to `hugo` via GitHub Actions. Stage only the new or changed post, its assets, and its verified generated `public/` changes. Inspect the staged diff before committing; never include unrelated pre-existing staged changes or theme modifications. Commit and push the intended branch without force. If the push is rejected or conflicts with remote or local changes, stop and report the blocker rather than overriding them.
3. Check the GitHub Actions run for the exact pushed commit, then verify the live post URL and the appropriate posts-list page at https://willscyber.net/posts/. Confirm the list contains the summary without the full body. A cache-busting query parameter can distinguish stale cache from a failed deployment. Do not claim the post is live until verified; report a deployment failure, delay, or inaccessible site accurately.
4. Tell the user the live article link and the outcome. If only a draft or local preparation was requested, report that it was not published.
