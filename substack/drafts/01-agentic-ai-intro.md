# Draft: Building an Agentic AI Podcast Pipeline (Without Outsourcing the Story)

*Working title: A technical build log for automating the boring parts of podcast production.*

## Before we start: what this is **not**

If you’ve felt uneasy about “AI in podcasts,” you’re not alone. A lot of people hear *AI podcast* and assume it means automated research, AI-written scripts, or synthetic voices. That’s not what we’re doing. Not even close.

The Maple History podcast is built the old-fashioned way:

- Christina (our host) hand-writes her research notes and types her scripts by hand, without any AI summarization.
- She spends hours with physical books, digital archives, and academic papers.
- The research is human, careful, and personal.

We believe historical storytelling is *is in the edit*, so AI can never replace what a human can do.

## So why AI at all?

Because there’s a difference between **craft** and **chores**.

Craft is what makes the show worth listening to: the research, the perspective, the conversations, the editing decisions that shape meaning and pacing.

Chores are the repetitive tasks that *steal time from craft*:

- Normalizing audio levels
- Isolating speakers
- Removing long pauses
- Detecting obvious mouth noise or breathing gaps

These are mechanical tasks that take real time — and they keep us away from the most valuable work: telling well-researched stories about the history of Canada.

That’s where we’re using AI. **Not to create the story, but to clear the runway.**

## A note on how AI is used in this write-up

The podcast content itself uses no AI for writing or research. However, I *am* using AI to help document the technical work you’ll see in these posts, including summarizing changes and clarifying what each automation step does. This is a build log, and I want it to be as clear as possible.

## Who this is for (and who it’s not)

This is for technical readers who want to see how an agentic AI system is designed and built in the open. If you want a plug-and-play, consumer-friendly shortcut, this won’t be it.

We’re going to outline every step we take to automate the *existing* manual Maple History workflow by building an agentic AI solution using OpenAI’s Codex. The code is public on GitHub and licensed under GPL 3.0 so anyone can learn from it, fork it, or adapt it to their own production flow as long as they have the required technical skills:

- Repo: https://github.com/seetheday/podcast-automation
- License: GPL 3.0

## The goal: an agentic workflow that respects authenticity

This project isn’t about replacing people. It’s about building a reliable, step-by-step automation pipeline that supports *human* creativity.

I’m documenting the build publicly for two reasons:

1. To demonstrate how to build an agentic AI system that solves a real-world production problem.
2. To promote Maple History and show how much care goes into the work behind each episode.

## The planning-first approach

This project starts with a principle: **automation has to be planned, staged, and testable** — or it will quietly degrade quality.

So the plan is structured as a series of milestones that mirror the real production flow:

1. **Ingest** raw recordings and validate that expected files exist.
2. **Edit** and align tracks in a repeatable, deterministic way.
3. **Export** and validate final renders (duration, loudness, peak).
4. **Transcript + Notes** generation with review hooks.
5. **Artwork + Publish** automation tied to metadata.

Each stage is designed as a runnable CLI with test fixtures so we can verify results before we trust them in production.

## Work done so far (foundation)

The initial ingest stage is done:

- It catalogs raw WAVs and checks for matching MP3 renders.
- It supports simple configuration overrides.
- It includes tests against sample inputs so the results stay predictable.

This is intentional: if the foundation isn’t reliable, nothing downstream is.

## What comes next

Next is **editing automation** — and this is where we’ll be most conservative. The goal isn’t to replace the editor. It’s to handle the repetitive, low-value edits so the human can focus on narrative pacing and clarity.

In other words: *make the editor faster, not replace them.*

## If you’re curious or skeptical — I get it

We’re not trying to automate the soul of the show. We’re trying to free up time to invest more of it.

If that resonates, I’ll be sharing progress as we build each stage. If you want to follow along (or help), I’d love to hear from you.

And if you’re here for the stories: subscribe to Maple History. We’re doing this to make the show stronger — not cheaper.
