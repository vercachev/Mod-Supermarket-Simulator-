using System.Numerics;
using AwakeDLC.Features;
using IVSDKDotNet;
using IVSDKDotNet.Enums;

namespace AwakeDLC.Menu
{
    internal static class MenuRenderer
    {
        public static void Draw(MenuState state)
        {
            if (!state.Open)
                return;

            Theme.Push();
            try
            {
                ImGuiIV.SetNextWindowPos(Theme.WindowPos);
                ImGuiIV.SetNextWindowSize(Theme.WindowSize);

                bool open = state.Open;
                if (!ImGuiIV.Begin("awake DLC", ref open, eImGuiWindowFlags.NoCollapse))
                {
                    state.Open = open;
                    ImGuiIV.End();
                    return;
                }

                state.Open = open;

                ImGuiIV.TextColored(Theme.TextDim, "SINGLE PLAYER  ·  Insert — закрыть");
                ImGuiIV.Separator();

                // Категории слева + контент справа
                ImGuiIV.BeginChild("tabs", new Vector2(110f, 0f), eImGuiChildFlags.Border, eImGuiWindowFlags.None);
                DrawTabButton(state, MenuTab.Player, "Player");
                DrawTabButton(state, MenuTab.Weapons, "Weapons");
                DrawTabButton(state, MenuTab.Vehicle, "Vehicle");
                DrawTabButton(state, MenuTab.World, "World");
                ImGuiIV.EndChild();

                ImGuiIV.SameLine();

                ImGuiIV.BeginChild("content", new Vector2(0f, 0f), eImGuiChildFlags.Border, eImGuiWindowFlags.None);
                switch (state.Tab)
                {
                    case MenuTab.Player:
                        DrawPlayer(state);
                        break;
                    case MenuTab.Weapons:
                        DrawWeapons();
                        break;
                    case MenuTab.Vehicle:
                        DrawVehicle();
                        break;
                    case MenuTab.World:
                        DrawWorld();
                        break;
                }
                ImGuiIV.EndChild();

                ImGuiIV.End();
            }
            finally
            {
                Theme.Pop();
            }
        }

        private static void DrawTabButton(MenuState state, MenuTab tab, string label)
        {
            bool selected = state.Tab == tab;
            if (selected)
                ImGuiIV.PushStyleColor(eImGuiCol.Button, Theme.Accent);

            if (ImGuiIV.Button(label, new Vector2(-1f, 34f)))
                state.Tab = tab;

            if (selected)
                ImGuiIV.PopStyleColor(1);
        }

        private static void DrawPlayer(MenuState state)
        {
            ImGuiIV.Text("Player");
            ImGuiIV.Separator();

            bool god = state.GodMode;
            if (ImGuiIV.CheckBox("God Mode", ref god))
            {
                state.GodMode = god;
                PlayerFeatures.SetGodMode(god);
            }

            bool never = state.NeverWanted;
            if (ImGuiIV.CheckBox("Never Wanted", ref never))
                state.NeverWanted = never;

            if (ImGuiIV.Button("Heal + Armour", new Vector2(-1f, 0f)))
                PlayerFeatures.Heal();

            if (ImGuiIV.Button("Clear Wanted", new Vector2(-1f, 0f)))
                PlayerFeatures.ClearWanted();

            ImGuiIV.Spacing();
            ImGuiIV.Text("Money");
            if (ImGuiIV.Button("+ 10 000", new Vector2(-1f, 0f)))
                PlayerFeatures.AddMoney(10_000);
            if (ImGuiIV.Button("+ 100 000", new Vector2(-1f, 0f)))
                PlayerFeatures.AddMoney(100_000);
            if (ImGuiIV.Button("+ 1 000 000", new Vector2(-1f, 0f)))
                PlayerFeatures.AddMoney(1_000_000);
        }

        private static void DrawWeapons()
        {
            ImGuiIV.Text("Weapons");
            ImGuiIV.Separator();
            if (ImGuiIV.Button("Give Weapons", new Vector2(-1f, 0f)))
                WeaponFeatures.GiveAll();
            if (ImGuiIV.Button("Remove Weapons", new Vector2(-1f, 0f)))
                WeaponFeatures.RemoveAll();
        }

        private static void DrawVehicle()
        {
            ImGuiIV.Text("Vehicle");
            ImGuiIV.Separator();
            if (ImGuiIV.Button("Repair Car", new Vector2(-1f, 0f)))
                VehicleFeatures.RepairCurrent();
            if (ImGuiIV.Button("Flip Car", new Vector2(-1f, 0f)))
                VehicleFeatures.FlipCurrent();
        }

        private static void DrawWorld()
        {
            ImGuiIV.Text("World");
            ImGuiIV.Separator();
            if (ImGuiIV.Button("Time 12:00", new Vector2(-1f, 0f)))
                WorldFeatures.SetNoon();
            if (ImGuiIV.Button("Time 00:00", new Vector2(-1f, 0f)))
                WorldFeatures.SetMidnight();
            if (ImGuiIV.Button("Clear Area", new Vector2(-1f, 0f)))
                WorldFeatures.ClearAreaAroundPlayer();
        }
    }
}
