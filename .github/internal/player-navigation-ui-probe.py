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
using UnityEngine;
using UnityEngine.SceneManagement;

namespace HoopLandExpanded;

public sealed partial class CustomSkills
{
    private int playerNavigationUiCaptureCount;

    private static string NavPath(Transform? t)
    {
        if (t == null) return "";
        List<string> parts = new();
        Transform? cur = t;
        for (int i = 0; cur != null && i < 24; i++)
        {
            parts.Add(cur.gameObject?.name ?? cur.name ?? "");
            cur = cur.parent;
        }
        parts.Reverse();
        return string.Join("/", parts);
    }

    private static bool NavInterestingName(string? value)
    {
        string s=(value ?? "").ToLowerInvariant();
        return s.Contains("player") || s.Contains("skill") || s.Contains("upgrade")
            || s.Contains("attribute") || s.Contains("profile") || s.Contains("development")
            || s.Contains("progression") || s.Contains("career");
    }

    private static int NavScore(string name, string path)
    {
        string n=(name ?? "").ToLowerInvariant();
        string p=(path ?? "").ToLowerInvariant();
        int score=0;
        if (n.Contains("player")) score += 12;
        if (n.Contains("skill")) score += 11;
        if (n.Contains("upgrade")) score += 11;
        if (n.Contains("attribute")) score += 9;
        if (n.Contains("profile")) score += 8;
        if (n.Contains("development")) score += 8;
        if (n.Contains("progression")) score += 8;
        if (n.Contains("career")) score += 6;
        if (n.Contains("button")) score += 3;
        if (p.Contains("player")) score += 4;
        if (p.Contains("skill") || p.Contains("upgrade")) score += 3;
        return score;
    }

    private object NavPersistentEvents(object? evt)
    {
        if (evt == null) return new { Count = -1, Events = Array.Empty<object>() };
        try
        {
            Type t=evt.GetType();
            MethodInfo? countMethod=t.GetMethods(UiFlags)
                .FirstOrDefault(m => m.Name=="GetPersistentEventCount" && m.GetParameters().Length==0);
            int count=countMethod == null ? -1 : Convert.ToInt32(countMethod.Invoke(evt,null),CultureInfo.InvariantCulture);
            List<object> rows=new();
            MethodInfo? methodName=t.GetMethods(UiFlags)
                .FirstOrDefault(m => m.Name=="GetPersistentMethodName" && m.GetParameters().Length==1);
            MethodInfo? target=t.GetMethods(UiFlags)
                .FirstOrDefault(m => m.Name=="GetPersistentTarget" && m.GetParameters().Length==1);
            for (int i=0; i>=0 && i<Math.Min(count,16); i++)
            {
                string name="";
                object? targetObj=null;
                try { name=UiString(methodName?.Invoke(evt,new object[]{i})); } catch { }
                try { targetObj=target?.Invoke(evt,new object[]{i}); } catch { }
                rows.Add(new { Index=i, Method=name, Target=UiObjectSummary(targetObj) });
            }
            return new { Count=count, Events=rows.ToArray() };
        }
        catch (Exception ex)
        {
            return new { Count=-1, Error=ex.GetBaseException().GetType().Name, Events=Array.Empty<object>() };
        }
    }

    private object NavNavigation(object? navigation)
    {
        if (navigation == null) return new { Mode="", Up="", Down="", Left="", Right="" };
        return new
        {
            Mode=UiString(UiReadProperty(navigation,"mode")),
            Up=UiName(UiReadProperty(navigation,"selectOnUp")),
            Down=UiName(UiReadProperty(navigation,"selectOnDown")),
            Left=UiName(UiReadProperty(navigation,"selectOnLeft")),
            Right=UiName(UiReadProperty(navigation,"selectOnRight"))
        };
    }

