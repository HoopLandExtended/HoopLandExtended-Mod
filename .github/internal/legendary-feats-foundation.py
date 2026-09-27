from pathlib import Path

root=Path("src/Main/HoopLandExpanded")
p=root/"CustomSkills.cs"
s=p.read_text()

# Add a postfix to the already-established ListSkills.OnEnable presentation hook.
lines=s.splitlines(True)
matches=[i for i,line in enumerate(lines)
         if 'Hook("list-presentation-reset"' in line
         and '"ListSkills"' in line and '"OnEnable"' in line
         and 'BeforeSkillListPresentation' in line]
if len(matches)!=1:
    raise SystemExit(f"ListSkills OnEnable feat UI hook anchor mismatch: {len(matches)}")
i=matches[0]
line=lines[i]
if 'AfterLegendaryFeatUi' not in line:
    end='\n' if line.endswith('\n') else ''
    body=line[:-1] if end else line
    if body.rstrip().endswith('),'):
        pos=body.rfind('),')
        body=body[:pos]+',postfix:nameof(AfterLegendaryFeatUi)),'+body[pos+2:]
    elif body.rstrip().endswith(')'):
        pos=body.rfind(')')
        body=body[:pos]+',postfix:nameof(AfterLegendaryFeatUi))'+body[pos+1:]
    else:
        raise SystemExit("ListSkills OnEnable hook line shape unsupported")
    lines[i]=body+end
s=''.join(lines)
p.write_text(s)

# Replace the old special classification facade with College/Pro Feat semantics
# while preserving legacy enum names for compatibility with existing runtime code.
rules=root/"SpecialSkillLoadoutRules.cs"
rules.write_text(r'''namespace HoopLandExpanded;

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
        return LegendaryFeatCatalog.Category(definition.Id) switch
        {
            LegendaryFeatCategory.College => SpecialSkillSlot.Icon,
            LegendaryFeatCategory.Pro => SpecialSkillSlot.Legendary,
            _ => SpecialSkillSlot.None
        };
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
        SpecialSkillSlot.Icon => "COLLEGE FEAT",
        SpecialSkillSlot.Legendary => "PRO FEAT",
        _ => "ORDINARY"
    };
}
''')

(root/"LegendaryFeatCatalog.cs").write_text(r'''using System;
using System.Collections.Generic;
using System.Linq;

namespace HoopLandExpanded;

public enum LegendaryFeatCategory
{
    None = 0,
    College = 1,
    Pro = 2
}

public sealed record LegendaryFeatDefinition(string Id, string Name, LegendaryFeatCategory Category);

public static class LegendaryFeatCatalog
{
    private static readonly LegendaryFeatDefinition[] definitions =
    {
        new("HLE_IC01", "Headliner", LegendaryFeatCategory.College),
        new("HLE_IC02", "Table Setter", LegendaryFeatCategory.College),
        new("HLE_IC03", "Two-Way Force", LegendaryFeatCategory.College),
        new("HLE_IC04", "Grab & Go", LegendaryFeatCategory.College),
        new("HLE_IC05", "March Hero", LegendaryFeatCategory.College),

        new("HLE_FR05", "Human Torch", LegendaryFeatCategory.Pro),
        new("HLE_FR06", "Century", LegendaryFeatCategory.Pro),
        new("HLE_FR07", "Total Control", LegendaryFeatCategory.Pro),
        new("HLE_LG01", "Maestro", LegendaryFeatCategory.Pro),
        new("HLE_LG02", "Unstoppable", LegendaryFeatCategory.Pro),
        new("HLE_LG03", "Glass Sovereign", LegendaryFeatCategory.Pro),
        new("HLE_LG04", "Defensive Colossus", LegendaryFeatCategory.Pro)
    };

    private static readonly Dictionary<string, LegendaryFeatDefinition> byId =
        definitions.ToDictionary(x => x.Id, StringComparer.Ordinal);

    public static IReadOnlyList<LegendaryFeatDefinition> All => definitions;

    public static LegendaryFeatDefinition? Find(string? id) =>
        id != null && byId.TryGetValue(id, out LegendaryFeatDefinition? value) ? value : null;

    public static LegendaryFeatCategory Category(string? id) => Find(id)?.Category ?? LegendaryFeatCategory.None;

    public static bool IsFeat(string? id) => Category(id) != LegendaryFeatCategory.None;

    public static IEnumerable<LegendaryFeatDefinition> InCategory(LegendaryFeatCategory category) =>
        definitions.Where(x => x.Category == category);
}
''')

