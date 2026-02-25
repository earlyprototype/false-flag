# Web UI Layout Design - Game Mechanics Mapping

## Game Structure Analysis

### Turn-Based Flow (4 Phases)
1. **BRIEFING** - Player receives intel/inject
2. **DISCUSSION** - Player asks questions, explores options
3. **DECISION** - Player commits to action
4. **ADJUDICATION** - Effects are applied, narrative outcome

### Available Commands During Discussion
```
/status      - Show metrics (escalation, stability, cohesion, casualties)
/menu        - Display all available commands
/advise      - Get input from all advisors at once
/resources   - Show UK military forces and stockpiles
/call [country] - Diplomatic encounter with foreign leader/diplomat
/decide      - Move to decision phase
/theme       - Change UI color theme
/save        - Save game
/quit        - Exit
```

### Metrics System
- Escalation Risk (0-100) - Higher = danger
- Domestic Stability (0-100) - Lower = civil unrest
- Alliance Cohesion (0-100) - Lower = NATO isolation
- Casualties (Military + Civilian)
- Influence (-10 to +10) - Political capital

---

## SCUMM-Style Web Layout (Indy Atlantis Adapted)

### Three-Panel Design

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  VIEWPORT AREA (60% height)                                  │
│  ─────────────────────────────────────────                  │
│  • Turn/Phase header                                          │
│  • Narrative/briefing text                                    │
│  • Advisor responses                                          │
│  • Diplomatic encounters                                      │
│  • Scrollable content area                                    │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│  COMMAND BAR (20% height)                                     │
│  ─────────────────────────────────────────                    │
│  [STATUS] [ADVISE] [RESOURCES] [DIPLOMACY]                   │
│  [DECIDE]  [THEME]   [SAVE]      [MENU]                      │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│  STATUS BAR (20% height)                                      │
│  ─────────────────────────────────────────                    │
│  ▲ Risk: 70  ■ Stability: 45  & Cohesion: 62  Turn: 3       │
│  [Progress bars] [Status badges] [Phase indicator]            │
└───────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown by Phase

### Phase 1: BRIEFING

**Viewport Area:**
```tsx
<SceneViewport>
  {/* Phase Header */}
  <PhaseHeader 
    turn={3} 
    phase="BRIEFING"
    style="scumm-panel-warm"
  />
  
  {/* Intel Channel Indicator */}
  <IntelChannel type="breaking" /> {/* or "briefing", "intel" */}
  
  {/* Narrative Text */}
  <NarrativeText 
    content={injectContent}
    typewriter={true}
    allowSkip={true}
  />
  
  {/* Effects Display */}
  <MetricChanges 
    changes={{
      escalation_risk: +10,
      domestic_stability: -5
    }}
  />
</SceneViewport>
```

**Command Bar:**
- All buttons DISABLED except `[CONTINUE]`
- Greyed out, non-interactive
- Only after briefing read: `[CONTINUE]` → Discussion Phase

**Status Bar:**
- Shows current metrics with NEW values highlighted
- Deltas displayed (+10, -5) in color (red/green)

---

### Phase 2: DISCUSSION (Primary Gameplay)

**Viewport Area:**
```tsx
<SceneViewport>
  <PhaseHeader 
    turn={3} 
    phase="DISCUSSION"
    hint="Ask advisors questions or use commands"
  />
  
  {/* Conversation History (Scrollable) */}
  <ConversationLog>
    {messages.map(msg => (
      <MessageBlock 
        key={msg.id}
        speaker={msg.speaker}
        content={msg.content}
        type={msg.type} // "player" | "advisor" | "system"
      />
    ))}
  </ConversationLog>
  
  {/* Input Area */}
  <QuestionInput 
    onSubmit={handleQuestion}
    placeholder="Ask advisors or type a command..."
    suggestions={["/status", "/advise", "/resources"]}
  />
</SceneViewport>
```

