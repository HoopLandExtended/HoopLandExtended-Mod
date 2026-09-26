from pathlib import Path

root=Path("src/Main/HoopLandExpanded")
catalog=root/"CustomSkillCatalog.cs"
s=catalog.read_text()

changes={
'new CustomSkillDefinition("HLE_FR05", "Human Torch", 1, 5, 1, 1,':'new CustomSkillDefinition("HLE_FR05", "Human Torch", 1, 0, 1, 1,',
'new CustomSkillDefinition("HLE_FR06", "Century", 1, 5, 1, 1,':'new CustomSkillDefinition("HLE_FR06", "Century", 1, 0, 1, 1,',
'new CustomSkillDefinition("HLE_FR07", "Total Control", 2, 5, 1, 1,':'new CustomSkillDefinition("HLE_FR07", "Total Control", 2, 0, 1, 1,',
'new CustomSkillDefinition("HLE_LG01", "Maestro", 2, 5, 1, 1,':'new CustomSkillDefinition("HLE_LG01", "Maestro", 2, 0, 1, 1,',
'new CustomSkillDefinition("HLE_LG02", "Unstoppable", 0, 5, 1, 1,':'new CustomSkillDefinition("HLE_LG02", "Unstoppable", 0, 0, 1, 1,',
'new CustomSkillDefinition("HLE_LG04", "Defensive Colossus", 3, 5, 1, 1,':'new CustomSkillDefinition("HLE_LG04", "Defensive Colossus", 3, 0, 1, 1,',
'new CustomSkillDefinition("HLE_LG03", "Glass Sovereign", 3, 4, 1, 1,':'new CustomSkillDefinition("HLE_LG03", "Glass Sovereign", 3, 0, 1, 1,',
'new CustomSkillDefinition("HLE_IC01", "Headliner", 1, 3, 1, 1,':'new CustomSkillDefinition("HLE_IC01", "Headliner", 1, 0, 1, 1,',
'new CustomSkillDefinition("HLE_IC02", "Table Setter", 2, 3, 1, 1,':'new CustomSkillDefinition("HLE_IC02", "Table Setter", 2, 0, 1, 1,',
'new CustomSkillDefinition("HLE_IC03", "Two-Way Force", 3, 3, 1, 1,':'new CustomSkillDefinition("HLE_IC03", "Two-Way Force", 3, 0, 1, 1,',
'new CustomSkillDefinition("HLE_IC04", "Grab & Go", 2, 3, 1, 1,':'new CustomSkillDefinition("HLE_IC04", "Grab & Go", 2, 0, 1, 1,',
'new CustomSkillDefinition("HLE_IC05", "March Hero", 1, 3, 1, 1,':'new CustomSkillDefinition("HLE_IC05", "March Hero", 1, 0, 1, 1,',
}
for old,new in changes.items():
    if s.count(old)!=1:
        raise SystemExit(f"catalog anchor mismatch: {old}")
    s=s.replace(old,new,1)
catalog.write_text(s)

(root/"SpecialSkillLoadoutRules.cs").write_text("""namespace HoopLandExpanded;

public enum SpecialSkillSlot
{
    None = 0,
    Icon = 1,
    Legendary = 2
}

public static class SpecialSkillLoadoutRules
{
    public const int IconEquipLimit = 1;
    public const int LegendaryEquipLimit = 1;

    public static SpecialSkillSlot Slot(CustomSkillDefinition? definition)
    {
        if (definition == null) return SpecialSkillSlot.None;
        if (definition.Icon) return SpecialSkillSlot.Icon;
        if (definition.Legendary) return SpecialSkillSlot.Legendary;
        return SpecialSkillSlot.None;
    }

    public static bool IsSpecial(CustomSkillDefinition? definition) => Slot(definition) != SpecialSkillSlot.None;

    public static int EquipLimit(SpecialSkillSlot slot) => slot switch
    {
        SpecialSkillSlot.Icon => IconEquipLimit,
        SpecialSkillSlot.Legendary => LegendaryEquipLimit,
        _ => int.MaxValue
    };

    public static string Label(SpecialSkillSlot slot) => slot switch
    {
        SpecialSkillSlot.Icon => "ICON",
        SpecialSkillSlot.Legendary => "LEGENDARY",
        _ => "ORDINARY"
    };
}
""")
print("Special catalog costs and slot rules applied.")
