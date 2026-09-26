from pathlib import Path
import re

root=Path("src/Main/HoopLandExpanded")

# Locked ICONs use the same per-player reveal boundary as Legendary skills.
p=root/"SkillPresentationPolicy.cs"
s=p.read_text()
old='''\t\tif (!skill.Legendary)
\t\t{
\t\t\treturn new SkillPresentationText(Legendary: false, Revealed: true, "", skill.Description, SkillRequirementPolicy.CatalogRequirement(skill));
\t\t}
\t\tbool flag = earnedRank > 0 && earnedRank <= skill.MaximumRank;
\t\treturn new SkillPresentationText(Legendary: true, flag, "LEGENDARY", flag ? skill.Description : "Unlock this legendary skill to reveal its requirements and effects.", flag ? ("Unlocked by: " + skill.Action) : "");'''
new='''\t\tif (!skill.Legendary && !skill.Icon)
\t\t{
\t\t\treturn new SkillPresentationText(Legendary: false, Revealed: true, "", skill.Description, SkillRequirementPolicy.CatalogRequirement(skill));
\t\t}
\t\tbool flag = earnedRank > 0 && earnedRank <= skill.MaximumRank;
\t\tif (skill.Icon)
\t\t{
\t\t\tstring label = System.String.IsNullOrWhiteSpace(skill.IconFamily) ? "ICON" : ("ICON • " + skill.IconFamily.ToUpperInvariant());
\t\t\treturn new SkillPresentationText(Legendary: false, flag, label, flag ? skill.Description : "Unlock this ICON to reveal its requirements and effects.", flag ? ("Unlocked by: " + skill.Action) : "");
\t\t}
\t\treturn new SkillPresentationText(Legendary: true, flag, "LEGENDARY", flag ? skill.Description : "Unlock this legendary skill to reveal its requirements and effects.", flag ? ("Unlocked by: " + skill.Action) : "");'''
if old not in s:
    raise SystemExit("presentation policy baseline not found")
p.write_text(s.replace(old,new))

# Prevent the shared native SkillData catalog from leaking the hidden text before
# the viewed-player row presentation gets a chance to resolve earned state.
p=root/"CustomSkills.cs"
s=p.read_text()
replacement='''\tprivate void CatalogPresentation(object skill, CustomSkillDefinition definition)
\t{
\t\tbool special = definition.Legendary || definition.Icon;
\t\tstring mystery = definition.Icon ? "Unlock this ICON to reveal its requirements and effects." : "Unlock this legendary skill to reveal its requirements and effects.";
\t\taccess.Set(skill, "description", special ? mystery : definition.Description);
\t\taccess.Set(skill, "unlockDescription", special ? "" : SkillRequirementPolicy.CatalogRequirement(definition));
\t\taccess.Set(skill, "actionRequirement", special ? "" : SkillRequirementPolicy.Action(definition));
\t}
'''
s,n=re.subn(r'\tprivate void CatalogPresentation\(object skill, CustomSkillDefinition definition\)\n\t\{.*?\n\t\}\n(?=\n\tprivate )', replacement, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"CatalogPresentation replacement count={n}")

# Make the achievement/detail presentation special-skill aware if the prototype
# has not already done so.
s=s.replace(
    'if ((object)customSkillDefinition != null && customSkillDefinition.Legendary)',
    'if ((object)customSkillDefinition != null && (customSkillDefinition.Legendary || customSkillDefinition.Icon))'
)
s=s.replace(
    'm.DisplayText(__instance, "header", "LEGENDARY SKILL");',
    'm.DisplayText(__instance, "header", customSkillDefinition.Icon ? "ICON SKILL" : "LEGENDARY SKILL");'
)
p.write_text(s)

# Hide the generic catalog requirement for ICONs. Their real requirement is only
# exposed through SkillPresentationPolicy after the viewed player has earned it.
p=root/"SkillRequirementPolicy.cs"
s=p.read_text()
method='''\tpublic static string CatalogRequirement(CustomSkillDefinition d)
\t{
\t\tif (d.Legendary || d.Icon)
\t\t{
\t\t\treturn "";
\t\t}
\t\treturn ((d.RawGate == RawSkillGate.None) ? "" : (RatingName(d.RawGate) + " 8.0; ")) + Action(d);
\t}
'''
s,n=re.subn(r'\tpublic static string CatalogRequirement\(CustomSkillDefinition d\)\n\t\{.*?\n\t\}\n(?=\n\tpublic static string Action)', method, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"CatalogRequirement replacement count={n}")

# Mirror Legendary routing for the ordinary progression-text helper.
s=s.replace(
    'if (d.Legendary)\n\t\t{\n\t\t\tthrow new ArgumentException("Legendary requirements use the concealment policy.");\n\t\t}',
    'if (d.Legendary || d.Icon)\n\t\t{\n\t\t\tthrow new ArgumentException("Special skill requirements use the concealment policy.");\n\t\t}'
)
p.write_text(s)

print("ICON concealment source patch applied.")
