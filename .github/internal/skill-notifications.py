from pathlib import Path

root=Path("src/Main/HoopLandExpanded")
p=root/"CustomSkills.cs"
s=p.read_text()

if s.count("public sealed class CustomSkills") != 1:
    raise SystemExit("CustomSkills class declaration anchor mismatch")
s=s.replace("public sealed class CustomSkills","public sealed partial class CustomSkills",1)

def one(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f"{label}: expected 1 anchor, found {n}")
    s=s.replace(old,new,1)

# Special-slot build has 25 skill hooks. Add one result-screen lifecycle hook
# and turn the existing GameUI.Start hook into prefix+postfix.
one(
    'public static readonly ProbeSpec[] SkillHooks = new ProbeSpec[25]',
    'public static readonly ProbeSpec[] SkillHooks = new ProbeSpec[26]',
    'skill hook count'
)
one(
    'Hook("game-reset", "GameUI", "Start", stat: false, "System.Void", Array.Empty<string>(), "ResetGame"),',
    'Hook("game-reset", "GameUI", "Start", stat: false, "System.Void", Array.Empty<string>(), "ResetGame", "SkillNotificationsGameReady"),\n\t\tHook("notification-results", "CareerGameResults", "OnEnable", stat: false, "System.Void", Array.Empty<string>(), "SkillNotificationsGameEnded"),',
    'game lifecycle hooks'
)

# Native replay must pass through the original game method instead of recursively
# re-entering HLE Grant().
one(
'''\tprivate static bool CustomProgress(object __0, string __1)
\t{
\t\tif (CustomSkillCatalog.Find(__1) == null)
''',
'''\tprivate static bool CustomProgress(object __0, string __1)
\t{
\t\tif (nativeNotificationReplay)
\t\t{
\t\t\treturn true;
\t\t}
\t\tif (CustomSkillCatalog.Find(__1) == null)
''',
    'native replay recursion guard'
)

# Notify only after HLE has committed the authoritative ordinary-skill transition.
old='''\t\t\tif (diagnostics.CaptureSkillEvent())
\t\t\t{
\t\t\t\tEvent("progress", new
\t\t\t\t{
\t\t\t\t\tId = id,
\t\t\t\t\tPlayer = access.Int(player, "id"),
\t\t\t\t\tXp = tuple2.Item1,
\t\t\t\t\tRank = tuple2.Item2,
\t\t\t\t\tPreviousRank = num2
\t\t\t\t}, player);
\t\t\t}
'''
new=old+'''\t\t\tNotifySkillTransition(player, customSkillDefinition, num2, tuple2.Item2, "ordinary-progress");
'''
one(old,new,'ordinary transition notification')

# Special achievements are not sent through Grant(), so enqueue/replay them
# when the award becomes authoritative.
old='''\t\t\t\t\tEvent("legend-qualified", new
\t\t\t\t\t{
\t\t\t\t\t\tPlayer = access.Int(item, "id"),
\t\t\t\t\t\tId = item2,
\t\t\t\t\t\tEvidence = "committed official native records",
\t\t\t\t\t\tAutomaticallyEquipped = false
\t\t\t\t\t}, item);
'''
new=old+'''\t\t\t\t\tNotifySkillTransition(item, customSkillDefinition, 0, 1, "legend-earned");
'''
one(old,new,'legend notification')

old='''\t\t\t\t\t\tEvent("icon-qualified", new
\t\t\t\t\t\t{
\t\t\t\t\t\t\tPlayer = access.Int(player, "id"),
\t\t\t\t\t\t\tId = icon.Id,
\t\t\t\t\t\t\tFamily = "Breakout",
\t\t\t\t\t\t\tEvidence = icon.Evidence,
\t\t\t\t\t\t\tAutomaticallyEquipped = false
\t\t\t\t\t\t}, player);
'''
new=old+'''\t\t\t\t\t\tNotifySkillTransition(player, CustomSkillCatalog.Find(icon.Id)!, 0, 1, "icon-earned");
'''
one(old,new,'icon notification')