**Command Bar (ACTIVE):**
```tsx
<CommandBar>
  <CommandButton 
    onClick={() => showStatus()}
    icon="▲"
  >
    STATUS
  </CommandButton>
  
  <CommandButton 
    onClick={() => consultAllAdvisors()}
    icon="→"
  >
    ADVISE
  </CommandButton>
  
  <CommandButton 
    onClick={() => showResources()}
    icon="■"
  >
    RESOURCES
  </CommandButton>
  
  <CommandButton 
    onClick={() => openDiplomacy()}
    icon="&"
  >
    DIPLOMACY
  </CommandButton>
  
  <CommandButton 
    onClick={() => moveToDecision()}
    variant="primary"
    icon="!"
  >
    DECIDE
  </CommandButton>
  
  <CommandButton onClick={() => changeTheme()}>
    THEME
  </CommandButton>
  
  <CommandButton onClick={() => saveGame()}>
    SAVE
  </CommandButton>
  
  <CommandButton onClick={() => showMenu()}>
    MENU
  </CommandButton>
</CommandBar>
```

**Status Bar (LIVE):**
- Metrics update in real-time if diplomacy affects them
- Hover over metric = tooltip with full explanation
- Click metric = expand to detailed view

---

### Phase 3: DECISION

**Viewport Area:**
```tsx
<SceneViewport>
  <PhaseHeader 
    turn={3} 
    phase="DECISION"
    warning="Your decision will have consequences"
  />
  
  {/* Decision Input */}
  <DecisionInput 
    multiline={true}
    placeholder="State your decision..."
    helperText="Be specific. LLM will interpret your intent."
  />
  
  {/* OR if decision entered, show interpretation */}
  <DecisionInterpretation>
    <InterpretedAction action={decision} />
    
    {/* Advisor Pushback (if concerns raised) */}
    {pushback.map(pb => (
      <AdvisorConcern 
        advisor={pb.advisor}
        concern={pb.text}
        severity={pb.level} // "caution" | "warning" | "critical"
      />
    ))}
    
    {/* Confirmation Buttons */}
    <ActionButtons>
      <Button variant="confirm">Confirm Decision</Button>
      <Button variant="amend">Amend Decision</Button>
      <Button variant="cancel">Cancel / Return to Discussion</Button>
    </ActionButtons>
  </DecisionInterpretation>
</SceneViewport>
```

**Command Bar:**
- All commands DISABLED except:
  - `[CANCEL]` - Return to discussion
  - `[CONFIRM]` - Proceed to adjudication

**Status Bar:**
- Shows CURRENT metrics (pre-decision)
- Optional: Show PROJECTED impact (if LLM can estimate)

---

### Phase 4: ADJUDICATION

**Viewport Area:**
```tsx
<SceneViewport>
  <PhaseHeader 
    turn={3} 
    phase="ADJUDICATION"
    subtitle="Assessing outcomes..."
  />
  
  {/* Narrative Outcome */}
  <NarrativeOutcome 
    content={adjudicationText}
    typewriter={true}
  />
  
  {/* Metric Changes */}
  <MetricChangesSummary 
    before={previousMetrics}
    after={currentMetrics}
    animated={true}
  />
  
  {/* Character Reactions (Immersive Mode) */}
  {playMode === "immersive" && (
    <CharacterReactions>
      {reactions.map(r => (
        <CharacterReaction 
          character={r.name}
          reaction={r.text}
          trustChange={r.trustDelta}
        />
      ))}
    </CharacterReactions>
  )}
  
  {/* Continue Button */}
  <ContinueButton onClick={nextTurn}>
    Continue to Turn {turn + 1}
  </ContinueButton>
</SceneViewport>
```

**Command Bar:**
- All DISABLED except `[CONTINUE]`

**Status Bar:**
- Shows UPDATED metrics with deltas
- Animates changes (bars fill/drain smoothly)

---

## Modal/Overlay Panels (On-Demand)

### 1. Status Panel (`/status` command)
```tsx
<Modal id="status-panel" style="scumm-dialog">
  <DialogHeader>SITUATION REPORT</DialogHeader>
  
  {playMode === "classic" && (
    <MetricsTable 
      metrics={world.metrics}
      showBars={true}
      showBadges={true}
    />
  )}
  
  {playMode === "immersive" && (
    <>
      <SituationVibes vibes={narrative.vibes} />
      <AdvisorAttitudes characters={narrative.characters} />
    </>
  )}
  
  {world.flags && (
    <ActiveFlags flags={world.flags} />
  )}
  
  <CloseButton />
</Modal>
```

### 2. Advisor Panel (`/advise` command)
```tsx
<Modal id="advisor-panel" style="scumm-dialog-wide">
  <DialogHeader>COBRA CABINET - ALL ADVISORS</DialogHeader>
  
  <AdvisorGrid>
    {advisors.map(advisor => (
      <AdvisorCard 
        key={advisor.id}
        name={advisor.name}
        title={advisor.title}
        response={advisor.response}
        expanded={false}
      />
    ))}
  </AdvisorGrid>
  
  <CloseButton />
</Modal>
```

