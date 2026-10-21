---
name: content-system
description: Use when someone wants to plan, research, draft or schedule social posts from a repeatable system, says "content system", "viral hooks", "draft a post", "what should I post", or asks to run the research, brain, drafts pipeline. Adapted from Sabrina Ramonov's "Content Systems on Autopilot". Never publishes without explicit approval.
---

# Content system

Three stages: find proven hooks, add your own point of view, draft, then a human approves before anything is scheduled.

Source framework: Sabrina Ramonov, "Content Systems on Autopilot" (copied PDF in ~/Downloads). Adapted for the AIOS. The principles below are hers; the rules marked **AIOS rule** are ours.

## The core idea

Stop looking for another framework. Copy a proven viral hook, then add your own point of view and a real story. The hook earns the first three seconds; your POV makes the post yours.

## Before any post

1. **One platform.** Talking on camera: TikTok or Reels. Text or images: LinkedIn or Substack. For Banks, default to LinkedIn (matches the content bank).
2. **One topic.** The overlap of skills, interests and paying demand. Start narrow; widen later.
3. **Warm up new accounts first.** TikTok, Pinterest and X need 2-3 weeks; other platforms 1-2 weeks. Engage about 15 minutes a day in the app, and about 10 minutes after posting. Skip this for accounts that are already established.

## Folder layout

Per topic, under a project folder (for example `projects/<topic>/`):

```
research/   proven viral hooks, with stats and source URLs
brain/      your POV, stories, proof, audience, beliefs, voice (see content-brain-interview)
drafts/     posts in progress, one file per post
```

**AIOS rule:** every hook in `research/` carries its URL and the stat that made it viral. No URL, no hook.

## Pipeline

1. **Find hooks.** Collect 5 high-performing posts on the topic from the last 12 months (the source suggests Reels over 500k views; adjust the threshold to the platform). Save each hook, its stats and its URL to `research/`. If Apify is connected, use it; otherwise the user pastes or links examples.
2. **Build the brain.** Run the `content-brain-interview` skill once. It fills `brain/`. Re-run it when you have a new lesson or story.
3. **Draft.** Pick one relevant hook from `research/` and one story or opinion from `brain/`. Write three openings, then a full post for the chosen platform. Save to `drafts/` with the status `draft`.
4. **Approve.** Show the user the draft and the chosen opening. Do not move on without a yes.
5. **Schedule.** Only after explicit approval, and only if a scheduler is connected (Blotato in the source). Show the exact text and the exact time before scheduling. Mark the file `scheduled` with the time.

## Rules

- **Never publish or schedule without a yes on the exact text.** This matches the house rule that nothing external goes out unreviewed.
- **Invent nothing.** Stories and numbers come from `brain/` or from a cited source. If the brain is missing the story, ask; don't fill it.
- **Sources go in the first comment, not the post body** (the convention already used in `references/linkedin-content-bank.md`).
- **Copy the structure, not the words.** A viral hook is a pattern. Never paste a competitor's hook verbatim.
- **Stop when it turns to filler.** Daily cadence dies if posts stop saying something specific. One post that's true beats three that aren't.

## Output

Keep it short: the chosen hook, the three openings, the post, and one line on what's needed to approve it. Ask for approval; don't assume it.