    private object NavComponentSnapshot(Component component)
    {
        Type t=component.GetType();
        object? onClick=UiReadProperty(component,"onClick");
        object? nav=UiReadProperty(component,"navigation");
        bool nonUnity=!(t.FullName ?? "").StartsWith("UnityEngine.",StringComparison.Ordinal)
            && !(t.FullName ?? "").StartsWith("TMPro.",StringComparison.Ordinal)
            && !(t.FullName ?? "").StartsWith("Il2Cpp",StringComparison.Ordinal);
        object? inventory=null;
        if (nonUnity)
        {
            try { inventory=UiTypeInventory(t); } catch { }
        }
        return new
        {
            Type=t.FullName ?? t.Name,
            Name=UiName(component),
            Enabled=UiString(UiReadProperty(component,"enabled")),
            Interactable=UiString(UiReadProperty(component,"interactable")),
            Transition=UiString(UiReadProperty(component,"transition")),
            Navigation=NavNavigation(nav),
            OnClick=NavPersistentEvents(onClick),
            TypeInventory=inventory
        };
    }

    private object[] NavComponents(GameObject go)
    {
        List<object> rows=new();
        try
        {
            foreach (Component component in go.GetComponents<Component>())
            {
                if (component == null) continue;
                rows.Add(NavComponentSnapshot(component));
                if (rows.Count >= 32) break;
            }
        }
        catch (Exception ex)
        {
            rows.Add(new { Error=ex.GetBaseException().GetType().Name });
        }
        return rows.ToArray();
    }

    private object[] NavChildSummary(GameObject go)
    {
        List<object> rows=new();
        try
        {
            Transform t=go.transform;
            for (int i=0; i<t.childCount && i<40; i++)
            {
                Transform child=t.GetChild(i);
                GameObject c=child.gameObject;
                rows.Add(new
                {
                    Name=c.name,
                    Path=NavPath(child),
                    ActiveSelf=c.activeSelf,
                    ActiveInHierarchy=c.activeInHierarchy,
                    Rect=UiRect(child)
                });
            }
        }
        catch { }
        return rows.ToArray();
    }

    private object[] NavTexts(GameObject root)
    {
        List<object> rows=new();
        Queue<(Transform T,int Depth)> q=new();
        q.Enqueue((root.transform,0));
        while (q.Count>0 && rows.Count<80)
        {
            var item=q.Dequeue();
            Transform t=item.T;
            if (item.Depth>6) continue;
            try
            {
                foreach (Component component in t.gameObject.GetComponents<Component>())
                {
                    if (component == null) continue;
                    string type=component.GetType().FullName ?? "";
                    if (type=="UnityEngine.UI.Text" || type.Contains("TextMeshPro",StringComparison.Ordinal))
                    {
                        string text=UiString(UiReadProperty(component,"text"));
                        if (!string.IsNullOrWhiteSpace(text))
                            rows.Add(new { Path=NavPath(t), Type=type, Text=text });
                    }
                }
                for (int i=0; i<t.childCount; i++) q.Enqueue((t.GetChild(i),item.Depth+1));
            }
            catch { }
        }
        return rows.ToArray();
    }

    private object NavGameObjectSnapshot(GameObject go, int score)
    {
        string scene="";
        bool valid=false;
        try { valid=go.scene.IsValid(); scene=go.scene.name ?? ""; } catch { }
        return new
        {
            Score=score,
            Name=go.name,
            Path=NavPath(go.transform),
            Scene=scene,
            SceneValid=valid,
            ActiveSelf=go.activeSelf,
            ActiveInHierarchy=go.activeInHierarchy,
            Rect=UiRect(go.transform),
            Components=NavComponents(go),
            Children=NavChildSummary(go),
            Text=NavTexts(go)
        };
    }

    private object[] NavAncestorChain(object listSkills)
    {
        List<object> rows=new();
        GameObject? go=UiGameObject(listSkills) as GameObject;
        Transform? cur=go?.transform;
        for (int depth=0; cur!=null && depth<16; depth++,cur=cur.parent)
        {
            List<object> siblings=new();
            Transform? parent=cur.parent;
            if (parent!=null)
            {
                for (int i=0; i<parent.childCount && i<80; i++)
                {
                    Transform child=parent.GetChild(i);
                    siblings.Add(new
                    {
                        Name=child.gameObject.name,
                        ActiveSelf=child.gameObject.activeSelf,
                        ActiveInHierarchy=child.gameObject.activeInHierarchy,
                        Rect=UiRect(child)
                    });
                }
            }
            rows.Add(new
            {
                Depth=depth,
                Name=cur.gameObject.name,
                Path=NavPath(cur),
                ActiveSelf=cur.gameObject.activeSelf,
                ActiveInHierarchy=cur.gameObject.activeInHierarchy,
                Rect=UiRect(cur),
                Components=NavComponents(cur.gameObject),
                Siblings=siblings.ToArray()
            });
        }
        return rows.ToArray();
    }

