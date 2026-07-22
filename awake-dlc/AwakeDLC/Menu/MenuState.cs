namespace AwakeDLC.Menu
{
    internal enum MenuTab
    {
        Player = 0,
        Weapons = 1,
        Vehicle = 2,
        World = 3
    }

    internal sealed class MenuState
    {
        public bool Open;
        public MenuTab Tab = MenuTab.Player;

        public bool GodMode;
        public bool NeverWanted;
    }
}
