from pathlib import Path

root=Path("src/Main/HoopLandExpanded")
p=root/"CustomSkills.cs"
s=p.read_text()

# Reuse the existing ListSkills.OnEnable presentation hook so the probe runs after
# the native screen has finished constructing. No extra native target is needed.
old='Hook("list-presentation-reset","ListSkills","OnEnable",false,"System.Void",Array.Empty<string>(),prefix:nameof(BeforeSkillListPresentation))'
new='Hook("list-presentation-reset","ListSkills","OnEnable",false,"System.Void",Array.Empty<string>(),prefix:nameof(BeforeSkillListPresentation),postfix:nameof(AfterPlayerSkillsUiProbe))'
if s.count(old)!=1:
    raise SystemExit(f"ListSkills OnEnable probe anchor mismatch: {s.count(old)}")
s=s.replace(old,new,1)

# Capture the final on-screen row after ordinary/HLE presentation has run. This
# remains read-only: it records the rendered state but changes no row values.
old='''\tprivate static void SkillRow(object __instance, object __0, object __1, object __2) =>
\t\tSafe("skill-row", m => m.Present(__instance, __0, __1, __2));
'''
new='''\tprivate static void SkillRow(object __instance, object __0, object __1, object __2) =>
\t\tSafe("skill-row", m =>
\t\t{
\t\t\tm.Present(__instance, __0, __1, __2);
\t\t\tm.CapturePlayerSkillsRow(__instance, __0, __1, __2);
\t\t});
'''
old=old.replace('\\t','\t')
new=new.replace('\\t','\t')
if s.count(old)!=1:
    raise SystemExit(f"skill row probe anchor mismatch: {s.count(old)}")
s=s.replace(old,new,1)

# Make normal flush/stop boundaries persist whatever the player browsed.
old='public void Flush() { Status(); icons?.Flush(); passes?.Flush(); diagnostics.SkillJournal.Flush(); }'
new='public void Flush() { FlushPlayerSkillsUiProbe(); Status(); icons?.Flush(); passes?.Flush(); diagnostics.SkillJournal.Flush(); }'
if s.count(old)!=1:
    raise SystemExit(f"flush probe anchor mismatch: {s.count(old)}")
s=s.replace(old,new,1)

# Reset only the process-local probe capture when switching careers/branches.
old='''\tprivate static void ResetCareer()
\t{
\t\tinstance?.ResetSkillNotifications();
'''
new='''\tprivate static void ResetCareer()
\t{
\t\tinstance?.ResetPlayerSkillsUiProbe();
\t\tinstance?.ResetSkillNotifications();
'''
old=old.replace('\\t','\t')
new=new.replace('\\t','\t')
if s.count(old)!=1:
    raise SystemExit(f"career probe reset anchor mismatch: {s.count(old)}")
s=s.replace(old,new,1)

p.write_text(s)

