from pathlib import Path

root=Path("src/Main/HoopLandExpanded")
probe=root/"PlayerSkillsUiProbe.cs"
s=probe.read_text()

old='''    private static void AfterPlayerSkillsUiProbe(object __instance)
    {
        Safe("player-skills-ui-probe", m => m.CapturePlayerSkillsUi(__instance));
    }
'''
new='''    private static void AfterPlayerSkillsUiProbe(object __instance)
    {
        Safe("player-skills-ui-probe", m => m.CapturePlayerSkillsUi(__instance));
        Safe("player-navigation-ui-probe", m => m.CapturePlayerNavigationUi(__instance));
    }
'''
if old not in s:
    raise SystemExit("Player Skills probe callback anchor missing")
probe.write_text(s.replace(old,new,1))

(root/"PlayerNavigationUiProbe.cs").write_text(r'''using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;

namespace HoopLandExpanded;

public sealed partial class CustomSkills
{
    private int playerNavigationUiCaptureCount;

    private static object? NavParent(object? transform)
    {
        return transform == null ? null : UiReadProperty(transform, "parent");
    }

    private static object? NavChild(object transform, int index)
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

    private static int NavChildCount(object? transform)
    {
        if (transform == null) return 0;
        try
        {
            object? value = UiReadProperty(transform, "childCount");
            return value == null ? 0 : Convert.ToInt32(value, CultureInfo.InvariantCulture);
        }
        catch { return 0; }
    }

    private static string NavPath(object? transform)
    {
        List<string> parts = new();
        object? current = transform;
        for (int i = 0; current != null && i < 24; i++)
        {
            string name = UiName(current);
            parts.Add(string.IsNullOrWhiteSpace(name) ? "<unnamed>" : name);
            current = NavParent(current);
        }
        parts.Reverse();
        return string.Join("/", parts);
    }

    private object[] NavChildren(object? transform)
    {
        if (transform == null) return Array.Empty<object>();
        List<object> rows = new();
        int count = Math.Min(NavChildCount(transform), 160);
        for (int i = 0; i < count; i++)
        {
            object? child = NavChild(transform, i);
            if (child == null) continue;
            rows.Add(new
            {
                Index = i,
                Name = UiName(child),
                Path = NavPath(child),
                Summary = UiObjectSummary(child)
            });
        }
        return rows.ToArray();
    }

    private object[] NavInterestingSiblingHierarchies(object? parent, object? self)
    {
        if (parent == null) return Array.Empty<object>();
        List<object> rows = new();
        int count = Math.Min(NavChildCount(parent), 160);
        for (int i = 0; i < count && rows.Count < 18; i++)
        {
            object? child = NavChild(parent, i);
            if (child == null || ReferenceEquals(child, self)) continue;
            string name = UiName(child);
            string lower = name.ToLowerInvariant();
            if (!lower.Contains("player") && !lower.Contains("skill")
                && !lower.Contains("upgrade") && !lower.Contains("profile")
                && !lower.Contains("career") && !lower.Contains("development"))
                continue;
            rows.Add(new
            {
                Index = i,
                Name = name,
                Path = NavPath(child),
                Summary = UiObjectSummary(child),
                Hierarchy = UiHierarchy(child)
            });
        }
        return rows.ToArray();
    }

    private object[] NavAncestors(object listSkills)
    {
        List<object> rows = new();
        object? current = UiTransform(listSkills);
        for (int depth = 0; current != null && depth < 18; depth++)
        {
            object? parent = NavParent(current);
            rows.Add(new
            {
                Depth = depth,
                Name = UiName(current),
                Path = NavPath(current),
                Summary = UiObjectSummary(current),
                Parent = UiObjectSummary(parent),
                ParentChildren = NavChildren(parent),
                InterestingSiblingHierarchies = NavInterestingSiblingHierarchies(parent, current)
            });
            current = parent;
        }
        return rows.ToArray();
    }

    private void CapturePlayerNavigationUi(object listSkills)
    {
        if (playerNavigationUiCaptureCount >= 8) return;
        playerNavigationUiCaptureCount++;

        object? start = UiTransform(listSkills);
        object? root = start;
        for (int i = 0; root != null && i < 24; i++)
        {
            object? parent = NavParent(root);
            if (parent == null) break;
            root = parent;
        }

        diagnostics.WriteJson("player-navigation-ui-probe.json", new
        {
            Probe = "player-navigation-transform-only-v2",
            ReadOnly = true,
            CapturedAtUtc = DateTime.UtcNow,
            Capture = playerNavigationUiCaptureCount,
            Instructions = "Transform-only probe: starts from ListSkills and inspects parents/siblings using APIs already validated by the Player Skills probe.",
            Trigger = UiObjectSummary(listSkills),
            TriggerType = UiTypeInventory(listSkills.GetType()),
            TriggerMembers = UiDeclaredMemberSnapshot(listSkills),
            TriggerHierarchy = UiHierarchy(listSkills),
            Ancestors = NavAncestors(listSkills),
            Root = UiObjectSummary(root),
            RootHierarchy = root == null ? Array.Empty<object>() : UiHierarchy(root)
        });
    }
}
''')

print("Transform-only player-navigation UI probe applied.")
