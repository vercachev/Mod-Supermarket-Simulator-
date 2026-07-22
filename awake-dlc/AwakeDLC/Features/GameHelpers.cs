using IVSDKDotNet;
using static IVSDKDotNet.Native.Natives;

namespace AwakeDLC.Features
{
    internal static class GameHelpers
    {
        public static Script Host;

        public static int PlayerId()
        {
            return (int)GET_PLAYER_ID();
        }

        public static bool IsSinglePlayerSession()
        {
            return !IS_NETWORK_SESSION();
        }

        public static bool TryGetPlayerPed(out int ped)
        {
            ped = 0;
            GET_PLAYER_CHAR(PlayerId(), out ped);
            return ped != 0 && DOES_CHAR_EXIST(ped);
        }

        public static void Notify(string message)
        {
            if (Host != null)
                Host.ShowSubtitleMessage(message);
            else
                IVGame.Console.Print(message);
        }

        public static bool EnsureSinglePlayer()
        {
            if (IsSinglePlayerSession())
                return true;
            Notify("awake DLC: только одиночная игра");
            return false;
        }
    }
}
