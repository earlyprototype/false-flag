# Convai

Convai (convai.com) is a hosted conversational-avatar service: it supplies
embodiment — character bodies, voices and lip-sync — for avatars whose words
come either from text you feed it or from its own cloud models. It supplies
embodiment, not game logic, and it is cloud-dependent at runtime.

*Service facts here are general knowledge, not repo-verified: the repo
contains no Convai integration code yet. The project-role rulings below are
recorded in issues #127 and #128.*

## Role in this project: embodiment, never the brain

The game engine on the laptop stays the single source of advisor content.
Convai gives the advisors bodies, voices and lip-sync in the VR room; it
never supplies game logic. Two operating modes are defined:

- **Puppet mode.** The game emits speak-tags and the avatars voice those
  lines verbatim — zero Convai thinking. The avatar is a mouth for text the
  engine already produced.
- **Conversational mode.** The user talks to an avatar directly and Convai's
  own model answers, from a per-turn context package pushed from game state.
  That model is a second brain, kept on a leash by the re-target: each turn
  the avatar's context is re-pointed at current game state, so its answers
  cannot drift from the campaign the engine is running.

In both modes authority stays with the engine. Conversational mode delegates
only the phrasing of answers, inside the context handed over that turn.

## SDK facts

- The **Unity SDK is first-class**: embodied, voiced, lip-synced advisors
  largely out of the box (recorded in #127, option A).
- A **Web SDK exists**. On the WebXR route (#127, option B) it can carry
  voice and conversation, but avatar embodiment is hand-rolled on the web
  route — the out-of-the-box bodies belong to the Unity SDK.

## The cloud dependency

Convai is a hosted service: no internet, no avatar voices or answers.
**Venue internet is therefore a live-demo risk.** Fallback options for
scripted moments: pre-generated lines (audio rendered ahead of time) or
local voices (laptop/on-device TTS), so a scripted sequence can still run
with the internet down.

## Decision state

Which route carries Convai — Unity SDK or Web SDK — is part of open decision
#127. No Convai code exists in the repo yet, and nothing about the service's
pricing or account state is recorded in the repo.