### 3. Resources Panel (`/resources` command)
```tsx
<Modal id="resources-panel" style="scumm-dialog-wide">
  <DialogHeader>UK MILITARY ASSETS</DialogHeader>
  
  <TabGroup>
    <Tab id="forces">FORCES</Tab>
    <Tab id="stockpiles">STOCKPILES</Tab>
  </TabGroup>
  
  <TabContent id="forces">
    <ForcesTable 
      naval={forces.naval}
      air={forces.air}
    />
  </TabContent>
  
  <TabContent id="stockpiles">
    <StockpilesTree 
      categories={stockpiles}
      colorCode={true}
    />
  </TabContent>
  
  <CloseButton />
</Modal>
```

### 4. Diplomacy Panel (`/call [country]`)
```tsx
<Modal id="diplomacy-panel" style="scumm-dialog-conversation">
  <DialogHeader>
    SECURE LINE: {country.toUpperCase()}
  </DialogHeader>
  
  <DiplomatInfo 
    country={country}
    contactName={contact.name}
    accessLevel={contact.level} // "leader" or "diplomat"
  />
  
  <ConversationLog 
    messages={diplomaticTranscript}
    maxExchanges={11}
  />
  
  <DiplomaticInput 
    onSubmit={handleDiplomaticMessage}
    placeholder="Your message..."
  />
  
  <EndConversationButton onClick={closeDiplomacy}>
    End Call
  </EndConversationButton>
</Modal>
```

### 5. Menu Panel (`/menu` command)
```tsx
<Modal id="menu-panel" style="scumm-dialog">
  <DialogHeader>COMMAND REFERENCE</DialogHeader>
  
  <MenuSections>
    <Section title="METRICS EXPLAINED">
      <MetricDefinition name="Escalation Risk" />
      <MetricDefinition name="Domestic Stability" />
      <MetricDefinition name="Alliance Cohesion" />
      <MetricDefinition name="Influence" />
    </Section>
    
    <Section title="COMMANDS">
      <CommandList commands={availableCommands} />
    </Section>
    
    <Section title="DIPLOMATIC CONTACTS">
      <ContactList 
        contacts={diplomaticContacts}
        groupBy="alliance"
      />
    </Section>
  </MenuSections>
  
  <CloseButton />
</Modal>
```

### 6. Theme Selector (`/theme` command)
```tsx
<Modal id="theme-panel" style="scumm-dialog">
  <DialogHeader>UI THEME SELECTOR</DialogHeader>
  
  <ThemeGrid>
    <ThemeOption 
      name="Standard"
      preview={<PreviewSwatch colors={themes.standard} />}
      active={currentTheme === "standard"}
      onClick={() => setTheme("standard")}
    />
    
    <ThemeOption 
      name="DEFCON"
      preview={<PreviewSwatch colors={themes.defcon} />}
      active={currentTheme === "defcon"}
      onClick={() => setTheme("defcon")}
    />
    
    <ThemeOption 
      name="Retro Green"
      preview={<PreviewSwatch colors={themes.retro} />}
      active={currentTheme === "retro"}
      onClick={() => setTheme("retro")}
    />
    
    <ThemeOption 
      name="Slate"
      preview={<PreviewSwatch colors={themes.slate} />}
      active={currentTheme === "slate"}
      onClick={() => setTheme("slate")}
    />
  </ThemeGrid>
  
  <ApplyButton onClick={applyTheme}>
    Apply Theme
  </ApplyButton>
</Modal>
```

---

## Responsive Breakpoints

### Desktop (1024px+)
- Full SCUMM three-panel layout
- Command bar: 4x2 grid
- Status bar: Horizontal metrics strip

### Tablet (768px - 1023px)
- Viewport: 70% height
- Command bar: 2x4 grid (stacked)
- Status bar: 2-column metrics

### Mobile (< 768px)
- Viewport: Full height
- Command bar: Collapsible drawer (hamburger menu)
- Status bar: Accordion (tap to expand)
- Consider: Bottom sheet navigation instead of SCUMM layout

---

## State Management Structure