    private object[] NavSceneRoots(IEnumerable<GameObject> loaded)
    {
        return loaded.Where(go =>
            {
                try { return go.scene.IsValid() && go.transform.parent==null; }
                catch { return false; }
            })
            .OrderBy(go => go.name,StringComparer.OrdinalIgnoreCase)
            .Take(240)
            .Select(go => new
            {
                Name=go.name,
                Scene=go.scene.name,
                ActiveSelf=go.activeSelf,
                ActiveInHierarchy=go.activeInHierarchy,
                Rect=UiRect(go.transform),
                Components=NavComponents(go)
            }).Cast<object>().ToArray();
    }

    private void CapturePlayerNavigationUi(object listSkills)
    {
        if (playerNavigationUiCaptureCount >= 8) return;
        playerNavigationUiCaptureCount++;

        List<GameObject> loaded=new();
        try
        {
            HashSet<int> seen=new();
            for (int sceneIndex=0; sceneIndex<SceneManager.sceneCount; sceneIndex++)
            {
                Scene scene=SceneManager.GetSceneAt(sceneIndex);
                if (!scene.IsValid() || !scene.isLoaded) continue;
                foreach (GameObject root in scene.GetRootGameObjects())
                {
                    if (root == null) continue;
                    Queue<Transform> queue=new();
                    queue.Enqueue(root.transform);
                    while (queue.Count>0 && loaded.Count<12000)
                    {
                        Transform t=queue.Dequeue();
                        GameObject go=t.gameObject;
                        int id=go.GetInstanceID();
                        if (seen.Add(id)) loaded.Add(go);
                        for (int i=0; i<t.childCount; i++) queue.Enqueue(t.GetChild(i));
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Error("player-navigation-ui-enumerate",ex);
        }

        List<(GameObject Go,int Score)> scored=new();
        foreach (GameObject go in loaded)
        {
            string path=NavPath(go.transform);
            int score=NavScore(go.name,path);
            bool ownInteresting=NavInterestingName(go.name);
            bool likelyButton=go.name.IndexOf("button",StringComparison.OrdinalIgnoreCase)>=0
                && path.IndexOf("player",StringComparison.OrdinalIgnoreCase)>=0;
            if (ownInteresting || likelyButton) scored.Add((go,score));
        }

        object[] candidates=scored
            .OrderByDescending(x => x.Score)
            .ThenBy(x => NavPath(x.Go.transform),StringComparer.OrdinalIgnoreCase)
            .Take(220)
            .Select(x => NavGameObjectSnapshot(x.Go,x.Score))
            .ToArray();

        diagnostics.WriteJson("player-navigation-ui-probe.json",new
        {
            Probe="player-navigation-native-ui-v1",
            ReadOnly=true,
            CapturedAtUtc=DateTime.UtcNow,
            Capture=playerNavigationUiCaptureCount,
            Instructions="Navigate from the normal career player screen into Player Skills. The probe changes no UI or save state.",
            Screen=new
            {
                Width=Screen.width,
                Height=Screen.height,
                Dpi=Screen.dpi,
                FullScreen=Screen.fullScreen,
                CurrentResolution=Screen.currentResolution.ToString()
            },
            TriggerType=UiTypeInventory(listSkills.GetType()),
            TriggerMembers=UiDeclaredMemberSnapshot(listSkills),
            TriggerAncestors=NavAncestorChain(listSkills),
            SceneRoots=NavSceneRoots(loaded),
            CandidateObjects=candidates,
            LoadedSceneGameObjects=loaded.Count
        });
    }
}
''')

print("Read-only player-navigation UI probe applied.")
