from pathlib import Path

p=Path("src/Main/HoopLandExpanded/CustomSkills.cs")
s=p.read_text()
anchor='\tprivate static void BeforeCatalog(out bool __state)\n'
if s.count(anchor)!=1:
    raise SystemExit(f"runtime insertion anchor mismatch: {s.count(anchor)}")

runtime=r'''\tprivate bool HandleSpecialEquip(object player, object skillData)
\t{
\t\tstring id = access.Text(skillData, "id");
\t\tCustomSkillDefinition? definition = CustomSkillCatalog.Find(id);
\t\tSpecialSkillSlot slot = SpecialSkillLoadoutRules.Slot(definition);
\t\tif (slot == SpecialSkillSlot.None)
\t\t{
\t\t\treturn true;
\t\t}
\t\tobject? skill = SkillXp(player, id);
\t\tif (skill == null || access.Int(skill, "level") <= 0)
\t\t{
\t\t\tEvent("special-slot-rejected", new
\t\t\t{
\t\t\t\tPlayer = access.Int(player, "id"),
\t\t\t\tId = id,
\t\t\t\tSlot = SpecialSkillLoadoutRules.Label(slot),
\t\t\t\tReason = "not-earned"
\t\t\t}, player);
\t\t\treturn false;
\t\t}
\t\tbool equip = !access.Bool(skill, "equipped");
\t\tobject list = access.Need(player, "skills");
\t\tif (equip)
\t\t{
\t\t\tfor (int i = 0; i < access.Count(list); i++)
\t\t\t{
\t\t\t\tobject other = access.Item(list, i);
\t\t\t\tif (CustomSkillAccess.Same(other, skill) || !access.Bool(other, "equipped"))
\t\t\t\t{
\t\t\t\t\tcontinue;
\t\t\t\t}
\t\t\t\tCustomSkillDefinition? otherDefinition = CustomSkillCatalog.Find(access.Text(other, "id"));
\t\t\t\tif (SpecialSkillLoadoutRules.Slot(otherDefinition) == slot)
\t\t\t\t{
\t\t\t\t\taccess.Set(other, "equipped", false);
\t\t\t\t\tEvent("special-slot-swapped-out", new
\t\t\t\t\t{
\t\t\t\t\t\tPlayer = access.Int(player, "id"),
\t\t\t\t\t\tId = access.Text(other, "id"),
\t\t\t\t\t\tReplacement = id,
\t\t\t\t\t\tSlot = SpecialSkillLoadoutRules.Label(slot)
\t\t\t\t\t}, player);
\t\t\t\t}
\t\t\t}
\t\t}
\t\taccess.Set(skill, "equipped", equip);
\t\tNormalizeSpecialSlots(player, "manual-equip");
\t\tEvent("special-slot-changed", new
\t\t{
\t\t\tPlayer = access.Int(player, "id"),
\t\t\tId = id,
\t\t\tSlot = SpecialSkillLoadoutRules.Label(slot),
\t\t\tEquipped = equip,
\t\t\tCost = 0,
\t\t\tOrdinarySkillPointsUnaffected = true
\t\t}, player);
\t\treturn false;
\t}

\tprivate void NormalizeSpecialSlots(object player, string source)
\t{
\t\tNormalizeSpecialSlot(player, SpecialSkillSlot.Icon, source);
\t\tNormalizeSpecialSlot(player, SpecialSkillSlot.Legendary, source);
\t}

\tprivate void NormalizeSpecialSlot(object player, SpecialSkillSlot slot, string source)
\t{
\t\tobject list = access.Need(player, "skills");
\t\tobject? keep = null;
\t\tList<string> removed = new List<string>();
\t\tfor (int i = 0; i < access.Count(list); i++)
\t\t{
\t\t\tobject skill = access.Item(list, i);
\t\t\tCustomSkillDefinition? definition = CustomSkillCatalog.Find(access.Text(skill, "id"));
\t\t\tif (SpecialSkillLoadoutRules.Slot(definition) != slot)
\t\t\t{
\t\t\t\tcontinue;
\t\t\t}
\t\t\tbool equipped = access.Bool(skill, "equipped");
\t\t\tif (access.Int(skill, "level") <= 0)
\t\t\t{
\t\t\t\tif (equipped)
\t\t\t\t{
\t\t\t\t\taccess.Set(skill, "equipped", false);
\t\t\t\t\tremoved.Add(access.Text(skill, "id"));
\t\t\t\t}
\t\t\t\tcontinue;
\t\t\t}
\t\t\tif (!equipped)
\t\t\t{
\t\t\t\tcontinue;
\t\t\t}
\t\t\tif (keep == null)
\t\t\t{
\t\t\t\tkeep = skill;
\t\t\t\tcontinue;
\t\t\t}
\t\t\taccess.Set(skill, "equipped", false);
\t\t\tremoved.Add(access.Text(skill, "id"));
\t\t}
\t\tif (removed.Count > 0)
\t\t{
\t\t\tEvent("special-slot-reconciled", new
\t\t\t{
\t\t\t\tPlayer = access.Int(player, "id"),
\t\t\t\tSlot = SpecialSkillLoadoutRules.Label(slot),
\t\t\t\tKept = ((keep == null) ? "" : access.Text(keep, "id")),
\t\t\t\tUnequipped = removed.ToArray(),
\t\t\t\tSource = source,
\t\t\t\tLimit = SpecialSkillLoadoutRules.EquipLimit(slot)
\t\t\t}, player);
\t\t}
\t}

\tprivate void NormalizeAllSpecialSlots(string source)
\t{
\t\tobject? league = access.Static("GameManager", "currentLeague");
\t\tif (league == null)
\t\t{
\t\t\treturn;
\t\t}
\t\tobject? teams = access.Read(league, "teams");
\t\tif (teams == null)
\t\t{
\t\t\treturn;
\t\t}
\t\tHashSet<int> seen = new HashSet<int>();
\t\tfor (int i = 0; i < Math.Min(access.Count(teams), 700); i++)
\t\t{
\t\t\tobject roster = access.Need(access.Item(teams, i), "roster");
\t\t\tfor (int j = 0; j < Math.Min(access.Count(roster), 64); j++)
\t\t\t{
\t\t\t\tobject player = access.Item(roster, j);
\t\t\t\tif (seen.Add(access.Int(player, "id")))
\t\t\t\t{
\t\t\t\t\tNormalizeSpecialSlots(player, source);
\t\t\t\t}
\t\t\t}
\t\t}
\t}

\tprivate static bool BeforeSpecialEquip(object __0, object __1)
\t{
\t\tCustomSkills? m = instance;
\t\tif (m == null || !m.Ready)
\t\t{
\t\t\treturn true;
\t\t}
\t\tCustomSkillDefinition? definition;
\t\ttry
\t\t{
\t\t\tdefinition = CustomSkillCatalog.Find(m.access.Text(__1, "id"));
\t\t}
\t\tcatch (Exception ex)
\t\t{
\t\t\tm.Error("special-equip-identify", ex);
\t\t\treturn true;
\t\t}
\t\tif (!SpecialSkillLoadoutRules.IsSpecial(definition))
\t\t{
\t\t\treturn true;
\t\t}
\t\ttry
\t\t{
\t\t\treturn m.HandleSpecialEquip(__0, __1);
\t\t}
\t\tcatch (Exception ex2)
\t\t{
\t\t\tm.Error("special-equip", ex2);
\t\t\treturn false;
\t\t}
\t}

\tprivate static void AfterCpuSpecialSkills(object __0)
\t{
\t\tSafe("special-cpu", (CustomSkills m) =>
\t\t{
\t\t\tm.NormalizeSpecialSlots(__0, "cpu-progression");
\t\t});
\t}

'''

runtime=runtime.replace('\\t','\t')

s=s.replace(anchor,runtime+anchor,1)
p.write_text(s)
print("Special-slot runtime equip and reconciliation logic applied.")
