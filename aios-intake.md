# AIS-OS Intake

This is the source-of-truth file for your AIOS. Fill it in by typing, voice-pasting (Wispr Flow / OS dictation), or running `/onboard` for a guided conversation. Whichever mode, this file is what `/onboard` reads to scaffold your Day-1 setup.

**Hard cap: 7 questions.** Each answerable in under 60 seconds. Don't overthink — you can edit and re-run `/onboard` any time.

---

## Q1 — Who are you, what do you sell, who do you sell it to?

Identity, offer, ICP. One paragraph each is fine.

```
I am Banks Dada, owner of webawesome.co.uk

Offer: a UK-based digital agency providing digital services and automation to small businesses locally and globally. I also serve as a business analysis mentor via mentoringba, which includes coaching, job transition to business analysis, and on-the-job support.

ICP: We sell to people wanting to change career to business analysis. We also support busineses with digital products and ai automations, hosting services and more
```

---

## Q2 — Paste 1-2 things you've written recently. Don't edit them.

An email, a LinkedIn post, a DM, a doc — anything that sounds like you when you're not trying. **Paste verbatim.** Do not type these mid-conversation with Claude — chat-shaped samples are worse than no samples (voice contamination).

```
Correct me if I am wrong

Does being versatile or experienced with jira make me a jira business analyst?

I see a lot of newly crafted roles with awesome job description that constantly make me think hard!

Ai is a tool. There are thousands and thousands of platforms and agents doing and providing multiple services such as text, embedding, audio and video

That description right there makes things more broad and in the coming future I am sure we will have titles attached to those capabilities

I use ai a lot and it is a great tool for speeding up work! It’s not perfect yet but getting better everyday

Automation and agentic workforce is here to stay and that is the base of my moan

And er.. I am #opentowork
```

```
[Sample 2 — paste raw]
```

---

## Q3 — What are your 2-3 biggest priorities for the next 90 days?

Quarterly priorities. Not yearly aspirations. Things that, if not done by July, would make you say "I wasted Q2."

```
1. Solve more problems for clients (make about £10,000)
2. Get more clients
3. Build more usable automations and digital products
```

---

## Q4 — Where does revenue actually land, and where is it tracked?

Multiple answers OK. Stripe? Skool? GoHighLevel? QuickBooks? A spreadsheet?

```
I have a Stripe account I never use. Also receive funds via my business account - Monzo which is connected to Stripe.
```

---

## Q5 — Where do you talk to customers, your team, and the outside world day-to-day?

Email (which one — Gmail / Outlook)? Slack? Teams? DMs (Skool / Discord / iMessage)? Phone?

```
Gmail and my custom email info@webawesome.co.uk but Gmail more
```

---

## Q6 — Where do meeting recordings, notes, and important docs live?

Granola? Otter? Fireflies? Google Drive? Notion? Dropbox? A folder on your desktop you keep meaning to organize?

```
Google Drive (but never recorded meetings in the past). Also have a TidyCal account for booking meetings.
```

---

## Q7 — What's the one task that eats your week, and where do you currently track work?

The single biggest time-suck or recurring drudgery. Plus where tasks/projects live (ClickUp / Asana / Linear / Notion / a notebook).

```
Finding clients who will pay for my services. Have a CRM but never use it.
```

---

When this file is filled, run `/onboard` (or re-run it) and the wizard will scaffold your Day-1 file set: `context/`, `references/voice.md`, populated `connections.md`, and a filled `CLAUDE.md`.
