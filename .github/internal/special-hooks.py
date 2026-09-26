from pathlib import Path
p=Path("src/Main/HoopLandExpanded/CustomSkills.cs")
s=p.read_text()

def one(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f"{label}: expected 1 anchor, found {n}")
    s=s.replace(old,new,1)

one(
    'public static readonly ProbeSpec[] SkillHooks = new ProbeSpec[23]',
    'public static readonly ProbeSpec[] SkillHooks = new ProbeSpec[25]',
    'hook count'
)

progress='\t\tHook("progress", "PlayerSkills", "ProgressSkill", stat: true, "System.Void", new string[2] { "PlayerData", "System.String" }, "CustomProgress"),\n'
one(
    progress,
    progress +
    '\t\tHook("special-equip", "ListSkills", "EquipSkill", stat: true, "System.Void", new string[2] { "PlayerData", "SkillData" }, "BeforeSpecialEquip"),\n' +
    '\t\tHook("special-cpu", "CPUProgression", "UnlockPlayerSkills", stat: true, "System.Void", new string[1] { "PlayerData" }, null, "AfterCpuSpecialSkills"),\n',
    'special hooks'
)

one(
    '\t\tSafe("save-before", (CustomSkills m) =>\n\t\t{\n\t\t\tstring text = m.SkillSavePath(__0);\n',
    '\t\tSafe("save-before", (CustomSkills m) =>\n\t\t{\n\t\t\tm.NormalizeAllSpecialSlots("save-before");\n\t\t\tstring text = m.SkillSavePath(__0);\n',
    'save normalization'
)

one(
    '\t\tSeedLegendQualifications(native);\n\t\tSeedIconQualifications(native);\n',
    '\t\tSeedLegendQualifications(native);\n\t\tSeedIconQualifications(native);\n\t\tNormalizeAllSpecialSlots(source);\n',
    'load normalization'
)

one(
    '\t\t\tLegendarySkillsEquippable = true,\n',
    '\t\t\tLegendarySkillsEquippable = true,\n\t\t\tSpecialLoadout = "15-SP ordinary economy unchanged; one zero-SP ICON slot plus one zero-SP Legendary slot",\n',
    'diagnostics'
)

p.write_text(s)
print("Special equip hooks and persistence reconciliation anchors applied.")
