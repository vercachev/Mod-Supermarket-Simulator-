using System.Numerics;
using static IVSDKDotNet.Native.Natives;

namespace AwakeDLC.Features
{
    internal static class VehicleFeatures
    {
        public static void RepairCurrent()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;
            if (!GameHelpers.TryGetPlayerPed(out int ped))
                return;

            if (!IS_CHAR_IN_ANY_CAR(ped))
            {
                GameHelpers.Notify("Сядьте в машину");
                return;
            }

            GET_CAR_CHAR_IS_USING(ped, out int car);
            if (car == 0)
                return;

            FIX_CAR(car);
            SET_CAR_HEALTH(car, 1000);
            GameHelpers.Notify("Машина починена");
        }

        public static void FlipCurrent()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;
            if (!GameHelpers.TryGetPlayerPed(out int ped))
                return;

            if (!IS_CHAR_IN_ANY_CAR(ped))
            {
                GameHelpers.Notify("Сядьте в машину");
                return;
            }

            GET_CAR_CHAR_IS_USING(ped, out int car);
            if (car == 0)
                return;

            GET_CAR_COORDINATES(car, out Vector3 pos);
            GET_CAR_HEADING(car, out float heading);
            SET_CAR_COORDINATES(car, pos.X, pos.Y, pos.Z + 1.0f);
            SET_CAR_HEADING(car, heading);
            GameHelpers.Notify("Машина перевёрнута");
        }
    }
}
