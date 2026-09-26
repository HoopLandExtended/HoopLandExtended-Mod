from pathlib import Path

p=Path("src/Main/HoopLandExpanded/CustomSkills.cs")
s=p.read_text()

icon_start=s.index('\tprivate void PresentIconRow(object row, object player, CustomSkillDefinition d, bool editor)')
legend_start=s.index('\n\tprivate void PresentLegendaryRow',icon_start)

icon=r'''\tprivate void PresentIconRow(object row, object player, CustomSkillDefinition d, bool editor)
\t{
\t\tif (!d.Icon)
\t\t{
\t\t\treturn;
\t\t}
\t\tobject? skill = SkillXp(player, d.Id);
\t\tbool equipped = skill != null && access.Int(skill, "level") > 0 && access.Bool(skill, "equipped");
\t\tSkillPresentationText text = TextFor(player, d);
\t\tDisplayText(row, "level", "ICON");
\t\tDisplayActive(row, access.Need(row, "level"), value: true);
\t\tDisplayActive(row, access.Need(row, "starRating"), value: false);
\t\tif (!editor)
\t\t{
\t\t\tDisplayText(row, "description", text.Effect);
\t\t\tstring family = d.IconFamily.Length == 0 ? "ICON" : d.IconFamily.ToUpperInvariant() + " ICON";
\t\t\tstring status = !text.Revealed ? (family + " — LOCKED") : (family + (equipped ? " — EQUIPPED" : " — EARNED") + "\nICON SLOT: " + (equipped ? "1/1" : "0/1") + " • 0 SP\n" + text.Requirement);
\t\t\tDisplayText(row, "status", status);
\t\t\tDisplayActive(row, access.Need(access.Need(row, "progress"), "parent"), value: false);
\t\t\tNativeTextLayout.Skill(row, (Action undo) =>
\t\t\t{
\t\t\t\tRememberPresentation(row, undo);
\t\t\t});
\t\t}
\t}
'''

s=s[:icon_start]+icon+s[legend_start:]

legend_start=s.index('\tprivate void PresentLegendaryRow(object row, object player, CustomSkillDefinition d, bool editor)')
next_start=s.index('\n\tprivate static void BeforeSkillPresentation',legend_start)

legend=r'''\tprivate void PresentLegendaryRow(object row, object player, CustomSkillDefinition d, bool editor)
\t{
\t\tif (!d.Legendary)
\t\t{
\t\t\treturn;
\t\t}
\t\tobject? skill = SkillXp(player, d.Id);
\t\tbool equipped = skill != null && access.Int(skill, "level") > 0 && access.Bool(skill, "equipped");
\t\tSkillPresentationText text = TextFor(player, d);
\t\tDisplayText(row, "level", text.Label);
\t\tDisplayActive(row, access.Need(row, "level"), value: true);
\t\tDisplayActive(row, access.Need(row, "starRating"), value: false);
\t\tif (!editor)
\t\t{
\t\t\tDisplayText(row, "description", text.Effect);
\t\t\tstring status = !text.Revealed ? "LEGENDARY — LOCKED" : ("LEGENDARY — " + (equipped ? "EQUIPPED" : "EARNED") + "\nLEGENDARY SLOT: " + (equipped ? "1/1" : "0/1") + " • 0 SP\n" + text.Requirement);
\t\t\tDisplayText(row, "status", status);
\t\t\tDisplayActive(row, access.Need(access.Need(row, "progress"), "parent"), value: false);
\t\t\tNativeTextLayout.Skill(row, (Action undo) =>
\t\t\t{
\t\t\t\tRememberPresentation(row, undo);
\t\t\t});
\t\t}
\t}
'''

s=s[:legend_start]+legend+s[next_start:]

old=r'''\t\t\tif ((object)customSkillDefinition != null && customSkillDefinition.Icon)
\t\t\t{
\t\t\t\tobject? skill = m.SkillXp(__0, customSkillDefinition.Id);
\t\t\t\tbool unlocked = skill != null && m.access.Int(skill, "level") > 0;
\t\t\t\tm.DisplayText(__instance, "header", "ICON — " + customSkillDefinition.IconFamily.ToUpperInvariant());
\t\t\t\tm.DisplayText(__instance, "description", customSkillDefinition.Name + "\n" + customSkillDefinition.Description + "\n\nUnlock: " + customSkillDefinition.Action + (unlocked ? "\n\nUNLOCKED" : ""));
\t\t\t}
\t\t\telse if ((object)customSkillDefinition != null && (customSkillDefinition.Legendary || customSkillDefinition.Icon))
\t\t\t{
\t\t\t\tSkillPresentationText skillPresentationText = m.TextFor(__0, customSkillDefinition);
\t\t\t\tm.DisplayText(__instance, "header", customSkillDefinition.Icon ? "ICON SKILL" : "LEGENDARY SKILL");
\t\t\t\tm.DisplayText(__instance, "description", customSkillDefinition.Name + "\n" + skillPresentationText.Details);
\t\t\t}
'''

new=r'''\t\t\tif ((object)customSkillDefinition != null && (customSkillDefinition.Legendary || customSkillDefinition.Icon))
\t\t\t{
\t\t\t\tSkillPresentationText text = m.TextFor(__0, customSkillDefinition);
\t\t\t\tstring header = customSkillDefinition.Icon ? ("ICON — " + customSkillDefinition.IconFamily.ToUpperInvariant()) : "LEGENDARY SKILL";
\t\t\t\tstring details = customSkillDefinition.Name + "\n" + text.Effect + (text.Revealed ? ("\n\n" + text.Requirement + "\n\n0 SP • 1 " + (customSkillDefinition.Icon ? "ICON" : "LEGENDARY") + " slot") : "");
\t\t\t\tm.DisplayText(__instance, "header", header);
\t\t\t\tm.DisplayText(__instance, "description", details);
\t\t\t}
'''

if s.count(old)!=1:
    raise SystemExit(f"achievement presentation anchor mismatch: {s.count(old)}")
s=s.replace(old,new,1)

p.write_text(s)
print("Special-slot UI and locked presentation applied.")
