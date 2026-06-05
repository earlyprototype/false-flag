# CLI to Web Component Mapping

## How Your Current CLI Translates to Web

### 1. Phase Headers
**CLI (current):**
```
╭────────────────────────────────────╮
│ TURN 1 │ DISCUSSION PHASE         │
╰────────────────────────────────────╯
```

**Web Option A (8bitcn Card):**
- Pixelated border matching `╭─╮` aesthetic
- Large heading with turn counter
- Phase name highlighted
- **Component:** `<Card>` with custom header styling

**Web Option B (Dark Matter):**
- Clean monospace text
- Subtle border
- Professional, less playful
- **Component:** Standard `<Card>` or custom div

---

### 2. Metrics Table
**CLI (current):**
```
▲ Escalation Risk    70  ████████░░  ELEVATED
■ Domestic Stability 45  ████░░░░░░  WEAK
& Alliance Cohesion  62  ██████░░░░  STABLE
```

**Web (8bitcn Chart + Table):**
- ASCII symbols become pixel icons or kept as-is
- Progress bars become pixelated `<progress>` elements
- Status labels remain text badges
- **Components:**
  - `<Table>` for layout
  - `<Progress>` (styled) for bars
  - `<Badge>` for status labels
  - Custom icons for ▲ ■ & symbols

**Code Example:**
```tsx
<Card>
  <Table>
    <TableRow>
      <TableCell>▲ Escalation Risk</TableCell>
      <TableCell>70</TableCell>
      <TableCell><Progress value={70} /></TableCell>
      <TableCell><Badge variant="warning">ELEVATED</Badge></TableCell>
    </TableRow>
  </Table>
</Card>
```

---

### 3. Advisor Menu Panel
**CLI (current):**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ COBRA CABINET STRUCTURE       ┃
┃                               ┃
┃ → National Security Advisor   ┃
┃ → Chief of Defence Staff      ┃
┃ → Foreign Secretary           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**Web (8bitcn Dialog or Sidebar):**
- Heavy borders match `┏━┓` boxes
- Arrow symbols `→` retained or become pixel chevrons
- Clickable list items
- **Components:**
  - `<Dialog>` for modal popup
  - Or `<Sidebar>` for persistent nav
  - `<Button variant="ghost">` for each advisor

---

### 4. Command Palette
**CLI (current):**
```
> /status
> /advise
> /resources
> /call [country]
```

**Web (Shadcn Command + 8bitcn styling):**
- CMD+K to open (like VS Code)
- Type to filter commands
- Retro styling with pixelated borders
- **Component:** `<Command>` (official Shadcn)
- **Enhancement:** Style with 8bitcn theme

**Installation:**
```bash
npx shadcn add command
```

**Visual:** Like Spotlight/Raycast but pixelated

---

### 5. Advisor Response Text
**CLI (current):**
```
National Security Advisor:

  The situation in the Baltic is deteriorating.
  Russian forces continue to mass along the border.
  
  ! WARNING: Intelligence suggests imminent action.
  
  → RECOMMEND: Deploy RAF Typhoons to Estonia.
```

**Web (Formatted Text Block):**
- Typewriter animation (character-by-character reveal)
- Warning icon `!` highlighted in amber
- Recommendation `→` highlighted in cyan
- **Components:**
  - Custom `<AdvisorText>` component
  - Framer Motion for typing effect
  - `<Alert>` for warnings
  - `<Callout>` for recommendations

**Animation:**
```tsx
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.3 }}
>
  <TypewriterText text={advisorResponse} speed={30} />
</motion.div>
```

---

### 6. Progress Bars
**CLI (current):**
```
██████████░░░░░░░░░░  50/100
```

**Web (8bitcn Progress):**
- Pixelated filled blocks
- Exact visual match to ASCII bars
- **Component:** `<Progress value={50} max={100} />`
- **Styling:** 8bitcn makes it pixel-perfect

---

### 7. Status Badges
**CLI (current):**
```
CRITICAL
ELEVATED
STABLE
```

**Web (8bitcn Badge):**
- Same text, pixelated container
- Colour-coded (red, amber, green)
- **Component:** `<Badge variant="destructive">CRITICAL</Badge>`

---

### 8. Diplomatic Contacts Tree
**CLI (current):**
```
NATO Allies
  # US President
  • French Ambassador
  • German Chancellor
```

**Web (8bitcn Tree or List):**
- Symbols retained (`#` for leaders, `•` for diplomats)
- Expandable groups
- **Components:**
  - `<Accordion>` for collapsible groups
  - `<List>` with custom icons
  - `<Avatar>` with pixel art flags

---

## Component Shopping List

### From Official Shadcn
```bash
npx shadcn add command     # Command palette
npx shadcn add table       # Data tables
npx shadcn add card        # Containers
npx shadcn add badge       # Status labels
npx shadcn add dialog      # Modal panels
npx shadcn add progress    # Progress bars
npx shadcn add separator   # Dividers
npx shadcn add accordion   # Collapsible lists
```

### From 8bitcn Registry
```bash
pnpm dlx shadcn@latest add @8bitcn/ui
```
Then style all official components with 8bitcn theme.

---

## Visual Continuity Checklist

- [ ] Box borders match CLI box-drawing characters
- [ ] Colour scheme matches `defcon` theme
- [ ] Symbols (▲ ■ & † →) carried over exactly
- [ ] Typewriter text animation for narrative
- [ ] Progress bars look like ASCII blocks
- [ ] Command palette feels like CLI prompt
- [ ] Monospace font for all data/metrics
- [ ] Theme switcher (Arcade ↔ Gameboy)


