using System;
using System.Windows.Forms;
using AwakeDLC.Features;
using AwakeDLC.Menu;
using IVSDKDotNet;

namespace AwakeDLC
{
    /// <summary>
    /// awake DLC — компактное SP-меню для GTA IV (IV-SDK .NET + ImGui).
    /// </summary>
    public class Main : Script
    {
        private readonly MenuState _state = new MenuState();

        public Main()
        {
            GameHelpers.Host = this;
            OnlyRaiseKeyEventsWhenInGame = true;
            Tick += OnTick;
            KeyDown += OnKeyDown;
            OnImGuiRendering += DrawMenu;
        }

        private void OnTick(object sender, EventArgs e)
        {
            if (!GameHelpers.IsSinglePlayerSession())
                return;

            PlayerFeatures.ApplyPersistent(_state.GodMode, _state.NeverWanted);
        }

        private void OnKeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Insert)
            {
                _state.Open = !_state.Open;
                if (_state.Open && !GameHelpers.IsSinglePlayerSession())
                {
                    _state.Open = false;
                    GameHelpers.Notify("awake DLC: только одиночная игра");
                }
            }
        }

        private void DrawMenu(IntPtr devicePtr, ImGuiIV_DrawingContext ctx)
        {
            MenuRenderer.Draw(_state);
        }
    }
}