```typescript
interface GameState {
  // Turn tracking
  turn: number;
  phase: "briefing" | "discussion" | "decision" | "adjudication";
  
  // World state
  metrics: {
    escalation_risk: number;
    domestic_stability: number;
    alliance_cohesion: number;
    casualties_mil: number;
    casualties_civ: number;
  };
  
  influence: number; // Derived from metrics
  
  // Play mode
  playMode: "classic" | "immersive" | "emergent";
  
  // Discussion history
  conversation: Message[];
  
  // Active panels
  activePanel: string | null;
  
  // Diplomatic state
  diplomaticContacts: DiplomaticContact[];
  activeDiplomacy: {
    country: string;
    transcript: Message[];
  } | null;
  
  // Resources
  forces: MilitaryForces;
  stockpiles: Stockpiles;
  
  // Settings
  theme: "standard" | "defcon" | "retro" | "slate";
  
  // Flags
  flags: Record<string, boolean>;
}
```

---

## Interaction Patterns

### Discussion Phase
1. Player types question in input field
2. OR Player clicks command button
3. Loading indicator appears
4. LLM response streams in (typewriter effect)
5. Response added to conversation log
6. Viewport auto-scrolls to latest message

### Command Shortcuts
```typescript
const shortcuts = {
  "Ctrl/Cmd + S": "Save game",
  "Ctrl/Cmd + M": "Open menu",
  "Ctrl/Cmd + D": "Move to decision",
  "Ctrl/Cmd + T": "Change theme",
  "Escape": "Close active panel"
};
```

### Accessibility
- All command buttons have keyboard shortcuts
- Screen reader announcements for phase changes
- Focus management for modals
- Color-blind friendly status badges
- High contrast mode available

---

## Animation & Transitions

### Phase Transitions
```css
.phase-enter {
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.phase-enter-active {
  opacity: 1;
  transform: translateY(0);
}
```

### Metric Changes
- Number ticker animation (rolling counter)
- Progress bar smooth fill/drain (0.6s duration)
- Color fade for status badge changes

### Typewriter Text
```typescript
const typewriterSpeed = {
  fast: 15,    // ms per character
  normal: 30,
  slow: 50
};

// Pause multipliers
const punctuationPause = {
  '.': 3x,
  '!': 3x,
  '?': 3x,
  ',': 2x,
  ';': 2x,
  ':': 2x
};
```

---

## Component Styling (SCUMM Painterly)

### Panel Base
```css
.scumm-panel {
  background: linear-gradient(
    135deg,
    var(--panel-dark) 0%,
    var(--panel-light) 100%
  );
  border: 2px solid var(--border-shadow);
  border-radius: 2px;
  box-shadow: 
    inset 1px 1px 0 rgba(255,255,255,0.1),
    2px 2px 4px rgba(0,0,0,0.4);
}
```

### Command Button
```css
.command-button {
  background: linear-gradient(
    180deg,
    var(--button-light) 0%,
    var(--button-dark) 100%
  );
  border: 1px solid var(--border-hard);
  box-shadow: 2px 2px 4px rgba(0,0,0,0.4);
  font-family: 'Crimson Text', serif;
  font-weight: 600;
  text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
  transition: all 0.15s ease;
}

.command-button:hover {
  transform: translateY(-1px);
  box-shadow: 3px 3px 6px rgba(0,0,0,0.5);
}

.command-button:active {
  transform: translateY(0);
  box-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

.command-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  filter: grayscale(0.8);
}
```

---

## Implementation Priority

### Phase 1 (MVP)
1. Basic three-panel layout
2. Phase header component
3. Command bar with all buttons
4. Status bar with metrics
5. Typewriter text for narratives
6. Discussion input/output

### Phase 2 (Core Features)
1. All modal panels (status, advise, resources, menu)
2. Diplomatic encounter UI
3. Decision input with interpretation
4. Metric change animations
5. Theme switcher

### Phase 3 (Polish)
1. Keyboard shortcuts
2. Mobile responsive layout
3. Immersive mode character attitudes
4. Advanced animations
5. Accessibility enhancements

---

## Next Steps

1. **Prototype the layout** - Build static HTML/CSS of SCUMM three-panel design
2. **Test the flow** - Walk through all four phases with dummy data
3. **Implement theme system** - Port `cli/theme.py` colors to Tailwind config
4. **Build command bar** - Create reusable CommandButton component
5. **Implement typewriter** - Character-by-character text reveal with skip
6. **Connect to backend** - API endpoints for LLM calls and game state

Would you like me to create the actual Tailwind config and component scaffolding next?