(root/"LegendaryFeatUi.cs").write_text(r'''using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;
using Il2CppInterop.Runtime;

namespace HoopLandExpanded;

public sealed partial class CustomSkills
{
    private GameObject? legendaryFeatScreen;
    private GameObject? legendaryFeatMenuButton;
    private GameObject? legendaryFeatSourceScreen;
    private GameObject? legendaryFeatMenu;
    private GameObject? legendaryFeatRowPrefab;
    private Transform? legendaryFeatListParent;
    private LegendaryFeatCategory legendaryFeatCategory = LegendaryFeatCategory.College;
    private readonly List<GameObject> legendaryFeatRows = new();
    private readonly List<object> legendaryFeatCallbacks = new();
    private bool buildingLegendaryFeatUi;

    private static IEnumerable<Transform> FeatWalk(Transform root, int maxDepth = 10)
    {
        Queue<(Transform T, int D)> queue = new();
        queue.Enqueue((root, 0));
        int seen = 0;
        while (queue.Count > 0 && seen < 1400)
        {
            var item = queue.Dequeue();
            yield return item.T;
            seen++;
            if (item.D >= maxDepth) continue;
            for (int i = 0; i < item.T.childCount; i++)
                queue.Enqueue((item.T.GetChild(i), item.D + 1));
        }
    }

    private static string FeatShortTypeName(string typeName)
    {
        int index = typeName.LastIndexOf('.');
        return index < 0 ? typeName : typeName[(index + 1)..];
    }

    private object? FeatComponent(GameObject gameObject, string typeName)
    {
        string shortName = FeatShortTypeName(typeName);

        Type? wrapper = null;
        try { wrapper = access.Type(typeName); } catch { }
        if (wrapper == null)
        {
            foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    wrapper = assembly.GetType(typeName, false);
                    if (wrapper != null) break;
                }
                catch { }
            }
        }

        if (wrapper != null)
        {
            try
            {
                Component? component = gameObject.GetComponent(Il2CppType.From(wrapper));
                if (component != null) return component;
            }
            catch { }
        }

        foreach (string candidate in new[] { typeName, shortName })
        {
            try
            {
                Component? component = gameObject.GetComponent(candidate);
                if (component != null) return component;
            }
            catch { }
        }
        return null;
    }

    private object? FeatText(Transform? transform) =>
        transform == null ? null : FeatComponent(transform.gameObject, "UnityEngine.UI.Text");

    private object? FeatButton(Transform? transform) =>
        transform == null ? null : FeatComponent(transform.gameObject, "UnityEngine.UI.Button");

    private static Transform? FeatTransform(object? component)
    {
        if (component is Component unityComponent) return unityComponent.transform;
        try
        {
            PropertyInfo? p = component?.GetType().GetProperty("transform",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            return p?.GetValue(component) as Transform;
        }
        catch { return null; }
    }

    private static GameObject? FeatGameObject(object? component)
    {
        if (component is Component unityComponent) return unityComponent.gameObject;
        try
        {
            PropertyInfo? p = component?.GetType().GetProperty("gameObject",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            return p?.GetValue(component) as GameObject;
        }
        catch { return null; }
    }

    private string FeatTextValue(object? text)
    {
        if (text == null) return "";
        try { return access.Text(text, "text"); }
        catch { return ""; }
    }

    private void FeatSetText(object? text, string value)
    {
        if (text == null) return;
        try { access.Set(text, "text", value); } catch { }
    }

    private string FeatCombinedText(Transform root)
    {
        List<string> values = new();
        foreach (Transform t in FeatWalk(root, 5))
        {
            object? text = FeatText(t);
            string value = FeatTextValue(text);
            if (!string.IsNullOrWhiteSpace(value))
                values.Add(value.Trim());
        }
        return string.Join(" | ", values);
    }

    private void FeatSetFirstText(Transform root, string value)
    {
        foreach (Transform t in FeatWalk(root, 5))
        {
            object? text = FeatText(t);
            if (text == null) continue;
            FeatSetText(text, value);
            return;
        }
    }

    private void FeatSetTextAt(Transform root, string path, string value)
    {
        Transform? t = root.Find(path);
        if (t != null) FeatSetText(FeatText(t), value);
    }

    private Transform? FeatFindMenuItem(Transform root, string token)
    {
        Transform? best = null;
        int bestScore = int.MinValue;

        foreach (Transform t in FeatWalk(root, 10))
        {
            string name = t.name ?? "";
            string text = FeatCombinedText(t);
            bool nameMatch = name.IndexOf(token, StringComparison.OrdinalIgnoreCase) >= 0;
            bool textMatch = text.IndexOf(token, StringComparison.OrdinalIgnoreCase) >= 0;
            if (!nameMatch && !textMatch) continue;

            Transform? candidate = t;
            for (int climb = 0; candidate != null && candidate != root.parent && climb < 5; climb++)
            {
                string candidateName = candidate.name ?? "";
                int score = 0;
                if (candidateName.IndexOf("button", StringComparison.OrdinalIgnoreCase) >= 0) score += 100;
                if (candidateName.IndexOf(token, StringComparison.OrdinalIgnoreCase) >= 0) score += 60;
                if (FeatButton(candidate) != null) score += 80;
                if (nameMatch) score += 20;
                if (textMatch) score += 10;
                if (score > bestScore)
                {
                    best = candidate;
                    bestScore = score;
                }
                if (score >= 180) break;
                candidate = candidate.parent;
            }
        }
        return best;
    }

    private object? FeatFindFirstButton(Transform root)
    {
        foreach (Transform t in FeatWalk(root, 5))
        {
            object? button = FeatButton(t);
            if (button != null) return button;
        }
        return null;
    }

    private void FeatWireButton(object button, Action callback)
    {
        object onClick = access.Need(button, "onClick");
        try { access.Call(onClick, "RemoveAllListeners"); } catch { }

        MethodInfo? addListener = onClick.GetType().GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
            .Where(m => m.Name == "AddListener" && !m.IsGenericMethod)
            .SingleOrDefault(m => m.GetParameters().Length == 1);
        if (addListener == null)
            throw new MissingMethodException(onClick.GetType().FullName, "AddListener");

        Type nativeDelegateType = addListener.GetParameters()[0].ParameterType;
        MethodInfo convert = typeof(DelegateSupport).GetMethods(BindingFlags.Public | BindingFlags.Static)
            .Single(m => m.Name == "ConvertDelegate" && m.IsGenericMethodDefinition
                && m.GetGenericArguments().Length == 1 && m.GetParameters().Length == 1);
        object converted = convert.MakeGenericMethod(nativeDelegateType)
            .Invoke(null, new object[] { callback })
            ?? throw new InvalidOperationException("IL2CPP delegate conversion returned null");

        legendaryFeatCallbacks.Add(converted);
        addListener.Invoke(onClick, new[] { converted });
    }

    private object? CareerFeatPlayer()
    {
        try
        {
            object? league = access.Static("GameManager", "currentLeague");
            if (league == null) return null;
            object season = access.Need(league, "season");
            return FindCurrentPlayer(access.Int(season, "playerId"));
        }
        catch
        {
            return null;
        }
    }

    private static string FeatStateLabel(object? skill, CustomSkillAccess access)
    {
        if (skill == null || access.Int(skill, "level") <= 0) return "LOCKED";
        return access.Bool(skill, "equipped") ? "EQUIPPED" : "EARNED";
    }

    private static string RelativeTransformPath(Transform root, Transform target)
    {
        List<string> names = new();
        Transform? current = target;
        while (current != null && current != root)
        {
            names.Add(current.name);
            current = current.parent;
        }
        if (current != root) return "";
        names.Reverse();
        return string.Join("/", names);
    }

    private void EnsureLegendaryFeatUi(object listSkills)
    {
        if (buildingLegendaryFeatUi) return;
        if (listSkills is not Component sourceComponent) return;
        GameObject source = sourceComponent.gameObject;
        if (!string.Equals(source.name, "Player Skills", StringComparison.Ordinal)) return;

        legendaryFeatSourceScreen = source;
        Transform? myPlayer = source.transform.parent;
        if (myPlayer == null || !string.Equals(myPlayer.name, "My Player", StringComparison.Ordinal)) return;
        legendaryFeatMenu = myPlayer.Find("Menu")?.gameObject;

        GameObject? sourceRowPrefab = null;
        Transform? sourceListParent = null;
        GameObject? sourceOptions = null;
        try { sourceRowPrefab = access.Need(listSkills, "listObject") as GameObject; } catch { }
        try { sourceListParent = access.Need(listSkills, "listParent") as Transform; } catch { }
        try { sourceOptions = access.Need(listSkills, "skillOptions") as GameObject; } catch { }

        if (legendaryFeatScreen == null)
        {
            buildingLegendaryFeatUi = true;
            try
            {
                legendaryFeatScreen = UnityEngine.Object.Instantiate(source, myPlayer);
                legendaryFeatScreen.name = "Legendary Feats";
                legendaryFeatScreen.SetActive(false);

                legendaryFeatRowPrefab = sourceRowPrefab;
                if (sourceListParent != null)
                {
                    string path = RelativeTransformPath(source.transform, sourceListParent);
                    if (!string.IsNullOrEmpty(path))
                        legendaryFeatListParent = legendaryFeatScreen.transform.Find(path);
                }

                if (sourceOptions != null)
                {
                    string path = RelativeTransformPath(source.transform, sourceOptions.transform);
                    Transform? clonedOptions = string.IsNullOrEmpty(path) ? null : legendaryFeatScreen.transform.Find(path);
                    if (clonedOptions != null) clonedOptions.gameObject.SetActive(false);
                }

                ConfigureLegendaryFeatScreen();
            }
            finally
            {
                buildingLegendaryFeatUi = false;
            }
        }

        EnsureLegendaryFeatMenuButton();
        WriteLegendaryFeatUiStatus("ready");
    }

    private void ConfigureLegendaryFeatScreen()
    {
        if (legendaryFeatScreen == null) return;
        Transform root = legendaryFeatScreen.transform;

        FeatSetTextAt(root, "Season Header/Mask/Text 1", "LEGENDARY FEATS");
        FeatSetTextAt(root, "Season Header/Mask/Text 2", "LEGENDARY FEATS");

        Transform? categories = root.Find("Panel/Categories");
        if (categories != null)
        {
            Transform? college = categories.Find("Finishing");
            Transform? pro = categories.Find("Shooting");
            Transform? creating = categories.Find("Creating");
            Transform? defense = categories.Find("Defense");
            Transform? points = categories.Find("Points");

            if (college != null)
            {
                FeatSetTextAt(college, "Header", "COLLEGE");
                object? b = FeatButton(college.Find("Buttons/Skill Button"));
                if (b != null) FeatWireButton(b,
                    () => SelectLegendaryFeatCategory(LegendaryFeatCategory.College));
            }
            if (pro != null)
            {
                FeatSetTextAt(pro, "Header", "PRO");
                object? b = FeatButton(pro.Find("Buttons/Skill Button"));
                if (b != null) FeatWireButton(b,
                    () => SelectLegendaryFeatCategory(LegendaryFeatCategory.Pro));
            }
            if (creating != null) creating.gameObject.SetActive(false);
            if (defense != null) defense.gameObject.SetActive(false);
            if (points != null) FeatSetTextAt(points, "Header", "EARNED");
        }

        ClearLegendaryFeatRows();
    }

    private void EnsureLegendaryFeatMenuButton()
    {
        if (legendaryFeatMenuButton != null || legendaryFeatMenu == null) return;

        Transform? sourceItem = FeatFindMenuItem(legendaryFeatMenu.transform, "SKILL");
        if (sourceItem == null)
        {
            Event("legendary-feats-ui-menu-missing",
                new
                {
                    Reason = "player-skills-menu-item-not-found",
                    TopLevelChildren = Enumerable.Range(0, legendaryFeatMenu.transform.childCount)
                        .Select(i => legendaryFeatMenu.transform.GetChild(i).name).ToArray()
                });
            return;
        }

        Transform parent = sourceItem.parent;
        GameObject clone = UnityEngine.Object.Instantiate(sourceItem.gameObject, parent);
        clone.name = "Legendary Feats Button";
        legendaryFeatMenuButton = clone;

        object? sourceButton = FeatFindFirstButton(sourceItem);
        object? button = FeatFindFirstButton(clone.transform);
        if (button == null)
        {
            Event("legendary-feats-ui-menu-missing",
                new
                {
                    Reason = "cloned-button-component-not-found",
                    SourceItem = sourceItem.name,
                    SourcePath = RelativeTransformPath(legendaryFeatMenu.transform, sourceItem)
                });
            UnityEngine.Object.Destroy(clone);
            legendaryFeatMenuButton = null;
            return;
        }

        FeatSetFirstText(clone.transform, "LEGENDARY FEATS");
        if (sourceButton != null)
            PlaceLegendaryFeatMenuButtonFallback(sourceButton, button);
        else
            clone.transform.SetSiblingIndex(Math.Min(sourceItem.GetSiblingIndex() + 1, parent.childCount - 1));
        FeatWireButton(button, OpenLegendaryFeats);
    }

    private void PlaceLegendaryFeatMenuButtonFallback(object sourceButton, object clonedButton)
    {
        Transform? sourceTransform = FeatTransform(sourceButton);
        Transform? cloneTransform = FeatTransform(clonedButton);
        RectTransform? sourceRect = sourceTransform as RectTransform;
        RectTransform? cloneRect = cloneTransform as RectTransform;
        if (sourceRect == null || cloneRect == null) return;

        List<RectTransform> siblings = new();
        Transform parent = sourceRect.parent;
        for (int i = 0; i < parent.childCount; i++)
        {
            Transform child = parent.GetChild(i);
            if (child == cloneRect) continue;
            if (FeatButton(child) != null && child is RectTransform rt) siblings.Add(rt);
        }

        RectTransform? next = siblings
            .Where(x => x.GetSiblingIndex() > sourceRect.GetSiblingIndex())
            .OrderBy(x => x.GetSiblingIndex()).FirstOrDefault();
        RectTransform? previous = siblings
            .Where(x => x.GetSiblingIndex() < sourceRect.GetSiblingIndex())
            .OrderByDescending(x => x.GetSiblingIndex()).FirstOrDefault();

        Vector2 delta = next != null
            ? next.anchoredPosition - sourceRect.anchoredPosition
            : previous != null
                ? sourceRect.anchoredPosition - previous.anchoredPosition
                : new Vector2(0f, -12f);

        int sourceIndex = sourceRect.GetSiblingIndex();
        foreach (RectTransform sibling in siblings.Where(x => x.GetSiblingIndex() > sourceIndex))
            sibling.anchoredPosition += delta;

        cloneRect.anchoredPosition = sourceRect.anchoredPosition + delta;
        cloneRect.SetSiblingIndex(Math.Min(sourceIndex + 1, parent.childCount - 1));
    }

    private void OpenLegendaryFeats()
    {
        if (legendaryFeatScreen == null) return;
        if (legendaryFeatMenu != null) legendaryFeatMenu.SetActive(false);
        if (legendaryFeatSourceScreen != null) legendaryFeatSourceScreen.SetActive(false);
        legendaryFeatScreen.SetActive(true);
        RefreshLegendaryFeatScreen();
        Event("legendary-feats-ui-opened",
            new { Category = legendaryFeatCategory.ToString() });
    }

    private void SelectLegendaryFeatCategory(LegendaryFeatCategory category)
    {
        if (category == LegendaryFeatCategory.None) return;
        legendaryFeatCategory = category;
        RefreshLegendaryFeatScreen();
    }

    private void ClearLegendaryFeatRows()
    {
        foreach (GameObject row in legendaryFeatRows)
            if (row != null) UnityEngine.Object.Destroy(row);
        legendaryFeatRows.Clear();

        if (legendaryFeatListParent == null) return;
        for (int i = legendaryFeatListParent.childCount - 1; i >= 0; i--)
        {
            Transform child = legendaryFeatListParent.GetChild(i);
            if (child == null) continue;
            child.gameObject.SetActive(false);
        }
    }

    private void RefreshLegendaryFeatScreen()
    {
        if (legendaryFeatScreen == null || legendaryFeatRowPrefab == null
            || legendaryFeatListParent == null) return;
        object? player = CareerFeatPlayer();
        if (player == null) return;

        ClearLegendaryFeatRows();

        int earned = 0;
        foreach (LegendaryFeatDefinition feat in LegendaryFeatCatalog.InCategory(legendaryFeatCategory))
        {
            CustomSkillDefinition? definition = CustomSkillCatalog.Find(feat.Id);
            if (definition == null) continue;

            object? skill = SkillXp(player, feat.Id);
            bool isEarned = skill != null && access.Int(skill, "level") > 0;
            bool isEquipped = isEarned && access.Bool(skill!, "equipped");
            if (isEarned) earned++;

            GameObject rowObject = UnityEngine.Object.Instantiate(
                legendaryFeatRowPrefab, legendaryFeatListParent);
            rowObject.name = "Legendary Feat - " + feat.Id;
            rowObject.SetActive(true);
            legendaryFeatRows.Add(rowObject);

            object? row = FeatComponent(rowObject, "SkillsObject");
            if (row == null)
            {
                Event("legendary-feats-ui-row-missing",
                    new { Id = feat.Id, Reason = "SkillsObject-component-not-found" });
                continue;
            }

            SkillPresentationText text = TextFor(player, definition);
            DisplayText(row, "skillName", feat.Name);
            DisplayText(row, "level", FeatStateLabel(skill, access));
            DisplayText(row, "description",
                text.Revealed ? text.Effect : "Complete the feat to reveal its effect.");
            DisplayText(row, "status", text.Revealed
                ? ((isEquipped ? "EQUIPPED" : "EARNED") + "\n" + text.Requirement)
                : "LOCKED");
            try { DisplayActive(row, access.Need(row, "starRating"), false); } catch { }
            try
            {
                object progress = access.Need(row, "progress");
                object parent = access.Need(progress, "parent");
                DisplayActive(row, parent, false);
            }
            catch { }

            object? button = FeatButton(rowObject.transform);
            if (button != null)
            {
                try { access.Set(button, "interactable", isEarned); } catch { }
                string capturedId = feat.Id;
                FeatWireButton(button, () => ToggleLegendaryFeat(capturedId));
            }
        }

        Transform root = legendaryFeatScreen.transform;
        Transform? categories = root.Find("Panel/Categories");
        if (categories != null)
        {
            UpdateLegendaryFeatTab(categories.Find("Finishing"),
                LegendaryFeatCategory.College, player);
            UpdateLegendaryFeatTab(categories.Find("Shooting"),
                LegendaryFeatCategory.Pro, player);
            Transform? points = categories.Find("Points");
            if (points != null) FeatSetTextAt(points, "Value", earned.ToString());
        }

        WriteLegendaryFeatUiStatus("refreshed");
    }

    private void UpdateLegendaryFeatTab(
        Transform? categoryRoot, LegendaryFeatCategory category, object player)
    {
        if (categoryRoot == null) return;
        int equipped = 0;
        foreach (LegendaryFeatDefinition feat in LegendaryFeatCatalog.InCategory(category))
        {
            object? skill = SkillXp(player, feat.Id);
            if (skill != null && access.Int(skill, "level") > 0
                && access.Bool(skill, "equipped"))
                equipped++;
        }
        Transform? textTransform = categoryRoot.Find("Buttons/Skill Button/Text");
        if (textTransform != null)
            FeatSetText(FeatText(textTransform), equipped + "/1");
    }

    private void ToggleLegendaryFeat(string id)
    {
        object? player = CareerFeatPlayer();
        if (player == null) return;
        LegendaryFeatCategory category = LegendaryFeatCatalog.Category(id);
        if (category == LegendaryFeatCategory.None) return;

        object? target = SkillXp(player, id);
        if (target == null || access.Int(target, "level") <= 0) return;

        bool equip = !access.Bool(target, "equipped");
        object skills = access.Need(player, "skills");
        if (equip)
        {
            for (int i = 0; i < access.Count(skills); i++)
            {
                object other = access.Item(skills, i);
                string otherId = access.Text(other, "id");
                if (LegendaryFeatCatalog.Category(otherId) != category) continue;
                access.Set(other, "equipped", false);
            }
        }
        access.Set(target, "equipped", equip);
        NormalizeSpecialSlots(player, "legendary-feats-ui");

        Event("legendary-feat-loadout-changed", new
        {
            Player = access.Int(player, "id"),
            Id = id,
            Category = category.ToString(),
            Equipped = equip,
            Limit = 1
        }, player);

        RefreshLegendaryFeatScreen();
    }

    private void WriteLegendaryFeatUiStatus(string stage)
    {
        try
        {
            diagnostics.WriteJson("legendary-feats-ui-status.json", new
            {
                Stage = stage,
                ScreenCreated = legendaryFeatScreen != null,
                MenuButtonCreated = legendaryFeatMenuButton != null,
                SourceScreen = legendaryFeatSourceScreen?.name ?? "",
                Menu = legendaryFeatMenu?.name ?? "",
                MenuChildCount = legendaryFeatMenu?.transform.childCount ?? 0,
                MenuTopLevelChildren = legendaryFeatMenu == null ? Array.Empty<string>() :
                    Enumerable.Range(0, legendaryFeatMenu.transform.childCount)
                        .Select(i => legendaryFeatMenu.transform.GetChild(i).name).ToArray(),
                Category = legendaryFeatCategory.ToString(),
                CollegeCount = LegendaryFeatCatalog
                    .InCategory(LegendaryFeatCategory.College).Count(),
                ProCount = LegendaryFeatCatalog
                    .InCategory(LegendaryFeatCategory.Pro).Count(),
                Storage = "native SkillXP compatibility backend",
                SaveSchemaChanged = false
            });
        }
        catch (Exception ex)
        {
            Error("legendary-feats-ui-status", ex);
        }
    }

    private static void AfterLegendaryFeatUi(object __instance)
    {
        Safe("legendary-feats-ui", m => m.EnsureLegendaryFeatUi(__instance));
    }
}
''')

print("Legendary Feats foundation and native-looking UI prototype applied.")
