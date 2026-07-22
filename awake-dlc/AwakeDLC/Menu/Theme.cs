using System.Drawing;
using System.Numerics;
using IVSDKDotNet;
using IVSDKDotNet.Enums;

namespace AwakeDLC.Menu
{
    /// <summary>
    /// Красно-чёрная тема awake DLC (компактный оверлей, без боковых артов).
    /// </summary>
    internal static class Theme
    {
        public static readonly Color Accent = Color.FromArgb(255, 196, 30, 58); // #C41E3A
        public static readonly Color AccentHover = Color.FromArgb(255, 220, 50, 70);
        public static readonly Color PanelBg = Color.FromArgb(242, 13, 13, 13);
        public static readonly Color ChildBg = Color.FromArgb(230, 18, 18, 18);
        public static readonly Color FrameBg = Color.FromArgb(255, 28, 28, 28);
        public static readonly Color Text = Color.FromArgb(255, 245, 245, 245);
        public static readonly Color TextDim = Color.FromArgb(255, 160, 160, 160);
        public static readonly Color Border = Color.FromArgb(255, 196, 30, 58);

        public static readonly Vector2 WindowSize = new Vector2(420f, 460f);
        public static readonly Vector2 WindowPos = new Vector2(48f, 120f);

        private const int StyleColorCount = 16;

        public static void Push()
        {
            ImGuiIV.PushStyleColor(eImGuiCol.WindowBg, PanelBg);
            ImGuiIV.PushStyleColor(eImGuiCol.ChildBg, ChildBg);
            ImGuiIV.PushStyleColor(eImGuiCol.TitleBg, Color.FromArgb(255, 10, 10, 10));
            ImGuiIV.PushStyleColor(eImGuiCol.TitleBgActive, Accent);
            ImGuiIV.PushStyleColor(eImGuiCol.TitleBgCollapsed, Color.FromArgb(255, 10, 10, 10));
            ImGuiIV.PushStyleColor(eImGuiCol.Border, Border);
            ImGuiIV.PushStyleColor(eImGuiCol.FrameBg, FrameBg);
            ImGuiIV.PushStyleColor(eImGuiCol.FrameBgHovered, Color.FromArgb(255, 45, 20, 28));
            ImGuiIV.PushStyleColor(eImGuiCol.FrameBgActive, Color.FromArgb(255, 70, 25, 35));
            ImGuiIV.PushStyleColor(eImGuiCol.CheckMark, Accent);
            ImGuiIV.PushStyleColor(eImGuiCol.Button, Accent);
            ImGuiIV.PushStyleColor(eImGuiCol.ButtonHovered, AccentHover);
            ImGuiIV.PushStyleColor(eImGuiCol.ButtonActive, Color.FromArgb(255, 160, 20, 40));
            ImGuiIV.PushStyleColor(eImGuiCol.Header, Color.FromArgb(200, 196, 30, 58));
            ImGuiIV.PushStyleColor(eImGuiCol.HeaderHovered, Accent);
            ImGuiIV.PushStyleColor(eImGuiCol.HeaderActive, AccentHover);
        }

        public static void Pop()
        {
            ImGuiIV.PopStyleColor(StyleColorCount);
        }
    }
}
