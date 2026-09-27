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
using UnityEngine;
using Il2CppInterop.Runtime;

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

    private object? UpComponents(object? gameObject)
    {
        if (gameObject == null) return null;
        try
        {
            MethodInfo? from = typeof(Il2CppType).GetMethods(BindingFlags.Public | BindingFlags.Static)
                .FirstOrDefault(m => m.Name == "From"
                    && m.GetParameters().Length >= 1
                    && m.GetParameters()[0].ParameterType == typeof(Type));
            object? nativeType = from?.Invoke(null, new object?[] { typeof(Component) });
            if (nativeType == null) return null;

            MethodInfo? getComponents = gameObject.GetType().GetMethods(UiFlags)
                .FirstOrDefault(m => m.Name == "GetComponents"
                    && !m.IsGenericMethod
                    && m.GetParameters().Length == 1
                    && (m.GetParameters()[0].ParameterType.FullName ?? "")
                        .Contains("Il2CppSystem.Type", StringComparison.Ordinal));
            return getComponents?.Invoke(gameObject, new[] { nativeType });
        }
        catch { return null; }
    }

    private object? UpCollectionItem(object collection, int index)
    {
        try
        {
            if (collection is Array array) return array.GetValue(index);
            PropertyInfo? indexer = collection.GetType().GetProperties(UiFlags)
                .FirstOrDefault(p => p.Name == "Item" && p.GetIndexParameters().Length == 1);
            if (indexer == null) return null;
            Type t = indexer.GetIndexParameters()[0].ParameterType;
            object key = t == typeof(long) ? (object)(long)index : index;
            return indexer.GetValue(collection, new[] { key });
        }
        catch { return null; }
    }

    private object UpEventSnapshot(object? evt)
    {
        if (evt == null) return new { Type = "", Count = -1, Calls = Array.Empty<object>() };
        Type type = evt.GetType();
        int count = -1;
        List<object> calls = new();
        try
        {
            MethodInfo? countMethod = type.GetMethods(UiFlags)
                .FirstOrDefault(m => m.Name == "GetPersistentEventCount"
                    && m.GetParameters().Length == 0);
            if (countMethod != null)
                count = Convert.ToInt32(countMethod.Invoke(evt, null), CultureInfo.InvariantCulture);

            MethodInfo? nameMethod = type.GetMethods(UiFlags)
                .FirstOrDefault(m => m.Name == "GetPersistentMethodName"
                    && m.GetParameters().Length == 1);
            MethodInfo? targetMethod = type.GetMethods(UiFlags)
                .FirstOrDefault(m => m.Name == "GetPersistentTarget"
                    && m.GetParameters().Length == 1);

            for (int i = 0; i >= 0 && i < Math.Min(count, 12); i++)
            {
                object? target = null;
                string method = "";
                try { method = UiString(nameMethod?.Invoke(evt, new object[] { i })); } catch { }
                try { target = targetMethod?.Invoke(evt, new object[] { i }); } catch { }
                calls.Add(new
                {
                    Index = i,
                    Method = method,
                    Target = UiObjectSummary(target),
                    TargetType = target?.GetType().FullName ?? ""
                });
            }
        }
        catch { }

        return new
        {
            Type = type.FullName ?? type.Name,
            Count = count,
            Calls = calls.ToArray(),
            Inventory = UiTypeInventory(type)
        };
    }

    private object UpComponentSnapshot(object component)
    {
        Type type = component.GetType();
        object? onClick = null;
        try { onClick = UiReadProperty(component, "onClick"); } catch { }

        bool custom = !(type.FullName ?? "").StartsWith("UnityEngine.", StringComparison.Ordinal)
            && !(type.FullName ?? "").StartsWith("Il2CppUnityEngine.", StringComparison.Ordinal)
            && !(type.FullName ?? "").StartsWith("TMPro.", StringComparison.Ordinal);

        object? declared = null;
        if (custom || (type.Name ?? "").Contains("Button", StringComparison.OrdinalIgnoreCase)
            || onClick != null)
        {
            try { declared = UiDeclaredMemberSnapshot(component); } catch { }
        }

        return new
        {
            Type = type.FullName ?? type.Name,
            Name = UiName(component),
            Enabled = UiString(UiReadProperty(component, "enabled")),
            Interactable = UiString(UiReadProperty(component, "interactable")),
            OnClick = UpEventSnapshot(onClick),
            Inventory = UiTypeInventory(type),
            DeclaredMembers = declared
        };
    }

    private object[] UpComponentList(object? transform)
    {
        object? go = UiGameObject(transform);
        object? collection = UpComponents(go);
        int count = UiCollectionCount(collection);
        if (collection == null || count < 0) return Array.Empty<object>();

        List<object> rows = new();
        for (int i = 0; i < Math.Min(count, 24); i++)
        {
            object? component = UpCollectionItem(collection, i);
            if (component == null) continue;
            rows.Add(UpComponentSnapshot(component));
        }
        return rows.ToArray();
    }

    private bool UpInterestingNode(string path, string name)
    {
        string p = path.ToLowerInvariant();
        string n = name.ToLowerInvariant();
        return n == "player upgrades"
            || n == "skill points"
            || n == "skills"
            || n == "buttons"
            || n == "skill button"
            || n.Contains("back")
            || p.Contains("/skills/")
            || p.EndsWith("/skills", StringComparison.Ordinal)
            || p.EndsWith("/skill points", StringComparison.Ordinal);
    }

    private object[] UpDetailedNodes(object rootValue)
    {
        object? root = UiTransform(rootValue);
        if (root == null) return Array.Empty<object>();

        List<object> rows = new();
        Queue<(object Transform, string Parent, int Depth)> queue = new();
        queue.Enqueue((root, "", 0));

        while (queue.Count > 0 && rows.Count < 160)
        {
            var item = queue.Dequeue();
            object transform = item.Transform;
            object? go = UiGameObject(transform);
            string name = go == null ? UiName(transform) : UiString(UiReadProperty(go, "name"));
            string path = item.Parent.Length == 0 ? name : item.Parent + "/" + name;

            if (UpInterestingNode(path, name))
            {
                rows.Add(new
                {
                    Path = path,
                    Depth = item.Depth,
                    Name = name,
                    Active = UiObjectSummary(go ?? transform),
                    Components = UpComponentList(transform)
                });
            }

            if (item.Depth >= 10) continue;
            int childCount = UpChildCount(transform);
            for (int i = 0; i < Math.Min(childCount, 100); i++)
            {
                object? child = UpChild(transform, i);
                if (child != null) queue.Enqueue((child, path, item.Depth + 1));
            }
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
            PlayerUpgradesHierarchy = upgrades == null ? Array.Empty<object>() : UiHierarchy(upgrades),
            PlayerUpgradesDetailedNodes = upgrades == null ? Array.Empty<object>() : UpDetailedNodes(upgrades),
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
