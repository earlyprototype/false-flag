# Diplomatic System - Quick Start Guide

## 🎯 What Is This?

You can now **talk to foreign leaders and diplomats** during the crisis! Negotiate with the US President, coordinate with France, or even engage with the Russian Ambassador.

## 🎮 How To Use

### During Discussion Phase:

1. **Check who's available**: Type `/menu`
2. **Call a country**: Type `/call <country>`
3. **Have a conversation**: Negotiate, request support, coordinate strategy
4. **End when ready**: Type `/end` or let the conversation conclude naturally

### Example:
```
>: /call us

Connecting to US...

US President: Prime Minister, I'm hearing concerning reports. 
What's your play here?

Your response: We need US support for Article 5. Russia has 
deployed 15 submarines and we're facing an unprecedented threat.

US President: Article 5 requires consensus. What assurances can 
you give us about UK readiness? We need to know you're not going 
to drag us into a war you can't win.

Your response: /end

[Conversation ends]

Diplomatic Outcome: SUCCESS
Alliance Cohesion: +10
```

## 📊 Access Levels

Your **Alliance Cohesion** determines who you can reach:

| Cohesion | Who You Can Talk To |
|----------|---------------------|
| **65+** | ★ US President, French President, German Chancellor |
| **50-64** | ★ French President, Polish President<br>○ US NSA, German FM |
| **40-49** | ★ Ukrainian President, Polish President<br>○ Most diplomats |
| **30-39** | ○ US NSA, German FM, others |
| **<30** | ○ Limited diplomat access only |

**★ = Leader** (President, Chancellor, etc.)  
**○ = Diplomat** (Foreign Minister, NSA, Ambassador)

## 🌍 Available Countries

1. **US** - Transactional, wants to know "what's in it for us?"
2. **France** - Intellectual, concerned about European sovereignty
3. **Germany** - Cautious, process-driven, avoids escalation
4. **Poland** - Hawkish, anti-Russian, eager to support
5. **Russia** - Dismissive, threatening (always Ambassador, never Putin)
6. **Ukraine** - Experienced with Russian tactics, urgent
7. **Ireland** - Neutral, awkward, "Have you tried... diplomacy?" 😂

## 💡 Tips

### Good Conversations:
- ✅ Reassure allies about coordination
- ✅ Request specific support (e.g., "Can you deploy THAAD batteries?")
- ✅ Explain your strategic rationale
- ✅ Respect each country's concerns (e.g., don't ask Ireland for troops)

### Bad Conversations:
- ❌ Making demands without offering anything
- ❌ Ignoring their concerns
- ❌ Being vague or evasive
- ❌ Antagonizing them

### Country-Specific:
- **US**: Be specific about what you need and what you'll contribute
- **France**: Acknowledge European leadership and sovereignty
- **Germany**: Emphasize process, consensus, and de-escalation
- **Poland**: They're eager to help; easy ally
- **Russia**: Don't expect cooperation; avoid escalation
- **Ukraine**: They have valuable intelligence; listen to their warnings
- **Ireland**: Respect their neutrality; ask for humanitarian support only

## 🎭 Mandatory Encounters

Some turns will have **mandatory diplomatic encounters** (e.g., US President calls you). These happen automatically during the briefing phase. You **must** complete them before proceeding.

## 📈 Impact on Game

Successful diplomacy:
- **Increases Alliance Cohesion** (+5 to +15)
- **Unlocks better access** (diplomats → leaders)
- **Improves future injects** (LLM considers diplomatic history)

Failed diplomacy:
- **Decreases Alliance Cohesion** (-5 to -15)
- **Loses access** (leaders → diplomats → none)
- **Triggers negative consequences** in future turns

## 🚀 Try It Now!

Start a game and when you reach the discussion phase:

1. Type `/menu` to see who's available
2. Type `/call poland` (easiest ally to practice with)
3. Have a conversation
4. See how it affects your Alliance Cohesion

**Have fun making ridiculous stereotype images of national leaders!** 😂

---

*For detailed documentation, see `docs/DIPLOMATIC_SYSTEM.md`*

