"""Fix indentation in main_dashboard.py for the discussion loop."""

# Read the file
with open("cli/main_dashboard.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the section to fix (after "if not user_input:" until "# Decision phase")
output_lines = []
fixing = False
for i, line in enumerate(lines):
    # Start fixing after line with "if not user_input:"
    if i > 0 and "if not user_input:" in lines[i-1] and "continue" in line:
        fixing = True
        output_lines.append(line)  # Keep the "continue" line as-is
        continue
    
    # Stop fixing at "# Decision phase"
    if "# Decision phase" in line and fixing:
        fixing = False
    
    # Add 4 spaces of indentation to lines in the fixing section
    if fixing and line.strip():  # Only indent non-empty lines
        output_lines.append("    " + line)
    else:
        output_lines.append(line)

# Write back
with open("cli/main_dashboard.py", "w", encoding="utf-8") as f:
    f.writelines(output_lines)

print("Fixed indentation in main_dashboard.py")

