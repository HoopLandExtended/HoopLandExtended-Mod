from pathlib import Path

root=Path("src/Main/HoopLandExpanded")
p=root/"PlayerSkillsUiProbe.cs"
s=p.read_text()

old='''    private static void AfterPlayerSkillsUiProbe(object __instance)
    {
        Safe("player-skills-ui-probe", m => m.CapturePlayerSkillsUi(__instance));
    }
'''
new='''    private static void AfterPlayerSkillsUiProbe(object __instance)
    {
        Safe("player-skills-ui-probe", m => m.CapturePlayerSkillsUi(__instance));
        Safe("player-upgrades-ui-probe", m => m.CapturePlayerUpgradesUi(__instance));
    }
'''
if old not in s:
    raise SystemExit("Player Skills callback anchor missing")
p.write_text(s.replace(old,new,1))

(root/"PlayerUpgradesUiProbe.cs").write_text(r'''using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;

namespace HoopLandExpanded;

public sealed partial class CustomSkills
{
    private int playerUpgradesUiCaptureCount;

    private static object? UpParent(object? transform) =>
        transform == null ? null : UiReadProperty(transform, "parent");

    private static object? UpChild(object transform, int index)
    {
        try
        {
            MethodInfo? method = transform.GetType().GetMethods(UiFlags)
                .FirstOrDefault(m => m.Name == "GetChild"
                    && m.GetParameters().Length == 1
                    && m.GetParameters()[0].ParameterType == typeof(int));
            return method?.Invoke(transform, new object[] { index });
        }
        catch { return null; }
    }

    private static int UpChildCount(object? transform)
    {
        if (transform == null) return 0;
        try
        {
            object? value = UiReadProperty(transform, "childCount");
            return value == null ? 0 : Convert.ToInt32(value, CultureInfo.InvariantCulture);
        }
        catch { return 0; }
    }

    private static string UpName(object? value)
    {
        string name = UiName(value);
        if (!string.IsNullOrWhiteSpace(name)) return name;
        object? go = UiGameObject(value);
        return go == null ? "" : UiName(go);
    }

    private object? FindSiblingScreen(object listSkills, string target)
    {
        object? current = UiTransform(listSkills);
        object? parent = UpParent(current);
        if (parent == null) return null;

        int count = Math.Min(UpChildCount(parent), 80);
        for (int i = 0; i < count; i++)
        {
            object? child = UpChild(parent, i);
            if (child == null) continue;
            if (string.Equals(UpName(child), target, StringComparison.OrdinalIgnoreCase))
                return child;
        }
        return null;
    }

    private object[] UpNamedNodes(object root)
    {
        List<object> rows = new();
        foreach (object node in UiHierarchy(root))
        {
            // UiHierarchy's anonymous nodes serialize cleanly but cannot be
            // strongly inspected here. Recording the full hierarchy below is
            // authoritative; this placeholder keeps the probe schema explicit.
            rows.Add(node);
            if (rows.Count >= 480) break;
        }
        return rows.ToArray();
    }

    private void CapturePlayerUpgradesUi(object listSkills)
    {
        if (playerUpgradesUiCaptureCount >= 8) return;
        playerUpgradesUiCaptureCount++;

        object? upgrades = FindSiblingScreen(listSkills, "Player Upgrades");
        object? myPlayer = UpParent(UiTransform(listSkills));

        diagnostics.WriteJson("player-upgrades-ui-probe.json", new
        {
            Probe = "player-upgrades-native-ui-v1",
            ReadOnly = true,
            CapturedAtUtc = DateTime.UtcNow,
            Capture = playerUpgradesUiCaptureCount,
            FoundPlayerUpgrades = upgrades != null,
            MyPlayer = UiObjectSummary(myPlayer),
            PlayerUpgrades = UiObjectSummary(upgrades),
            PlayerUpgradesHierarchy = upgrades == null ? Array.Empty<object>() : UpNamedNodes(upgrades),
            MyPlayerChildren = myPlayer == null ? Array.Empty<object>() :
                Enumerable.Range(0, Math.Min(UpChildCount(myPlayer), 80))
                    .Select(i => UiObjectSummary(UpChild(myPlayer, i))).ToArray(),
            Trigger = UiObjectSummary(listSkills),
            TriggerType = UiTypeInventory(listSkills.GetType()),
            Instructions = "Read-only capture. Open Player Skills once from Player Upgrades; no other interaction is required."
        });
    }
}
''')

print("Read-only Player Upgrades sibling UI probe applied.")
