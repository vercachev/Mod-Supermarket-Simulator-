using static IVSDKDotNet.Native.Natives;

namespace AwakeDLC.Features
{
    internal static class PlayerFeatures
    {
        public static void ApplyPersistent(bool godMode, bool neverWanted)
        {
            if (!GameHelpers.TryGetPlayerPed(out int ped))
                return;

            if (godMode)
                SET_CHAR_INVINCIBLE(ped, true);

            if (neverWanted)
                CLEAR_WANTED_LEVEL(GameHelpers.PlayerId());
        }

        public static void SetGodMode(bool enabled)
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;
            if (!GameHelpers.TryGetPlayerPed(out int ped))
                return;

            SET_CHAR_INVINCIBLE(ped, enabled);
            GameHelpers.Notify(enabled ? "God Mode: ON" : "God Mode: OFF");
        }

        public static void Heal()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;
            if (!GameHelpers.TryGetPlayerPed(out int ped))
                return;

            SET_CHAR_HEALTH(ped, 200);
            ADD_ARMOUR_TO_CHAR(ped, 100);
            GameHelpers.Notify("Здоровье + броня восстановлены");
        }

        public static void AddMoney(int amount)
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;

            ADD_SCORE(GameHelpers.PlayerId(), amount);
            GameHelpers.Notify($"Деньги +{amount:N0}");
        }

        public static void ClearWanted()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;

            CLEAR_WANTED_LEVEL(GameHelpers.PlayerId());
            GameHelpers.Notify("Розыск сброшен");
        }
    }
}
