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
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;
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
    private object? legendaryFeatListController;
    private LegendaryFeatCategory legendaryFeatCategory = LegendaryFeatCategory.College;
    private readonly List<GameObject> legendaryFeatRows = new();
    private readonly List<UnityAction> legendaryFeatCallbacks = new();
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

    private static Text? FeatText(Transform? transform)
    {
        if (transform == null) return null;
        try { return transform.GetComponent<Text>(); } catch { return null; }
    }

    private static Button? FeatButton(Transform? transform)
    {
        if (transform == null) return null;
        try { return transform.GetComponent<Button>(); } catch { return null; }
    }

    private static object? FeatFindComponentByTypeName(GameObject gameObject, string typeName)
    {
        try
        {
            MethodInfo? method = gameObject.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance)
                .FirstOrDefault(m => m.Name == "GetComponents"
                    && !m.IsGenericMethod
                    && m.GetParameters().Length == 1
                    && m.GetParameters()[0].ParameterType == typeof(Type));
            object? result = method?.Invoke(gameObject, new object[] { typeof(Component) });
            if (result is Array array)
            {
                for (int i = 0; i < array.Length; i++)
                {
                    object? component = array.GetValue(i);
                    if (component == null) continue;
                    Type type = component.GetType();
                    if (string.Equals(type.Name, typeName, StringComparison.Ordinal)
                        || string.Equals(type.FullName, typeName, StringComparison.Ordinal))
                        return component;
                }
            }
        }
        catch { }
        return null;
    }

    private static string FeatCombinedText(Transform root)
    {
        List<string> values = new();
        foreach (Transform t in FeatWalk(root, 5))
        {
            Text? text = FeatText(t);
            if (text != null && !string.IsNullOrWhiteSpace(text.text))
                values.Add(text.text.Trim());
        }
        return string.Join(" | ", values);
    }

    private static void FeatSetFirstText(Transform root, string value)
    {
        foreach (Transform t in FeatWalk(root, 5))
        {
            Text? text = FeatText(t);
            if (text == null) continue;
            text.text = value;
            return;
        }
    }

    private static void FeatSetTextAt(Transform root, string path, string value)
    {
        Transform? t = root.Find(path);
        Text? text = FeatText(t);
        if (text != null) text.text = value;
    }

    private static Button? FeatFindButtonByLabel(Transform root, string token)
    {
        foreach (Transform t in FeatWalk(root, 8))
        {
            Button? button = FeatButton(t);
            if (button == null) continue;
            string text = FeatCombinedText(t);
            if (text.IndexOf(token, StringComparison.OrdinalIgnoreCase) >= 0)
                return button;
        }
        return null;
    }

    private void FeatWireButton(Button button, Action callback)
    {
        button.onClick.RemoveAllListeners();
        UnityAction action = DelegateSupport.ConvertDelegate<UnityAction>(callback);
        legendaryFeatCallbacks.Add(action);
        button.onClick.AddListener(action);
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

        if (legendaryFeatScreen == null)
        {
            buildingLegendaryFeatUi = true;
            try
            {
                legendaryFeatScreen = UnityEngine.Object.Instantiate(source, myPlayer);
                legendaryFeatScreen.name = "Legendary Feats";
                legendaryFeatScreen.SetActive(false);

                object? clonedList = FeatFindComponentByTypeName(legendaryFeatScreen, "ListSkills");
                if (clonedList != null)
                {
                    legendaryFeatListController = clonedList;
                    try { legendaryFeatRowPrefab = access.Need(clonedList, "listObject") as GameObject; } catch { }
                    try { legendaryFeatListParent = access.Need(clonedList, "listParent") as Transform; } catch { }
                    try { access.Set(clonedList, "enabled", false); } catch { }
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
        if (legendaryFeatScreen == null || legendaryFeatListController == null) return;
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
                Button? b = FeatButton(college.Find("Skill Button"));
                if (b != null) FeatWireButton(b, () => SelectLegendaryFeatCategory(LegendaryFeatCategory.College));
            }
            if (pro != null)
            {
                FeatSetTextAt(pro, "Header", "PRO");
                Button? b = FeatButton(pro.Find("Skill Button"));
                if (b != null) FeatWireButton(b, () => SelectLegendaryFeatCategory(LegendaryFeatCategory.Pro));
            }
            if (creating != null) creating.gameObject.SetActive(false);
            if (defense != null) defense.gameObject.SetActive(false);
            if (points != null) FeatSetTextAt(points, "Header", "EARNED");
        }

        try
        {
            GameObject options = (GameObject)access.Need(legendaryFeatListController, "skillOptions");
            options.SetActive(false);
        }
        catch { }

        ClearLegendaryFeatRows();
    }

    private void EnsureLegendaryFeatMenuButton()
    {
        if (legendaryFeatMenuButton != null || legendaryFeatMenu == null) return;

        Button? sourceButton = FeatFindButtonByLabel(legendaryFeatMenu.transform, "SKILL");
        if (sourceButton == null)
        {
            Event("legendary-feats-ui-menu-missing", new { Reason = "player-skills-button-not-found" });
            return;
        }

        Transform parent = sourceButton.transform.parent;
        GameObject clone = UnityEngine.Object.Instantiate(sourceButton.gameObject, parent);
        clone.name = "Legendary Feats Button";
        legendaryFeatMenuButton = clone;

        Button? button = clone.GetComponent<Button>();
        if (button == null)
        {
            Event("legendary-feats-ui-menu-missing", new { Reason = "cloned-button-component-not-found" });
            UnityEngine.Object.Destroy(clone);
            legendaryFeatMenuButton = null;
            return;
        }

        foreach (Transform t in FeatWalk(clone.transform, 5))
        {
            Text? text = FeatText(t);
            if (text == null) continue;
            if (string.IsNullOrWhiteSpace(text.text)) continue;
            text.text = "LEGENDARY FEATS";
            break;
        }

        PlaceLegendaryFeatMenuButtonFallback(sourceButton, button);

        FeatWireButton(button, OpenLegendaryFeats);
    }

    private void PlaceLegendaryFeatMenuButtonFallback(Button sourceButton, Button clonedButton)
    {
        RectTransform? sourceRect = sourceButton.transform as RectTransform;
        RectTransform? cloneRect = clonedButton.transform as RectTransform;
        if (sourceRect == null || cloneRect == null) return;

        List<RectTransform> siblings = new();
        Transform parent = sourceButton.transform.parent;
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
        Event("legendary-feats-ui-opened", new { Category = legendaryFeatCategory.ToString() });
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
        if (legendaryFeatScreen == null || legendaryFeatRowPrefab == null || legendaryFeatListParent == null) return;
        object? player = CareerFeatPlayer();
        if (player == null) return;

        ClearLegendaryFeatRows();

        int earned = 0;
        int equipped = 0;
        foreach (LegendaryFeatDefinition feat in LegendaryFeatCatalog.InCategory(legendaryFeatCategory))
        {
            CustomSkillDefinition? definition = CustomSkillCatalog.Find(feat.Id);
            if (definition == null) continue;

            object? skill = SkillXp(player, feat.Id);
            bool isEarned = skill != null && access.Int(skill, "level") > 0;
            bool isEquipped = isEarned && access.Bool(skill!, "equipped");
            if (isEarned) earned++;
            if (isEquipped) equipped++;

            GameObject rowObject = UnityEngine.Object.Instantiate(legendaryFeatRowPrefab, legendaryFeatListParent);
            rowObject.name = "Legendary Feat - " + feat.Id;
            rowObject.SetActive(true);
            legendaryFeatRows.Add(rowObject);

            object? row = FeatFindComponentByTypeName(rowObject, "SkillsObject");
            if (row == null) continue;

            SkillPresentationText text = TextFor(player, definition);
            DisplayText(row, "skillName", feat.Name);
            DisplayText(row, "level", FeatStateLabel(skill, access));
            DisplayText(row, "description", text.Revealed ? text.Effect : "Complete the feat to reveal its effect.");
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

            Button? button = rowObject.GetComponent<Button>();
            if (button != null)
            {
                button.interactable = isEarned;
                string capturedId = feat.Id;
                FeatWireButton(button, () => ToggleLegendaryFeat(capturedId));
            }
        }

        Transform root = legendaryFeatScreen.transform;
        Transform? categories = root.Find("Panel/Categories");
        if (categories != null)
        {
            UpdateLegendaryFeatTab(categories.Find("Finishing"), LegendaryFeatCategory.College, player);
            UpdateLegendaryFeatTab(categories.Find("Shooting"), LegendaryFeatCategory.Pro, player);
            Transform? points = categories.Find("Points");
            if (points != null) FeatSetTextAt(points, "Value", earned.ToString());
        }

        WriteLegendaryFeatUiStatus("refreshed");
    }

    private void UpdateLegendaryFeatTab(Transform? categoryRoot, LegendaryFeatCategory category, object player)
    {
        if (categoryRoot == null) return;
        int equipped = 0;
        foreach (LegendaryFeatDefinition feat in LegendaryFeatCatalog.InCategory(category))
        {
            object? skill = SkillXp(player, feat.Id);
            if (skill != null && access.Int(skill, "level") > 0 && access.Bool(skill, "equipped"))
                equipped++;
        }
        Transform? textTransform = categoryRoot.Find("Skill Button/Text");
        Text? text = FeatText(textTransform);
        if (text != null) text.text = equipped + "/1";
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
                Category = legendaryFeatCategory.ToString(),
                CollegeCount = LegendaryFeatCatalog.InCategory(LegendaryFeatCategory.College).Count(),
                ProCount = LegendaryFeatCatalog.InCategory(LegendaryFeatCategory.Pro).Count(),
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
