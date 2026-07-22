using IVSDKDotNet.Enums;
using static IVSDKDotNet.Native.Natives;

namespace AwakeDLC.Features
{
    internal static class WeaponFeatures
    {
        private static readonly eWeaponType[] StarterKit =
        {
            eWeaponType.WEAPON_PISTOL,
            eWeaponType.WEAPON_DEAGLE,
            eWeaponType.WEAPON_SHOTGUN,
            eWeaponType.WEAPON_MP5,
            eWeaponType.WEAPON_AK47,
            eWeaponType.WEAPON_M4,
            eWeaponType.WEAPON_SNIPERRIFLE,
            eWeaponType.WEAPON_RLAUNCHER,
            eWeaponType.WEAPON_MOLOTOV,
            eWeaponType.WEAPON_GRENADE,
            eWeaponType.WEAPON_BASEBALLBAT,
            eWeaponType.WEAPON_KNIFE,
        };

        public static void GiveAll()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;
            if (!GameHelpers.TryGetPlayerPed(out int ped))
                return;

            foreach (eWeaponType weapon in StarterKit)
                GIVE_WEAPON_TO_CHAR(ped, (int)weapon, 9999, true);

            GameHelpers.Notify("Оружие выдано");
        }

        public static void RemoveAll()
        {
            if (!GameHelpers.EnsureSinglePlayer())
                return;
            if (!GameHelpers.TryGetPlayerPed(out int ped))
                return;

            REMOVE_ALL_CHAR_WEAPONS(ped);
            GameHelpers.Notify("Оружие снято");
        }
    }
}