# A career load must not inherit process-local notification suppression from a
# different branch/career.
one(
'''\tprivate static void ResetCareer()
\t{
\t\tinstance?.ResetPresentation();
''',
'''\tprivate static void ResetCareer()
\t{
\t\tinstance?.ResetSkillNotifications();
\t\tinstance?.ResetPresentation();
''',
    'career notification reset'
)

p.write_text(s)

(root/"SkillNotificationRuntime.cs").write_text(r'''using System;
using System.Collections.Generic;
using System.Globalization;

namespace HoopLandExpanded;

public sealed partial class CustomSkills
{
    [ThreadStatic]
    private static bool nativeNotificationReplay;

    private readonly Queue<SkillNotificationTicket> pendingSkillNotifications = new();
    private readonly HashSet<string> queuedOrShownSkillNotifications = new(StringComparer.Ordinal);
    private bool skillNotificationsGameReady;

    private sealed record SkillNotificationTicket(int PlayerId, string SkillId, int Rank, string Source);

    private bool IsCareerPlayer(object player)
    {
        try
        {
            object? league = access.Static("GameManager", "currentLeague");
            if (league == null) return false;
            object season = access.Need(league, "season");
            return access.Int(player, "id") == access.Int(season, "playerId")
                && access.Int(player, "tid") == access.Int(season, "teamId");
        }
        catch
        {
            return false;
        }
    }

    private string NotificationKey(object player, string id, int rank)
    {
        string anchor = "";
        try
        {
            object? league = access.Static("GameManager", "currentLeague");
            if (league != null) anchor = NativeAnchor(league);
        }
        catch { }
        return anchor + ":" + access.Int(player, "id").ToString(CultureInfo.InvariantCulture)
            + ":" + id + ":" + rank.ToString(CultureInfo.InvariantCulture);
    }

    private void NotifySkillTransition(object player, CustomSkillDefinition definition, int oldRank, int newRank, string source)
    {
        if (newRank <= oldRank || !IsCareerPlayer(player)) return;

        for (int rank = oldRank + 1; rank <= newRank; rank++)
        {
            string key = NotificationKey(player, definition.Id, rank);
            if (!queuedOrShownSkillNotifications.Add(key)) continue;

            SkillNotificationTicket ticket = new(access.Int(player, "id"), definition.Id, rank, source);
            if (skillNotificationsGameReady && TryReplayNativeSkillNotification(player, ticket))
            {
                Event("skill-notification-shown", new
                {
                    ticket.PlayerId,
                    ticket.SkillId,
                    ticket.Rank,
                    ticket.Source,
                    NativeUi = true
                }, player);
                continue;
            }

            if (pendingSkillNotifications.Count >= 64)
            {
                queuedOrShownSkillNotifications.Remove(key);
                Event("skill-notification-dropped", new
                {
                    ticket.PlayerId,
                    ticket.SkillId,
                    ticket.Rank,
                    ticket.Source,
                    Reason = "queue-bound"
                }, player);
                continue;
            }
            pendingSkillNotifications.Enqueue(ticket);
            Event("skill-notification-queued", new
            {
                ticket.PlayerId,
                ticket.SkillId,
                ticket.Rank,
                ticket.Source
            }, player);
        }
    }

    private object? FindCurrentPlayer(int playerId)
    {
        object? league = access.Static("GameManager", "currentLeague");
        object? teams = league == null ? null : access.Read(league, "teams");
        if (teams == null) return null;
        for (int i = 0; i < Math.Min(access.Count(teams), 700); i++)
        {
            object roster = access.Need(access.Item(teams, i), "roster");
            for (int j = 0; j < Math.Min(access.Count(roster), 64); j++)
            {
                object player = access.Item(roster, j);
                if (access.Int(player, "id") == playerId) return player;
            }
        }
        return null;
    }

    private bool TryReplayNativeSkillNotification(object player, SkillNotificationTicket ticket)
    {
        if (!skillNotificationsGameReady || nativeNotificationReplay) return false;
        CustomSkillDefinition? definition = CustomSkillCatalog.Find(ticket.SkillId);
        if (definition == null || ticket.Rank < 1 || ticket.Rank > definition.MaximumRank) return false;

        object? xp = SkillXp(player, ticket.SkillId);
        if (xp == null || access.Int(xp, "level") < ticket.Rank) return false;

        int actualXp = access.Int(xp, "xp");
        int actualRank = access.Int(xp, "level");
        bool actualEquipped = access.Bool(xp, "equipped");
        int observedRank = ticket.Rank - 1;

        try
        {
            (int season, int minutes) = Settings();
            int previousRank = ticket.Rank - 1;
            int threshold = CustomSkillCatalog.Threshold(definition, previousRank, season, minutes);
            if (threshold <= 0 || threshold == int.MaxValue) return false;

            access.Set(xp, "xp", Math.Max(0, threshold - 1));
            access.Set(xp, "level", previousRank);
            // Mastery ranks only progress natively while equipped. Preserve the
            // real equip state for unlocks, but force the synthetic mastery replay
            // on because HLE already proved that this rank transition occurred.
            if (previousRank > 0) access.Set(xp, "equipped", true);

            nativeNotificationReplay = true;
            access.Call(access.Type("PlayerSkills"), "ProgressSkill", player, ticket.SkillId);
            observedRank = access.Int(xp, "level");
        }
        catch (Exception ex)
        {
            Error("skill-notification-native-replay", ex);
            return false;
        }
        finally
        {
            nativeNotificationReplay = false;
            object? current = SkillXp(player, ticket.SkillId);
            if (current != null)
            {
                access.Set(current, "xp", actualXp);
                access.Set(current, "level", actualRank);
                access.Set(current, "equipped", actualEquipped);
            }
        }

        return observedRank >= ticket.Rank;
    }

    private void FlushSkillNotifications()
    {
        if (!skillNotificationsGameReady || pendingSkillNotifications.Count == 0) return;

        int attempts = pendingSkillNotifications.Count;
        for (int i = 0; i < attempts; i++)
        {
            SkillNotificationTicket ticket = pendingSkillNotifications.Peek();
            object? player = FindCurrentPlayer(ticket.PlayerId);
            if (player == null || !IsCareerPlayer(player)) break;
            if (!TryReplayNativeSkillNotification(player, ticket)) break;

            pendingSkillNotifications.Dequeue();
            Event("skill-notification-shown", new
            {
                ticket.PlayerId,
                ticket.SkillId,
                ticket.Rank,
                ticket.Source,
                NativeUi = true,
                Deferred = true
            }, player);
        }
    }

    private void ResetSkillNotifications()
    {
        skillNotificationsGameReady = false;
        pendingSkillNotifications.Clear();
        queuedOrShownSkillNotifications.Clear();
    }

    private static void SkillNotificationsGameReady()
    {
        Safe("skill-notifications-game-ready", m =>
        {
            m.skillNotificationsGameReady = true;
            m.FlushSkillNotifications();
        });
    }

    private static void SkillNotificationsGameEnded()
    {
        Safe("skill-notifications-game-ended", m =>
        {
            m.skillNotificationsGameReady = false;
        });
    }
}

public static class SkillNotificationRules
{
    public static bool IsRankTransition(int oldRank, int newRank) => newRank > oldRank && oldRank >= 0;
    public static string Kind(int oldRank, int newRank) =>
        !IsRankTransition(oldRank, newRank) ? "none" : oldRank == 0 ? "unlock" : "level-up";
}
''')

print("Native HLE skill notification replay bridge applied.")