(root/"PlayerSkillsUiProbe.cs").write_text(r'''using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using UnityEngine;

namespace HoopLandExpanded;

public sealed partial class CustomSkills
{
    private readonly List<object> playerSkillsUiOpenSnapshots = new();
    private readonly List<object> playerSkillsUiRows = new();
    private readonly HashSet<string> playerSkillsUiRowKeys = new(StringComparer.Ordinal);
    private object? playerSkillsUiListTypeInventory;
    private object? playerSkillsUiRowTypeInventory;
    private int playerSkillsUiOpenCount;
    private int playerSkillsUiDroppedRows;

    private static readonly BindingFlags UiFlags =
        BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static;

    private static string UiTypeName(object? value) => value?.GetType().FullName ?? "";

    private static object? UiReadProperty(object obj, string name)
    {
        try
        {
            PropertyInfo? p = obj.GetType().GetProperty(name, UiFlags);
            return p?.GetValue(obj);
        }
        catch { return null; }
    }

    private static string UiString(object? value)
    {
        if (value == null) return "";
        try
        {
            Type t = value.GetType();
            if (value is string s) return s;
            if (value is bool or byte or sbyte or short or ushort or int or uint or long or ulong
                or float or double or decimal or char || t.IsEnum)
                return Convert.ToString(value, CultureInfo.InvariantCulture) ?? "";
            return value.ToString() ?? "";
        }
        catch { return ""; }
    }

    private static string UiName(object? value)
    {
        if (value == null) return "";
        object? name = UiReadProperty(value, "name");
        if (name != null) return UiString(name);
        object? go = UiReadProperty(value, "gameObject");
        return go == null ? "" : UiString(UiReadProperty(go, "name"));
    }

    private static object? UiGameObject(object? value)
    {
        if (value == null) return null;
        if (value.GetType().FullName == "UnityEngine.GameObject") return value;
        return UiReadProperty(value, "gameObject");
    }

    private static object? UiTransform(object? value)
    {
        if (value == null) return null;
        object? transform = UiReadProperty(value, "transform");
        if (transform != null) return transform;
        object? go = UiGameObject(value);
        return go == null ? null : UiReadProperty(go, "transform");
    }

    private static string UiValue(object? value)
    {
        if (value == null) return "";
        try
        {
            Type t = value.GetType();
            if (value is string || value is bool || value is byte || value is sbyte || value is short
                || value is ushort || value is int || value is uint || value is long || value is ulong
                || value is float || value is double || value is decimal || value is char || t.IsEnum)
                return UiString(value);

            // Unity value types have useful ToString() implementations, while
            // native object wrappers do not need to be recursively serialized.
            string full = t.FullName ?? "";
            if (full.StartsWith("UnityEngine.Vector", StringComparison.Ordinal)
                || full == "UnityEngine.Rect" || full == "UnityEngine.Color"
                || full == "UnityEngine.Color32")
                return UiString(value);

            string name = UiName(value);
            return name.Length == 0 ? "<" + full + ">" : name + " <" + full + ">";
        }
        catch { return ""; }
    }

    private static object UiRect(object? transform)
    {
        if (transform == null) return new { Type = "", Values = Array.Empty<object>() };
        string[] names =
        {
            "anchoredPosition","anchoredPosition3D","sizeDelta","anchorMin","anchorMax",
            "pivot","offsetMin","offsetMax","localPosition","localScale","position","rect"
        };
        List<object> values = new();
        foreach (string name in names)
        {
            object? v = UiReadProperty(transform, name);
            if (v != null) values.Add(new { Name = name, Value = UiValue(v) });
        }
        return new { Type = UiTypeName(transform), Values = values.ToArray() };
    }

    private object UiObjectSummary(object? value)
    {
        if (value == null) return new { Type = "", Name = "", Active = (bool?)null, Rect = (object?)null };
        object? go = UiGameObject(value);
        bool? active = null;
        if (go != null)
        {
            object? a = UiReadProperty(go, "activeSelf");
            if (a is bool b) active = b;
        }
        return new
        {
            Type = UiTypeName(value),
            Name = UiName(value),
            Active = active,
            Rect = UiRect(UiTransform(value))
        };
    }

    private static int UiCollectionCount(object? value)
    {
        if (value == null || value is string) return -1;
        if (value is Array array) return array.Length;
        try
        {
            PropertyInfo? p = value.GetType().GetProperty("Count", UiFlags)
                ?? value.GetType().GetProperty("Length", UiFlags);
            return p == null ? -1 : Convert.ToInt32(p.GetValue(value), CultureInfo.InvariantCulture);
        }
        catch { return -1; }
    }

    private object UiMemberValue(object? value)
    {
        int count = UiCollectionCount(value);
        if (count >= 0)
        {
            List<object> sample = new();
            int max = Math.Min(count, 12);
            for (int i = 0; i < max; i++)
            {
                object? item = null;
                try
                {
                    if (value is Array array) item = array.GetValue(i);
                    else
                    {
                        PropertyInfo? indexer = value!.GetType().GetProperties(UiFlags)
                            .FirstOrDefault(p => p.Name == "Item" && p.GetIndexParameters().Length == 1);
                        if (indexer != null)
                        {
                            Type it = indexer.GetIndexParameters()[0].ParameterType;
                            item = indexer.GetValue(value, new object[] { it == typeof(long) ? (object)(long)i : i });
                        }
                    }
                }
                catch { }
                sample.Add(UiObjectSummary(item));
            }
            return new { Kind = "collection", Count = count, Sample = sample.ToArray() };
        }

        Type? t = value?.GetType();
        if (value == null || value is string || value is bool || value is byte || value is sbyte
            || value is short || value is ushort || value is int || value is uint || value is long
            || value is ulong || value is float || value is double || value is decimal || value is char
            || t?.IsEnum == true)
            return new { Kind = "scalar", Value = UiString(value) };

        return new { Kind = "object", Summary = UiObjectSummary(value) };
    }

    private object UiTypeInventory(Type type)
    {
        const BindingFlags flags = BindingFlags.Public | BindingFlags.NonPublic
            | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly;
        return new
        {
            Type = type.FullName,
            Fields = type.GetFields(flags)
                .Select(f => f.FieldType.FullName + " " + f.Name).OrderBy(x => x).ToArray(),
            Properties = type.GetProperties(flags)
                .Select(p => p.PropertyType.FullName + " " + p.Name).OrderBy(x => x).ToArray(),
            Methods = type.GetMethods(flags)
                .Where(m => !m.IsSpecialName)
                .Select(m => (m.IsStatic ? "static " : "instance ") + (m.ReturnType.FullName ?? m.ReturnType.Name)
                    + " " + m.Name + "(" + string.Join(", ",
                        m.GetParameters().Select(p => p.ParameterType.FullName ?? p.ParameterType.Name)) + ")")
                .OrderBy(x => x).ToArray()
        };
    }

    private object[] UiDeclaredMemberSnapshot(object instance)
    {
        Type type = instance.GetType();
        List<object> rows = new();
        foreach (FieldInfo f in type.GetFields(UiFlags | BindingFlags.DeclaredOnly).OrderBy(f => f.Name))
        {
            object? value = null;
            string error = "";
            try { value = f.GetValue(instance); } catch (Exception ex) { error = ex.GetBaseException().GetType().Name; }
            rows.Add(new { Member = f.Name, DeclaredType = f.FieldType.FullName, Source = "field", Error = error, Value = UiMemberValue(value) });
        }
        foreach (PropertyInfo prop in type.GetProperties(UiFlags | BindingFlags.DeclaredOnly)
                     .Where(p => p.GetIndexParameters().Length == 0).OrderBy(p => p.Name))
        {
            object? value = null;
            string error = "";
            try { value = prop.GetValue(instance); } catch (Exception ex) { error = ex.GetBaseException().GetType().Name; }
            rows.Add(new { Member = prop.Name, DeclaredType = prop.PropertyType.FullName, Source = "property", Error = error, Value = UiMemberValue(value) });
        }
        return rows.ToArray();
    }

    private object[] UiHierarchy(object rootValue)
    {
        object? root = UiTransform(rootValue);
        if (root == null) return Array.Empty<object>();
        List<object> nodes = new();
        WalkUiTransform(root, "", 0, nodes);
        return nodes.ToArray();
    }

    private void WalkUiTransform(object transform, string parentPath, int depth, List<object> nodes)
    {
        if (nodes.Count >= 480 || depth > 9) return;
        object? go = UiGameObject(transform);
        string name = go == null ? UiName(transform) : UiString(UiReadProperty(go, "name"));
        string path = parentPath.Length == 0 ? name : parentPath + "/" + name;

        List<object> components = new();
        if (go != null)
        {
            try
            {
                // Unity exposes GetComponents(System.Type). Invoke it by exact
                // signature when available; if this build wraps the Type
                // parameter differently, the rest of the hierarchy still records.
                MethodInfo? method = go.GetType().GetMethods(UiFlags)
                    .FirstOrDefault(m => m.Name == "GetComponents" && !m.IsGenericMethod
                        && m.GetParameters().Length == 1
                        && m.GetParameters()[0].ParameterType == typeof(Type));
                if (method != null)
                {
                    object? result = method.Invoke(go, new object[] { typeof(Component) });
                    int count = UiCollectionCount(result);
                    for (int i = 0; i < Math.Min(count, 24); i++)
                    {
                        object? c = null;
                        if (result is Array array) c = array.GetValue(i);
                        else if (result != null)
                        {
                            PropertyInfo? idx = result.GetType().GetProperties(UiFlags)
                                .FirstOrDefault(p => p.Name == "Item" && p.GetIndexParameters().Length == 1);
                            if (idx != null) c = idx.GetValue(result, new object[] { i });
                        }
                        if (c != null) components.Add(new { Type = UiTypeName(c), Name = UiName(c) });
                    }
                }
            }
            catch { }
        }

        bool? active = null;
        if (go != null && UiReadProperty(go, "activeSelf") is bool b) active = b;
        nodes.Add(new
        {
            Path = path,
            Depth = depth,
            Name = name,
            Active = active,
            Transform = UiRect(transform),
            Components = components.ToArray()
        });

        int childCount = 0;
        try
        {
            object? cc = UiReadProperty(transform, "childCount");
            if (cc != null) childCount = Convert.ToInt32(cc, CultureInfo.InvariantCulture);
        }
        catch { }
        MethodInfo? getChild = transform.GetType().GetMethods(UiFlags)
            .FirstOrDefault(m => m.Name == "GetChild" && m.GetParameters().Length == 1
                && m.GetParameters()[0].ParameterType == typeof(int));
        if (getChild == null) return;
        for (int i = 0; i < childCount && nodes.Count < 480; i++)
        {
            try
            {
                object? child = getChild.Invoke(transform, new object[] { i });
                if (child != null) WalkUiTransform(child, path, depth + 1, nodes);
            }
            catch { }
        }
    }

    private object UiTextMember(object row, string name)
    {
        try
        {
            object value = access.Need(row, name);
            return new
            {
                Member = name,
                Type = UiTypeName(value),
                Text = UiString(UiReadProperty(value, "text") ?? access.Read(value, "text")),
                Active = UiObjectSummary(value)
            };
        }
        catch (Exception ex)
        {
            return new { Member = name, Error = ex.GetBaseException().GetType().Name };
        }
    }

    private object UiProgressMember(object row)
    {
        try
        {
            object progress = access.Need(row, "progress");
            object? parent = null;
            object? localScale = null;
            try { parent = access.Read(progress, "parent"); } catch { }
            try { localScale = access.Read(progress, "localScale"); } catch { }
            return new
            {
                Type = UiTypeName(progress),
                Name = UiName(progress),
                Progress = UiObjectSummary(progress),
                Parent = UiObjectSummary(parent),
                LocalScale = UiValue(localScale),
                Members = UiDeclaredMemberSnapshot(progress)
            };
        }
        catch (Exception ex)
        {
            return new { Error = ex.GetBaseException().GetType().Name };
        }
    }

    private void CapturePlayerSkillsUi(object listSkills)
    {
        if (playerSkillsUiOpenCount >= 16) return;
        playerSkillsUiOpenCount++;
        playerSkillsUiListTypeInventory ??= UiTypeInventory(listSkills.GetType());

        object snapshot = new
        {
            Open = playerSkillsUiOpenCount,
            TimeUtc = DateTime.UtcNow,
            Screen = new
            {
                Width = Screen.width,
                Height = Screen.height,
                Dpi = Screen.dpi,
                FullScreen = Screen.fullScreen,
                CurrentResolution = Screen.currentResolution.ToString()
            },
            Root = UiObjectSummary(listSkills),
            DeclaredMembers = UiDeclaredMemberSnapshot(listSkills),
            Hierarchy = UiHierarchy(listSkills)
        };
        playerSkillsUiOpenSnapshots.Add(snapshot);
        FlushPlayerSkillsUiProbe();
    }

    private void CapturePlayerSkillsRow(object row, object sprites, object player, object skillData)
    {
        if (playerSkillsUiRows.Count >= 512)
        {
            playerSkillsUiDroppedRows++;
            return;
        }

        string skillId = "";
        int category = -1;
        try { skillId = access.Text(skillData, "id"); } catch { }
        try { category = access.Int(skillData, "category"); } catch { }
        CustomSkillDefinition? definition = CustomSkillCatalog.Find(skillId);

        string level = "";
        string description = "";
        string status = "";
        try { level = access.Text(access.Need(row, "level"), "text"); } catch { }
        try { description = access.Text(access.Need(row, "description"), "text"); } catch { }
        try { status = access.Text(access.Need(row, "status"), "text"); } catch { }

        object progress = UiProgressMember(row);
        string key = string.Join("|", skillId, category.ToString(CultureInfo.InvariantCulture),
            level, description, status, System.Text.Json.JsonSerializer.Serialize(progress));
        if (!playerSkillsUiRowKeys.Add(key)) return;

        playerSkillsUiRowTypeInventory ??= UiTypeInventory(row.GetType());

        int rank = -1;
        int xp = -1;
        bool? equipped = null;
        try
        {
            object? record = SkillXp(player, skillId);
            if (record != null)
            {
                rank = access.Int(record, "level");
                xp = access.Int(record, "xp");
                equipped = access.Bool(record, "equipped");
            }
        }
        catch { }

        playerSkillsUiRows.Add(new
        {
            TimeUtc = DateTime.UtcNow,
            SkillId = skillId,
            NativeCategory = category,
            Hle = definition != null,
            Icon = definition?.Icon ?? false,
            Legendary = definition?.Legendary ?? false,
            PlayerId = SafePlayerId(player),
            Rank = rank,
            Xp = xp,
            Equipped = equipped,
            Text = new
            {
                Level = level,
                Description = description,
                Status = status,
                AllDeclared = UiDeclaredMemberSnapshot(row)
            },
            Progress = progress,
            Row = UiObjectSummary(row),
            Hierarchy = UiHierarchy(row)
        });
        FlushPlayerSkillsUiProbe();
    }

    private int SafePlayerId(object player)
    {
        try { return access.Int(player, "id"); } catch { return -1; }
    }

    private void FlushPlayerSkillsUiProbe()
    {
        try
        {
            diagnostics.WriteJson("player-skills-ui-probe.json", new
            {
                Probe = "player-skills-native-ui-v1",
                ReadOnly = true,
                CapturedAtUtc = DateTime.UtcNow,
                Instructions = "Open Player Skills, click all four native categories, and scroll each list. The probe changes no UI state.",
                ListSkillsType = playerSkillsUiListTypeInventory,
                SkillsObjectType = playerSkillsUiRowTypeInventory,
                Opens = playerSkillsUiOpenSnapshots.ToArray(),
                Rows = playerSkillsUiRows.ToArray(),
                DroppedRows = playerSkillsUiDroppedRows
            });
        }
        catch (Exception ex)
        {
            Error("player-skills-ui-probe-write", ex);
        }
    }

    private void ResetPlayerSkillsUiProbe()
    {
        playerSkillsUiOpenSnapshots.Clear();
        playerSkillsUiRows.Clear();
        playerSkillsUiRowKeys.Clear();
        playerSkillsUiListTypeInventory = null;
        playerSkillsUiRowTypeInventory = null;
        playerSkillsUiOpenCount = 0;
        playerSkillsUiDroppedRows = 0;
    }

    private static void AfterPlayerSkillsUiProbe(object __instance)
    {
        Safe("player-skills-ui-probe", m => m.CapturePlayerSkillsUi(__instance));
    }
}
''')

print("Read-only Player Skills UI probe applied.")
