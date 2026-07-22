using System.Numerics;
using static IVSDKDotNet.Native.Natives;

namespace AwakeDLC.Features
{
    internal static class WorldFeatures
    {
        public static void SetNoon()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;

            SET_TIME_OF_DAY(12, 0);
            GameHelpers.Notify("Время: 12:00");
        }

        public static void SetMidnight()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;

            SET_TIME_OF_DAY(0, 0);
            GameHelpers.Notify("Время: 00:00");
        }

        public static void ClearAreaAroundPlayer()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;
            if (!GameHelpers.TryGetPlayerPed(out int ped))
                return;

            GET_CHAR_COORDINATES(ped, out Vector3 pos);
            CLEAR_AREA(pos, 50.0f, true);
            GameHelpers.Notify("Зона очищена");
        }
    }
}
